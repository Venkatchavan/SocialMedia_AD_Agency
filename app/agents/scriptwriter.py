"""Scriptwriter Agent — Generates short-form content scripts.

Rules enforced:
- No unverifiable claims.
- No fake testimonials.
- Must include {{AFFILIATE_DISCLOSURE}} placeholder.
- Anti-repetition via content hashing.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import structlog

from app.agents.base_agent import BaseAgent
from app.agents.script_templates import SCRIPT_TEMPLATES, build_template_scenes
from app.schemas.content import Script, ScriptScene
from app.services.audit_logger import AuditLogger
from app.services.content_hasher import ContentHasher
from app.services.llm_client import LLMClient

logger = structlog.get_logger(__name__)


class ScriptwriterAgent(BaseAgent):
    """Write short-form video scripts based on content briefs."""

    def __init__(
        self,
        audit_logger: AuditLogger,
        llm_client: LLMClient | None = None,
        session_id: str = "",
    ) -> None:
        super().__init__(
            agent_id="scriptwriter",
            audit_logger=audit_logger,
            session_id=session_id,
        )
        self._hasher = ContentHasher()
        self._llm = llm_client or LLMClient()

    def execute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Generate a script from a content brief.

        Inputs:
            - brief: dict (ContentBrief data)
            - product_title: str
            - product_category: str
            - use_cases: list[str]
            - reference_style: str (style description for reference integration)

        Returns:
            - script: dict (Script data)
        """
        brief_data = inputs.get("brief", {})
        product_title = inputs.get("product_title", "this product")
        category = inputs.get("product_category", "products")
        use_cases = inputs.get("use_cases", ["everyday use"])
        reference_style = inputs.get("reference_style", "")

        angle = brief_data.get("angle", "problem_solution")
        template = SCRIPT_TEMPLATES.get(angle, SCRIPT_TEMPLATES["problem_solution"])

        # Generate hook
        hook = self._generate_hook(template, product_title, category, use_cases)

        # Generate scenes
        scenes = self._generate_scenes(
            angle, template, product_title, use_cases, reference_style
        )

        # Generate CTA with disclosure placeholder
        cta = self._generate_cta(product_title)

        # Compute content hash for dedup
        full_text = hook + " ".join(s.dialogue for s in scenes) + cta
        content_hash = self._hasher.hash_text(full_text)
        word_count = len(full_text.split())

        script = Script(
            id=str(uuid.uuid4()),
            brief_id=brief_data.get("id", ""),
            hook=hook,
            scenes=scenes,
            cta=cta,
            word_count=word_count,
            estimated_duration_seconds=template["duration_target"],
            content_hash=content_hash,
            version=1,
            status="draft",
            created_at=datetime.now(tz=UTC),
        )

        logger.info(
            "script_generated",
            script_id=script.id,
            angle=angle,
            word_count=word_count,
            duration=template["duration_target"],
        )

        return {"script": script.model_dump(mode="json")}

    def _generate_hook(
        self,
        template: dict,
        product_title: str,
        category: str,
        use_cases: list[str],
    ) -> str:
        """Generate the hook (first 3 seconds). Uses LLM if available."""
        if not self._llm.is_dry_run:
            return self._llm_generate_hook(product_title, category, use_cases)

        # Template fallback
        hook_templates = template.get("hook_templates", [])
        if not hook_templates:
            return f"Check out this amazing {category} find!"

        hook = hook_templates[0]
        hook = hook.replace("{product_a}", product_title)
        hook = hook.replace("{product}", product_title)
        hook = hook.replace("{category}", category)
        hook = hook.replace("{use_case}", use_cases[0] if use_cases else "daily routine")
        hook = hook.replace("{problem}", f"finding the right {category}")
        return hook

    def _llm_generate_hook(
        self, product_title: str, category: str, use_cases: list[str],
    ) -> str:
        """Generate a hook using the LLM."""
        system = (
            "You write viral short-form video hooks (3 seconds max). "
            "Return ONLY the hook text, no quotes, no JSON."
        )
        user = (
            f"Product: {product_title}\nCategory: {category}\n"
            f"Use cases: {', '.join(use_cases)}\n"
            "Write one punchy, scroll-stopping hook."
        )
        try:
            hook = self._llm.complete(
                system_prompt=system,
                user_prompt=user,
                agent_id="scriptwriter",
                temperature=0.8,
                max_tokens=100,
            )
            return hook.strip().strip('"')
        except Exception:
            logger.warning("llm_hook_fallback", product=product_title)
            return f"Stop scrolling — you need to see this {category}!"

    def _generate_scenes(
        self,
        angle: str,
        template: dict,
        product_title: str,
        use_cases: list[str],
        reference_style: str,
    ) -> list[ScriptScene]:
        """Generate body scenes. Uses LLM if available."""
        if not self._llm.is_dry_run:
            return self._llm_generate_scenes(
                angle, template, product_title, use_cases, reference_style,
            )

        return self._template_scenes(
            angle, template, product_title, use_cases, reference_style,
        )

    def _template_scenes(
        self, angle: str, template: dict, product_title: str,
        use_cases: list[str], reference_style: str,
    ) -> list[ScriptScene]:
        """Delegate to extracted template scene builder."""
        return build_template_scenes(angle, template, product_title, use_cases, reference_style)

    def _llm_generate_scenes(
        self,
        angle: str,
        template: dict,
        product_title: str,
        use_cases: list[str],
        reference_style: str,
    ) -> list[ScriptScene]:
        """Generate scenes using the LLM."""
        scene_count = template.get("scene_count", 3)
        system = (
            "You write short-form video scene breakdowns. "
            "Return a JSON array of objects with keys: "
            "scene_number, scene_type, dialogue, visual_direction, "
            "duration_seconds. Never include health/medical claims."
        )
        user = (
            f"Product: {product_title}\nAngle: {angle}\n"
            f"Use cases: {', '.join(use_cases)}\n"
            f"Reference style: {reference_style or 'none'}\n"
            f"Generate exactly {scene_count} scenes."
        )
        try:
            import json
            raw = self._llm.complete(
                system_prompt=system,
                user_prompt=user,
                agent_id="scriptwriter",
                temperature=0.7,
            )
            scenes_data = json.loads(
                raw.strip().strip("`").removeprefix("json").strip()
            )
            return [ScriptScene(**s) for s in scenes_data[:scene_count]]
        except Exception:
            logger.warning("llm_scenes_fallback", angle=angle)
            return self._template_scenes(
                angle, template, product_title, use_cases, reference_style,
            )

    def _generate_cta(self, product_title: str) -> str:
        """Generate CTA with mandatory affiliate disclosure placeholder."""
        return (
            f"Link in bio to grab your {product_title}! "
            "{{AFFILIATE_DISCLOSURE}}"
        )
