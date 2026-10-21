"""Console routes for Posts: list, create, edit, preview, delete."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse

from app import auth, db, pages, posts, taxonomy
from app.markdown import render_markdown
from app.templating import flash, templates

router = APIRouter(prefix="/admin/posts")

NOT_YOURS = "You can only open your own Posts"


def _own_post(conn, post_id: int, user) -> posts.Post:
    """The Post, or a refusal. Editors reach only their own; Admins reach all."""
    post = posts.get_post(conn, post_id)
    if post is None:
        # An Editor gets the same refusal as for someone else's Post, so ids do not leak.
        if user.role != "admin":
            raise HTTPException(status_code=403, detail=NOT_YOURS)
        raise HTTPException(status_code=404, detail="No such Post")
    if user.role != "admin" and post.author_id != user.id:
        raise HTTPException(status_code=403, detail=NOT_YOURS)
    return post


def _editor_page(request, user, post, title, body, error=None, status_code=200,
                 category=None, tags=None):
    return templates.TemplateResponse(
        request, "admin/post_edit.html",
        {"title": "Edit Post" if post else "New Post", "user": user, "post": post,
         "form_title": title, "form_body": body, "preview_html": render_markdown(body),
         "form_category": category if category is not None else (post.category if post else ""),
         "form_tags": tags if tags is not None else (post.tags if post else ""),
         "error": error},
        status_code=status_code,
    )


STATUS_FILTERS = {"all": None, "published": posts.PUBLISHED, "draft": posts.DRAFT}
TYPE_FILTERS = ("all", "post", "page")


@router.get("")
def post_list(request: Request, status: str = "all", kind: str = Query("all", alias="type"),
              category: str = "", user=Depends(auth.require_user), conn=Depends(db.get_db)):
    """Content list. Unknown filter values fall back to All; a category (by slug) that
    matches nothing shows nothing."""
    status = status if status in STATUS_FILTERS else "all"
    kind = kind if kind in TYPE_FILTERS else "all"
    # A filter with no letters or digits matches nothing ("-" is never a slug), not everything.
    category = taxonomy.term_slug(category) or ("-" if category.strip() else "")
    is_admin = user.role == "admin"
    own_only = None if is_admin else user.id
    # Pages are President-only: Officers get Posts regardless of the type filter.
    shows_posts = kind != "page" or not is_admin
    # Pages have no category, so a category filter leaves them out.
    shows_pages = is_admin and kind != "post" and not category
    counts = {posts.DRAFT: 0, posts.PUBLISHED: 0}
    items = []
    if shows_posts:
        in_category = posts.list_posts(conn, own_only, category=category or None)
        for p in in_category:
            counts[p.status] += 1  # counts follow the category filter, like the list
        items += [{"kind": "Post", "title": p.title, "status": p.status, "by": p.author_email,
                   "category": p.category, "url": f"/admin/posts/{p.id}",
                   "sort": (p.created_at, p.id)}
                  for p in in_category if STATUS_FILTERS[status] in (None, p.status)]
    if shows_pages:
        for k, n in pages.count_by_status(conn).items():
            counts[k] += n
        items += [{"kind": "Page", "title": p.title, "status": p.status, "by": None,
                   "url": f"/admin/pages/{p.id}", "sort": (p.created_at, p.id)}
                  for p in pages.list_pages(conn, STATUS_FILTERS[status])]
    items.sort(key=lambda i: i["sort"], reverse=True)
    published, drafts = counts[posts.PUBLISHED], counts[posts.DRAFT]
    status_links = [("all", "All", published + drafts), ("published", "Published", published),
                    ("draft", "Draft", drafts)]
    return templates.TemplateResponse(
        request, "admin/post_list.html",
        {"title": "Content list", "user": user, "items": items, "status": status, "type": kind,
         "category": category, "category_links": posts.categories(conn, own_only),
         "status_links": status_links, "type_links": TYPE_FILTERS if is_admin else ()},
    )


@router.get("/new")
def post_new(request: Request, user=Depends(auth.require_user)):
    return _editor_page(request, user, None, "", "")


@router.post("")
def post_create(request: Request, title: str = Form(""), body: str = Form(""),
                category: str = Form(""), tags: str = Form(""),
                user=Depends(auth.require_user), conn=Depends(db.get_db)):
    title = title.strip()
    if not title:
        return _editor_page(request, user, None, title, body, "A Post needs a title", 400,
                            category, tags)
    post_id = posts.create_post(conn, title, body, user.id, auth.now(request), category, tags)
    flash(request, "Saved.")
    return RedirectResponse(f"/admin/posts/{post_id}", status_code=303)


@router.post("/preview")
def post_preview(request: Request, title: str = Form(""), body: str = Form(""),
                 category: str = Form(""), tags: str = Form(""),
                 post_id: int | None = Form(None),
                 user=Depends(auth.require_user), conn=Depends(db.get_db)):
    post = _own_post(conn, post_id, user) if post_id else None
    return _editor_page(request, user, post, title, body, category=category, tags=tags)


@router.get("/{post_id}")
def post_edit(post_id: int, request: Request, user=Depends(auth.require_user),
              conn=Depends(db.get_db)):
    post = _own_post(conn, post_id, user)
    return _editor_page(request, user, post, post.title, post.body)


@router.post("/{post_id}")
def post_update(post_id: int, request: Request, title: str = Form(""), body: str = Form(""),
                category: str = Form(""), tags: str = Form(""),
                slug: str | None = Form(None), user=Depends(auth.require_user), conn=Depends(db.get_db)):
    post = _own_post(conn, post_id, user)
    title = title.strip()
    if not title:
        return _editor_page(request, user, post, title, body, "A Post needs a title", 400,
                            category=category, tags=tags)
    new_slug = None
    if user.role == "admin" and slug is not None and slug.strip():
        new_slug = posts.slugify(slug)
        if posts.slug_taken(conn, new_slug, post_id):
            return _editor_page(request, user, post, title, body,
                                f"The slug “{new_slug}” is already used by another Post", 400,
                                category, tags)
    # An Editor's edit sends a Published Post back to Draft; an Admin's leaves it alone.
    status = post.status if user.role == "admin" else posts.DRAFT
    posts.update_post(conn, post_id, title, body, auth.now(request), status, new_slug,
                      category, tags)
    flash(request, "Saved.")
    return RedirectResponse(f"/admin/posts/{post_id}", status_code=303)


def _deletable(post: posts.Post, user) -> posts.Post:
    if user.role != "admin" and post.status != posts.DRAFT:
        raise HTTPException(status_code=403, detail="Only a President can delete a Published Post")
    return post


@router.get("/{post_id}/delete")
def post_delete_confirm(post_id: int, request: Request, user=Depends(auth.require_user),
                        conn=Depends(db.get_db)):
    post = _deletable(_own_post(conn, post_id, user), user)
    return templates.TemplateResponse(
        request, "admin/post_delete.html", {"title": "Delete Post", "user": user, "post": post}
    )


@router.post("/{post_id}/delete")
def post_delete(post_id: int, user=Depends(auth.require_user), conn=Depends(db.get_db)):
    post = _deletable(_own_post(conn, post_id, user), user)
    posts.delete_post(conn, post.id)
    return RedirectResponse("/admin/posts", status_code=303)


CONFIRMS = {
    "publish": ("Publish this?", "Yes, publish it", posts.DRAFT, posts.PUBLISHED,
                "It becomes Live at the next Publish run."),
    "unpublish": ("Are you sure you want to unpublish this?", "Yes, unpublish it",
                  posts.PUBLISHED, posts.DRAFT,
                  "It returns to Draft and leaves the public site at the next Publish run."),
}

admin_only = Depends(auth.require_role("admin"))


def _confirm_page(action: str, post_id: int, request, user, conn):
    heading, button, _, _, note = CONFIRMS[action]
    post = _own_post(conn, post_id, user)
    return templates.TemplateResponse(
        request, "admin/post_confirm.html",
        {"title": heading, "user": user, "post": post, "action": action,
         "heading": heading, "button": button, "note": note},
    )


def _change_status(action: str, post_id: int, request, user, conn):
    _, _, from_status, to_status, _ = CONFIRMS[action]
    post = _own_post(conn, post_id, user)
    if post.status == from_status:
        posts.set_status(conn, post_id, to_status, auth.now(request))
    return RedirectResponse(f"/admin/posts/{post_id}", status_code=303)


@router.get("/{post_id}/publish")
def post_publish_confirm(post_id: int, request: Request, user=admin_only,
                         conn=Depends(db.get_db)):
    return _confirm_page("publish", post_id, request, user, conn)


@router.post("/{post_id}/publish")
def post_publish(post_id: int, request: Request, user=admin_only, conn=Depends(db.get_db)):
    return _change_status("publish", post_id, request, user, conn)


@router.get("/{post_id}/unpublish")
def post_unpublish_confirm(post_id: int, request: Request, user=admin_only,
                           conn=Depends(db.get_db)):
    return _confirm_page("unpublish", post_id, request, user, conn)


@router.post("/{post_id}/unpublish")
def post_unpublish(post_id: int, request: Request, user=admin_only, conn=Depends(db.get_db)):
    return _change_status("unpublish", post_id, request, user, conn)
