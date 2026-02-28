"""Performance metrics pull (U-28).

Pull post-publish metrics at 6h/24h/72h intervals per platform.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timezone
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class MetricInterval(str, Enum):
    HOUR_6 = "6h"
    HOUR_24 = "24h"
    HOUR_72 = "72h"


@dataclass
class PostMetrics:
    """Metrics pulled for a single published post."""

    post_id: str
    platform: str
    interval: str
    pulled_at: str = ""
    impressions: int = 0
    reach: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    clicks: int = 0
    video_views: int = 0
    watch_time_seconds: float = 0.0
    completion_rate: float = 0.0
    ctr: float = 0.0
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def engagement_rate(self) -> float:
        """Total engagements / impressions."""
        total = self.likes + self.comments + self.shares + self.saves
        if self.impressions == 0:
            return 0.0
        return round(total / self.impressions, 4)


# Platform-specific metric keys
PLATFORM_METRICS: dict[str, list[str]] = {
    "instagram": [
        "reach", "impressions", "likes", "comments", "saves", "shares", "profile_visits",
    ],
    "tiktok": [
        "video_views", "likes", "comments", "shares", "watch_time_seconds", "completion_rate",
    ],
    "linkedin": [
        "impressions", "clicks", "likes", "comments", "shares", "ctr",
    ],
    "pinterest": [
        "impressions", "saves", "clicks",
    ],
    "x": [
        "impressions", "likes", "shares", "comments", "clicks",
    ],
    "youtube": [
        "video_views", "likes", "comments", "watch_time_seconds", "ctr",
    ],
}


class MetricsPuller:
    """Pull post-publish metrics from platform APIs.

    NOTE: Production connects to real platform APIs.
    This implementation stores/retrieves metrics in-memory.
    """

    def __init__(self) -> None:
        self._metrics: dict[str, list[PostMetrics]] = {}

    def record_metrics(self, metrics: PostMetrics) -> None:
        """Record metrics for a post (or from an API pull)."""
        metrics.pulled_at = datetime.now(UTC).isoformat()
        key = metrics.post_id
        if key not in self._metrics:
            self._metrics[key] = []
        self._metrics[key].append(metrics)

        logger.info(
            "metrics_recorded",
            post_id=metrics.post_id,
            platform=metrics.platform,
            interval=metrics.interval,
            engagement_rate=metrics.engagement_rate,
        )

    def get_metrics(
        self, post_id: str, interval: str | None = None
    ) -> list[PostMetrics]:
        """Get metrics for a post, optionally filtered by interval."""
        all_metrics = self._metrics.get(post_id, [])
        if interval is None:
            return all_metrics
        return [m for m in all_metrics if m.interval == interval]

    def get_latest(self, post_id: str) -> PostMetrics | None:
        """Get the most recent metrics for a post."""
        all_metrics = self._metrics.get(post_id, [])
        if not all_metrics:
            return None
        return all_metrics[-1]

    def get_platform_metrics_keys(self, platform: str) -> list[str]:
        """Get the metric keys available for a platform."""
        return PLATFORM_METRICS.get(platform, [])

    def get_top_posts(
        self, platform: str | None = None, limit: int = 10
    ) -> list[PostMetrics]:
        """Get top-performing posts by engagement rate."""
        all_latest: list[PostMetrics] = []
        for post_id in self._metrics:
            latest = self.get_latest(post_id)
            if latest is not None:
                if platform is None or latest.platform == platform:
                    all_latest.append(latest)

        all_latest.sort(key=lambda m: m.engagement_rate, reverse=True)
        return all_latest[:limit]

    def get_average_engagement(self, platform: str) -> float:
        """Get average engagement rate across all posts for a platform."""
        rates: list[float] = []
        for post_id in self._metrics:
            latest = self.get_latest(post_id)
            if latest is not None and latest.platform == platform:
                rates.append(latest.engagement_rate)
        if not rates:
            return 0.0
        return round(sum(rates) / len(rates), 4)
