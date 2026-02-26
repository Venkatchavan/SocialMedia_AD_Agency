"""core.schemas_brief — Pydantic models for creative briefs."""

from __future__ import annotations


from pydantic import BaseModel, Field


class Audience(BaseModel):
    persona: str = ""
    situation: str = ""
    barriers: list[str] = Field(default_factory=list)


class Insight(BaseModel):
    tension: str = ""
    why_now: str = ""


class Offer(BaseModel):
    type: str = ""
    terms: str = ""
    urgency: str = ""


class Mandatories(BaseModel):
    must_include: list[str] = Field(default_factory=list)
    must_avoid: list[str] = Field(default_factory=list)
    legal: list[str] = Field(default_factory=list)


class CreativeDirection(BaseModel):
    angle: str = ""
    hook: str = ""
    proof: str = ""
    cta: str = ""
    notes: str = ""


class ScriptBeat(BaseModel):
    time_range: str = ""
    action: str = ""
    on_screen_text: str = ""
    b_roll: str = ""


class Script(BaseModel):
    title: str = ""
    beats: list[ScriptBeat] = Field(default_factory=list)
    cta_line: str = ""


class BriefTestVariant(BaseModel):
    variant: str = ""
    hook: str = ""
    angle: str = ""
    offer: str = ""
    cta: str = ""
    format: str = ""


class RiskCompliance(BaseModel):
    claim_risks: list[str] = Field(default_factory=list)
    platform_risks: list[str] = Field(default_factory=list)


class BriefObject(BaseModel):
    """Full creative brief matching BRIEF_TEMPLATE.md."""
    workspace_id: str
    run_id: str
    background: str = ""
    objective_primary: str = ""
    objective_secondary: str = ""
    audience: Audience = Field(default_factory=Audience)
    insight: Insight = Field(default_factory=Insight)
    smp: str = ""  # Single-Minded Proposition — exactly one
    rtbs: list[str] = Field(default_factory=list)
    offer: Offer = Field(default_factory=Offer)
    mandatories: Mandatories = Field(default_factory=Mandatories)
    creative_directions: list[CreativeDirection] = Field(
        default_factory=list, min_length=0
    )
    hook_bank: list[str] = Field(default_factory=list)
    scripts: list[Script] = Field(default_factory=list)
    testing_matrix: list[BriefTestVariant] = Field(default_factory=list)
    risks: RiskCompliance = Field(default_factory=RiskCompliance)
    evidence_assets: list[str] = Field(default_factory=list)
