"""A small database-backed PC Build Planner prototype for PW2."""
import csv
import hashlib
import io
import time
import secrets
import sqlite3

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from catalogue import INSERT_COMPONENT, MAX_CSV_BYTES, csv_rows, lookup
from domain import (
    CATEGORY_LABELS, CATEGORY_ORDER, CHOOSE_LABELS, RAM_TYPES, SINGLE_CATEGORIES, check_rows, clean_specs,
    compatibility, compatibility_state, component_values, max_quantity, money_cents, part_fit, text_amount,
)
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
templates.env.globals.update(
    CATEGORY_ORDER=CATEGORY_ORDER, CATEGORY_LABELS=CATEGORY_LABELS, CHOOSE_LABELS=CHOOSE_LABELS,
    max_quantity=max_quantity,
)


@app.middleware("http")
async def response_headers(request: Request, call_next):
    if request.method == "POST":
        try:
            length = int(request.headers.get("content-length", ""))
        except ValueError:
            return Response("A valid Content-Length is required.", status_code=411)
        if not 0 <= length <= 64 * 1024:
            return Response("This request is larger than 64 KiB.", status_code=413)
    response = await call_next(request)
    if PRODUCTION:
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
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
    info = {
        "request": request, "user": user_from_request(request),
        "csrf": token_for(request), "notice": request.session.pop("notice", None),
    }
    info.update(data)
    return templates.TemplateResponse(request, template, info)


def require_user(request):
    user = user_from_request(request)
    if not user:
        raise HTTPException(status_code=401, detail="Please log in first.")
    return user


def require_admin(request):
    user = require_user(request)
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Catalogue changes require the administrator role.")
    return user


def require_confirmation(confirmed):
    if confirmed != "yes":
        raise HTTPException(status_code=422, detail="Open the confirmation page before deleting.")


def owned_build(db, build_id, user_id):
    result = db.execute("SELECT * FROM builds WHERE id = ? AND user_id = ?", (build_id, user_id)).fetchone()
    if result is None:
        raise HTTPException(status_code=404, detail="Build not found.")
    return result


def redirect(url):
    return RedirectResponse(url=url, status_code=303)


def saved(request, url, message):
    request.session["notice"] = message
    return redirect(url)


ITEM_QUERY = """SELECT bi.id, bi.build_id, bi.quantity, c.id AS component_id, c.name, c.socket, c.ram_type,
    c.specs, c.price_cents, cat.name AS category
    FROM build_items bi JOIN components c ON c.id = bi.component_id
    JOIN categories cat ON cat.id = c.category_id"""


def summarise(build, items):
    """Totals, slot progress and check results for one build."""
    chosen = {row["category"] for row in items}
    return {
        "build": build, "parts": items, "budget": build["budget_cents"],
        "total": sum(row["price_cents"] * row["quantity"] for row in items),
        "chosen": [name for name in CATEGORY_ORDER if name in chosen],
        "missing": [name for name in CATEGORY_ORDER if name not in chosen],
        "state": compatibility_state(items), "checks": check_rows(items),
    }


def user_builds(db, user_id, build_id=None):
    builds = db.execute(
        "SELECT * FROM builds WHERE user_id = ? AND (? IS NULL OR id = ?) ORDER BY id DESC",
        (user_id, build_id, build_id),
    ).fetchall()
    grouped = {}
    for row in db.execute(
        ITEM_QUERY + " JOIN builds b ON b.id = bi.build_id WHERE b.user_id = ? ORDER BY cat.id, c.name", (user_id,),
    ):
        grouped.setdefault(row["build_id"], []).append(row)
    return [summarise(build, grouped.get(build["id"], [])) for build in builds]


def amount(cents):
    return f"{cents / 100:.2f}"


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    user = user_from_request(request)
    builds = []
    if user:
        with connection() as db:
            builds = user_builds(db, user["id"])
    view = request.cookies.get("pcbuild_view", "cards")
    return page(request, "home.html", builds=builds, view="list" if view == "list" else "cards")


@app.post("/preferences/build-view")
def build_view(request: Request, view: str = Form(...), csrf: str = Form(...)):
    require_user(request)
    check_token(request, csrf)
    if view not in {"cards", "list"}:
        raise HTTPException(status_code=422, detail="Choose a supported build view.")
    response = saved(request, "/", "Build view saved.")
    response.set_cookie(
        "pcbuild_view", view, max_age=30 * 24 * 60 * 60,
        httponly=True, secure=PRODUCTION, samesite="lax",
    )
    return response


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


