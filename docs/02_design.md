# Checkpoint 2 — Planning and design (draft)

## Site map

```text
Home / My builds
├── Login
├── Create build
├── Build details
│   ├── Add/remove component
│   ├── Edit build
│   └── Delete build (confirmation)
├── Components
│   ├── Search by name + category
│   └── Add component (admin only)
└── Report
    ├── Print
    └── Download CSV
```

## Database (ER diagram in Mermaid)

See [`er_diagram.mmd`](er_diagram.mmd). Users can create many builds. Builds contain many build items. Each item references one component, and every component belongs to one category.

## Main app architecture

```text
Browser -> HTTP request -> FastAPI route (app.py)
                         -> session & CSRF / role check
                         -> parameterized SQLite query (db.py)
                         -> HTML template (templates/)
                         -> HTML response to browser
```

## Primary screens — wireframes (text sketch)

```text
+------------------------------------------------------+
| PC Build Planner | My builds | Components | Report    |
+------------------------------------------------------+
| Plan your PC build       [ + Create a build ]         |
|                                                      |
| My saved builds                                      |
| +-----------------+  +-----------------+             |
| | Office PC       |  | Gaming PC       |             |
| | Total €...      |  | Total €...      |             |
| +-----------------+  +-----------------+             |
+------------------------------------------------------+

Build detail:
+------------------------------------------------------+
| My gaming build | Budget €900 | Total €...            |
| Component             Category             Price     |
| Demo CPU               CPU                 €190      |
| Demo motherboard       Motherboard         €130      |
| [select catalogue part         v] [Add component]     |
| [Edit name]                        [Delete build]     |
+------------------------------------------------------+
```

## Decisions and reasons

- **SQLite:** simple relational DB stored in one file; enough for a local demo.
- **FastAPI + HTML templates:** one Python server and simple reusable HTML; no need for a React frontend.
- **Prices as integer cents:** avoids common decimal rounding errors when summing costs.
- **Link table `build_items`:** a build can have many components and a component can appear in many builds.
- **Session login & role checks:** student should only modify their own builds; admin can manage catalogue.
- **No external product API:** avoids network unreliability and licensing problems.

## Next engineering improvements

1. Replace demo-only session setup with tested secure deployment configuration.
2. Add user registration or lecturer-approved provisioned accounts.
3. Complete component/category CRUD with ownership/role tests.
4. Implement and test compatibility rules.
5. Cookie preference, browser and accessibility checks, async feature and file processing.
6. Full test matrix, clean install check and final release documentation.
