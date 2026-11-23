# Builder redesign (24 November 2026)

The earlier interface worked, but it read like a database form: one long drop-down for every part, a table of rows and a report that repeated the build list. This iteration changes the user flow around the job a builder actually does: fill seven part slots, keep an eye on the budget and fix conflicts as soon as they appear.

## What changed for the user

| Screen | Before | Now |
|---|---|---|
| My builds | Cards with a total | A short form starts a build directly. Each build shows total, budget, a strip of seven slot drawings (filled or empty), the parts still missing and the check result. Cards and List remain as the cookie preference. |
| Build editor | Drop-down of all parts and a table | Seven slots in assembly order: processor, motherboard, memory, graphics card, storage, power supply, case. An empty slot says why it matters and offers **Choose …**. The next empty slot is highlighted. Filled slots show model, key specifications, socket or memory type, price, **Change** and **Remove**. Parts involved in a conflict are marked in their slot. |
| Summary | Light panel | A dark summary panel stays beside the slots on desktop: total, budget, remaining or over amount, progress, both checks with concrete text, budget change in place, print and CSV. On phones a compact total bar stays at the bottom of the screen. |
| Choosing a part | Pick from the drop-down, remove before replacing | **Choose** opens the catalogue filtered to that slot for that build. Each part shows whether it fits the parts already chosen and what the total becomes. Fitting parts are listed first. A filled single slot offers **Replace**, which swaps the part in one step. |
| Catalogue | Table | Category list with part drawings and counts, one search box (model, socket, memory type or specification), parts grouped by category. Choosing a build in the catalogue turns on Add buttons and fit hints. Administrators get a separate admin bar and Edit/Delete links. |
| Reports | Same totals as My builds | A printable parts sheet per build: every slot (including empty ones), quantities, unit prices, subtotals, budget figures and both check results. CSV export lists the same items per build. |

## Visual direction

- Light neutral page, white sheets, near-black ink and one blue for actions. Green, amber and red only for states.
- The one strong element is the dark summary panel next to the slots.
- Seven project-made line drawings of parts (`static/parts.svg`) identify slots, catalogue categories and build progress. Product photos were not used because they belong to manufacturers and shops.
- Fira Sans (already in the project) with tabular figures for prices. Small radii, no gradients, shadows only on floating elements.

## Backend changes

| File | Change and reason |
|---|---|
| `database/seed_components.csv` | 27 real parts with key specifications. The CSV uses the importer format, so the seed is validated by the same code as an upload. |
| `database/schema.sql`, `db.py` | New `specs` column. On an existing database `init_database()` adds the column, renames the ten placeholder parts in place (IDs and saved builds stay valid) and adds the remaining real parts once. |
| `catalogue.py` | Search also matches socket, memory type and specifications. The import header may include an optional `specs` column. |
| `domain.py` | Slot order and labels, single-slot rule (storage may hold several drives), quantity limits, check rows with part names, and `part_fit()` for catalogue hints. |
| `app.py` | Build summaries for My builds and Reports, slot data for the editor, `replace=yes` on the existing add route, build context in the catalogue, itemised CSV. Routes, CSRF, sessions, ownership and role checks are unchanged. |

Compatibility still covers exactly two rules: CPU socket against the motherboard and memory type against the motherboard. The interface states what is not checked (power supply wattage, cooler, BIOS version, case fit).

## Data sources

Specifications were checked on 24 November 2026 against manufacturer pages: AMD (Ryzen 5 7600, Ryzen 7 9700X, Ryzen 7 7800X3D), Intel (Core i5-14400F, i5-12400F), MSI, ASUS, Sapphire, NVIDIA, Samsung, Crucial, Seagate, be quiet!, Corsair, Seasonic, Cooler Master, Fractal Design and NZXT. Memory kits and the Ryzen 5 5600 were cross-checked with retailer listings of the exact part numbers. Prices are demonstration values and are marked as such in the interface.

## Verification

- `python -m pytest -q`: 30 passed, 12 subtests passed. `python -m unittest discover -s tests -p test_domain.py`: 11 tests OK.
- Scripted browser walkthrough at 1440, 768 and 390 px: 66 of 66 checks passed in Playwright Chromium 157 and in Chrome for Testing 153. It covers the €375.00 example, replace with a concrete mismatch, quantities, removal, budget change, async search, Cards/List cookie, report, print, CSV, roles, import, errors and console/CSP messages. With JavaScript disabled, search, Add, Replace and Remove still work as plain forms. Main text and state colours reach at least 4.5:1 contrast.
- The local environment could not install FastAPI, so it ran through a small Starlette-based compatibility shim outside the project. Re-run the tests after installing `requirements-dev.txt`.
- Still to check by a person: Firefox and Safari, W3C validators, a screen reader, 200 % zoom and the hosted site after deployment.

## Screenshots

[Builder](screenshots/builder.png) · [mismatch](screenshots/builder-mismatch.png) · [phone](screenshots/builder-mobile.png) · [choosing a motherboard](screenshots/picker.png) · [catalogue](screenshots/catalogue.png) · [report](screenshots/report.png)

## AI assistance

Claude designed and implemented this iteration (data, routes, templates, styles, drawings, tests) and wrote these notes. The team must review the diff, run the tests and be able to explain each change.
