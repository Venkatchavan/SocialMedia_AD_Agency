"""Amazon Product Advertising API adapter.

Uses official Amazon PA-API 5.0.
NEVER scrapes Amazon pages.
"""

from __future__ import annotations

from typing import Any

import structlog

from app.services.secrets import SecretsManager
from app.services.audit_logger import AuditLogger

logger = structlog.get_logger(__name__)


class AmazonAdapter:
    """Amazon Product Advertising API (PA-API 5.0) adapter."""

    def __init__(
        self,
        secrets_manager: SecretsManager,
        audit_logger: AuditLogger,
    ) -> None:
        self._secrets = secrets_manager
        self._audit = audit_logger

    def lookup_product(self, asin: str) -> dict[str, Any]:
        """Look up a product by ASIN.

        TODO: Implement actual PA-API 5.0 calls using amazon-paapi SDK.

        API flow:
          1. GetItems operation with ItemIds=[asin]
          2. Parse ItemsResult -> Items -> Item

        Returns dict with product data.
        """
        self._secrets.get_platform_credentials("amazon")
        # credentials: AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY, AMAZON_PARTNER_TAG

        logger.info("amazon_lookup", asin=asin)

        self._audit.log(
            agent_id="amazon_adapter",
            action="product_lookup",
            decision="EXECUTED",
            reason=f"PA-API lookup for ASIN {asin}",
            input_data={"asin": asin},
        )

        # MVP: Placeholder response
        return {
            "asin": asin,
            "title": f"Product {asin}",
            "price": 0.0,
            "category": "",
            "description": "",
            "image_urls": [],
            "available": True,
        }

    def search_products(
        self,
        keywords: str,
        category: str = "",
        max_results: int = 10,
    ) -> list[dict[str, Any]]:
        """Search for products by keywords.

        TODO: Implement actual PA-API SearchItems operation.
        """
        logger.info(
            "amazon_search",
            keywords=keywords,
            category=category,
            max_results=max_results,
        )

        # MVP: Empty results
        return []

    def get_affiliate_link(self, asin: str) -> str:
        """Generate an affiliate link for a product."""
        credentials = self._secrets.get_platform_credentials("amazon")
        partner_tag = credentials.get("AMAZON_PARTNER_TAG", "affiliate-20")
        return f"https://www.amazon.com/dp/{asin}?tag={partner_tag}"
