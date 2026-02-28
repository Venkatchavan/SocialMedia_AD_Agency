"""Pydantic schemas for rights and compliance decisions."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RightsRecord(BaseModel):
    """A record in the rights registry."""

    id: str
    reference_title: str
    reference_type: str  # licensed_direct | public_domain | style_only | commentary
    ip_owner: str = ""
    license_id: str = ""
    license_scope: dict = Field(
        default_factory=lambda: {
            "commercial": False,
            "social": False,
            "derivative": False,
        }
    )
    license_expiry: Optional[datetime] = None
    territory: str = "worldwide"
    status: str = "pending"  # active | expired | revoked | pending | blocked
    risk_score: int = Field(ge=0, le=100, default=100)
    auto_block: bool = False
    license_proof_url: str = ""
    provenance_chain: list[dict] = Field(default_factory=list)
    trademark_elements: list[str] = Field(default_factory=list)
    blocked_elements: list[str] = Field(default_factory=list)
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = ""


class RightsDecision(BaseModel):
    """Output of the rights verification engine for a single reference."""

    reference_id: str
    reference_title: str = ""
    reference_type: str = ""
    decision: str = Field(description="APPROVE | REWRITE | REJECT")
    reason: str
    risk_score: int = Field(ge=0, le=100, default=100)
    rewrite_instructions: Optional[str] = None
    audit_id: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    def is_approved(self) -> bool:
        return self.decision == "APPROVE"

    def is_rewrite(self) -> bool:
        return self.decision == "REWRITE"

    def is_rejected(self) -> bool:
        return self.decision == "REJECT"
