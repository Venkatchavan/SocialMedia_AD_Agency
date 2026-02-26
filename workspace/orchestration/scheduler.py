"""orchestration.scheduler — Weekly per-workspace pipeline refresh."""

from __future__ import annotations

import json
import time
from pathlib import Path

import yaml

from core.config import CLIENTS_DIR, DATE_RANGE_DAYS, MAX_ASSETS_PER_BRAND
from core.logging import get_logger
from core.doc_updater import append_phase_notes

_log = get_logger(__name__)

_SCHEDULE_INTERVAL_SECS = 7 * 24 * 60 * 60  # one week


def discover_workspaces() -> list[str]:
    """List all workspace IDs under clients/."""
    if not CLIENTS_DIR.exists():
        return []
    return [d.name for d in CLIENTS_DIR.iterdir() if d.is_dir()]


def load_competitors(workspace_id: str) -> dict | None:
    """Load Competitors.yml for a workspace."""
    fp = CLIENTS_DIR / workspace_id / "Competitors.yml"
    if not fp.exists():
        return None
    return yaml.safe_load(fp.read_text(encoding="utf-8"))


def run_scheduled_cycle() -> None:
    """Execute one scheduled cycle for all workspaces."""
    workspaces = discover_workspaces()
    _log.info("Scheduler: found %d workspaces", len(workspaces))

    for ws_id in workspaces:
        _log.info("Scheduler: running workspace %s", ws_id)
        try:
            _run_workspace(ws_id)
        except Exception as exc:
            _log.error("Scheduler error for %s: %s", ws_id, exc)


def _run_workspace(workspace_id: str) -> None:
    """Run the full pipeline for one workspace."""
    from orchestration.pipeline import run_pipeline
    from collectors.tiktok_collector import TikTokCollector
    from collectors.meta_collector import MetaCollector
    from collectors.pinterest_collector import PinterestCollector
    from collectors.x_collector import XCollector

    competitors = load_competitors(workspace_id) or {}
    run_id_hint = "scheduled"

    all_assets = []
    for comp in competitors.get("competitors", []):
        brand = comp.get("name", "unknown")
        # TikTok
        kws = comp.get("tiktok_keywords", [])
        if kws:
            all_assets.extend(
                TikTokCollector().collect(workspace_id, run_id_hint, brand, keywords=kws)
            )
        # Meta
        meta_urls = [comp.get("meta_ad_library_url", "")]
        meta_urls = [u for u in meta_urls if u]
        if meta_urls:
            all_assets.extend(
                MetaCollector().collect(workspace_id, run_id_hint, brand, ad_library_urls=meta_urls)
            )
        # Pinterest
        pin_name = comp.get("pinterest_advertiser_name")
        if pin_name:
            all_assets.extend(
                PinterestCollector().collect(workspace_id, run_id_hint, brand, search_queries=[pin_name])
            )
        # X
        x_handle = comp.get("x_advertiser_handle")
        if x_handle:
            all_assets.extend(
                XCollector().collect(workspace_id, run_id_hint, brand, mode="organic_api", advertiser=x_handle)
            )

    if not all_assets:
        _log.warning("Scheduler: no assets collected for %s", workspace_id)
        return

    result = run_pipeline(workspace_id, all_assets)
    _log.info("Scheduler: completed %s → %s", workspace_id, result)


def run_scheduler_loop() -> None:
    """Run indefinitely on a weekly cadence."""
    _log.info("Scheduler loop started (interval=%ds)", _SCHEDULE_INTERVAL_SECS)
    while True:
        run_scheduled_cycle()
        _log.info("Scheduler sleeping for %d seconds", _SCHEDULE_INTERVAL_SECS)
        time.sleep(_SCHEDULE_INTERVAL_SECS)
