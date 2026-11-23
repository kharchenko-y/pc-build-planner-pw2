# PW2 Test Matrix

This matrix records checks for the current work in progress. The archived starter test result applies only to its original snapshot.

| Area | Expected result | Evidence for this version |
|---|---|---|
| SQLite initialization and restart | Seed catalogue stays stable and builds survive reinitialization | Local Python/SQLite test passed |
| Relationships | SQLite restricts referenced parts and cascades build items | Local Python/SQLite test passed |
| Money and compatibility | Valid amounts become integer cents. Invalid amounts and mismatches are handled | Local domain tests passed |
| Combined filter | Name and category both apply. Wildcards are literal input | Local SQLite test passed |
| CSV validation and rollback | Invalid files fail. A duplicate rolls back the import | Local parser and SQLite tests passed |
| Password storage | Different salts per hash and valid verification | Local Python test passed |
| Build CRUD and authorization | Owner can save and delete; other users cannot access the build | HTTP integration and live browser checks pending |
| Catalogue CRUD / import | Admin can create, edit, delete and import. Student is refused | HTTP integration and live browser checks pending |
| Login and logout | New session at login, old token invalid after logout | HTTP integration and live browser checks pending |
| Cookie preference | Selection remains on reload and lasts 30 days | HTTP integration and live browser checks pending |
| Async search | Search updates the table without page navigation. GET fallback works | Browser test pending |
| Report | Current totals and print view; CSV opens in spreadsheet software | Browser and file checks pending |
| Validity and accessibility | Valid markup. Keyboard/zoom and focus work | HTML/CSS validators, keyboard, zoom, contrast and labels pending |
| Responsive testing | Practical desktop, tablet and mobile sizes. Table scroll stays local | Two current browsers with names and versions pending |
| Deployment | HTTPS URL works in private window and data remains after reload/redeploy | Pending authenticated hosting setup and live checks |
| Clean ZIP installation | The README works from a fresh extraction | Pending full dependency install and HTTP smoke test |
