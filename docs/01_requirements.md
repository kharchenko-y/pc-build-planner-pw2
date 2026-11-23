# Checkpoint 1 · Research and requirements

**PC Build Planner** · Vilnius University · WWW Development Technologies · Practical Work II
**Evidence prepared for 24 November 2026.** Checkpoint presentation and acceptance are for the lecturer to confirm. The first two scheduled updates were missed.

## Problem and users

A beginner who plans a desktop PC needs to combine parts, keep the price total within a budget and spot basic socket and memory conflicts before comparing options. A note or spreadsheet can hold a list, but the user has to keep prices in sync, recreate the same parts across builds and interpret each specification manually. This project gives the user a saved configuration, a shared catalogue, an automatic budget calculation and two explainable compatibility checks.

| Actor | Goal and access |
|---|---|
| Visitor | Read what the tool does and reach the login form. |
| Student / beginner builder | Sign in, keep multiple private builds, choose parts, find examples by name and category, and print or export current totals. |
| Catalogue administrator | Curate example parts and import sample records. Builds still belong to their individual owners, including when the owner is an admin. |

## Comparable solutions

| Source | Observed features | Decision for PC Build Planner |
|---|---|---|
| [PCPartPicker](https://pcpartpicker.com/) ([official service description](https://discord.com/servers/pcpartpicker-197079805710041088)) | Part selection, compatibility and pricing guidance for DIY builders. | Keep a category-led part chooser, a total and a compatibility result within one saved build. |
| [Pangoly PC Builder](https://pangoly.com/en/pc-builder) and [Pangoly’s builder overview](https://pangoly.com/en/blog/comment/164) | Category-led builds, starting configurations, seller/price columns and compatibility guidance. | Keep editable example parts and explain the two supported rules alongside the result. |

Sources consulted 23 November 2026. The PCPartPicker homepage was unavailable to the research fetch, so the feature description is grounded in its official staff-run community listing. Pangoly's builder and product overview were available. The project uses its own application screens and example catalogue. Retailer feeds, buying, benchmarking, public sharing, BIOS support, physical clearance and PSU sizing are outside current scope. A small synthetic catalogue keeps the demonstration reproducible and lets both students explain the relational model and the exact policy behind every warning.

## Functional requirements

| ID | Requirement | Acceptance evidence |
|---|---|---|
| F01 | Use provisioned login/logout and two permission levels. | Anonymous protected route is denied. Student cannot open catalogue write routes. Admin can manage catalogue entries. |
| F02 | Create, open, rename, change the budget and explicitly confirm deletion of an owned build. | Saved build survives refresh. A different user gets 404. Local test verifies creation through deletion. |
| F03 | Add a part by name, adjust quantity where allowed and confirm removal. | Linked items appear in the build. Duplicate part rejected, invalid quantity refused and a selected part cannot be deleted from the catalogue. |
| F04 | Filter the catalogue by component name and category. | Searching AM5 + CPU returns Demo CPU AM5. Fetch enhances the standard GET form. |
| F05 | Calculate current total against budget and report limited compatibility. | €190 + €130 + €55 = €375 on an €800 build. The two checks compare CPU socket and memory generation against the motherboard. |
| F06 | Print and export current build totals. | Report and CSV include the same €375 example. |
| F07 | Maintain catalogue parts and import CSV as admin. | Add/edit/delete an unused part. A conflicting import rolls back. Fixed categories are reference data. |
| F08 | Store the Cards/List preference. | A 30-day non-sensitive cookie persists the selected view. |

## Non-functional requirements

| ID | Requirement | Acceptance evidence |
|---|---|---|
| N01 | Preserve referential integrity and persist data. | Foreign keys enabled on every app connection. Invalid links are rejected, build items cascade and in-use parts are restricted. |
| N02 | Validate input and enforce security on the server. | Bound values in SQL, escaped Jinja output, per-session CSRF token, salted password hashes, new revocable login token, owner/role checks and production HTTPS cookie controls. Negative checks in the test matrix. |
| N03 | Keep the main workflows usable on mobile, tablet and desktop. | Semantic controls, navigation, visible focus, readable feedback and no page-wide overflow at the tested viewports. Final browser/validator coverage remains open. |
| N04 | Provide a reproducible, explainable setup. | A fresh extraction can install dependencies, create the demo database and run tests using the README. Scope and AI assistance are declared. |
| N05 | Keep demonstration data safe. | Synthetic prices and parts, separate learner/admin credentials, protected SQLite file and runtime settings outside public/static directories. |

## Use cases

1. **Plan a build.** A signed-in student creates an €800 build, picks an AM5 CPU, matching board and DDR5 kit, then reads the €375 result. Reopening the page shows the saved build. A bad amount results in feedback and an unmatched socket results in a warning.
2. **Maintain the catalogue.** An admin creates a part in an existing category and edits its price. The catalogue shows the new value. A part linked to a build receives a conflict response on deletion. Students can search the catalogue and are refused on its write routes.
3. **Report current costs.** A signed-in owner opens Report and prints or downloads their build totals. Prices reflect the current catalogue, so a price edit can change an existing build’s current total.

## Initial priorities and responsibilities

| Priority | Work | Evidence |
|---|---|---|
| P0 | Schema, authentication, role and ownership checks, owned build CRUD, named part picker | SQL schema, live and local checks |
| P1 | Catalogue maintenance, two-criteria search, calculations, compatibility, print and CSV, preference | Application routes and integration tests |
| P2 | Responsive redesign review, browser/accessibility and validation coverage, release documentation | Review branch, test matrix and release backlog |

These priorities reconstruct the design rationale for the catch-up presentation. See [live backlog and contribution record](05_backlog.md) for future work and confirmed activity. Proposed division: Yaroslav leads database/build/security review, the partner leads catalogue and UI/accessibility review, and both reproduce tests, review each other’s evidence and rehearse. Log only actions, reviews, and commits each student can substantiate. Design, implementation and documentation received material AI assistance.

**Talk and visuals:** [Checkpoint deck](checkpoints/slides.html) and [speaking guide](03_tomorrow_checkpoint.md).
