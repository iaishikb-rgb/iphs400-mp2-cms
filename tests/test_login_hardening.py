"""S2: login hardening. Through the HTTP app (seam 1)."""
from tests.conftest import sign_in


def test_same_error_for_wrong_password_and_unknown_email(client):
    wrong_pw = sign_in(client, "admin@example.test", "nope")
    unknown = sign_in(client, "nobody@example.test", "nope")
    assert wrong_pw.status_code == unknown.status_code == 401
    assert "Email or password is incorrect" in wrong_pw.text
    assert "Email or password is incorrect" in unknown.text


ADMIN = "admin@example.test"
EDITOR = "editor@example.test"


def _fail_five_times(client, email):
    for _ in range(5):
        assert sign_in(client, email, "nope").status_code == 401


def test_sixth_attempt_refused_even_with_right_password(client, clock):
    _fail_five_times(client, ADMIN)
    response = sign_in(client, ADMIN, "test-admin-pw")
    assert response.status_code == 429
    assert client.get("/admin", follow_redirects=False).status_code != 200


def test_login_works_again_after_15_minutes(client, clock):
    _fail_five_times(client, ADMIN)
    assert sign_in(client, ADMIN, "test-admin-pw").status_code == 429
    clock.advance(15 * 60 + 1)
    assert sign_in(client, ADMIN, "test-admin-pw").status_code == 303


def test_lockout_is_per_account_other_email_still_logs_in(client, clock):
    _fail_five_times(client, ADMIN)
    assert sign_in(client, ADMIN, "test-admin-pw").status_code == 429
    assert sign_in(client, EDITOR, "test-editor-pw").status_code == 303
