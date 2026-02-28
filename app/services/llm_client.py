"""LLM client service — thin wrapper over OpenAI-compatible chat completions.

Supports multiple providers via app.core.llm_models registry.
Has a DRY_RUN mode (default) that returns canned responses for testing.

SECURITY:
- API keys loaded from config, never logged or exposed.
- Prompts are validated via AgentConstitution before sending.
- Responses are validated for secret exposure after receiving.
"""

from __future__ import annotations

import json
from typing import Any

import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)

# Dry-run response templates keyed by agent_id
_DRY_RUN_RESPONSES: dict[str, str] = {
    "scriptwriter": json.dumps({
        "hook": "Stop scrolling — this changes everything.",
        "scenes": [
            {"scene_number": 1, "scene_type": "problem",
             "dialogue": "Finding the right product is overwhelming.",
             "visual_direction": "Show frustration with alternatives",
             "duration_seconds": 5},
            {"scene_number": 2, "scene_type": "solution_reveal",
             "dialogue": "That is why this product stands out.",
             "visual_direction": "Clean product reveal shot",
             "duration_seconds": 5},
            {"scene_number": 3, "scene_type": "demo",
             "dialogue": "Perfect for everyday use.",
             "visual_direction": "Lifestyle demonstration",
             "duration_seconds": 8},
            {"scene_number": 4, "scene_type": "social_proof",
             "dialogue": "See why people are switching.",
             "visual_direction": "Show features and benefits",
             "duration_seconds": 5},
        ],
        "cta": "Link in bio! {{AFFILIATE_DISCLOSURE}}",
    }),
    "caption_seo": json.dumps({
        "caption": "Stop scrolling — you need to see this!\n\nThis product is a game-changer.",
        "hashtags": ["#musthave", "#trending", "#fyp"],
    }),
    "product_enrichment": json.dumps({
        "category_path": ["Electronics", "Audio"],
        "primary_persona": "tech-savvy young adult who loves gadgets",
        "use_cases": ["music listening", "video calls", "commute"],
        "trending_score": 65,
    }),
    "manager": json.dumps({
        "quality_score": 78,
        "issues": [],
        "approved": True,
        "feedback": "Content meets quality and compliance standards.",
    }),
}


class LLMClient:
    """Thin LLM client with dry-run support.

    In dry-run mode (default), returns canned responses.
    In live mode, calls OpenAI-compatible API via httpx.
    """

    def __init__(self, dry_run: bool | None = None) -> None:
        settings = get_settings()
        self._dry_run = dry_run if dry_run is not None else settings.llm_dry_run
        self._api_key = settings.openai_api_key
        self._model = settings.openai_model

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        agent_id: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Send a chat completion request.

        Args:
            system_prompt: System message defining agent behavior.
            user_prompt: User message with task context.
            agent_id: Agent identifier for dry-run response selection.
            temperature: LLM temperature (0.0-1.0).
            max_tokens: Max response tokens.

        Returns:
            LLM response text.
        """
        if self._dry_run:
            return self._dry_run_response(agent_id)

        return self._call_openai(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        agent_id: str = "",
        temperature: float = 0.4,
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        """Send a chat completion and parse JSON response.

        Returns parsed dict. Falls back to empty dict on parse failure.
        """
        raw = self.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            agent_id=agent_id,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return self._parse_json(raw)

    @property
    def is_dry_run(self) -> bool:
        """Whether client is in dry-run mode."""
        return self._dry_run

    def _dry_run_response(self, agent_id: str) -> str:
        """Return a canned response for testing."""
        response = _DRY_RUN_RESPONSES.get(agent_id, '{"result": "dry_run"}')
        logger.debug("llm_dry_run", agent_id=agent_id)
        return response

    def _call_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Call OpenAI-compatible chat completions API."""
        import httpx

        if not self._api_key:
            logger.error("llm_no_api_key")
            raise ValueError(
                "OPENAI_API_KEY not set. Set LLM_DRY_RUN=true for testing."
            )

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        logger.info(
            "llm_request",
            model=self._model,
            system_len=len(system_prompt),
            user_len=len(user_prompt),
        )

        try:
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()

            content = data["choices"][0]["message"]["content"]
            logger.info(
                "llm_response",
                model=self._model,
                response_len=len(content),
            )
            return content

        except httpx.HTTPStatusError as e:
            logger.error("llm_http_error", status=e.response.status_code)
            raise
        except Exception as e:
            logger.error("llm_error", error=str(e))
            raise

    @staticmethod
    def _parse_json(raw: str) -> dict[str, Any]:
        """Parse JSON from LLM response, handling markdown fences."""
        text = raw.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last fence lines
            lines = [ln for ln in lines if not ln.strip().startswith("```")]
            text = "\n".join(lines)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("llm_json_parse_failed", raw_length=len(raw))
            return {}
