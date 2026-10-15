"""Pages: lasting club information. Like a Post, plus a navigation order; Admin-only."""
from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

from app import db
from app.posts import DRAFT, PUBLISHED, slugify

SEED_TITLES = ("Homepage", "About", "Leadership", "Analyst Program", "Join", "Recruiting")


@dataclass(frozen=True)
class Page:
    id: int
    title: str
    slug: str
    body: str
    status: str
    nav_order: int
    created_at: float
    updated_at: float


def _row(row: sqlite3.Row) -> Page:
    return Page(row["id"], row["title"], row["slug"], row["body"], row["status"],
                row["nav_order"], row["created_at"], row["updated_at"])


def _unique_slug(conn: sqlite3.Connection, title: str) -> str:
    base = slugify(title)
    slug, n = base, 1
    while conn.execute("SELECT 1 FROM pages WHERE slug = ?", (slug,)).fetchone():
        n += 1
        slug = f"{base}-{n}"
    return slug


def create_page(conn: sqlite3.Connection, title: str, body: str, nav_order: int,
                now: float) -> int:
    """New Pages are always Drafts."""
    with conn:
        cur = conn.execute(
            "INSERT INTO pages (title, slug, body, status, nav_order, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (title, _unique_slug(conn, title), body, DRAFT, nav_order, now, now))
    return cur.lastrowid


def get_page(conn: sqlite3.Connection, page_id: int) -> Page | None:
    row = conn.execute("SELECT * FROM pages WHERE id = ?", (page_id,)).fetchone()
    return _row(row) if row else None


def list_pages(conn: sqlite3.Connection, status: str | None = None) -> list[Page]:
    """Newest first, optionally one status."""
    where, args = ("", ()) if status is None else (" WHERE status = ?", (status,))
    rows = conn.execute("SELECT * FROM pages" + where + " ORDER BY created_at DESC, id DESC",
                        args).fetchall()
    return [_row(r) for r in rows]


def count_by_status(conn: sqlite3.Connection) -> dict[str, int]:
    found = {r["status"]: r["n"] for r in
             conn.execute("SELECT status, COUNT(*) AS n FROM pages GROUP BY status")}
    return {DRAFT: found.get(DRAFT, 0), PUBLISHED: found.get(PUBLISHED, 0)}


def update_page(conn: sqlite3.Connection, page_id: int, title: str, body: str,
                nav_order: int, now: float, slug: str | None = None) -> None:
    """The slug changes only when a normalised `slug` is passed."""
    with conn:
        conn.execute(
            "UPDATE pages SET title = ?, body = ?, nav_order = ?, updated_at = ?,"
            " slug = COALESCE(?, slug) WHERE id = ?",
            (title, body, nav_order, now, slug, page_id))


def set_status(conn: sqlite3.Connection, page_id: int, status: str, now: float) -> None:
    with conn:
        conn.execute("UPDATE pages SET status = ?, updated_at = ? WHERE id = ?",
                     (status, now, page_id))


def slug_taken(conn: sqlite3.Connection, slug: str, page_id: int) -> bool:
    return conn.execute("SELECT 1 FROM pages WHERE slug = ? AND id != ?",
                        (slug, page_id)).fetchone() is not None


def delete_page(conn: sqlite3.Connection, page_id: int) -> None:
    with conn:
        conn.execute("DELETE FROM pages WHERE id = ?", (page_id,))


def seed_pages(database: Path) -> list[str]:
    """Create the club's named Pages as Drafts; existing titles are left alone."""
    db.init_db(database)
    conn = db.connect(database)
    existing = {p.title for p in list_pages(conn)}
    created = []
    for order, title in enumerate(SEED_TITLES, start=1):
        if title not in existing:
            create_page(conn, title, "", order, time.time())
            created.append(title)
    conn.close()
    return created
