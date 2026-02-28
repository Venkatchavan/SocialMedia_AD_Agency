"""Test configuration and shared fixtures."""

from __future__ import annotations

import pytest

from app.services.audit_logger import AuditLogger
from app.services.content_hasher import ContentHasher
from app.services.rights_engine import RightsEngine
from app.services.risk_scorer import RiskScorer


@pytest.fixture
def audit_logger() -> AuditLogger:
    """Provide a fresh AuditLogger for testing."""
    return AuditLogger()


@pytest.fixture
def content_hasher() -> ContentHasher:
    """Provide a ContentHasher instance."""
    return ContentHasher()


@pytest.fixture
def rights_engine(audit_logger: AuditLogger) -> RightsEngine:
    """Provide a RightsEngine instance."""
    return RightsEngine(audit_logger=audit_logger)


@pytest.fixture
def risk_scorer() -> RiskScorer:
    """Provide a RiskScorer instance."""
    return RiskScorer()


@pytest.fixture
def sample_product_data() -> dict:
    """Provide sample product data for testing."""
    return {
        "asin": "B0CTEST123",
        "title": "Test Wireless Headphones",
        "price": 49.99,
        "category": "Electronics",
        "description": "Wireless noise-cancelling headphones",
        "image_urls": ["https://example.com/img1.jpg"],
    }


@pytest.fixture
def sample_reference_licensed() -> dict:
    """Provide a licensed_direct reference for testing."""
    return {
        "reference_id": "ref-1",
        "title": "Licensed Music Track",
        "medium": "music",
        "reference_type": "licensed_direct",
        "allowed_usage_mode": "Full track usage for commercial content",
        "risk_score": 10,
        "license_id": "LIC-001",
        "license_expiry": "2026-12-31",
    }


@pytest.fixture
def sample_reference_style() -> dict:
    """Provide a style_only reference for testing."""
    return {
        "reference_id": "ref-2",
        "title": "Cyberpunk neon aesthetic",
        "medium": "movie",
        "reference_type": "style_only",
        "allowed_usage_mode": "Visual style only, no character likenesses",
        "risk_score": 15,
    }


@pytest.fixture
def sample_reference_risky() -> dict:
    """Provide a risky reference for testing."""
    return {
        "reference_id": "ref-3",
        "title": "Some Trademarked Character™",
        "medium": "tv_show",
        "reference_type": "commentary",
        "allowed_usage_mode": "Commentary use only",
        "risk_score": 75,
    }
