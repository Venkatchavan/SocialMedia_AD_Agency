"""analyzers.gemini_client — Gemini Vision API client (stubbed behind env flag)."""

from __future__ import annotations

from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from analyzers.vision_client_base import VisionClientBase
from core.config import GEMINI_API_KEY
from core.logging import get_logger

_log = get_logger(__name__)
_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent"


class GeminiClient(VisionClientBase):
    """Gemini Vision — real calls only when GEMINI_API_KEY is set."""

    def is_available(self) -> bool:
        return bool(GEMINI_API_KEY)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=20))
    def analyze_image(self, image_url: str, prompt: str) -> dict[str, Any]:
        if not self.is_available():
            return {"error": "GEMINI_API_KEY not set"}
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {"inlineData": {"mimeType": "image/jpeg", "data": image_url}},
                    ]
                }
            ]
        }
        resp = httpx.post(
            _ENDPOINT,
            json=payload,
            params={"key": GEMINI_API_KEY},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()

    def analyze_video_thumbnail(self, thumb_url: str, prompt: str) -> dict[str, Any]:
        """For video, analyze the thumbnail image."""
        return self.analyze_image(thumb_url, prompt)
