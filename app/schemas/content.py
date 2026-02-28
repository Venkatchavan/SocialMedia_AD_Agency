"""Pydantic schemas for content generation artifacts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ContentAngle = Literal[
    "comparison", "top_3", "story", "problem_solution", "aesthetic", "meme_style"
]


class ContentBrief(BaseModel):
    """Creative brief for a single piece of content."""

    id: str
    product_id: str
    reference_ids: list[str] = Field(default_factory=list)
    angle: ContentAngle
    format: str = Field(default="short_video", description="short_video | image_carousel | pin")
    target_platforms: list[str] = Field(default_factory=list)
    hook_strategy: str = ""
    reference_integration_plan: str = ""
    notes: str = ""
    status: str = "draft"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ScriptScene(BaseModel):
    """A single scene in a video script."""

    scene_number: int
    scene_type: str = Field(description="e.g., hook, body, demo, cta")
    dialogue: str = ""
    visual_direction: str = ""
    duration_seconds: float = 5.0
    text_overlay: str = ""


class Script(BaseModel):
    """A complete video/content script."""

    id: str
    brief_id: str
    hook: str = Field(description="First 3-second hook text")
    scenes: list[ScriptScene] = Field(default_factory=list)
    cta: str = Field(description="Call to action text with {{AFFILIATE_DISCLOSURE}} placeholder")
    word_count: int = 0
    estimated_duration_seconds: int = 30
    content_hash: str = Field(default="", description="SHA-256 hash for dedup")
    version: int = 1
    status: str = "draft"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Storyboard(BaseModel):
    """Scene-by-scene visual prompts for asset generation."""

    id: str
    script_id: str
    scene_prompts: list[str] = Field(default_factory=list)
    style_guide: str = ""
    negative_prompts: list[str] = Field(
        default_factory=list,
        description="Elements to exclude from generation (e.g., copyrighted characters)",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CaptionBundle(BaseModel):
    """Platform-specific captions with affiliate disclosures."""

    id: str
    script_id: str
    captions: dict[str, str] = Field(
        default_factory=dict,
        description="Platform-keyed captions (e.g., {'tiktok': '...', 'instagram': '...'})",
    )
    affiliate_link: str = ""
    disclosure_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def has_disclosure(self, platform: str) -> bool:
        """Check if the caption for a given platform contains an affiliate disclosure."""
        caption = self.captions.get(platform, "")
        disclosure_markers = [
            "#ad",
            "#affiliate",
            "affiliate link",
            "commission",
            "paid partnership",
            "sponsored",
        ]
        caption_lower = caption.lower()
        return any(marker in caption_lower for marker in disclosure_markers)

    def verify_all_disclosures(self) -> bool:
        """Verify all platform captions contain disclosures."""
        if not self.captions:
            return False
        self.disclosure_verified = all(
            self.has_disclosure(platform) for platform in self.captions
        )
        return self.disclosure_verified
