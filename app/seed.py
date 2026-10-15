"""Create the demo President and Officer. Safe to run repeatedly."""
from __future__ import annotations

from pathlib import Path

from app import db, users


def seed_users(database: Path, accounts: dict[str, tuple[str, str]]) -> list[str]:
    """accounts maps role -> (email, password). Existing emails are left alone.

    Returns the emails that were created. Passwords are hashed by users.create_user
    and are never printed or stored as text.
    """
    db.init_db(database)
    conn = db.connect(database)
    created = []
    for role, (email, password) in accounts.items():
        if not users.email_exists(conn, email):
            users.create_user(conn, email, password, role)
            created.append(email)
    conn.close()
    return created