def build_form(request, build=None, title=None, budget=None, error=None):
    return page(
        request, "build_form.html", error=error,
        heading="Edit build" if build else "Create a PC build",
        submit="Save changes" if build else "Save build",
        title=title if title is not None else (build["title"] if build else ""),
        budget=budget if budget is not None else (text_amount(build["budget_cents"]) if build else "1000"),
    )


def build_fields(title, budget):
    title = title.strip()
    if not 2 <= len(title) <= 60 or any(ord(char) < 32 for char in title):
        raise ValueError("Title must be 2 to 60 printable characters.")
    try:
        return title, money_cents(budget)
    except ValueError as error:
        raise ValueError(f"Budget must be a valid amount. {error}") from error


@app.get("/builds/new", response_class=HTMLResponse)
def new_build_form(request: Request):
    require_user(request)
    return build_form(request)


@app.post("/builds/new")
def create_build(request: Request, title: str = Form(...), budget: str = Form("0"), csrf: str = Form(...)):
    user = require_user(request)
    check_token(request, csrf)
    try:
        name, cents = build_fields(title, budget)
    except ValueError as error:
        return build_form(request, title=title, budget=budget, error=str(error))
    with connection() as db:
        cursor = db.execute("INSERT INTO builds (user_id, title, budget_cents) VALUES (?, ?, ?)", (user["id"], name, cents))
        build_id = cursor.lastrowid
    return saved(request, f"/builds/{build_id}", "Build created.")

@app.get("/builds/{build_id}", response_class=HTMLResponse)
def build_detail(request: Request, build_id: int):
    user = require_user(request)
    with connection() as db:
        build = owned_build(db, build_id, user["id"])
        items = db.execute(ITEM_QUERY + " WHERE bi.build_id = ? ORDER BY cat.id, c.name", (build_id,)).fetchall()
    summary = summarise(build, items)
    slots = [{"category": name, "parts": [row for row in items if row["category"] == name]} for name in CATEGORY_ORDER]
    warnings, status = compatibility(items)
    return page(
        request, "build_detail.html", build=build, summary=summary, slots=slots, items=items,
        total=summary["total"], warnings=warnings, compatibility_status=status,
    )


@app.post("/builds/{build_id}/items")
def add_item(request: Request, build_id: int, component_id: int = Form(...), replace: str = Form(""),
             csrf: str = Form(...)):
    user = require_user(request)
    check_token(request, csrf)
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        owned_build(db, build_id, user["id"])
        component = db.execute(
            """SELECT c.name, c.category_id, cat.name AS category FROM components c
               JOIN categories cat ON cat.id = c.category_id WHERE c.id = ?""",
            (component_id,),
        ).fetchone()
        if not component:
            raise HTTPException(status_code=400, detail="Unknown component.")
        duplicate = db.execute(
            "SELECT 1 FROM build_items WHERE build_id = ? AND component_id = ?", (build_id, component_id),
        ).fetchone()
        if duplicate:
            raise HTTPException(status_code=400, detail="This component is already in the build.")
        slot = f"/builds/{build_id}#slot-{component['category'].lower()}"
        if component["category"] in SINGLE_CATEGORIES:
            current = db.execute(
                """SELECT bi.id FROM build_items bi JOIN components c ON c.id = bi.component_id
                   WHERE bi.build_id = ? AND c.category_id = ?""",
                (build_id, component["category_id"]),
            ).fetchone()
            if current and replace != "yes":
                label = CATEGORY_LABELS[component["category"]].lower()
                raise HTTPException(
                    status_code=409, detail=f"The {label} slot is already filled. Use Replace to swap the part.",
                )
            if current:
                db.execute(
                    "UPDATE build_items SET component_id = ?, quantity = 1 WHERE id = ?", (component_id, current["id"]),
                )
                return saved(request, slot, f"{component['name']} replaced the previous part.")
        db.execute("INSERT INTO build_items (build_id, component_id, quantity) VALUES (?, ?, 1)", (build_id, component_id))
    return saved(request, slot, f"{component['name']} added.")


