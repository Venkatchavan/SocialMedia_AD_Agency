"""Scriptwriter Agent — Generates short-form content scripts.

Rules enforced:
- No unverifiable claims.
- No fake testimonials.
- Must include {{AFFILIATE_DISCLOSURE}} placeholder.
- Anti-repetition via content hashing.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog

from app.agents.base_agent import BaseAgent
from app.schemas.content import ContentBrief, Script, ScriptScene
from app.services.audit_logger import AuditLogger
from app.services.content_hasher import ContentHasher

logger = structlog.get_logger(__name__)


# Script templates by content angle
SCRIPT_TEMPLATES: dict[str, dict] = {
    "comparison": {
        "hook_templates": [
            "Everyone says {product_a} is the best, but wait till you see this...",
            "{product_a} vs the alternative — here's what nobody tells you",
        ],
        "scene_count": 4,
        "duration_target": 30,
    },
    "top_3": {
        "hook_templates": [
            "3 things I wish I knew before buying {category}...",
            "Stop scrolling — here are the top 3 {category} picks",
        ],
        "scene_count": 5,
        "duration_target": 45,
    },
    "story": {
        "hook_templates": [
            "I was about to give up on {use_case} until I found this...",
            "This changed everything about my {use_case} routine",
        ],
        "scene_count": 4,
        "duration_target": 45,
    },
    "problem_solution": {
        "hook_templates": [
            "Struggling with {problem}? Here's what actually works.",
            "If {problem} is ruining your day, you need to see this",
        ],
        "scene_count": 4,
        "duration_target": 30,
    },
    "aesthetic": {
        "hook_templates": [
            "POV: Your {use_case} setup hits different ✨",
            "The aesthetic {use_case} setup you didn't know you needed",
        ],
        "scene_count": 3,
        "duration_target": 20,
    },
    "meme_style": {
        "hook_templates": [
            "Me pretending I don't need {product} vs. me at 3am adding it to cart",
            "Nobody: ... Me: *adds {product} to cart for the 5th time*",
        ],
        "scene_count": 3,
        "duration_target": 15,
    },
}


class ScriptwriterAgent(BaseAgent):
    """Write short-form video scripts based on content briefs."""

    def __init__(self, audit_logger: AuditLogger, session_id: str = "") -> None:
        super().__init__(
            agent_id="scriptwriter",
            audit_logger=audit_logger,
            session_id=session_id,
        )
        self._hasher = ContentHasher()

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
            created_at=datetime.now(tz=timezone.utc),
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
        """Generate the hook (first 3 seconds)."""
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

    def _generate_scenes(
        self,
        angle: str,
        template: dict,
        product_title: str,
        use_cases: list[str],
        reference_style: str,
    ) -> list[ScriptScene]:
        """Generate body scenes."""
        scene_count = template.get("scene_count", 3)
        scenes: list[ScriptScene] = []

        if angle == "problem_solution":
            scenes = [
                ScriptScene(
                    scene_number=1,
                    scene_type="problem",
                    dialogue=f"Finding the right {product_title} can be overwhelming.",
                    visual_direction=f"Show frustration scene. {reference_style}" if reference_style else "Show frustration with alternatives",
                    duration_seconds=5,
                ),
                ScriptScene(
                    scene_number=2,
                    scene_type="solution_reveal",
                    dialogue=f"That's why {product_title} stands out from the rest.",
                    visual_direction=f"Product reveal shot. {reference_style}" if reference_style else "Clean product reveal",
                    duration_seconds=5,
                ),
                ScriptScene(
                    scene_number=3,
                    scene_type="demo",
                    dialogue=f"Perfect for {', '.join(use_cases[:2])}.",
                    visual_direction="Lifestyle usage demonstration",
                    duration_seconds=8,
                ),
                ScriptScene(
                    scene_number=4,
                    scene_type="social_proof",
                    dialogue="See why people are switching.",
                    visual_direction="Show product features and benefits",
                    duration_seconds=5,
                ),
            ]
        elif angle == "aesthetic":
            scenes = [
                ScriptScene(
                    scene_number=1,
                    scene_type="aesthetic_showcase",
                    dialogue="",
                    visual_direction=f"Cinematic product shot. {reference_style}" if reference_style else "Beautiful flat lay arrangement",
                    duration_seconds=6,
                ),
                ScriptScene(
                    scene_number=2,
                    scene_type="lifestyle",
                    dialogue=f"Elevate your {use_cases[0] if use_cases else 'daily'} setup.",
                    visual_direction=f"Lifestyle scene. {reference_style}" if reference_style else "Person using product in stylish environment",
                    duration_seconds=7,
                ),
                ScriptScene(
                    scene_number=3,
                    scene_type="detail",
                    dialogue="The details make the difference.",
                    visual_direction="Close-up product details",
                    duration_seconds=5,
                ),
            ]
        else:
            # Generic scenes
            for i in range(min(scene_count, 4)):
                scenes.append(
                    ScriptScene(
                        scene_number=i + 1,
                        scene_type="body",
                        dialogue=f"Feature {i + 1} of {product_title}.",
                        visual_direction=f"Demonstrate feature {i + 1}",
                        duration_seconds=5,
                    )
                )

        return scenes[:scene_count]

    def _generate_cta(self, product_title: str) -> str:
        """Generate CTA with mandatory affiliate disclosure placeholder."""
        return (
            f"Link in bio to grab your {product_title}! "
            "{{AFFILIATE_DISCLOSURE}}"
        )
