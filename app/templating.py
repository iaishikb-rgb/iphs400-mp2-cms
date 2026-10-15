"""The shared Jinja environment for the admin console."""
from __future__ import annotations

from fastapi.templating import Jinja2Templates

from app import auth, settings


def flash(request, message: str) -> None:
    """Remember a one-time success message for the next page the User sees."""
    request.session["flash"] = message


def _flash_processor(request) -> dict:
    return {"flash": request.session.pop("flash", None)}


templates = Jinja2Templates(directory=str(settings.TEMPLATES),
                            context_processors=[_flash_processor])
templates.env.globals["csrf_token"] = auth.csrf_token


def url(path: str) -> str:
    """Every admin link goes through here, so a mount prefix has one place to live."""
    return path


templates.env.globals["url"] = url
