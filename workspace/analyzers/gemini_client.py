"""analyzers.gemini_client — Gemini Vision + text API client."""

from __future__ import annotations

import base64
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from analyzers.vision_client_base import VisionClientBase
from core.config import GEMINI_API_KEY
from core.logging import get_logger

_log = get_logger(__name__)
_MODEL = "gemini-2.0-flash"
_BASE = f"https://generativelanguage.googleapis.com/v1beta/models/{_MODEL}"
_VISION_URL = f"{_BASE}:generateContent"
_TEXT_URL = f"{_BASE}:generateContent"
_PARAMS = {"key": GEMINI_API_KEY}


def _retryable(exc: BaseException) -> bool:
    """Retry on 429 rate-limit, 5xx errors, and connection issues."""
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in (429, 500, 502, 503, 504)
    return isinstance(exc, (httpx.ConnectError, httpx.TimeoutException))


def _params() -> dict:
    """Build params dict at call time (supports key rotation)."""
    return {"key": GEMINI_API_KEY}


def _download_b64(url: str) -> tuple[str, str]:
    """Download image from URL, return (base64_data, mime_type)."""
    resp = httpx.get(url, timeout=20, follow_redirects=True)
    resp.raise_for_status()
    mime = resp.headers.get("content-type", "image/jpeg").split(";")[0].strip()
    return base64.b64encode(resp.content).decode(), mime


class GeminiClient(VisionClientBase):
    """Gemini 2.0 Flash — vision + text, real calls only when GEMINI_API_KEY is set."""

    def is_available(self) -> bool:
        return bool(GEMINI_API_KEY)

    @retry(
        retry=retry_if_exception(_retryable),
        stop=stop_after_attempt(4),
        wait=wait_exponential(min=5, max=60),
    )
    def analyze_image(self, image_url: str, prompt: str) -> dict[str, Any]:
        if not self.is_available():
            return {"error": "GEMINI_API_KEY not set"}
        b64_data, mime_type = _download_b64(image_url)
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inlineData": {"mimeType": mime_type, "data": b64_data}},
                ]
            }]
        }
        resp = httpx.post(_VISION_URL, json=payload, params=_params(), timeout=60)
        resp.raise_for_status()
        return resp.json()

    def analyze_video_thumbnail(self, thumb_url: str, prompt: str) -> dict[str, Any]:
        return self.analyze_image(thumb_url, prompt)

    @retry(
        retry=retry_if_exception(_retryable),
        stop=stop_after_attempt(4),
        wait=wait_exponential(min=5, max=60),
    )
    def generate_text(self, prompt: str, max_tokens: int = 512) -> str:
        """Text-only generation via Gemini 2.0 Flash."""
        if not self.is_available():
            return ""
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.4},
        }
        resp = httpx.post(_TEXT_URL, json=payload, params=_params(), timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
