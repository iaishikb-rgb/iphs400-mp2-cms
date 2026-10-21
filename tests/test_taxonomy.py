"""MP2plus F2 (issue #11): categories and tags. Seam 1 (HTTP app) and seam 2 (render_site).

Test names start test_stepN_ for the ticket's acceptance step N; the rest cover migration
and the Pending-changes and Editor rules the steps rely on.
"""
import re

from app.publish import has_pending_changes, publish, render_site
from tests.conftest import csrf_of
from tests.test_t02_posts import post_url
from tests.test_t03_president_control import act, president_for


def write_post(c, title="Pitch: NVDA", category="", tags="", body="Body text", url=None):
    """Create (or, with `url`, edit) a Post with a category and tags."""
    path = url or "/admin/posts/new"
    token = csrf_of(c, path)
    data = {"title": title, "body": body, "category": category, "tags": tags,
            "csrf_token": token}
    return c.post(url or "/admin/posts", data=data, follow_redirects=False)


def live(editor, admin, **fields):
    url = post_url(write_post(editor, **fields))
    assert act(admin, url, "publish").status_code == 303
    return url


def render(client, tmp_path):
    return render_site(tmp_path / "site", client.app.state.database)


# Step 1: one category and comma-separated tags persist after save.
def test_step1_category_and_tags_persist_after_save(client_as):
    c = client_as("editor")
    url = post_url(write_post(c, category="Pitches", tags="NVDA, tech ,spring"))
    page = c.get(url).text
    assert re.search(r'name="category"[^>]*value="Pitches"', page)
    assert re.search(r'name="tags"[^>]*value="NVDA, tech, spring"', page)


def test_step1_category_and_tags_can_be_edited_and_cleared(client_as):
    c = client_as("editor")
    url = post_url(write_post(c, category="Pitches", tags="a"))
    write_post(c, category="", tags="", url=url)
    page = c.get(url).text
    assert re.search(r'name="category"[^>]*value=""', page)
    assert re.search(r'name="tags"[^>]*value=""', page)


def test_step1_duplicate_blank_and_repeated_tags_are_tidied(client_as):
    c = client_as("editor")
    url = post_url(write_post(c, tags="NVDA, nvda,, ,tech,NVDA"))
    assert re.search(r'name="tags"[^>]*value="NVDA, tech"', c.get(url).text)


# Step 2: the admin content list filters by category.
def test_step2_content_list_filters_by_category(client_as):
    c = client_as("editor")
    write_post(c, title="Pitch One", category="Pitches")
    write_post(c, title="Recap One", category="Recaps")
    write_post(c, title="Uncategorised One")
    everything = c.get("/admin/posts").text
    assert "Pitch One" in everything and "Recap One" in everything
    filtered = c.get("/admin/posts?category=pitches").text
    assert "Pitch One" in filtered
    assert "Recap One" not in filtered and "Uncategorised One" not in filtered


def test_step2_category_filter_excludes_pages_for_a_president(client_as):
    editor = client_as("editor")
    admin = president_for(editor)
    write_post(editor, title="Pitch One", category="Pitches")
    from tests.test_t05_pages import create_page
    create_page(admin, "About Page", "x", "1")
    assert "About Page" in admin.get("/admin/posts").text
    filtered = admin.get("/admin/posts?category=pitches").text
    assert "Pitch One" in filtered and "About Page" not in filtered


def test_step2_editor_filter_still_shows_only_their_own_posts(client_as):
    editor = client_as("editor")
    admin = president_for(editor)
    write_post(admin, title="President Pitch", category="Pitches")
    write_post(editor, title="Officer Pitch", category="Pitches")
    listing = editor.get("/admin/posts?category=pitches").text
    assert "Officer Pitch" in listing and "President Pitch" not in listing


# Step 3: publish writes category/<slug>.html and tag/<slug>.html.
def test_step3_publish_writes_category_and_tag_pages(client_as, tmp_path):
    editor = client_as("editor")
    admin = president_for(editor)
    live(editor, admin, title="Pitch: NVDA", category="Pitches", tags="tech, NVDA")
    live(editor, admin, title="Pitch: XOM", category="Pitches", tags="energy")
    live(editor, admin, title="Recap: Alumni call", category="Recaps", tags="tech")
    out = render(editor, tmp_path)
    pitches = (out / "category" / "pitches.html").read_text()
    assert "Pitch: NVDA" in pitches and "Pitch: XOM" in pitches
    assert "Recap: Alumni call" not in pitches
    tech = (out / "tag" / "tech.html").read_text()
    assert "Pitch: NVDA" in tech and "Recap: Alumni call" in tech
    assert "Pitch: XOM" not in tech
    assert (out / "category" / "recaps.html").exists()
    assert (out / "tag" / "energy.html").exists() and (out / "tag" / "nvda.html").exists()


