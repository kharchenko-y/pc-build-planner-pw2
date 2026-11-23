# Likely lecturer questions

| Question | Short answer |
|---|---|
| 1. What problem are you solving? | A beginner needs a saved list of desktop PC parts, a reliable cost total and a clear warning for two common specification mismatches. |
| 2. Who are your users? | A student or beginner builder plans private builds. An administrator maintains the shared example catalogue. |
| 3. How does it differ from PCPartPicker or Pangoly? | Our small educational scope uses example prices and two explainable checks. It focuses on owned builds, lecturer-visible CRUD and traceable data. |
| 4. Why FastAPI and SQLite? | FastAPI handles validation, routing, sessions and server-rendered responses in Python. SQLite provides relational constraints and transactions in one persistent file. |
| 5. Which are the domain tables? | Categories, components, builds and build_items. Users and login_sessions support authentication. |
| 6. Give an example of one-to-many. | A category can group several components. Each component has one valid category ID. A user can also own many builds. |
| 7. Why have build_items? | Builds and catalogue components have a many-to-many relationship. The linking row holds quantity, references both records and prevents duplicate pairs. |
| 8. What happens when you delete a build or a component? | SQLite cascades a build deletion to its items. It restricts deletion of a component referenced by a build item. |
| 9. Where does the total come from? | The server joins each item to its current catalogue price and sums price in integer cents times quantity. The example is 19,000 + 13,000 + 5,500 cents. |
| 10. How does compatibility work? | It compares CPU socket and the selected memory generation with the motherboard. Missing evidence and mismatches are surfaced. |
| 11. Can an admin open another owner’s build? | No. The ownership query requires the current user’s ID for both roles. Admin grants catalogue permissions. |
| 12. How do you stop SQL injection? | Queries bind values separately from SQL text. The tests verify that SQL-shaped input is treated as a search value. |
| 13. How do you prevent forged requests? | Every mutating form uses POST and supplies a per-session CSRF token checked by the route. Deletion also requires a confirmation value. |
| 14. What happens at login and logout? | Login verifies a salted PBKDF2 hash and issues a fresh token. The database stores its digest and expiry. Logout deletes the record and clears the cookie. |
| 15. Why redirect after saving? | The POST writes once, then a 303 leads to a GET. Refreshing the result page simply re-reads the database. |
| 16. What does JavaScript do? | It fetches a result fragment on catalogue search and triggers browser print. With scripts disabled, the search still works through the GET form. |
| 17. Is this the redesign on the public site? | The live site runs the baseline interface. The redesign is in the review branch and passed a fresh Windows FastAPI installation and tests. |
| 18. What did each student do, and how was AI used? | We describe only evidenced individual actions, and we identify AI help with the prototype, code, design, documentation and checkpoint preparation. Both students need to verify and explain the solution. |
| 19. Were the first two checkpoints accepted? | We missed their scheduled updates. We prepared the evidence for a catch-up presentation. The lecturer decides how it is assessed. |
| 20. How are accounts created and what work remains? | The operator provisions two separate classroom accounts. We need the lecturer’s approval for that method and still owe final release, contribution and submission evidence. |
