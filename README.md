# PC Build Planner — PW2 prototype

**Status: work in progress, not a final submission.** Prepared as a starting point for the team's implementation and discussion with the lecturer.

## Purpose

A small web application for people planning a desktop PC. Users create builds, choose components from a catalogue, and see a price total based on database records. Administrators can add catalogue components.

## Stack

- Python 3.11+ / FastAPI / Jinja2 (server-rendered HTML)
- SQLite relational database
- Plain CSS, small browser JavaScript for print and delete confirmation
- No external product APIs, paid services or frontend framework

## Local setup (Windows)

Open the project directory in PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python setup_db.py
python -m uvicorn app:app --reload
```

Open **http://127.0.0.1:8000**. Do not open an HTML template as a local file — the database app needs a Python server.

Local demonstration accounts (not for public deployment):

- `student` / `demo12345`
- `admin` / `demo12345`

The `admin` account can add catalogue components; student cannot. Both can create and manage their own builds. Change all demo credentials and `SESSION_SECRET` before any public hosting.

## Test a complete workflow

1. Log in as `student`.
2. Select **Create a build**, enter `My first PC`, budget `900`, and save.
3. In the detail page, add `Demo CPU AM5` and `Demo motherboard AM5`.
4. Check that the total increases by the sum of their prices.
5. Edit the build name, remove an item, and optionally delete the build.
6. Open **Components** and try filtering by name and category.
7. Open **Report** and use Print or Download CSV.
8. Log in as `admin` to see the additional Add component page.

## Files

- `app.py`: request handlers / routes
- `db.py`: SQLite connection and password hashing helpers
- `database/schema.sql`: tables and constraints
- `setup_db.py`: initializes the local database and demo records
- `templates/`: HTML generated on the server
- `static/styles.css`: styling and responsiveness
- `docs/`: requirements, ER diagram, backlog and lesson walkthrough
- `tests/`: automated checks for the starter

## Current features

- Login/logout with PBKDF2 password hashing and signed session cookie
- Separate student/admin roles for catalogue modifications
- Own-build access checks, CSRF form tokens, SQL parameters
- Complete create/read/update/delete workflow for saved builds
- Add/remove saved components; calculation of the total cost
- Search and category filter using joined database tables
- Print-friendly and CSV reports
- Responsive layout and form labels

## Not yet complete for the PW2 rubric

- User sign-up or lecturer-approved account provisioning (demo accounts only)
- Complete catalogue/category CRUD, editing all build fields, more polished UI states
- Actual CPU/motherboard/RAM compatibility rules (not implemented)
- Documented non-sensitive preference cookie and its lifetime
- Required asynchronous/file-processing scope — must be clarified and implemented
- Broader security tests and deployment hardening (HTTPS, secure cookies, session lifecycle)
- Testing matrix, documentation, contribution logs, presentation/video and final report
- Both students must review, modify, test and explain this code and contribute through Git

**Demo data warning:** the prices and products in `setup_db.py` are synthetic, not live retail information. Totals are not shopping recommendations.

## Academic process

The assignment requires approval of project topic/stack, five progress checkpoints, evidence of both members' contributions, and disclosure of material AI assistance. Agree on how to document assistance with the lecturer. Do not claim a generated prototype was independently authored by both students.

## Checks of this starter snapshot

- 10 automated pytest checks passed in the preparation environment on 23 November 2026.
- Server returned HTTP 200 for the public home page; HTML/CSS screenshots were rendered separately for visual review.
- Browser-based end-to-end testing in your own Chrome/Edge, along with full security testing, is still required.
- Quick test command: `python -m pytest -q tests` (install `pytest`, `httpx` and `beautifulsoup4` for the developer test environment).
