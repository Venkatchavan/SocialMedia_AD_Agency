"""Pinterest Platform Adapter — API v5 integration.

Uses Pinterest API v5 (official).
Never uses browser automation or scraping.
"""

from __future__ import annotations

from typing import Any

import structlog

from app.adapters.base_adapter import BasePlatformAdapter
from app.policies.platform_policies import PLATFORM_SPECS

logger = structlog.get_logger(__name__)


class PinterestAdapter(BasePlatformAdapter):
    """Pinterest API v5 adapter."""

    def _do_publish(self, package: dict) -> dict:
        """Publish content to Pinterest via API v5.

        TODO: Implement actual Pinterest API v5 calls.
        API flow:
          1. POST /v5/pins — create pin

        For MVP, returns a mock response.
        """
        caption = package.get("caption", "")
        media_url = package.get("media_url", "")

        credentials = self._get_credentials()

        logger.info(
            "pinterest_publish_initiated",
            has_media=bool(media_url),
            caption_length=len(caption),
        )

        # MVP: Mock response
        return {
            "platform": "pinterest",
            "post_id": "pin_mock_id",
            "status": "published",
            "url": "https://www.pinterest.com/pin/mock_id/",
        }

    def validate_content(self, package: dict) -> tuple[bool, str]:
        """Validate content against Pinterest specs."""
        specs = PLATFORM_SPECS["pinterest"]
        caption = package.get("caption", "")

        max_caption = specs.get("max_caption_length", 500)
        if len(caption) > max_caption:
            return False, f"Caption exceeds Pinterest max ({max_caption} chars)"

        return True, "Valid"
