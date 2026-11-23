import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pytest
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient
from db import init_database
from app import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("PCBUILDER_DB", str(tmp_path / "test.db"))
    init_database()
    with TestClient(app) as c:
        yield c


def csrf(client, url):
    response = client.get(url)
    assert response.status_code == 200
    form = BeautifulSoup(response.text, "html.parser")
    token = form.select_one('input[name="csrf"]')
    assert token is not None, response.text[:500]
    return token["value"]


def login(client, username="student"):
    value = csrf(client, "/login")
    result = client.post("/login", data={"username": username, "password": "demo12345", "csrf": value}, follow_redirects=False)
    assert result.status_code == 303


def new_build(client, title="Office PC"):
    result = client.post("/builds/new", data={"title": title, "budget": "850", "csrf": csrf(client, "/builds/new")}, follow_redirects=False)
    assert result.status_code == 303
    return int(result.headers["location"].split("/")[-1])


def test_login_and_create_build_with_components(client):
    assert client.get("/").status_code == 200
    login(client)
    build_id = new_build(client)
    response = client.get(f"/builds/{build_id}")
    assert response.status_code == 200 and "Office PC" in response.text
    # AMD Ryzen 5 7600 is the first catalogue entry.
    result = client.post(f"/builds/{build_id}/items", data={"component_id": 1, "csrf": csrf(client, f"/builds/{build_id}")}, follow_redirects=False)
    assert result.status_code == 303
    assert "€190.00" in client.get(f"/builds/{build_id}").text
    assert "Office PC" in client.get("/report").text
    assert "Office PC" in client.get("/report.csv").text


def test_build_update_delete_and_xss_escaping(client):
    login(client)
    build_id = new_build(client, title='<script>alert(1)</script>')
    body = client.get(f"/builds/{build_id}").text
    assert "&lt;script&gt;" in body
    assert "<script>alert(1)</script>" not in body
    result = client.post(f"/builds/{build_id}/edit", data={"title": "Renamed build", "csrf": csrf(client, f"/builds/{build_id}/edit")}, follow_redirects=False)
    assert result.status_code == 303
    assert "Renamed build" in client.get(f"/builds/{build_id}").text
    result = client.post(f"/builds/{build_id}/delete", data={"confirmed": "yes", "csrf": csrf(client, f"/builds/{build_id}")}, follow_redirects=False)
    assert result.status_code == 303
    assert client.get(f"/builds/{build_id}").status_code == 404


def test_csrf_blocks_write(client):
    login(client)
    resp = client.post("/builds/new", data={"title": "No CSRF", "budget": "100", "csrf": "wrong"})
    assert resp.status_code == 403
    assert "No CSRF" not in client.get("/").text


def test_role_blocks_admin_only(client):
    login(client)
    assert client.get("/components/new").status_code == 403
    assert client.post("/components/new", data={"category_id": 1, "name": "Illegal part", "price": "1", "csrf": csrf(client, "/builds/new")}).status_code == 403
    assert "Illegal part" not in client.get("/components").text


def test_admin_can_add_component(client):
    login(client, "admin")
    result = client.post("/components/new", data={"category_id": 1, "name": "Test processor", "price": "9.95", "socket": "AM5", "csrf": csrf(client, "/components/new")}, follow_redirects=False)
    assert result.status_code == 303
    page = client.get("/components?category=CPU&q=Test")
    assert "Test processor" in page.text and "€9.95" in page.text


def test_unauthorized_own_build(client):
    login(client)
    build_id = new_build(client)
    client.post("/logout", data={"csrf": csrf(client, "/builds/new")})
    login(client, "admin")
    assert client.get(f"/builds/{build_id}").status_code == 404
    assert client.post(f"/builds/{build_id}/delete", data={"csrf": csrf(client, "/builds/new")}).status_code == 404


def test_search_sql_injection_is_data(client):
    login(client)
    page = client.get("/components?q=%27%20OR%201%3D1%20--&category=CPU")
    assert page.status_code == 200
    assert "No components found." in page.text


def test_csv_formula_not_executed(client):
    login(client)
    new_build(client, title='=1+2')
    report = client.get('/report.csv').text
    assert "'=1+2" in report


def test_reject_invalid_budget(client):
    login(client)
    result = client.post('/builds/new', data={'title':'Bad budget','budget':'-10','csrf':csrf(client,'/builds/new')})
    assert result.status_code == 200
    assert 'Budget must be' in result.text
    assert 'Bad budget' not in client.get('/').text


