"""A small database-backed PC Build Planner prototype for PW2."""
import csv
import hashlib
import io
import time
import secrets
import sqlite3

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from config import PRODUCTION, ROOT, SESSION_SECONDS, SESSION_SECRET
from db import connection, verify_password

app = FastAPI(title="PC Build Planner", docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie="pcbuild_session",
    max_age=SESSION_SECONDS,
    same_site="lax",
    https_only=PRODUCTION,
)
app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")
templates = Jinja2Templates(directory=str(ROOT / "templates"))


@app.middleware("http")
async def response_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; object-src 'none'; base-uri 'none'; "
        "frame-ancestors 'none'; form-action 'self'"
    )
    if request.url.path.startswith("/static/"):
        return response
    response.headers["Cache-Control"] = "no-store"
    return response


def session_digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def user_from_request(request):
    if not hasattr(request.state, "current_user"):
        request.state.current_user = None
        token = request.session.get("login_token")
        if token:
            with connection() as db:
                request.state.current_user = db.execute(
                    """SELECT u.id, u.username, u.role FROM users u
                       JOIN login_sessions s ON s.user_id = u.id
                       WHERE s.token_digest = ? AND s.expires_at > ?""",
                    (session_digest(token), int(time.time())),
                ).fetchone()
    return request.state.current_user


def revoke_login(db, request):
    token = request.session.get("login_token")
    if token:
        db.execute("DELETE FROM login_sessions WHERE token_digest = ?", (session_digest(token),))


def token_for(request):
    if not request.session.get("csrf_token"):
        request.session["csrf_token"] = secrets.token_hex(24)
    return request.session["csrf_token"]


def check_token(request, token):
    actual = request.session.get("csrf_token", "")
    if not actual or not token.isascii() or not secrets.compare_digest(actual, token):
        raise HTTPException(status_code=403, detail="Invalid form token. Reload the page and try again.")


def page(request, template, **data):
    info = {"request": request, "user": user_from_request(request), "csrf": token_for(request)}
    info.update(data)
    return templates.TemplateResponse(request, template, info)


def require_user(request):
    user = user_from_request(request)
    if not user:
        raise HTTPException(status_code=401, detail="Please log in first.")
    return user


def owned_build(db, build_id, user_id):
    result = db.execute("SELECT * FROM builds WHERE id = ? AND user_id = ?", (build_id, user_id)).fetchone()
    if result is None:
        raise HTTPException(status_code=404, detail="Build not found.")
    return result


def redirect(url):
    return RedirectResponse(url=url, status_code=303)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    user = user_from_request(request)
    builds = []
    if user:
        with connection() as db:
            builds = db.execute("""SELECT b.id, b.title, b.budget_cents,
                COALESCE(SUM(c.price_cents * bi.quantity), 0) AS total_cents
                FROM builds b
                LEFT JOIN build_items bi ON bi.build_id = b.id
                LEFT JOIN components c ON c.id = bi.component_id
                WHERE b.user_id = ? GROUP BY b.id ORDER BY b.id DESC""", (user["id"],)).fetchall()
    return page(request, "home.html", builds=builds)


@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return page(request, "login.html", error=None)


@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), csrf: str = Form(...)):
    check_token(request, csrf)
    username = username.strip()
    if not 1 <= len(username) <= 32 or not 1 <= len(password) <= 128:
        return page(request, "login.html", error="Incorrect username or password.")
    with connection() as db:
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if not user or not verify_password(password, user["password_hash"]):
            return page(request, "login.html", error="Incorrect username or password.")
        token = secrets.token_urlsafe(32)
        now = int(time.time())
        revoke_login(db, request)
        db.execute("DELETE FROM login_sessions WHERE expires_at <= ?", (now,))
        db.execute(
            "INSERT INTO login_sessions (token_digest, user_id, expires_at) VALUES (?, ?, ?)",
            (session_digest(token), user["id"], now + SESSION_SECONDS),
        )
    request.session.clear()
    request.session["login_token"] = token
    token_for(request)
    return redirect("/")


