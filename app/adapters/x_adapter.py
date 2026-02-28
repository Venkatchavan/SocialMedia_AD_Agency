"""X (Twitter) Platform Adapter — API v2 integration.

Uses X API v2 (official).
Never uses browser automation or scraping.
"""

from __future__ import annotations


import structlog

from app.adapters.base_adapter import BasePlatformAdapter
from app.policies.platform_policies import PLATFORM_SPECS

logger = structlog.get_logger(__name__)


class XAdapter(BasePlatformAdapter):
    """X (Twitter) API v2 adapter."""

    def _do_publish(self, package: dict) -> dict:
        """Publish content to X via API v2.

        TODO: Implement actual X API v2 calls.
        API flow:
          1. POST /2/tweets — create tweet
          2. For media: POST /1.1/media/upload — upload media first

        For MVP, returns a mock response.
        """
        caption = package.get("caption", "")
        media_url = package.get("media_url", "")

        self._get_credentials()

        logger.info(
            "x_publish_initiated",
            has_media=bool(media_url),
            caption_length=len(caption),
        )

        # MVP: Mock response
        return {
            "platform": "x",
            "post_id": "x_mock_id",
            "status": "published",
            "url": "https://x.com/user/status/mock_id",
        }

    def validate_content(self, package: dict) -> tuple[bool, str]:
        """Validate content against X specs."""
        specs = PLATFORM_SPECS["x"]
        caption = package.get("caption", "")

        max_caption = specs.get("max_caption_length", 280)
        if len(caption) > max_caption:
            return False, f"Caption exceeds X max ({max_caption} chars)"

        return True, "Valid"
