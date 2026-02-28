"""YouTube collector — uses YouTube Data API v3 to find short-form video ads.

Searches for competitor/product-related Shorts and collects engagement data.
Uses official API only — no scraping.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

import structlog

from app.collectors.base_collector import BaseCollector, CollectedAd
from app.config import get_settings

logger = structlog.get_logger(__name__)


class YouTubeCollector(BaseCollector):
    """Collect short-form video ads from YouTube Data API v3."""

    platform_name = "youtube"

    def __init__(self, api_key: str = "") -> None:
        settings = get_settings()
        self._api_key = api_key or getattr(settings, "youtube_api_key", "")

    def validate_credentials(self) -> bool:
        """Check if YouTube API key is set."""
        return bool(self._api_key)

    def collect(
        self,
        query: str,
        workspace_id: str,
        max_results: int = 25,
        **kwargs: Any,
    ) -> list[CollectedAd]:
        """Search YouTube for short-form videos matching query.

        Uses search.list endpoint with type=video, videoDuration=short.
        """
        if not self.validate_credentials():
            logger.warning("youtube_missing_api_key", workspace_id=workspace_id)
            return []

        logger.info(
            "youtube_collect_start",
            query=query,
            workspace_id=workspace_id,
            max_results=max_results,
        )

        # Build API request params
        params = self._build_search_params(query, max_results, **kwargs)

        # In production, call: GET https://www.googleapis.com/youtube/v3/search
        # For now, return params structure for integration testing
        results = self._execute_search(params, workspace_id)

        logger.info(
            "youtube_collect_complete",
            workspace_id=workspace_id,
            results_count=len(results),
        )
        return results

    def _build_search_params(
        self, query: str, max_results: int, **kwargs: Any
    ) -> dict[str, Any]:
        """Build YouTube Data API v3 search parameters."""
        return {
            "part": "snippet",
            "q": query,
            "type": "video",
            "videoDuration": kwargs.get("duration", "short"),
            "order": kwargs.get("order", "relevance"),
            "maxResults": min(max_results, 50),  # API max is 50
            "key": self._api_key,
            "relevanceLanguage": kwargs.get("language", "en"),
        }

    def _execute_search(
        self, params: dict[str, Any], workspace_id: str
    ) -> list[CollectedAd]:
        """Execute the YouTube search API call.

        NOTE: Actual HTTP call requires `httpx` or `aiohttp`.
        This method is structured for easy integration.
        """
        # Placeholder — real implementation makes HTTP request
        # Response parsing would create CollectedAd objects
        logger.debug("youtube_search_params", params={k: v for k, v in params.items() if k != "key"})
        return []

    def parse_search_response(
        self, response_data: dict[str, Any]
    ) -> list[CollectedAd]:
        """Parse YouTube Data API v3 search response into CollectedAd objects."""
        ads: list[CollectedAd] = []
        items = response_data.get("items", [])

        for item in items:
            snippet = item.get("snippet", {})
            video_id = item.get("id", {}).get("videoId", "")
            if not video_id:
                continue

            ad = CollectedAd(
                platform="youtube",
                post_id=video_id,
                url=f"https://www.youtube.com/shorts/{video_id}",
                title=snippet.get("title", ""),
                description=snippet.get("description", ""),
                media_urls=[snippet.get("thumbnails", {}).get("high", {}).get("url", "")],
                media_type="video",
                author=snippet.get("channelTitle", ""),
                published_at=_parse_datetime(snippet.get("publishedAt")),
                raw_metadata={"channel_id": snippet.get("channelId", "")},
            )
            ads.append(ad)

        return ads


def _parse_datetime(dt_str: str | None) -> datetime | None:
    """Parse ISO datetime string from YouTube API."""
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
