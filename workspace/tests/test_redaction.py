"""tests.test_redaction — Validate PII detection and redaction."""

from __future__ import annotations

import pytest

from qa.pii_redaction import has_pii, redact, scan_texts


class TestHasPII:
    def test_email_detected(self):
        assert has_pii("Contact me at john@example.com") is True

    def test_phone_detected(self):
        assert has_pii("Call 555-123-4567 now") is True

    def test_handle_detected(self):
        assert has_pii("Follow @johndoe for more") is True

    def test_social_url_detected(self):
        assert has_pii("Visit https://twitter.com/johndoe") is True

    def test_name_indicator_detected(self):
        assert has_pii("My name is John and I love it") is True

    def test_clean_text(self):
        assert has_pii("Great product, works well!") is False

    def test_empty_string(self):
        assert has_pii("") is False


class TestRedact:
    def test_email_redacted(self):
        result = redact("Email me at test@example.com please")
        assert "[REDACTED-EMAIL]" in result
        assert "test@example.com" not in result

    def test_handle_redacted(self):
        result = redact("Thank you @username!")
        assert "[REDACTED-HANDLE]" in result
        assert "@username" not in result

    def test_clean_unchanged(self):
        text = "This product is amazing"
        assert redact(text) == text


class TestScanTexts:
    def test_mixed_batch(self):
        texts = [
            "Clean text here",
            "Email me at a@b.com",
            "Also clean",
            "Follow @handle",
        ]
        found, indices = scan_texts(texts)
        assert found is True
        assert 1 in indices
        assert 3 in indices
        assert 0 not in indices

    def test_all_clean(self):
        texts = ["Clean one", "Clean two"]
        found, indices = scan_texts(texts)
        assert found is False
        assert indices == []
