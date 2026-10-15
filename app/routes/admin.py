"""The admin console's home page and the /admin catch-all."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from app import auth, db, pages, posts, publish, users
from app.templating import templates

router = APIRouter(prefix="/admin")

# Include this router LAST: an unknown /admin address still sends anonymous
# visitors to the login page instead of a bare 404.
catch_all = APIRouter(prefix="/admin")


@router.get("")
def admin_home(request: Request, user=Depends(auth.require_user), conn=Depends(db.get_db)):
    is_admin = user.role == "admin"
    counts = posts.count_by_status(conn, None if is_admin else user.id)
    if is_admin:
        for status, n in pages.count_by_status(conn).items():
            counts[status] += n
    active, deactivated = users.count_by_active(conn) if is_admin else (None, None)
    return templates.TemplateResponse(
        request, "admin/hello.html",
        {"title": "Admin", "user": user, "drafts": counts[posts.DRAFT],
         "published": counts[posts.PUBLISHED], "active_users": active,
         "deactivated_users": deactivated,
         "pending": publish.has_pending_changes(conn)},
    )


@catch_all.api_route("/{rest:path}", include_in_schema=False,
                     methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
                     dependencies=[Depends(auth.require_user)])
def admin_unknown(rest: str):
    raise HTTPException(status_code=404)
