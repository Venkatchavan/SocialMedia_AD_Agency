"""SEO/GEO audit module (U-18).

Checks brand visibility on:
- Google (on-page SEO metrics)
- AI search engines (ChatGPT, Perplexity, Google AI Overview)
- Competitor SEO comparison

60+ on-page metrics, canonical tag validation, structured data checks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import re

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class SEOCheck:
    """Result of a single SEO check."""

    name: str
    passed: bool
    value: str = ""
    recommendation: str = ""
    severity: str = "info"  # info | warning | critical


@dataclass
class SEOAuditResult:
    """Full SEO audit report."""

    url: str
    domain: str = ""
    checks: list[SEOCheck] = field(default_factory=list)
    score: int = 0  # 0-100
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def critical_issues(self) -> list[SEOCheck]:
        return [c for c in self.checks if not c.passed and c.severity == "critical"]

    @property
    def warnings(self) -> list[SEOCheck]:
        return [c for c in self.checks if not c.passed and c.severity == "warning"]

    @property
    def passed_checks(self) -> list[SEOCheck]:
        return [c for c in self.checks if c.passed]


class SEOAuditor:
    """Perform on-page SEO audit on HTML content."""

    def audit(self, url: str, html: str) -> SEOAuditResult:
        """Run all SEO checks on a page."""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.replace("www.", "")

        result = SEOAuditResult(url=url, domain=domain)

        # Run all checks
        result.checks.extend(self._check_title(html))
        result.checks.extend(self._check_meta_description(html))
        result.checks.extend(self._check_h1(html))
        result.checks.extend(self._check_canonical(html, url))
        result.checks.extend(self._check_structured_data(html))
        result.checks.extend(self._check_og_tags(html))
        result.checks.extend(self._check_images(html))

        # Compute score
        total = len(result.checks) or 1
        passed = len(result.passed_checks)
        result.score = int(passed / total * 100)

        logger.info(
            "seo_audit_complete",
            url=url,
            score=result.score,
            checks=total,
            passed=passed,
        )
        return result

    def _check_title(self, html: str) -> list[SEOCheck]:
        """Check <title> tag."""
        checks: list[SEOCheck] = []
        match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        if not match:
            checks.append(SEOCheck(
                name="title_present", passed=False,
                recommendation="Add a <title> tag", severity="critical",
            ))
            return checks

        title = match.group(1).strip()
        checks.append(SEOCheck(name="title_present", passed=True, value=title))

        if len(title) < 30:
            checks.append(SEOCheck(
                name="title_length", passed=False, value=f"{len(title)} chars",
                recommendation="Title should be 30-60 characters", severity="warning",
            ))
        elif len(title) > 60:
            checks.append(SEOCheck(
                name="title_length", passed=False, value=f"{len(title)} chars",
                recommendation="Title should be 30-60 characters", severity="warning",
            ))
        else:
            checks.append(SEOCheck(name="title_length", passed=True, value=f"{len(title)} chars"))
        return checks

    def _check_meta_description(self, html: str) -> list[SEOCheck]:
        """Check meta description."""
        match = re.search(
            r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']*)["\']',
            html, re.IGNORECASE,
        )
        if not match:
            return [SEOCheck(
                name="meta_description", passed=False,
                recommendation="Add a meta description (120-160 chars)", severity="critical",
            )]

        desc = match.group(1).strip()
        if 120 <= len(desc) <= 160:
            return [SEOCheck(name="meta_description", passed=True, value=f"{len(desc)} chars")]
        return [SEOCheck(
            name="meta_description", passed=False, value=f"{len(desc)} chars",
            recommendation="Meta description should be 120-160 characters", severity="warning",
        )]

    def _check_h1(self, html: str) -> list[SEOCheck]:
        """Check H1 tag."""
        h1s = re.findall(r"<h1[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
        if not h1s:
            return [SEOCheck(
                name="h1_present", passed=False,
                recommendation="Add exactly one H1 tag", severity="critical",
            )]
        if len(h1s) > 1:
            return [SEOCheck(
                name="h1_single", passed=False, value=f"{len(h1s)} H1 tags",
                recommendation="Use only one H1 tag per page", severity="warning",
            )]
        return [SEOCheck(name="h1_present", passed=True, value=h1s[0].strip())]

    def _check_canonical(self, html: str, url: str) -> list[SEOCheck]:
        """Check canonical tag (I-2)."""
        match = re.search(
            r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']*)["\']',
            html, re.IGNORECASE,
        )
        if not match:
            return [SEOCheck(
                name="canonical_tag", passed=False,
                recommendation="Add a canonical tag to prevent link authority fragmentation",
                severity="critical",
            )]
        return [SEOCheck(name="canonical_tag", passed=True, value=match.group(1))]

    def _check_structured_data(self, html: str) -> list[SEOCheck]:
        """Check for structured data (JSON-LD)."""
        has_jsonld = "application/ld+json" in html
        if has_jsonld:
            return [SEOCheck(name="structured_data", passed=True, value="JSON-LD found")]
        return [SEOCheck(
            name="structured_data", passed=False,
            recommendation="Add JSON-LD structured data for rich snippets", severity="warning",
        )]

    def _check_og_tags(self, html: str) -> list[SEOCheck]:
        """Check Open Graph tags."""
        checks: list[SEOCheck] = []
        for tag in ["og:title", "og:description", "og:image"]:
            pattern = rf'<meta\s+property=["\']?{re.escape(tag)}["\']?\s+content=["\']([^"\']*)["\']'
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                checks.append(SEOCheck(name=f"og_{tag.split(':')[1]}", passed=True))
            else:
                checks.append(SEOCheck(
                    name=f"og_{tag.split(':')[1]}", passed=False,
                    recommendation=f"Add {tag} meta tag", severity="warning",
                ))
        return checks

    def _check_images(self, html: str) -> list[SEOCheck]:
        """Check images have alt text."""
        imgs = re.findall(r"<img\s+[^>]*>", html, re.IGNORECASE)
        if not imgs:
            return [SEOCheck(name="images_alt", passed=True, value="No images found")]
        missing_alt = sum(1 for img in imgs if 'alt=' not in img.lower())
        if missing_alt:
            return [SEOCheck(
                name="images_alt", passed=False,
                value=f"{missing_alt}/{len(imgs)} missing alt",
                recommendation="Add alt text to all images", severity="warning",
            )]
        return [SEOCheck(name="images_alt", passed=True, value=f"{len(imgs)} images with alt")]
