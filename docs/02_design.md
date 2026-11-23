# Checkpoint 2 · Planning and design

**PC Build Planner** · Design notes for the 24 November 2026 progress update.

## Navigation and screens

Open the [visual site map](checkpoints/visuals/site-map.svg) and [wireframes](checkpoints/visuals/wireframes.svg). These are drawn from the actual route structure and the review-branch layout.

| Area | Paths and interactions |
|---|---|
| Public | `/` overview, `/login` provisioned-account form. The same home route becomes My builds after sign-in. |
| Authenticated | My builds has Cards/List, saved build links and create. A build detail leads to choose/update/remove items, edit and confirmed deletion. Components lists and filters the shared catalogue. Report shows the owner's build totals, with print and CSV. |
| Admin | The catalogue adds links to create, edit, delete and import pages. The server rechecks the admin role for each action. |
| Owner only | Detail, edit, delete and item actions all require the build owner's ID. Admin has the same ownership restriction. |

| View | Baseline on PythonAnywhere | Claude review candidate |
|---|---|---|
| Home and login | Compact header, introductory block and signed-in cards with a view selector. | Redesigned overview, graphite navigation, local Fira Sans and Cards/List buttons. |
| Build detail | Budget and total above compatibility and selected parts, followed by the part picker. | Parts and picker beside a sticky budget summary on desktop. Mobile orders summary, picker, items and cost breakdown. Status text, categories and amounts carry meaning without colour. |
| Catalogue and report | Search name + category and a printable owner-scoped table. | Updated table, role controls, status feedback and print styling. Existing paths and browser search script retained. |

[Local overview](home_preview.png) · [Local dashboard](dashboard_preview.png) · [Local build detail](build_detail_preview.png) · [Local mobile build](mobile_preview.png) · [Redesign implementation notes](07_interface_redesign.md). Screenshots show the local redesign, while the public classroom app uses the baseline interface.

## Data model

Open the [visual ER diagram](checkpoints/visuals/er-diagram.svg). Its editable text form is [Mermaid](er_diagram.mmd). [The SQL schema](../database/schema.sql) is the implementation source.

| Table | Fields and integrity |
|---|---|
| `users` | Integer PK `id`, required unique `username`, `password_hash`, and `role` constrained to student/admin. |
| `login_sessions` | Text PK `token_digest`, required FK `user_id` and integer `expires_at` in Unix seconds. |
| `categories` | Integer PK `id`, required unique `name`. Fixed reference data protects the category semantics used by the compatibility rules and workflow. |
| `components` | Integer PK `id`, required FK `category_id`, unique name, non-negative integer `price_cents`, optional text `socket` and `ram_type`. |
| `builds` | Integer PK `id`, required owner FK `user_id` and `title`, non-negative integer `budget_cents` default 0, required text `created_at` default current timestamp. |
| `build_items` | Integer PK `id`, required `build_id` / `component_id` FKs, `quantity` defaults to 1 and is constrained to 1–20, unique `(build_id, component_id)`. |

A user can own zero or many builds and sessions. One category can classify many components. A build can contain multiple items and one component can occur in multiple builds. `build_items` implements the many-to-many relationship and stores its own quantity. Each child row references exactly one parent per FK. Build deletion cascades to its items. A component used by any build and a category with components are restricted. Deleting a user at the database level cascades to owned builds and their items, as well as login sessions. There is no user deletion screen.

Prices are integer cents in the catalogue. A live join retrieves prices when computing totals, so a catalogue price change can change a saved build’s subtotal. Zero budget means no limit. Current prices are a design decision for a planner.

## Architecture and technology

[Open the request flow diagram](checkpoints/visuals/request-flow.svg).

| Technology | Why it fits this project |
|---|---|
| FastAPI + Jinja | Python routes can check forms, sessions and roles and render accessible HTML using shared templates. The browser receives server-rendered pages. |
| SQLite | A single persistent database file fits a small demonstration and supports joins, constraints and transactions. The app enables foreign keys per connection. |
| HTML + CSS | Semantic forms, links and tables work with normal navigation. One stylesheet covers responsive layouts and print. |
| JavaScript | A small Fetch enhancement updates catalogue results and print triggers the browser dialog. The regular catalogue GET form is the fallback. |
| PythonAnywhere + a2wsgi | The classroom URL works over HTTPS. The WSGI worker uses an adapter for the FastAPI ASGI app and a SQLite file in the non-public account directory. |

**Example.** Browser POSTs a title, budget and CSRF token to `/builds/new`. FastAPI resolves the session, checks the token and validates input. The SQLite helper opens a transaction with FK enforcement. The route inserts the owner, title and integer cents using bound parameters. A 303 redirect leads to GET build detail. A fresh query scoped to the owner fetches data and Jinja renders the response.

## Repository and work plan

[Private repository](https://github.com/kharchenko-y/pc-build-planner-pw2) · [Redesign source](https://github.com/kharchenko-y/pc-build-planner-pw2/tree/review/claude-redesign) · [HTTPS classroom](https://yarslv.pythonanywhere.com/). Baseline source for the classroom is `main` at `8ac831a`. The visual candidate is based on `2fa2e18`. Both source revisions were checked before these notes were prepared.

1. Establish schema, transactions, sessions and one complete owned build workflow.
2. Integrate catalogue management, search, compatibility, budget, reports and file handling.
3. Review the redesign against actual routes and data. Reproduce role and ownership checks. Record team contributions and finish browser and release evidence before final submission.

Yaroslav is proposed to lead build/data/security review, the partner catalogue/UI and accessibility. Both review each other’s changes and rehearse the full flow. See [contribution record and backlog](05_backlog.md). The checked-in application and these materials include declared AI assistance.
