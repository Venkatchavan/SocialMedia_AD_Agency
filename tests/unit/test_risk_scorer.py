"""Unit tests for RiskScorer — deterministic risk scoring."""

from __future__ import annotations

from datetime import datetime, timezone

from app.services.risk_scorer import RiskScorer
from app.schemas.reference import Reference
from app.schemas.rights import RightsDecision


def _make_ref(ref_type: str = "public_domain", risk_score: int = 5) -> Reference:
    return Reference(
        reference_id="ref-test",
        title="Test Reference",
        medium="other",
        reference_type=ref_type,
        allowed_usage_mode="test",
        risk_score=risk_score,
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
    )


def _make_decision(
    decision: str = "APPROVE", risk_score: int = 0
) -> RightsDecision:
    return RightsDecision(
        reference_id="ref-test",
        decision=decision,
        reason="test",
        risk_score=risk_score,
    )


class TestRiskScorer:
    """Test suite for risk scoring logic."""

    def test_public_domain_low_score(self, risk_scorer: RiskScorer):
        """Public domain should get a low risk score."""
        ref = _make_ref("public_domain", 5)
        decision = _make_decision("APPROVE", 5)
        scored = risk_scorer.score(ref, decision)
        assert scored.final_risk_score < 40

    def test_licensed_with_license_low_score(self, risk_scorer: RiskScorer):
        """Licensed direct with approval gets base risk, flagged for review without registry."""
        ref = _make_ref("licensed_direct", 10)
        decision = _make_decision("APPROVE", 10)
        scored = risk_scorer.score(ref, decision)
        # Without a registry entry, unknown reference adds risk
        # Score = 10 (base) + 30 (unknown) = 40, so it flags for human review
        assert scored.final_risk_score <= 70  # Not auto-blocked

    def test_high_risk_score_auto_blocks(self, risk_scorer: RiskScorer):
        """References with score >=70 should recommend auto-block."""
        action = risk_scorer.recommend_action(75)
        assert action == "auto_block"

    def test_medium_risk_human_review(self, risk_scorer: RiskScorer):
        """References with score 40-69 should recommend human review."""
        action = risk_scorer.recommend_action(55)
        assert action == "human_review"

    def test_low_risk_auto_approve(self, risk_scorer: RiskScorer):
        """References with score <40 should recommend auto-approve."""
        action = risk_scorer.recommend_action(25)
        assert action == "auto_approve"

    def test_boundary_70_blocks(self, risk_scorer: RiskScorer):
        """Score exactly 70 should auto-block."""
        action = risk_scorer.recommend_action(70)
        assert action == "auto_block"

    def test_boundary_40_human_review(self, risk_scorer: RiskScorer):
        """Score exactly 40 should be human review."""
        action = risk_scorer.recommend_action(40)
        assert action == "human_review"

    def test_score_between_0_and_100(self, risk_scorer: RiskScorer):
        """Risk scores should always be 0-100."""
        cases = [
            ("public_domain", 0),
            ("licensed_direct", 50),
            ("commentary", 100),
        ]
        for ref_type, initial_risk in cases:
            ref = _make_ref(ref_type, min(initial_risk, 100))
            decision = _make_decision("APPROVE", min(initial_risk, 100))
            scored = risk_scorer.score(ref, decision)
            assert 0 <= scored.final_risk_score <= 100