@app.post("/logout")
def logout(request: Request, csrf: str = Form(...)):
    check_token(request, csrf)
    with connection() as db:
        revoke_login(db, request)
    request.session.clear()
    return redirect("/")


@app.get("/builds/new", response_class=HTMLResponse)
def new_build_form(request: Request):
    require_user(request)
    return page(request, "new_build.html", error=None)


@app.post("/builds/new")
def create_build(request: Request, title: str = Form(...), budget: str = Form("0"), csrf: str = Form(...)):
    user = require_user(request)
    check_token(request, csrf)
    title = title.strip()
    try:
        from decimal import Decimal
        value = Decimal(budget)
        if value < 0 or value > 100000 or value.as_tuple().exponent < -2:
            raise ValueError()
        cents = int(value * 100)
    except (ValueError, ArithmeticError):
        return page(request, "new_build.html", error="Budget must be a positive amount with at most 2 decimal places.")
    if not 2 <= len(title) <= 60:
        return page(request, "new_build.html", error="Title must be 2 to 60 characters.")
    with connection() as db:
        cursor = db.execute("INSERT INTO builds (user_id, title, budget_cents) VALUES (?, ?, ?)", (user["id"], title, cents))
        build_id = cursor.lastrowid
    return redirect(f"/builds/{build_id}")


@app.get("/builds/{build_id}", response_class=HTMLResponse)
def build_detail(request: Request, build_id: int):
    user = require_user(request)
    with connection() as db:
        build = owned_build(db, build_id, user["id"])
        items = db.execute("""SELECT bi.id, bi.quantity, c.name, c.socket, c.ram_type,
            c.price_cents, cat.name AS category
            FROM build_items bi JOIN components c ON c.id = bi.component_id
            JOIN categories cat ON cat.id = c.category_id
            WHERE bi.build_id = ? ORDER BY cat.id""", (build_id,)).fetchall()
        components = db.execute("""SELECT c.id, c.name, c.price_cents, cat.name AS category
            FROM components c JOIN categories cat ON cat.id = c.category_id
            ORDER BY cat.id, c.name""").fetchall()
    total = sum(row["price_cents"] * row["quantity"] for row in items)
    return page(request, "build_detail.html", build=build, items=items, components=components, total=total)


@app.post("/builds/{build_id}/items")
def add_item(request: Request, build_id: int, component_id: int = Form(...), csrf: str = Form(...)):
    user = require_user(request)
    check_token(request, csrf)
    with connection() as db:
        owned_build(db, build_id, user["id"])
        component = db.execute("SELECT id FROM components WHERE id = ?", (component_id,)).fetchone()
        if not component:
            raise HTTPException(status_code=400, detail="Unknown component.")
        try:
            db.execute("INSERT INTO build_items (build_id, component_id, quantity) VALUES (?, ?, 1)", (build_id, component_id))
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="This component is already in the build.")
    return redirect(f"/builds/{build_id}")


@app.post("/builds/{build_id}/items/{item_id}/delete")
def delete_item(request: Request, build_id: int, item_id: int, csrf: str = Form(...)):
    user = require_user(request)
    check_token(request, csrf)
    with connection() as db:
        owned_build(db, build_id, user["id"])
        db.execute("DELETE FROM build_items WHERE id = ? AND build_id = ?", (item_id, build_id))
    return redirect(f"/builds/{build_id}")


@app.get("/builds/{build_id}/edit", response_class=HTMLResponse)
def edit_build_form(request: Request, build_id: int):
    user = require_user(request)
    with connection() as db:
        build = owned_build(db, build_id, user["id"])
    return page(request, "edit_build.html", build=build, error=None)


@app.post("/builds/{build_id}/edit")
def edit_build(request: Request, build_id: int, title: str = Form(...), csrf: str = Form(...)):
    user = require_user(request)
    check_token(request, csrf)
    title = title.strip()
    if not 2 <= len(title) <= 60:
        with connection() as db:
            build = owned_build(db, build_id, user["id"])
        return page(request, "edit_build.html", build=build, error="Title must be 2 to 60 characters.")
    with connection() as db:
        owned_build(db, build_id, user["id"])
        db.execute("UPDATE builds SET title = ? WHERE id = ? AND user_id = ?", (title, build_id, user["id"]))
    return redirect(f"/builds/{build_id}")


