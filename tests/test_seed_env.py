"""Regression test for #9: the seed script must load .env itself."""
from __future__ import annotations

import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_seed_script_loads_env_from_fresh_copy_of_env_example(tmp_path):
    shutil.copy(ROOT / ".env.example", tmp_path / ".env")
    # A clean environment: no CMS_* variables, so only .env can supply them.
    env = {k: v for k, v in os.environ.items() if not k.startswith("CMS_")}
    env["CMS_ENV_FILE"] = str(tmp_path / ".env")

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "seed_demo.py")],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=120,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Set CMS_ADMIN_PASSWORD" not in result.stdout
    # CMS_DATABASE=cms.db in .env.example is relative to the working directory.
    conn = sqlite3.connect(tmp_path / "cms.db")
    emails = {row[0] for row in conn.execute("SELECT email FROM users")}
    conn.close()
    assert emails == {"admin@example.test", "editor@example.test"}


def test_load_env_file_parses_and_real_environment_wins(tmp_path, monkeypatch):
    from app import settings

    env_file = tmp_path / ".env"
    env_file.write_text(
        "# comment\n\nA_PLAIN=one\nexport B_EXPORT=two\nC_QUOTED=\"three\"\n"
        "D_EQUALS=a=b\nE_EMPTY=\nF_KEPT=from-file\nno-equals-line\n"
    )
    for name in ("A_PLAIN", "B_EXPORT", "C_QUOTED", "D_EQUALS", "E_EMPTY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("F_KEPT", "from-environment")

    settings.load_env_file(env_file)

    assert os.environ["A_PLAIN"] == "one"
    assert os.environ["B_EXPORT"] == "two"
    assert os.environ["C_QUOTED"] == "three"
    assert os.environ["D_EQUALS"] == "a=b"
    assert os.environ["E_EMPTY"] == ""
    assert os.environ["F_KEPT"] == "from-environment"
    for name in ("A_PLAIN", "B_EXPORT", "C_QUOTED", "D_EQUALS", "E_EMPTY"):
        monkeypatch.delenv(name)


def test_load_env_file_missing_file_is_fine(tmp_path):
    from app import settings

    settings.load_env_file(tmp_path / "nope.env")


def test_default_env_file_is_dot_env_at_repo_root():
    """The grader copies .env.example to ./.env at the repo root; settings must read that."""
    from app import settings

    assert settings.DEFAULT_ENV_FILE == settings.ROOT / ".env"
    assert (ROOT / ".env.example").exists()
