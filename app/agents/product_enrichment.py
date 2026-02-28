"""Product Enrichment Agent — Enriches product records with context.

Uses LLM to determine category taxonomy, audience persona, and use cases.
No external scraping — only uses product data + LLM reasoning.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import structlog

from app.agents.base_agent import BaseAgent
from app.schemas.product import EnrichedProduct, ProductRecord
from app.services.audit_logger import AuditLogger

logger = structlog.get_logger(__name__)


# Category taxonomy for mapping
CATEGORY_TAXONOMY: dict[str, list[str]] = {
    "Electronics": ["Audio", "Computers", "Phones", "Cameras", "Gaming", "Wearables"],
    "Home & Kitchen": ["Kitchen", "Bedding", "Furniture", "Decor", "Storage"],
    "Beauty": ["Skincare", "Makeup", "Haircare", "Fragrance", "Tools"],
    "Fashion": ["Men", "Women", "Shoes", "Accessories", "Activewear"],
    "Books": ["Fiction", "Non-Fiction", "Manga", "Self-Help", "Technical"],
    "Sports": ["Fitness", "Outdoor", "Team Sports", "Water Sports", "Cycling"],
    "Toys & Games": ["Board Games", "Action Figures", "Building", "Educational"],
}

# Persona templates
PERSONA_TEMPLATES: list[str] = [
    "college student who loves {interest} and {medium}",
    "young professional into {interest} and {medium}",
    "creative freelancer who enjoys {interest} and {medium}",
    "tech enthusiast who follows {interest} trends",
    "home-focused parent interested in {interest}",
]


class ProductEnrichmentAgent(BaseAgent):
    """Enrich product records with category path, persona, and use cases."""

    def __init__(self, audit_logger: AuditLogger, session_id: str = "") -> None:
        super().__init__(
            agent_id="product_enrichment",
            audit_logger=audit_logger,
            session_id=session_id,
        )

    def execute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Enrich a product record.

        Inputs:
            - product: dict (ProductRecord data)

        Returns:
            - enriched_product: dict (EnrichedProduct data)
        """
        product_data = inputs.get("product", {})
        product = ProductRecord(**product_data)

        # Determine category path
        category_path = self._map_category_path(product)

        # Determine persona
        persona = self._map_persona(product, category_path)

        # Determine use cases
        use_cases = self._map_use_cases(product, category_path)

        # Calculate trending score (placeholder)
        trending_score = self._calculate_trending_score(product)

        enriched = EnrichedProduct(
            product=product,
            category_path=category_path,
            primary_persona=persona,
            use_cases=use_cases,
            trending_score=trending_score,
            enriched_at=datetime.now(tz=timezone.utc),
        )

        logger.info(
            "product_enriched",
            asin=product.asin,
            category_path=category_path,
            persona=persona,
        )

        return {"enriched_product": enriched.model_dump(mode="json")}

    def _map_category_path(self, product: ProductRecord) -> list[str]:
        """Map product to category taxonomy path.

        TODO: Use LLM for more sophisticated mapping.
        For MVP, use keyword matching.
        """
        title_lower = product.title.lower()
        category = product.category or ""

        for top_cat, sub_cats in CATEGORY_TAXONOMY.items():
            if top_cat.lower() in title_lower or top_cat.lower() in category.lower():
                # Find matching sub-category
                for sub in sub_cats:
                    if sub.lower() in title_lower:
                        return [top_cat, sub]
                return [top_cat]

        return [category] if category else ["General"]

    def _map_persona(self, product: ProductRecord, category_path: list[str]) -> str:
        """Map product to an audience persona.

        TODO: Use LLM for nuanced persona creation.
        """
        category = category_path[0] if category_path else "General"

        persona_map: dict[str, str] = {
            "Electronics": "tech-savvy young adult who loves gadgets and digital culture",
            "Home & Kitchen": "home-focused adult who values aesthetics and functionality",
            "Beauty": "beauty enthusiast who follows trends and loves self-care routines",
            "Fashion": "style-conscious individual who curates their look carefully",
            "Books": "avid reader who enjoys deep dives into culture and ideas",
            "Sports": "active lifestyle enthusiast who values performance and health",
        }

        return persona_map.get(category, "curious consumer looking for quality products")

    def _map_use_cases(
        self, product: ProductRecord, category_path: list[str]
    ) -> list[str]:
        """Determine top use cases for the product.

        TODO: Use LLM for context-aware use case discovery.
        """
        title_lower = product.title.lower()
        use_cases: list[str] = []

        # Simple keyword-based use case mapping
        keyword_use_cases: dict[str, list[str]] = {
            "headphone": ["music listening", "video calls", "gaming", "commute"],
            "keyboard": ["typing", "gaming", "programming", "content creation"],
            "mouse": ["gaming", "productivity", "design work"],
            "speaker": ["music listening", "party", "home entertainment"],
            "lamp": ["reading", "ambient lighting", "desk setup"],
            "mug": ["coffee drinking", "desk accessory", "gift"],
        }

        for keyword, cases in keyword_use_cases.items():
            if keyword in title_lower:
                use_cases.extend(cases[:3])
                break

        if not use_cases:
            use_cases = ["everyday use", "gift idea", "lifestyle upgrade"]

        return use_cases[:3]

    def _calculate_trending_score(self, product: ProductRecord) -> int:
        """Calculate trending relevance score.

        TODO: Integrate with trend APIs for real scoring.
        """
        # Placeholder — real implementation checks social trends, search volume
        score = 50  # Baseline

        # Higher price products tend to be more "considered" purchases
        if product.price > 100:
            score += 10
        if product.price > 300:
            score += 10

        return min(score, 100)
