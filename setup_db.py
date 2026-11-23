"""Initialize SQLite and provision an account without storing plaintext."""
import argparse
import getpass
import re
import sqlite3

from config import PRODUCTION
from db import connection, init_database, make_password_hash

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--add-user", metavar="USERNAME")
parser.add_argument("--role", choices=("student", "admin"), default="student")


def main():
    args = parser.parse_args()
    init_database()
    if args.add_user is None:
        print("Database ready." if PRODUCTION else "Database ready. Local demo users: student and admin.")
        return
    if not re.fullmatch(r"[a-zA-Z0-9_.-]{3,32}", args.add_user):
        parser.error("Username must be 3–32 letters, digits, periods, hyphens or underscores.")
    password = getpass.getpass("New password (at least 16 characters): ")
    if not 16 <= len(password) <= 128 or password != getpass.getpass("Repeat password: "):
        parser.error("Invalid password length or passwords do not match.")
    try:
        with connection() as db:
            db.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (args.add_user, make_password_hash(password), args.role),
            )
    except sqlite3.IntegrityError:
        parser.error("That username already exists.")
    print(f"Created {args.role} account {args.add_user}.")


if __name__ == "__main__":
    main()

