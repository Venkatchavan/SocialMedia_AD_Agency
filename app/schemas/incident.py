"""Pydantic schemas for incidents."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class Incident(BaseModel):
    """An incident record for compliance violations, errors, or security events."""

    id: str
    incident_type: str = Field(
        description="dmca | policy_violation | token_leak | account_restriction | "
        "auth_failure | duplicate_content | disclosure_missing"
    )
    severity: str = Field(default="medium", description="low | medium | high | critical")
    description: str
    affected_posts: list[str] = Field(default_factory=list)
    affected_platforms: list[str] = Field(default_factory=list)
    resolution: str = ""
    status: str = "open"  # open | investigating | resolved | closed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = None
    created_by: str = ""