def test_step3_category_page_shows_the_name_title_and_date(client_as, tmp_path):
    editor = client_as("editor")
    admin = president_for(editor)
    live(editor, admin, title="Pitch: NVDA", category="Stock Pitches")
    html = (render(editor, tmp_path) / "category" / "stock-pitches.html").read_text()
    assert "<h1>Stock Pitches</h1>" in html
    assert re.search(r"\d{4}-\d{2}-\d{2}", html)


def test_step3_names_that_slugify_alike_share_one_page(client_as, tmp_path):
    editor = client_as("editor")
    admin = president_for(editor)
    live(editor, admin, title="One", category="Pitches")
    live(editor, admin, title="Two", category="pitches")
    out = render(editor, tmp_path)
    assert sorted(p.name for p in (out / "category").iterdir()) == ["pitches.html"]
    html = (out / "category" / "pitches.html").read_text()
    assert 'href="../posts/one.html">One</a>' in html
    assert 'href="../posts/two.html">Two</a>' in html


def test_step3_names_with_no_letters_or_digits_write_no_page(client_as, tmp_path):
    editor = client_as("editor")
    admin = president_for(editor)
    live(editor, admin, title="Odd", category="!!!", tags="???")
    out = render(editor, tmp_path)
    assert not (out / "category").exists() or not list((out / "category").iterdir())
    assert not (out / "tag").exists() or not list((out / "tag").iterdir())


def test_step3_markup_in_names_is_escaped(client_as, tmp_path):
    editor = client_as("editor")
    admin = president_for(editor)
    live(editor, admin, title="Sneaky", category="<script>alert(1)</script>",
         tags="<img src=x onerror=alert(1)>")
    out = render(editor, tmp_path)
    everything = "".join(p.read_text() for p in out.rglob("*.html"))
    assert "<script>" not in everything and "<img src=x" not in everything
    post = (out / "posts" / "sneaky.html").read_text()
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in post  # shown as text, not dropped
    assert "&lt;img src=x onerror=alert(1)&gt;" in post


# Step 4: each published post links to its category and tag pages, relatively.
def test_step4_post_links_to_its_category_and_tag_pages_relatively(client_as, tmp_path):
    editor = client_as("editor")
    admin = president_for(editor)
    live(editor, admin, title="Pitch: NVDA", category="Pitches", tags="tech, NVDA")
    out = render(editor, tmp_path)
    html = (out / "posts" / "pitch-nvda.html").read_text()
    for target in ("category/pitches.html", "tag/tech.html", "tag/nvda.html"):
        assert f'href="../{target}"' in html
        assert (out / "posts" / ".." / target).exists()


def test_step4_index_pages_link_back_with_relative_paths(client_as, tmp_path):
    editor = client_as("editor")
    admin = president_for(editor)
    live(editor, admin, title="Pitch: NVDA", category="Pitches", tags="tech")
    out = render(editor, tmp_path)
    for name in ("category/pitches.html", "tag/tech.html"):
        html = (out / name).read_text()
        assert 'href="../posts/pitch-nvda.html"' in html
        assert 'href="../style.css"' in html
        assert 'href="../index.html"' in html


def test_step4_no_root_absolute_paths_anywhere(client_as, tmp_path):
    editor = client_as("editor")
    admin = president_for(editor)
    live(editor, admin, title="Pitch: NVDA", category="Pitches", tags="tech")
    out = render(editor, tmp_path)
    for path in out.rglob("*.html"):
        assert not re.search(r'(?:href|src)="/', path.read_text()), path


def test_step4_post_without_category_or_tags_has_no_taxonomy_links(client_as, tmp_path):
    editor = client_as("editor")
    admin = president_for(editor)
    live(editor, admin, title="Plain")
    out = render(editor, tmp_path)
    assert "category/" not in (out / "posts" / "plain.html").read_text()
    assert not (out / "category").exists() or not list((out / "category").iterdir())


# Step 5: drafts never reach either index page.
def test_step5_draft_with_same_category_and_tag_is_absent(client_as, tmp_path):
    editor = client_as("editor")
    admin = president_for(editor)
    live(editor, admin, title="Live Pitch", category="Pitches", tags="tech")
    write_post(editor, title="Secret Draft", category="Pitches", tags="tech")
    out = render(editor, tmp_path)
    for name in ("category/pitches.html", "tag/tech.html"):
        html = (out / name).read_text()
        assert "Live Pitch" in html and "Secret Draft" not in html
    everything = "".join(p.read_text() for p in out.rglob("*.html"))
    assert "Secret Draft" not in everything


