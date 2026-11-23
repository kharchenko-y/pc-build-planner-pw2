# Checkpoint 1 — Research and requirements (draft)

**Working title:** PC Build Planner

**Problem.** Beginners often keep a list of PC parts in notes or spreadsheets and need to manually add up prices and remember which components belong to each build. A small web app can keep builds and their parts together.

**Target users.** Students and beginner PC builders who want to plan and compare configurations. A second role is a catalogue administrator maintaining example parts.

**What is NOT part of the first release.** Real-time store prices, ordering parts, benchmarking, advanced compatibility data, public social networking.

## Main workflows

1. **Build a PC**: log in -> create a build -> choose a component from the catalogue -> save it to the build -> view total cost -> edit or remove items -> print the report.
2. **Maintain catalogue** (admin): log in -> inspect catalogue -> add/edit/remove a component -> user searches again and sees updated data.

## Requirements mapped to PW2

| PW2 feature | Proposed implementation | Starter status |
|---|---|---|
| Three related domain tables | categories, components, builds, build_items (+ users) | Schema ready |
| CRUD | Builds and catalogue | Builds CRUD; catalogue add only |
| Two roles | Student / Admin | Starter working |
| Two-criteria search | Name + category (components JOIN categories) | Starter working |
| Calculation | SUM of selected part prices | Starter working |
| Report | Print-friendly build summary | Starter working |
| Cookie preference | View mode compact/list | Not yet |
| Security | Prepared statements, password hashing, role checks, CSRF, escaping | Foundation only |
| Relational rules | Primary/foreign keys, deletion handling, constraints | Schema ready |
| Responsive, accessible UI | Grid, media query, labels, keyboard focus | Preliminary |
| File processing/asynchronous | CSV export, perhaps CSV import / fetch filter | Needs lecturer clarification and further work |

## Initial comparison / research questions

Comparable solutions to study: PCPartPicker and conventional component catalogues. We should discuss what is useful in their workflows, but not copy any template, content, or source code. Research citations, licence checks and final references will be added by both team members before the report is submitted.

## Small release scope

Start with a working, secure flow involving real database entries. Add compatibility checking (CPU socket matches motherboard socket; RAM generation matches motherboard) only after CRUD and roles work reliably.

## Team contributions (fill with real names and actions)

- Member A: TBD — planned data model, build CRUD, tests; actual commits not yet recorded.
- Member B: TBD — planned catalogue and search, UI tests/docs; actual commits not yet recorded.
- Both: review the entire application, run tests, demonstrate security, and prepare the presentation.

Do not submit invented or retroactively attributed contributions. Split the next tasks once the two members agree.
