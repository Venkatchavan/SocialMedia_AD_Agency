"""Quota enforcement — checks workspace usage against plan limits.

Called before every pipeline run and publish action.
"""

from __future__ import annotations

from dataclasses import dataclass

import structlog

from app.billing import PLANS, PlanConfig, PlanTier, UsageCounter

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class QuotaCheckResult:
    """Result of a quota check."""

    allowed: bool
    resource: str  # "runs" | "posts" | "platform"
    used: int = 0
    limit: int = 0
    reason: str = ""


class QuotaEnforcer:
    """Enforce usage quotas per workspace per billing cycle.

    Thread-safe in single-process; for multi-process, back with Redis.
    """

    def __init__(self) -> None:
        self._counters: dict[str, UsageCounter] = {}
        self._workspace_plans: dict[str, PlanTier] = {}

    def set_plan(self, workspace_id: str, tier: PlanTier) -> None:
        """Assign a plan tier to a workspace."""
        self._workspace_plans[workspace_id] = tier
        if workspace_id not in self._counters:
            self._counters[workspace_id] = UsageCounter(workspace_id=workspace_id)

    def get_plan(self, workspace_id: str) -> PlanConfig:
        """Get the plan config for a workspace."""
        tier = self._workspace_plans.get(workspace_id, PlanTier.STARTER)
        return PLANS[tier]

    def get_usage(self, workspace_id: str) -> UsageCounter:
        """Get current usage for a workspace."""
        if workspace_id not in self._counters:
            self._counters[workspace_id] = UsageCounter(workspace_id=workspace_id)
        return self._counters[workspace_id]

    def check_run_quota(self, workspace_id: str) -> QuotaCheckResult:
        """Check if workspace can start a new pipeline run."""
        plan = self.get_plan(workspace_id)
        usage = self.get_usage(workspace_id)

        if usage.runs_used >= plan.runs_per_month:
            logger.warning(
                "quota_exceeded",
                workspace_id=workspace_id,
                resource="runs",
                used=usage.runs_used,
                limit=plan.runs_per_month,
            )
            return QuotaCheckResult(
                allowed=False,
                resource="runs",
                used=usage.runs_used,
                limit=plan.runs_per_month,
                reason=f"Run quota exceeded: {usage.runs_used}/{plan.runs_per_month}",
            )
        return QuotaCheckResult(
            allowed=True,
            resource="runs",
            used=usage.runs_used,
            limit=plan.runs_per_month,
        )

    def check_post_quota(self, workspace_id: str) -> QuotaCheckResult:
        """Check if workspace can publish another post."""
        plan = self.get_plan(workspace_id)
        usage = self.get_usage(workspace_id)

        if usage.posts_used >= plan.posts_per_month:
            return QuotaCheckResult(
                allowed=False,
                resource="posts",
                used=usage.posts_used,
                limit=plan.posts_per_month,
                reason=f"Post quota exceeded: {usage.posts_used}/{plan.posts_per_month}",
            )
        return QuotaCheckResult(
            allowed=True,
            resource="posts",
            used=usage.posts_used,
            limit=plan.posts_per_month,
        )

    def check_platform_access(
        self, workspace_id: str, platform: str
    ) -> QuotaCheckResult:
        """Check if workspace plan includes access to a platform."""
        plan = self.get_plan(workspace_id)

        if platform.lower() not in plan.platforms:
            return QuotaCheckResult(
                allowed=False,
                resource="platform",
                reason=f"Platform '{platform}' not included in {plan.tier.value} plan",
            )
        return QuotaCheckResult(allowed=True, resource="platform")

    def record_run(self, workspace_id: str) -> None:
        """Record a pipeline run against the workspace quota."""
        usage = self.get_usage(workspace_id)
        usage.runs_used += 1

    def record_post(self, workspace_id: str) -> None:
        """Record a published post against the workspace quota."""
        usage = self.get_usage(workspace_id)
        usage.posts_used += 1

    def record_tokens(self, workspace_id: str, tokens: int) -> None:
        """Record LLM token usage."""
        usage = self.get_usage(workspace_id)
        usage.llm_tokens_used += tokens

    def reset_cycle(self, workspace_id: str) -> None:
        """Reset usage counters for a new billing cycle."""
        usage = self.get_usage(workspace_id)
        usage.reset()
