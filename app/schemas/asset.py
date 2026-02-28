"""Pydantic schemas for asset management."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AssetRecord(BaseModel):
    """A single generated asset (image, video, audio, thumbnail)."""

    id: str
    script_id: str
    asset_type: str = Field(description="image | video | audio | thumbnail")
    storage_key: str = Field(description="S3/storage key")
    content_hash: str = Field(description="SHA-256 hash for dedup and tamper detection")
    mime_type: str = ""
    file_size_bytes: int = 0
    resolution: str = ""  # e.g., "1080x1920"
    duration_seconds: float | None = None
    generation_params: dict = Field(default_factory=dict)
    signed_url: str = ""
    signed_url_expiry: datetime | None = None
    status: str = "generated"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AssetManifest(BaseModel):
    """Collection of all assets for a single content piece."""

    id: str
    script_id: str
    assets: list[AssetRecord] = Field(default_factory=list)
    total_size_bytes: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FinalVideo(BaseModel):
    """Assembled final video ready for publishing."""

    id: str
    manifest_id: str
    storage_key: str
    content_hash: str
    mime_type: str = "video/mp4"
    file_size_bytes: int = 0
    resolution: str = ""
    duration_seconds: float = 0.0
    format: str = "mp4"
    signed_url: str = ""
    signed_url_expiry: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
