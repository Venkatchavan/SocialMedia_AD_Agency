"""Tests for self-serve onboarding (U-16)."""

from __future__ import annotations

import pytest

from app.onboarding.url_scanner import URLScanner
from app.onboarding.onboarding_flow import (
    OnboardingOrchestrator,
    OnboardingStep,
    STEP_ORDER,
)


# ── URLScanner ───────────────────────────────────────────────────────

SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Acme Corp - Best Widgets</title>
    <meta name="description" content="Acme Corp makes the best widgets for developers.">
    <meta property="og:title" content="Acme Corp">
    <meta property="og:image" content="https://acme.com/logo.png">
    <meta name="keywords" content="widgets, developer tools, saas">
    <style>body { color: #333333; background: #ffffff; accent: #4A90D9; }</style>
</head>
<body>
    <a href="https://instagram.com/acmecorp">Instagram</a>
    <a href="https://twitter.com/acmecorp">Twitter</a>
    <a href="https://www.linkedin.com/company/acme">LinkedIn</a>
</body>
</html>
"""


class TestURLScanner:
    def test_basic_scan(self):
        scanner = URLScanner()
        profile = scanner.scan("https://www.acme.com")
        assert profile.domain == "acme.com"
        assert profile.brand_name == "Acme"

    def test_scan_html_extracts_title(self):
        scanner = URLScanner()
        profile = scanner.scan_html("https://acme.com", SAMPLE_HTML)
        assert "Acme Corp" in profile.brand_name

    def test_scan_html_extracts_description(self):
        scanner = URLScanner()
        profile = scanner.scan_html("https://acme.com", SAMPLE_HTML)
        assert "widgets" in profile.description.lower()

    def test_scan_html_extracts_logo(self):
        scanner = URLScanner()
        profile = scanner.scan_html("https://acme.com", SAMPLE_HTML)
        assert profile.logo_url == "https://acme.com/logo.png"

    def test_scan_html_extracts_social_links(self):
        scanner = URLScanner()
        profile = scanner.scan_html("https://acme.com", SAMPLE_HTML)
        assert "instagram" in profile.social_links
        assert "x" in profile.social_links
        assert "linkedin" in profile.social_links

    def test_scan_html_extracts_colors(self):
        scanner = URLScanner()
        profile = scanner.scan_html("https://acme.com", SAMPLE_HTML)
        assert len(profile.primary_colors) > 0
        assert any("#" in c for c in profile.primary_colors)

    def test_scan_html_extracts_keywords(self):
        scanner = URLScanner()
        profile = scanner.scan_html("https://acme.com", SAMPLE_HTML)
        assert "widgets" in profile.keywords

    def test_empty_html(self):
        scanner = URLScanner()
        profile = scanner.scan_html("https://blank.com", "")
        assert profile.domain == "blank.com"
        assert profile.brand_name == "Blank"

    def test_infer_brand_name(self):
        scanner = URLScanner()
        assert scanner._infer_brand_name("myshop.io") == "Myshop"


# ── OnboardingOrchestrator ───────────────────────────────────────────

class TestOnboardingOrchestrator:
    def test_start(self):
        orch = OnboardingOrchestrator()
        state = orch.start("ws1", "user1")
        assert state.workspace_id == "ws1"
        assert state.current_step == OnboardingStep.SIGNUP
        assert state.progress_pct == 0

    def test_get_state(self):
        orch = OnboardingOrchestrator()
        orch.start("ws1", "user1")
        state = orch.get_state("ws1")
        assert state is not None
        assert state.user_id == "user1"

    def test_get_state_missing(self):
        orch = OnboardingOrchestrator()
        assert orch.get_state("nonexistent") is None

    def test_complete_step_advances(self):
        orch = OnboardingOrchestrator()
        orch.start("ws1", "user1")
        state = orch.complete_step("ws1", OnboardingStep.SIGNUP)
        assert OnboardingStep.SIGNUP in state.completed_steps
        assert state.current_step == OnboardingStep.BRAND_SCAN
        assert state.progress_pct == 20

    def test_complete_all_steps(self):
        orch = OnboardingOrchestrator()
        orch.start("ws1", "user1")
        for step in STEP_ORDER:
            orch.complete_step("ws1", step)
        state = orch.get_state("ws1")
        assert state.is_complete
        assert state.progress_pct == 100
        assert state.completed_at is not None

    def test_scan_brand_url(self):
        orch = OnboardingOrchestrator()
        orch.start("ws1", "user1")
        profile = orch.scan_brand_url("ws1", "https://www.example.com")
        assert profile.domain == "example.com"

    def test_scan_brand_html(self):
        orch = OnboardingOrchestrator()
        orch.start("ws1", "user1")
        profile = orch.scan_brand_html("ws1", "https://acme.com", SAMPLE_HTML)
        assert "Acme" in profile.brand_name

    def test_connect_platform(self):
        orch = OnboardingOrchestrator()
        orch.start("ws1", "user1")
        assert orch.connect_platform("ws1", "instagram")
        state = orch.get_state("ws1")
        assert "instagram" in state.connected_platforms

    def test_connect_platform_no_state(self):
        orch = OnboardingOrchestrator()
        assert not orch.connect_platform("nonexistent", "instagram")

    def test_complete_step_missing_workspace(self):
        orch = OnboardingOrchestrator()
        with pytest.raises(ValueError):
            orch.complete_step("nonexistent", OnboardingStep.SIGNUP)
