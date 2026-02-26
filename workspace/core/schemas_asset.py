"""core.schemas_asset — Pydantic models for collected assets."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from core.enums import AssetStatus, Platform


class Metrics(BaseModel):
    impressions_range: Optional[str] = None
    views: Optional[int] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    shares: Optional[int] = None


class MetricsExtra(BaseModel):
    saves: Optional[int] = None
    reposts: Optional[int] = None
    clicks: Optional[int] = None


class PlatformFields(BaseModel):
    ad_id: Optional[str] = None
    post_id: Optional[str] = None
    page_id: Optional[str] = None
    pin_id: Optional[str] = None
    tweet_id: Optional[str] = None


class Provenance(BaseModel):
    collector: str
    collector_version: Optional[str] = None
    source_url: Optional[str] = None
    fetched_at: str
    http_status: Optional[int] = None
    notes: Optional[str] = None


class Asset(BaseModel):
    asset_id: str
    platform: Platform
    workspace_id: str
    run_id: str
    brand: str
    collected_at: str
    ad_url: Optional[str] = None
    media_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    caption_or_copy: Optional[str] = None
    headline: Optional[str] = None
    cta: Optional[str] = None
    landing_page_url: Optional[str] = None
    landing_domain: Optional[str] = None
    first_seen_at: Optional[str] = None
    last_seen_at: Optional[str] = None
    status: AssetStatus = AssetStatus.UNKNOWN
    text_hash: Optional[str] = None
    media_hash: Optional[str] = None
    metrics: Metrics = Field(default_factory=Metrics)
    metrics_extra: MetricsExtra = Field(default_factory=MetricsExtra)
    platform_fields: PlatformFields = Field(default_factory=PlatformFields)
    provenance: Provenance


class AgentEnvelope(BaseModel):
    """Standard wrapper every agent must emit."""
    status: str = "ok"
    evidence_assets: list[str] = Field(default_factory=list)
    output: dict = Field(default_factory=dict)
    uncertainties: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
