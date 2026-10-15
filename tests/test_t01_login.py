"""T01: sign in and out. All through the HTTP app (seam 1)."""
import re


def csrf_of(client, path="/login"):
    html = client.get(path).text
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def sign_in(client, email, password, token=None):
    return client.post(
        "/login",
        data={"email": email, "password": password,
              "csrf_token": token or csrf_of(client)},
        follow_redirects=False,
    )


def test_user_signs_in_and_lands_on_admin(client):
    response = sign_in(client, "admin@example.test", "test-admin-pw")
    assert response.status_code == 303
    assert response.headers["location"] == "/admin"
    assert client.get("/admin").status_code == 200


def test_user_signs_out(client):
    sign_in(client, "admin@example.test", "test-admin-pw")
    response = client.post("/logout", data={"csrf_token": csrf_of(client, "/admin")},
                           follow_redirects=False)
    assert response.status_code == 303
    assert client.get("/admin", follow_redirects=False).status_code == 303


def test_wrong_password_and_unknown_email_get_the_same_message(client):
    wrong_pw = sign_in(client, "admin@example.test", "nope")
    unknown = sign_in(client, "nobody@example.test", "nope")
    for response in (wrong_pw, unknown):
        assert response.status_code == 401
        assert "Email or password is incorrect" in response.text
    assert client.get("/admin", follow_redirects=False).status_code == 303


def test_anonymous_admin_requests_redirect_to_login(client):
    for path in ("/admin", "/admin/users", "/admin/anything/at/all"):
        response = client.get(path, follow_redirects=False)
        assert response.status_code == 303, path
        assert response.headers["location"] == "/login"
    posted = client.post("/admin/anything", follow_redirects=False)
    assert posted.status_code == 303 and posted.headers["location"] == "/login"


def test_post_without_valid_csrf_token_is_rejected(client):
    no_token = client.post("/login", data={"email": "admin@example.test",
                                           "password": "test-admin-pw"})
    bad_token = sign_in(client, "admin@example.test", "test-admin-pw", token="forged")
    assert no_token.status_code == bad_token.status_code == 403
    assert client.get("/admin", follow_redirects=False).status_code == 303


def test_logout_without_csrf_token_is_rejected(client_as):
    c = client_as("admin")
    assert c.post("/logout", follow_redirects=False).status_code == 403
    assert c.get("/admin").status_code == 200


def test_idle_session_is_signed_out_after_two_hours(client, clock):
    sign_in(client, "admin@example.test", "test-admin-pw")
    clock.advance(2 * 3600 + 1)
    response = client.get("/admin", follow_redirects=False)
    assert response.status_code == 303 and response.headers["location"] == "/login"


def test_activity_keeps_the_session_alive(client, clock):
    sign_in(client, "admin@example.test", "test-admin-pw")
    for _ in range(3):
        clock.advance(2 * 3600 - 60)
        assert client.get("/admin").status_code == 200


def test_client_as_signs_in_each_role(client_as):
    for role in ("admin", "editor"):
        assert client_as(role).get("/admin").status_code == 200


def test_role_guard_refuses_an_editor_but_admits_an_admin(make_app, client_as):
    from fastapi import Depends
    from fastapi.testclient import TestClient

    from app import auth
    from tests.conftest import DEMO_USERS

    application = make_app()

    @application.get("/admin-only-probe")
    def probe(user=Depends(auth.require_role("admin"))):
        return {"role": user.role}

    def signed_in(role):
        c = TestClient(application)
        sign_in(c, DEMO_USERS[role]["email"], DEMO_USERS[role]["password"])
        return c

    assert signed_in("editor").get("/admin-only-probe").status_code == 403
    assert signed_in("admin").get("/admin-only-probe").json() == {"role": "admin"}


def test_seed_stores_only_argon2_hashes(tmp_path):
    import sqlite3

    from app.seed import seed_users

    db = tmp_path / "seed.db"
    seed_users(db, {"admin": ("p@example.test", "s3cret-pw"),
                    "editor": ("o@example.test", "an0ther-pw")})
    seed_users(db, {"admin": ("p@example.test", "s3cret-pw")})  # idempotent
    rows = sqlite3.connect(db).execute("SELECT role, password_hash FROM users").fetchall()
    assert sorted(r[0] for r in rows) == ["admin", "editor"]
    assert all(h.startswith("$argon2") for _, h in rows)
    assert not any(pw in h for _, h in rows for pw in ("s3cret-pw", "an0ther-pw"))
