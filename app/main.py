"""The FastAPI application.

The admin console answers at /admin and the public site answers at /. Sign-in,
sessions, CSRF and the permission guard live in app/auth.py; add routes in their
own modules (app/routes/...) and include them here. Keep this file small.
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Callable

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from app import auth, db, settings
from app.templating import templates


def create_app(database: Path | None = None,
               clock: Callable[[], float] | None = None) -> FastAPI:
    database = Path(database or settings.DATABASE_PATH)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        db.init_db(database)
        yield

    app = FastAPI(title="IPHS 400 MP2 CMS", lifespan=lifespan,
                  dependencies=[Depends(auth.csrf_protect)])
    app.state.database = database
    app.state.clock = clock or time.time
    app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY,
                       session_cookie="cms_session", same_site="lax",
                       max_age=None)

    @app.exception_handler(auth.NotSignedIn)
    async def to_login(request: Request, exc: auth.NotSignedIn):
        return RedirectResponse("/login", status_code=303)

    from app.routes import auth as auth_routes

    app.include_router(auth_routes.router)

    admin = APIRouter(prefix="/admin")

    @admin.get("")
    def admin_home(request: Request, user=Depends(auth.require_user)):
        return templates.TemplateResponse(
            request, "admin/hello.html", {"title": "Admin", "user": user}
        )

    app.include_router(admin)

    @app.get("/")
    def public_home(request: Request):
        return templates.TemplateResponse(
            request, "public/home.html",
            {"title": settings.SITE_TITLE, "items": []},
        )

    # Later ticket routers plug in here, above the catch-all below.

    # Keep LAST: an unknown /admin address still sends anonymous visitors to login.
    @app.api_route("/admin/{rest:path}", include_in_schema=False,
                   methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
                   dependencies=[Depends(auth.require_user)])
    def admin_unknown(rest: str):
        raise HTTPException(status_code=404)

    return app


app = create_app()
