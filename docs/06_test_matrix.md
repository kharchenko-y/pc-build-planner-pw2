# PW2 Test Matrix

The hosted classroom build was verified on 23 November 2026. A clean install on PythonAnywhere with Python 3.13.1 ran `python -m pytest -q` and reported 24 passed and 12 subtests passed. The one warning came from Starlette's test client dependency.

| Area | Expected result | Evidence for this version |
|---|---|---|
| SQLite initialization and restart | Seed catalogue stays stable and builds survive reinitialization | Local Python/SQLite test passed |
| Relationships | SQLite restricts referenced parts and cascades build items | Local Python/SQLite test passed |
| Money and compatibility | Valid amounts become integer cents. Invalid amounts and mismatches are handled | Local domain tests passed |
| Combined filter | Name and category both apply. Wildcards are literal input | Local SQLite test passed |
| CSV validation and rollback | Invalid files fail. A duplicate rolls back the import | Local parser and SQLite tests passed |
| Password storage | Different salts per hash and valid verification | Local Python test passed |
| Build CRUD and authorization | Owner can save and delete. Other users cannot access the build | Automated tests passed. Live creation, edit and owner isolation passed |
| Catalogue CRUD and import | Admin can maintain the catalogue. Student is refused | Automated tests passed. Live import page access matched role permissions |
| Login and logout | New session at login. Old token invalid after logout | Automated tests passed. Live login, logout and denied access after logout passed |
| Cookie preference | Selection stays set when navigating | Automated test passed. Redesign: List selection stayed after navigating in Chromium 157 and Chrome 153 |
| Async search | Search updates the table without page navigation | Live browser filter for AM5 in CPU category returned one correct result |
| Report | Current total is visible, with print and CSV controls | Live report and CSV contained the saved €375.00 total. Redesign: local report and CSV showed €375.00; print media hides navigation and buttons (PDF preview generated). Physical printing and spreadsheet import pending |
| Validity and accessibility | Valid markup. Keyboard/zoom and focus work | Redesign: local nesting/duplicate-id check passed on 15 pages; labels, describedby targets and one `h1` checked per page; skip link and visible 3 px focus checked; contrast measured (text ≥ 4.6:1). W3C validators, zoom and screen reader pending |
| Responsive testing | Practical desktop, tablet and mobile sizes. Table scroll stays local | Redesign: builds, build detail, catalogue, report, forms, login and home checked at 390, 768 and 1440 px with no page-level horizontal scroll. Parts list stacks below 720 px. Firefox and Safari pending |
| Deployment | HTTPS responds, HTTP redirects and data stays after restart | Live HTTPS 200, HTTP redirect and Secure/HttpOnly session cookie verified. The saved build remained visible after restarting the WSGI worker |
| Clean ZIP installation | Dependencies install and the service starts from the archive | PythonAnywhere clean extraction, dependency install and test suite passed. The updated worker adapter was verified against the live app |

## Interface redesign, 23 November 2026

The redesign was verified locally in an offline sandbox. FastAPI could not be installed there, so the tests and the server ran through a small compatibility shim outside the project. The unchanged baseline reproduced 24 passed and 12 subtests passed under that shim. After the redesign the suite reported **25 passed and 12 subtests passed** (one new test for the €375.00 summary). A scripted browser walkthrough passed 76 of 76 checks in Playwright Chromium 157.0.8103.78 and in Chrome for Testing 153.0.8010.12. Details: [test_results_redesign_2026-11-23.txt](test_results_redesign_2026-11-23.txt) and [07_interface_redesign.md](07_interface_redesign.md).

| Area | Expected result | Evidence for the redesign |
|---|---|---|
| €375.00 example | €800 budget with Demo CPU AM5, Demo motherboard AM5 and 16 GB DDR5 demo kit | Summary shows €375.00, €425.00 left and Compatible. Report and CSV show 375.00 |
| Quantity and removal | Quantity changes the total. Removal needs confirmation | SSD ×2 gave €525.00; confirmed removal returned €375.00 |
| Over budget and mismatch | Clear status | €300 budget with LGA1700 CPU, AM5 board and DDR4 kit shows Over by €45.00 and two mismatch messages |
| Async and plain search | AM5 in CPU returns one part | Fetch update without reload; with JavaScript disabled the form submits normally |
| Roles | Admin manages catalogue, student cannot | Admin sees Add, Import, Edit and Delete and imported a CSV; student sees none and gets 403 on `/components/new` |
| Errors and empty states | Understandable messages and next step | 401, 404, 409, invalid budget, invalid CSV header, no search results, no builds and no parts checked |
| Console | No unexpected errors | None apart from the intentional 401, 404 and 409 responses |
