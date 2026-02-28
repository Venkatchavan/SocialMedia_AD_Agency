"""TikTok Platform Adapter — Content Posting API integration.

Uses TikTok Content Posting API (official).
Never uses browser automation or scraping.
"""

from __future__ import annotations


import structlog

from app.adapters.base_adapter import BasePlatformAdapter
from app.policies.platform_policies import PLATFORM_SPECS

logger = structlog.get_logger(__name__)


class TikTokAdapter(BasePlatformAdapter):
    """TikTok Content Posting API adapter."""

    def _do_publish(self, package: dict) -> dict:
        """Publish content to TikTok.

        TODO: Implement actual TikTok Content Posting API calls.
        API flow:
          1. POST /v2/post/publish/video/init/ — initialize upload
          2. PUT upload_url — upload video file
          3. POST /v2/post/publish/status/fetch/ — check status

        For MVP, returns a mock response.
        """
        caption = package.get("caption", "")
        media_url = package.get("media_url", "")

        self._get_credentials()
        # credentials contains: TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET, TIKTOK_ACCESS_TOKEN

        logger.info(
            "tiktok_publish_initiated",
            has_media=bool(media_url),
            caption_length=len(caption),
        )

        # MVP: Mock response
        return {
            "platform": "tiktok",
            "post_id": "tiktok_mock_id",
            "status": "published",
            "url": "https://www.tiktok.com/@user/video/mock_id",
        }

    def validate_content(self, package: dict) -> tuple[bool, str]:
        """Validate content against TikTok specs."""
        specs = PLATFORM_SPECS["tiktok"]
        caption = package.get("caption", "")

        # Caption length check
        max_caption = specs.get("max_caption_length", 2200)
        if len(caption) > max_caption:
            return False, f"Caption exceeds TikTok max ({max_caption} chars)"

        # TODO: Video format/duration/resolution checks

        return True, "Valid"
