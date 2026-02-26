"""analyzers.llm_router — Provider-agnostic LLM text generation.

Adding a new provider:
  1. Implement LLMProvider subclass below.
  2. Register it in _REGISTRY.
  3. Add its name to LLM_PROVIDER_ORDER in .env (or it auto-detects by key).

No other code needs to change.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Optional

from core.logging import get_logger

_log = get_logger(__name__)


# ── Provider contract ────────────────────────────────────────────────────────

class LLMProvider(ABC):
    """Interface every LLM backend must implement."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 512) -> str: ...


# ── Concrete providers ───────────────────────────────────────────────────────

class GeminiProvider(LLMProvider):
    name = "gemini"

    def is_available(self) -> bool:
        return bool(os.getenv("GEMINI_API_KEY"))

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        from analyzers.gemini_client import GeminiClient
        return GeminiClient().generate_text(prompt, max_tokens=max_tokens)


class OpenAIProvider(LLMProvider):
    name = "openai"

    def is_available(self) -> bool:
        return bool(os.getenv("OPENAI_API_KEY"))

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.4")),
        )
        return resp.choices[0].message.content or ""


class AnthropicProvider(LLMProvider):
    """Claude — set ANTHROPIC_API_KEY + add 'anthropic' to LLM_PROVIDER_ORDER."""
    name = "anthropic"

    def is_available(self) -> bool:
        return bool(os.getenv("ANTHROPIC_API_KEY"))

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        msg = client.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307"),
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text


class MistralProvider(LLMProvider):
    """Mistral — set MISTRAL_API_KEY + add 'mistral' to LLM_PROVIDER_ORDER."""
    name = "mistral"

    def is_available(self) -> bool:
        return bool(os.getenv("MISTRAL_API_KEY"))

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        from mistralai import Mistral
        client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
        resp = client.chat.complete(
            model=os.getenv("MISTRAL_MODEL", "mistral-small-latest"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or ""


# ── Registry — add new providers here only ──────────────────────────────────

_REGISTRY: dict[str, LLMProvider] = {
    p.name: p
    for p in [GeminiProvider(), OpenAIProvider(), AnthropicProvider(), MistralProvider()]
}


# ── Router ───────────────────────────────────────────────────────────────────

class LLMRouter:
    """Tries providers in priority order, returns first successful response.

    Priority is controlled by LLM_PROVIDER_ORDER env var (comma-separated).
    Defaults to all available providers in registry order.
    Example .env:
        LLM_PROVIDER_ORDER=anthropic,openai,gemini
    """

    def __init__(self) -> None:
        order_str = os.getenv("LLM_PROVIDER_ORDER", "")
        if order_str:
            names = [n.strip() for n in order_str.split(",") if n.strip()]
        else:
            names = list(_REGISTRY.keys())
        self._providers = [_REGISTRY[n] for n in names if n in _REGISTRY]

    def available_providers(self) -> list[str]:
        return [p.name for p in self._providers if p.is_available()]

    def generate(self, prompt: str, max_tokens: int = 512) -> Optional[str]:
        """Try each provider in order, return first success or None."""
        for provider in self._providers:
            if not provider.is_available():
                continue
            try:
                result = provider.generate(prompt, max_tokens=max_tokens)
                _log.info("LLM response from provider=%s", provider.name)
                return result
            except Exception as exc:
                _log.warning("Provider %s failed: %s — trying next", provider.name, exc)
        _log.warning("All LLM providers failed or unavailable")
        return None
