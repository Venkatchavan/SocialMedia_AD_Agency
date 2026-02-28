"""Pydantic schemas for cultural references."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ReferenceType = Literal["licensed_direct", "public_domain", "style_only", "commentary"]
Medium = Literal["anime", "movie", "music", "novel", "other"]


class Reference(BaseModel):
    """A cultural reference mapped to a product."""

    reference_id: str
    title: str = Field(description="Work/franchise name")
    medium: Medium
    reference_type: ReferenceType
    allowed_usage_mode: str = Field(
        description="What exactly can be used from this reference",
        examples=["visual style inspired by; no character names or logos"],
    )
    risk_score: int = Field(ge=0, le=100, description="0=safe, 100=dangerous")
    audience_overlap_score: float = Field(ge=0.0, le=1.0, default=0.0)
    trending_relevance: float = Field(ge=0.0, le=1.0, default=0.0)
    keywords: list[str] = Field(default_factory=list)
    fallback_references: list[str] = Field(
        default_factory=list,
        description="IDs of safer alternative references",
    )
    source_metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ReferenceBundle(BaseModel):
    """Collection of references mapped to a single product."""

    product_id: str
    references: list[Reference] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ScoredReference(BaseModel):
    """A reference that has passed rights verification and has a final risk score."""

    reference: Reference
    final_risk_score: int = Field(ge=0, le=100)
    auto_blocked: bool = False
    human_review_required: bool = False
    compliance_status: str = Field(description="APPROVED | REWRITE | REJECT")
    compliance_reason: str = Field(default="")
