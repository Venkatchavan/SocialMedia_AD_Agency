"""Pydantic schemas for publishing and platform interactions."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PlatformPackage(BaseModel):
    """A complete content package ready for a specific platform."""

    id: str
    platform: str = Field(description="tiktok | instagram | x | pinterest")
    media_path: str = ""
    media_size: int = 0
    signed_media_url: str = ""
    caption: str = ""
    hashtags: list[str] = Field(default_factory=list)
    scheduled_time: Optional[datetime] = None
    content_hash: str = ""
    qa_status: str = "pending"  # pending | approved | rewrite | reject
    compliance_status: str = "pending"
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PublishResult(BaseModel):
    """Result of a publish attempt."""

    platform: str = ""
    post_id: str = ""
    status: str = Field(
        description="PUBLISHED | QUEUED | RATE_LIMITED | TRANSIENT_ERROR | AUTH_ERROR | POLICY_ERROR"
    )
    url: str = ""
    reason: str = ""
    retry_after: Optional[int] = None  # seconds
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    def is_success(self) -> bool:
        return self.status == "PUBLISHED"


class PostQueueItem(BaseModel):
    """An item in the publishing queue."""

    id: str
    asset_id: str
    platform: str
    caption: str
    scheduled_time: Optional[datetime] = None
    priority: int = 0
    qa_status: str = "pending"
    compliance_status: str = "pending"
    retry_count: int = 0
    max_retries: int = 3
    status: str = "queued"
    error_type: str = ""
    error_message: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
