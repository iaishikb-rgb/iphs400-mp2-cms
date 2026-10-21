"""Render the public site into site/ as plain HTML.

Rules the rubric checks:

  1. Only PUBLISHED content is written here. A draft that reaches site/ is a bug.
  2. Every href and src is RELATIVE ("style.css", "../style.css"), never
     root-absolute ("/style.css"), because Pages serves this from a subfolder.

Layout: Pages are <slug>.html at the top, Posts are posts/<slug>.html, so a Post
slug can never collide with a Page slug. "index" is a reserved slug. Each category
and tag in use by a Published Post also gets category/<slug>.html or tag/<slug>.html.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app import db, pages, posts, settings, taxonomy
from app.markdown import render_markdown

HOMEPAGE_SLUG = "homepage"  # the seeded Homepage; its slug is made once and survives renames
LATEST_POSTS = 5
ANONYMOUS_BYLINE = "Kenyon Finance Club"  # a User with no display name; never an email

CSS = """/* Minimal starter styles — make them yours. */
:root { color-scheme: light dark; }
body { font: 16px/1.6 system-ui, sans-serif; margin: 0 auto; max-width: 42rem; padding: 1rem; }
header a { font-weight: 700; text-decoration: none; margin-right: .75rem; }
header nav { display: inline; }
main { margin-block: 2rem; }
"""


def environment() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(settings.TEMPLATES)),
        autoescape=select_autoescape(["html"]),
    )


def _date(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")


def _byline_name(post: posts.Post) -> str:
    return post.author_name or ANONYMOUS_BYLINE


def _published(conn: sqlite3.Connection) -> tuple[list[pages.Page], list[posts.Post]]:
    live_pages = sorted(pages.list_pages(conn, posts.PUBLISHED),
                        key=lambda p: (p.nav_order, p.id))
    return live_pages, posts.list_posts(conn, status=posts.PUBLISHED)


def _fingerprint(conn: sqlite3.Connection) -> str:
    """A hash of everything a Publish run would write, to tell what changed since."""
    live_pages, live_posts = _published(conn)
    content = {
        "pages": [[p.slug, p.title, p.body, p.nav_order] for p in live_pages],
        "posts": [[p.slug, p.title, p.body, _byline_name(p), _date(p.created_at),
                   p.category, p.tags] for p in live_posts],
    }
    return hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()


def _categories_of(post: posts.Post) -> list[tuple[str, str]]:
    """[(slug, name)] of the Post's category; empty when it has none worth a page."""
    slug = taxonomy.term_slug(post.category)
    return [(slug, post.category)] if slug else []


def _tags_of(post: posts.Post) -> list[tuple[str, str]]:
    tags = ((taxonomy.term_slug(name), name) for name in taxonomy.parse_tags(post.tags))
    return [(slug, name) for slug, name in tags if slug]


def _group(live_posts: list[posts.Post], terms_of) -> dict[str, dict]:
    """slug -> {"name", "posts"} over the Published Posts, newest first, first spelling wins."""
    groups: dict[str, dict] = {}
    for post in live_posts:
        for slug, name in terms_of(post):
            groups.setdefault(slug, {"name": name, "posts": []})["posts"].append(post)
    return groups


def has_pending_changes(conn: sqlite3.Connection) -> bool:
    """True when Published content differs from what the last Publish run wrote."""
    row = conn.execute("SELECT value FROM meta WHERE key = 'last_publish'").fetchone()
    if row is None:  # never published: pending only if there is something to publish
        live_pages, live_posts = _published(conn)
        return bool(live_pages or live_posts)
    return row["value"] != _fingerprint(conn)


def render_site(out: Path | None = None, database: Path | None = None) -> Path:
    out = Path(out or settings.SITE)
    database = Path(database or settings.DATABASE_PATH)
    live_pages, live_posts = [], []
    if database.exists():  # no database yet means nothing is Published
        db.init_db(database)  # brings an older database up to the current schema
        conn = db.connect(database)
        try:
            live_pages, live_posts = _published(conn)
        finally:
            conn.close()
    if out.exists():
        shutil.rmtree(out)
    (out / "posts").mkdir(parents=True)
    env = environment()
    category_groups = _group(live_posts, _categories_of)
    tag_groups = _group(live_posts, _tags_of)
    (out / "style.css").write_text(CSS)

    def render(template: str, root: str, **context) -> str:
        nav = [{"title": p.title, "href": f"{p.slug}.html"} for p in live_pages
               if p.slug != HOMEPAGE_SLUG]
        nav.append({"title": "Posts", "href": "posts/index.html"})
        return env.get_template(template).render(
            root=root, nav=nav, site_title=settings.SITE_TITLE,
            contact_email=settings.CONTACT_EMAIL, **context)

    homepage = next((p for p in live_pages if p.slug == HOMEPAGE_SLUG), None)
    (out / "index.html").write_text(render(
        "public/home.html", "", title=settings.SITE_TITLE,
        next_meeting_html=render_markdown(homepage.body) if homepage else "",
        latest=[{"title": p.title, "href": f"posts/{p.slug}.html", "date": _date(p.created_at)}
                for p in live_posts[:LATEST_POSTS]]))
    for page in live_pages:
        if page.slug == HOMEPAGE_SLUG:
            continue
        (out / f"{page.slug}.html").write_text(render(
            "public/page.html", "", title=page.title, body_html=render_markdown(page.body)))
    (out / "posts" / "index.html").write_text(render(
        "public/posts.html", "../", title="Posts",
        posts=[{"title": p.title, "href": f"{p.slug}.html", "date": _date(p.created_at)}
               for p in live_posts]))
    for post in live_posts:
        (out / "posts" / f"{post.slug}.html").write_text(render(
            "public/post.html", "../", title=post.title, body_html=render_markdown(post.body),
            byline_name=_byline_name(post), date=_date(post.created_at),
            category=next(({"name": name, "href": f"../category/{slug}.html"}
                           for slug, name in _categories_of(post)), None),
            tags=[{"name": name, "href": f"../tag/{slug}.html"} for slug, name in _tags_of(post)]))
    for folder, label, groups in (("category", "Category", category_groups),
                                  ("tag", "Tag", tag_groups)):
        if groups:
            (out / folder).mkdir()
        for slug, group in groups.items():
            (out / folder / f"{slug}.html").write_text(render(
                "public/term.html", "../", title=group["name"], label=label,
                posts=[{"title": p.title, "href": f"../posts/{p.slug}.html",
                        "date": _date(p.created_at)} for p in group["posts"]]))
    return out


def publish(out: Path | None = None, database: Path | None = None) -> Path:
    """A Publish run: render site/ and record what was written, clearing Pending changes."""
    database = Path(database or settings.DATABASE_PATH)
    # Fingerprint first: an edit made while rendering then shows up as Pending, never lost.
    db.init_db(database)
    conn = db.connect(database)
    try:
        fingerprint = _fingerprint(conn)
        written = render_site(out, database)
        with conn:
            conn.execute("INSERT INTO meta (key, value) VALUES ('last_publish', ?)"
                         " ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                         (fingerprint,))
    finally:
        conn.close()
    return written
