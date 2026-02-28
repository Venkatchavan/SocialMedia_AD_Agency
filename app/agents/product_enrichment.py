"""Product Enrichment Agent — Enriches product records with context.

Uses LLM to determine category taxonomy, audience persona, and use cases.
No external scraping — only uses product data + LLM reasoning.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import structlog

from app.agents.base_agent import BaseAgent
from app.schemas.product import EnrichedProduct, ProductRecord
from app.services.audit_logger import AuditLogger
from app.services.llm_client import LLMClient

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


class ProductEnrichmentAgent(BaseAgent):
    """Enrich product records with category path, persona, and use cases."""

    def __init__(
        self,
        audit_logger: AuditLogger,
        llm_client: LLMClient | None = None,
        session_id: str = "",
    ) -> None:
        super().__init__(
            agent_id="product_enrichment",
            audit_logger=audit_logger,
            session_id=session_id,
        )
        self._llm = llm_client or LLMClient()

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
            enriched_at=datetime.now(tz=UTC),
        )

        logger.info(
            "product_enriched",
            asin=product.asin,
            category_path=category_path,
            persona=persona,
        )

        return {"enriched_product": enriched.model_dump(mode="json")}

    def _map_category_path(self, product: ProductRecord) -> list[str]:
        """Map product to category taxonomy path. LLM or keyword fallback."""
        if not self._llm.is_dry_run:
            return self._llm_category(product)
        return self._keyword_category(product)

    def _llm_category(self, product: ProductRecord) -> list[str]:
        """Use LLM for category mapping."""
        system = (
            "You classify products into categories. "
            "Return a JSON array of strings representing the category path, "
            "e.g. [\"Electronics\", \"Audio\"]. Max 3 levels."
        )
        user = (
            f"Product: {product.title}\n"
            f"Category hint: {product.category or 'none'}\n"
            f"Price: ${product.price}"
        )
        try:
            raw = self._llm.complete(
                system_prompt=system,
                user_prompt=user,
                agent_id="product_enrichment",
                temperature=0.3,
                max_tokens=100,
            )
            result = json.loads(raw.strip().strip("`").removeprefix("json").strip())
            if isinstance(result, list) and result:
                return [str(x) for x in result[:3]]
        except Exception:
            logger.warning("llm_category_fallback", asin=product.asin)
        return self._keyword_category(product)

    def _keyword_category(self, product: ProductRecord) -> list[str]:
        """Keyword-based category mapping (deterministic fallback)."""
        title_lower = product.title.lower()
        category = product.category or ""
        for top_cat, sub_cats in CATEGORY_TAXONOMY.items():
            if top_cat.lower() in title_lower or top_cat.lower() in category.lower():
                for sub in sub_cats:
                    if sub.lower() in title_lower:
                        return [top_cat, sub]
                return [top_cat]
        return [category] if category else ["General"]

    def _map_persona(self, product: ProductRecord, category_path: list[str]) -> str:
        """Map product to audience persona. LLM or lookup fallback."""
        if not self._llm.is_dry_run:
            return self._llm_persona(product, category_path)
        return self._keyword_persona(category_path)

    def _llm_persona(self, product: ProductRecord, category_path: list[str]) -> str:
        """Use LLM for persona creation."""
        system = (
            "You create concise audience personas for product marketing. "
            "Return ONLY a short persona description (one sentence). "
            "No quotes around it."
        )
        user = (
            f"Product: {product.title}\n"
            f"Category: {' > '.join(category_path)}\n"
            "Describe the ideal buyer persona."
        )
        try:
            persona = self._llm.complete(
                system_prompt=system,
                user_prompt=user,
                agent_id="product_enrichment",
                temperature=0.6,
                max_tokens=80,
            )
            return persona.strip().strip('"')
        except Exception:
            logger.warning("llm_persona_fallback", asin=product.asin)
            return self._keyword_persona(category_path)

    def _keyword_persona(self, category_path: list[str]) -> str:
        """Keyword-based persona mapping (deterministic fallback)."""
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
        """Determine top use cases. LLM or keyword fallback."""
        if not self._llm.is_dry_run:
            return self._llm_use_cases(product, category_path)
        return self._keyword_use_cases(product)

    def _llm_use_cases(
        self, product: ProductRecord, category_path: list[str],
    ) -> list[str]:
        """Use LLM for use case discovery."""
        system = (
            "You identify product use cases for marketing. "
            "Return a JSON array of 3 short use-case strings."
        )
        user = (
            f"Product: {product.title}\n"
            f"Category: {' > '.join(category_path)}\n"
            "List 3 top use cases."
        )
        try:
            raw = self._llm.complete(
                system_prompt=system,
                user_prompt=user,
                agent_id="product_enrichment",
                temperature=0.5,
                max_tokens=150,
            )
            result = json.loads(raw.strip().strip("`").removeprefix("json").strip())
            if isinstance(result, list) and result:
                return [str(x) for x in result[:3]]
        except Exception:
            logger.warning("llm_use_cases_fallback", asin=product.asin)
        return self._keyword_use_cases(product)

    def _keyword_use_cases(self, product: ProductRecord) -> list[str]:
        """Keyword-based use case mapping (deterministic fallback)."""
        title_lower = product.title.lower()
        use_cases: list[str] = []

        # Simple keyword-based use case mapping
        kw_map = {
            "headphone": ["music listening", "video calls", "commute"],
            "keyboard": ["typing", "gaming", "programming"],
            "mouse": ["gaming", "productivity", "design work"],
            "speaker": ["music listening", "party", "home entertainment"],
            "lamp": ["reading", "ambient lighting", "desk setup"],
            "mug": ["coffee drinking", "desk accessory", "gift"],
        }

        for keyword, cases in kw_map.items():
            if keyword in title_lower:
                use_cases.extend(cases[:3])
                break
        if not use_cases:
            use_cases = ["everyday use", "gift idea", "lifestyle upgrade"]
        return use_cases[:3]

    def _calculate_trending_score(self, product: ProductRecord) -> int:
        """Calculate trending relevance score (placeholder)."""
        score = 50
        if product.price > 100:
            score += 10
        if product.price > 300:
            score += 10
        return min(score, 100)
