"""Rights Verification Tool — CrewAI tool wrapper.

Deterministic tool for checking rights on references.
"""

from __future__ import annotations

from typing import Any


class RightsCheckTool:
    """CrewAI-compatible tool for rights verification."""

    name: str = "rights_check"
    description: str = (
        "Check the rights/licensing status of a cultural reference. "
        "Returns APPROVED, REWRITE, or REJECT with reasons. "
        "This is a deterministic check — no LLM involved."
    )

    def __init__(self, rights_engine: Any) -> None:
        self._engine = rights_engine

    def run(self, reference: dict) -> dict:
        """Execute the tool — check rights for a reference."""
        decision = self._engine.verify(reference)
        return decision.model_dump(mode="json")


class RiskScoreTool:
    """CrewAI-compatible tool for risk scoring."""

    name: str = "risk_score"
    description: str = (
        "Calculate a risk score (0-100) for a reference. "
        "Scores ≥70 auto-block, 40-69 need human review, <40 auto-approve. "
        "This is a deterministic calculation."
    )

    def __init__(self, risk_scorer: Any, rights_engine: Any) -> None:
        self._scorer = risk_scorer
        self._rights = rights_engine

    def run(self, reference: dict) -> dict:
        """Execute the tool — score risk for a reference."""
        # Get a rights decision first, then score
        decision = self._rights.verify(reference)
        ref_obj = self._rights._dict_to_reference(reference)
        scored = self._scorer.score(ref_obj, decision)
        return {
            "risk_score": scored.final_risk_score,
            "action": self._scorer.recommend_action(scored.final_risk_score),
            "auto_blocked": scored.auto_blocked,
            "human_review_required": scored.human_review_required,
        }
