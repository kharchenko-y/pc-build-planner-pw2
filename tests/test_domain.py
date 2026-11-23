import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from catalogue import INSERT_COMPONENT, csv_rows, lookup
from db import DEMO_NAMES, connection, init_database, make_password_hash, verify_password
from domain import compatibility, component_values, money_cents, part_fit


class DomainTests(unittest.TestCase):
    def test_amounts_are_stored_as_cents(self):
        self.assertEqual(money_cents("139.90"), 13990)
        self.assertEqual(money_cents("0"), 0)
        self.assertEqual(money_cents("100000"), 10000000)
        for invalid in ("", "NaN", "Infinity", "1e2", "-1", "9.999", "100001"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                money_cents(invalid)

    def test_category_specific_specs(self):
        self.assertEqual(
            component_values("Motherboard", "B650 board", "129.99", "am5", "ddr5"),
            ("B650 board", 12999, "AM5", "DDR5"),
        )
        with self.assertRaises(ValueError):
            component_values("RAM", "Example", "29", "AM5", "DDR5")

    def test_incompatible_socket_and_memory(self):
        items = [
            {"category": "Motherboard", "socket": "AM5", "ram_type": "DDR5"},
            {"category": "CPU", "socket": "LGA1700", "ram_type": None},
            {"category": "RAM", "socket": None, "ram_type": "DDR4"},
        ]
        warnings, status = compatibility(items)
        self.assertEqual(len(warnings), 2)
        self.assertEqual(status, "")
        self.assertIn("does not match", warnings[0])
        self.assertIn("does not match", warnings[1])
        items[1]["socket"] = "AM5"
        items[2]["ram_type"] = "DDR5"
        self.assertEqual(compatibility(items), ([], "CPU socket and RAM generation match the motherboard."))
        self.assertIn("Remove duplicate", compatibility([*items, items[1]])[0][0])
        self.assertIn("Complete both checks", compatibility(items[:1])[1])

    def test_warnings_and_fit_name_the_parts(self):
        items = [
            {"category": "Motherboard", "name": "Board X", "socket": "AM5", "ram_type": "DDR5"},
            {"category": "CPU", "name": "CPU Y", "socket": "LGA1700", "ram_type": None},
        ]
        warning = compatibility(items)[0][0]
        self.assertIn("CPU Y uses socket LGA1700", warning)
        self.assertIn("AM5 socket on Board X", warning)
        self.assertEqual(part_fit({"category": "CPU", "socket": "AM5", "ram_type": None}, items)[0], "ok")
        self.assertEqual(part_fit({"category": "RAM", "socket": None, "ram_type": "DDR4"}, items)[0], "bad")
        self.assertEqual(part_fit({"category": "Motherboard", "socket": "AM5", "ram_type": "DDR5"}, items)[0], "bad")
        self.assertIsNone(part_fit({"category": "GPU", "socket": None, "ram_type": None}, items))

    def test_csv_input_validation(self):
        header = b"category,name,price_eur,socket,ram_type\n"
        self.assertEqual(csv_rows(header + b"CPU,A new CPU,19.95,AM5,\n", {"CPU": 1}), [(1, "A new CPU", 1995, "AM5", None, "")])
        with_specs = b"category,name,price_eur,socket,ram_type,specs\nCPU,A new CPU,19.95,AM5,,8 cores;  65 W\n"
        self.assertEqual(csv_rows(with_specs, {"CPU": 1})[0][-1], "8 cores; 65 W")
        for invalid in (b"bad header\n", header + b"Unknown,A CPU,19.95,AM5,\n", header + b"CPU,A CPU,19.95,,\n", b"\x80", b"a" * 32769):
            with self.subTest(invalid=invalid[:30]), self.assertRaises(ValueError):
                csv_rows(invalid, {"CPU": 1})


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        path = str(Path(folder.name) / "test.sqlite3")
        environment = patch.dict("os.environ", PCBUILDER_DB=path)
        environment.start()
        self.addCleanup(environment.stop)
        init_database()

    def test_seed_and_restart(self):
        with connection() as db:
            db.execute("INSERT INTO builds (user_id, title) VALUES (?, ?)", (1, "Saved build"))
        init_database()
        with connection() as db:
            self.assertEqual(db.execute("SELECT title FROM builds").fetchone()[0], "Saved build")
            self.assertEqual(db.execute("SELECT COUNT(*) FROM components").fetchone()[0], 27)

    def test_foreign_key_restrict_and_cascade(self):
        with connection() as db:
            build = db.execute("INSERT INTO builds (user_id, title) VALUES (?, ?)", (1, "Saved build")).lastrowid
            db.execute("INSERT INTO build_items (build_id, component_id) VALUES (?, ?)", (build, 1))
        with self.assertRaises(sqlite3.IntegrityError), connection() as db:
            db.execute("DELETE FROM components WHERE id = ?", (1,))
        with connection() as db:
            db.execute("DELETE FROM builds WHERE id = ?", (build,))
            self.assertEqual(db.execute("SELECT COUNT(*) FROM build_items").fetchone()[0], 0)

    def test_two_criteria_search_and_literal_wildcards(self):
        with connection() as db:
            self.assertEqual(
                [row["name"] for row in lookup(db, "AM5", "CPU")],
                ["AMD Ryzen 5 7600", "AMD Ryzen 7 9700X", "AMD Ryzen 7 7800X3D"],
            )
            self.assertEqual([row["name"] for row in lookup(db, "DDR4", "Motherboard")][0], "MSI B550M PRO-VDH WIFI")
            self.assertEqual(lookup(db, "%", ""), [])
            self.assertEqual(lookup(db, "_", ""), [])
            self.assertEqual(lookup(db, "' OR 1=1 --", ""), [])

    def test_csv_transaction_rolls_back_on_conflict(self):
        with self.assertRaises(sqlite3.IntegrityError), connection() as db:
            db.executemany(INSERT_COMPONENT, [
                (1, "Previously nonexistent CPU", 2000, "AM5", None, ""),
                (1, "AMD Ryzen 5 7600", 19000, "AM5", None, ""),
            ])
        with connection() as db:
            self.assertEqual(lookup(db, "Previously nonexistent", "CPU"), [])

    def test_demo_catalogue_is_upgraded_in_place(self):
        with connection() as db:
            for old, new in DEMO_NAMES.items():
                db.execute("UPDATE components SET name = ? WHERE name = ?", (old, new))
            db.execute("DELETE FROM components WHERE id > 10")
            db.execute("ALTER TABLE components DROP COLUMN specs")
            build = db.execute("INSERT INTO builds (user_id, title) VALUES (?, ?)", (1, "Old build")).lastrowid
            db.execute("INSERT INTO build_items (build_id, component_id) VALUES (?, ?)", (build, 1))
        init_database()
        with connection() as db:
            name = db.execute("SELECT c.name FROM build_items bi JOIN components c ON c.id = bi.component_id").fetchone()[0]
            self.assertEqual(name, "AMD Ryzen 5 7600")
            self.assertEqual(db.execute("SELECT COUNT(*) FROM components").fetchone()[0], 27)
            self.assertIn("65 W TDP", db.execute("SELECT specs FROM components WHERE id = 1").fetchone()[0])

    def test_password_hash_is_salted_and_verifiable(self):
        first = make_password_hash("classroom test password")
        self.assertNotEqual(first, make_password_hash("classroom test password"))
        self.assertTrue(verify_password("classroom test password", first))
        self.assertFalse(verify_password("wrong password", first))


if __name__ == "__main__":
    unittest.main()
