"""Small SQLite helpers for the local PW2 prototype."""
from contextlib import contextmanager
import hashlib
import hmac
import os
from pathlib import Path
import secrets
import sqlite3

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
        if db.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 0:
            categories = ["CPU", "Motherboard", "RAM", "GPU", "Storage", "PSU", "Case"]
            db.executemany("INSERT INTO categories (name) VALUES (?)", [(x,) for x in categories])
        if db.execute("SELECT COUNT(*) FROM components").fetchone()[0] == 0:
            sample = [
                ("CPU", "Demo CPU AM5", 19000, "AM5", None),
                ("CPU", "Demo CPU LGA1700", 17500, "LGA1700", None),
                ("Motherboard", "Demo motherboard AM5", 13000, "AM5", "DDR5"),
                ("Motherboard", "Demo motherboard LGA1700", 12500, "LGA1700", "DDR4"),
                ("RAM", "16 GB DDR5 demo kit", 5500, None, "DDR5"),
                ("RAM", "16 GB DDR4 demo kit", 4000, None, "DDR4"),
                ("GPU", "Demo graphics card", 29000, None, None),
                ("Storage", "1 TB SSD demo", 7500, None, None),
                ("PSU", "650 W power supply demo", 7000, None, None),
                ("Case", "Basic case demo", 6000, None, None),
            ]
            db.executemany(
                """INSERT INTO components (category_id, name, price_cents, socket, ram_type)
                   VALUES ((SELECT id FROM categories WHERE name = ?), ?, ?, ?, ?)""",
                sample,
            )
