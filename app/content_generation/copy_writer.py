"""AI copy & caption generation (U-21).

Platform-specific caption rules with brand voice alignment.
Uses existing LLM Router pattern — no direct LLM calls in this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import structlog

from app.policies.agent_constitution import AgentConstitution

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class PlatformCaptionSpec:
    """Platform-specific caption constraints."""

    platform: str
    max_chars: int
    hashtag_range: tuple[int, int]
    tone: str
    cta_required: bool = True


PLATFORM_SPECS: dict[str, PlatformCaptionSpec] = {
    "instagram_feed": PlatformCaptionSpec("instagram_feed", 2200, (5, 10), "brand voice"),
    "instagram_reels": PlatformCaptionSpec("instagram_reels", 2200, (3, 5), "punchy, hook-first"),
    "tiktok": PlatformCaptionSpec("tiktok", 2200, (3, 5), "casual, trend-aware"),
    "linkedin": PlatformCaptionSpec("linkedin", 3000, (3, 5), "professional"),
    "x": PlatformCaptionSpec("x", 280, (1, 2), "concise"),
    "pinterest": PlatformCaptionSpec("pinterest", 500, (2, 4), "descriptive"),
    "youtube_shorts": PlatformCaptionSpec("youtube_shorts", 5000, (3, 5), "searchable"),
}


@dataclass
class GeneratedCaption:
    """A generated caption for a specific platform."""

    platform: str
    caption: str
    hashtags: list[str] = field(default_factory=list)
    cta: str = ""
    disclosure: str = "#ad"
    word_count: int = 0
    char_count: int = 0

    @property
    def full_text(self) -> str:
        """Caption with hashtags and disclosure."""
        parts = [self.caption]
        if self.cta:
            parts.append(self.cta)
        if self.hashtags:
            parts.append(" ".join(f"#{h}" for h in self.hashtags))
        parts.append(self.disclosure)
        return "\n\n".join(parts)


class CopyWriter:
    """Generate platform-specific captions from brief data.

    NOTE: In production, this calls the LLM Router for AI-generated copy.
    This implementation uses template-based generation for testing.
    """

    def generate(
        self,
        platform: str,
        hook: str,
        product_name: str = "",
        angle: str = "",
        brand_voice: dict[str, str] | None = None,
        affiliate_link: str = "",
    ) -> GeneratedCaption:
        """Generate a caption for the given platform."""
        spec = PLATFORM_SPECS.get(platform)
        if spec is None:
            spec = PlatformCaptionSpec(platform, 2200, (3, 5), "neutral")

        # Rule 5: Validate input against prompt injection
        if hook:
            hook = AgentConstitution.validate_input(hook)

        caption_body = self._build_caption(hook, product_name, angle, spec)
        hashtags = self._generate_hashtags(product_name, angle, spec)
        cta = self._build_cta(affiliate_link, spec)

        # Rule 4: Affiliate agency — always include disclosure
        disclosure = "#ad"

        # Rule 5: Check for forbidden marketing claims
        violations = AgentConstitution.validate_caption(
            caption_body + " " + disclosure, spec.platform
        )
        for v in violations:
            if v.startswith("FORBIDDEN_CLAIM"):
                logger.warning("forbidden_claim_in_caption", violation=v)

        # Truncate if over limit
        if len(caption_body) > spec.max_chars:
            caption_body = caption_body[: spec.max_chars - 3] + "..."

        result = GeneratedCaption(
            platform=platform,
            caption=caption_body,
            hashtags=hashtags,
            cta=cta,
            disclosure=disclosure,
            word_count=len(caption_body.split()),
            char_count=len(caption_body),
        )

        logger.info(
            "caption_generated",
            platform=platform,
            char_count=result.char_count,
            hashtag_count=len(hashtags),
        )
        return result

    def generate_multi_platform(
        self,
        platforms: list[str],
        hook: str,
        product_name: str = "",
        angle: str = "",
        brand_voice: dict[str, str] | None = None,
        affiliate_link: str = "",
    ) -> dict[str, GeneratedCaption]:
        """Generate captions for multiple platforms."""
        results: dict[str, GeneratedCaption] = {}
        for platform in platforms:
            results[platform] = self.generate(
                platform, hook, product_name, angle, brand_voice, affiliate_link
            )
        return results

    def _build_caption(
        self, hook: str, product_name: str, angle: str, spec: PlatformCaptionSpec
    ) -> str:
        """Build caption body from components."""
        parts: list[str] = []
        if hook:
            parts.append(hook)
        if product_name:
            if angle:
                parts.append(f"Check out {product_name} — {angle}.")
            else:
                parts.append(f"Check out {product_name}.")
        return "\n\n".join(parts) if parts else "Check this out!"

    def _generate_hashtags(
        self, product_name: str, angle: str, spec: PlatformCaptionSpec
    ) -> list[str]:
        """Generate hashtags within platform constraints."""
        min_h, max_h = spec.hashtag_range
        tags: list[str] = []
        if product_name:
            tags.append(product_name.replace(" ", "").lower())
        if angle:
            tags.append(angle.replace(" ", "").lower())
        # Pad with generic tags
        generic = ["musthave", "trending", "fyp", "viral", "recommendation", "review"]
        for g in generic:
            if len(tags) >= max_h:
                break
            if g not in tags:
                tags.append(g)
        return tags[:max_h]

    def _build_cta(self, affiliate_link: str, spec: PlatformCaptionSpec) -> str:
        """Build call-to-action text."""
        if not spec.cta_required:
            return ""
        if affiliate_link:
            return f"🔗 Link in bio | {affiliate_link}"
        return "🔗 Link in bio"
