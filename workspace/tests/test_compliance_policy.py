"""tests.test_compliance_policy — Tests for URL validator, policy loader, preflight (§7.2, §11, §13)."""

from __future__ import annotations

import pytest

from compliance.policy_loader import CompliancePolicy, _stricter_merge, load_policy
from compliance.preflight import PreflightError, run_preflight
from compliance.url_validator import URLValidationError, validate_url


# ── URL Validator (§7.2) ──────────────────────────────────────────────────────

class TestURLValidator:
    def test_allows_https_api(self):
        url = "https://api.apify.com/v2/acts"
        assert validate_url(url, allowlist_mode=False) == url

    def test_blocks_file_scheme(self):
        with pytest.raises(URLValidationError, match="Forbidden URL scheme"):
            validate_url("file:///etc/passwd")

    def test_blocks_ftp_scheme(self):
        with pytest.raises(URLValidationError, match="Forbidden URL scheme"):
            validate_url("ftp://internal.server.com/data")

    def test_blocks_localhost(self):
        with pytest.raises(URLValidationError, match="Private hostname"):
            validate_url("http://localhost:8080/api", allowlist_mode=False)

    def test_blocks_private_ip_10(self):
        with pytest.raises(URLValidationError, match="Private IP"):
            validate_url("http://10.0.0.1/secret", allowlist_mode=False)

    def test_blocks_private_ip_192_168(self):
        with pytest.raises(URLValidationError, match="Private IP"):
            validate_url("http://192.168.1.1/admin", allowlist_mode=False)

    def test_blocks_private_ip_172_16(self):
        with pytest.raises(URLValidationError, match="Private IP"):
            validate_url("http://172.16.0.1/internal", allowlist_mode=False)

    def test_blocks_domain_not_on_allowlist(self):
        with pytest.raises(URLValidationError, match="not on allowlist"):
            validate_url("https://evil.example.com/data", allowlist_mode=True)

    def test_allows_extra_domain(self):
        url = "https://custom.api.example.com/data"
        result = validate_url(url, extra_allowed_domains=["custom.api.example.com"], allowlist_mode=True)
        assert result == url

    def test_allows_subdomain_of_allowed(self):
        url = "https://api2.apify.com/v2/acts"
        assert validate_url(url, allowlist_mode=True) == url

    def test_rejects_empty_url(self):
        with pytest.raises(URLValidationError):
            validate_url("")


# ── Policy Loader (§13) ───────────────────────────────────────────────────────

class TestPolicyLoader:
    def test_global_baseline_defaults(self):
        p = CompliancePolicy()
        assert p.retention_days == 90
        assert p.pii_checks_enabled is True
        assert "tiktok" in p.allowed_platforms

    def test_stricter_merge_retention_days(self):
        merged = _stricter_merge({"retention_days": 90}, {"retention_days": 30})
        assert merged["retention_days"] == 30  # shorter = stricter

    def test_stricter_merge_bool_enabled(self):
        merged = _stricter_merge({"pii_checks_enabled": False}, {"pii_checks_enabled": True})
        assert merged["pii_checks_enabled"] is True  # True = stricter

    def test_stricter_merge_list_union(self):
        merged = _stricter_merge({"high_risk_flags": ["health"]}, {"high_risk_flags": ["finance"]})
        assert "health" in merged["high_risk_flags"]
        assert "finance" in merged["high_risk_flags"]

    def test_load_policy_sample_client(self):
        policy = load_policy("sample_client")
        assert policy.retention_days <= 30  # client policy is stricter than 90-day baseline

    def test_load_policy_unknown_workspace_uses_baseline(self):
        policy = load_policy("nonexistent_workspace_xyz")
        assert policy.retention_days == 90


# ── Preflight (§11) ───────────────────────────────────────────────────────────

class TestPreflight:
    def test_sample_client_passes(self):
        report = run_preflight("sample_client", raise_on_error=False)
        assert report.passed is True

    def test_missing_workspace_fails(self):
        report = run_preflight("nonexistent_workspace_xyz", raise_on_error=False)
        assert report.passed is False
        assert any("not found" in e for e in report.errors)

    def test_missing_workspace_raises(self):
        with pytest.raises(PreflightError):
            run_preflight("nonexistent_workspace_xyz", raise_on_error=True)

    def test_report_workspace_id(self):
        report = run_preflight("sample_client", raise_on_error=False)
        assert report.workspace_id == "sample_client"

    def test_summary_contains_status(self):
        report = run_preflight("sample_client", raise_on_error=False)
        assert "PASS" in report.summary() or "FAIL" in report.summary()

    def test_policy_attached_to_report(self):
        report = run_preflight("sample_client", raise_on_error=False)
        assert report.policy is not None
        assert report.policy.pii_checks_enabled is True
