"""Catalogue filtering and bounded CSV parsing."""
import csv
import io

from domain import clean_specs, component_values

MAX_CSV_BYTES = 32 * 1024
CSV_FIELDS = ["category", "name", "price_eur", "socket", "ram_type"]
CSV_FIELDS_WITH_SPECS = [*CSV_FIELDS, "specs"]
INSERT_COMPONENT = """
    INSERT INTO components (category_id, name, price_cents, socket, ram_type, specs)
    VALUES (?, ?, ?, ?, ?, ?)
"""


def lookup(db, query, category):
    """Match the text against name, socket, memory type and key specifications."""
    pattern = "%" + query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
    return db.execute(
        """SELECT c.*, cat.name AS category FROM components c
           JOIN categories cat ON cat.id = c.category_id
           WHERE (c.name LIKE ? ESCAPE '\\' OR c.socket LIKE ? ESCAPE '\\'
                  OR c.ram_type LIKE ? ESCAPE '\\' OR c.specs LIKE ? ESCAPE '\\')
             AND (? = '' OR cat.name = ?)
           ORDER BY cat.id, c.price_cents, c.name""",
        (pattern, pattern, pattern, pattern, category, category),
    ).fetchall()


def csv_rows(raw, categories):
    """Parse an import file. The specs column is optional so older files still work."""
    if len(raw) > MAX_CSV_BYTES:
        raise ValueError("Choose a CSV file no larger than 32 KiB.")
    try:
        rows = csv.reader(io.StringIO(raw.decode("utf-8-sig"), newline=""), strict=True)
        header = next(rows, None)
        if header not in (CSV_FIELDS, CSV_FIELDS_WITH_SPECS):
            raise ValueError("The CSV header must match the example file.")
        result = []
        for row in rows:
            if not row:
                continue
            if len(result) == 50:
                raise ValueError("Import at most 50 components per file.")
            if len(row) != len(header):
                raise ValueError(f"Line {rows.line_num} has the wrong number of columns.")
            category, name, price, socket, ram_type, *extra = row
            category = category.strip()
            if category not in categories:
                raise ValueError(f"Line {rows.line_num} has an unknown category.")
            try:
                values = component_values(category, name, price.strip(), socket, ram_type)
                specs = clean_specs(extra[0] if extra else "")
            except ValueError as exc:
                raise ValueError(f"Line {rows.line_num}: {exc}") from exc
            result.append((categories[category], *values, specs))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise ValueError("The file must be a valid UTF-8 CSV.") from exc
    if not result:
        raise ValueError("Include at least one component.")
    return result
