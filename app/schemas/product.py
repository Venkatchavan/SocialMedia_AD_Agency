"""Pydantic schemas for product data."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ProductRecord(BaseModel):
    """Raw product record ingested from Amazon PA-API or CSV."""

    id: str = Field(description="Internal product UUID")
    asin: str = Field(description="Amazon Standard Identification Number")
    title: str = Field(description="Product title")
    price: float = Field(ge=0, description="Product price")
    currency: str = Field(default="USD", max_length=3)
    category: str = Field(default="", description="Top-level category")
    description: str = Field(default="", description="Product description")
    image_urls: list[str] = Field(default_factory=list)
    affiliate_link: str = Field(default="", description="Amazon affiliate link")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("asin")
    @classmethod
    def validate_asin(cls, v: str) -> str:
        import re

        if not re.match(r"^[A-Z0-9]{10}$", v):
            raise ValueError(f"Invalid ASIN format: {v}. Must be 10 alphanumeric characters.")
        return v


class EnrichedProduct(BaseModel):
    """Product enriched with category taxonomy, persona, and use-case data."""

    product: ProductRecord
    category_path: list[str] = Field(
        default_factory=list,
        description="Full category taxonomy path",
        examples=[["Electronics", "Audio", "Headphones", "Wireless"]],
    )
    primary_persona: str = Field(
        default="",
        description="Target audience persona description",
        examples=["College student who loves anime and lo-fi music"],
    )
    use_cases: list[str] = Field(
        default_factory=list,
        description="Top use cases for this product",
        examples=[["music listening", "gaming", "commute"]],
    )
    trending_score: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Trending relevance score",
    )
    enriched_at: datetime = Field(default_factory=datetime.utcnow)
