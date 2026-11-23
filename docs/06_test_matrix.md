# PW2 · Verification matrix

**Session:** 23 November 2026. **Baseline:** `8ac831a`. **Redesign:** `2fa2e18` plus documentation.
A clean Git extraction of the redesign was installed with the bundled local wheel cache into a new Windows virtual environment. Python 3.14.3, FastAPI 0.165.0, Starlette 1.10.0, Uvicorn 0.54.0, SQLite 3.50.4 and pytest 9.2.0. The baseline was separately extracted and tested with the same verified environment. Each run emitted a Starlette/TestClient HTTPX deprecation warning.

| Scope | Expected | Actual and fixture |
|---|---|---|
| Clean extraction | Project installs and initializes a new DB | Redesign dependencies installed from the offline cache. `setup_db.py` completed. |
| Redesign tests | All HTTP and database cases pass | 25 passed, 12 subtests passed. [Output](checkpoints/redesign-tests.txt). |
| Baseline tests | All corresponding cases pass | 24 passed, 12 subtests passed. [Output](checkpoints/baseline-tests.txt). |
| Domain unittest | Money, compatibility, seed, FK, search, CSV and hash cases pass | 9 passed on redesign. [Output](checkpoints/unittest.txt). |
| Schema, integrity and restart | Four domain entities, enforced FKs, valid DB | Probe found all six tables, FK enforcement enabled, negative integrity cases refused, seed re-run preserved data, and integrity checks clean. [Output](checkpoints/sqlite-results.txt). |
| Student sign-in and logout | Valid session, logout invalidates old token | Live signed-in Student verified. Automated logout and rejection of an already-issued token passed. |
| Build create, view and update | A saved build and its parts are read after refresh and can be changed | Live Student created an €800 build, added 3 parts, refreshed, saw €375, renamed and reopened it. |
| Build delete | Confirmation is required and the build disappears after confirmed deletion | Automated missing-confirmation test returns 422 and leaves the record. Confirmed delete returns 303 then detail GET returns 404. SQLite probe confirms cascade and catalogue preservation. Live confirmation opened and cancelled. |
| Role and ownership | Student management routes refused; admin can manage catalogue; other owner refused | Live Student role refusal. Automated student GET and POST refused, admin CRUD and CSV import passed, admin other-owner GET and delete refused. |
| Validation and CSRF | Invalid budget and wrong CSRF rejected and state unchanged | Automated tests passed. Entry and file validation covered with invalid values and duplicate cases. |
| SQL and escaping | SQL-shaped input stays data and HTML-shaped title is escaped | Automated tests passed with no unintended search matches and escaped output. |
| Relationships | Missing FK, duplicate pair, bad quantity and referenced component deletion rejected | Independent disposable SQLite probe passed all cases. |
| Search and reports | AM5 + CPU returns one row; current total appears in report and CSV | Live filter and HTML report confirmed. CSV tested locally. Latest live CSV file was not downloaded. |
| Cookie preference | Cards/List setting persists | Automated test confirms the preference survives logout. |
| Responsive design | Core screens fit mobile, tablet and desktop | Previous redesign checks covered 390, 768 and 1440 px in Chromium-based browsers. [Redesign notes](07_interface_redesign.md). This run verified the Python backend on real FastAPI. |
| Production | HTTPS baseline available; selected operations persist | [Live browser evidence](checkpoints/live-results.txt). Earlier deployment notes recorded HTTP redirect, secure sessions and persistence after worker reload. This recheck left existing data, deployment and worker unchanged. |

Remaining final-release evidence includes a redesigned Linux/hosted check, a second browser engine, HTML/CSS validators, zoom and assistive-technology checks, and repetition from the final submission ZIP. The historical redesign browser run used a Starlette compatibility shim because FastAPI was unavailable in that original environment.
