"""Demo seed: published club content, one Draft that never leaves the database."""
from app import db, pages, posts
from app.demo_content import NEXT_MEETING, seed_demo_content
from app.publish import render_site
from app.seed import seed_users

ACCOUNTS = {"admin": ("a@kenyon.edu", "pw-admin-123"), "editor": ("e@kenyon.edu", "pw-editor-123")}


def seeded(tmp_path):
    database = tmp_path / "demo.db"
    seed_users(database, ACCOUNTS)
    pages.seed_pages(database)
    seed_demo_content(database)
    return database


def test_seed_is_rerunnable_and_does_not_overwrite_edits(tmp_path):
    database = seeded(tmp_path)
    conn = db.connect(database)
    about = next(p for p in pages.list_pages(conn) if p.title == "About")
    pages.update_page(conn, about.id, "About", "Edited by a President", about.nav_order, 1.0)
    count = len(posts.list_posts(conn))
    conn.close()
    assert seed_demo_content(database) == []
    conn = db.connect(database)
    assert len(posts.list_posts(conn)) == count
    assert pages.get_page(conn, about.id).body == "Edited by a President"


def test_published_demo_content_reaches_site_and_the_draft_does_not(tmp_path):
    out = render_site(tmp_path / "site", seeded(tmp_path))
    home = (out / "index.html").read_text()
    assert NEXT_MEETING in home and "financeclub@kenyon.edu" in home
    for name in ("about", "leadership", "join"):
        assert (out / f"{name}.html").exists()
    assert not (out / "recruiting.html").exists()
    live = [f.name for f in (out / "posts").glob("*.html")]
    assert len(live) == 3  # index plus two Posts
    everything = "".join(f.read_text() for f in out.rglob("*.html"))
    assert "Lucas Flynn" in everything and "William Blair" in everything
    assert "sector team writeup" not in everything.lower()


def test_reseeding_resets_demo_display_names(tmp_path):
    database = seeded(tmp_path)
    conn = db.connect(database)
    conn.execute("UPDATE users SET display_name = 'Old Name'")
    conn.commit()
    conn.close()
    seed_users(database, ACCOUNTS)
    names = {r["role"]: r["display_name"] for r in
             db.connect(database).execute("SELECT role, display_name FROM users")}
    assert names == {"admin": "Aishik Biswas", "editor": "Club Officer"}
