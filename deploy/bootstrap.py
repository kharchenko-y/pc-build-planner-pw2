"""Initialize persistent state in the hosting account's private home directory."""
import json
import os
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
PRIVATE = Path.home() / ".pcbuild-pw2"


def write_private(path, text):
    with path.open("x", encoding="utf-8") as stream:
        os.chmod(path, 0o600)
        stream.write(text)


def main():
    os.umask(0o077)
    PRIVATE.mkdir(mode=0o700, exist_ok=True)
    config_path = PRIVATE / "runtime.json"
    if not config_path.exists():
        write_private(config_path, json.dumps({
            "PCBUILDER_ENV": "production",
            "SESSION_SECRET": secrets.token_urlsafe(48),
            "PCBUILDER_DB": str(PRIVATE / "app.sqlite3"),
        }))
    os.environ.update(json.loads(config_path.read_text(encoding="utf-8")))

    from db import connection, init_database, make_password_hash

    init_database()
    for username, role in (("classroom", "student"), ("classroom-admin", "admin")):
        login_path = PRIVATE / f"{username}.txt"
        with connection() as db:
            row = db.execute("SELECT role FROM users WHERE username = ?", (username,)).fetchone()
            if row:
                if row["role"] != role or not login_path.exists():
                    raise RuntimeError(f"Review the existing {username} account before rerunning.")
                continue
            password = login_path.read_text(encoding="utf-8").splitlines()[1] if login_path.exists() else secrets.token_urlsafe(24)
            if not login_path.exists():
                write_private(login_path, f"{username}\n{password}\n")
            db.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, make_password_hash(password), role),
            )
    print("Persistent SQLite database and separate classroom accounts are ready.")


if __name__ == "__main__":
    main()

