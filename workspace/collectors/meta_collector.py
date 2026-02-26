"""collectors.meta_collector — Collect Meta/Facebook ads via Apify."""

from __future__ import annotations

from core.enums import Platform
from core.schemas_asset import Asset, Metrics, PlatformFields, Provenance
from core.utils_hash import hash_text, stable_asset_id
from core.utils_time import utcnow_iso
from collectors.apify_client import run_actor
from collectors.base import BaseCollector
from core.logging import get_logger

_log = get_logger(__name__)

_ACTOR_ID = "apify/facebook-ads-scraper"


class MetaCollector(BaseCollector):
    platform = Platform.META

    def collect(
        self,
        workspace_id: str,
        run_id: str,
        brand: str,
        *,
        ad_library_urls: list[str] | None = None,
        **kwargs,
    ) -> list[Asset]:
        ad_library_urls = ad_library_urls or []
        all_assets: list[Asset] = []
        if not ad_library_urls:
            _log.warning("No Meta ad library URLs provided")
            return all_assets

        items = run_actor(
            _ACTOR_ID,
            {"startUrls": [{"url": u} for u in ad_library_urls]},
        )
        for item in items:
            asset = _map_item(item, workspace_id, run_id, brand)
            if asset:
                all_assets.append(asset)
        _log.info("Meta collected %d assets for brand=%s", len(all_assets), brand)
        return all_assets


def _map_item(item: dict, ws: str, rid: str, brand: str) -> Asset | None:
    ad_id = item.get("adId") or item.get("id", "")
    if not ad_id:
        return None
    return Asset(
        asset_id=stable_asset_id("meta", brand, str(ad_id)),
        platform=Platform.META,
        workspace_id=ws,
        run_id=rid,
        brand=brand,
        collected_at=utcnow_iso(),
        ad_url=item.get("adUrl") or item.get("url"),
        media_url=item.get("imageUrl") or item.get("videoUrl"),
        thumbnail_url=item.get("imageUrl"),
        caption_or_copy=item.get("adText") or item.get("bodyText"),
        headline=item.get("title"),
        cta=item.get("ctaText"),
        landing_page_url=item.get("linkUrl"),
        text_hash=hash_text(item.get("adText") or item.get("bodyText")),
        first_seen_at=item.get("startDate"),
        last_seen_at=item.get("endDate"),
        metrics=Metrics(
            impressions_range=item.get("impressions"),
        ),
        platform_fields=PlatformFields(
            ad_id=str(ad_id),
            page_id=item.get("pageId"),
        ),
        provenance=Provenance(
            collector="MetaCollector",
            collector_version="0.1.0",
            source_url=item.get("url"),
            fetched_at=utcnow_iso(),
        ),
    )