def test_duplicate_component_is_rejected(client):
    login(client)
    build_id = new_build(client)
    endpoint = f'/builds/{build_id}/items'
    first = client.post(endpoint,data={'component_id':1,'csrf':csrf(client,f'/builds/{build_id}')})
    assert first.status_code == 200
    second = client.post(endpoint,data={'component_id':1,'csrf':csrf(client,f'/builds/{build_id}')})
    assert second.status_code == 400
    assert 'already in the build' in second.text

def test_view_cookie_requires_csrf_and_survives_logout(client):
    login(client)
    new_build(client)
    response = client.post("/preferences/build-view", data={"view": "list", "csrf": csrf(client, "/")})
    assert response.status_code == 200
    assert 'class="build-list"' in response.text
    assert client.cookies.get("pcbuild_view") == "list"
    client.post("/logout", data={"csrf": csrf(client, "/")})
    assert client.cookies.get("pcbuild_view") == "list"


def test_delete_requires_explicit_confirmation(client):
    login(client)
    build_id = new_build(client)
    url = f"/builds/{build_id}/delete"
    token = csrf(client, url)
    assert client.post(url, data={"csrf": token}).status_code == 422
    assert client.get(f"/builds/{build_id}").status_code == 200
    assert client.post(url, data={"csrf": token, "confirmed": "yes"}, follow_redirects=False).status_code == 303


def test_component_fragment_and_permission(client):
    assert client.get("/components/results?q=AM5&category=CPU").status_code == 401
    login(client)
    response = client.get("/components/results?q=AM5&category=CPU")
    assert response.status_code == 200
    assert "AMD Ryzen 5 7600" in response.text
    assert "motherboard" not in response.text
    assert client.get("/components/import").status_code == 403
    assert client.get("/components/1/edit").status_code == 403


def test_import_update_delete_component(client):
    login(client, "admin")
    data = b"category,name,price_eur,socket,ram_type\nStorage,Lab SSD,29.95,,\n"
    response = client.post(
        "/components/import",
        files={"upload": ("sample.csv", data, "text/csv")},
        data={"csrf": csrf(client, "/components/import")},
        follow_redirects=False,
    )
    assert response.status_code == 303
    document = BeautifulSoup(client.get("/components?q=Lab%20SSD&category=Storage").text, "html.parser")
    edit = document.select_one('a[aria-label="Edit Lab SSD"]')["href"]
    delete = edit.removesuffix("edit") + "delete"
    form = BeautifulSoup(client.get(edit).text, "html.parser")
    category_id = form.select_one("#category_id option[selected]")["value"]
    patch = {"name": "Updated Lab SSD", "price": "34.99", "category_id": category_id, "csrf": csrf(client, edit)}
    assert client.post(edit, data=patch, follow_redirects=False).status_code == 303
    assert "Updated Lab SSD" in client.get("/components").text
    assert client.post(delete, data={"confirmed": "yes", "csrf": csrf(client, delete)}, follow_redirects=False).status_code == 303
    assert "Updated Lab SSD" not in client.get("/components").text


def test_logout_revokes_previously_issued_session(client):
    login(client)
    cookie = client.cookies.get("pcbuild_session")
    client.post("/logout", data={"csrf": csrf(client, "/")})
    client.cookies.clear()
    client.cookies.set("pcbuild_session", cookie)
    assert client.get("/builds/new").status_code == 401


def test_build_summary_shows_total_budget_and_compatibility(client):
    login(client)
    token = csrf(client, "/builds/new")
    result = client.post("/builds/new", data={"title": "Campus PC", "budget": "800", "csrf": token}, follow_redirects=False)
    build_id = int(result.headers["location"].split("/")[-1])
    for component_id in (1, 3, 5):  # AMD Ryzen 5 7600, MSI PRO B650M-A WIFI, Kingston FURY Beast DDR5 kit
        client.post(f"/builds/{build_id}/items", data={"component_id": component_id, "csrf": csrf(client, f"/builds/{build_id}")})
    document = BeautifulSoup(client.get(f"/builds/{build_id}").text, "html.parser")
    assert document.select_one(".summary-total .total").get_text(strip=True) == "€375.00"
    assert "€425.00 left" in document.select_one(".budget-state").get_text()
    assert document.select_one(".compat .status-ok").get_text(strip=True) == "Compatible"
    assert document.select_one('#component option[value="1"]').has_attr("disabled")
    assert "€375.00" in client.get("/report").text
