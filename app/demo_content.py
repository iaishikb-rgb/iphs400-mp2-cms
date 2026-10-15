"""Demo Kenyon Finance Club content for scripts/seed_demo.py. Safe to run repeatedly.

Pages are filled in only while their body is still empty, and Posts are matched by
title, so anything an Admin has since edited is left alone.
"""
from __future__ import annotations

import time
from pathlib import Path

from app import db, pages, posts, settings

NEXT_MEETING = "Next meeting: Wed Oct 28, 7 pm, Oden 110"
EMAIL = settings.CONTACT_EMAIL

PAGES = {  # title -> (body, publish?)
    "Homepage": (f"{NEXT_MEETING}\n\nWelcome to the Kenyon College Finance Club. "
                 "We meet every other week, and everyone is welcome.", True),
    "About": (
        "The Kenyon College Finance Club is a student organization, founded in 2019, that "
        "helps students explore finance and prepare for opportunities in the field.\n\n"
        "We run stock pitches, trading competitions, speaker events and resume workshops, "
        "and an Analyst Program for newer members. Our alumni network connects students "
        "with people at banks and investment firms, and has helped members find jobs.\n\n"
        "We meet every other week in Oden 110. The best way to reach us is "
        f"[{EMAIL}](mailto:{EMAIL}).", True),
    "Leadership": (
        "The club is run by three co-presidents:\n\n"
        "- Aishik Biswas\n- Lucas Flynn\n- Madeline Ha\n\n"
        "Each spring, each of us also leads one of the three sector teams in the stock "
        "pitch competition.", True),
    "Join": (
        "Come to any meeting: we meet every other week in Oden 110, and you do not need "
        "prior finance experience.\n\n"
        f"Questions, or want a resume review? Email us at [{EMAIL}](mailto:{EMAIL}) and we "
        "will send you the resume review form.", True),
}

POSTS = [  # (title, body, author role, publish?)
    ("Fall meeting: Wed Oct 28, Oden 110",
     "Our next meeting is **Wednesday, October 28 at 7 pm in Oden 110**. We meet every "
     f"other week, and new members are always welcome. Questions? Write to [{EMAIL}]"
     f"(mailto:{EMAIL}).", "admin", True),
    ("Recap: Spring 2026 stock pitch competition",
     "In the spring stock pitch competition, members worked in three sector teams, each "
     "led by one of the co-presidents. Each team presented its pitch to Kenyon alumni who "
     "work in equity research at William Blair, and got feedback from people in the "
     "industry.", "admin", True),
    ("Pitch: sector team writeup (draft)",
     "Draft. Team members and the full writeup go here once a President has reviewed it.",
     "editor", False),
]


def seed_demo_content(database: Path) -> list[str]:
    """Create the club's Pages and Posts; returns what this run created or filled in."""
    db.init_db(database)
    conn = db.connect(database)
    now = time.time()
    done = []
    try:
        for page in pages.list_pages(conn):
            body, live = PAGES.get(page.title, ("", False))
            if body and not page.body:
                pages.update_page(conn, page.id, page.title, body, page.nav_order, now)
                if live:
                    pages.set_status(conn, page.id, pages.PUBLISHED, now)
                done.append(f"page {page.title}")
        authors = {row["role"]: row["id"] for row in
                   conn.execute("SELECT id, role FROM users ORDER BY id DESC")}
        have = {p.title for p in posts.list_posts(conn)}
        for title, body, role, live in POSTS:
            if title not in have and role in authors:
                post_id = posts.create_post(conn, title, body, authors[role], now)
                if live:
                    posts.set_status(conn, post_id, posts.PUBLISHED, now)
                done.append(f"post {title}")
    finally:
        conn.close()
    return done
