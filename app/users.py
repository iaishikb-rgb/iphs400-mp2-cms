"""Users: argon2-hashed passwords, roles, the active flag."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from functools import cache

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_hasher = PasswordHasher()


@dataclass(frozen=True)
class User:
    id: int
    email: str
    role: str  # "admin" (President) or "editor" (Officer)
    active: bool
    display_name: str = ""


def normalize_email(email: str) -> str:
    return email.strip().lower()


def _row_to_user(row: sqlite3.Row) -> User:
    return User(row["id"], row["email"], row["role"], bool(row["active"]), row["display_name"])


def create_user(conn: sqlite3.Connection, email: str, password: str, role: str,
                display_name: str = "") -> None:
    with conn:
        conn.execute(
            "INSERT INTO users (email, password_hash, role, display_name) VALUES (?, ?, ?, ?)",
            (normalize_email(email), _hasher.hash(password), role, display_name.strip()),
        )


def set_display_name(conn: sqlite3.Connection, user_id: int, display_name: str) -> None:
    """The name shown in public bylines. Blank is refused: a byline needs a name."""
    display_name = display_name.strip()
    if not display_name:
        raise GuardRailError("A display name is required")
    if get_user(conn, user_id) is None:
        raise GuardRailError("Unknown User")
    with conn:
        conn.execute("UPDATE users SET display_name = ? WHERE id = ?", (display_name, user_id))


def get_user(conn: sqlite3.Connection, user_id: int) -> User | None:
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return _row_to_user(row) if row else None


def count_by_active(conn: sqlite3.Connection) -> tuple[int, int]:
    """(active, Deactivated) User counts."""
    row = conn.execute(
        "SELECT COALESCE(SUM(active), 0) AS a, COUNT(*) AS n FROM users").fetchone()
    return row["a"], row["n"] - row["a"]


def email_exists(conn: sqlite3.Connection, email: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM users WHERE email = ?", (normalize_email(email),)
    ).fetchone() is not None


@cache
def _dummy_hash() -> str:
    return _hasher.hash("not-a-real-password")


def authenticate(conn: sqlite3.Connection, email: str, password: str) -> User | None:
    """Return the User for a correct email and password, else None.

    Unknown email, wrong password and Deactivated all look the same to the
    caller, and unknown emails still cost one hash check so timing does not
    reveal which accounts exist.
    """
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?", (normalize_email(email),)
    ).fetchone()
    stored = row["password_hash"] if row else _dummy_hash()
    try:
        _hasher.verify(stored, password)
    except (VerificationError, InvalidHashError):
        return None
    if row is None or not row["active"]:
        return None
    return _row_to_user(row)


ROLES = ("admin", "editor")
EMAIL_DOMAIN = "@kenyon.edu"
MIN_PASSWORD_LENGTH = 8


class GuardRailError(ValueError):
    """A change the rules forbid; the message is shown to the President."""


def list_users(conn: sqlite3.Connection) -> list[User]:
    rows = conn.execute("SELECT * FROM users ORDER BY active DESC, email").fetchall()
    return [_row_to_user(r) for r in rows]


def _active_presidents(conn: sqlite3.Connection) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM users WHERE role = 'admin' AND active = 1").fetchone()[0]


def _keeps_a_president(conn: sqlite3.Connection, target: User) -> bool:
    """False when `target` is the last active President."""
    return not (target.role == "admin" and target.active and _active_presidents(conn) <= 1)


def set_role(conn: sqlite3.Connection, user_id: int, role: str, acting_id: int) -> None:
    target = get_user(conn, user_id)
    if target is None or role not in ROLES:
        raise GuardRailError("Unknown User or role")
    if role != target.role and user_id == acting_id:
        raise GuardRailError("You cannot change your own role")
    if role != "admin" and not _keeps_a_president(conn, target):
        raise GuardRailError("The last active President cannot be demoted")
    with conn:
        conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))


def set_active(conn: sqlite3.Connection, user_id: int, active: bool, acting_id: int) -> None:
    target = get_user(conn, user_id)
    if target is None:
        raise GuardRailError("Unknown User")
    if not active:
        if user_id == acting_id:
            raise GuardRailError("You cannot deactivate yourself")
        if not _keeps_a_president(conn, target):
            raise GuardRailError("The last active President cannot be deactivated")
    with conn:
        conn.execute("UPDATE users SET active = ? WHERE id = ?", (int(active), user_id))
