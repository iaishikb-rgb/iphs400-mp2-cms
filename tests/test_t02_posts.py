"""T02: Officers write and edit their own Post drafts. Seam 1: the HTTP app."""
import re

from tests.conftest import csrf_of


def create_post(c, title="Meeting announcement", body="Come to **Oden 110**."):
    token = csrf_of(c, "/admin/posts/new")
    return c.post("/admin/posts", data={"title": title, "body": body, "csrf_token": token},
                  follow_redirects=False)


def post_url(response) -> str:
    assert response.status_code == 303
    return response.headers["location"]


def test_officer_creates_a_draft_they_own(client_as):
    c = client_as("editor")
    url = post_url(create_post(c))
    assert re.fullmatch(r"/admin/posts/\d+", url)
    page = c.get(url)
    assert page.status_code == 200
    assert "Meeting announcement" in page.text
    assert "Draft" in page.text
    listing = c.get("/admin/posts").text
    assert "Meeting announcement" in listing
    assert "editor@example.test" in listing


def test_slug_is_made_once_unique_and_survives_title_edits(client_as):
    c = client_as("editor")
    first = post_url(create_post(c, title="Spring Stock Pitch!"))
    second = post_url(create_post(c, title="Spring Stock Pitch!"))
    assert "spring-stock-pitch" in c.get(first).text
    assert "spring-stock-pitch-2" in c.get(second).text
    token = csrf_of(c, first)
    c.post(first, data={"title": "Totally different", "body": "x", "csrf_token": token})
    edited = c.get(first).text
    assert "Totally different" in edited
    assert "spring-stock-pitch" in edited
    assert "totally-different" not in edited


def test_editor_cannot_set_the_slug(client_as):
    c = client_as("editor")
    url = post_url(create_post(c, title="Alumni call"))
    token = csrf_of(c, url)
    c.post(url, data={"title": "Alumni call", "body": "x", "slug": "hacked",
                      "csrf_token": token})
    page = c.get(url).text
    assert "alumni-call" in page
    assert "hacked" not in page
    assert 'name="slug"' not in page


def test_officer_sees_and_opens_only_their_own_posts(client_as, make_app):
    from fastapi.testclient import TestClient
    from app.seed import seed_users
    from tests.conftest import sign_in

    app = make_app()
    seed_users(app.state.database, {"editor": ("other@example.test", "other-pw")})
    mine = TestClient(app)
    sign_in(mine, "editor@example.test", "test-editor-pw")
    theirs = TestClient(app)
    sign_in(theirs, "other@example.test", "other-pw")

    their_url = post_url(create_post(theirs, title="Their secret pitch"))
    create_post(mine, title="My announcement")

    listing = mine.get("/admin/posts").text
    assert "My announcement" in listing
    assert "Their secret pitch" not in listing
    for path in (their_url, their_url + "/delete"):
        assert mine.get(path, follow_redirects=False).status_code == 403
    token = csrf_of(mine, "/admin/posts/new")
    edit = mine.post(their_url, data={"title": "pwned", "body": "", "csrf_token": token})
    assert edit.status_code == 403
    assert "pwned" not in theirs.get(their_url).text


def test_president_opens_and_edits_any_post(client_as, make_app):
    editor = client_as("editor")
    url = post_url(create_post(editor, title="Pitch: NVDA"))
    # Same app and database, signed in as the President.
    from fastapi.testclient import TestClient
    from tests.conftest import sign_in
    admin = TestClient(editor.app)
    sign_in(admin, "admin@example.test", "test-admin-pw")
    assert "Pitch: NVDA" in admin.get("/admin/posts").text
    token = csrf_of(admin, url)
    admin.post(url, data={"title": "Pitch: NVDA (reviewed)", "body": "ok", "csrf_token": token})
    assert "Pitch: NVDA (reviewed)" in admin.get(url).text


def test_missing_title_is_refused_with_a_message(client_as):
    c = client_as("editor")
    response = create_post(c, title="   ")
    assert response.status_code == 400
    assert "needs a title" in response.text


HOSTILE = """# Heading

- one
- two

[safe](https://example.com) and [bad](javascript:alert(1))

<script>alert(1)</script>
<img src=x onerror=alert(1)>
<iframe src="https://evil.example"></iframe>
"""


def preview(c, body):
    token = csrf_of(c, "/admin/posts/new")
    return c.post("/admin/posts/preview",
                  data={"title": "T", "body": body, "csrf_token": token})


def test_preview_is_sanitized_and_labelled_draft_not_live(client_as):
    page = preview(client_as("editor"), HOSTILE)
    assert page.status_code == 200
    assert "Draft, not Live" in page.text
    html = page.text
    assert "<h1>Heading</h1>" in html
    assert "<li>one</li>" in html
    assert 'href="https://example.com"' in html
    # Hostile words may survive as inert escaped text, never as live markup.
    preview_pane = html.split('aria-label="Preview"')[1]
    for dangerous in ("<script", "<img", "<iframe", 'href="javascript'):
        assert dangerous not in preview_pane


def test_saved_post_page_shows_the_sanitized_preview(client_as):
    c = client_as("editor")
    url = post_url(create_post(c, body=HOSTILE))
    pane = c.get(url).text.split('aria-label="Preview"')[1]
    assert "<h1>Heading</h1>" in pane
    assert "<script" not in pane and 'href="javascript' not in pane


def test_officer_deletes_own_draft_after_an_are_you_sure_step(client_as):
    c = client_as("editor")
    url = post_url(create_post(c, title="Abandoned idea"))
    confirm = c.get(url + "/delete")
    assert confirm.status_code == 200
    assert "Are you sure" in confirm.text
    assert "Abandoned idea" in c.get("/admin/posts").text  # a GET deletes nothing
    token = csrf_of(c, url + "/delete")
    done = c.post(url + "/delete", data={"csrf_token": token}, follow_redirects=False)
    assert done.status_code == 303
    assert "Abandoned idea" not in c.get("/admin/posts").text
    assert c.get(url).status_code == 403  # gone, and an Officer cannot tell gone from not theirs


def test_every_post_form_carries_a_csrf_token_and_rejects_without_it(client_as):
    c = client_as("editor")
    url = post_url(create_post(c))
    for path in ("/admin/posts/new", url, url + "/delete"):
        assert 'name="csrf_token"' in c.get(path).text, path
    for path in ("/admin/posts", url, url + "/delete", "/admin/posts/preview"):
        response = c.post(path, data={"title": "x", "body": "y"})
        assert response.status_code == 403, path
    assert c.get(url).status_code == 200


def test_posts_are_reachable_from_the_console_home(client_as):
    assert "/admin/posts" in client_as("editor").get("/admin").text
