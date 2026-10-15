"""T03: Presidents publish, unpublish and delete Posts. Seam 1: the HTTP app."""
from fastapi.testclient import TestClient

from tests.conftest import csrf_of, sign_in
from tests.test_t02_posts import create_post, post_url


def president_for(editor) -> TestClient:
    """A President on the same app and database as `editor`."""
    admin = TestClient(editor.app)
    sign_in(admin, "admin@example.test", "test-admin-pw")
    return admin


def act(c, url, action, **extra):
    token = csrf_of(c, url)
    return c.post(f"{url}/{action}", data={"csrf_token": token, **extra},
                  follow_redirects=False)


def published_post(editor, title="Pitch: NVDA"):
    url = post_url(create_post(editor, title=title))
    admin = president_for(editor)
    assert act(admin, url, "publish").status_code == 303
    assert "Published" in admin.get(url).text
    return url, admin


def test_president_publishes_a_draft_after_a_confirm(client_as):
    editor = client_as("editor")
    url = post_url(create_post(editor))
    admin = president_for(editor)
    confirm = admin.get(url + "/publish")
    assert confirm.status_code == 200
    assert "Publish this?" in confirm.text
    assert 'name="csrf_token"' in confirm.text
    assert "Status: Draft" in admin.get(url).text  # a GET publishes nothing
    assert act(admin, url, "publish").status_code == 303
    assert "Status: Published" in admin.get(url).text


def test_officer_cannot_publish_even_by_direct_post(client_as):
    editor = client_as("editor")
    url = post_url(create_post(editor))
    assert editor.get(url + "/publish").status_code == 403
    assert act(editor, url, "publish").status_code == 403
    assert "Status: Draft" in editor.get(url).text


def test_president_unpublishes_a_published_post(client_as):
    editor = client_as("editor")
    url, admin = published_post(editor)
    confirm = admin.get(url + "/unpublish")
    assert "Are you sure" in confirm.text
    assert act(admin, url, "unpublish").status_code == 303
    assert "Status: Draft" in admin.get(url).text


def test_officer_cannot_unpublish(client_as):
    editor = client_as("editor")
    url, admin = published_post(editor)
    assert act(editor, url, "unpublish").status_code == 403
    assert "Status: Published" in admin.get(url).text


def test_officers_edit_turns_a_published_post_back_to_draft(client_as):
    editor = client_as("editor")
    url, admin = published_post(editor)
    token = csrf_of(editor, url)
    edit = editor.post(url, data={"title": "Pitch: NVDA", "body": "changed",
                                  "csrf_token": token}, follow_redirects=False)
    assert edit.status_code == 303
    assert "Status: Draft" in admin.get(url).text


def test_presidents_edit_keeps_a_published_post_published(client_as):
    editor = client_as("editor")
    url, admin = published_post(editor)
    token = csrf_of(admin, url)
    admin.post(url, data={"title": "Pitch: NVDA", "body": "reviewed", "csrf_token": token})
    assert "Status: Published" in admin.get(url).text


def test_only_a_president_can_delete_a_published_post(client_as):
    editor = client_as("editor")
    url, admin = published_post(editor)
    assert editor.get(url + "/delete").status_code == 403
    assert act(editor, url, "delete").status_code == 403
    assert "Pitch: NVDA" in admin.get("/admin/posts").text
    assert "Are you sure" in admin.get(url + "/delete").text
    assert act(admin, url, "delete").status_code == 303
    assert "Pitch: NVDA" not in admin.get("/admin/posts").text
    assert admin.get(url).status_code == 404


def test_president_deletes_any_draft_after_a_confirm(client_as):
    editor = client_as("editor")
    url = post_url(create_post(editor, title="Their draft"))
    admin = president_for(editor)
    assert "Are you sure" in admin.get(url + "/delete").text
    assert act(admin, url, "delete").status_code == 303
    assert "Their draft" not in admin.get("/admin/posts").text


def test_only_a_president_can_edit_a_slug(client_as):
    editor = client_as("editor")
    url = post_url(create_post(editor, title="Alumni call"))
    admin = president_for(editor)
    page = admin.get(url).text
    assert 'name="slug"' in page
    token = csrf_of(admin, url)
    admin.post(url, data={"title": "Alumni call", "body": "x", "slug": "William Blair Recap",
                          "csrf_token": token})
    assert "william-blair-recap" in admin.get(url).text
    # An Officer's attempt is ignored.
    token = csrf_of(editor, url)
    editor.post(url, data={"title": "Alumni call", "body": "x", "slug": "hacked",
                           "csrf_token": token})
    page = editor.get(url).text
    assert "william-blair-recap" in page
    assert "hacked" not in page


def test_slug_cannot_collide_with_another_post(client_as):
    editor = client_as("editor")
    post_url(create_post(editor, title="Taken"))
    url = post_url(create_post(editor, title="Other"))
    admin = president_for(editor)
    token = csrf_of(admin, url)
    response = admin.post(url, data={"title": "Other", "body": "x", "slug": "taken",
                                     "csrf_token": token})
    assert response.status_code == 400
    assert "already used" in response.text
    assert 'value="other"' in admin.get(url).text


def test_confirm_posts_reject_missing_csrf(client_as):
    editor = client_as("editor")
    url, admin = published_post(editor)
    for action in ("unpublish", "delete", "publish"):
        assert admin.post(f"{url}/{action}", data={}).status_code == 403, action
    assert "Status: Published" in admin.get(url).text


def test_officer_slug_attempt_on_a_published_post_is_ignored(client_as):
    editor = client_as("editor")
    url, admin = published_post(editor)
    token = csrf_of(editor, url)
    editor.post(url, data={"title": "Pitch: NVDA", "body": "x", "slug": "hacked",
                           "csrf_token": token})
    assert "hacked" not in admin.get(url).text
    assert 'value="pitch-nvda"' in admin.get(url).text


def test_blank_slug_from_a_president_keeps_the_slug(client_as):
    editor = client_as("editor")
    url = post_url(create_post(editor, title="Keep me"))
    admin = president_for(editor)
    token = csrf_of(admin, url)
    admin.post(url, data={"title": "Keep me", "body": "x", "slug": "  ", "csrf_token": token})
    assert 'value="keep-me"' in admin.get(url).text
