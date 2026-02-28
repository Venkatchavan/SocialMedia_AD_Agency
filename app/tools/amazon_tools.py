"""Amazon Product Lookup Tool — CrewAI tool wrapper.

Wraps AmazonAdapter for use by CrewAI agents.
"""

from __future__ import annotations

from typing import Any


class AmazonLookupTool:
    """CrewAI-compatible tool for Amazon product lookups.

    In production, this extends crewai.tools.BaseTool.
    For MVP, implements the same interface pattern.
    """

    name: str = "amazon_product_lookup"
    description: str = (
        "Look up an Amazon product by ASIN. Returns title, price, category, "
        "description, image URLs, and affiliate link. Only use official Amazon PA-API."
    )

    def __init__(self, amazon_adapter: Any) -> None:
        self._adapter = amazon_adapter

    def run(self, asin: str) -> dict[str, Any]:
        """Execute the tool — look up a product by ASIN."""
        result = self._adapter.lookup_product(asin)
        result["affiliate_link"] = self._adapter.get_affiliate_link(asin)
        return result


class AmazonSearchTool:
    """CrewAI-compatible tool for Amazon product search."""

    name: str = "amazon_product_search"
    description: str = (
        "Search Amazon products by keywords. Returns a list of matching products "
        "with title, price, and ASIN. Uses official Amazon PA-API."
    )

    def __init__(self, amazon_adapter: Any) -> None:
        self._adapter = amazon_adapter

    def run(self, keywords: str, category: str = "", max_results: int = 10) -> list[dict]:
        """Execute the tool — search products by keywords."""
        return self._adapter.search_products(
            keywords=keywords,
            category=category,
            max_results=max_results,
        )
