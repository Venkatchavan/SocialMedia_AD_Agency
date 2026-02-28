"""Tests for SEO/GEO audit module (U-18)."""

from __future__ import annotations

from app.analyzers.seo_auditor import SEOAuditor, SEOAuditResult, SEOCheck

GOOD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Acme Corp - Premium Developer Tools</title>
    <meta name="description" content="Acme Corp provides premium developer tools for modern engineering teams. Build faster, ship better code today.">
    <meta property="og:title" content="Acme Corp">
    <meta property="og:description" content="Premium developer tools">
    <meta property="og:image" content="https://acme.com/og.png">
    <link rel="canonical" href="https://acme.com/">
    <script type="application/ld+json">{"@type": "Organization"}</script>
</head>
<body>
    <h1>Acme Corp</h1>
    <img src="hero.png" alt="Hero image">
</body>
</html>
"""

BAD_HTML = """
<html>
<head></head>
<body>
    <img src="logo.png">
    <img src="banner.png">
</body>
</html>
"""


class TestSEOAuditor:
    def test_good_page_high_score(self):
        auditor = SEOAuditor()
        result = auditor.audit("https://acme.com", GOOD_HTML)
        assert result.score >= 80
        assert len(result.critical_issues) == 0

    def test_bad_page_low_score(self):
        auditor = SEOAuditor()
        result = auditor.audit("https://bad.com", BAD_HTML)
        assert result.score < 50
        assert len(result.critical_issues) > 0

    def test_title_check(self):
        auditor = SEOAuditor()
        result = auditor.audit("https://acme.com", GOOD_HTML)
        title_checks = [c for c in result.checks if "title" in c.name]
        assert any(c.passed for c in title_checks)

    def test_missing_title(self):
        auditor = SEOAuditor()
        result = auditor.audit("https://x.com", "<html><head></head></html>")
        title_checks = [c for c in result.checks if c.name == "title_present"]
        assert len(title_checks) == 1
        assert not title_checks[0].passed

    def test_canonical_check(self):
        auditor = SEOAuditor()
        result = auditor.audit("https://acme.com", GOOD_HTML)
        canonical = [c for c in result.checks if c.name == "canonical_tag"]
        assert len(canonical) == 1
        assert canonical[0].passed

    def test_missing_canonical(self):
        auditor = SEOAuditor()
        result = auditor.audit("https://bad.com", BAD_HTML)
        canonical = [c for c in result.checks if c.name == "canonical_tag"]
        assert len(canonical) == 1
        assert not canonical[0].passed
        assert canonical[0].severity == "critical"

    def test_structured_data(self):
        auditor = SEOAuditor()
        result = auditor.audit("https://acme.com", GOOD_HTML)
        sd = [c for c in result.checks if c.name == "structured_data"]
        assert sd[0].passed

    def test_h1_check(self):
        auditor = SEOAuditor()
        result = auditor.audit("https://acme.com", GOOD_HTML)
        h1 = [c for c in result.checks if c.name == "h1_present"]
        assert h1[0].passed

    def test_multiple_h1_warning(self):
        html = "<html><body><h1>First</h1><h1>Second</h1></body></html>"
        auditor = SEOAuditor()
        result = auditor.audit("https://x.com", html)
        h1 = [c for c in result.checks if c.name == "h1_single"]
        assert len(h1) == 1
        assert not h1[0].passed

    def test_og_tags(self):
        auditor = SEOAuditor()
        result = auditor.audit("https://acme.com", GOOD_HTML)
        og = [c for c in result.checks if c.name.startswith("og_")]
        assert len(og) == 3
        assert all(c.passed for c in og)

    def test_images_alt(self):
        auditor = SEOAuditor()
        result = auditor.audit("https://acme.com", GOOD_HTML)
        img = [c for c in result.checks if c.name == "images_alt"]
        assert img[0].passed

    def test_images_missing_alt(self):
        auditor = SEOAuditor()
        result = auditor.audit("https://bad.com", BAD_HTML)
        img = [c for c in result.checks if c.name == "images_alt"]
        assert not img[0].passed

    def test_audit_result_properties(self):
        result = SEOAuditResult(url="https://x.com")
        result.checks = [
            SEOCheck(name="a", passed=True),
            SEOCheck(name="b", passed=False, severity="warning"),
            SEOCheck(name="c", passed=False, severity="critical"),
        ]
        assert len(result.passed_checks) == 1
        assert len(result.warnings) == 1
        assert len(result.critical_issues) == 1
