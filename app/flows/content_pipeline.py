"""Content Pipeline Flow — Main CrewAI Flow for the ad creation pipeline.

This is the master flow that orchestrates the entire content creation pipeline:
  Product Intake → Enrichment → Reference Mapping → Rights Check →
  Content Generation → QA → Platform Adaptation → Publish

Uses @start, @listen, @router decorators for state transitions.
Implements APPROVE / REWRITE / REJECT branching per Agents.md.
"""

from __future__ import annotations

from typing import Any

import structlog

from app.flows.pipeline_state import PipelineState, PipelineStatus
from app.flows.pipeline_steps import PipelineStepsMixin

logger = structlog.get_logger(__name__)


class ContentPipelineFlow(PipelineStepsMixin):
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
        manager_agent: Any = None,
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
        self._manager = manager_agent

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

            # Manager review (LLM-powered quality gate)
            if self._manager is not None:
                state = self._step_manager_review(state)
                if state.status == PipelineStatus.REJECTED:
                    return self._finalize(state)

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

    def _step_manager_review(self, state: PipelineState) -> PipelineState:
        """Step 5b: Manager agent reviews generated content via LLM."""
        logger.info("step_manager_review", pipeline_id=state.pipeline_id)

        review = self._manager.run({
            "action": "review_content",
            "script": state.script,
            "captions": state.caption_bundle.get("captions", {}),
            "product_title": state.product.get("title", ""),
        })

        if review.get("decision") == "REWRITE":
            state.rewrite_count += 1
            if state.rewrite_count > state.max_retries:
                state.status = PipelineStatus.REJECTED
                state.error_message = "Manager review: max rewrites exceeded"
                return state
            logger.info("manager_rewrite", feedback=review.get("feedback", ""))
            return self._step_content_generation(state)

        return state
