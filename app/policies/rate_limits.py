"""Rate limiting configuration per platform.

Security (from Agents_Security.md Rule 9):
- Anti-spam / anti-repetition enforcement
- Posting cadence and quotas enforced by platform adapter
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)


class RateLimitConfig:
    """Rate limit configuration for a single platform."""

    def __init__(
        self,
        platform: str,
        max_posts_per_day: int = 10,
        min_interval_seconds: int = 3600,
        max_retries: int = 3,
        backoff_strategy: str = "exponential",
        circuit_breaker_threshold: int = 3,
        circuit_breaker_cooldown_seconds: int = 900,
    ) -> None:
        self.platform = platform
        self.max_posts_per_day = max_posts_per_day
        self.min_interval_seconds = min_interval_seconds
        self.max_retries = max_retries
        self.backoff_strategy = backoff_strategy
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_cooldown_seconds = circuit_breaker_cooldown_seconds


# Default rate limit configs per platform
RATE_LIMITS: dict[str, RateLimitConfig] = {
    "tiktok": RateLimitConfig(
        platform="tiktok",
        max_posts_per_day=10,
        min_interval_seconds=3600,
        max_retries=5,
        backoff_strategy="exponential",
        circuit_breaker_threshold=3,
        circuit_breaker_cooldown_seconds=900,
    ),
    "instagram": RateLimitConfig(
        platform="instagram",
        max_posts_per_day=25,
        min_interval_seconds=1800,
        max_retries=3,
        backoff_strategy="linear",
        circuit_breaker_threshold=3,
        circuit_breaker_cooldown_seconds=1800,
    ),
    "x": RateLimitConfig(
        platform="x",
        max_posts_per_day=50,
        min_interval_seconds=600,
        max_retries=5,
        backoff_strategy="exponential",
        circuit_breaker_threshold=5,
        circuit_breaker_cooldown_seconds=900,
    ),
    "pinterest": RateLimitConfig(
        platform="pinterest",
        max_posts_per_day=50,
        min_interval_seconds=600,
        max_retries=3,
        backoff_strategy="linear",
        circuit_breaker_threshold=3,
        circuit_breaker_cooldown_seconds=1800,
    ),
}


class RateLimiter:
    """Enforce posting rate limits per platform."""

    def __init__(self, platform: str) -> None:
        self.config = RATE_LIMITS.get(platform, RateLimitConfig(platform=platform))
        self._post_timestamps: list[datetime] = []

    def can_post(self) -> tuple[bool, str]:
        """Check if posting is allowed right now."""
        now = datetime.now(tz=timezone.utc)

        # Check daily limit
        today_posts = [
            ts for ts in self._post_timestamps
            if ts.date() == now.date()
        ]
        if len(today_posts) >= self.config.max_posts_per_day:
            return False, f"Daily limit reached: {len(today_posts)}/{self.config.max_posts_per_day}"

        # Check minimum interval
        if self._post_timestamps:
            last_post = self._post_timestamps[-1]
            elapsed = (now - last_post).total_seconds()
            if elapsed < self.config.min_interval_seconds:
                wait = self.config.min_interval_seconds - int(elapsed)
                return False, f"Minimum interval not met. Wait {wait}s."

        return True, "OK"

    def record_post(self) -> None:
        """Record that a post was made."""
        self._post_timestamps.append(datetime.now(tz=timezone.utc))

    def check_and_consume(self) -> bool:
        """Check if posting is allowed and record the post if so.

        Combined convenience method used by adapters.
        Returns True if the post was allowed and recorded.
        """
        allowed, _reason = self.can_post()
        if allowed:
            self.record_post()
        return allowed

    def get_backoff_seconds(self, retry_count: int) -> int:
        """Calculate backoff time for a given retry attempt."""
        if self.config.backoff_strategy == "exponential":
            return min(2 ** retry_count, 300)  # Cap at 5 minutes
        else:  # linear
            return 60 * (retry_count + 1)


class CircuitBreaker:
    """Circuit breaker for platform API calls."""

    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 900) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._failure_count: int = 0
        self._last_failure_time: Optional[datetime] = None
        self._state: str = "closed"  # closed | open | half-open

    @property
    def is_open(self) -> bool:
        if self._state == "open":
            # Check if recovery timeout has passed
            if self._last_failure_time:
                elapsed = (
                    datetime.now(tz=timezone.utc) - self._last_failure_time
                ).total_seconds()
                if elapsed >= self.recovery_timeout:
                    self._state = "half-open"
                    return False
            return True
        return False

    def can_execute(self) -> bool:
        """Return True if the circuit breaker allows execution."""
        return not self.is_open

    def record_success(self) -> None:
        self._failure_count = 0
        self._state = "closed"

    def record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = datetime.now(tz=timezone.utc)
        if self._failure_count >= self.failure_threshold:
            self._state = "open"
            logger.warning(
                "circuit_breaker_opened",
                failure_count=self._failure_count,
                threshold=self.failure_threshold,
            )
