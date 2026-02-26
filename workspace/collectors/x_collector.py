"""collectors.x_collector — Collect X/Twitter ads via CSV import or organic API."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional

from core.enums import Platform
from core.schemas_asset import Asset, PlatformFields, Provenance
from core.utils_hash import hash_text, stable_asset_id
from core.utils_time import utcnow_iso
from collectors.base import BaseCollector
from core.config import X_BEARER_TOKEN
from core.logging import get_logger

_log = get_logger(__name__)


class XCollector(BaseCollector):
    platform = Platform.X

    def collect(
        self,
        workspace_id: str,
        run_id: str,
        brand: str,
        *,
        mode: str = "ads_repository_csv",
        csv_source: Optional[str] = None,
        advertiser: Optional[str] = None,
        **kwargs,
    ) -> list[Asset]:
        if mode == "ads_repository_csv":
            return self._from_csv(workspace_id, run_id, brand, csv_source)
        elif mode == "organic_api":
            return self._from_api(workspace_id, run_id, brand, advertiser)
        _log.warning("Unknown X collection mode: %s", mode)
        return []

    def _from_csv(
        self, ws: str, rid: str, brand: str, csv_path: Optional[str]
    ) -> list[Asset]:
        if not csv_path or not Path(csv_path).exists():
            _log.warning("X CSV not found: %s", csv_path)
            return []
        assets: list[Asset] = []
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                asset = _map_csv_row(row, ws, rid, brand)
                if asset:
                    assets.append(asset)
        _log.info("X CSV imported %d assets", len(assets))
        return assets

    def _from_api(
        self, ws: str, rid: str, brand: str, advertiser: Optional[str]
    ) -> list[Asset]:
        if not X_BEARER_TOKEN:
            _log.warning("X_BEARER_TOKEN missing — skipping organic API")
            return []
        _log.info("X organic API stub — not yet implemented")
        return []


def _map_csv_row(row: dict, ws: str, rid: str, brand: str) -> Asset | None:
    ad_id = row.get("ad_id") or row.get("id", "")
    advertiser = row.get("advertiser_name", brand)
    if not ad_id:
        return None
    return Asset(
        asset_id=stable_asset_id("x", "adsrepo", advertiser, str(ad_id)),
        platform=Platform.X,
        workspace_id=ws,
        run_id=rid,
        brand=brand,
        collected_at=utcnow_iso(),
        caption_or_copy=row.get("ad_text") or row.get("content"),
        text_hash=hash_text(row.get("ad_text") or row.get("content")),
        media_url=row.get("media_url"),
        first_seen_at=row.get("first_shown"),
        last_seen_at=row.get("last_shown"),
        platform_fields=PlatformFields(
            ad_id=str(ad_id),
            tweet_id=row.get("tweet_id"),
        ),
        provenance=Provenance(
            collector="XCollector",
            collector_version="0.1.0",
            source_url=row.get("source_url"),
            fetched_at=utcnow_iso(),
            notes="EU/DSA Ads Repository CSV import",
        ),
    )
