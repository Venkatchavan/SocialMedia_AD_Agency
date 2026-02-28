"""Reference Intelligence Agent — Maps products to cultural references.

Rules enforced:
- Every reference MUST have a reference_type tag.
- Default to style_only when uncertain.
- Never suggest using character names/logos without license proof.
- If no safe direct references exist, use style/trope mode.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog

from app.agents.base_agent import BaseAgent
from app.schemas.reference import Reference, ReferenceBundle
from app.services.audit_logger import AuditLogger

logger = structlog.get_logger(__name__)


# Reference knowledge base — maps product categories to cultural references
# In production, this would be a database + LLM-enriched knowledge graph
REFERENCE_KNOWLEDGE: dict[str, list[dict]] = {
    "Electronics": [
        {
            "title": "Cyberpunk neon aesthetic",
            "medium": "movie",
            "reference_type": "style_only",
            "usage_mode": "Neon-lit futuristic visual style. No character likenesses or franchise logos.",
            "risk_score": 15,
            "keywords": ["cyberpunk", "neon", "futuristic", "tech"],
        },
        {
            "title": "Lo-fi study aesthetic",
            "medium": "music",
            "reference_type": "style_only",
            "usage_mode": "Cozy desk setup, warm lighting, animated study scene aesthetic. Generic lo-fi style.",
            "risk_score": 10,
            "keywords": ["lofi", "study", "chill", "aesthetic", "cozy"],
        },
        {
            "title": "Retro synthwave aesthetic",
            "medium": "music",
            "reference_type": "style_only",
            "usage_mode": "80s retro-futuristic visual style with synth colors. No specific band/artist references.",
            "risk_score": 10,
            "keywords": ["synthwave", "retro", "80s", "neon", "retrowave"],
        },
    ],
    "Home & Kitchen": [
        {
            "title": "Cottagecore aesthetic",
            "medium": "other",
            "reference_type": "style_only",
            "usage_mode": "Rustic, pastoral, cozy home aesthetic. Generic style movement.",
            "risk_score": 5,
            "keywords": ["cottagecore", "cozy", "rustic", "pastoral", "homey"],
        },
        {
            "title": "Wabi-sabi philosophy",
            "medium": "other",
            "reference_type": "style_only",
            "usage_mode": "Japanese aesthetic of imperfect beauty. Cultural concept, not IP.",
            "risk_score": 5,
            "keywords": ["wabisabi", "minimalist", "japanese", "imperfection"],
        },
    ],
    "Beauty": [
        {
            "title": "Glass skin K-beauty aesthetic",
            "medium": "other",
            "reference_type": "style_only",
            "usage_mode": "Korean beauty glass skin visual style. Generic beauty trend, not IP.",
            "risk_score": 5,
            "keywords": ["glassskin", "kbeauty", "skincare", "dewy", "glow"],
        },
    ],
    "Books": [
        {
            "title": "Dark academia aesthetic",
            "medium": "other",
            "reference_type": "style_only",
            "usage_mode": "Dark academia visual style: old libraries, vintage books, moody lighting. Generic aesthetic movement.",
            "risk_score": 5,
            "keywords": ["darkacademia", "bookish", "vintage", "literary"],
        },
        {
            "title": "Classic literature (pre-1928)",
            "medium": "novel",
            "reference_type": "public_domain",
            "usage_mode": "Public domain works published before 1928. Full text/imagery usage allowed.",
            "risk_score": 5,
            "keywords": ["classic", "literature", "publicdomain", "vintage"],
        },
    ],
    "General": [
        {
            "title": "Clean minimalist aesthetic",
            "medium": "other",
            "reference_type": "style_only",
            "usage_mode": "Minimal, clean visual style with white space and simple composition.",
            "risk_score": 5,
            "keywords": ["minimalist", "clean", "simple", "modern"],
        },
    ],
}


class ReferenceIntelligenceAgent(BaseAgent):
    """Map enriched products to culturally resonant references."""

    def __init__(self, audit_logger: AuditLogger, session_id: str = "") -> None:
        super().__init__(
            agent_id="reference_intelligence",
            audit_logger=audit_logger,
            session_id=session_id,
        )

    def execute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Map a product to cultural references.

        Inputs:
            - product_id: str
            - category: str
            - primary_persona: str
            - use_cases: list[str]

        Returns:
            - reference_bundle: dict (ReferenceBundle data)
        """
        product_id = inputs.get("product_id", "")
        category = inputs.get("category", "General")
        persona = inputs.get("primary_persona", "")
        use_cases = inputs.get("use_cases", [])

        # Find matching references
        references = self._find_references(category, persona, use_cases)

        # Always ensure we have at least one safe reference
        if not references:
            references = self._get_fallback_references()

        bundle = ReferenceBundle(
            product_id=product_id,
            references=references,
            created_at=datetime.now(tz=timezone.utc),
        )

        logger.info(
            "references_mapped",
            product_id=product_id,
            category=category,
            reference_count=len(references),
            types=[r.reference_type for r in references],
        )

        return {"reference_bundle": bundle.model_dump(mode="json")}

    def _find_references(
        self, category: str, persona: str, use_cases: list[str]
    ) -> list[Reference]:
        """Find relevant references for the product category and persona."""
        references: list[Reference] = []

        # Look up category-specific references
        category_refs = REFERENCE_KNOWLEDGE.get(category, [])
        general_refs = REFERENCE_KNOWLEDGE.get("General", [])

        all_refs = category_refs + general_refs

        for ref_data in all_refs[:5]:  # Max 5 references
            ref = Reference(
                reference_id=str(uuid.uuid4()),
                title=ref_data["title"],
                medium=ref_data["medium"],
                reference_type=ref_data["reference_type"],
                allowed_usage_mode=ref_data["usage_mode"],
                risk_score=ref_data["risk_score"],
                keywords=ref_data.get("keywords", []),
                audience_overlap_score=0.7,  # Placeholder
                trending_relevance=0.5,  # Placeholder
                created_at=datetime.now(tz=timezone.utc),
                updated_at=datetime.now(tz=timezone.utc),
            )
            references.append(ref)

        return references

    def _get_fallback_references(self) -> list[Reference]:
        """Provide safe fallback references when no matches found.

        Uses generic style/trope/aesthetic references only.
        """
        return [
            Reference(
                reference_id=str(uuid.uuid4()),
                title="Clean minimalist aesthetic",
                medium="other",
                reference_type="style_only",
                allowed_usage_mode="Minimal, clean visual style with white space and simple composition.",
                risk_score=5,
                keywords=["minimalist", "clean", "simple"],
                audience_overlap_score=0.5,
                trending_relevance=0.5,
                created_at=datetime.now(tz=timezone.utc),
                updated_at=datetime.now(tz=timezone.utc),
            )
        ]
