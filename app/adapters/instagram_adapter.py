"""Instagram Platform Adapter — Graph API integration.

Uses Instagram Graph API (official, via Meta Business SDK).
Never uses browser automation or scraping.
"""

from __future__ import annotations

from typing import Any

import structlog

from app.adapters.base_adapter import BasePlatformAdapter
from app.policies.platform_policies import PLATFORM_SPECS

logger = structlog.get_logger(__name__)


class InstagramAdapter(BasePlatformAdapter):
    """Instagram Graph API adapter."""

    def _do_publish(self, package: dict) -> dict:
        """Publish content to Instagram via Graph API.

        TODO: Implement actual Instagram Graph API calls.
        API flow for Reels:
          1. POST /{ig-user-id}/media — create media container
          2. POST /{ig-user-id}/media_publish — publish container

        For MVP, returns a mock response.
        """
        caption = package.get("caption", "")
        media_url = package.get("media_url", "")
        content_type = package.get("content_type", "reel")  # reel, image, carousel

        credentials = self._get_credentials()

        logger.info(
            "instagram_publish_initiated",
            content_type=content_type,
            has_media=bool(media_url),
            caption_length=len(caption),
        )

        # MVP: Mock response
        return {
            "platform": "instagram",
            "post_id": "ig_mock_id",
            "status": "published",
            "url": "https://www.instagram.com/p/mock_id/",
            "content_type": content_type,
        }

    def validate_content(self, package: dict) -> tuple[bool, str]:
        """Validate content against Instagram specs."""
        specs = PLATFORM_SPECS["instagram"]
        caption = package.get("caption", "")

        max_caption = specs.get("max_caption_length", 2200)
        if len(caption) > max_caption:
            return False, f"Caption exceeds Instagram max ({max_caption} chars)"

        return True, "Valid"
