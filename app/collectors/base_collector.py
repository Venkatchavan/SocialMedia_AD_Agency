"""Base collector ABC — shared interface for all platform ad collectors.

Every collector follows the same pattern:
    collector.collect(query, workspace_id) → list[CollectedAd]
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class CollectedAd:
    """A single ad/post collected from a platform."""

    platform: str
    post_id: str
    url: str = ""
    title: str = ""
    description: str = ""
    media_urls: list[str] = field(default_factory=list)
    media_type: str = "video"  # video | image | carousel | text
    engagement: dict[str, int] = field(default_factory=dict)
    hashtags: list[str] = field(default_factory=list)
    author: str = ""
    published_at: datetime | None = None
    collected_at: datetime = field(default_factory=datetime.utcnow)
    raw_metadata: dict[str, Any] = field(default_factory=dict)


class BaseCollector(ABC):
    """Abstract base for all platform ad collectors."""

    platform_name: str = "base"

    @abstractmethod
    def collect(
        self,
        query: str,
        workspace_id: str,
        max_results: int = 25,
        **kwargs: Any,
    ) -> list[CollectedAd]:
        """Collect ads matching the query.

        Args:
            query: Search query (keywords, brand name, etc.).
            workspace_id: Workspace isolation key.
            max_results: Max ads to return.

        Returns:
            List of CollectedAd objects.
        """
        ...

    @abstractmethod
    def validate_credentials(self) -> bool:
        """Check if platform API credentials are configured and valid."""
        ...
