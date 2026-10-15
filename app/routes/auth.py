"""/login and /logout."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from app import auth, db, users
from app.templating import templates

router = APIRouter()

GENERIC_ERROR = "Email or password is incorrect"


@router.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse(
        request, "admin/login.html", {"title": "Sign in", "error": None}
    )


@router.post("/login")
def login(request: Request, email: str = Form(""), password: str = Form(""),
          conn=Depends(db.get_db)):
    user = users.authenticate(conn, email, password)
    if user is None:
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
