"""Bug #10: save confirmations, greeting by display name, site name."""
import re

from app import db
from tests.conftest import csrf_of
from tests.test_t06_users import act, find, make_user


def status_text(response):
    m = re.search(r'<p role="status">([^<]*)</p>', response.text)
    return m.group(1) if m else None


def follow(client, response):
    assert response.status_code == 303
    return client.get(response.headers["location"])


def test_save_draft_shows_saved_on_create_and_update(client_as):
    editor = client_as("editor")
    token = csrf_of(editor, "/admin/posts/new")
    r = editor.post("/admin/posts", data={"title": "Hi", "body": "x", "csrf_token": token},
                    follow_redirects=False)
    page = follow(editor, r)
    assert status_text(page) == "Saved."
    assert status_text(editor.get(r.headers["location"])) is None  # shown once only
    r = editor.post(r.headers["location"], data={"title": "Hi2", "body": "y",
                                                 "csrf_token": csrf_of(editor, r.headers["location"])},
                    follow_redirects=False)
    assert status_text(follow(editor, r)) == "Saved."


def test_save_page_shows_saved(client_as):
    admin = client_as("admin")
    token = csrf_of(admin, "/admin/pages/new")
    r = admin.post("/admin/pages", data={"title": "About", "body": "x", "nav_order": "1",
                                         "csrf_token": token}, follow_redirects=False)
    assert status_text(follow(admin, r)) == "Saved."
    loc = r.headers["location"]
    r = admin.post(loc, data={"title": "About", "body": "z", "nav_order": "1",
                              "csrf_token": csrf_of(admin, loc)}, follow_redirects=False)
    assert status_text(follow(admin, r)) == "Saved."


def test_user_actions_show_a_status_message(client_as):
    admin = client_as("admin")
    assert status_text(follow(admin, make_user(admin))) == "User created."
    assert status_text(follow(admin, act(admin, "new@kenyon.edu", "role", role="admin"))) == "Role changed."
    assert status_text(follow(admin, act(admin, "new@kenyon.edu", "name", display_name="N P"))) == "Name saved."
    assert status_text(follow(admin, act(admin, "new@kenyon.edu", "deactivate"))) == "User deactivated."
    assert status_text(follow(admin, act(admin, "new@kenyon.edu", "reactivate"))) == "User reactivated."


def test_failed_post_shows_no_success_message(client_as):
    editor = client_as("editor")
    token = csrf_of(editor, "/admin/posts/new")
    r = editor.post("/admin/posts", data={"title": " ", "body": "x", "csrf_token": token})
    assert r.status_code == 400 and status_text(r) is None


def test_dashboard_greets_by_display_name(client_as):
    assert "Hello Aishik Biswas" in client_as("admin").get("/admin").text
    officer = client_as("editor").get("/admin").text
    assert "Hello Club Officer" in officer and "Hello admin" not in officer


def test_example_env_names_the_club():
    from pathlib import Path
    text = (Path(__file__).parents[1] / ".env.example").read_text()
    assert "CMS_SITE_TITLE=Kenyon College Finance Club" in text
    assert "Knox County" not in text


def test_guard_rail_refusal_shows_no_success_message(client_as):
    admin = client_as("admin")
    own = find(admin, "admin@example.test")
    r = admin.post(f"/admin/users/{own}/deactivate",
                   data={"csrf_token": csrf_of(admin, "/admin/users")}, follow_redirects=False)
    assert r.status_code == 400 and status_text(r) is None
