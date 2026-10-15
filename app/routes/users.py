"""Console routes for User management. President-only: every route is behind the admin guard.

There is deliberately no delete route: Users are only ever Deactivated.
"""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

from app import auth, db, users
from app.templating import flash, templates

router = APIRouter(prefix="/admin/users", dependencies=[Depends(auth.require_role("admin"))])


def _list(request, user, conn, error=None, form_email="", form_role="editor", status_code=200,
          form_name=""):
    return templates.TemplateResponse(
        request, "admin/user_list.html",
        {"title": "Users", "user": user, "users": users.list_users(conn), "error": error,
         "form_email": form_email, "form_role": form_role, "form_name": form_name, "roles": users.ROLES},
        status_code=status_code)


@router.get("")
def user_list(request: Request, user=Depends(auth.require_user), conn=Depends(db.get_db)):
    return _list(request, user, conn)


@router.post("")
def user_create(request: Request, email: str = Form(""), role: str = Form("editor"),
                password: str = Form(""), display_name: str = Form(""), user=Depends(auth.require_user),
                conn=Depends(db.get_db)):
    email = users.normalize_email(email)

    def fail(message):
        return _list(request, user, conn, message, email, role, 400, display_name)

    local = email.removesuffix(users.EMAIL_DOMAIN)
    if local == email or not local or "@" in local or " " in local:
        return fail(f"Use a Kenyon email address ending {users.EMAIL_DOMAIN}")
    if not display_name.strip():
        return fail("Give the User a display name; it is shown in public bylines")
    if role not in users.ROLES:
        return fail("Choose a role")
    if len(password) < users.MIN_PASSWORD_LENGTH:
        return fail(f"The first password needs at least {users.MIN_PASSWORD_LENGTH} characters")
    try:
        users.create_user(conn, email, password, role, display_name)
    except sqlite3.IntegrityError:
        return fail("A User with that email already exists")
    flash(request, "User created.")
    return RedirectResponse("/admin/users", status_code=303)


def _change(request: Request, user, conn, user_id: int, apply, done: str) -> object:
    if users.get_user(conn, user_id) is None:
        raise HTTPException(status_code=404, detail="No such User")
    try:
        apply()
    except users.GuardRailError as exc:
        return _list(request, user, conn, str(exc), status_code=400)
    flash(request, done)
    return RedirectResponse("/admin/users", status_code=303)


@router.post("/{user_id}/role")
def user_role(user_id: int, request: Request, role: str = Form(""),
              user=Depends(auth.require_user), conn=Depends(db.get_db)):
    return _change(request, user, conn, user_id, lambda: users.set_role(conn, user_id, role, user.id),
                   "Role changed.")


@router.post("/{user_id}/name")
def user_name(user_id: int, request: Request, display_name: str = Form(""),
              user=Depends(auth.require_user), conn=Depends(db.get_db)):
    return _change(request, user, conn, user_id,
                   lambda: users.set_display_name(conn, user_id, display_name),
                   "Name saved.")


@router.post("/{user_id}/deactivate")
def user_deactivate(user_id: int, request: Request, user=Depends(auth.require_user),
                    conn=Depends(db.get_db)):
    return _change(request, user, conn, user_id,
                   lambda: users.set_active(conn, user_id, False, user.id),
                   "User deactivated.")


@router.post("/{user_id}/reactivate")
def user_reactivate(user_id: int, request: Request, user=Depends(auth.require_user),
                    conn=Depends(db.get_db)):
    return _change(request, user, conn, user_id,
                   lambda: users.set_active(conn, user_id, True, user.id),
                   "User reactivated.")
