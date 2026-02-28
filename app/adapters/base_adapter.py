"""Base Platform Adapter — Abstract interface for all platform integrations.

Every adapter MUST:
- Use SecretsManager for credentials (never hardcode).
- Implement rate limiting via RateLimiter.
- Implement circuit breaking via CircuitBreaker.
- Use signed, time-limited media URLs.
- Log every API call via AuditLogger.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import structlog

from app.policies.rate_limits import RateLimiter, CircuitBreaker
from app.services.audit_logger import AuditLogger
from app.services.secrets import SecretsManager

logger = structlog.get_logger(__name__)


class BasePlatformAdapter(ABC):
    """Abstract base for all platform adapters."""

    def __init__(
        self,
        platform_name: str,
        secrets_manager: SecretsManager,
        rate_limiter: RateLimiter,
        circuit_breaker: CircuitBreaker,
        audit_logger: AuditLogger,
    ) -> None:
        self._platform_name = platform_name
        self._secrets = secrets_manager
        self._rate_limiter = rate_limiter
        self._circuit_breaker = circuit_breaker
        self._audit = audit_logger

    @property
    def platform_name(self) -> str:
        return self._platform_name

    def publish(self, package: dict) -> dict:
        """Publish content to the platform with safety controls.

        This is the public entry point. Wraps _do_publish with guards.
        """
        # Check circuit breaker
        if not self._circuit_breaker.can_execute():
            logger.warning("circuit_breaker_open", platform=self._platform_name)
            raise RuntimeError(f"Circuit breaker open for {self._platform_name}")

        # Check rate limit
        if not self._rate_limiter.check_and_consume():
            logger.warning("rate_limited", platform=self._platform_name)
            raise RuntimeError(f"Rate limit exceeded for {self._platform_name}")

        try:
            result = self._do_publish(package)

            self._circuit_breaker.record_success()

            self._audit.log(
                agent_id=f"adapter_{self._platform_name}",
                action="publish_success",
                decision="PUBLISHED",
                reason=f"Content published to {self._platform_name}",
                output_data={"platform": self._platform_name},
            )

            return result

        except Exception as e:
            self._circuit_breaker.record_failure()

            self._audit.log(
                agent_id=f"adapter_{self._platform_name}",
                action="publish_error",
                decision="ERROR",
                reason=str(e),
            )
            raise

    @abstractmethod
    def _do_publish(self, package: dict) -> dict:
        """Platform-specific publish logic. Implemented by subclasses."""
        ...

    @abstractmethod
    def validate_content(self, package: dict) -> tuple[bool, str]:
        """Validate content against platform specs before publishing."""
        ...

    def _get_credentials(self) -> dict[str, str]:
        """Retrieve platform credentials from secrets manager."""
        return self._secrets.get_platform_credentials(self._platform_name)
