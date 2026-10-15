"""Sessions, CSRF and the permission guard. Every admin route goes through here."""
from __future__ import annotations

import secrets

from fastapi import Depends, HTTPException, Request
from jinja2 import pass_context

from app import db, settings, users

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


class NotSignedIn(Exception):
    """Raised by the guard; the app turns it into a redirect to /login."""


def ensure_csrf(request: Request) -> str:
    token = request.session.get("csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf"] = token
    return token


@pass_context
def csrf_token(context) -> str:
    """Use as {{ csrf_token() }} inside every state-changing form."""
    return ensure_csrf(context["request"])


async def csrf_protect(request: Request) -> None:
    """App-wide: any request that is not GET/HEAD/OPTIONS needs a valid token."""
    if request.method in SAFE_METHODS:
        return
    if request.url.path.startswith("/admin") and "user_id" not in request.session:
        raise NotSignedIn  # anonymous: send to login rather than a CSRF error
    form = await request.form()
    sent = str(form.get("csrf_token", ""))
    expected = request.session.get("csrf", "")
    if not expected or not secrets.compare_digest(sent, expected):
        raise HTTPException(status_code=403, detail="Invalid or missing CSRF token")


def start_session(request: Request, user: users.User) -> None:
    request.session.clear()  # fresh session on sign-in
    request.session["user_id"] = user.id
    request.session["last_seen"] = request.app.state.clock()
    ensure_csrf(request)


def end_session(request: Request) -> None:
    request.session.clear()


def require_user(request: Request, conn=Depends(db.get_db)) -> users.User:
    """Signed in, not idle too long, and still active; otherwise to the login page."""
    user_id = request.session.get("user_id")
    last_seen = request.session.get("last_seen")
    now = request.app.state.clock()
    if user_id is None or last_seen is None or now - last_seen > settings.IDLE_TIMEOUT_SECONDS:
        end_session(request)
        raise NotSignedIn
    user = users.get_user(conn, user_id)
    if user is None or not user.active:
        end_session(request)
        raise NotSignedIn
    request.session["last_seen"] = now
    return user


def require_role(*roles: str):
    """Guard for role-restricted routes: Depends(require_role("admin"))."""

    def guard(user: users.User = Depends(require_user)) -> users.User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="You do not have access to this page")
        return user

    return guard
