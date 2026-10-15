"""Console routes for Pages. President-only: every route is behind the admin guard."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

from app import auth, db, pages
from app.markdown import render_markdown
from app.posts import DRAFT, PUBLISHED, slugify
from app.templating import templates

router = APIRouter(prefix="/admin/pages", dependencies=[Depends(auth.require_role("admin"))])


NAV_ERROR = "Navigation order must be a whole number, 0 or more"


def _page(conn, page_id: int) -> pages.Page:
    page = pages.get_page(conn, page_id)
    if page is None:
        raise HTTPException(status_code=404, detail="No such Page")
    return page


def _int(value: str) -> int:
    """The navigation order as a number; anything that is not 0 or more counts as -1."""
    try:
        return max(int(value.strip() or 0), -1)
    except ValueError:
        return -1


def _editor(request, user, page, title, body, nav_order, error=None, status_code=200):
    return templates.TemplateResponse(
        request, "admin/page_edit.html",
        {"title": "Edit Page" if page else "New Page", "user": user, "page": page,
         "form_title": title, "form_body": body, "form_nav_order": nav_order,
         "preview_html": render_markdown(body), "error": error},
        status_code=status_code)


@router.get("")
def page_list():
    return RedirectResponse("/admin/posts?type=page", status_code=303)


@router.get("/new")
def page_new(request: Request, user=Depends(auth.require_user)):
    return _editor(request, user, None, "", "", 0)


@router.post("")
def page_create(request: Request, title: str = Form(""), body: str = Form(""),
                nav_order: str = Form("0"), user=Depends(auth.require_user),
                conn=Depends(db.get_db)):
    title = title.strip()
    if not title:
        return _editor(request, user, None, title, body, nav_order, "A Page needs a title", 400)
    if _int(nav_order) < 0:
        return _editor(request, user, None, title, body, nav_order, NAV_ERROR, 400)
    page_id = pages.create_page(conn, title, body, _int(nav_order), auth.now(request))
    return RedirectResponse(f"/admin/pages/{page_id}", status_code=303)


@router.get("/{page_id}")
def page_edit(page_id: int, request: Request, user=Depends(auth.require_user),
              conn=Depends(db.get_db)):
    page = _page(conn, page_id)
    return _editor(request, user, page, page.title, page.body, page.nav_order)


@router.post("/{page_id}")
def page_update(page_id: int, request: Request, title: str = Form(""), body: str = Form(""),
                nav_order: str = Form("0"), slug: str | None = Form(None),
                user=Depends(auth.require_user), conn=Depends(db.get_db)):
    page = _page(conn, page_id)
    title = title.strip()
    if not title:
        return _editor(request, user, page, title, body, nav_order, "A Page needs a title", 400)
    if _int(nav_order) < 0:
        return _editor(request, user, page, title, body, nav_order, NAV_ERROR, 400)
    new_slug = slugify(slug) if slug and slug.strip() else None
    if new_slug and pages.slug_taken(conn, new_slug, page_id):
        return _editor(request, user, page, title, body, _int(nav_order),
                       f"The slug “{new_slug}” is already used by another Page", 400)
    pages.update_page(conn, page_id, title, body, _int(nav_order), auth.now(request), new_slug)
    return RedirectResponse(f"/admin/pages/{page_id}", status_code=303)


CONFIRMS = {
    "publish": ("Publish this?", "Yes, publish it", DRAFT, PUBLISHED,
                "It becomes Live at the next Publish run."),
    "unpublish": ("Are you sure you want to unpublish this?", "Yes, unpublish it",
                  PUBLISHED, DRAFT,
                  "It returns to Draft and leaves the public site at the next Publish run."),
}


def _confirm(action: str, page_id: int, request, user, conn):
    heading, button, _, _, note = CONFIRMS[action]
    return templates.TemplateResponse(
        request, "admin/page_confirm.html",
        {"title": heading, "user": user, "page": _page(conn, page_id), "action": action,
         "heading": heading, "button": button, "note": note})


def _change(action: str, page_id: int, request, conn):
    _, _, from_status, to_status, _ = CONFIRMS[action]
    if _page(conn, page_id).status == from_status:
        pages.set_status(conn, page_id, to_status, auth.now(request))
    return RedirectResponse(f"/admin/pages/{page_id}", status_code=303)


@router.get("/{page_id}/publish")
def page_publish_confirm(page_id: int, request: Request, user=Depends(auth.require_user),
                         conn=Depends(db.get_db)):
    return _confirm("publish", page_id, request, user, conn)


@router.post("/{page_id}/publish")
def page_publish(page_id: int, request: Request, conn=Depends(db.get_db)):
    return _change("publish", page_id, request, conn)


@router.get("/{page_id}/unpublish")
def page_unpublish_confirm(page_id: int, request: Request, user=Depends(auth.require_user),
                           conn=Depends(db.get_db)):
    return _confirm("unpublish", page_id, request, user, conn)


@router.post("/{page_id}/unpublish")
def page_unpublish(page_id: int, request: Request, conn=Depends(db.get_db)):
    return _change("unpublish", page_id, request, conn)


@router.get("/{page_id}/delete")
def page_delete_confirm(page_id: int, request: Request, user=Depends(auth.require_user),
                        conn=Depends(db.get_db)):
    return templates.TemplateResponse(
        request, "admin/page_delete.html",
        {"title": "Delete Page", "user": user, "page": _page(conn, page_id)})


@router.post("/{page_id}/delete")
def page_delete(page_id: int, conn=Depends(db.get_db)):
    pages.delete_page(conn, _page(conn, page_id).id)
    return RedirectResponse("/admin/posts?type=page", status_code=303)
