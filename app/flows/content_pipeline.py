"""Content Pipeline Flow — Main CrewAI Flow for the ad creation pipeline.

This is the master flow that orchestrates the entire content creation pipeline:
  Product Intake → Enrichment → Reference Mapping → Rights Check →
  Content Generation → QA → Platform Adaptation → Publish

Uses @start, @listen, @router decorators for state transitions.
Implements APPROVE / REWRITE / REJECT branching per Agents.md.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Pipeline state
# ---------------------------------------------------------------------------


class PipelineStatus(str, Enum):
    """Pipeline execution status."""

    PENDING = "pending"
    INTAKE = "intake"
    ENRICHMENT = "enrichment"
    REFERENCE_MAPPING = "reference_mapping"
    RIGHTS_CHECK = "rights_check"
    CONTENT_GENERATION = "content_generation"
    QA = "qa"
    PLATFORM_ADAPTATION = "platform_adaptation"
    PUBLISHING = "publishing"
    COMPLETED = "completed"
    REJECTED = "rejected"
    ERROR = "error"


class PipelineState(BaseModel):
    """Shared state object that flows through the pipeline."""

    pipeline_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: PipelineStatus = PipelineStatus.PENDING
    session_id: str = ""

    # Inputs
    asin: str = ""
    source: str = "manual"
    product_data: dict = Field(default_factory=dict)
    target_platforms: list[str] = Field(default_factory=lambda: ["tiktok", "instagram"])

    # Stage outputs
    product: dict = Field(default_factory=dict)
    enriched_product: dict = Field(default_factory=dict)
    reference_bundle: dict = Field(default_factory=dict)
    rights_decision: dict = Field(default_factory=dict)
    script: dict = Field(default_factory=dict)
    caption_bundle: dict = Field(default_factory=dict)
    qa_decision: dict = Field(default_factory=dict)
    platform_packages: list[dict] = Field(default_factory=list)
    publish_results: list[dict] = Field(default_factory=list)

    # Control flow
    rewrite_count: int = 0
    max_retries: int = 3
    error_message: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    completed_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Content Pipeline Flow
# ---------------------------------------------------------------------------


class ContentPipelineFlow:
    """Main content pipeline flow.

    This implements the CrewAI Flow pattern with explicit state transitions.
    In production, this would use @start / @listen / @router decorators
    from crewai.flow. For the MVP scaffold, we implement the pattern manually
    to keep dependencies minimal and enable testing.
    """

    def __init__(
        self,
        product_intake_agent: Any,
        product_enrichment_agent: Any,
        reference_intelligence_agent: Any,
        scriptwriter_agent: Any,
        caption_seo_agent: Any,
        orchestrator_agent: Any,
        rights_engine: Any,
        qa_checker: Any,
        audit_logger: Any,
    ) -> None:
        self._intake = product_intake_agent
        self._enrichment = product_enrichment_agent
        self._reference = reference_intelligence_agent
        self._scriptwriter = scriptwriter_agent
        self._caption = caption_seo_agent
        self._orchestrator = orchestrator_agent
        self._rights = rights_engine
        self._qa = qa_checker
        self._audit = audit_logger

    def run(self, state: PipelineState) -> PipelineState:
        """Execute the full pipeline.

        This is the main entry point. It drives the state machine.
        """
        logger.info(
            "pipeline_started",
            pipeline_id=state.pipeline_id,
            asin=state.asin,
            platforms=state.target_platforms,
        )

        try:
            state = self._step_intake(state)
            state = self._step_enrichment(state)
            state = self._step_reference_mapping(state)
            state = self._step_rights_check(state)

            # APPROVE/REWRITE/REJECT branching
            if state.status == PipelineStatus.REJECTED:
                return self._finalize(state)

            state = self._step_content_generation(state)
            state = self._step_qa(state)

            # QA branching
            if state.status == PipelineStatus.REJECTED:
                return self._finalize(state)

            state = self._step_publish(state)
            return self._finalize(state)

        except Exception as e:
            state.status = PipelineStatus.ERROR
            state.error_message = str(e)
            logger.error(
                "pipeline_error",
                pipeline_id=state.pipeline_id,
                error=str(e),
            )
            return self._finalize(state)

    # -----------------------------------------------------------------------
    # Pipeline steps
    # -----------------------------------------------------------------------

    def _step_intake(self, state: PipelineState) -> PipelineState:
        """Step 1: Product intake."""
        state.status = PipelineStatus.INTAKE
        logger.info("step_intake", pipeline_id=state.pipeline_id)

        result = self._intake.run({
            "source": state.source,
            "asin": state.asin,
            **state.product_data,
        })

        products = result.get("products", [])
        if not products:
            state.status = PipelineStatus.ERROR
            state.error_message = "No products ingested"
            return state

        state.product = products[0]
        return state

    def _step_enrichment(self, state: PipelineState) -> PipelineState:
        """Step 2: Product enrichment."""
        state.status = PipelineStatus.ENRICHMENT
        logger.info("step_enrichment", pipeline_id=state.pipeline_id)

        result = self._enrichment.run({"product": state.product})
        state.enriched_product = result.get("enriched_product", {})
        return state

    def _step_reference_mapping(self, state: PipelineState) -> PipelineState:
        """Step 3: Reference intelligence mapping."""
        state.status = PipelineStatus.REFERENCE_MAPPING
        logger.info("step_reference_mapping", pipeline_id=state.pipeline_id)

        enriched = state.enriched_product
        result = self._reference.run({
            "product_id": state.product.get("id", ""),
            "category": enriched.get("category_path", ["General"])[0]
            if enriched.get("category_path")
            else "General",
            "primary_persona": enriched.get("primary_persona", ""),
            "use_cases": enriched.get("use_cases", []),
        })

        state.reference_bundle = result.get("reference_bundle", {})
        return state

    def _step_rights_check(self, state: PipelineState) -> PipelineState:
        """Step 4: Rights verification (deterministic)."""
        state.status = PipelineStatus.RIGHTS_CHECK
        logger.info("step_rights_check", pipeline_id=state.pipeline_id)

        references = state.reference_bundle.get("references", [])

        # Check each reference
        for ref in references:
            decision = self._rights.verify(ref)
            if decision.is_rejected():
                state.rights_decision = decision.model_dump(mode="json")

                # Route through orchestrator
                routing = self._orchestrator.run({
                    "action": "route_rights_decision",
                    "compliance_status": "REJECT",
                    "reason": decision.reason,
                })
                if not routing.get("should_continue", False):
                    state.status = PipelineStatus.REJECTED
                    state.error_message = routing.get("reason", "Rights rejected")
                    return state

            elif decision.is_rewrite():
                state.rights_decision = decision.model_dump(mode="json")

                routing = self._orchestrator.run({
                    "action": "route_rights_decision",
                    "compliance_status": "REWRITE",
                })
                if not routing.get("should_continue", False):
                    state.status = PipelineStatus.REJECTED
                    return state

                # Rewrite: re-run reference mapping with fewer refs
                state.rewrite_count += 1
                return self._step_reference_mapping(state)

        # All references approved
        state.rights_decision = {"decision": "APPROVED", "reason": "All references cleared"}
        return state

    def _step_content_generation(self, state: PipelineState) -> PipelineState:
        """Step 5: Script + caption generation."""
        state.status = PipelineStatus.CONTENT_GENERATION
        logger.info("step_content_generation", pipeline_id=state.pipeline_id)

        enriched = state.enriched_product
        product = enriched.get("product", state.product)

        # Get reference style info
        refs = state.reference_bundle.get("references", [])
        ref_style = refs[0].get("allowed_usage_mode", "") if refs else ""

        # Generate script
        script_result = self._scriptwriter.run({
            "brief": {
                "id": str(uuid.uuid4()),
                "angle": "problem_solution",
            },
            "product_title": product.get("title", ""),
            "product_category": enriched.get("category_path", ["General"])[0]
            if enriched.get("category_path")
            else "General",
            "use_cases": enriched.get("use_cases", []),
            "reference_style": ref_style,
        })
        state.script = script_result.get("script", {})

        # Generate captions
        caption_result = self._caption.run({
            "hook": state.script.get("hook", ""),
            "value_prop": product.get("title", ""),
            "category": enriched.get("category_path", ["General"])[0]
            if enriched.get("category_path")
            else "General",
            "affiliate_link": product.get("affiliate_link", ""),
            "target_platforms": state.target_platforms,
            "script_id": state.script.get("id", ""),
        })
        state.caption_bundle = caption_result.get("caption_bundle", {})

        return state

    def _step_qa(self, state: PipelineState) -> PipelineState:
        """Step 6: Quality assurance check (deterministic)."""
        state.status = PipelineStatus.QA
        logger.info("step_qa", pipeline_id=state.pipeline_id)

        from app.schemas.publish import PlatformPackage
        from app.schemas.content import CaptionBundle

        # Build a synthetic PlatformPackage for QA checking
        captions = state.caption_bundle.get("captions", {})
        first_platform = state.target_platforms[0] if state.target_platforms else "tiktok"
        first_caption = captions.get(first_platform, "")

        package = PlatformPackage(
            id=str(uuid.uuid4()),
            platform=first_platform,
            caption=first_caption,
            content_hash=state.script.get("content_hash", ""),
            compliance_status=state.rights_decision.get("decision", ""),
            media_path="placeholder.mp4",
            signed_media_url="https://placeholder.example.com/media",
        )

        # Build CaptionBundle if data available
        cb = None
        if state.caption_bundle:
            try:
                cb = CaptionBundle(**state.caption_bundle)
            except Exception:
                cb = None

        qa_result = self._qa.check(
            package=package,
            caption_bundle=cb,
            session_id=state.session_id,
        )

        state.qa_decision = {
            "status": qa_result.decision,
            "checks": [c.model_dump() for c in qa_result.checks],
            "reason": qa_result.reason,
        }

        if qa_result.decision == "REJECT":
            routing = self._orchestrator.run({
                "action": "route_qa_decision",
                "qa_status": "REJECT",
                "reason": qa_result.reason if hasattr(qa_result, "reason") else "",
            })
            if not routing.get("should_continue", False):
                state.status = PipelineStatus.REJECTED
                state.error_message = routing.get("reason", "QA rejected")
                return state

        elif qa_result.decision == "REWRITE":
            routing = self._orchestrator.run({
                "action": "route_qa_decision",
                "qa_status": "REWRITE",
            })
            if not routing.get("should_continue", False):
                state.status = PipelineStatus.REJECTED
                return state
            # Re-run content generation
            return self._step_content_generation(state)

        return state

    def _step_publish(self, state: PipelineState) -> PipelineState:
        """Step 7: Platform publishing (placeholder for MVP)."""
        state.status = PipelineStatus.PUBLISHING
        logger.info("step_publish", pipeline_id=state.pipeline_id)

        # MVP: Create platform packages without actual publishing
        for platform in state.target_platforms:
            caption = state.caption_bundle.get("captions", {}).get(platform, "")
            package = {
                "platform": platform,
                "caption": caption,
                "script": state.script,
                "status": "queued",
                "scheduled_at": datetime.now(tz=timezone.utc).isoformat(),
            }
            state.platform_packages.append(package)

        logger.info(
            "packages_queued",
            pipeline_id=state.pipeline_id,
            platforms=state.target_platforms,
        )
        return state

    def _finalize(self, state: PipelineState) -> PipelineState:
        """Finalize pipeline execution."""
        if state.status not in (PipelineStatus.REJECTED, PipelineStatus.ERROR):
            state.status = PipelineStatus.COMPLETED

        state.completed_at = datetime.now(tz=timezone.utc)

        self._audit.log(
            agent_id="pipeline",
            action="pipeline_finalized",
            decision=state.status.value.upper(),
            reason=state.error_message or "Pipeline completed successfully",
            input_data={"asin": state.asin, "pipeline_id": state.pipeline_id},
            output_data={
                "status": state.status.value,
                "platforms": state.target_platforms,
                "rewrite_count": state.rewrite_count,
            },
            session_id=state.session_id,
        )

        logger.info(
            "pipeline_finalized",
            pipeline_id=state.pipeline_id,
            status=state.status.value,
            duration=(state.completed_at - state.created_at).total_seconds()
            if state.completed_at
            else None,
        )

        return state
