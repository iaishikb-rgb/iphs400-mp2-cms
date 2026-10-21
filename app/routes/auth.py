"""/login and /logout."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from app import auth, db, login_limiter, users
from app.templating import templates

router = APIRouter()

GENERIC_ERROR = "Email or password is incorrect"
LOCKED_MESSAGE = "Too many failed attempts. Try again in 15 minutes."


@router.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse(
        request, "admin/login.html", {"title": "Sign in", "error": None}
    )


@router.post("/login")
def login(request: Request, email: str = Form(""), password: str = Form(""),
          conn=Depends(db.get_db)):
    now = auth.now(request)
    if login_limiter.is_locked(email, now):
        return templates.TemplateResponse(
            request, "admin/login.html",
            {"title": "Sign in", "error": LOCKED_MESSAGE}, status_code=429,
        )
    user = users.authenticate(conn, email, password)
    if user is None:
        login_limiter.record_failure(email, now)
        return templates.TemplateResponse(
            request, "admin/login.html", {"title": "Sign in", "error": GENERIC_ERROR},
            status_code=401,
        )
    auth.start_session(request, user)
    return RedirectResponse("/admin", status_code=303)


@router.post("/logout")
def logout(request: Request):
    auth.end_session(request)
    return RedirectResponse("/login", status_code=303)
