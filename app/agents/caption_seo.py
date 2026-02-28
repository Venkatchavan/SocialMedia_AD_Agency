"""Caption + SEO + Disclosure Agent — Generates platform-optimized captions.

CRITICAL RULES:
- Every caption MUST include affiliate disclosure (non-negotiable).
- No deceptive "organic recommendation" phrasing.
- Adapted per platform (length, hashtags, tone).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog

from app.agents.base_agent import BaseAgent
from app.schemas.content import CaptionBundle
from app.policies.disclosure_rules import validate_disclosure, add_disclosure
from app.services.audit_logger import AuditLogger

logger = structlog.get_logger(__name__)


# Platform-specific caption templates
CAPTION_TEMPLATES: dict[str, str] = {
    "tiktok": (
        "{hook}\n\n"
        "{value_prop}\n\n"
        "{hashtags}\n\n"
        "🔗 Link in bio!\n"
        "#ad #affiliate — I may earn a commission at no extra cost to you."
    ),
    "instagram": (
        "{hook}\n\n"
        "{value_prop}\n\n"
        "👉 Link in bio to shop!\n\n"
        "{hashtags}\n\n"
        "#ad #affiliate — This post contains affiliate links. "
        "I may earn a commission at no extra cost to you."
    ),
    "x": (
        "{hook} {value_prop_short}\n\n"
        "🔗 {link}\n\n"
        "#ad #affiliate"
    ),
    "pinterest": (
        "{hook}\n\n"
        "{value_prop}\n\n"
        "Shop now: {link}\n\n"
        "{hashtags}\n\n"
        "#ad #affiliate"
    ),
}

# Hashtag sets by category
HASHTAG_LIBRARY: dict[str, list[str]] = {
    "Electronics": ["#tech", "#gadgets", "#techfinds", "#amazonfinds", "#techreview"],
    "Home & Kitchen": ["#homedecor", "#homefinds", "#amazonhome", "#interiordesign"],
    "Beauty": ["#beauty", "#skincare", "#beautytips", "#amazonbeauty", "#beautyfind"],
    "Fashion": ["#fashion", "#style", "#ootd", "#amazonfashion", "#fashionfinds"],
    "General": ["#amazonfinds", "#musthave", "#recommendation", "#find"],
}


class CaptionSEOAgent(BaseAgent):
    """Generate platform-specific captions with proper disclosures."""

    def __init__(self, audit_logger: AuditLogger, session_id: str = "") -> None:
        super().__init__(
            agent_id="caption_seo",
            audit_logger=audit_logger,
            session_id=session_id,
        )

    def execute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Generate captions for all target platforms.

        Inputs:
            - hook: str (video hook text)
            - value_prop: str (product value proposition)
            - category: str (product category)
            - affiliate_link: str
            - target_platforms: list[str]
            - script_id: str

        Returns:
            - caption_bundle: dict (CaptionBundle data)
        """
        hook = inputs.get("hook", "")
        value_prop = inputs.get("value_prop", "")
        category = inputs.get("category", "General")
        affiliate_link = inputs.get("affiliate_link", "")
        target_platforms = inputs.get("target_platforms", ["tiktok", "instagram"])
        script_id = inputs.get("script_id", "")

        # Get hashtags for category
        hashtags = self._get_hashtags(category, target_platforms)

        # Generate per-platform captions
        captions: dict[str, str] = {}
        for platform in target_platforms:
            caption = self._generate_caption(
                platform, hook, value_prop, affiliate_link, hashtags.get(platform, "")
            )

            # Validate disclosure
            is_valid, reason = validate_disclosure(caption, platform)
            if not is_valid:
                # Auto-add disclosure (from Agents.md Rule 10: fail-safe)
                caption = add_disclosure(caption, platform)
                logger.warning(
                    "disclosure_auto_added",
                    platform=platform,
                    original_reason=reason,
                )

            captions[platform] = caption

        bundle = CaptionBundle(
            id=str(uuid.uuid4()),
            script_id=script_id,
            captions=captions,
            affiliate_link=affiliate_link,
            created_at=datetime.now(tz=timezone.utc),
        )

        # Final verification — ALL captions must have disclosure
        all_valid = bundle.verify_all_disclosures()
        if not all_valid:
            logger.error("disclosure_verification_failed", bundle_id=bundle.id)
            # This should never happen given the auto-add above,
            # but if it does, raise to block publishing
            raise ValueError("Caption bundle failed disclosure verification")

        logger.info(
            "captions_generated",
            bundle_id=bundle.id,
            platforms=target_platforms,
            all_disclosures_valid=all_valid,
        )

        return {"caption_bundle": bundle.model_dump(mode="json")}

    def _generate_caption(
        self,
        platform: str,
        hook: str,
        value_prop: str,
        affiliate_link: str,
        hashtags: str,
    ) -> str:
        """Generate a caption for a specific platform."""
        template = CAPTION_TEMPLATES.get(platform, CAPTION_TEMPLATES["instagram"])

        # Shorten for X (280 char limit)
        value_prop_short = value_prop[:80] + "..." if len(value_prop) > 80 else value_prop

        caption = template.format(
            hook=hook,
            value_prop=value_prop,
            value_prop_short=value_prop_short,
            link=affiliate_link,
            hashtags=hashtags,
        )

        return caption.strip()

    def _get_hashtags(
        self, category: str, platforms: list[str]
    ) -> dict[str, str]:
        """Get platform-appropriate hashtags for a category."""
        base_tags = HASHTAG_LIBRARY.get(category, HASHTAG_LIBRARY["General"])

        result: dict[str, str] = {}
        for platform in platforms:
            if platform == "x":
                # X: fewer hashtags (3-5)
                result[platform] = " ".join(base_tags[:3])
            elif platform == "instagram":
                # Instagram: more hashtags
                result[platform] = " ".join(base_tags)
            else:
                result[platform] = " ".join(base_tags[:5])

        return result
