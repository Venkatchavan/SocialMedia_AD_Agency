"""Stripe billing integration — subscription plans, usage metering, quotas.

Tiers: Starter ($149/mo), Pro ($499/mo), Enterprise ($1,499/mo).
All Stripe API calls go through this module. No direct Stripe SDK elsewhere.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class PlanTier(str, Enum):
    """Subscription plan tiers."""

    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass(frozen=True)
class PlanConfig:
    """Configuration and limits for a subscription plan."""

    tier: PlanTier
    price_monthly_cents: int
    runs_per_month: int
    posts_per_month: int
    platforms: list[str]
    video_enabled: bool = False
    white_label: bool = False


# Plan definitions
PLANS: dict[PlanTier, PlanConfig] = {
    PlanTier.STARTER: PlanConfig(
        tier=PlanTier.STARTER,
        price_monthly_cents=14900,
        runs_per_month=20,
        posts_per_month=10,
        platforms=["instagram", "tiktok"],
    ),
    PlanTier.PRO: PlanConfig(
        tier=PlanTier.PRO,
        price_monthly_cents=49900,
        runs_per_month=100,
        posts_per_month=50,
        platforms=["instagram", "tiktok", "x", "pinterest", "linkedin", "youtube"],
    ),
    PlanTier.ENTERPRISE: PlanConfig(
        tier=PlanTier.ENTERPRISE,
        price_monthly_cents=149900,
        runs_per_month=999_999,  # effectively unlimited
        posts_per_month=999_999,
        platforms=["instagram", "tiktok", "x", "pinterest", "linkedin", "youtube"],
        video_enabled=True,
        white_label=True,
    ),
}


@dataclass
class UsageCounter:
    """Tracks usage for a workspace within a billing cycle."""

    workspace_id: str
    cycle_start: datetime = field(default_factory=datetime.utcnow)
    runs_used: int = 0
    posts_used: int = 0
    llm_tokens_used: int = 0

    def reset(self) -> None:
        """Reset counters for new billing cycle."""
        self.runs_used = 0
        self.posts_used = 0
        self.llm_tokens_used = 0
        self.cycle_start = datetime.utcnow()