@app.post("/builds/{build_id}/delete")
def delete_build(request: Request, build_id: int, csrf: str = Form(...)):
    user = require_user(request)
    check_token(request, csrf)
    with connection() as db:
        owned_build(db, build_id, user["id"])
        db.execute("DELETE FROM builds WHERE id = ? AND user_id = ?", (build_id, user["id"]))
    return redirect("/")


@app.get("/components", response_class=HTMLResponse)
def component_list(request: Request, q: str = "", category: str = ""):
    require_user(request)
    with connection() as db:
        categories = db.execute("SELECT * FROM categories ORDER BY name").fetchall()
        rows = db.execute("""SELECT c.*, cat.name AS category FROM components c
            JOIN categories cat ON cat.id = c.category_id
            WHERE c.name LIKE ? AND (? = '' OR cat.name = ?)
            ORDER BY cat.name, c.name""", ("%" + q[:80] + "%", category, category)).fetchall()
    return page(request, "components.html", components=rows, categories=categories, q=q, selected=category)


@app.get("/components/new", response_class=HTMLResponse)
def component_form(request: Request):
    user = require_user(request)
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only.")
    with connection() as db:
        categories = db.execute("SELECT * FROM categories ORDER BY name").fetchall()
    return page(request, "new_component.html", categories=categories)


@app.post("/components/new")
def create_component(request: Request, category_id: int = Form(...), name: str = Form(...), price: str = Form(...), csrf: str = Form(...)):
    user = require_user(request)
    check_token(request, csrf)
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only.")
    from decimal import Decimal, InvalidOperation
    try:
        value = Decimal(price)
        if not 2 <= len(name.strip()) <= 80 or value < 0 or value > 100000 or value.as_tuple().exponent < -2:
            raise ValueError()
        cents = int(value * 100)
    except (InvalidOperation, ValueError):
        raise HTTPException(status_code=400, detail="Invalid name or price.")
    with connection() as db:
        try:
            db.execute("INSERT INTO components (category_id, name, price_cents) VALUES (?, ?, ?)", (category_id, name.strip(), cents))
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Invalid category or duplicate component name.")
    return redirect("/components")


@app.get("/report", response_class=HTMLResponse)
def report(request: Request):
    user = require_user(request)
    with connection() as db:
        builds = db.execute("""SELECT b.title, b.budget_cents, b.created_at,
            COALESCE(SUM(bi.quantity * c.price_cents), 0) AS total_cents
            FROM builds b LEFT JOIN build_items bi ON bi.build_id = b.id
            LEFT JOIN components c ON c.id = bi.component_id
            WHERE b.user_id = ? GROUP BY b.id ORDER BY b.id DESC""", (user["id"],)).fetchall()
    return page(request, "report.html", builds=builds)


def safe_csv_text(value):
    # Avoid interpreting user-supplied titles as spreadsheet formulas.
    text = str(value)
    if text.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


@app.get("/report.csv")
def csv_report(request: Request):
    user = require_user(request)
    with connection() as db:
        rows = db.execute("""SELECT b.title, b.created_at,
            COALESCE(SUM(bi.quantity * c.price_cents), 0) AS total_cents
            FROM builds b LEFT JOIN build_items bi ON bi.build_id = b.id
            LEFT JOIN components c ON c.id = bi.component_id
            WHERE b.user_id = ? GROUP BY b.id ORDER BY b.id DESC""", (user["id"],)).fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Build", "Created", "Total (EUR)"])
    for row in rows:
        writer.writerow([safe_csv_text(row["title"]), row["created_at"], f"{row['total_cents']/100:.2f}"])
    return Response(output.getvalue(), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": 'attachment; filename="build-report.csv"'})


@app.exception_handler(HTTPException)
async def friendly_error(request: Request, exc: HTTPException):
    return templates.TemplateResponse(request, "error.html", {"request": request, "error": exc.detail, "user": user_from_request(request), "csrf": token_for(request)}, status_code=exc.status_code)
