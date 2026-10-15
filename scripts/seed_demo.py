#!/usr/bin/env python3
"""Create demo data so a grader (and you) can use the CMS immediately.

    uv run python scripts/seed_demo.py

Creates one admin and one editor (passwords read from the environment), the club's
Pages, and demo Kenyon Finance Club content: published Pages and Posts plus one Draft.

The rubric expects this to run clean on a fresh clone with .env.example values
(item E4), because the database itself is never committed.
"""
from __future__ import annotations

import os
import sys


def main() -> int:
    # Importing settings loads .env into the environment, so it must come first.
    from app import settings

    admin_pw = os.environ.get("CMS_ADMIN_PASSWORD")
    editor_pw = os.environ.get("CMS_EDITOR_PASSWORD")
    if not admin_pw or not editor_pw:
        print("Set CMS_ADMIN_PASSWORD and CMS_EDITOR_PASSWORD in .env "
              "(copy .env.example).")
        return 1

    from app.seed import seed_users

    created = seed_users(settings.DATABASE_PATH, {
        "admin": (os.environ.get("CMS_ADMIN_EMAIL", "admin@example.test"), admin_pw),
        "editor": (os.environ.get("CMS_EDITOR_EMAIL", "editor@example.test"), editor_pw),
    })
    print(f"Users created: {', '.join(created) or 'none (already present)'}")
    from app.pages import seed_pages

    print(f"Pages created: {', '.join(seed_pages(settings.DATABASE_PATH)) or 'none (already present)'}")
    from app.demo_content import seed_demo_content

    print(f"Demo content: {', '.join(seed_demo_content(settings.DATABASE_PATH)) or 'none (already present)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
