# Interface redesign (23 November 2026)

This iteration changes how PC Build Planner looks and reads. Routes, form methods, field names, CSRF, validation, sessions, roles, build ownership and stored data are unchanged.

## Design direction

The interface follows the subject: a technical tool for assembling a PC against a budget.

| Token | Value | Use |
|---|---|---|
| Graphite | `#22272e` | Navigation bar, login side panel, workflow steps |
| Workspace | `#eef1f4` | Page background behind white panels |
| Ink / muted | `#1b2027` / `#56606b` | Text and secondary text |
| Teal accent | `#0b7285` | Primary actions, active navigation, CPU colour |
| States | green `#2b7a4b`, amber `#8a5300`, red `#b42318` | Within budget / incomplete / over budget or mismatch |

- **Typeface:** Fira Sans (400, 500, 600) served from `static/fonts/`. Prices use tabular figures so amounts line up in columns.
- **Category colours:** each part category has one colour. The same colour appears in the budget bar, the legend, the parts list and the catalogue. Labels always accompany the colour.
- **One emphasis per screen:** on the build page it is the total with the budget bar. Other elements stay quiet.

## Screen decisions

| Screen | Decision and reason |
|---|---|
| Public home | The headline states the purpose. A numbered four-step panel shows the real workflow, because the steps are a sequence. A second panel says what is checked and what is not. |
| Login | A split panel. The dark side repeats the product identity from the navigation bar. Failed login marks both fields with `aria-invalid` and links them to the error. |
| My builds | Title, count and a primary **Create a build** button. Each build shows total, budget, a bar and a status (left, over by, no limit). Cards and List are two submit buttons with `aria-pressed`, posting the same `view` field. They work without JavaScript and keep the 30-day cookie. |
| Build details | Two columns on wide screens: Add a component and the parts list on the left, a sticky summary on the right. The summary shows total, budget, remaining amount, compatibility status and a budget bar split by category. On phones the order follows the task: summary, add a part, adjust the list, then the cost breakdown and check details. |
| Part picker | Options are grouped by category and show socket or memory type. Parts already in the build and second CPU, motherboard or RAM choices are disabled with the reason in the option text. The server still enforces every rule. |
| Components | Name and category form one search block. Results show category, specs and right-aligned prices. Loading dims the table and announces status. The empty result explains what to try. Only administrators see Add, Import, Edit and Delete. |
| Report | Same header and table style. A status column shows over or within budget. Print hides navigation and buttons and prints plain black text. CSV export is unchanged. |
| Forms, confirmations, errors | One field pattern: label, input, hint, error. Success uses a green notice with `role="status"`. Errors use `role="alert"`. Delete pages use a red top edge and a single red button beside Cancel. Error pages offer the next step (Log in, or Back to My builds). |

## Compatibility scope shown to users

The build summary, home page and footer state the limit of the check: CPU socket and RAM generation are compared with the motherboard using catalogue data. BIOS support, physical fit, cooling and power are not checked. Catalogue prices are demonstration values.

## Changes by file

| File | Change |
|---|---|
| `static/styles.css` | Rewritten as one design system: tokens, header, buttons, alerts, fields, tables, cards, build layout, catalogue, report, responsive rules at 1024, 900, 860, 720 and 420 px, reduced motion, print. |
| `static/fonts/` | Fira Sans subset to Latin glyphs (WOFF) and its licence `OFL.txt`. |
| `static/favicon.svg` | New icon based on the chip mark. Prevents a missing `/favicon.ico` request. |
| `static/actions.js` | Unchanged. Its selectors `#catalogue-filter`, `#catalogue-results`, `#catalogue-status` and `[data-print]` remain in the templates. |
| `templates/_macros.html` | New. Money formatting with thousands separators, category class, logo, budget meter, budget status, empty-state drawing. |
| `templates/*.html` | All screens restructured as described above. Breadcrumbs on inner pages. Visible labels and hints kept for every field. |
| `domain.py` | Adds the constant `COMPATIBLE` for the success message. The compatibility function returns the same values as before. |
| `app.py` | Two interface-only changes in `build_detail`: passes `compatibility_state` (`ok`, `issue`, `incomplete`) for the status badge, and selects `socket` and `ram_type` for the part picker. No route, validation or permission changes. |
| `tests/test_app.py` | One new test for the €375.00 example: total, remaining budget, compatibility badge, disabled duplicate option and report total. |

## Accessibility notes

- Skip link, landmarks, one `h1` per page, breadcrumbs with `aria-current`.
- Focus outline 3 px: dark amber `#b26a00` on light surfaces (3.7:1 against the workspace), bright amber on the graphite bar.
- Measured text contrast: body 16.4:1, muted 5.7–6.4:1, white on teal buttons 5.6:1, status labels 4.6–5.8:1.
- Wide tables scroll inside their own region with a keyboard-focusable wrapper. The parts list becomes stacked rows below 720 px.
- Charts are decorative (`aria-hidden`). The same figures are present as text: total, budget, remaining amount and a cost-by-category list.

## Third-party resources

Fira Sans: Copyright 2012–2015 The Mozilla Foundation and Telefonica S.A., SIL Open Font License 1.1 (`static/fonts/OFL.txt`). The licence declares no Reserved Font Name, so the subset keeps the family name. All other graphics are project-made inline SVG.

## AI assistance

Claude (Anthropic) produced this redesign: the CSS, templates, macros, the two small `app.py`/`domain.py` changes, the new test, the verification scripts and this document. The team must review each change, re-run the checks on their own machines and be able to explain the decisions above.

## Verification and open items

See `test_results_redesign_2026-11-23.txt`. Checks that still need a person or another environment:

- Re-run `pytest` after a clean install of the real FastAPI from `requirements-dev.txt` (the redesign was tested through a compatibility shim).
- Firefox and Safari (only Chromium-based browsers were available).
- W3C HTML and CSS validators (no network). A local nesting and duplicate-id check passed on 15 pages.
- Screen reader pass (NVDA or VoiceOver) and 200 % browser zoom.
- A physical printer and opening the CSV in Excel or LibreOffice.
- Deployment to PythonAnywhere and a live comparison with the published version.
