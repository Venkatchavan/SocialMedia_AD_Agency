"""collectors.csv_importer — Generic CSV → Asset importer."""

from __future__ import annotations

import csv
from pathlib import Path

from core.enums import Platform
from core.schemas_asset import Asset, Provenance
from core.utils_hash import hash_text, stable_asset_id
from core.utils_time import utcnow_iso
from core.logging import get_logger

_log = get_logger(__name__)

# Mapping from CSV column name alternatives to Asset fields
_COL_MAP: dict[str, list[str]] = {
    "ad_id": ["ad_id", "id", "asset_id"],
    "platform": ["platform", "source"],
    "caption": ["caption", "caption_or_copy", "ad_text", "text", "copy"],
    "media_url": ["media_url", "video_url", "image_url"],
    "headline": ["headline", "title"],
    "cta": ["cta", "cta_text"],
    "landing": ["landing_page_url", "link", "landing_url"],
}


def _resolve_col(row: dict, key: str) -> str | None:
    for alt in _COL_MAP.get(key, [key]):
        if alt in row and row[alt]:
            return row[alt]
    return None


def import_csv(
    csv_path: str | Path,
    workspace_id: str,
    run_id: str,
    brand: str,
    platform: Platform = Platform.META,
) -> list[Asset]:
    """Import a CSV file into Asset objects."""
    path = Path(csv_path)
    if not path.exists():
        _log.warning("CSV file not found: %s", path)
        return []
    assets: list[Asset] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            aid = _resolve_col(row, "ad_id") or ""
            if not aid:
                continue
            assets.append(
                Asset(
                    asset_id=stable_asset_id(platform.value, brand, aid),
                    platform=platform,
                    workspace_id=workspace_id,
                    run_id=run_id,
                    brand=brand,
                    collected_at=utcnow_iso(),
                    caption_or_copy=_resolve_col(row, "caption"),
                    media_url=_resolve_col(row, "media_url"),
                    headline=_resolve_col(row, "headline"),
                    cta=_resolve_col(row, "cta"),
                    landing_page_url=_resolve_col(row, "landing"),
                    text_hash=hash_text(_resolve_col(row, "caption")),
                    provenance=Provenance(
                        collector="CSVImporter",
                        collector_version="0.1.0",
                        source_url=str(path),
                        fetched_at=utcnow_iso(),
                    ),
                )
            )
    _log.info("CSV imported %d assets from %s", len(assets), path.name)
    return assets
