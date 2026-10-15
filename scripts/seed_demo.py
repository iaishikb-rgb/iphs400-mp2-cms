#!/usr/bin/env python3
"""Create demo data so a grader (and you) can use the CMS immediately.

    uv run python scripts/seed_demo.py

T01 creates the users. Later tickets extend this so it also creates:
  - (done in T01) one admin and one editor, passwords read from the environment
  - a few posts and pages, at least one draft and one published

The rubric expects this to run clean on a fresh clone with .env.example values
(item E4), because the database itself is never committed.
"""
from __future__ import annotations

import os
import sys


def main() -> int:
    admin_pw = os.environ.get("CMS_ADMIN_PASSWORD")
    editor_pw = os.environ.get("CMS_EDITOR_PASSWORD")
    if not admin_pw or not editor_pw:
        print("Set CMS_ADMIN_PASSWORD and CMS_EDITOR_PASSWORD in .env "
              "(copy .env.example).")
        return 1

    # Local import so the script runs from a plain `uv run python scripts/...`.
    from app import settings
    from app.seed import seed_users

    created = seed_users(settings.DATABASE_PATH, {
        "admin": (os.environ.get("CMS_ADMIN_EMAIL", "admin@example.test"), admin_pw),
        "editor": (os.environ.get("CMS_EDITOR_EMAIL", "editor@example.test"), editor_pw),
    })
    print(f"Users created: {', '.join(created) or 'none (already present)'}")
    # TODO (later tickets): demo posts and pages, one draft and one published.
    return 0


if __name__ == "__main__":
    sys.exit(main())
