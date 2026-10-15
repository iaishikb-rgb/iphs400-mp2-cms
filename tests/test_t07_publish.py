"""T07: Publish run and the public site. Seam 2: render_site / publish; seam 1 for the banner."""
import re
from pathlib import Path

from fastapi.testclient import TestClient

from app import db, users
from app.publish import publish, render_site
from tests.conftest import csrf_of, sign_in
from tests.test_t02_posts import create_post, post_url
from tests.test_t03_president_control import act, president_for
from tests.test_t05_pages import create_page, page_url
from tests.test_t06_users import act as user_act, make_user


def live_post(editor, admin, title="Pitch: NVDA", body="Body text"):
    url = post_url(create_post(editor, title=title, body=body))
    act(admin, url, "publish")
    return url


def live_page(admin, title="About", body="We are KCFC.", order="2"):
    url = page_url(create_page(admin, title, body, order))
    act(admin, url, "publish")
    return url


def render(client, tmp_path) -> Path:
    return render_site(tmp_path / "site", client.app.state.database)


def test_only_published_items_are_written_under_their_own_paths(client_as, tmp_path):
    editor = client_as("editor")
    admin = president_for(editor)
    live_post(editor, admin, "Live Post")
    create_post(editor, title="Secret Draft")
    live_page(admin, "About")
    create_page(admin, "Hidden Page")
    out = render(editor, tmp_path)
    assert (out / "posts" / "live-post.html").exists()
    assert (out / "about.html").exists()
    assert not (out / "posts" / "secret-draft.html").exists()
    assert not (out / "hidden-page.html").exists()
    everything = "".join(p.read_text() for p in out.rglob("*.html"))
    assert "Secret Draft" not in everything and "Hidden Page" not in everything


def test_post_and_page_with_the_same_title_do_not_collide(client_as, tmp_path):
    editor = client_as("editor")
    admin = president_for(editor)
    live_post(editor, admin, "Join", "post body")
    live_page(admin, "Join", "page body")
    out = render(editor, tmp_path)
    assert "post body" in (out / "posts" / "join.html").read_text()
    assert "page body" in (out / "join.html").read_text()


def test_homepage_order_and_latest_posts(client_as, tmp_path):
    editor = client_as("editor")
    admin = president_for(editor)
    live_page(admin, "Homepage", "Next meeting: Wed Oct 28, 7 pm, Oden 110", "1")
    live_post(editor, admin, "Older Post")
    live_post(editor, admin, "Newer Post")
    html = (render(editor, tmp_path) / "index.html").read_text()
    order = [html.index(s) for s in ("Next meeting: Wed Oct 28", "financeclub@kenyon.edu",
                                      "Newer Post", "Older Post")]
    assert order == sorted(order)


def test_navigation_lists_published_pages_in_order_plus_posts_listing(client_as, tmp_path):
    editor = client_as("editor")
    admin = president_for(editor)
    live_page(admin, "Zeta", order="1")
    live_page(admin, "Alpha", order="2")
    create_page(admin, "Draftpage", order="0")
    html = (render(editor, tmp_path) / "index.html").read_text()
    assert html.index("Zeta") < html.index("Alpha") < html.index("Posts")
    assert "Draftpage" not in html
    assert 'href="zeta.html"' in html and 'href="posts/index.html"' in html


def test_posts_listing_is_newest_first_with_title_and_date(client_as, tmp_path):
    editor = client_as("editor")
    admin = president_for(editor)
    live_post(editor, admin, "First Post")
    live_post(editor, admin, "Second Post")
    html = (render(editor, tmp_path) / "posts" / "index.html").read_text()
    assert html.index("Second Post") < html.index("First Post")
    assert re.search(r"\d{4}-\d{2}-\d{2}", html)
    assert 'href="first-post.html"' in html  # relative to posts/


def test_byline_uses_display_name_never_email_and_pages_have_none(client_as, tmp_path):
    editor = client_as("editor")
    admin = president_for(editor)
    live_post(editor, admin, "Bylined")
    live_page(admin, "About")
    out = render(editor, tmp_path)
    post = (out / "posts" / "bylined.html").read_text()
    assert re.search(r"By Club Officer, \d{4}-\d{2}-\d{2}", post)
    assert "@" not in "".join(p.read_text() for p in out.rglob("*.html")).replace(
        "financeclub@kenyon.edu", "")
    assert "By " not in (out / "about.html").read_text()


def test_deactivated_author_name_still_shows(client_as, tmp_path):
    editor = client_as("editor")
    admin = president_for(editor)
    live_post(editor, admin, "Old Post")
    user_act(admin, "editor@example.test", "deactivate")
    assert "By Club Officer" in (render(editor, tmp_path) / "posts" / "old-post.html").read_text()


