"""The shared Jinja environment for the admin console."""
from __future__ import annotations

from fastapi.templating import Jinja2Templates

from app import auth, settings

templates = Jinja2Templates(directory=str(settings.TEMPLATES))
templates.env.globals["csrf_token"] = auth.csrf_token


def url(path: str) -> str:
    """Every admin link goes through here, so a mount prefix has one place to live."""
    return path


templates.env.globals["url"] = url
