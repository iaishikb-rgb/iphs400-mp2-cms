"""T06: President-only User management. Seam 1: the HTTP app."""
from fastapi.testclient import TestClient

from app import db, posts, users
from tests.conftest import csrf_of, sign_in
from tests.test_t02_posts import create_post, post_url
from tests.test_t03_president_control import president_for


def make_user(admin, email="new@kenyon.edu", role="editor", password="first-pw-123"):
    token = csrf_of(admin, "/admin/users")
    return admin.post("/admin/users", data={"email": email, "role": role,
                                            "password": password, "csrf_token": token},
                      follow_redirects=False)


def find(admin, email):
    conn = db.connect(admin.app.state.database)
    row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    return row["id"]


def act(admin, email, action, **extra):
    uid = find(admin, email)
    token = csrf_of(admin, "/admin/users")
    return admin.post(f"/admin/users/{uid}/{action}",
                      data={"csrf_token": token, **extra}, follow_redirects=False)


def test_president_creates_a_user_with_a_hashed_first_password(client_as):
    admin = client_as("admin")
    assert make_user(admin).status_code == 303
    assert "new@kenyon.edu" in admin.get("/admin/users").text
    conn = db.connect(admin.app.state.database)
    stored = conn.execute("SELECT password_hash FROM users WHERE email = 'new@kenyon.edu'"
                          ).fetchone()[0]
    assert stored.startswith("$argon2") and "first-pw-123" not in stored
    # signs in at once with the President-set password, no forced change
    fresh = TestClient(admin.app)
    assert sign_in(fresh, "new@kenyon.edu", "first-pw-123").status_code == 303
    assert fresh.get("/admin").status_code == 200


def test_create_rejects_bad_input(client_as):
    admin = client_as("admin")
    assert make_user(admin, email="x@gmail.com").status_code == 400
    assert make_user(admin, email="a@b@kenyon.edu").status_code == 400
    assert make_user(admin, password="short").status_code == 400
    assert make_user(admin, role="root").status_code == 400
    assert make_user(admin).status_code == 303
    assert make_user(admin).status_code == 400  # duplicate


def test_president_changes_a_role(client_as):
    admin = client_as("admin")
    assert act(admin, "editor@example.test", "role", role="admin").status_code == 303
    conn = db.connect(admin.app.state.database)
    assert users.get_user(conn, find(admin, "editor@example.test")).role == "admin"


def test_deactivated_user_cannot_sign_in_and_open_session_ends(client_as):
    editor = client_as("editor")
    admin = president_for(editor)
    assert editor.get("/admin").status_code == 200
    assert act(admin, "editor@example.test", "deactivate").status_code == 303
    assert editor.get("/admin", follow_redirects=False).status_code == 303  # next action
    fresh = TestClient(admin.app)
    assert sign_in(fresh, "editor@example.test", "test-editor-pw").status_code != 303
    assert fresh.get("/admin", follow_redirects=False).status_code == 303


def test_president_reactivates(client_as):
    editor = client_as("editor")
    admin = president_for(editor)
    act(admin, "editor@example.test", "deactivate")
    assert act(admin, "editor@example.test", "reactivate").status_code == 303
    fresh = TestClient(admin.app)
    assert sign_in(fresh, "editor@example.test", "test-editor-pw").status_code == 303
    assert fresh.get("/admin").status_code == 200


def test_there_is_no_delete_user_action(client_as):
    admin = client_as("admin")
    uid = find(admin, "editor@example.test")
    token = csrf_of(admin, "/admin/users")
    r = admin.post(f"/admin/users/{uid}/delete", data={"csrf_token": token},
                   follow_redirects=False)
    assert r.status_code in (404, 405)
    r = admin.delete(f"/admin/users/{uid}", headers={"x-csrf": token}, follow_redirects=False)
    assert r.status_code in (403, 404, 405)
    assert "/delete" not in admin.get("/admin/users").text
    assert find(admin, "editor@example.test") == uid


def test_deactivated_users_posts_still_show_their_name(client_as):
    editor = client_as("editor")
    url = post_url(create_post(editor, title="Recap: alumni call"))
    admin = president_for(editor)
    act(admin, "editor@example.test", "deactivate")
    conn = db.connect(admin.app.state.database)
    post = posts.get_post(conn, int(url.rsplit("/", 1)[1]))
    assert post.author_email == "editor@example.test"
    assert [p.author_email for p in posts.list_posts(conn)] == ["editor@example.test"]


def test_last_active_president_is_protected(client_as):
    admin = client_as("admin")
    assert act(admin, "admin@example.test", "deactivate").status_code == 400  # self + last
    assert act(admin, "admin@example.test", "role", role="editor").status_code == 400
    conn = db.connect(admin.app.state.database)
    me = users.get_user(conn, find(admin, "admin@example.test"))
    assert me.active and me.role == "admin"


def test_president_cannot_deactivate_or_demote_self(client_as):
    admin = client_as("admin")
    make_user(admin, email="second@kenyon.edu", role="admin")
    assert act(admin, "admin@example.test", "deactivate").status_code == 400
    assert act(admin, "admin@example.test", "role", role="editor").status_code == 400
    other = TestClient(admin.app)
    sign_in(other, "second@kenyon.edu", "first-pw-123")
    assert act(other, "admin@example.test", "deactivate").status_code == 303
    # second is now the last active President
    assert act(other, "second@kenyon.edu", "role", role="editor").status_code == 400


def test_officer_is_refused_everywhere(client_as):
    editor = client_as("editor")
    assert "/admin/users" not in editor.get("/admin").text
    assert editor.get("/admin/users").status_code == 403
    token = csrf_of(editor, "/admin")
    uid = find(editor, "admin@example.test")
    for path, data in (("/admin/users", {"email": "z@kenyon.edu", "role": "admin",
                                         "password": "long-enough-pw"}),
                       (f"/admin/users/{uid}/role", {"role": "editor"}),
                       (f"/admin/users/{uid}/deactivate", {}),
                       (f"/admin/users/{uid}/reactivate", {})):
        r = editor.post(path, data={**data, "csrf_token": token}, follow_redirects=False)
        assert r.status_code == 403, path
    assert users.get_user(db.connect(editor.app.state.database), uid).active


def test_president_dashboard_links_to_users(client_as):
    assert "/admin/users" in client_as("admin").get("/admin").text
