"""core.utils_urls — URL validation, allowlist, and SSRF protection."""

from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlparse

from core.errors import SSRFError, URLNotAllowedError

# Allowed domain patterns (regex)
_ALLOWED_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^(www\.)?facebook\.com"),
    re.compile(r"^(www\.)?meta\.com"),
    re.compile(r"^(www\.)?tiktok\.com"),
    re.compile(r"^(www\.)?twitter\.com"),
    re.compile(r"^(www\.)?x\.com"),
    re.compile(r"^(www\.)?pinterest\.com"),
    re.compile(r"^api\.apify\.com"),
    re.compile(r"^(www\.)?apify\.com"),
    re.compile(r"^(www\.)?ad-transparency\.google\.com"),
    re.compile(r"^library\.tiktok\.com"),
    re.compile(r"^www\.facebook\.com/ads/library"),
]


def validate_url(url: str) -> str:
    """Return the URL if valid & allowed; raise otherwise."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise SSRFError(f"Blocked non-HTTP scheme: {parsed.scheme}")
    _check_ssrf(parsed.hostname or "")
    if not _matches_allowlist(parsed.hostname or ""):
        raise URLNotAllowedError(f"Domain not in allowlist: {parsed.hostname}")
    return url


def safe_url(url: str) -> bool:
    """Check URL safety without raising."""
    try:
        validate_url(url)
        return True
    except Exception:
        return False


def _check_ssrf(hostname: str) -> None:
    """Block private / loopback IPs."""
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_reserved:
            raise SSRFError(f"Blocked private/loopback IP: {hostname}")
    except ValueError:
        # Not an IP — that's fine, it's a domain
        if hostname in ("localhost", "127.0.0.1", "0.0.0.0", "::1"):
            raise SSRFError(f"Blocked localhost: {hostname}")


def _matches_allowlist(hostname: str) -> bool:
    return any(p.search(hostname) for p in _ALLOWED_PATTERNS)
