"""Orchestrator / Manager Agent — Top-level pipeline flow controller."""

from __future__ import annotations

import uuid
from typing import Any

import structlog

from app.agents.base_agent import BaseAgent
from app.services.audit_logger import AuditLogger

logger = structlog.get_logger(__name__)


class OrchestratorAgent(BaseAgent):
    """Manage end-to-end pipeline flow, handle branching, enforce retry limits."""

    MAX_REWRITE_LOOPS = 3

    def __init__(self, audit_logger: AuditLogger, session_id: str = "") -> None:
        if not session_id:
            session_id = f"pipeline-{uuid.uuid4().hex[:12]}"
        super().__init__(
            agent_id="orchestrator",
            audit_logger=audit_logger,
            session_id=session_id,
        )
        self._rewrite_count = 0
        self._content_rewrite_count = 0

    def execute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute orchestration logic.

        This agent coordinates the pipeline — it doesn't do content work itself.
        It tracks state transitions and enforces guardrails.

        Inputs:
            - action: str — "route_rights_decision" | "route_qa_decision" | "check_state"
            - compliance_status: str (for routing)
            - qa_status: str (for routing)

        Returns:
            - next_step: str — what should happen next
            - should_continue: bool
            - reason: str
        """
        action = inputs.get("action", "check_state")

        if action == "route_rights_decision":
            return self._route_rights_decision(inputs)
        elif action == "route_qa_decision":
            return self._route_qa_decision(inputs)
        elif action == "check_state":
            return self._check_state(inputs)
        else:
            return {
                "next_step": "error",
                "should_continue": False,
                "reason": f"Unknown orchestrator action: {action}",
            }

    def _route_rights_decision(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Route based on rights verification decision."""
        status = inputs.get("compliance_status", "")

        if status == "APPROVED":
            return {
                "next_step": "generate_content",
                "should_continue": True,
                "reason": "Rights approved — proceed to content generation",
            }
        elif status == "REWRITE":
            self._rewrite_count += 1
            if self._rewrite_count > self.MAX_REWRITE_LOOPS:
                return {
                    "next_step": "reject",
                    "should_continue": False,
                    "reason": f"Max rewrite attempts ({self.MAX_REWRITE_LOOPS}) exceeded",
                }
            return {
                "next_step": "rewrite_reference",
                "should_continue": True,
                "reason": f"Rewrite needed (attempt {self._rewrite_count}/{self.MAX_REWRITE_LOOPS})",
            }
        else:  # REJECT
            return {
                "next_step": "reject",
                "should_continue": False,
                "reason": f"Rights rejected: {inputs.get('reason', 'No reason provided')}",
            }

    def _route_qa_decision(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Route based on QA decision."""
        status = inputs.get("qa_status", "")

        if status == "APPROVE":
            return {
                "next_step": "publish",
                "should_continue": True,
                "reason": "QA approved — proceed to publish",
            }
        elif status == "REWRITE":
            self._content_rewrite_count += 1
            if self._content_rewrite_count > self.MAX_REWRITE_LOOPS:
                return {
                    "next_step": "reject",
                    "should_continue": False,
                    "reason": f"Max content rewrite attempts ({self.MAX_REWRITE_LOOPS}) exceeded",
                }
            return {
                "next_step": "rewrite_content",
                "should_continue": True,
                "reason": f"Content rewrite needed (attempt {self._content_rewrite_count}/{self.MAX_REWRITE_LOOPS})",
            }
        else:  # REJECT
            return {
                "next_step": "reject",
                "should_continue": False,
                "reason": f"QA rejected: {inputs.get('reason', 'No reason provided')}",
            }

    def _check_state(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Check pipeline state and report status."""
        return {
            "next_step": "continue",
            "should_continue": True,
            "reason": "Pipeline state check OK",
            "rewrite_count": self._rewrite_count,
            "content_rewrite_count": self._content_rewrite_count,
            "session_id": self.session_id,
        }
