"""Configuration, read from the environment (never hard-code secrets)."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
SITE = ROOT / "site"

DEV_SECRET_KEY = "dev-only-not-for-production"
EXAMPLE_SECRET_KEY = "change-me-to-a-long-random-string"  # the value in .env.example
SECRET_KEY = os.environ.get("CMS_SECRET_KEY", DEV_SECRET_KEY)
DATABASE_PATH = Path(os.environ.get("CMS_DATABASE", ROOT / "cms.db"))
SITE_TITLE = os.environ.get("CMS_SITE_TITLE", "My CMS")
CONTACT_EMAIL = os.environ.get("CMS_CONTACT_EMAIL", "financeclub@kenyon.edu")
# Set this to your Pages URL once you deploy, e.g.
# https://yourname.github.io/iphs400-mp2-cms/
BASE_PATH = os.environ.get("CMS_BASE_PATH", "")
# Idle sign-out: the Club laptop is shared at meetings.
IDLE_TIMEOUT_SECONDS = 2 * 60 * 60


def require_safe_secret_key() -> None:
    """With CMS_ENV=production, refuse a missing or well-known CMS_SECRET_KEY.

    Anyone who knows the key can forge a session cookie, so the development
    default and the .env.example value must never run in production.
    """
    if os.environ.get("CMS_ENV") != "production":
        return
    key = os.environ.get("CMS_SECRET_KEY", "")
    if key in ("", DEV_SECRET_KEY, EXAMPLE_SECRET_KEY):
        raise RuntimeError(
            "CMS_SECRET_KEY must be set to a private random value when "
            "CMS_ENV=production (it is missing or is a well-known default)."
        )
