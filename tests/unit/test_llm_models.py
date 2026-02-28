"""Tests for LLM model configuration (U-5)."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from app.core.llm_models import (
    ModelSpec,
    get_all_models,
    get_model,
    get_model_id,
)


class TestModelSpec:
    """ModelSpec dataclass basics."""

    def test_frozen(self) -> None:
        spec = ModelSpec(provider="openai", model_id="gpt-4o", max_tokens=4096)
        with pytest.raises(AttributeError):
            spec.model_id = "other"  # type: ignore[misc]

    def test_defaults(self) -> None:
        spec = ModelSpec(provider="openai", model_id="gpt-4o", max_tokens=4096)
        assert spec.supports_vision is False
        assert spec.supports_thinking is False


class TestGetModel:
    """get_model() returns correct tier based on USE_PREMIUM_MODELS."""

    @patch.dict(os.environ, {"USE_PREMIUM_MODELS": "false"}, clear=False)
    def test_budget_openai(self) -> None:
        spec = get_model("openai")
        assert spec.model_id == "gpt-4o-mini"
        assert spec.provider == "openai"

    @patch.dict(os.environ, {"USE_PREMIUM_MODELS": "true"}, clear=False)
    def test_premium_openai(self) -> None:
        spec = get_model("openai")
        assert spec.model_id == "gpt-4o"

    @patch.dict(os.environ, {"USE_PREMIUM_MODELS": "true"}, clear=False)
    def test_premium_anthropic(self) -> None:
        spec = get_model("anthropic")
        assert spec.model_id == "claude-3-5-sonnet-20241022"

    @patch.dict(os.environ, {"USE_PREMIUM_MODELS": "false"}, clear=False)
    def test_budget_anthropic(self) -> None:
        spec = get_model("anthropic")
        assert spec.model_id == "claude-3-haiku-20240307"

    @patch.dict(os.environ, {"USE_PREMIUM_MODELS": "true"}, clear=False)
    def test_premium_gemini_has_thinking(self) -> None:
        spec = get_model("gemini")
        assert "thinking" in spec.model_id
        assert spec.supports_thinking is True

    @patch.dict(os.environ, {"USE_PREMIUM_MODELS": "true"}, clear=False)
    def test_premium_mistral(self) -> None:
        spec = get_model("mistral")
        assert spec.model_id == "mistral-large-latest"


class TestGetModelId:
    """get_model_id() shortcut."""

    @patch.dict(os.environ, {"USE_PREMIUM_MODELS": "false"}, clear=False)
    def test_returns_string(self) -> None:
        model_id = get_model_id("openai")
        assert isinstance(model_id, str)
        assert model_id == "gpt-4o-mini"


class TestGetAllModels:
    """get_all_models() returns complete dict."""

    @patch.dict(os.environ, {"USE_PREMIUM_MODELS": "false"}, clear=False)
    def test_all_providers_present(self) -> None:
        models = get_all_models()
        assert set(models.keys()) == {"openai", "anthropic", "gemini", "mistral"}
        for spec in models.values():
            assert isinstance(spec, ModelSpec)
