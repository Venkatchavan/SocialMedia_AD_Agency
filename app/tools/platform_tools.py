"""Platform Validation Tools — Validate content against platform specs."""

from __future__ import annotations

from typing import Any

from app.policies.platform_policies import PLATFORM_SPECS, validate_media_for_platform


class PlatformValidationTool:
    """CrewAI-compatible tool for validating content against platform specs."""

    name: str = "platform_validation"
    description: str = (
        "Validate media and caption content against the target platform's "
        "specifications (max duration, file size, resolution, caption length). "
        "Call this BEFORE attempting to publish."
    )

    def __init__(self) -> None:
        pass

    def run(self, platform: str, package: dict) -> dict:
        """Execute the tool — validate content for a platform."""
        specs = PLATFORM_SPECS.get(platform)
        if not specs:
            return {
                "is_valid": False,
                "platform": platform,
                "reason": f"Unknown platform: {platform}",
            }

        issues: list[str] = []

        # Check caption length
        caption = package.get("caption", "")
        max_caption = specs.get("max_caption_length", 2200)
        if len(caption) > max_caption:
            issues.append(
                f"Caption too long: {len(caption)} > {max_caption}"
            )

        # Check media if provided
        media_info = package.get("media_info", {})
        if media_info:
            media_result = validate_media_for_platform(media_info, platform)
            if not media_result[0]:
                issues.append(media_result[1])

        return {
            "is_valid": len(issues) == 0,
            "platform": platform,
            "issues": issues,
            "specs": {
                "max_caption_length": max_caption,
                "supports_video": specs.get("supports_video", False),
                "supports_carousel": specs.get("supports_carousel", False),
                "max_video_duration": specs.get("max_video_duration_seconds"),
            },
        }
