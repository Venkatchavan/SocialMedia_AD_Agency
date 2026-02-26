"""db.repo_runs — Run metadata repository."""

from __future__ import annotations

from typing import Optional

from core.utils_time import utcnow_iso
from db.sqlite import get_connection


def create_run(run_id: str, workspace_id: str, notes: str = "") -> None:
    """Register a new pipeline run."""
    with get_connection() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO runs
               (run_id, workspace_id, started_at, status, notes)
               VALUES (?, ?, ?, 'running', ?)""",
            (run_id, workspace_id, utcnow_iso(), notes),
        )


def finish_run(run_id: str, status: str = "completed") -> None:
    """Mark a run as finished."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE runs SET finished_at=?, status=? WHERE run_id=?",
            (utcnow_iso(), status, run_id),
        )


def get_run(run_id: str) -> Optional[dict]:
    """Return run metadata dict or None."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM runs WHERE run_id=?", (run_id,)
        ).fetchone()
    if row is None:
        return None
    return dict(row)


def list_runs(workspace_id: str) -> list[dict]:
    """List all runs for a workspace, newest first."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM runs WHERE workspace_id=? ORDER BY started_at DESC",
            (workspace_id,),
        ).fetchall()
    return [dict(r) for r in rows]
