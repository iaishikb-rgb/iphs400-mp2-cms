"""Shared test fixtures.

`client` gives you the app. `client_as(role)` gives you a client that is logged
in as a seeded user of that role — it works as soon as your login route exists,
so access-control tests stay one line:

    def test_editor_cannot_manage_users(client_as):
        assert client_as("editor").get("/admin/users").status_code in (302, 403)
"""
from __future__ import annotations

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


@pytest.fixture
def client_as(make_app):
    """Return a factory: client_as("editor") -> a logged-in TestClient."""

    def _csrf(c: TestClient) -> str:
        page = c.get("/login")
        return page.text.split('name="csrf_token" value="')[1].split('"')[0]

    def _login(role: str) -> TestClient:
        user = DEMO_USERS[role]
        c = TestClient(make_app())
        response = c.post("/login", data={"email": user["email"],
                                          "password": user["password"],
                                          "csrf_token": _csrf(c)},
                          follow_redirects=False)
        assert response.status_code in (200, 302, 303), (
            f"Login as {role} failed with {response.status_code}")
        return c

    return _login
