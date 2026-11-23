"""Small SQLite helpers for the local PW2 prototype."""
from contextlib import contextmanager
import hashlib
import hmac
import os
from pathlib import Path
import secrets
import sqlite3

from catalogue import INSERT_COMPONENT, csv_rows
from config import LOCAL_PASSWORD, PRODUCTION

HERE = Path(__file__).resolve().parent


@contextmanager
def connection():
    path = os.environ.get("PCBUILDER_DB", str(HERE / "database" / "app.db"))
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    try:
        with db:
            yield db
    finally:
        db.close()


def make_password_hash(password):
    salt = secrets.token_bytes(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310000)
    return salt.hex() + ":" + hashed.hex()


def verify_password(password, stored):
    try:
        salt_hex, hash_hex = stored.split(":", 1)
        attempt = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 310000)
        return hmac.compare_digest(attempt, bytes.fromhex(hash_hex))
    except (ValueError, TypeError):
        return False


def init_database():
    with connection() as db:
        db.executescript((HERE / "database" / "schema.sql").read_text(encoding="utf-8"))
        if db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0 and not PRODUCTION:
            db.executemany(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                [
                    ("student", make_password_hash(LOCAL_PASSWORD), "student"),
                    ("admin", make_password_hash(LOCAL_PASSWORD), "admin"),
                ],
            )
        if PRODUCTION:
            for row in db.execute("SELECT username, password_hash FROM users"):
                if row["username"] in {"student", "admin"} and verify_password(LOCAL_PASSWORD, row["password_hash"]):
                    raise RuntimeError("Use a fresh database or remove local demo accounts before deployment.")
        if "specs" not in {row["name"] for row in db.execute("PRAGMA table_info(components)")}:
            db.execute("ALTER TABLE components ADD COLUMN specs TEXT NOT NULL DEFAULT ''")
        new_catalogue = db.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 0
        if new_catalogue:
            categories = ["CPU", "Motherboard", "RAM", "GPU", "Storage", "PSU", "Case"]
            db.executemany("INSERT INTO categories (name) VALUES (?)", [(x,) for x in categories])
        categories = {row["name"]: row["id"] for row in db.execute("SELECT id, name FROM categories")}
        seed = csv_rows((HERE / "database" / "seed_components.csv").read_bytes(), categories)
        if new_catalogue:
            db.executemany(INSERT_COMPONENT, seed)
        else:
            upgrade_demo_catalogue(db, seed)


# Placeholder parts from the first prototype and the real models that replace them.
DEMO_NAMES = {
    "Demo CPU AM5": "AMD Ryzen 5 7600",
    "Demo CPU LGA1700": "Intel Core i5-14400F",
    "Demo motherboard AM5": "MSI PRO B650M-A WIFI",
    "Demo motherboard LGA1700": "MSI PRO B760M-A WIFI DDR4",
    "16 GB DDR5 demo kit": "Kingston FURY Beast 16 GB (2 × 8 GB) DDR5-5600",
    "16 GB DDR4 demo kit": "Corsair Vengeance LPX 16 GB (2 × 8 GB) DDR4-3200",
    "Demo graphics card": "MSI GeForce RTX 5060 8G VENTUS 2X OC",
    "1 TB SSD demo": "Samsung 990 EVO Plus 1 TB",
    "650 W power supply demo": "be quiet! System Power 10 650W",
    "Basic case demo": "Cooler Master MasterBox Q300L",
}


def upgrade_demo_catalogue(db, seed):
    """Rename placeholder parts in place, so saved builds keep their items, then add the rest once."""
    specs = {row[1]: row[5] for row in seed}
    renamed = 0
    for old, new in DEMO_NAMES.items():
        if not db.execute("SELECT 1 FROM components WHERE name = ?", (new,)).fetchone():
            renamed += db.execute(
                "UPDATE components SET name = ?, specs = ? WHERE name = ?", (new, specs[new], old),
            ).rowcount
    if renamed:
        db.executemany(INSERT_COMPONENT.replace("INSERT INTO", "INSERT OR IGNORE INTO"), seed)
