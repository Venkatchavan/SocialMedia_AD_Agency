"""analyzers.vision_client_base — Abstract vision-model interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class VisionClientBase(ABC):
    """Contract for any vision-model backend (Gemini, OpenAI, etc.)."""

    @abstractmethod
    def analyze_image(self, image_url: str, prompt: str) -> dict[str, Any]:
        """Send an image URL + prompt; return structured tag dict."""
        ...

    @abstractmethod
    def analyze_video_thumbnail(self, thumb_url: str, prompt: str) -> dict[str, Any]:
        """Analyze a video via its thumbnail."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the backend has valid credentials."""
        ...