@app.post("/builds/{build_id}/items/{item_id}/quantity")
def update_quantity(request: Request, build_id: int, item_id: int, quantity: int = Form(...), csrf: str = Form(...)):
    user = require_user(request)
    check_token(request, csrf)
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        owned_build(db, build_id, user["id"])
        item = db.execute(
            """SELECT cat.name AS category FROM build_items bi
               JOIN components c ON c.id = bi.component_id JOIN categories cat ON cat.id = c.category_id
               WHERE bi.build_id = ? AND bi.id = ?""",
            (build_id, item_id),
        ).fetchone()
        if item is None:
            raise HTTPException(status_code=404, detail="Component is not in this build.")
        maximum = max_quantity(item["category"])
        if not 1 <= quantity <= maximum:
            raise HTTPException(status_code=422, detail=f"Quantity must be between 1 and {maximum}.")
        db.execute("UPDATE build_items SET quantity = ? WHERE id = ? AND build_id = ?", (quantity, item_id, build_id))
    return saved(request, f"/builds/{build_id}#slot-{item['category'].lower()}", "Quantity updated.")


@app.post("/builds/{build_id}/items/{item_id}/delete")
def delete_item(request: Request, build_id: int, item_id: int, confirmed: str = Form(""), csrf: str = Form(...)):
    user = require_user(request)
    check_token(request, csrf)
    require_confirmation(confirmed)
    with connection() as db:
        owned_build(db, build_id, user["id"])
        deleted = db.execute("DELETE FROM build_items WHERE id = ? AND build_id = ?", (item_id, build_id))
        if not deleted.rowcount:
            raise HTTPException(status_code=404, detail="Component is not in this build.")
    return saved(request, f"/builds/{build_id}", "Component removed.")


@app.get("/builds/{build_id}/edit", response_class=HTMLResponse)
def edit_build_form(request: Request, build_id: int):
    user = require_user(request)
    with connection() as db:
        build = owned_build(db, build_id, user["id"])
    return build_form(request, build)


@app.post("/builds/{build_id}/edit")
def edit_build(request: Request, build_id: int, title: str = Form(...), budget: str | None = Form(None), csrf: str = Form(...)):
    user = require_user(request)
    check_token(request, csrf)
    with connection() as db:
        build = owned_build(db, build_id, user["id"])
        amount = text_amount(build["budget_cents"]) if budget is None else budget
        try:
            name, cents = build_fields(title, amount)
        except ValueError as error:
            return build_form(request, build, title, amount, str(error))
        db.execute("UPDATE builds SET title = ?, budget_cents = ? WHERE id = ? AND user_id = ?", (name, cents, build_id, user["id"]))
    return saved(request, f"/builds/{build_id}", "Build updated.")


@app.get("/builds/{build_id}/delete", response_class=HTMLResponse)
def confirm_delete_build(request: Request, build_id: int):
    user = require_user(request)
    with connection() as db:
        build = owned_build(db, build_id, user["id"])
    return page(
        request, "confirm_delete.html", entity="build", name=build["title"],
        explanation="The build and its selected items will be deleted.",
        action=f"/builds/{build_id}/delete", cancel=f"/builds/{build_id}",
    )


@app.post("/builds/{build_id}/delete")
def delete_build(request: Request, build_id: int, confirmed: str = Form(""), csrf: str = Form(...)):
    user = require_user(request)
    check_token(request, csrf)
    with connection() as db:
        owned_build(db, build_id, user["id"])
        require_confirmation(confirmed)
        db.execute("DELETE FROM builds WHERE id = ? AND user_id = ?", (build_id, user["id"]))
    return saved(request, "/", "Build deleted.")

def part_view(row, context):
    """A catalogue row plus, when a build is chosen, its fit and what adding it would do."""
    view = dict(row, fit=None, action=None, after=None)
    if context:
        items = context["parts"]
        same = [item for item in items if item["category"] == row["category"]]
        view["fit"] = part_fit(row, items)
        if any(item["component_id"] == row["id"] for item in items):
            view["action"] = "in_build"
        elif row["category"] in SINGLE_CATEGORIES and same:
            view["action"] = "replace"
            view["after"] = context["total"] - same[0]["price_cents"] * same[0]["quantity"] + row["price_cents"]
        else:
            view["action"] = "add"
            view["after"] = context["total"] + row["price_cents"]
    return view


