"""URL scanner — auto-extract brand information from a website URL.

Scans: title, meta description, OG tags, logo, colors, fonts, taglines.
Produces a BrandProfile that seeds the Brand Book.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class BrandProfile:
    """Extracted brand profile from URL scanning."""

    url: str
    domain: str = ""
    brand_name: str = ""
    tagline: str = ""
    description: str = ""
    logo_url: str = ""
    primary_colors: list[str] = field(default_factory=list)
    social_links: dict[str, str] = field(default_factory=dict)
    industry: str = ""
    keywords: list[str] = field(default_factory=list)
    raw_meta: dict[str, str] = field(default_factory=dict)


class URLScanner:
    """Scan a brand URL and extract profile information.

    NOTE: Actual HTML fetching requires `httpx`.
    This class parses pre-fetched HTML or uses mock data for testing.
    """

    def scan(self, url: str) -> BrandProfile:
        """Scan a URL and return extracted brand profile."""
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        domain = domain.replace("www.", "")

        logger.info("url_scan_start", url=url, domain=domain)

        profile = BrandProfile(
            url=url,
            domain=domain,
            brand_name=self._infer_brand_name(domain),
        )
        return profile

    def scan_html(self, url: str, html: str) -> BrandProfile:
        """Parse pre-fetched HTML to extract brand information."""
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        domain = domain.replace("www.", "")

        profile = BrandProfile(url=url, domain=domain)
        profile.brand_name = self._extract_title(html) or self._infer_brand_name(domain)
        profile.description = self._extract_meta(html, "description")
        profile.tagline = self._extract_meta(html, "og:title") or profile.brand_name
        profile.logo_url = self._extract_meta(html, "og:image")
        profile.social_links = self._extract_social_links(html)
        profile.primary_colors = self._extract_colors(html)
        profile.keywords = self._extract_keywords(html)
        profile.raw_meta = {
            "title": self._extract_title(html),
            "description": profile.description,
            "og:image": profile.logo_url,
        }

        logger.info(
            "url_scan_complete",
            domain=domain,
            brand_name=profile.brand_name,
            colors_found=len(profile.primary_colors),
        )
        return profile

    def _infer_brand_name(self, domain: str) -> str:
        """Infer brand name from domain (e.g., 'acme.com' → 'Acme')."""
        name = domain.split(".")[0] if "." in domain else domain
        return name.capitalize()

    def _extract_title(self, html: str) -> str:
        """Extract <title> text."""
        match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else ""

    def _extract_meta(self, html: str, name: str) -> str:
        """Extract content from <meta name='...'> or <meta property='...'>."""
        patterns = [
            rf'<meta\s+(?:name|property)=["\']?{re.escape(name)}["\']?\s+content=["\']([^"\']*)["\']',
            rf'<meta\s+content=["\']([^"\']*)["\']?\s+(?:name|property)=["\']?{re.escape(name)}["\']',
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""

    def _extract_social_links(self, html: str) -> dict[str, str]:
        """Extract social media links from HTML."""
        socials: dict[str, str] = {}
        platforms = {
            "instagram.com": "instagram",
            "tiktok.com": "tiktok",
            "twitter.com": "x",
            "x.com": "x",
            "linkedin.com": "linkedin",
            "youtube.com": "youtube",
            "pinterest.com": "pinterest",
            "facebook.com": "facebook",
        }
        urls = re.findall(r'href=["\']?(https?://[^"\'>\s]+)["\']?', html, re.IGNORECASE)
        for u in urls:
            for domain, platform in platforms.items():
                if domain in u and platform not in socials:
                    socials[platform] = u
        return socials

    def _extract_colors(self, html: str) -> list[str]:
        """Extract hex color codes from inline styles."""
        colors = re.findall(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b", html)
        # Deduplicate and return up to 5 unique colors
        seen: set[str] = set()
        unique: list[str] = []
        for c in colors:
            c_lower = c.lower()
            if c_lower not in seen:
                seen.add(c_lower)
                unique.append(f"#{c_lower}")
            if len(unique) >= 5:
                break
        return unique

    def _extract_keywords(self, html: str) -> list[str]:
        """Extract keywords from meta tag."""
        kw_str = self._extract_meta(html, "keywords")
        if not kw_str:
            return []
        return [k.strip() for k in kw_str.split(",") if k.strip()]