def test_president_creates_and_renames_display_name(client_as, tmp_path):
    admin = client_as("admin")
    token = csrf_of(admin, "/admin/users")
    r = admin.post("/admin/users", data={"email": "kim@kenyon.edu", "role": "editor",
                   "password": "first-pw-123", "display_name": "Kim Lee",
                   "csrf_token": token}, follow_redirects=False)
    assert r.status_code == 303 and "Kim Lee" in admin.get("/admin/users").text
    # a name is required
    assert make_user(admin, email="noname@kenyon.edu", display_name=" ").status_code == 400
    user_act(admin, "kim@kenyon.edu", "name", display_name="Kimberly Lee")
    page = admin.get("/admin/users").text
    assert "Kimberly Lee" in page and "Kim Lee<" not in page


def test_editor_cannot_rename_users(client_as):
    editor = client_as("editor")
    token = csrf_of(editor, "/admin/posts/new")
    r = editor.post("/admin/users/1/name", data={"display_name": "X", "csrf_token": token},
                    follow_redirects=False)
    assert r.status_code == 403


def test_sanitizer_in_published_output(client_as, tmp_path):
    editor = client_as("editor")
    admin = president_for(editor)
    body = ("# Heading\n\n- item\n\n[ok](https://example.com) [bad](javascript:alert(1))\n\n"
            "<script>alert(1)</script><img src=x onerror=alert(1)><iframe src=x></iframe>")
    live_post(editor, admin, "Dirty", body)
    html = (render(editor, tmp_path) / "posts" / "dirty.html").read_text()
    # raw HTML is shown as inert escaped text, so only live tags and links matter
    for bad in ("<script", "<iframe", "<img", "<a href=\"javascript", "href=\"javascript"):
        assert bad not in html
    assert "<h1>Heading</h1>" in html and "<li>item</li>" in html
    assert 'href="https://example.com"' in html


def test_script_and_onerror_payloads_in_title_and_body_are_inert(client_as, tmp_path):
    editor = client_as("editor")
    admin = president_for(editor)
    title = "Probe <script>window.__xss=1</script>"
    body = '<script>window.__xss=1</script>\n\n<img src=x onerror="window.__xss=2">'
    live_post(editor, admin, title, body)
    published = (render(editor, tmp_path) / "posts").rglob("*.html")
    pane = editor.post("/admin/posts/preview", data={
        "title": title, "body": body, "csrf_token": csrf_of(editor, "/admin/posts/new")}).text
    for html in [pane, *(f.read_text() for f in published)]:
        assert "<script" not in html and "<img" not in html  # shown as escaped text instead


def test_no_root_absolute_paths_anywhere(client_as, tmp_path):
    editor = client_as("editor")
    admin = president_for(editor)
    live_post(editor, admin, "P1")
    live_page(admin, "Homepage")
    for f in render(editor, tmp_path).rglob("*.html"):
        text = f.read_text()
        assert 'href="/' not in text and 'src="/' not in text, f
    assert 'href="../style.css"' in (tmp_path / "site/posts/p1.html").read_text()


def test_unpublish_and_rerun_removes_the_item(client_as, tmp_path):
    editor = client_as("editor")
    admin = president_for(editor)
    url = live_post(editor, admin, "Gone Soon")
    assert (render(editor, tmp_path) / "posts" / "gone-soon.html").exists()
    act(admin, url, "unpublish")
    out = render(editor, tmp_path)
    assert not (out / "posts" / "gone-soon.html").exists()
    assert "Gone Soon" not in (out / "posts" / "index.html").read_text()


def test_pending_changes_banner_appears_and_clears_after_publish_run(client_as, tmp_path):
    editor = client_as("editor")
    admin = president_for(editor)
    assert "Pending changes" not in admin.get("/admin").text
    url = live_post(editor, admin, "Banner Post")
    assert "Pending changes" in admin.get("/admin").text
    publish(tmp_path / "site", editor.app.state.database)
    assert "Pending changes" not in admin.get("/admin").text
    act(admin, url, "unpublish")  # taking something down is a change too
    assert "Pending changes" in admin.get("/admin").text


def test_root_absolute_links_in_markdown_are_dropped(client_as, tmp_path):
    editor = client_as("editor")
    admin = president_for(editor)
    live_post(editor, admin, "Links", "[a](/about.html) [b](//evil.test/x) [c](page.html)")
    html = (render(editor, tmp_path) / "posts" / "links.html").read_text()
    assert 'href="/' not in html and 'href="//' not in html
    assert 'href="page.html"' in html


def test_admin_cannot_claim_the_reserved_index_slug(client_as, tmp_path):
    editor = client_as("editor")
    admin = president_for(editor)
    url = live_post(editor, admin, "Clash")
    token = csrf_of(admin, url)
    admin.post(url, data={"title": "Clash", "body": "x", "slug": "index", "csrf_token": token})
    out = render(editor, tmp_path)
    assert "Clash" in (out / "posts" / "index-1.html").read_text()
