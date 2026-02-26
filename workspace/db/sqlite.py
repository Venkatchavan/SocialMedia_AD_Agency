"""db.sqlite — SQLite connection manager (Postgres-switchable)."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from core.config import DATA_DIR, DATABASE_URL
from core.logging import get_logger

_log = get_logger(__name__)

_DB_PATH: Path = DATA_DIR / "creative_os.db"

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS assets (
    asset_id   TEXT PRIMARY KEY,
    platform   TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    run_id     TEXT NOT NULL,
    brand      TEXT NOT NULL,
    collected_at TEXT NOT NULL,
    data_json  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
    run_id       TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    started_at   TEXT NOT NULL,
    finished_at  TEXT,
    status       TEXT DEFAULT 'running',
    notes        TEXT
);

CREATE INDEX IF NOT EXISTS idx_assets_ws ON assets(workspace_id);
CREATE INDEX IF NOT EXISTS idx_assets_run ON assets(run_id);
CREATE INDEX IF NOT EXISTS idx_runs_ws ON runs(workspace_id);
"""


def _ensure_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def init_db() -> None:
    """Create tables if they don't exist."""
    _ensure_dir()
    with get_connection() as conn:
        conn.executescript(_SCHEMA_SQL)
    _log.info("Database initialised at %s", _DB_PATH)


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """Yield a SQLite connection with row_factory."""
    _ensure_dir()
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
