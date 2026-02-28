"""Tests for Stripe billing + usage quotas (U-15)."""

from __future__ import annotations

import pytest

from app.billing import PLANS, PlanTier, UsageCounter
from app.billing.quota_enforcer import QuotaEnforcer
from app.billing.stripe_client import CheckoutSession, StripeClient

# ── Plan definitions ─────────────────────────────────────────────────

class TestPlans:
    def test_three_tiers(self):
        assert len(PLANS) == 3
        assert PlanTier.STARTER in PLANS
        assert PlanTier.PRO in PLANS
        assert PlanTier.ENTERPRISE in PLANS

    def test_starter_pricing(self):
        p = PLANS[PlanTier.STARTER]
        assert p.price_monthly_cents == 14900  # $149
        assert p.runs_per_month == 20
        assert p.posts_per_month == 10
        assert len(p.platforms) == 2

    def test_pro_pricing(self):
        p = PLANS[PlanTier.PRO]
        assert p.price_monthly_cents == 49900  # $499
        assert p.runs_per_month == 100

    def test_enterprise_unlimited(self):
        p = PLANS[PlanTier.ENTERPRISE]
        assert p.price_monthly_cents == 149900  # $1499
        assert p.runs_per_month > 100000
        assert p.video_enabled
        assert p.white_label

    def test_plan_config_frozen(self):
        p = PLANS[PlanTier.STARTER]
        with pytest.raises(AttributeError):
            p.runs_per_month = 999  # type: ignore[misc]


# ── UsageCounter ─────────────────────────────────────────────────────

class TestUsageCounter:
    def test_default_zero(self):
        u = UsageCounter(workspace_id="ws1")
        assert u.runs_used == 0
        assert u.posts_used == 0
        assert u.llm_tokens_used == 0

    def test_reset(self):
        u = UsageCounter(workspace_id="ws1")
        u.runs_used = 15
        u.posts_used = 8
        u.reset()
        assert u.runs_used == 0
        assert u.posts_used == 0


# ── QuotaEnforcer ────────────────────────────────────────────────────

class TestQuotaEnforcer:
    def test_default_plan_is_starter(self):
        qe = QuotaEnforcer()
        plan = qe.get_plan("ws_new")
        assert plan.tier == PlanTier.STARTER

    def test_set_plan(self):
        qe = QuotaEnforcer()
        qe.set_plan("ws1", PlanTier.PRO)
        assert qe.get_plan("ws1").tier == PlanTier.PRO

    def test_run_quota_allowed(self):
        qe = QuotaEnforcer()
        qe.set_plan("ws1", PlanTier.STARTER)
        result = qe.check_run_quota("ws1")
        assert result.allowed
        assert result.resource == "runs"

    def test_run_quota_exceeded(self):
        qe = QuotaEnforcer()
        qe.set_plan("ws1", PlanTier.STARTER)
        for _ in range(20):
            qe.record_run("ws1")
        result = qe.check_run_quota("ws1")
        assert not result.allowed
        assert "exceeded" in result.reason

    def test_post_quota_allowed(self):
        qe = QuotaEnforcer()
        qe.set_plan("ws1", PlanTier.STARTER)
        result = qe.check_post_quota("ws1")
        assert result.allowed

    def test_post_quota_exceeded(self):
        qe = QuotaEnforcer()
        qe.set_plan("ws1", PlanTier.STARTER)
        for _ in range(10):
            qe.record_post("ws1")
        result = qe.check_post_quota("ws1")
        assert not result.allowed

    def test_platform_access_allowed(self):
        qe = QuotaEnforcer()
        qe.set_plan("ws1", PlanTier.PRO)
        result = qe.check_platform_access("ws1", "linkedin")
        assert result.allowed

    def test_platform_access_denied(self):
        qe = QuotaEnforcer()
        qe.set_plan("ws1", PlanTier.STARTER)
        result = qe.check_platform_access("ws1", "linkedin")
        assert not result.allowed
        assert "not included" in result.reason

    def test_record_tokens(self):
        qe = QuotaEnforcer()
        qe.set_plan("ws1", PlanTier.STARTER)
        qe.record_tokens("ws1", 5000)
        assert qe.get_usage("ws1").llm_tokens_used == 5000

    def test_reset_cycle(self):
        qe = QuotaEnforcer()
        qe.set_plan("ws1", PlanTier.STARTER)
        qe.record_run("ws1")
        qe.record_post("ws1")
        qe.reset_cycle("ws1")
        usage = qe.get_usage("ws1")
        assert usage.runs_used == 0
        assert usage.posts_used == 0


# ── StripeClient ─────────────────────────────────────────────────────

class TestStripeClient:
    def test_not_configured_without_key(self):
        client = StripeClient(secret_key="")
        assert not client.is_configured()

    def test_configured_with_key(self):
        client = StripeClient(secret_key="sk_test_123")
        assert client.is_configured()

    def test_create_checkout_session(self):
        client = StripeClient(secret_key="sk_test")
        session = client.create_checkout_session("ws1", PlanTier.PRO)
        assert isinstance(session, CheckoutSession)
        assert session.workspace_id == "ws1"
        assert session.plan_tier == PlanTier.PRO
        assert "mock" in session.session_id

    def test_cancel_subscription(self):
        client = StripeClient(secret_key="sk_test")
        assert client.cancel_subscription("sub_123") is True

    def test_get_subscription_status(self):
        client = StripeClient(secret_key="sk_test")
        assert client.get_subscription_status("sub_123") == "active"

    def test_parse_webhook_returns_none(self):
        client = StripeClient(secret_key="sk_test")
        result = client.parse_webhook("{}", "sig")
        assert result is None
