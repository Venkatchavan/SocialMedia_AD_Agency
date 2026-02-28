"""AI image generation (U-22).

Configurable provider: DALL-E 3, Stable Diffusion, Ideogram, Flux.
Template-based prompt building — actual API calls delegated to provider SDK.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class ImageProvider(str, Enum):
    """Supported image generation providers."""

    DALLE3 = "dalle3"
    STABLE_DIFFUSION = "stable_diffusion"
    IDEOGRAM = "ideogram"
    FLUX = "flux"


@dataclass(frozen=True)
class ImageSpec:
    """Image generation specification."""

    width: int = 1024
    height: int = 1024
    style: str = "vivid"
    quality: str = "standard"
    n: int = 1


@dataclass
class GeneratedImage:
    """Result of an image generation request."""

    provider: str
    prompt: str
    image_url: str = ""
    local_path: str = ""
    width: int = 0
    height: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: str = ""


class ImagePromptBuilder:
    """Build image prompts from brief data + brand style."""

    def build(
        self,
        product_name: str = "",
        visual_direction: str = "",
        brand_colors: list[str] | None = None,
        mood: str = "",
        platform: str = "",
    ) -> str:
        """Build an image generation prompt."""
        parts: list[str] = []

        if visual_direction:
            parts.append(visual_direction)
        elif product_name:
            parts.append(f"Product photo of {product_name}")

        if mood:
            parts.append(f"Mood: {mood}")
        if brand_colors:
            parts.append(f"Color palette: {', '.join(brand_colors)}")

        # Platform-specific aspect ratio hints
        aspect_hints = {
            "instagram_feed": "square composition, 1:1 aspect ratio",
            "instagram_reels": "vertical composition, 9:16 aspect ratio",
            "tiktok": "vertical composition, 9:16 aspect ratio",
            "pinterest": "vertical composition, 2:3 aspect ratio",
            "linkedin": "horizontal composition, 1.91:1 aspect ratio",
            "x": "horizontal composition, 16:9 aspect ratio",
            "youtube_shorts": "vertical composition, 9:16 aspect ratio",
        }
        if platform in aspect_hints:
            parts.append(aspect_hints[platform])

        parts.append("High quality, professional, commercial photography style")

        return ". ".join(parts) if parts else "Professional product photograph"


class ImageGenerator:
    """Generate images using configurable providers.

    NOTE: In production, this calls the image generation API.
    This implementation builds prompts and returns structured results.
    """

    def __init__(self, provider: ImageProvider = ImageProvider.DALLE3):
        self.provider = provider
        self._prompt_builder = ImagePromptBuilder()

    def generate(
        self,
        product_name: str = "",
        visual_direction: str = "",
        brand_colors: list[str] | None = None,
        mood: str = "",
        platform: str = "",
        spec: ImageSpec | None = None,
    ) -> GeneratedImage:
        """Generate an image from brief data."""
        if spec is None:
            spec = ImageSpec()

        prompt = self._prompt_builder.build(
            product_name=product_name,
            visual_direction=visual_direction,
            brand_colors=brand_colors,
            mood=mood,
            platform=platform,
        )

        result = GeneratedImage(
            provider=self.provider.value,
            prompt=prompt,
            width=spec.width,
            height=spec.height,
            metadata={
                "style": spec.style,
                "quality": spec.quality,
                "n": spec.n,
                "platform": platform,
            },
        )

        logger.info(
            "image_generation_requested",
            provider=self.provider.value,
            prompt_len=len(prompt),
            platform=platform,
        )
        return result

    def generate_batch(
        self,
        platforms: list[str],
        product_name: str = "",
        visual_direction: str = "",
        brand_colors: list[str] | None = None,
        mood: str = "",
    ) -> dict[str, GeneratedImage]:
        """Generate images for multiple platforms."""
        results: dict[str, GeneratedImage] = {}
        for platform in platforms:
            results[platform] = self.generate(
                product_name=product_name,
                visual_direction=visual_direction,
                brand_colors=brand_colors,
                mood=mood,
                platform=platform,
            )
        return results
