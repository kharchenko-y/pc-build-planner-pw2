# Tuesday, 24 November 2026 — short PW2 progress update

## Important

This material shows **work actually present in the starter**. Do not claim that both members wrote it or that the project is complete. The lecturer determines which checkpoint is due. Since 24 November may fall in the 13th teaching week, they may expect integrated features already. Two previous updates may have been missed; ask how to document those honestly.

## What to show in 2–4 minutes

1. **Problem & scope**: desktop PC build planning with saved parts and budgets.
2. **Users / workflows**: Student creates a build; Admin maintains components.
3. **ER diagram**: open `docs/er_diagram.mmd` (or `database/schema.sql`), explain 5 tables and foreign keys.
4. **Running demo**: login as `student`, create a build, add CPU and motherboard, show total.
5. **SQL & security**: open `app.py`, show `create_build()` and parameterized SQL, CSRF check, owner check.
6. **Progress / next steps**: plan actual teammate responsibilities, complete catalogue CRUD, compatibility, security, testing.

## Speaking notes (simple English)

> We chose PC Build Planner, a web application for planning computer configurations. The main problem is that beginners need a place to save their parts and calculate the cost. Our first workflow is to create a build and add components. The second is managing the component catalogue with an admin role.
>
> We designed a relational database with users, categories, components, builds and build items. One user can own many builds, and one build can contain many items. Build items connect builds to components.
>
> This is an early working prototype. It uses Python, FastAPI and SQLite. I can log in, create a build, add a component and show the calculated price. The server reads and writes the database. We have also started using parameterized queries, password hashing, access checks and CSRF tokens.
>
> The system is not finished. Next, we will complete component management, add compatibility checks, test security, and improve the frontend. We will also document the contributions of both team members in Git.

Adapt pronouns and attribution to what has actually been performed by each teammate; don't claim joint coding if it hasn't occurred.

## Likely questions (answer in one sentence)

**Why a database?** The builds and components need to remain saved after the browser is closed.

**Why five tables?** Users own builds, categories group components, and build_items connects a build to its parts.

**What is CRUD?** Create, Read, Update and Delete operations on database records.

**Where is the calculation?** We sum price_cents multiplied by quantity for the items in the build.

**Why integer cents?** It avoids floating-point rounding problems for prices.

**How do you prevent SQL injection?** Values are passed as parameters using `?` placeholders, not joined into SQL strings.

**Can a student edit another student's build?** The SQL query checks both build ID and current user ID.

**What is the role difference?** Students edit their own builds; only admins can add catalogue components in this prototype.

**Does it already check compatibility?** No. CPU socket and RAM types are stored, but validation is a planned improvement.

**Is the app deployed?** Currently localhost only, which the assignment permits.

**How did you use AI?** Answer truthfully. Material AI assistance needs to be declared according to course rules.

## Important follow-up with lecturer

- Confirm topic and stack approval.
- Ask which checkpoint is expected on 24 November, and whether the missed earlier checkpoints can be documented (they cannot simply be replaced by the final demo).
- Ask what counts as the required asynchronous and file-processing feature.
- Confirm how to document material AI assistance.
