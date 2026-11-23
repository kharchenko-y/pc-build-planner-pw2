# Checkpoint 3 · Database and core backend

**Evidence prepared 23 November 2026 for the 24 November update.** The assignment asks for a schema, connection, authentication foundation and first working CRUD flow. Open the [ER diagram](visuals/er-diagram.svg) and [request diagram](visuals/request-flow.svg).

## What works and where it is proved

| Evidence | What to show |
|---|---|
| Schema and relation integrity | [SQL schema](../../database/schema.sql), [SQLite verification](sqlite-results.txt). The subject has four domain tables: categories, components, builds and build_items. There are two separate authentication tables. |
| Application connection | [db.py](../../db.py) opens SQLite and enables FK enforcement. `with connection()` commits on success, rolls back on errors and closes the connection. `PCBUILDER_DB` points to private persistent storage in production. |
| Live user flow | [HTTPS app](https://yarslv.pythonanywhere.com/), [live notes](live-results.txt). Student session confirmed. Created a separate €800 demo build, added three parts, saw €375 after refresh, renamed the build, opened its delete confirmation, cancelled and re-opened the saved build. |
| Complete CRUD | [HTTP integration tests](../../tests/test_app.py) exercise actual FastAPI routes and disposable SQLite files. A confirmed delete removes a test build, while unconfirmed deletion is refused. SQLite test also confirms the dependent row is removed and a referenced catalogue record is protected. |
| Both roles and privacy | Student direct navigation to `/components/new` was refused live. Integration tests prove admin catalogue management and deny access to another owner’s build for reading and mutation. |
| Supporting workflows | Live AM5 + CPU filter returned exactly Demo CPU AM5, the report displayed the revised build's €375 row, and the two compatibility comparisons matched. |
| Automated results | [Fresh redesign suite](redesign-tests.txt) · [baseline suite](baseline-tests.txt) · [test matrix](../06_test_matrix.md). The fresh redesign run uses real FastAPI with wheels installed into a new environment. |

## Security evidence

| Mechanism | Location and negative evidence |
|---|---|
| Parameter binding | `owned_build` and write routes in `app.py`, catalogue `lookup` in `catalogue.py`. SQL values are passed as parameters. A SQL-shaped search remains input in the test and yields no matches. |
| Server-side roles and ownership | `require_admin`, `require_user`, and `owned_build` in `app.py`. Student management attempt fails, anonymous protected access fails, other-owner build access results in 404. |
| Escaping and CSP | Jinja HTML output escapes a markup-shaped name in integration tests. Middleware sets a self-only CSP. |
| CSRF and safe mutators | `check_token` checks a per-session token, mutations use POST and an explicit confirmation value for deletion. An invalid CSRF token is rejected in the HTTP test. Successful changes use 303 redirects. |
| Credentials and session lifecycle | Salted PBKDF2-HMAC-SHA256 in `db.py`, fresh random session token and two-hour expiry in `app.py`. SQLite stores its digest. Logout deletes the corresponding row and clears the cookie. A previously issued session is rejected in the automated test. |

The published site serves the baseline interface. The tested Claude candidate remains on its review branch. Production deletes and reloads were skipped during this recheck. Lecturer approval of the topic/stack, account provisioning and any make-up assessment remains to be confirmed.
