"""SQLite access. One short-lived connection per request."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterator

from fastapi import Request

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('admin', 'editor')),
    active        INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS posts (
    id         INTEGER PRIMARY KEY,
    title      TEXT NOT NULL,
    slug       TEXT NOT NULL UNIQUE,
    body       TEXT NOT NULL DEFAULT '',
    status     TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published')),
    author_id  INTEGER NOT NULL REFERENCES users (id),
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
"""


def connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(path: Path) -> None:
    conn = connect(path)
    with conn:
        conn.executescript(SCHEMA)
    conn.close()


def get_db(request: Request) -> Iterator[sqlite3.Connection]:
    """FastAPI dependency: a connection for this request, closed afterwards."""
    conn = connect(request.app.state.database)
    try:
        yield conn
    finally:
        conn.close()
