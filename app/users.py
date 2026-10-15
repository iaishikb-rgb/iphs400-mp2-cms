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


def normalize_email(email: str) -> str:
    return email.strip().lower()


def _row_to_user(row: sqlite3.Row) -> User:
    return User(row["id"], row["email"], row["role"], bool(row["active"]))


def create_user(conn: sqlite3.Connection, email: str, password: str, role: str) -> None:
    with conn:
        conn.execute(
            "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
            (normalize_email(email), _hasher.hash(password), role),
        )


def get_user(conn: sqlite3.Connection, user_id: int) -> User | None:
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return _row_to_user(row) if row else None


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
