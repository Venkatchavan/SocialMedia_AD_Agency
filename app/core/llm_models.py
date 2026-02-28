"""LLM model configuration — selects model tiers per provider.

Supports premium vs. budget models controlled by USE_PREMIUM_MODELS env flag.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.config import get_settings

Provider = Literal["openai", "anthropic", "gemini", "mistral"]


@dataclass(frozen=True)
class ModelSpec:
    """Specification for a single LLM model."""

    provider: Provider
    model_id: str
    max_tokens: int
    supports_vision: bool = False
    supports_thinking: bool = False


# ── Budget models (dev/test) ───────────────────────────
_BUDGET_MODELS: dict[Provider, ModelSpec] = {
    "openai": ModelSpec(
        provider="openai",
        model_id="gpt-4o-mini",
        max_tokens=4096,
        supports_vision=True,
    ),
    "anthropic": ModelSpec(
        provider="anthropic",
        model_id="claude-3-haiku-20240307",
        max_tokens=4096,
    ),
    "gemini": ModelSpec(
        provider="gemini",
        model_id="gemini-2.0-flash",
        max_tokens=8192,
    ),
    "mistral": ModelSpec(
        provider="mistral",
        model_id="mistral-small-latest",
        max_tokens=4096,
    ),
}

# ── Premium models (production) ────────────────────────
_PREMIUM_MODELS: dict[Provider, ModelSpec] = {
    "openai": ModelSpec(
        provider="openai",
        model_id="gpt-4o",
        max_tokens=4096,
        supports_vision=True,
    ),
    "anthropic": ModelSpec(
        provider="anthropic",
        model_id="claude-3-5-sonnet-20241022",
        max_tokens=8192,
    ),
    "gemini": ModelSpec(
        provider="gemini",
        model_id="gemini-2.0-flash-thinking-exp",
        max_tokens=8192,
        supports_thinking=True,
    ),
    "mistral": ModelSpec(
        provider="mistral",
        model_id="mistral-large-latest",
        max_tokens=4096,
    ),
}


def get_model(provider: Provider) -> ModelSpec:
    """Return the model spec for a provider based on the premium flag.

    Args:
        provider: One of openai, anthropic, gemini, mistral.

    Returns:
        ModelSpec for the selected tier.
    """
    settings = get_settings()
    tier = _PREMIUM_MODELS if settings.use_premium_models else _BUDGET_MODELS
    return tier[provider]


def get_all_models() -> dict[Provider, ModelSpec]:
    """Return all active model specs keyed by provider."""
    settings = get_settings()
    return dict(
        _PREMIUM_MODELS if settings.use_premium_models else _BUDGET_MODELS,
    )


def get_model_id(provider: Provider) -> str:
    """Shortcut — return just the model ID string."""
    return get_model(provider).model_id
