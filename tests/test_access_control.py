"""D3: access control for every /admin route, discovered from the app's own router.

Default-deny: a route is admin-only unless it is listed in EDITOR_ALLOWED, so a
new admin route that forgets its guard fails here without anyone remembering to
add a test. Seam 1: the HTTP app.
"""
import re

import pytest
from fastapi.testclient import TestClient

from tests.conftest import csrf_of
from tests.test_t02_posts import create_post, post_url
from tests.test_t03_president_control import president_for
from tests.test_t05_pages import create_page, page_url

# What an Officer (role "editor") may touch. Everything else under /admin is President-only.
EDITOR_ALLOWED = {
    ("GET", "/admin"),
    ("GET", "/admin/posts"), ("POST", "/admin/posts"),
    ("GET", "/admin/posts/new"), ("POST", "/admin/posts/preview"),
    ("GET", "/admin/posts/{post_id}"), ("POST", "/admin/posts/{post_id}"),
    ("GET", "/admin/posts/{post_id}/delete"), ("POST", "/admin/posts/{post_id}/delete"),
}


def admin_routes(app):
    paths = app.openapi()["paths"]
    return sorted((method.upper(), path) for path, ops in paths.items()
                  if path == "/admin" or path.startswith("/admin/") for method in ops)


def fill(template: str, ids: dict) -> str:
    return re.sub(r"\{(\w+)\}", lambda m: str(ids[m.group(1)]), template)


@pytest.fixture
def world(client_as):
    """An app with a post, a page, and a user to aim requests at."""
    editor = client_as("editor")
    post_id = post_url(create_post(editor)).rsplit("/", 1)[1]
    admin = president_for(editor)
    page_id = page_url(create_page(admin)).rsplit("/", 1)[1]
    ids = {"post_id": post_id, "page_id": page_id, "user_id": 1}
    return editor, ids


def test_editor_allowed_list_matches_real_routes(client):
    known = set(admin_routes(client.app))
    assert EDITOR_ALLOWED <= known, EDITOR_ALLOWED - known
    assert len(known - EDITOR_ALLOWED) >= 20  # pages, users and publish routes are all in scope


def test_anonymous_is_redirected_to_login_on_every_admin_route(client, world):
    _, ids = world
    anon = TestClient(client.app)
    for method, template in admin_routes(client.app):
        r = anon.request(method, fill(template, ids), data={} if method == "POST" else None,
                         follow_redirects=False)
        assert r.status_code in (302, 303), (method, template, r.status_code)
        assert r.headers["location"] == "/login", (method, template)


def test_editor_is_refused_on_every_admin_only_route(world):
    editor, ids = world
    token = csrf_of(editor, "/admin/posts/new")
    refused = [(m, t) for m, t in admin_routes(editor.app) if (m, t) not in EDITOR_ALLOWED]
    assert refused
    for method, template in refused:
        r = editor.request(method, fill(template, ids),
                           data={"csrf_token": token, "title": "x", "body": "x", "role": "editor",
                                 "email": "x@kenyon.edu", "password": "long-enough-pw",
                                 "display_name": "X"} if method == "POST" else None,
                           follow_redirects=False)
        assert r.status_code in (302, 303, 403), (method, template, r.status_code)
        if r.status_code in (302, 303):
            assert r.headers["location"] == "/login", (method, template)


def test_browser_gets_a_friendly_403_page_and_api_clients_keep_json(client_as):
    editor = client_as("editor")
    page = editor.get("/admin/users", headers={"accept": "text/html"})
    assert page.status_code == 403
    assert "Not allowed" in page.text and 'href="/admin"' in page.text
    plain = editor.get("/admin/users", headers={"accept": "application/json"})
    assert plain.status_code == 403 and plain.json()["detail"]
