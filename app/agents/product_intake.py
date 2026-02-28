"""Product Intake Agent — Ingests Amazon product data.

Rules enforced:
- Only uses Amazon Product Advertising API (official) or CSV.
- Never scrapes any website.
- Validates ASIN format.
- Logs every ingestion attempt.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any

import structlog

from app.agents.base_agent import BaseAgent
from app.schemas.product import ProductRecord
from app.services.audit_logger import AuditLogger

logger = structlog.get_logger(__name__)


class ProductIntakeAgent(BaseAgent):
    """Ingest Amazon product data from API or CSV."""

    def __init__(self, audit_logger: AuditLogger, session_id: str = "") -> None:
        super().__init__(
            agent_id="product_intake",
            audit_logger=audit_logger,
            session_id=session_id,
        )

    def execute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Ingest product data.

        Inputs:
            - source: "csv" | "api" | "manual"
            - asin: str (if manual/api)
            - title: str (if manual)
            - price: float (if manual)
            - category: str (if manual)
            - csv_data: list[dict] (if csv)

        Returns:
            - products: list[ProductRecord dict]
        """
        source = inputs.get("source", "manual")
        products: list[dict] = []

        if source == "manual":
            product = self._ingest_manual(inputs)
            products.append(product)
        elif source == "csv":
            csv_data = inputs.get("csv_data", [])
            for row in csv_data:
                try:
                    product = self._ingest_manual(row)
                    products.append(product)
                except Exception as e:
                    logger.warning("csv_row_skip", error=str(e))
        elif source == "api":
            # TODO: Implement Amazon PA-API integration
            asin = inputs.get("asin", "")
            product = self._ingest_from_api(asin)
            products.append(product)

        logger.info(
            "products_ingested",
            source=source,
            count=len(products),
        )

        return {"products": products}

    def _ingest_manual(self, data: dict) -> dict:
        """Create a ProductRecord from manual input."""
        asin = data.get("asin", "")
        if not re.match(r"^[A-Z0-9]{10}$", asin):
            raise ValueError(f"Invalid ASIN format: {asin}")

        product = ProductRecord(
            id=str(uuid.uuid4()),
            asin=asin,
            title=data.get("title", ""),
            price=float(data.get("price", 0)),
            category=data.get("category", ""),
            description=data.get("description", ""),
            image_urls=data.get("image_urls", []),
            affiliate_link=data.get(
                "affiliate_link",
                f"https://www.amazon.com/dp/{asin}?tag=affiliate-20",
            ),
            created_at=datetime.now(tz=timezone.utc),
        )

        return product.model_dump(mode="json")

    def _ingest_from_api(self, asin: str) -> dict:
        """Fetch product data from Amazon PA-API.

        TODO: Implement with actual amazon-paapi SDK.
        For MVP, returns a placeholder.
        """
        if not re.match(r"^[A-Z0-9]{10}$", asin):
            raise ValueError(f"Invalid ASIN format: {asin}")

        logger.info("api_lookup", asin=asin)

        # Placeholder — real implementation uses Amazon PA-API client
        product = ProductRecord(
            id=str(uuid.uuid4()),
            asin=asin,
            title=f"Product {asin} (API lookup pending)",
            price=0.0,
            category="",
            affiliate_link=f"https://www.amazon.com/dp/{asin}?tag=affiliate-20",
            created_at=datetime.now(tz=timezone.utc),
        )

        return product.model_dump(mode="json")
