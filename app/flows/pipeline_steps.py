"""Heavy pipeline step implementations (mixin).

Extracted from ContentPipelineFlow to keep content_pipeline.py under 250 lines.
These methods access pipeline agents via self._ attributes set by the flow.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import structlog

from app.flows.pipeline_state import PipelineState, PipelineStatus

logger = structlog.get_logger(__name__)


class PipelineStepsMixin:
    """Mixin that provides the heavier pipeline step methods."""

    # Attributes expected from ContentPipelineFlow:
    _rights: Any
    _orchestrator: Any
    _scriptwriter: Any
    _caption: Any
    _qa: Any
    _audit: Any
    _manager: Any

    def _step_rights_check(self, state: PipelineState) -> PipelineState:
        """Step 4: Rights verification (deterministic)."""
        state.status = PipelineStatus.RIGHTS_CHECK
        logger.info("step_rights_check", pipeline_id=state.pipeline_id)

        references = state.reference_bundle.get("references", [])

        for ref in references:
            decision = self._rights.verify(ref)
            if decision.is_rejected():
                state.rights_decision = decision.model_dump(mode="json")
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
                state.rewrite_count += 1
                return self._step_reference_mapping(state)  # type: ignore[attr-defined]

        state.rights_decision = {"decision": "APPROVED", "reason": "All references cleared"}
        return state

    def _step_content_generation(self, state: PipelineState) -> PipelineState:
        """Step 5: Script + caption generation."""
        state.status = PipelineStatus.CONTENT_GENERATION
        logger.info("step_content_generation", pipeline_id=state.pipeline_id)

        enriched = state.enriched_product
        product = enriched.get("product", state.product)
        refs = state.reference_bundle.get("references", [])
        ref_style = refs[0].get("allowed_usage_mode", "") if refs else ""

        script_result = self._scriptwriter.run({
            "brief": {"id": str(uuid.uuid4()), "angle": "problem_solution"},
            "product_title": product.get("title", ""),
            "product_category": enriched.get("category_path", ["General"])[0]
            if enriched.get("category_path") else "General",
            "use_cases": enriched.get("use_cases", []),
            "reference_style": ref_style,
        })
        state.script = script_result.get("script", {})

        caption_result = self._caption.run({
            "hook": state.script.get("hook", ""),
            "value_prop": product.get("title", ""),
            "category": enriched.get("category_path", ["General"])[0]
            if enriched.get("category_path") else "General",
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

        from app.schemas.content import CaptionBundle
        from app.schemas.publish import PlatformPackage

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

        cb = None
        if state.caption_bundle:
            try:
                cb = CaptionBundle(**state.caption_bundle)
            except Exception:
                cb = None

        qa_result = self._qa.check(
            package=package, caption_bundle=cb, session_id=state.session_id,
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
                "action": "route_qa_decision", "qa_status": "REWRITE",
            })
            if not routing.get("should_continue", False):
                state.status = PipelineStatus.REJECTED
                return state
            return self._step_content_generation(state)

        return state

    def _step_publish(self, state: PipelineState) -> PipelineState:
        """Step 7: Platform publishing (placeholder for MVP)."""
        state.status = PipelineStatus.PUBLISHING
        logger.info("step_publish", pipeline_id=state.pipeline_id)

        for platform in state.target_platforms:
            caption = state.caption_bundle.get("captions", {}).get(platform, "")
            state.platform_packages.append({
                "platform": platform,
                "caption": caption,
                "script": state.script,
                "status": "queued",
                "scheduled_at": datetime.now(tz=UTC).isoformat(),
            })

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
        state.completed_at = datetime.now(tz=UTC)

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
            if state.completed_at else None,
        )
        return state