def catalogue_data(request, q, category, build, template):
    user = require_user(request)
    if len(q) > 80 or len(category) > 30:
        raise HTTPException(status_code=422, detail="Search text is too long.")
    with connection() as db:
        categories = db.execute("SELECT * FROM categories ORDER BY id").fetchall()
        if category and category not in {row["name"] for row in categories}:
            raise HTTPException(status_code=422, detail="Choose a category from the catalogue.")
        matches = lookup(db, q.strip(), "")
        builds = db.execute("SELECT id, title FROM builds WHERE user_id = ? ORDER BY id DESC", (user["id"],)).fetchall()
        context = None
        if build:
            owned = owned_build(db, build, user["id"])
            items = db.execute(ITEM_QUERY + " WHERE bi.build_id = ? ORDER BY cat.id", (build,)).fetchall()
            context = summarise(owned, items)
    counts = {row["name"]: 0 for row in categories}
    for row in matches:
        counts[row["category"]] += 1
    parts = [part_view(row, context) for row in matches if not category or row["category"] == category]
    if context:
        # Parts that fit the chosen build come first, conflicts last.
        parts.sort(key=lambda part: (
            CATEGORY_ORDER.index(part["category"]),
            {"ok": 0, "bad": 2}.get(part["fit"][0] if part["fit"] else "", 1),
        ))
    return page(
        request, template, components=parts, categories=categories, counts=counts, matches=len(matches),
        q=q, selected=category, context=context, builds=builds,
    )


@app.get("/components", response_class=HTMLResponse)
def component_list(request: Request, q: str = "", category: str = "", build: int = 0):
    return catalogue_data(request, q, category, build, "components.html")


@app.get("/components/results", response_class=HTMLResponse)
def component_results(request: Request, q: str = "", category: str = "", build: int = 0):
    return catalogue_data(request, q, category, build, "component_results.html")


def catalogue_form(request, component_id=None, values=None, error=None):
    with connection() as db:
        categories = db.execute("SELECT * FROM categories ORDER BY id").fetchall()
        if component_id is not None and values is None:
            row = find_component(db, component_id)
            values = dict(row, price=text_amount(row["price_cents"]))
    return page(
        request, "component_form.html",
        values=values or {"name": "", "price": "", "category_id": None, "socket": "", "ram_type": "", "specs": ""},
        categories=categories, ram_types=sorted(RAM_TYPES),
        heading="Edit component" if component_id is not None else "Add component", error=error,
    )


def find_component(db, component_id):
    component = db.execute("SELECT * FROM components WHERE id = ?", (component_id,)).fetchone()
    if component is None:
        raise HTTPException(status_code=404, detail="Component not found.")
    return component


def save_component(request, component_id, category_id, name, price, socket, ram_type, specs):
    try:
        with connection() as db:
            db.execute("BEGIN IMMEDIATE")
            category = db.execute("SELECT name FROM categories WHERE id = ?", (category_id,)).fetchone()
            if not category:
                raise ValueError("Choose an existing category.")
            values = (*component_values(category["name"], name, price, socket, ram_type), clean_specs(specs))
            if component_id is None:
                db.execute(INSERT_COMPONENT, (category_id, *values))
            else:
                previous = find_component(db, component_id)
                if previous["category_id"] != category_id and db.execute(
                    "SELECT 1 FROM build_items WHERE component_id = ?", (component_id,),
                ).fetchone():
                    raise ValueError("Category cannot change while this component is used in a build.")
                db.execute(
                    """UPDATE components SET category_id = ?, name = ?, price_cents = ?, socket = ?, ram_type = ?,
                       specs = ? WHERE id = ?""",
                    (category_id, *values, component_id),
                )
    except (ValueError, sqlite3.IntegrityError) as error:
        message = str(error) if isinstance(error, ValueError) else "A component with that name already exists."
        fields = dict(category_id=category_id, name=name, price=price, socket=socket, ram_type=ram_type, specs=specs)
        return catalogue_form(request, component_id, fields, message)
    return saved(request, "/components", "Component saved.")


@app.get("/components/new", response_class=HTMLResponse)
def component_form(request: Request):
    require_admin(request)
    return catalogue_form(request)


@app.post("/components/new")
def create_component(request: Request, category_id: int = Form(...), name: str = Form(...), price: str = Form(...),
                     socket: str = Form(""), ram_type: str = Form(""), specs: str = Form(""), csrf: str = Form(...)):
    require_admin(request)
    check_token(request, csrf)
    return save_component(request, None, category_id, name, price, socket, ram_type, specs)


@app.get("/components/{component_id}/edit", response_class=HTMLResponse)
def edit_component_form(request: Request, component_id: int):
    require_admin(request)
    return catalogue_form(request, component_id)


