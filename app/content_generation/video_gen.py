"""AI video pipeline + voiceover (U-23).

Script → ElevenLabs voiceover → images → MoviePy+FFmpeg assembly → output.
Providers: Runway ML, Kling AI, Pika Labs for full video gen.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class VoiceProvider(str, Enum):
    ELEVENLABS = "elevenlabs"
    GOOGLE_TTS = "google_tts"


class VideoProvider(str, Enum):
    RUNWAY = "runway"
    KLING = "kling"
    PIKA = "pika"
    MOVIEPY = "moviepy"  # local assembly


@dataclass(frozen=True)
class VoiceoverSpec:
    """Voiceover generation parameters."""

    voice_id: str = "default"
    language: str = "en"
    speed: float = 1.0
    stability: float = 0.5
    similarity_boost: float = 0.75


@dataclass
class GeneratedVoiceover:
    """Result of voice generation."""

    provider: str
    script_text: str
    audio_url: str = ""
    local_path: str = ""
    duration_seconds: float = 0.0
    success: bool = True
    error: str = ""


@dataclass(frozen=True)
class VideoSpec:
    """Video generation parameters."""

    duration_seconds: int = 30
    width: int = 1080
    height: int = 1920
    fps: int = 30
    format: str = "mp4"


@dataclass
class GeneratedVideo:
    """Result of video generation."""

    provider: str
    video_url: str = ""
    local_path: str = ""
    duration_seconds: float = 0.0
    width: int = 0
    height: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: str = ""


class VoiceoverGenerator:
    """Generate voiceovers from script text."""

    def __init__(self, provider: VoiceProvider = VoiceProvider.ELEVENLABS):
        self.provider = provider

    def generate(
        self, script_text: str, spec: VoiceoverSpec | None = None
    ) -> GeneratedVoiceover:
        """Generate voiceover audio from script."""
        if spec is None:
            spec = VoiceoverSpec()

        if not script_text.strip():
            return GeneratedVoiceover(
                provider=self.provider.value,
                script_text="",
                success=False,
                error="Empty script text",
            )

        # Estimate duration: ~150 words per minute at 1.0x speed
        word_count = len(script_text.split())
        estimated_duration = (word_count / 150.0) * 60.0 / spec.speed

        result = GeneratedVoiceover(
            provider=self.provider.value,
            script_text=script_text,
            duration_seconds=round(estimated_duration, 1),
        )

        logger.info(
            "voiceover_requested",
            provider=self.provider.value,
            word_count=word_count,
            est_duration=estimated_duration,
        )
        return result


class VideoGenerator:
    """Generate short-form video from components.

    Pipeline: script → voiceover → images → assembly → output .mp4
    """

    def __init__(self, provider: VideoProvider = VideoProvider.MOVIEPY):
        self.provider = provider

    def generate(
        self,
        script_text: str = "",
        image_urls: list[str] | None = None,
        voiceover_path: str = "",
        spec: VideoSpec | None = None,
    ) -> GeneratedVideo:
        """Generate a video from components."""
        if spec is None:
            spec = VideoSpec()

        result = GeneratedVideo(
            provider=self.provider.value,
            duration_seconds=spec.duration_seconds,
            width=spec.width,
            height=spec.height,
            metadata={
                "script_length": len(script_text),
                "image_count": len(image_urls or []),
                "has_voiceover": bool(voiceover_path),
                "fps": spec.fps,
                "format": spec.format,
            },
        )

        logger.info(
            "video_generation_requested",
            provider=self.provider.value,
            duration=spec.duration_seconds,
            image_count=len(image_urls or []),
        )
        return result

    def generate_short(
        self,
        script_text: str,
        duration: int = 30,
    ) -> GeneratedVideo:
        """Convenience: generate a short-form video (15/30/60s)."""
        valid_durations = (15, 30, 60)
        if duration not in valid_durations:
            duration = min(valid_durations, key=lambda d: abs(d - duration))

        spec = VideoSpec(duration_seconds=duration)
        return self.generate(script_text=script_text, spec=spec)
