"""Typed application settings loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application configuration — loaded from .env / environment."""

    # General
    app_env: str = Field(default="dev", alias="APP_ENV")

    # LLM
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", alias="OPENAI_MODEL")
    use_premium_models: bool = Field(default=False, alias="USE_PREMIUM_MODELS")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    mistral_api_key: str = Field(default="", alias="MISTRAL_API_KEY")

    # Amazon PA-API
    amazon_paapi_access_key: str = Field(default="", alias="AMAZON_PAAPI_ACCESS_KEY")
    amazon_paapi_secret_key: str = Field(default="", alias="AMAZON_PAAPI_SECRET_KEY")
    amazon_paapi_partner_tag: str = Field(default="", alias="AMAZON_PAAPI_PARTNER_TAG")
    amazon_paapi_region: str = Field(default="us-east-1", alias="AMAZON_PAAPI_REGION")

    # Database
    database_url: str = Field(
        default="postgresql://user:pass@localhost:5432/affiliate_agency",
        alias="DATABASE_URL",
    )

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # Storage
    s3_bucket: str = Field(default="affiliate-agency-assets", alias="S3_BUCKET")
    s3_region: str = Field(default="us-east-1", alias="S3_REGION")
    s3_endpoint_url: str = Field(default="", alias="S3_ENDPOINT_URL")

    # Secrets Manager
    secrets_backend: str = Field(default="env", alias="SECRETS_BACKEND")

    # Content thresholds
    max_rewrite_attempts: int = Field(default=3, alias="MAX_REWRITE_ATTEMPTS")
    similarity_threshold: float = Field(default=0.85, alias="SIMILARITY_THRESHOLD")
    min_quality_score: int = Field(default=60, alias="MIN_QUALITY_SCORE")
    risk_score_auto_block: int = Field(default=70, alias="RISK_SCORE_AUTO_BLOCK")
    risk_score_review_threshold: int = Field(default=40, alias="RISK_SCORE_REVIEW_THRESHOLD")

    # Rate limits
    tiktok_posts_per_day: int = Field(default=10, alias="TIKTOK_POSTS_PER_DAY")
    instagram_posts_per_day: int = Field(default=25, alias="INSTAGRAM_POSTS_PER_DAY")
    x_posts_per_3h: int = Field(default=50, alias="X_POSTS_PER_3H")
    pinterest_pins_per_day: int = Field(default=50, alias="PINTEREST_PINS_PER_DAY")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


def get_settings() -> Settings:
    """Singleton accessor for application settings."""
    return Settings()
