"""LinkedIn collector — uses Marketing API v2 to collect ad creatives.

Fetches competitor ad data via /adAnalytics and /creatives endpoints.
Uses official API only — no scraping.
"""

from __future__ import annotations

from typing import Any

import structlog

from app.collectors.base_collector import BaseCollector, CollectedAd
from app.config import get_settings

logger = structlog.get_logger(__name__)


class LinkedInCollector(BaseCollector):
    """Collect ads from LinkedIn Marketing API v2."""

    platform_name = "linkedin"

    def __init__(
        self,
        client_id: str = "",
        client_secret: str = "",
        access_token: str = "",
    ) -> None:
        settings = get_settings()
        self._client_id = client_id or getattr(settings, "linkedin_client_id", "")
        self._client_secret = client_secret or getattr(settings, "linkedin_client_secret", "")
        self._access_token = access_token or getattr(settings, "linkedin_access_token", "")

    def validate_credentials(self) -> bool:
        """Check if LinkedIn API credentials are configured."""
        return bool(self._access_token)

    def collect(
        self,
        query: str,
        workspace_id: str,
        max_results: int = 25,
        **kwargs: Any,
    ) -> list[CollectedAd]:
        """Collect ads from LinkedIn Marketing API.

        Uses /adAnalytics endpoint with search filters.
        """
        if not self.validate_credentials():
            logger.warning("linkedin_missing_credentials", workspace_id=workspace_id)
            return []

        logger.info(
            "linkedin_collect_start",
            query=query,
            workspace_id=workspace_id,
            max_results=max_results,
        )

        params = self._build_request_params(query, max_results, **kwargs)
        results = self._execute_request(params, workspace_id)

        logger.info(
            "linkedin_collect_complete",
            workspace_id=workspace_id,
            results_count=len(results),
        )
        return results

    def _build_request_params(
        self, query: str, max_results: int, **kwargs: Any
    ) -> dict[str, Any]:
        """Build LinkedIn Marketing API request parameters."""
        return {
            "q": "search",
            "search": {"query": query},
            "count": min(max_results, 100),
            "start": kwargs.get("offset", 0),
            "projection": "(elements*(creative,analytics))",
        }

    def _execute_request(
        self, params: dict[str, Any], workspace_id: str
    ) -> list[CollectedAd]:
        """Execute LinkedIn API request.

        NOTE: Actual HTTP call requires `httpx` with OAuth2 bearer token.
        This method is structured for easy integration.
        """
        logger.debug("linkedin_request_params", params=params)
        return []

    def parse_creatives_response(
        self, response_data: dict[str, Any]
    ) -> list[CollectedAd]:
        """Parse LinkedIn Marketing API creatives response."""
        ads: list[CollectedAd] = []
        elements = response_data.get("elements", [])

        for elem in elements:
            creative = elem.get("creative", {})
            analytics = elem.get("analytics", {})
            creative_id = creative.get("id", "")
            if not creative_id:
                continue

            content = creative.get("content", {})
            text_content = content.get("textAd", {})

            ad = CollectedAd(
                platform="linkedin",
                post_id=str(creative_id),
                url=creative.get("landingPage", ""),
                title=text_content.get("headline", ""),
                description=text_content.get("body", ""),
                media_urls=_extract_media_urls(content),
                media_type=_detect_media_type(content),
                engagement={
                    "impressions": analytics.get("impressions", 0),
                    "clicks": analytics.get("clicks", 0),
                    "reactions": analytics.get("reactions", 0),
                    "shares": analytics.get("shares", 0),
                    "comments": analytics.get("comments", 0),
                },
                raw_metadata={
                    "campaign_id": creative.get("campaign", ""),
                    "status": creative.get("status", ""),
                },
            )
            ads.append(ad)

        return ads


def _extract_media_urls(content: dict[str, Any]) -> list[str]:
    """Extract media URLs from LinkedIn creative content."""
    urls: list[str] = []
    media = content.get("media", {})
    if isinstance(media, dict) and media.get("url"):
        urls.append(media["url"])
    image = content.get("image", {})
    if isinstance(image, dict) and image.get("url"):
        urls.append(image["url"])
    return urls


def _detect_media_type(content: dict[str, Any]) -> str:
    """Detect media type from LinkedIn creative content."""
    if "video" in content:
        return "video"
    if "image" in content or "media" in content:
        return "image"
    return "text"
