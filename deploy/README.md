# PythonAnywhere deployment

This keeps the FastAPI application and the SQLite database. PythonAnywhere's WSGI worker calls FastAPI through a2wsgi. A persistent file in the hosting account's private home directory stores database records, including login sessions.

The WSGI entry point creates the adapter on the first request in each worker. PythonAnywhere loads the WSGI module in the master process before starting workers. Starting the adapter at import time leaves a forked worker with an event loop whose thread is missing.

1. Create a free Beginner web app using **Manual configuration**. Choose Python 3.13 if available. Use the same Python version for the virtual environment.
2. Upload `PC_Build_Planner_PW2_Hosting.zip` to the hosting account's home directory using **Files**.
3. Run the following in a PythonAnywhere **Bash** console.

```bash
set -e
mkdir -p "$HOME/apps/pc-build-planner"
unzip -o "$HOME/PC_Build_Planner_PW2_Hosting.zip" -d "$HOME/apps/pc-build-planner"
python3.13 -m venv "$HOME/.virtualenvs/pcbuild-pw2"
source "$HOME/.virtualenvs/pcbuild-pw2/bin/activate"
cd "$HOME/apps/pc-build-planner"
python -m pip install -r requirements-dev.txt
python -m pytest -q
python deploy/bootstrap.py
```

4. In the **Web** tab, set the virtualenv to `/home/YOUR_USER/.virtualenvs/pcbuild-pw2`. Replace the WSGI configuration contents with `deploy/pythonanywhere_wsgi.py`. Enable **Force HTTPS** and reload.
5. Open the HTTPS URL shown in **Web**. The separate student and administrator credentials are in `~/.pcbuild-pw2/classroom.txt` and `~/.pcbuild-pw2/classroom-admin.txt` in the hosting dashboard. Use the student credential for a classroom demonstration. Keep the administrator credential and runtime configuration private.
6. Verify the main workflow. Create a sample build, add Demo CPU AM5 and the AM5 motherboard, then the 16 GB DDR5 demo kit. Confirm €375.00 and the compatibility result. Edit the build, filter CPU by AM5, open the report and verify logout. Reload the web worker and log in again to confirm that the build persists.

A Beginner web app has a one-month expiry. Check the date shown in Web before the assessment. No GitHub checkout or database connection string is needed to run this package. Keep `~/.pcbuild-pw2` outside all web/static directories. Never copy that directory into source control or a submission ZIP.
