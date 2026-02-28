"""Platform-specific content policies and technical specifications."""

from __future__ import annotations

# Platform capability and spec matrix
PLATFORM_SPECS: dict[str, dict] = {
    "tiktok": {
        "video": {
            "supported": True,
            "max_duration_seconds": 600,
            "min_duration_seconds": 3,
            "aspect_ratios": ["9:16"],
            "max_file_size_mb": 287,
            "formats": ["mp4", "webm"],
            "resolutions": ["1080x1920"],
        },
        "image": {"supported": False},
        "carousel": {"supported": False},
        "link_in_post": False,
        "link_in_bio": True,
        "hashtag_limit": 8,
        "api": "TikTok Content Posting API",
    },
    "instagram": {
        "video": {
            "supported": True,
            "max_duration_seconds": 90,  # Reels
            "min_duration_seconds": 3,
            "aspect_ratios": ["9:16", "1:1"],
            "max_file_size_mb": 250,
            "formats": ["mp4"],
            "resolutions": ["1080x1920", "1080x1080"],
        },
        "image": {
            "supported": True,
            "max_file_size_mb": 8,
            "formats": ["jpg", "png"],
            "resolutions": ["1080x1080", "1080x1350"],
        },
        "carousel": {"supported": True, "max_items": 10},
        "link_in_post": False,
        "link_in_bio": True,
        "link_in_stories": True,
        "hashtag_limit": 30,
        "api": "Instagram Graph API",
    },
    "x": {
        "video": {
            "supported": True,
            "max_duration_seconds": 140,
            "min_duration_seconds": 1,
            "aspect_ratios": ["16:9", "1:1"],
            "max_file_size_mb": 512,
            "formats": ["mp4"],
            "resolutions": ["1280x720", "1080x1080"],
        },
        "image": {
            "supported": True,
            "max_file_size_mb": 5,
            "formats": ["jpg", "png", "gif"],
        },
        "carousel": {"supported": False},
        "link_in_post": True,
        "hashtag_limit": 5,
        "api": "X API v2",
    },
    "pinterest": {
        "video": {
            "supported": True,
            "max_duration_seconds": 300,
            "min_duration_seconds": 4,
            "aspect_ratios": ["2:3", "9:16", "1:1"],
            "max_file_size_mb": 2048,
            "formats": ["mp4"],
            "resolutions": ["1000x1500"],
        },
        "image": {
            "supported": True,
            "max_file_size_mb": 32,
            "formats": ["jpg", "png"],
            "resolutions": ["1000x1500"],
        },
        "carousel": {"supported": False},
        "link_in_post": True,
        "hashtag_limit": 20,
        "api": "Pinterest API v5",
    },
}


def get_platform_spec(platform: str) -> dict:
    """Get the full spec for a platform."""
    return PLATFORM_SPECS.get(platform, {})


def validate_media_for_platform(
    platform: str,
    media_type: str,  # "video" or "image"
    file_size_mb: float,
    duration_seconds: float = 0,
    resolution: str = "",
) -> tuple[bool, str]:
    """Validate media against platform specs.

    Returns (is_valid, reason).
    """
    spec = PLATFORM_SPECS.get(platform, {}).get(media_type, {})
    if not spec:
        return False, f"Platform '{platform}' does not support {media_type}"

    if not spec.get("supported", False):
        return False, f"{media_type} not supported on {platform}"

    max_size = spec.get("max_file_size_mb", 0)
    if file_size_mb > max_size:
        return False, f"File size {file_size_mb}MB exceeds {platform} max {max_size}MB"

    if media_type == "video":
        max_dur = spec.get("max_duration_seconds", 0)
        min_dur = spec.get("min_duration_seconds", 0)
        if duration_seconds > max_dur:
            return False, f"Duration {duration_seconds}s exceeds {platform} max {max_dur}s"
        if duration_seconds < min_dur:
            return False, f"Duration {duration_seconds}s below {platform} min {min_dur}s"

    return True, "Media valid for platform"
