"""Stripe client wrapper — handles checkout, subscriptions, webhooks.

All Stripe SDK interactions are isolated here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import structlog

from app.billing import PlanTier, PLANS
from app.config import get_settings

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class CheckoutSession:
    """Result of creating a Stripe Checkout session."""

    session_id: str
    url: str
    workspace_id: str
    plan_tier: PlanTier


@dataclass(frozen=True)
class WebhookEvent:
    """Parsed Stripe webhook event."""

    event_type: str
    customer_id: str
    subscription_id: str = ""
    plan_tier: PlanTier | None = None
    raw: dict = None  # type: ignore[assignment]


class StripeClient:
    """Wrapper around Stripe API for billing operations.

    NOTE: Actual Stripe calls require `stripe` PyPI package.
    This class is structured for integration — methods document
    the exact Stripe API calls needed.
    """

    def __init__(self, secret_key: str = "") -> None:
        settings = get_settings()
        self._secret_key = secret_key or getattr(settings, "stripe_secret_key", "")

    def is_configured(self) -> bool:
        """Check if Stripe API key is available."""
        return bool(self._secret_key)

    def create_checkout_session(
        self,
        workspace_id: str,
        plan_tier: PlanTier,
        success_url: str = "",
        cancel_url: str = "",
    ) -> CheckoutSession:
        """Create a Stripe Checkout session for subscription.

        Stripe API: POST /v1/checkout/sessions
        mode: subscription
        line_items: [{ price: PRICE_ID, quantity: 1 }]
        """
        plan = PLANS[plan_tier]
        logger.info(
            "stripe_checkout_create",
            workspace_id=workspace_id,
            tier=plan_tier.value,
            price_cents=plan.price_monthly_cents,
        )

        # In production: stripe.checkout.Session.create(...)
        return CheckoutSession(
            session_id=f"cs_mock_{workspace_id}_{plan_tier.value}",
            url=success_url or "https://checkout.stripe.com/mock",
            workspace_id=workspace_id,
            plan_tier=plan_tier,
        )

    def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel a Stripe subscription.

        Stripe API: DELETE /v1/subscriptions/{id}
        """
        logger.info("stripe_cancel", subscription_id=subscription_id)
        return True

    def parse_webhook(self, payload: str, signature: str) -> WebhookEvent | None:
        """Parse and verify a Stripe webhook event.

        Stripe API: stripe.Webhook.construct_event(payload, sig, secret)
        """
        # In production: uses webhook secret for signature verification
        logger.info("stripe_webhook_received")
        return None

    def get_subscription_status(self, subscription_id: str) -> str:
        """Get current subscription status.

        Stripe API: GET /v1/subscriptions/{id}
        Returns: active | past_due | canceled | incomplete
        """
        return "active"
