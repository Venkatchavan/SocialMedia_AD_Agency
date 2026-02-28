"""Unit tests for Pydantic schemas — validation and serialization."""

from __future__ import annotations

import pytest
from datetime import datetime, timezone

from app.schemas.product import ProductRecord, EnrichedProduct
from app.schemas.reference import Reference, ReferenceBundle
from app.schemas.audit import AuditEvent
from app.schemas.content import CaptionBundle


class TestProductSchemas:
    """Test ProductRecord and EnrichedProduct schemas."""

    def test_valid_product_record(self, sample_product_data: dict):
        """Valid product data should create a ProductRecord."""
        product = ProductRecord(
            id="test-id",
            created_at=datetime.now(tz=timezone.utc),
            affiliate_link="https://amazon.com/dp/B0CTEST123?tag=aff-20",
            **sample_product_data,
        )
        assert product.asin == "B0CTEST123"
        assert product.price == 49.99

    def test_invalid_asin_rejected(self):
        """Invalid ASIN format should be rejected by validator."""
        with pytest.raises(Exception):  # ValidationError
            ProductRecord(
                id="test-id",
                asin="INVALID",  # Too short, should be 10 chars
                title="Test",
                price=10.0,
                category="Test",
                affiliate_link="https://example.com",
                created_at=datetime.now(tz=timezone.utc),
            )

    def test_product_serialization(self, sample_product_data: dict):
        """ProductRecord should serialize to dict correctly."""
        product = ProductRecord(
            id="test-id",
            created_at=datetime.now(tz=timezone.utc),
            affiliate_link="https://amazon.com/dp/B0CTEST123?tag=aff-20",
            **sample_product_data,
        )
        data = product.model_dump(mode="json")
        assert isinstance(data, dict)
        assert data["asin"] == "B0CTEST123"


class TestReferenceSchemas:
    """Test Reference and ReferenceBundle schemas."""

    def test_valid_reference(self):
        """Valid reference data should create a Reference."""
        ref = Reference(
            reference_id="ref-1",
            title="Test aesthetic",
            medium="other",
            reference_type="style_only",
            allowed_usage_mode="Visual style only",
            risk_score=10,
            audience_overlap_score=0.5,
            trending_relevance=0.5,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )
        assert ref.reference_type == "style_only"
        assert ref.risk_score == 10

    def test_reference_bundle(self):
        """ReferenceBundle should contain a list of references."""
        bundle = ReferenceBundle(
            product_id="prod-1",
            references=[],
            created_at=datetime.now(tz=timezone.utc),
        )
        assert bundle.product_id == "prod-1"
        assert len(bundle.references) == 0


class TestAuditSchemas:
    """Test AuditEvent schema."""

    def test_audit_event_hash_input(self):
        """AuditEvent should produce consistent hash input."""
        event = AuditEvent(
            event_id="evt-1",
            agent_id="test_agent",
            action="test_action",
            decision="APPROVED",
            reason="Test reason",
            timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        hash_input = event.to_hash_input()
        assert "test_agent" in hash_input
        assert "test_action" in hash_input


class TestCaptionSchemas:
    """Test CaptionBundle schema."""

    def test_caption_has_disclosure_check(self):
        """CaptionBundle.has_disclosure should detect #ad."""
        bundle = CaptionBundle(
            id="cap-1",
            script_id="script-1",
            captions={
                "tiktok": "Great product! #ad #affiliate",
                "instagram": "Check it out! #ad",
            },
            affiliate_link="https://amazon.com/dp/B0CTEST123",
            created_at=datetime.now(tz=timezone.utc),
        )
        assert bundle.has_disclosure("tiktok")
        assert bundle.has_disclosure("instagram")

    def test_caption_missing_disclosure(self):
        """CaptionBundle.has_disclosure should catch missing disclosure."""
        bundle = CaptionBundle(
            id="cap-2",
            script_id="script-2",
            captions={
                "tiktok": "Great product, buy now!",
            },
            affiliate_link="https://amazon.com/dp/B0CTEST123",
            created_at=datetime.now(tz=timezone.utc),
        )
        assert not bundle.has_disclosure("tiktok")
