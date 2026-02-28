"""Affiliate disclosure rules per platform.

MANDATORY (from Agents.md Rule 4):
- Every publishable caption must include clear affiliate disclosure.
- Disclosure checks are required per platform variant.
- No deceptive "organic recommendation" phrasing if affiliate links are present.
"""

from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)


# Platform-specific disclosure requirements
PLATFORM_DISCLOSURE_RULES: dict[str, dict] = {
    "tiktok": {
        "required_markers": ["#ad", "#affiliate", "#sponsored"],
        "min_markers": 1,
        "placement": "Must appear in caption, preferably near the beginning",
        "format_note": "TikTok requires clear and conspicuous disclosure",
        "max_caption_length": 2200,
    },
    "instagram": {
        "required_markers": ["#ad", "#affiliate", "#sponsored", "Paid partnership"],
        "min_markers": 1,
        "placement": "Must appear in caption before 'more' fold if possible",
        "format_note": "Instagram supports Paid Partnership tag — use when available",
        "max_caption_length": 2200,
    },
    "x": {
        "required_markers": ["#ad", "#affiliate", "#sponsored"],
        "min_markers": 1,
        "placement": "Must appear in tweet text",
        "format_note": "Keep within 280 chars including disclosure",
        "max_caption_length": 280,
    },
    "pinterest": {
        "required_markers": ["#ad", "#affiliate", "#sponsored"],
        "min_markers": 1,
        "placement": "Must appear in pin description",
        "format_note": "Pinterest recommends clear disclosure in description",
        "max_caption_length": 500,
    },
}

# Deceptive phrasing patterns that are FORBIDDEN when affiliate links are present
DECEPTIVE_PATTERNS: list[str] = [
    "just found this gem",
    "stumbled upon this",
    "my honest opinion",  # without disclosure
    "not sponsored",      # if affiliate links are present, this is deceptive
    "organic find",
    "randomly found",
]


def validate_disclosure(caption: str, platform: str) -> tuple[bool, str]:
    """Validate a caption has proper affiliate disclosure for a platform.

    Args:
        caption: The caption text to validate.
        platform: Target platform (tiktok, instagram, x, pinterest).

    Returns:
        Tuple of (is_valid, reason).
    """
    rules = PLATFORM_DISCLOSURE_RULES.get(platform)
    if not rules:
        return False, f"Unknown platform: {platform}"

    caption_lower = caption.lower()

    # Check for required disclosure markers
    markers_found = [
        marker for marker in rules["required_markers"]
        if marker.lower() in caption_lower
    ]

    if len(markers_found) < rules["min_markers"]:
        return False, (
            f"Missing affiliate disclosure for {platform}. "
            f"Must include at least one of: {rules['required_markers']}"
        )

    # Check for deceptive phrasing
    for pattern in DECEPTIVE_PATTERNS:
        if pattern.lower() in caption_lower:
            return False, (
                f"Deceptive phrasing detected: '{pattern}'. "
                "Cannot use organic/casual phrasing when affiliate links are present."
            )

    # Check caption length
    if len(caption) > rules["max_caption_length"]:
        return False, (
            f"Caption exceeds {platform} max length: "
            f"{len(caption)} > {rules['max_caption_length']}"
        )

    return True, "Disclosure valid"


def add_disclosure(caption: str, platform: str) -> str:
    """Auto-add disclosure to a caption if missing.

    Args:
        caption: Original caption.
        platform: Target platform.

    Returns:
        Caption with disclosure added (if it was missing).
    """
    is_valid, _ = validate_disclosure(caption, platform)
    if is_valid:
        return caption

    rules = PLATFORM_DISCLOSURE_RULES.get(platform, {})
    default_disclosure = "\n\n#ad #affiliate — This post contains affiliate links. I may earn a commission at no extra cost to you."

    if platform == "x":
        # X has tight char limit — use shortest disclosure
        default_disclosure = " #ad #affiliate"
        if len(caption) + len(default_disclosure) > 280:
            # Truncate caption to fit
            caption = caption[: 280 - len(default_disclosure)]

    caption = caption.rstrip() + default_disclosure

    logger.info("disclosure_auto_added", platform=platform)
    return caption
