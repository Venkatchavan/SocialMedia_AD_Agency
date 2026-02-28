"""Pydantic schemas for analytics and experiments."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class PerformanceMetrics(BaseModel):
    """Performance metrics for a published post."""

    id: str
    published_post_id: str
    platform: str
    impressions: int = 0
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    clicks: int = 0
    ctr: float = 0.0
    watch_time_avg: Optional[float] = None
    affiliate_clicks: int = 0
    affiliate_conversions: int = 0
    affiliate_revenue: float = 0.0
    collected_at: datetime = Field(default_factory=datetime.utcnow)


class ExperimentVariant(BaseModel):
    """A variant in an A/B experiment."""

    variant_id: str
    name: str  # "control", "treatment_a"
    config: dict = Field(default_factory=dict, alias="content_config")
    traffic_percentage: float = 0.0
    sample_count: int = 0
    metrics: Optional[PerformanceMetrics] = None

    model_config = {"populate_by_name": True}


class ExperimentResult(BaseModel):
    """Statistical result of an experiment."""

    winning_variant: Optional[str] = None
    p_value: float = 1.0
    confidence_level: float = 0.0
    lift_percentage: float = 0.0
    sample_size_met: bool = False
    recommendation: Literal["promote", "pause", "rewrite", "inconclusive"] = "inconclusive"


class Experiment(BaseModel):
    """An A/B experiment definition and results."""

    experiment_id: str
    name: str
    hypothesis: str = ""
    hypothesis_source: Literal["data", "reddit", "intuition", "competitor"] = "intuition"
    experiment_type: Literal[
        "hook_ab", "reference_type_ab", "caption_ab",
        "posting_time_ab", "angle_ab", "platform_ab",
    ] = "hook_ab"
    variants: list[ExperimentVariant] = Field(default_factory=list)
    traffic_split: dict[str, float] = Field(default_factory=dict)
    min_sample_size: int = 100
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Literal["draft", "active", "running", "completed", "stopped"] = "draft"
    results: Optional[ExperimentResult] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
