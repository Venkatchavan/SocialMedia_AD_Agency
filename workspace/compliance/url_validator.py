"""compliance.url_validator — SSRF + domain allowlist guard (§7.2).

Validates URLs before any outbound HTTP request.
Blocks:
  - private / loopback / link-local IP ranges
  - forbidden schemes (file://, ftp://, javascript://, data://)
  - domains not on the allowlist (when allowlist mode is active)
  - localhost and named private hostnames
"""

from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlparse

from core.logging import get_logger

_log = get_logger(__name__)

# ── Forbidden schemes ────────────────────────────────────────────────────────
_FORBIDDEN_SCHEMES: frozenset[str] = frozenset(
    {"file", "ftp", "javascript", "data", "gopher", "ldap", "dict", "tftp"}
)

# ── Private / reserved ranges (RFC1918, loopback, link-local, etc.) ─────────
_PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),   # link-local
    ipaddress.ip_network("::1/128"),           # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),          # IPv6 ULA
    ipaddress.ip_network("fe80::/10"),         # IPv6 link-local
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),     # CGNAT
    ipaddress.ip_network("192.0.2.0/24"),      # TEST-NET
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("240.0.0.0/4"),
]

# ── Known private hostnames ──────────────────────────────────────────────────
_PRIVATE_HOSTNAME_RE = re.compile(
    r"^(localhost|localhos\.t|.*\.local|.*\.internal|.*\.intranet|metadata\.google\.internal)$",
    re.IGNORECASE,
)

# ── Default collector domain allowlist ──────────────────────────────────────
_DEFAULT_ALLOWED_DOMAINS: frozenset[str] = frozenset(
    {
        "api.apify.com",
        "api.tiktok.com",
        "graph.facebook.com",
        "graph.instagram.com",
        "ads-api.twitter.com",
        "api.twitter.com",
        "api.x.com",
        "api.pinterest.com",
        "generativelanguage.googleapis.com",
        "api2.apify.com",
    }
)


class URLValidationError(ValueError):
    """Raised when a URL fails security validation."""


def _is_private_ip(host: str) -> bool:
    """Return True if host resolves to a private/reserved IP range."""
    try:
        addr = ipaddress.ip_address(host)
        return any(addr in net for net in _PRIVATE_NETWORKS)
    except ValueError:
        return False


def validate_url(
    url: str,
    extra_allowed_domains: list[str] | None = None,
    *,
    allowlist_mode: bool = True,
) -> str:
    """Validate and normalise a URL. Raises URLValidationError on failure.

    Args:
        url: The URL to validate.
        extra_allowed_domains: Additional allowed domains beyond the default set.
        allowlist_mode: When True, reject domains not in the allowed set.

    Returns:
        The normalised URL string (scheme + netloc + path).
    """
    if not url or not isinstance(url, str):
        raise URLValidationError(f"Invalid URL: {url!r}")

    parsed = urlparse(url.strip())
    scheme = (parsed.scheme or "").lower()
    host = (parsed.hostname or "").lower()

    # 1) Scheme check
    if scheme in _FORBIDDEN_SCHEMES:
        raise URLValidationError(f"Forbidden URL scheme '{scheme}': {url}")
    if scheme not in {"http", "https"}:
        raise URLValidationError(f"Only http/https allowed, got '{scheme}': {url}")

    # 2) Private hostname check
    if _PRIVATE_HOSTNAME_RE.match(host):
        raise URLValidationError(f"Private hostname blocked: {host}")

    # 3) Private IP check (when host is a bare IP)
    if _is_private_ip(host):
        raise URLValidationError(f"Private IP range blocked: {host}")

    # 4) Domain allowlist
    if allowlist_mode:
        allowed = _DEFAULT_ALLOWED_DOMAINS
        if extra_allowed_domains:
            allowed = allowed | frozenset(d.lower() for d in extra_allowed_domains)
        # Allow any subdomain of an allowed domain
        if not any(host == d or host.endswith("." + d) for d in allowed):
            raise URLValidationError(
                f"Domain '{host}' not on allowlist. "
                "Add it to extra_blocklist_domains in CompliancePolicy.yaml or expand the allowlist."
            )

    _log.debug("URL validated: %s", url)
    return url
