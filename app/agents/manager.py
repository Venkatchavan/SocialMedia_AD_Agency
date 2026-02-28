"""Manager Agent — Supervises agent execution and pipeline health.

The Manager Agent sits above all other agents. It:
- Monitors agent health and execution time
- Enforces retry / rewrite limits across the pipeline
- Provides LLM-powered quality review of generated content
- Makes final APPROVE / REWRITE / REJECT routing decisions
- Tracks pipeline-level metrics for observability

SECURITY:
- All inputs/outputs pass through BaseAgent constitution checks.
- LLM prompts never include raw API keys or secrets.
- Audit logging for every decision.
"""

from __future__ import annotations

import time
from typing import Any

import structlog

from app.agents.base_agent import BaseAgent
from app.services.audit_logger import AuditLogger
from app.services.llm_client import LLMClient

logger = structlog.get_logger(__name__)

# System prompt for the Manager's LLM-powered quality review
_REVIEW_SYSTEM_PROMPT = """\
You are a quality-control manager for a social-media ad agency.
Review the generated content and return a JSON object:
{
  "quality_score": <int 0-100>,
  "issues": [<string>, ...],
  "approved": <bool>,
  "feedback": "<string>"
}
Rules:
- Score >= 60 means APPROVE. Below 60 means REWRITE.
- Check for: clarity, engagement, disclosure presence, brand safety.
- Never approve content with missing affiliate disclosures.
- Never approve content with health/medical/financial claims.
- Be concise in feedback.
"""


class ManagerAgent(BaseAgent):
    """Supervises agent execution, reviews content quality, routes decisions."""

    MAX_REWRITE_LOOPS = 3

    def __init__(
        self,
        audit_logger: AuditLogger,
        llm_client: LLMClient | None = None,
        session_id: str = "",
    ) -> None:
        super().__init__(
            agent_id="manager",
            audit_logger=audit_logger,
            session_id=session_id,
        )
        self._llm = llm_client or LLMClient()
        self._rewrite_counts: dict[str, int] = {}
        self._agent_health: dict[str, dict[str, Any]] = {}

    def execute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Dispatch to the appropriate management action.

        Actions:
            - route_rights: Route a rights decision (APPROVE/REWRITE/REJECT)
            - route_qa: Route a QA decision
            - review_content: LLM-powered content quality review
            - track_agent: Record agent execution health
            - get_status: Return pipeline supervision status
        """
        action = inputs.get("action", "get_status")
        dispatch = {
            "route_rights": self._route_rights,
            "route_qa": self._route_qa,
            "review_content": self._review_content,
            "track_agent": self._track_agent,
            "get_status": self._get_status,
        }
        handler = dispatch.get(action, self._unknown_action)
        return handler(inputs)

    # ------------------------------------------------------------------
    # Routing decisions (deterministic)
    # ------------------------------------------------------------------

    def _route_rights(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Route based on rights verification decision."""
        status = inputs.get("compliance_status", "")
        return self._route_decision(
            scope="rights",
            status=status,
            reason=inputs.get("reason", ""),
            approve_next="generate_content",
            rewrite_next="rewrite_reference",
        )

    def _route_qa(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Route based on QA decision."""
        status = inputs.get("qa_status", "")
        return self._route_decision(
            scope="qa",
            status=status,
            reason=inputs.get("reason", ""),
            approve_next="publish",
            rewrite_next="rewrite_content",
        )

    def _route_decision(
        self,
        scope: str,
        status: str,
        reason: str,
        approve_next: str,
        rewrite_next: str,
    ) -> dict[str, Any]:
        """Generic routing logic for APPROVE/REWRITE/REJECT."""
        if status in ("APPROVED", "APPROVE"):
            return {
                "next_step": approve_next,
                "should_continue": True,
                "reason": f"{scope} approved — proceed to {approve_next}",
            }

        if status == "REWRITE":
            count = self._rewrite_counts.get(scope, 0) + 1
            self._rewrite_counts[scope] = count
            if count > self.MAX_REWRITE_LOOPS:
                return {
                    "next_step": "reject",
                    "should_continue": False,
                    "reason": f"Max {scope} rewrites ({self.MAX_REWRITE_LOOPS}) exceeded",
                }
            return {
                "next_step": rewrite_next,
                "should_continue": True,
                "reason": f"{scope} rewrite {count}/{self.MAX_REWRITE_LOOPS}",
            }

        # REJECT or unknown
        return {
            "next_step": "reject",
            "should_continue": False,
            "reason": f"{scope} rejected: {reason or 'No reason provided'}",
        }

    # ------------------------------------------------------------------
    # LLM-powered content review
    # ------------------------------------------------------------------

    def _review_content(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Use LLM to review generated content quality."""
        script = inputs.get("script", {})
        captions = inputs.get("captions", {})

        user_prompt = (
            f"Product: {inputs.get('product_title', 'Unknown')}\n"
            f"Hook: {script.get('hook', '')}\n"
            f"CTA: {script.get('cta', '')}\n"
            f"Captions: {captions}\n"
            "Review this content for quality, brand safety, and compliance."
        )

        review = self._llm.complete_json(
            system_prompt=_REVIEW_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            agent_id="manager",
        )

        quality_score = review.get("quality_score", 0)
        approved = review.get("approved", False)

        decision = "APPROVE" if approved else "REWRITE"
        logger.info(
            "manager_review",
            quality_score=quality_score,
            decision=decision,
        )

        return {
            "decision": decision,
            "quality_score": quality_score,
            "issues": review.get("issues", []),
            "feedback": review.get("feedback", ""),
        }

    # ------------------------------------------------------------------
    # Agent health tracking
    # ------------------------------------------------------------------

    def _track_agent(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Record agent execution metrics."""
        agent_id = inputs.get("agent_id", "unknown")
        duration = inputs.get("duration_ms", 0)
        success = inputs.get("success", True)

        health = self._agent_health.setdefault(agent_id, {
            "runs": 0, "failures": 0, "total_ms": 0,
        })
        health["runs"] += 1
        health["total_ms"] += duration
        if not success:
            health["failures"] += 1

        return {"tracked": True, "agent_id": agent_id}

    def _get_status(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Return current pipeline supervision status."""
        return {
            "next_step": "continue",
            "should_continue": True,
            "reason": "Pipeline supervision status OK",
            "rewrite_counts": dict(self._rewrite_counts),
            "agent_health": dict(self._agent_health),
            "session_id": self.session_id,
        }

    @staticmethod
    def _unknown_action(inputs: dict[str, Any]) -> dict[str, Any]:
        return {
            "next_step": "error",
            "should_continue": False,
            "reason": f"Unknown manager action: {inputs.get('action')}",
        }

    # ------------------------------------------------------------------
    # Supervised execution helper
    # ------------------------------------------------------------------

    def supervise(
        self, agent: BaseAgent, inputs: dict[str, Any],
    ) -> dict[str, Any]:
        """Run an agent under supervision — track timing and errors."""
        start = time.monotonic()
        success = True
        try:
            result = agent.run(inputs)
        except Exception:
            success = False
            self._track_agent({
                "agent_id": agent.agent_id,
                "duration_ms": int((time.monotonic() - start) * 1000),
                "success": False,
            })
            raise

        duration_ms = int((time.monotonic() - start) * 1000)
        self._track_agent({
            "agent_id": agent.agent_id,
            "duration_ms": duration_ms,
            "success": success,
        })
        return result
