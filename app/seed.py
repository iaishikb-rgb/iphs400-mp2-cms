"""Create the demo President and Officer. Safe to run repeatedly."""
from __future__ import annotations

from pathlib import Path

from app import db, users


DEMO_NAMES = {"admin": "Demo President", "editor": "Demo Officer"}


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
            users.create_user(conn, email, password, role, DEMO_NAMES.get(role, ""))
            created.append(email)
        elif role in DEMO_NAMES:  # accounts made before display names existed
            conn.execute("UPDATE users SET display_name = ? WHERE email = ? AND display_name = ''",
                         (DEMO_NAMES[role], users.normalize_email(email)))
            conn.commit()
    conn.close()
    return created
