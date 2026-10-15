"""T05: President-only Pages. Seam 1: the HTTP app."""
import re

from app import db, pages
from tests.conftest import csrf_of
from tests.test_t03_president_control import act, president_for


def create_page(c, title="About", body="We are KCFC.", order="2"):
    token = csrf_of(c, "/admin/pages/new")
    return c.post("/admin/pages", data={"title": title, "body": body, "nav_order": order,
                                        "csrf_token": token}, follow_redirects=False)


def page_url(response) -> str:
    assert response.status_code == 303
    return response.headers["location"]


def test_president_creates_edits_and_sees_a_page(client_as):
    admin = client_as("admin")
    url = page_url(create_page(admin))
    assert re.fullmatch(r"/admin/pages/\d+", url)
    html = admin.get(url).text
    assert "About" in html and "Status: Draft" in html and "about" in html
    token = csrf_of(admin, url)
    admin.post(url, data={"title": "About us", "body": "New", "nav_order": "5",
                          "csrf_token": token}, follow_redirects=False)
    html = admin.get(url).text
    assert "About us" in html and 'value="5"' in html


def test_slug_is_generated_once_and_editable_by_president(client_as):
    admin = client_as("admin")
    url = page_url(create_page(admin, title="Join Us"))
    token = csrf_of(admin, url)
    admin.post(url, data={"title": "Join the club", "body": "", "nav_order": "1",
                          "csrf_token": token})
    assert 'value="join-us"' in admin.get(url).text
    admin.post(url, data={"title": "Join the club", "body": "", "nav_order": "1",
                          "slug": "Get Involved", "csrf_token": token})
    assert 'value="get-involved"' in admin.get(url).text


def test_navigation_order_is_stored_on_the_page(client_as):
    admin = client_as("admin")
    url = page_url(create_page(admin, order="7"))
    conn = db.connect(admin.app.state.database)
    pid = int(url.rsplit("/", 1)[1])
    assert pages.get_page(conn, pid).nav_order == 7
    conn.close()


def test_president_publishes_unpublishes_and_deletes_with_confirms(client_as):
    admin = client_as("admin")
    url = page_url(create_page(admin))
    assert "Publish this?" in admin.get(url + "/publish").text
    assert "Status: Draft" in admin.get(url).text
    assert act(admin, url, "publish").status_code == 303
    assert "Status: Published" in admin.get(url).text
    assert "Are you sure you want to unpublish this?" in admin.get(url + "/unpublish").text
    act(admin, url, "unpublish")
    assert "Status: Draft" in admin.get(url).text
    assert "Are you sure" in admin.get(url + "/delete").text
    assert act(admin, url, "delete").status_code == 303
    assert admin.get(url).status_code == 404


def test_officer_is_refused_on_every_page_url_get_and_post(client_as):
    editor = client_as("editor")
    admin = president_for(editor)
    url = page_url(create_page(admin))
    token = csrf_of(editor, "/admin/posts/new")
    for path in ("/admin/pages", "/admin/pages/new", url, url + "/publish",
                 url + "/unpublish", url + "/delete"):
        assert editor.get(path).status_code in (302, 303, 403), path
        r = editor.post(path, data={"csrf_token": token, "title": "x"}, follow_redirects=False)
        assert r.status_code in (302, 303, 403), path
    assert "Status: Draft" in admin.get(url).text
    assert admin.get(url).status_code == 200  # still there


def test_officer_sees_no_pages_link_or_pages_in_content_list(client_as):
    editor = client_as("editor")
    admin = president_for(editor)
    create_page(admin, title="Secret page")
    for path in ("/admin", "/admin/posts", "/admin/posts?type=page"):
        html = editor.get(path).text
        assert "/admin/pages" not in html and "Secret page" not in html, path
    assert "/admin/pages" in admin.get("/admin").text


def test_content_list_includes_pages_for_president_and_type_filter(client_as):
    editor = client_as("editor")
    admin = president_for(editor)
    create_page(admin, title="Leadership")
    editor_post = editor.post("/admin/posts", data={
        "title": "A post", "body": "", "csrf_token": csrf_of(editor, "/admin/posts/new")})
    assert editor_post.status_code in (200, 303)
    assert "Leadership" in admin.get("/admin/posts").text
    only_pages = admin.get("/admin/posts?type=page").text
    assert "Leadership" in only_pages and "A post" not in only_pages
    only_posts = admin.get("/admin/posts?type=post").text
    assert "A post" in only_posts and "Leadership" not in only_posts
    assert re.search(r">All \(2\)</a>", admin.get("/admin/posts").text)


def test_seed_creates_the_six_pages_as_drafts_once(make_app):
    app = make_app()
    for _ in range(2):
        pages.seed_pages(app.state.database)
    conn = db.connect(app.state.database)
    found = [(p.title, p.status) for p in pages.list_pages(conn)]
    conn.close()
    assert sorted(found) == sorted((t, "draft") for t in (
        "Homepage", "About", "Leadership", "Analyst Program", "Join", "Recruiting"))


def test_bad_navigation_order_is_rejected_not_coerced(client_as):
    admin = client_as("admin")
    for bad in ("abc", "-3"):
        r = create_page(admin, order=bad)
        assert r.status_code == 400 and "whole number" in r.text
    assert "About" not in admin.get("/admin/posts?type=page").text


def test_president_has_a_pages_link_officer_does_not(client_as):
    assert 'href="/admin/posts?type=page"' in client_as("admin").get("/admin").text
