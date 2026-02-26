"""collectors.pinterest_collector — Collect Pinterest ads via Apify."""

from __future__ import annotations

from core.enums import Platform
from core.schemas_asset import Asset, Metrics, PlatformFields, Provenance
from core.utils_hash import hash_text, stable_asset_id
from core.utils_time import utcnow_iso
from collectors.apify_client import run_actor
from collectors.base import BaseCollector
from core.logging import get_logger

_log = get_logger(__name__)

_ACTOR_ID = "apify/pinterest-scraper"


class PinterestCollector(BaseCollector):
    platform = Platform.PINTEREST

    def collect(
        self,
        workspace_id: str,
        run_id: str,
        brand: str,
        *,
        search_queries: list[str] | None = None,
        max_items: int = 30,
        **kwargs,
    ) -> list[Asset]:
        queries = search_queries or []
        all_assets: list[Asset] = []
        for q in queries:
            items = run_actor(
                _ACTOR_ID,
                {"search": q, "maxItems": max_items},
            )
            for item in items:
                asset = _map_item(item, workspace_id, run_id, brand)
                if asset:
                    all_assets.append(asset)
        _log.info("Pinterest collected %d assets for brand=%s", len(all_assets), brand)
        return all_assets


def _map_item(item: dict, ws: str, rid: str, brand: str) -> Asset | None:
    pin_id = item.get("id") or item.get("pinId", "")
    if not pin_id:
        return None
    return Asset(
        asset_id=stable_asset_id("pinterest", "pin", str(pin_id)),
        platform=Platform.PINTEREST,
        workspace_id=ws,
        run_id=rid,
        brand=brand,
        collected_at=utcnow_iso(),
        ad_url=item.get("url"),
        media_url=item.get("imageUrl") or item.get("videoUrl"),
        thumbnail_url=item.get("imageUrl"),
        caption_or_copy=item.get("description"),
        headline=item.get("title"),
        landing_page_url=item.get("link"),
        text_hash=hash_text(item.get("description")),
        metrics=Metrics(
            saves=item.get("saveCount"),
            comments=item.get("commentCount"),
        ),
        platform_fields=PlatformFields(pin_id=str(pin_id)),
        provenance=Provenance(
            collector="PinterestCollector",
            collector_version="0.1.0",
            source_url=item.get("url"),
            fetched_at=utcnow_iso(),
        ),
    )