def test_step5_a_category_used_only_by_drafts_has_no_page(client_as, tmp_path):
    editor = client_as("editor")
    write_post(editor, title="Secret Draft", category="Hidden", tags="covert")
    out = render(editor, tmp_path)
    assert not (out / "category" / "hidden.html").exists()
    assert not (out / "tag" / "covert.html").exists()
    assert "Hidden" not in "".join(p.read_text() for p in out.rglob("*.html"))


def test_step5_unpublished_post_leaves_the_index_pages(client_as, tmp_path):
    editor = client_as("editor")
    admin = president_for(editor)
    url = live(editor, admin, title="Soon Gone", category="Pitches", tags="tech")
    out = render(editor, tmp_path)
    assert (out / "category" / "pitches.html").exists() and (out / "tag" / "tech.html").exists()
    act(admin, url, "unpublish")
    out = render(editor, tmp_path)
    assert not (out / "category" / "pitches.html").exists()
    assert not (out / "tag" / "tech.html").exists()


# Publish run bookkeeping: a taxonomy change is a pending change.
def test_changing_a_category_is_a_pending_change(client_as, tmp_path):
    editor = client_as("editor")
    admin = president_for(editor)
    url = live(editor, admin, title="Pitch: NVDA", category="Pitches")
    database = editor.app.state.database
    publish(tmp_path / "site", database)
    from app import db
    conn = db.connect(database)
    assert not has_pending_changes(conn)
    write_post(admin, title="Pitch: NVDA", category="Recaps", url=url)
    assert has_pending_changes(conn)
    conn.close()


def test_an_editors_edit_keeps_taxonomy_and_returns_post_to_draft(client_as):
    editor = client_as("editor")
    admin = president_for(editor)
    url = live(editor, admin, title="Pitch: NVDA", category="Pitches", tags="tech")
    write_post(editor, title="Pitch: NVDA", category="Pitches", tags="tech, new", url=url)
    page = editor.get(url).text
    assert "Draft" in page and 'value="tech, new"' in page


def test_an_older_database_without_the_columns_is_upgraded(tmp_path):
    import sqlite3
    from app import db
    path = tmp_path / "old.db"
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL, role TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1,
            display_name TEXT NOT NULL DEFAULT '');
        CREATE TABLE posts (id INTEGER PRIMARY KEY, title TEXT NOT NULL, slug TEXT NOT NULL UNIQUE,
            body TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'draft',
            author_id INTEGER NOT NULL, created_at REAL NOT NULL, updated_at REAL NOT NULL);
        INSERT INTO users (id, email, password_hash, role) VALUES (1, 'a@x.test', 'h', 'admin');
        INSERT INTO posts (title, slug, author_id, created_at, updated_at)
            VALUES ('Old', 'old', 1, 1, 1);
    """)
    conn.commit()
    conn.close()
    db.init_db(path)
    conn = db.connect(path)
    row = conn.execute("SELECT category, tags FROM posts").fetchone()
    assert (row["category"], row["tags"]) == ("", "")
    conn.close()


def test_step5_a_published_post_and_a_draft_share_a_term_and_only_the_published_one_is_listed(
        client_as, tmp_path):
    editor = client_as("editor")
    admin = president_for(editor)
    live(editor, admin, title="Live One", category="Pitches", tags="tech")
    write_post(editor, title="Draft Two", category="Pitches", tags="tech")
    out = render(editor, tmp_path)
    for name in ("category/pitches.html", "tag/tech.html"):
        html = (out / name).read_text()
        assert 'href="../posts/live-one.html">Live One</a>' in html
        assert "Draft Two" not in html and "draft-two" not in html


def test_step3_a_very_long_name_is_cut_so_publishing_still_works(client_as, tmp_path):
    editor = client_as("editor")
    admin = president_for(editor)
    live(editor, admin, title="Long", category="c" * 400, tags="t" * 400 + ", short")
    out = render(editor, tmp_path)  # must not raise OSError (file name too long)
    assert (out / "category" / ("c" * 60 + ".html")).exists()
    assert (out / "tag" / ("t" * 60 + ".html")).exists()
    assert (out / "tag" / "short.html").exists()


def test_step2_a_filter_with_no_letters_or_digits_matches_nothing(client_as):
    c = client_as("editor")
    write_post(c, title="Pitch One", category="Pitches")
    page = c.get("/admin/posts?category=%21%21%21").text
    assert "Pitch One" not in page
