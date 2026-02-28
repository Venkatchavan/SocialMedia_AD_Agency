"""Scheduling queue + content calendar (U-26).

Redis-backed scheduling with best-time optimization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class ScheduleStatus(str, Enum):
    QUEUED = "queued"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledPost:
    """A post in the scheduling queue."""

    post_id: str
    content_id: str
    workspace_id: str
    platform: str
    scheduled_at: str
    status: ScheduleStatus = ScheduleStatus.QUEUED
    publish_result: dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    created_at: str = ""


# Best posting times by platform (hour in UTC, day_of_week 0=Mon)
BEST_TIMES: dict[str, list[dict[str, int]]] = {
    "instagram": [
        {"day": 1, "hour": 11},  # Tuesday 11am
        {"day": 2, "hour": 11},  # Wednesday 11am
        {"day": 4, "hour": 10},  # Friday 10am
    ],
    "tiktok": [
        {"day": 1, "hour": 9},
        {"day": 3, "hour": 12},
        {"day": 4, "hour": 17},
    ],
    "linkedin": [
        {"day": 1, "hour": 10},
        {"day": 2, "hour": 12},
        {"day": 3, "hour": 8},
    ],
    "x": [
        {"day": 0, "hour": 8},
        {"day": 2, "hour": 12},
        {"day": 4, "hour": 9},
    ],
    "pinterest": [
        {"day": 5, "hour": 20},
        {"day": 6, "hour": 14},
        {"day": 4, "hour": 15},
    ],
    "youtube": [
        {"day": 4, "hour": 15},
        {"day": 5, "hour": 11},
        {"day": 6, "hour": 10},
    ],
}


class PublishScheduler:
    """Manage the publishing schedule and queue."""

    def __init__(self) -> None:
        self._queue: dict[str, ScheduledPost] = {}

    def schedule(
        self,
        post_id: str,
        content_id: str,
        workspace_id: str,
        platform: str,
        scheduled_at: str,
    ) -> ScheduledPost:
        """Add a post to the schedule."""
        post = ScheduledPost(
            post_id=post_id,
            content_id=content_id,
            workspace_id=workspace_id,
            platform=platform,
            scheduled_at=scheduled_at,
            status=ScheduleStatus.SCHEDULED,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._queue[post_id] = post
        logger.info(
            "post_scheduled",
            post_id=post_id,
            platform=platform,
            scheduled_at=scheduled_at,
        )
        return post

    def cancel(self, post_id: str) -> bool:
        """Cancel a scheduled post."""
        post = self._queue.get(post_id)
        if post is None:
            return False
        if post.status in (ScheduleStatus.PUBLISHED, ScheduleStatus.PUBLISHING):
            return False
        post.status = ScheduleStatus.CANCELLED
        logger.info("post_cancelled", post_id=post_id)
        return True

    def mark_published(self, post_id: str, result: dict[str, Any] | None = None) -> bool:
        """Mark a post as successfully published."""
        post = self._queue.get(post_id)
        if post is None:
            return False
        post.status = ScheduleStatus.PUBLISHED
        post.publish_result = result or {}
        return True

    def mark_failed(self, post_id: str, error: str = "") -> bool:
        """Mark a post as failed, increment retry."""
        post = self._queue.get(post_id)
        if post is None:
            return False
        post.retry_count += 1
        if post.retry_count >= post.max_retries:
            post.status = ScheduleStatus.FAILED
        else:
            post.status = ScheduleStatus.QUEUED
        post.publish_result["last_error"] = error
        return True

    def get_due(self) -> list[ScheduledPost]:
        """Get posts that are due for publishing (scheduled_at <= now)."""
        now = datetime.now(timezone.utc).isoformat()
        return [
            p
            for p in self._queue.values()
            if p.status in (ScheduleStatus.SCHEDULED, ScheduleStatus.QUEUED)
            and p.scheduled_at <= now
        ]

    def get_calendar(self, workspace_id: str) -> list[ScheduledPost]:
        """Get all scheduled posts for a workspace (calendar view)."""
        return [
            p
            for p in self._queue.values()
            if p.workspace_id == workspace_id
        ]

    def get_best_time(self, platform: str) -> dict[str, int] | None:
        """Get the next best posting time for a platform."""
        times = BEST_TIMES.get(platform)
        if not times:
            return None
        return times[0]

    def count_by_status(self, workspace_id: str) -> dict[str, int]:
        """Count posts by status for a workspace."""
        counts: dict[str, int] = {}
        for post in self._queue.values():
            if post.workspace_id == workspace_id:
                counts[post.status.value] = counts.get(post.status.value, 0) + 1
        return counts
