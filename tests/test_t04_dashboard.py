"""T04: Dashboard counts and the filterable Content list. Seam 1: the HTTP app."""
import re

from app import db
from tests.test_t02_posts import create_post, post_url
from tests.test_t03_president_control import act, president_for


def count_of(html: str, label: str) -> int:
    """The number printed next to a label such as 'Drafts: 3'."""
    return int(re.search(rf"{label}:\s*(\d+)", html).group(1))


def titles_in_order(html: str, titles: list[str]) -> list[str]:
    return sorted((t for t in titles if t in html), key=html.index)


def test_dashboard_counts_follow_post_changes(client_as):
    editor = client_as("editor")
    admin = president_for(editor)
    assert count_of(admin.get("/admin").text, "Drafts") == 0
    url = post_url(create_post(editor, title="One"))
    create_post(editor, title="Two")
    page = admin.get("/admin").text
    assert (count_of(page, "Drafts"), count_of(page, "Published")) == (2, 0)
    act(admin, url, "publish")
    page = admin.get("/admin").text
    assert (count_of(page, "Drafts"), count_of(page, "Published")) == (1, 1)


def test_dashboard_has_a_new_post_button_that_opens_the_editor(client_as):
    c = client_as("editor")
    page = c.get("/admin").text
    assert 'href="/admin/posts/new"' in page
    assert c.get("/admin/posts/new").status_code == 200


def test_president_sees_user_counts_officer_does_not(client_as):
    editor = client_as("editor")
    admin = president_for(editor)
    page = admin.get("/admin").text
    assert (count_of(page, "Active Users"), count_of(page, "Deactivated Users")) == (2, 0)
    conn = db.connect(editor.app.state.database)
    with conn:
        conn.execute("UPDATE users SET active = 0 WHERE role = 'editor'")
    conn.close()
    page = admin.get("/admin").text
    assert (count_of(page, "Active Users"), count_of(page, "Deactivated Users")) == (1, 1)
    assert "Active Users" not in editor.get("/admin").text
    assert "Deactivated Users" not in editor.get("/admin").text


def test_content_list_is_newest_first_with_status_links_and_counts(client_as):
    editor = client_as("editor")
    admin = president_for(editor)
    old = post_url(create_post(editor, title="Older post"))
    create_post(editor, title="Newer post")
    act(admin, old, "publish")
    page = admin.get("/admin/posts").text
    assert titles_in_order(page, ["Older post", "Newer post"]) == ["Newer post", "Older post"]
    for label, n in (("All", 2), ("Published", 1), ("Draft", 1)):
        assert re.search(rf'<a href="[^"]*status=\w+[^"]*">{label} \({n}\)</a>', page), label


def test_status_filter_limits_the_list(client_as):
    editor = client_as("editor")
    admin = president_for(editor)
    live = post_url(create_post(editor, title="Live one"))
    create_post(editor, title="Draft one")
    act(admin, live, "publish")
    published = admin.get("/admin/posts?status=published").text
    assert "Live one" in published and "Draft one" not in published
    drafts = admin.get("/admin/posts?status=draft").text
    assert "Draft one" in drafts and "Live one" not in drafts
    both = admin.get("/admin/posts?status=all").text
    assert "Live one" in both and "Draft one" in both
    assert "Live one" in admin.get("/admin/posts?status=bogus").text  # unknown means All


def test_type_filter_limits_to_posts_or_pages_without_breaking(client_as):
    editor = client_as("editor")
    admin = president_for(editor)
    create_post(editor, title="A post")
    assert "A post" in admin.get("/admin/posts?type=post").text
    pages = admin.get("/admin/posts?type=page")
    assert pages.status_code == 200
    assert "A post" not in pages.text
    assert admin.get("/admin/posts?type=bogus").status_code == 200


def test_officer_list_and_counts_include_only_their_own_posts(client_as):
    editor = client_as("editor")
    admin = president_for(editor)
    create_post(editor, title="Mine")
    create_post(admin, title="President only")
    listing = editor.get("/admin/posts").text
    assert "Mine" in listing and "President only" not in listing
    assert count_of(editor.get("/admin").text, "Drafts") == 1
    assert count_of(admin.get("/admin").text, "Drafts") == 2
    assert re.search(r">All \(1\)</a>", listing)
    assert "President only" not in editor.get("/admin/posts?status=draft").text


def test_officer_published_count_and_filters_cover_only_their_posts(client_as):
    editor = client_as("editor")
    admin = president_for(editor)
    live = post_url(create_post(editor, title="Mine live"))
    create_post(editor, title="Mine draft")
    other = post_url(create_post(admin, title="Theirs live"))
    act(admin, live, "publish")
    act(admin, other, "publish")
    assert count_of(editor.get("/admin").text, "Published") == 1
    published = editor.get("/admin/posts?status=published").text
    assert "Mine live" in published and "Theirs live" not in published
    assert "Mine draft" not in published
    assert "Theirs live" not in editor.get("/admin/posts?type=post").text
    assert editor.get("/admin/posts?type=page").status_code == 200
    assert "type=page" not in editor.get("/admin/posts").text  # Editors see Posts only
