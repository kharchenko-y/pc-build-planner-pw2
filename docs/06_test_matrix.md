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
| Cookie preference | Selection stays set when navigating | Automated test passed. Browser preference check pending |
| Async search | Search updates the table without page navigation | Live browser filter for AM5 in CPU category returned one correct result |
| Report | Current total is visible, with print and CSV controls | Live report and CSV contained the saved €375.00 total. Print preview and spreadsheet import pending |
| Validity and accessibility | Valid markup. Keyboard/zoom and focus work | HTML/CSS validators, keyboard, zoom, contrast and labels pending |
| Responsive testing | Practical desktop, tablet and mobile sizes. Table scroll stays local | Live report fit a 390 px browser viewport. Additional browser and page checks pending |
| Deployment | HTTPS responds, HTTP redirects and data stays after restart | Live HTTPS 200, HTTP redirect and Secure/HttpOnly session cookie verified. The saved build remained visible after restarting the WSGI worker |
| Clean ZIP installation | Dependencies install and the service starts from the archive | PythonAnywhere clean extraction, dependency install and test suite passed. The updated worker adapter was verified against the live app |
