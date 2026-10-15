"""Shared test fixtures.

`client` gives you the app. `client_as(role)` gives you a client that is logged
in as a seeded user of that role — it works as soon as your login route exists,
so access-control tests stay one line:

    def test_editor_cannot_manage_users(client_as):
        assert client_as("editor").get("/admin/users").status_code in (302, 403)
"""
from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

# Matches scripts/seed_demo.py. Passwords come from the environment there; in
# tests they are fixed and meaningless.
DEMO_USERS = {
    "admin": {"email": "admin@example.test", "password": "test-admin-pw"},
    "editor": {"email": "editor@example.test", "password": "test-editor-pw"},
}


class FakeClock:
    """Injected clock so idle sign-out is tested without waiting."""

    def __init__(self, now: float = 1_000_000.0):
        self.now = now

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def make_app(tmp_path, clock):
    """Factory for a fresh app on its own seeded database and the fake clock."""
    from app.seed import seed_users

    def _make():
        db = tmp_path / "test.db"
        application = create_app(database=db, clock=clock)
        seed_users(db, {role: (u["email"], u["password"])
                        for role, u in DEMO_USERS.items()})
        return application

    return _make


@pytest.fixture
def client(make_app) -> TestClient:
    return TestClient(make_app())


def csrf_of(client: TestClient, path: str = "/login") -> str:
    """Read the CSRF token out of the form on `path`."""
    html = client.get(path).text
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def sign_in(client: TestClient, email: str, password: str, token: str | None = None):
    return client.post(
        "/login",
        data={"email": email, "password": password,
              "csrf_token": token or csrf_of(client)},
        follow_redirects=False,
    )


@pytest.fixture
def client_as(make_app):
    """Return a factory: client_as("editor") -> a logged-in TestClient."""

    def _login(role: str) -> TestClient:
        user = DEMO_USERS[role]
        c = TestClient(make_app())
        response = sign_in(c, user["email"], user["password"])
        assert response.status_code in (200, 302, 303), (
            f"Login as {role} failed with {response.status_code}")
        return c

    return _login
