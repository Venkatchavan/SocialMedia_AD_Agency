"""core.schemas_tag — Pydantic models for deterministic tagging."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from core.enums import (
    AssetType,
    CTAType,
    FormatType,
    HookTactic,
    MessagingAngle,
    OfferType,
    ProofElement,
    RiskFlag,
)


class First3Seconds(BaseModel):
    visual: Optional[str] = None
    spoken_hook: Optional[str] = None
    on_screen_text: Optional[str] = None
    pattern_interrupt: bool = False


class OfferDetail(BaseModel):
    type: OfferType = OfferType.UNKNOWN
    terms: Optional[str] = None
    urgency: Optional[str] = None


class CTADetail(BaseModel):
    type: CTAType = CTAType.UNKNOWN
    exact_text_if_visible: Optional[str] = None


class ProductionNotes(BaseModel):
    pacing: Optional[str] = None
    cuts_per_10s: Optional[int] = None
    captions_style: Optional[str] = None


class TagSet(BaseModel):
    """Full tag output for a single asset."""
    asset_id: str
    asset_type: AssetType = AssetType.UNKNOWN
    format_type: FormatType = FormatType.UNKNOWN
    hook_tactics: list[HookTactic] = Field(default_factory=list)
    messaging_angle: MessagingAngle = MessagingAngle.OTHER
    offer_type: OfferType = OfferType.UNKNOWN
    proof_elements: list[ProofElement] = Field(default_factory=list)
    cta_type: CTAType = CTAType.UNKNOWN
    risk_flags: list[RiskFlag] = Field(default_factory=lambda: [RiskFlag.NONE])
    first_3_seconds: First3Seconds = Field(default_factory=First3Seconds)
    offer: OfferDetail = Field(default_factory=OfferDetail)
    cta: CTADetail = Field(default_factory=CTADetail)
    objections_addressed: list[str] = Field(default_factory=list)
    production_notes: ProductionNotes = Field(default_factory=ProductionNotes)
    reuse_ideas: list[str] = Field(default_factory=list, max_length=5)
