# Speaking guide · Progress updates 1–3

**24 November 2026 · PC Build Planner · Vilnius University**
Each segment runs approximately 2–5 minutes including the evidence shown. Start with:
> We missed the first two scheduled progress updates. May I show the evidence for those stages first, then demonstrate Checkpoint 3? We understand the checkpoint decisions are yours.

## 1 · Research and requirements

**Open:** slides 2–4 and [the requirements notes](01_requirements.md). Point to one row in the comparison, the Student/Admin roles and the P0 backlog.

> PC Build Planner helps someone planning a desktop computer keep the list of parts, its total cost and basic compatibility in one place. For a beginner keeping parts in notes or a spreadsheet, changing a selection means calculating the total again and looking up technical details separately.
>
> Our primary user is a student or first-time PC builder. They sign in, create a private build with a budget, choose example parts and see the total. A second user is an administrator who maintains the shared catalogue. An administrator still owns only their own builds.
>
> We looked at PCPartPicker for its part selection, compatibility and pricing guidance, and at Pangoly for its category-led builder and seller information. Their workflows helped us identify which decisions a beginner makes first. Our project uses an illustrative catalogue and supports two explicit checks: CPU socket and memory generation against the motherboard. We can explain each result from the stored data. Live retailer prices, power sizing and physical fit are outside this version.
>
> The first workflow to prove is a student creating and editing a build from named parts. The second is an admin maintaining the catalogue, with students able to search it. Our first backlog priority is the schema, login, owner checks and complete build CRUD. Search, totals, reporting and interface improvements followed. We also require persistent storage, input validation and a responsive layout.
>
> Our proposed division is for Yaroslav to lead the data and build-flow review and for me to lead the catalogue and interface review. We both need to be able to trace the full system. We used material AI assistance in the prototype, redesign and preparation. Our contribution record says which activities have evidence and which are planned.

## 2 · Planning and design

**Open:** slides 5–8. Show [site map](checkpoints/visuals/site-map.svg), [wireframes](checkpoints/visuals/wireframes.svg) and [ER diagram](checkpoints/visuals/er-diagram.svg). Point to the review branch and an actual local screenshot. Compare it with the live overview before moving on.

> The site map starts with a public overview and login. After signing in, the same home URL shows the current user's builds. From there, a user can create a build or open its detail page. Components is the shared searchable catalogue. Report shows the signed-in user's build totals. An admin also sees the component management controls.
>
> The wireframe shows the redesigned build detail. On a wide screen the picker and parts list share the page with a cost and compatibility summary. On a phone the summary appears first, then the picker and parts list. This image is from the redesign review branch. The online classroom demo currently shows the baseline layout.
>
> The core database has four application tables. A category can have many components. A user can have many builds. A build can contain many items. Each item points to a component and records a quantity. The same catalogue component may be reused in different builds, so build_items connects builds and components. A unique pair prevents adding the identical catalogue part twice.
>
> We chose FastAPI with Jinja to render HTML on the server. SQLite gives us transactions and constraints in a file. CSS handles layout and print. A small JavaScript enhancement fetches the catalogue results, and the normal form still works without it. PythonAnywhere serves the classroom URL over HTTPS using an adapter for the FastAPI app.
>
> We planned to prove one reliable database-backed flow first, then integrate search, catalogue and reporting, and finally check responsiveness and release readiness. GitHub has the baseline and the redesign review branch. The work plan records follow-up checks and who is proposed to lead them.

## 3 · Database and core backend

**Open:** slides 9–11, then the [classroom site](https://yarslv.pythonanywhere.com/). Sign in beforehand and use the scripted order below. Allow 2–3 minutes for clicking and about 1–2 minutes for narration.

> This update shows how the database, login and first CRUD flow work together. I am signed in as a student. I can create an €800 build. The server associates it with my user ID. I select an AM5 CPU, an AM5 motherboard and a DDR5 kit. Their prices sum to €375. When I refresh, the saved parts stay because each selection is a row in SQLite. The application compares the CPU socket and RAM generation with the motherboard.
>
> I can rename the build and save it. Delete opens a confirmation page. For the classroom demo I will cancel there. The integration test performs the actual delete in a temporary database and verifies the build is gone. A separate database check proves the items cascade and the catalogue component remains.
>
> The routes enforce access on the server. A student gets a refusal on an admin catalogue URL, and a build lookup always binds both the build ID and the current user’s ID. The test suite checks both roles, other-owner access, a missing CSRF token and session revocation. The schema and test results are available here if you want to see the query or the full evidence.

### Exact live click order

1. Open the [classroom URL](https://yarslv.pythonanywhere.com/) → **Log in to try the demo** → sign in with the classroom Student credentials received privately.
2. **+ Create a build** → name `PW2 Live Demo 24 Nov` → **Budget (EUR)** `800` → **Save build**.
3. In **Choose from catalogue**, select **Demo CPU AM5**, click **Add component**. Repeat for **Demo motherboard AM5** and **16 GB DDR5 demo kit**. Check **€375.00** and the matching compatibility message.
4. Refresh. Check title, total and the three saved rows. **Edit build** → rename to `PW2 Live Demo 24 Nov - revised` → **Save changes**.
5. **Delete build** → show the named confirmation → **Cancel**. Show completed deletion in the local test evidence. Only demonstrate a real deletion on a disposable local build.
6. If time permits, **Components** → **Search name** `AM5` → **Category** `CPU` → **Search** → one row. **Report** → show the revised row and **Print report** / **Export CSV**. A Student visiting `/components/new` sees a role refusal.
7. On the classroom PC, log out when done. If time runs short, the signed-in Student can open [the prepared €375 demo](https://yarslv.pythonanywhere.com/builds/3).

## If the lecturer requests code or SQL

| Request | Open | Explain |
|---|---|---|
| Schema or foreign keys | `database/schema.sql` → `build_items` | Two FKs, a unique pair, quantity range and cascade vs. restrict. |
| Trace one request | `app.py` → `create_build`, `owned_build` and `build_detail` | POST, user and CSRF, validated amount, INSERT with bound values, 303, owner-bound SELECT, template. |
| Find the connection | `db.py` → `connection` | Opens the configured file, enables FKs, commits or rolls back and closes. |
| See evidence | `tests/test_app.py` → `test_build_update_delete_and_xss_escaping`, `test_unauthorized_own_build` and `test_role_blocks_admin_only` | Temporary database, expected results, refused requests. |
| GitHub | [Repository](https://github.com/kharchenko-y/pc-build-planner-pw2) | Show `main` and `review/claude-redesign`. Use the offline code excerpts if private access is unavailable. |

If the public link fails: “Here are local screenshots of the review interface and the recorded results from the live baseline. I can show the exact flow and the passed tests from the package.” Open [the fallback gallery](checkpoints/gallery.html) and [the evidence notes](checkpoints/04_backend_evidence.md). Do not present screenshots as a current live interaction.
