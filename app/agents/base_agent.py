"""Base agent class with constitution guardrails.

Every agent in the system MUST extend this base class,
which enforces the Agent Constitution before any action.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import structlog

from app.policies.agent_constitution import AgentConstitution, ConstitutionViolation
from app.services.audit_logger import AuditLogger

logger = structlog.get_logger(__name__)


class BaseAgent(ABC):
    """Abstract base for all agents. Enforces constitution and audit logging."""

    def __init__(
        self,
        agent_id: str,
        audit_logger: AuditLogger,
        session_id: str = "",
    ) -> None:
        self.agent_id = agent_id
        self._audit = audit_logger
        self.session_id = session_id

    @abstractmethod
    def execute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute the agent's primary task. Must be implemented by subclasses."""
        ...

    def run(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Run the agent with constitution checks, audit logging, and error handling.

        This is the public entry point. It wraps execute() with guardrails.
        """
        # Pre-execution: validate inputs
        self._pre_execute_checks(inputs)

        # Log start
        self._audit.log(
            agent_id=self.agent_id,
            action=f"{self.agent_id}_start",
            decision="STARTED",
            reason="Agent execution started",
            input_data=self._safe_input_summary(inputs),
            session_id=self.session_id,
        )

        try:
            # Execute
            result = self.execute(inputs)

            # Post-execution: validate outputs
            self._post_execute_checks(result)

            # Log completion
            self._audit.log(
                agent_id=self.agent_id,
                action=f"{self.agent_id}_complete",
                decision="COMPLETED",
                reason="Agent execution completed successfully",
                output_data=self._safe_output_summary(result),
                session_id=self.session_id,
            )

            return result

        except ConstitutionViolation as e:
            self._audit.log(
                agent_id=self.agent_id,
                action=f"{self.agent_id}_violation",
                decision="BLOCKED",
                reason=str(e),
                session_id=self.session_id,
            )
            raise

        except Exception as e:
            self._audit.log(
                agent_id=self.agent_id,
                action=f"{self.agent_id}_error",
                decision="ERROR",
                reason=str(e),
                session_id=self.session_id,
            )
            raise

    def _pre_execute_checks(self, inputs: dict[str, Any]) -> None:
        """Run constitution checks before execution."""
        # Validate all string inputs for injection
        for key, value in inputs.items():
            if isinstance(value, str) and value:
                AgentConstitution.validate_input(value)

    def _post_execute_checks(self, result: dict[str, Any]) -> None:
        """Run constitution checks after execution."""
        # Ensure no secrets in output
        for key, value in result.items():
            if isinstance(value, str):
                if not AgentConstitution.validate_no_secret_exposure(value):
                    raise ConstitutionViolation(
                        "SECRET_EXPOSURE",
                        f"Output field '{key}' contains potential secret material",
                    )

    def _safe_input_summary(self, inputs: dict[str, Any]) -> dict:
        """Create a safe summary of inputs for audit logging (no secrets)."""
        return {k: type(v).__name__ for k, v in inputs.items()}

    def _safe_output_summary(self, result: dict[str, Any]) -> dict:
        """Create a safe summary of outputs for audit logging (no secrets)."""
        return {k: type(v).__name__ for k, v in result.items()}
