"""Deterministic risk scoring engine.

Security rules enforced (from Agents.md):
- risk_score >= 70: auto-block (REJECT)
- risk_score 40-69: flag for human review
- risk_score < 40: proceed automatically
- On uncertainty: treat as risk_score = 80 (block)
"""

from __future__ import annotations

from typing import Optional

import structlog

from app.schemas.reference import Reference, ScoredReference
from app.schemas.rights import RightsDecision, RightsRecord
from app.config import get_settings

logger = structlog.get_logger(__name__)


class RiskScorer:
    """Deterministic risk scoring. Reproducible and auditable."""

    def __init__(
        self,
        auto_block_threshold: int = 70,
        review_threshold: int = 40,
        registry: Optional[dict[str, RightsRecord]] = None,
    ) -> None:
        settings = get_settings()
        self.auto_block_threshold = auto_block_threshold or settings.risk_score_auto_block
        self.review_threshold = review_threshold or settings.risk_score_review_threshold
        self._registry = registry or {}

    def score(
        self, reference: Reference, rights_decision: RightsDecision
    ) -> ScoredReference:
        """Score a reference and determine if it should be blocked, reviewed, or approved."""

        # If already rejected by rights engine, score = 100
        if rights_decision.is_rejected():
            return ScoredReference(
                reference=reference,
                final_risk_score=100,
                auto_blocked=True,
                human_review_required=False,
                compliance_status="REJECT",
                compliance_reason=rights_decision.reason,
            )

        # Calculate risk score
        risk_score = self._calculate_score(reference, rights_decision)

        # Apply thresholds
        auto_blocked = risk_score >= self.auto_block_threshold
        human_review = (
            self.review_threshold <= risk_score < self.auto_block_threshold
        )

        if auto_blocked:
            status = "REJECT"
            reason = f"Auto-blocked: risk score {risk_score} >= {self.auto_block_threshold}"
        elif human_review:
            status = rights_decision.decision  # Keep original decision but flag
            reason = f"Flagged for human review: risk score {risk_score}"
        elif rights_decision.is_rewrite():
            status = "REWRITE"
            reason = rights_decision.reason
        else:
            status = "APPROVED"
            reason = f"Approved: risk score {risk_score} < {self.review_threshold}"

        scored = ScoredReference(
            reference=reference,
            final_risk_score=risk_score,
            auto_blocked=auto_blocked,
            human_review_required=human_review,
            compliance_status=status,
            compliance_reason=reason,
        )

        logger.info(
            "risk_score_calculated",
            reference_id=reference.reference_id,
            title=reference.title,
            risk_score=risk_score,
            auto_blocked=auto_blocked,
            human_review=human_review,
            status=status,
        )

        return scored

    def _calculate_score(
        self, reference: Reference, rights_decision: RightsDecision
    ) -> int:
        """Calculate the risk score (0-100) for a reference."""
        score = 0

        # Base score by reference type
        type_base = {
            "licensed_direct": 10 if rights_decision.is_approved() else 90,
            "public_domain": 5,
            "style_only": 20,
            "commentary": 30,
        }
        score += type_base.get(reference.reference_type, 50)

        # Registry lookup for additional risk factors
        record = self._registry.get(reference.title.lower())
        if reference.reference_type != "public_domain":
            if not record:
                score += 30  # Unknown reference = risky
            elif record.trademark_elements:
                score += len(record.trademark_elements) * 5
            if record and record.auto_block:
                return 100  # Hard block

        # Factor in the rights decision's risk score
        if rights_decision.risk_score > 0:
            score = max(score, rights_decision.risk_score)

        # If it was a rewrite decision, add penalty
        if rights_decision.is_rewrite():
            score += 10

        return max(0, min(100, score))

    def recommend_action(self, risk_score: int) -> str:
        """Return the recommended action for a given risk score.

        Returns:
            'auto_block' if score >= auto_block_threshold,
            'human_review' if score >= review_threshold,
            'auto_approve' otherwise.
        """
        if risk_score >= self.auto_block_threshold:
            return "auto_block"
        if risk_score >= self.review_threshold:
            return "human_review"
        return "auto_approve"
