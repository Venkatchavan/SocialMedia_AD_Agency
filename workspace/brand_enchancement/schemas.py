"""brand_enchancement.schemas — Pydantic models for the Brand Enhancement Engine.

Industry-agnostic: works for SaaS, healthcare, fashion, finance, food, B2B, etc.
All sections use dict[str, Any] so no field is ever missing for an unfamiliar industry.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


# ── Atomic building blocks ───────────────────────────────────────────────────

class ChangeRecord(BaseModel):
    """One entry in the brand bible's change log."""

    run_id: str
    timestamp: str
    fields_updated: list[str] = Field(default_factory=list)
    keywords_added: list[str] = Field(default_factory=list)
    hashtags_added: list[str] = Field(default_factory=list)
    summary: str = ""


class UpdateSignal(BaseModel):
    """Inputs for one brand enhancement run."""

    run_id: str
    keywords: list[str] = Field(default_factory=list)
    hashtags: list[str] = Field(default_factory=list)
    extra_context: str = ""


# ── Core brand sections (generic keys, any-industry content) ─────────────────

class BrandSummary(BaseModel):
    what_we_sell: str = ""
    what_we_stand_for: str = ""
    what_we_never_do: str = ""
    industry: str = "general"
    extra: dict[str, Any] = Field(default_factory=dict)


class AudienceSection(BaseModel):
    primary: str = ""
    secondary: str = ""
    awareness_level: str = ""
    pain_points: list[str] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)


class VoiceToneSection(BaseModel):
    adjectives: list[str] = Field(default_factory=list)
    use: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)


class ProofClaimsSection(BaseModel):
    allowed: list[str] = Field(default_factory=list)
    forbidden: list[str] = Field(default_factory=list)
    substantiation_required: bool = True
    extra: dict[str, Any] = Field(default_factory=dict)


class VisualStyleSection(BaseModel):
    do: list[str] = Field(default_factory=list)
    dont: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)


class OffersSection(BaseModel):
    typical: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)


class CompetitorsSection(BaseModel):
    main: list[str] = Field(default_factory=list)
    positioning_difference: str = ""
    extra: dict[str, Any] = Field(default_factory=dict)


# ── Root document ─────────────────────────────────────────────────────────────

class BrandBibleDoc(BaseModel):
    """Versioned, industry-agnostic brand bible document.

    Fields are merged incrementally across runs — never blindly overwritten.
    All history is preserved in ``change_log``.
    """

    workspace_id: str
    version: int = 1
    run_id: str = ""
    updated_at: str = ""

    brand_summary: BrandSummary = Field(default_factory=BrandSummary)
    audience: AudienceSection = Field(default_factory=AudienceSection)
    voice_tone: VoiceToneSection = Field(default_factory=VoiceToneSection)
    proof_claims: ProofClaimsSection = Field(default_factory=ProofClaimsSection)
    visual_style: VisualStyleSection = Field(default_factory=VisualStyleSection)
    offers: OffersSection = Field(default_factory=OffersSection)
    competitors: CompetitorsSection = Field(default_factory=CompetitorsSection)

    # Accumulated signal pools
    keywords: list[str] = Field(default_factory=list)
    hashtags: list[str] = Field(default_factory=list)
    extra_context_log: list[str] = Field(default_factory=list)

    # Full history
    change_log: list[ChangeRecord] = Field(default_factory=list)
