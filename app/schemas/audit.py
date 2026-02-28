"""Pydantic schemas for audit events."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AuditEvent(BaseModel):
    """Immutable audit event. Every decision must produce one."""

    event_id: str = Field(description="UUID")
    agent_id: str = Field(description="Which agent/service produced this event")
    action: str = Field(description="What action was taken")
    input_hash: str = Field(default="", description="SHA-256 of input data")
    output_hash: str = Field(default="", description="SHA-256 of output data")
    decision: str = Field(default="", description="APPROVE | REWRITE | REJECT | PUBLISH | etc.")
    reason: str = Field(default="", description="Human-readable reason for the decision")
    session_id: str = Field(default="", description="Pipeline run ID for tracing")
    previous_event_hash: str = Field(
        default="",
        description="Hash of the previous audit event for tamper detection",
    )
    metadata: dict = Field(default_factory=dict, description="Additional context")
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="timestamp")

    model_config = {"populate_by_name": True}

    def to_hash_input(self) -> str:
        """Produce a deterministic string for hashing this event."""
        return (
            f"{self.event_id}|{self.agent_id}|{self.action}|"
            f"{self.input_hash}|{self.output_hash}|{self.decision}|"
            f"{self.reason}|{self.session_id}|{self.previous_event_hash}|"
            f"{self.created_at.isoformat()}"
        )
