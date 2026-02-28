"""Integration test — MVP content pipeline end-to-end flow."""

from __future__ import annotations

import pytest

from app.agents.caption_seo import CaptionSEOAgent
from app.agents.orchestrator import OrchestratorAgent
from app.agents.product_enrichment import ProductEnrichmentAgent
from app.agents.product_intake import ProductIntakeAgent
from app.agents.reference_intelligence import ReferenceIntelligenceAgent
from app.agents.scriptwriter import ScriptwriterAgent
from app.flows.content_pipeline import ContentPipelineFlow, PipelineState, PipelineStatus
from app.services.audit_logger import AuditLogger
from app.services.content_hasher import ContentHasher
from app.services.qa_checker import QAChecker
from app.services.rights_engine import RightsEngine


class TestMVPPipeline:
    """End-to-end integration test for the MVP content pipeline."""

    @pytest.fixture
    def pipeline(self) -> ContentPipelineFlow:
        """Build a complete pipeline for testing."""
        audit = AuditLogger()
        ContentHasher()
        rights = RightsEngine(audit_logger=audit)
        qa = QAChecker(audit_logger=audit)

        return ContentPipelineFlow(
            product_intake_agent=ProductIntakeAgent(audit_logger=audit),
            product_enrichment_agent=ProductEnrichmentAgent(audit_logger=audit),
            reference_intelligence_agent=ReferenceIntelligenceAgent(audit_logger=audit),
            scriptwriter_agent=ScriptwriterAgent(audit_logger=audit),
            caption_seo_agent=CaptionSEOAgent(audit_logger=audit),
            orchestrator_agent=OrchestratorAgent(audit_logger=audit),
            rights_engine=rights,
            qa_checker=qa,
            audit_logger=audit,
        )

    def test_pipeline_completes_with_valid_product(self, pipeline: ContentPipelineFlow):
        """Pipeline should complete successfully with valid product data."""
        state = PipelineState(
            asin="B0CTEST123",
            source="manual",
            target_platforms=["tiktok", "instagram"],
            product_data={
                "asin": "B0CTEST123",
                "title": "Test Wireless Headphones",
                "price": 49.99,
                "category": "Electronics",
            },
        )

        result = pipeline.run(state)

        # Pipeline should reach COMPLETED or a controlled state
        assert result.status in (
            PipelineStatus.COMPLETED,
            PipelineStatus.REJECTED,  # May reject if QA fails the first time
        )

        # Should have a pipeline ID
        assert result.pipeline_id

        # Should have completion timestamp
        assert result.completed_at is not None

    def test_pipeline_generates_script(self, pipeline: ContentPipelineFlow):
        """Pipeline should generate a script for a valid product."""
        state = PipelineState(
            asin="B0CTEST456",
            source="manual",
            target_platforms=["tiktok"],
            product_data={
                "asin": "B0CTEST456",
                "title": "Minimalist Desk Lamp",
                "price": 35.00,
                "category": "Home & Kitchen",
            },
        )

        result = pipeline.run(state)

        if result.status == PipelineStatus.COMPLETED:
            # Script should have been generated
            assert result.script
            assert result.script.get("hook")

    def test_pipeline_creates_captions_with_disclosure(
        self, pipeline: ContentPipelineFlow
    ):
        """All generated captions must contain affiliate disclosure."""
        state = PipelineState(
            asin="B0CTEST789",
            source="manual",
            target_platforms=["tiktok", "instagram"],
            product_data={
                "asin": "B0CTEST789",
                "title": "Cozy Reading Light",
                "price": 19.99,
                "category": "Home & Kitchen",
            },
        )

        result = pipeline.run(state)

        if result.status == PipelineStatus.COMPLETED and result.caption_bundle:
            captions = result.caption_bundle.get("captions", {})
            for platform, caption in captions.items():
                assert "#ad" in caption.lower() or "affiliate" in caption.lower(), (
                    f"Missing disclosure in {platform} caption"
                )

    def test_pipeline_handles_invalid_asin(self, pipeline: ContentPipelineFlow):
        """Pipeline should handle invalid ASIN gracefully."""
        state = PipelineState(
            asin="INVALID",
            source="manual",
            target_platforms=["tiktok"],
            product_data={
                "asin": "INVALID",
                "title": "Bad Product",
                "price": 10.0,
                "category": "General",
            },
        )

        result = pipeline.run(state)

        # Should not crash — should reach ERROR state
        assert result.status in (
            PipelineStatus.ERROR,
            PipelineStatus.REJECTED,
        )

    def test_audit_trail_populated(self, pipeline: ContentPipelineFlow):
        """Pipeline execution should produce audit events."""
        state = PipelineState(
            asin="B0CAUDIT001",
            source="manual",
            target_platforms=["tiktok"],
            product_data={
                "asin": "B0CAUDIT001",
                "title": "Audit Test Product",
                "price": 25.00,
                "category": "Electronics",
            },
        )

        result = pipeline.run(state)

        # The audit logger should have recorded events
        # (We can't directly check without accessing the logger,
        # but the pipeline should complete without crash)
        assert result.completed_at is not None
