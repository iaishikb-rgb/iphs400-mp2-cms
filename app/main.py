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

from fastapi import Depends, FastAPI, Request
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from app import auth, db, settings
from app.routes import admin as admin_routes
from app.routes import auth as auth_routes
from app.templating import templates


def create_app(database: Path | None = None,
               clock: Callable[[], float] | None = None) -> FastAPI:
    settings.require_safe_secret_key()
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

    app.include_router(auth_routes.router)
    app.include_router(admin_routes.router)

    @app.get("/")
    def public_home(request: Request):
        return templates.TemplateResponse(
            request, "public/home.html",
            {"title": settings.SITE_TITLE, "items": []},
        )

    # Later ticket routers plug in here, above the catch-all.
    app.include_router(admin_routes.catch_all)  # keep LAST

    return app


app = create_app()
