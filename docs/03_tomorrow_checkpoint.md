# PC Build Planner Progress Demonstration

24 November 2026 · Vilnius University · WWW Development Technologies · Practical Work II

## Browser route

Use the verified HTTPS URL if the deployment is complete. Sign in with the separately provisioned student account. Use a private browser window on the university PC, do not save the password and sign out when finished. Open this script, the ER diagram and the starter screenshots in advance. If the live site is unavailable, show the starter screenshots and label them as earlier local captures.

1. **0:00–0:35** Open the landing page, log in and introduce the two workflows.
2. **0:35–1:30** Create `Campus PC` with an €800 budget. Add **Demo CPU AM5**, **Demo motherboard AM5**, then **16 GB DDR5 demo kit**. Point at the total of **€375.00**. Refresh to demonstrate the saved build.
3. **1:30–2:15** Edit the name to `Campus PC revised` and save. Open **Components**, filter **AM5** in **CPU**, then open **Report**. Open print preview and cancel it. If time permits, delete the demo build through the confirmation screen.
4. **2:15–3:15** Show the diagram and explain the request path and ownership. State the status of deployment, testing, AI assistance and team contributions accurately.

## Speaking script

> Our working title is PC Build Planner. A beginner can save a desktop PC configuration, choose parts from a catalogue and see its cost in one place. A catalogue administrator maintains the catalogue. Both roles can manage their own builds.
>
> I will create a build called Campus PC with an 800-euro budget. I will add an AM5 processor, an AM5 motherboard and a DDR5 memory kit. The total is 375 euros. Each catalogue price is stored as a whole number of cents. The server multiplies prices by quantities and adds the results. When I refresh, the items stay because they were written to the SQLite database.
>
> I can change the name and save it. The catalogue filter uses the part name and its category. Those values come from two related tables. The report reads the saved builds and produces a printable summary.
>
> This diagram shows the main relationships. A user can own many builds, and a build can contain many items. A build item points to a catalogue component. A foreign key links the records, and SQLite prevents a referenced catalogue component from being deleted. The server checks who is signed in and whether the build belongs to that user. Form submissions also require a CSRF token.
>
> This is a progress demonstration. We used material AI assistance in building and documenting the prototype. We still need to review the implementation as a pair, document our individual contributions and complete the release checks.

If the latest build is verified in the browser, add this line after the parts are selected:

> The application also compares the CPU socket and memory generation with the motherboard. These are the two compatibility rules in this version.

If the live app is unavailable, replace the action narration with this opening:

> I can show the project structure and screenshots of the earlier local prototype today. The publicly hosted application is still awaiting verification, so the screenshots are evidence of the earlier local workflow.

## Likely questions

| Question | Short answer |
|---|---|
| What is a foreign key? | It links a value in one table to a valid record in another table. For example, a build item references its build and selected component. |
| Trace a saved build from the browser to the database. | The browser submits `POST /builds/new`. The route checks the active user, CSRF and the inputs, then inserts a row with bound parameters. A 303 sends the browser to the saved build. |
| Why use cents? | Integer arithmetic keeps the stored amounts and totals exact. |
| Can an admin edit another student's build? | No. Admin applies to the catalogue. The build query still requires the current user's ID. |
| What happens when a part is deleted? | A part referenced by a build is protected by a foreign key. Deleting a build removes its linked items and keeps catalogue parts. |
| What is CSRF? | It is when another site tries to trigger a request using the browser's login. The server checks that each change includes a valid token from this app. |
| How do sessions work? | Login generates a new session token. The server stores a digest and expiry. Logout deletes that record and clears the cookie. |
| What changes when the CPU socket is wrong? | The build displays a mismatch warning when the specifications are known. The user can remove the part and choose a replacement. |
| What did your teammate do? | Describe only the work each of you can show in commits, tests or documentation. The handoff did not contain a verified contribution record. |
| What work remains? | Confirm the topic and account workflow, collect browser and accessibility evidence, record team contributions and finish the report, slides and video. |

Ask the lecturer which checkpoint is due, confirm the title and FastAPI/SQLite stack, and ask whether operator-provisioned accounts are accepted. Mention missed sessions accurately if asked and record any answer in the checkpoint notes.
