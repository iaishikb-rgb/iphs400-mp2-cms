"""Posts: Markdown body, Draft/Published status, author, immutable slug."""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass

from app import taxonomy

DRAFT = "draft"
PUBLISHED = "published"


@dataclass(frozen=True)
class Post:
    id: int
    title: str
    slug: str
    body: str
    status: str
    author_id: int
    author_email: str
    author_name: str
    created_at: float
    updated_at: float
    category: str = ""
    tags: str = ""


_SELECT = """
SELECT p.*, u.email AS author_email, u.display_name AS author_name
FROM posts p JOIN users u ON u.id = p.author_id
"""


def _row_to_post(row: sqlite3.Row) -> Post:
    return Post(row["id"], row["title"], row["slug"], row["body"], row["status"],
                row["author_id"], row["author_email"], row["author_name"], row["created_at"], row["updated_at"],
                row["category"], row["tags"])


# "index" would collide with the generated index.html / posts/index.html.
RESERVED_SLUGS = {"index"}


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "post"
    return slug + "-1" if slug in RESERVED_SLUGS else slug


def _unique_slug(conn: sqlite3.Connection, title: str) -> str:
    base = slugify(title)
    slug, n = base, 1
    while conn.execute("SELECT 1 FROM posts WHERE slug = ?", (slug,)).fetchone():
        n += 1
        slug = f"{base}-{n}"
    return slug


def create_post(conn: sqlite3.Connection, title: str, body: str, author_id: int,
                now: float, category: str = "", tags: str = "") -> int:
    """New Posts are always Drafts."""
    with conn:
        cur = conn.execute(
            "INSERT INTO posts (title, slug, body, status, author_id, category, tags,"
            " created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (title, _unique_slug(conn, title), body, DRAFT, author_id,
             taxonomy.clean_category(category), taxonomy.clean_tags(tags), now, now),
        )
    return cur.lastrowid


def get_post(conn: sqlite3.Connection, post_id: int) -> Post | None:
    row = conn.execute(_SELECT + " WHERE p.id = ?", (post_id,)).fetchone()
    return _row_to_post(row) if row else None


def list_posts(conn: sqlite3.Connection, author_id: int | None = None,
               status: str | None = None, category: str | None = None) -> list[Post]:
    """Newest first. author_id limits the list to one User's Posts, status to one status,
    category (a category slug) to one category."""
    clauses, args = [], []
    if author_id is not None:
        clauses.append("p.author_id = ?")
        args.append(author_id)
    if status is not None:
        clauses.append("p.status = ?")
        args.append(status)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    rows = conn.execute(_SELECT + where + " ORDER BY p.created_at DESC, p.id DESC",
                        args).fetchall()
    found = [_row_to_post(r) for r in rows]
    if category is not None:
        found = [p for p in found if taxonomy.term_slug(p.category) == category]
    return found


def categories(conn: sqlite3.Connection, author_id: int | None = None) -> list[tuple[str, str]]:
    """(slug, name) of every category in use, A to Z; the newest Post's spelling names it."""
    named = {}
    for post in list_posts(conn, author_id):
        slug = taxonomy.term_slug(post.category)
        if slug:
            named.setdefault(slug, post.category)
    return sorted(named.items(), key=lambda item: item[1].lower())


def count_by_status(conn: sqlite3.Connection, author_id: int | None = None) -> dict[str, int]:
    """Posts per status (draft, published), optionally for one author."""
    sql, args = "SELECT status, COUNT(*) AS n FROM posts", ()
    if author_id is not None:
        sql, args = sql + " WHERE author_id = ?", (author_id,)
    found = {r["status"]: r["n"] for r in conn.execute(sql + " GROUP BY status", args)}
    return {DRAFT: found.get(DRAFT, 0), PUBLISHED: found.get(PUBLISHED, 0)}


def update_post(conn: sqlite3.Connection, post_id: int, title: str, body: str,
                now: float, status: str, slug: str | None = None,
                category: str = "", tags: str = "") -> None:
    """The slug changes only when a normalised `slug` is passed (Admin-only callers)."""
    with conn:
        conn.execute(
            "UPDATE posts SET title = ?, body = ?, status = ?, updated_at = ?,"
            " slug = COALESCE(?, slug), category = ?, tags = ? WHERE id = ?",
            (title, body, status, now, slug, taxonomy.clean_category(category),
             taxonomy.clean_tags(tags), post_id),
        )


def set_status(conn: sqlite3.Connection, post_id: int, status: str, now: float) -> None:
    with conn:
        conn.execute("UPDATE posts SET status = ?, updated_at = ? WHERE id = ?",
                     (status, now, post_id))


def slug_taken(conn: sqlite3.Connection, slug: str, post_id: int) -> bool:
    return conn.execute("SELECT 1 FROM posts WHERE slug = ? AND id != ?",
                        (slug, post_id)).fetchone() is not None


def delete_post(conn: sqlite3.Connection, post_id: int) -> None:
    with conn:
        conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
