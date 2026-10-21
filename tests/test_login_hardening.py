"""S2: login hardening. Through the HTTP app (seam 1)."""
from tests.conftest import sign_in


def test_same_error_for_wrong_password_and_unknown_email(client):
    wrong_pw = sign_in(client, "admin@example.test", "nope")
    unknown = sign_in(client, "nobody@example.test", "nope")
    assert wrong_pw.status_code == unknown.status_code == 401
    assert "Email or password is incorrect" in wrong_pw.text
    assert "Email or password is incorrect" in unknown.text
