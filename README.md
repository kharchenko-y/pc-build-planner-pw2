# PC Build Planner

A Vilnius University Practical Work II application for saving desktop PC configurations and comparing their cost against a budget. Catalogue administrators maintain the parts list. Prices and parts in the seed catalogue are illustrative.

## Run locally

Use Python 3.11 or newer. From the extracted project directory in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe setup_db.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. The local seed accounts are `student` and `admin`, both with password `demo12345`. In production, the bootstrap command creates separate accounts with random passwords; the application rejects a database containing the original default accounts during initialization.

## Features

- Students create, open, edit and delete their own builds. They choose parts by name and update quantities for applicable parts.
- The catalogue combines a name search with a category filter. The search uses Fetch when JavaScript is available. The regular form works without JavaScript.
- Administrators can create, edit, delete and import catalogue parts. A component used in a build cannot be deleted. Category names are fixed reference data for the compatibility rules.
- Build totals are calculated from the current catalogue price in integer cents multiplied by quantities. Saved builds reflect changes to catalogue prices.
- Compatibility checks compare CPU socket and RAM generation to the motherboard. The display calls out missing data or mismatches. It does not check BIOS, physical clearance, cooling, power supply, or other hardware requirements.
- Users can print a current report and download a CSV. The administrator CSV importer checks headers, UTF-8, row count and file size. The import commits all rows together.
- A 30-day `pcbuild_view` cookie stores the user's Cards or List preference.

## Architecture and security

| File | Responsibility |
|---|---|
| `app.py` | FastAPI routes, server-rendered views, validation and access checks |
| `config.py` | Runtime environment rules |
| `db.py` and `database/schema.sql` | SQLite connections, password hashes, schema and seeds |
| `domain.py` and `catalogue.py` | Money and compatibility rules, search and CSV import |
| `templates/` and `static/` | English HTML, CSS and browser interactions |
| `tests/` | Python/SQLite checks and HTTP integration tests |

SQL statements bind input values. Jinja escapes HTML text. Forms use CSRF tokens, logout invalidates the server-side session, and production cookies are Secure, HttpOnly and SameSite=Lax. Server-side login records expire after two hours. Build access is scoped to the owner, and catalogue writes require the admin role. Public use is intended for a small classroom demonstration with synthetic data. Accounts are provisioned by the operator; the lecturer must approve this workflow for the final submission.

## Deployment

Follow [the PythonAnywhere guide](deploy/README.md) for free HTTPS hosting using `a2wsgi` and persistent SQLite. Keep credentials, runtime configuration and the database outside static directories and source control. The web app must run in production mode on the host.

The [classroom deployment](https://yarslv.pythonanywhere.com/) was verified on 23 November 2026. The hosting dashboard shows an expiry date of 23 December 2026. Sign in with the provisioned classroom account and open **Campus PC Demo** to see the verified €375.00 example. The hosting account owner can retrieve the demo password from the private deployment folder.

## Test commands and materials

- `python -m pytest -q` runs all tests with development dependencies installed.
- `python -m unittest discover -s tests -p test_domain.py -v` runs Python/SQLite tests without external test dependencies.
- [Checkpoint script](docs/03_tomorrow_checkpoint.md), [learning guide in Russian](docs/04_learning_guide_RU.md), [test matrix](docs/06_test_matrix.md), [ER diagram](docs/er_diagram.mmd).

## Dependencies and attribution

Python 3.11+, SQLite from Python, FastAPI, Uvicorn, Jinja2, python-multipart, itsdangerous and a2wsgi. Development dependencies are pytest, HTTPX and Beautiful Soup. Supported dependency ranges are listed in the requirements files. The HTML, CSS, seed data and diagrams are project materials. They use no external media.

Material AI assistance was used for the initial prototype, code changes and documentation. The team must review, test and explain each submitted feature. The project registration must carry both students’ actual names. Record each person's completed contribution and corresponding commits in [the contribution log](docs/05_backlog.md). Add the approved team credit and contact email before final submission.
