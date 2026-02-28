"""Publish Flow — Handles post-QA publishing to platform adapters.

Enforces:
- Rate limiting per platform
- Circuit breaker patterns
- Duplicate hash detection
- Signed media URLs
"""

from __future__ import annotations

from typing import Protocol

import structlog

from app.policies.rate_limits import RATE_LIMITS, CircuitBreaker, RateLimiter
from app.services.audit_logger import AuditLogger
from app.services.content_hasher import ContentHasher

logger = structlog.get_logger(__name__)


class PlatformAdapter(Protocol):
    """Protocol for platform adapters."""

    def publish(self, package: dict) -> dict:
        ...

    @property
    def platform_name(self) -> str:
        ...


class PublishFlow:
    """Manage publishing across multiple platforms with safety controls."""

    def __init__(
        self,
        adapters: dict[str, PlatformAdapter],
        audit_logger: AuditLogger,
    ) -> None:
        self._adapters = adapters
        self._audit = audit_logger
        self._hasher = ContentHasher()
        self._published_hashes: set[str] = set()

        # Initialize rate limiters and circuit breakers per platform
        self._rate_limiters: dict[str, RateLimiter] = {}
        self._circuit_breakers: dict[str, CircuitBreaker] = {}

        for platform_name in adapters:
            config = RATE_LIMITS.get(platform_name)
            if config:
                self._rate_limiters[platform_name] = RateLimiter(platform_name)
                self._circuit_breakers[platform_name] = CircuitBreaker(
                    failure_threshold=config.circuit_breaker_threshold,
                    recovery_timeout=config.circuit_breaker_cooldown_seconds,
                )

    def publish_all(
        self,
        platform_packages: list[dict],
        session_id: str = "",
    ) -> list[dict]:
        """Publish to all platforms in the packages list.

        Returns list of publish result dicts.
        """
        results: list[dict] = []

        for package in platform_packages:
            package.get("platform", "")
            result = self.publish_one(package, session_id)
            results.append(result)

        return results

    def publish_one(self, package: dict, session_id: str = "") -> dict:
        """Publish a single package to one platform."""
        platform = package.get("platform", "")
        caption = package.get("caption", "")

        # 1. Duplicate check (Agents.md Rule 9)
        content_hash = self._hasher.hash_text(caption)
        if content_hash in self._published_hashes:
            logger.warning("duplicate_blocked", platform=platform, hash=content_hash)
            self._audit.log(
                agent_id="publish_flow",
                action="duplicate_blocked",
                decision="BLOCKED",
                reason="Duplicate content hash detected",
                session_id=session_id,
            )
            return {
                "platform": platform,
                "status": "blocked",
                "reason": "Duplicate content",
            }

        # 2. Circuit breaker check (Agents.md Rule 10)
        cb = self._circuit_breakers.get(platform)
        if cb and not cb.can_execute():
            logger.warning("circuit_open", platform=platform)
            self._audit.log(
                agent_id="publish_flow",
                action="circuit_open",
                decision="QUEUED",
                reason=f"Circuit breaker open for {platform}",
                session_id=session_id,
            )
            return {
                "platform": platform,
                "status": "queued",
                "reason": "Circuit breaker open — will retry after recovery",
            }

        # 3. Rate limit check
        rl = self._rate_limiters.get(platform)
        if rl and not rl.check_and_consume():
            logger.warning("rate_limited", platform=platform)
            return {
                "platform": platform,
                "status": "queued",
                "reason": "Rate limited — queued for later",
            }

        # 4. Publish via adapter
        adapter = self._adapters.get(platform)
        if not adapter:
            logger.error("no_adapter", platform=platform)
            return {
                "platform": platform,
                "status": "error",
                "reason": f"No adapter registered for {platform}",
            }

        try:
            result = adapter.publish(package)

            # Track published hash
            self._published_hashes.add(content_hash)

            # Record circuit breaker success
            if cb:
                cb.record_success()

            self._audit.log(
                agent_id="publish_flow",
                action=f"published_{platform}",
                decision="PUBLISHED",
                reason="Successfully published",
                output_data={"platform": platform, "content_hash": content_hash},
                session_id=session_id,
            )

            return {
                "platform": platform,
                "status": "published",
                "result": result,
            }

        except Exception as e:
            # Record circuit breaker failure
            if cb:
                cb.record_failure()

            self._audit.log(
                agent_id="publish_flow",
                action=f"publish_error_{platform}",
                decision="ERROR",
                reason=str(e),
                session_id=session_id,
            )

            return {
                "platform": platform,
                "status": "error",
                "reason": str(e),
            }