@app.post("/components/{component_id}/edit")
def edit_component(request: Request, component_id: int, category_id: int = Form(...), name: str = Form(...),
                   price: str = Form(...), socket: str = Form(""), ram_type: str = Form(""), specs: str = Form(""),
                   csrf: str = Form(...)):
    require_admin(request)
    check_token(request, csrf)
    return save_component(request, component_id, category_id, name, price, socket, ram_type, specs)


@app.get("/components/{component_id}/delete", response_class=HTMLResponse)
def confirm_delete_component(request: Request, component_id: int):
    require_admin(request)
    with connection() as db:
        component = find_component(db, component_id)
    return page(
        request, "confirm_delete.html", entity="component", name=component["name"],
        explanation="Components used in builds can be removed after all references are removed.",
        action=f"/components/{component_id}/delete", cancel="/components",
    )


@app.post("/components/{component_id}/delete")
def delete_component(request: Request, component_id: int, confirmed: str = Form(""), csrf: str = Form(...)):
    require_admin(request)
    check_token(request, csrf)
    require_confirmation(confirmed)
    try:
        with connection() as db:
            find_component(db, component_id)
            db.execute("DELETE FROM components WHERE id = ?", (component_id,))
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="This component is still used in a saved build.")
    return saved(request, "/components", "Component deleted.")


@app.get("/components/import", response_class=HTMLResponse)
def import_form(request: Request):
    require_admin(request)
    return page(request, "import_components.html", error=None)


@app.post("/components/import")
def import_components(request: Request, upload: UploadFile = File(...), csrf: str = Form(...)):
    require_admin(request)
    check_token(request, csrf)
    try:
        if not (upload.filename or "").lower().endswith(".csv"):
            raise ValueError("Choose a .csv file.")
        raw = upload.file.read(MAX_CSV_BYTES + 1)
        with connection() as db:
            categories = {row["name"]: row["id"] for row in db.execute("SELECT id, name FROM categories")}
            rows = csv_rows(raw, categories)
            db.executemany(INSERT_COMPONENT, rows)
    except (ValueError, sqlite3.IntegrityError) as error:
        message = str(error) if isinstance(error, ValueError) else "A component name is duplicated. No rows were imported."
        return page(request, "import_components.html", error=message)
    return saved(request, "/components", f"Imported {len(rows)} components.")

@app.get("/report", response_class=HTMLResponse)
def report(request: Request, build: int = 0):
    user = require_user(request)
    with connection() as db:
        if build:
            owned_build(db, build, user["id"])
        builds = db.execute("SELECT id, title FROM builds WHERE user_id = ? ORDER BY id DESC", (user["id"],)).fetchall()
        sheets = user_builds(db, user["id"], build or None)
    return page(request, "report.html", sheets=sheets, builds=builds, selected=build)


def safe_csv_text(value):
    # Avoid interpreting user-supplied titles as spreadsheet formulas.
    text = str(value)
    if text.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


@app.get("/report.csv")
def csv_report(request: Request, build: int = 0):
    user = require_user(request)
    with connection() as db:
        if build:
            owned_build(db, build, user["id"])
        sheets = user_builds(db, user["id"], build or None)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Build", "Category", "Component", "Quantity", "Unit price (EUR)", "Subtotal (EUR)"])
    for sheet in sheets:
        title = safe_csv_text(sheet["build"]["title"])
        for item in sheet["parts"]:
            writer.writerow([
                title, CATEGORY_LABELS[item["category"]], safe_csv_text(item["name"]), item["quantity"],
                amount(item["price_cents"]), amount(item["price_cents"] * item["quantity"]),
            ])
        writer.writerow([title, "Total", "", "", "", amount(sheet["total"])])
        if sheet["budget"]:
            writer.writerow([title, "Budget", "", "", "", amount(sheet["budget"])])
    name = f"build-{build}.csv" if build else "build-report.csv"
    return Response(output.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{name}"'})


@app.exception_handler(StarletteHTTPException)
async def friendly_error(request: Request, exc: HTTPException):
    response = page(request, "error.html", error=exc.detail)
    response.status_code = exc.status_code
    return response


@app.exception_handler(RequestValidationError)
async def invalid_form(request: Request, exc: RequestValidationError):
    return await friendly_error(request, HTTPException(
        status_code=422, detail="Check the form fields and try again.",
    ))
