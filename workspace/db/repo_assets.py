"""db.repo_assets — Asset repository (CRUD over SQLite)."""

from __future__ import annotations


from core.schemas_asset import Asset
from db.sqlite import get_connection


def upsert_asset(asset: Asset) -> None:
    """Insert or replace an asset row."""
    with get_connection() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO assets
               (asset_id, platform, workspace_id, run_id, brand, collected_at, data_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                asset.asset_id,
                asset.platform.value,
                asset.workspace_id,
                asset.run_id,
                asset.brand,
                asset.collected_at,
                asset.model_dump_json(),
            ),
        )


def upsert_many(assets: list[Asset]) -> int:
    """Bulk upsert; return count inserted."""
    for a in assets:
        upsert_asset(a)
    return len(assets)


def get_assets_for_run(workspace_id: str, run_id: str) -> list[Asset]:
    """Load all assets for a given run."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT data_json FROM assets WHERE workspace_id=? AND run_id=?",
            (workspace_id, run_id),
        ).fetchall()
    return [Asset.model_validate_json(r["data_json"]) for r in rows]


def get_asset(asset_id: str) -> Asset | None:
    """Load a single asset by ID."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT data_json FROM assets WHERE asset_id=?", (asset_id,)
        ).fetchone()
    if row is None:
        return None
    return Asset.model_validate_json(row["data_json"])


def count_assets(workspace_id: str) -> int:
    """Return total asset count for workspace."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM assets WHERE workspace_id=?",
            (workspace_id,),
        ).fetchone()
    return row["cnt"] if row else 0
