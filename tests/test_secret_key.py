"""In production the app refuses to start with a missing or well-known secret key."""
import pytest

from app import settings
from app.cli import main
from app.main import create_app

BAD_KEYS = [None, "", settings.DEV_SECRET_KEY, settings.EXAMPLE_SECRET_KEY]


def set_env(monkeypatch, key):
    monkeypatch.setenv("CMS_ENV", "production")
    if key is None:
        monkeypatch.delenv("CMS_SECRET_KEY", raising=False)
    else:
        monkeypatch.setenv("CMS_SECRET_KEY", key)


@pytest.mark.parametrize("key", BAD_KEYS)
def test_create_app_refuses_unsafe_key_in_production(monkeypatch, tmp_path, key):
    set_env(monkeypatch, key)
    with pytest.raises(RuntimeError, match="CMS_SECRET_KEY"):
        create_app(database=tmp_path / "x.db")


@pytest.mark.parametrize("key", BAD_KEYS)
def test_cms_serve_refuses_unsafe_key_in_production(monkeypatch, capsys, key):
    set_env(monkeypatch, key)
    assert main(["serve"]) == 1
    assert "CMS_SECRET_KEY" in capsys.readouterr().out


def test_production_accepts_a_private_key(monkeypatch, tmp_path):
    set_env(monkeypatch, "a-private-random-value-7f3c9e1b")
    create_app(database=tmp_path / "x.db")


def test_development_still_starts_without_a_key(monkeypatch, tmp_path):
    monkeypatch.delenv("CMS_ENV", raising=False)
    monkeypatch.delenv("CMS_SECRET_KEY", raising=False)
    create_app(database=tmp_path / "x.db")
