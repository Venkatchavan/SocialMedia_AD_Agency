"""Pipeline state models and status enum.

Extracted from content_pipeline.py to keep modules under 250 lines.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field


class PipelineStatus(str, Enum):
    """Pipeline execution status."""

    PENDING = "pending"
    INTAKE = "intake"
    ENRICHMENT = "enrichment"
    REFERENCE_MAPPING = "reference_mapping"
    RIGHTS_CHECK = "rights_check"
    CONTENT_GENERATION = "content_generation"
    QA = "qa"
    PLATFORM_ADAPTATION = "platform_adaptation"
    PUBLISHING = "publishing"
    COMPLETED = "completed"
    REJECTED = "rejected"
    ERROR = "error"


class PipelineState(BaseModel):
    """Shared state object that flows through the pipeline."""

    pipeline_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: PipelineStatus = PipelineStatus.PENDING
    session_id: str = ""

    # Inputs
    asin: str = ""
    source: str = "manual"
    product_data: dict = Field(default_factory=dict)
    target_platforms: list[str] = Field(default_factory=lambda: ["tiktok", "instagram"])

    # Stage outputs
    product: dict = Field(default_factory=dict)
    enriched_product: dict = Field(default_factory=dict)
    reference_bundle: dict = Field(default_factory=dict)
    rights_decision: dict = Field(default_factory=dict)
    script: dict = Field(default_factory=dict)
    caption_bundle: dict = Field(default_factory=dict)
    qa_decision: dict = Field(default_factory=dict)
    platform_packages: list[dict] = Field(default_factory=list)
    publish_results: list[dict] = Field(default_factory=list)

    # Control flow
    rewrite_count: int = 0
    max_retries: int = 3
    error_message: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    completed_at: datetime | None = None
