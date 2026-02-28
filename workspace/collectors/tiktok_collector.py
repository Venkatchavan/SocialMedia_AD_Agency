"""collectors.tiktok_collector — Collect TikTok ads via Apify actor."""

from __future__ import annotations

from core.enums import Platform
from core.schemas_asset import Asset, Metrics, PlatformFields, Provenance
from core.utils_hash import hash_text, stable_asset_id
from core.utils_time import utcnow_iso
from collectors.apify_client import run_actor
from collectors.base import BaseCollector
from core.logging import get_logger

_log = get_logger(__name__)

# Default Apify actor for TikTok ad scraping
_ACTOR_ID = "clockworks/tiktok-scraper"


class TikTokCollector(BaseCollector):
    platform = Platform.TIKTOK

    def collect(
        self,
        workspace_id: str,
        run_id: str,
        brand: str,
        *,
        keywords: list[str] | None = None,
        count_per_keyword: int = 10,
        **kwargs,
    ) -> list[Asset]:
        keywords = keywords or []
        all_assets: list[Asset] = []
        for kw in keywords:
            items = run_actor(
                _ACTOR_ID,
                {
                    "searchQueries": [kw],
                    "resultsPerPage": count_per_keyword,
                    "shouldDownloadVideos": False,
                },
            )
            for item in items:
                asset = _map_item(item, workspace_id, run_id, brand)
                if asset:
                    all_assets.append(asset)
        _log.info("TikTok collected %d assets for brand=%s", len(all_assets), brand)
        return all_assets


def _map_item(item: dict, ws: str, rid: str, brand: str) -> Asset | None:
    video_id = item.get("id") or item.get("videoId", "")
    if not video_id:
        return None
    return Asset(
        asset_id=stable_asset_id("tiktok", str(video_id)),
        platform=Platform.TIKTOK,
        workspace_id=ws,
        run_id=rid,
        brand=brand,
        collected_at=utcnow_iso(),
        ad_url=item.get("webVideoUrl"),
        media_url=item.get("videoUrl"),
        thumbnail_url=item.get("coverUrl"),
        caption_or_copy=item.get("text"),
        text_hash=hash_text(item.get("text")),
        metrics=Metrics(
            views=item.get("playCount"),
            likes=item.get("diggCount"),
            comments=item.get("commentCount"),
            shares=item.get("shareCount"),
        ),
        platform_fields=PlatformFields(post_id=str(video_id)),
        provenance=Provenance(
            collector="TikTokCollector",
            collector_version="0.1.0",
            source_url=item.get("webVideoUrl"),
            fetched_at=utcnow_iso(),
        ),
    )
