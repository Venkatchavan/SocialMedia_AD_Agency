"""Tests for AI image generation (U-22) and video pipeline (U-23)."""

from __future__ import annotations

import pytest

from app.content_generation.image_gen import (
    GeneratedImage,
    ImageGenerator,
    ImagePromptBuilder,
    ImageProvider,
    ImageSpec,
)
from app.content_generation.video_gen import (
    GeneratedVideo,
    GeneratedVoiceover,
    VideoGenerator,
    VideoProvider,
    VideoSpec,
    VoiceoverGenerator,
    VoiceoverSpec,
    VoiceProvider,
)

# ── Image Prompt Builder ──


class TestImagePromptBuilder:
    def test_basic_prompt(self):
        builder = ImagePromptBuilder()
        prompt = builder.build(product_name="Widget X")
        assert "Widget X" in prompt

    def test_visual_direction_override(self):
        builder = ImagePromptBuilder()
        prompt = builder.build(visual_direction="Minimalist flat lay", product_name="X")
        assert "Minimalist flat lay" in prompt

    def test_brand_colors_included(self):
        builder = ImagePromptBuilder()
        prompt = builder.build(product_name="P", brand_colors=["#FF0000", "#00FF00"])
        assert "#FF0000" in prompt

    def test_platform_aspect_hint(self):
        builder = ImagePromptBuilder()
        prompt = builder.build(product_name="P", platform="instagram_reels")
        assert "9:16" in prompt

    def test_empty_prompt_fallback(self):
        builder = ImagePromptBuilder()
        prompt = builder.build()
        assert "professional" in prompt.lower()


# ── ImageGenerator ──


class TestImageGenerator:
    def test_default_provider(self):
        gen = ImageGenerator()
        assert gen.provider == ImageProvider.DALLE3

    def test_generate_returns_result(self):
        gen = ImageGenerator()
        result = gen.generate(product_name="Serum")
        assert isinstance(result, GeneratedImage)
        assert result.provider == "dalle3"
        assert "Serum" in result.prompt

    def test_custom_spec(self):
        gen = ImageGenerator(provider=ImageProvider.STABLE_DIFFUSION)
        spec = ImageSpec(width=512, height=512, quality="hd")
        result = gen.generate(product_name="P", spec=spec)
        assert result.width == 512
        assert result.height == 512
        assert result.metadata["quality"] == "hd"

    def test_batch_generation(self):
        gen = ImageGenerator()
        platforms = ["instagram_feed", "tiktok", "linkedin"]
        results = gen.generate_batch(platforms, product_name="Gadget")
        assert set(results.keys()) == set(platforms)
        for platform, img in results.items():
            assert platform in img.metadata.get("platform", "")

    def test_frozen_spec(self):
        spec = ImageSpec()
        with pytest.raises(AttributeError):
            spec.width = 2048  # type: ignore[misc]


# ── VoiceoverGenerator ──


class TestVoiceoverGenerator:
    def test_default_provider(self):
        gen = VoiceoverGenerator()
        assert gen.provider == VoiceProvider.ELEVENLABS

    def test_generate_voiceover(self):
        gen = VoiceoverGenerator()
        result = gen.generate("This is a test script for a product ad.")
        assert isinstance(result, GeneratedVoiceover)
        assert result.success
        assert result.duration_seconds > 0

    def test_empty_script_fails(self):
        gen = VoiceoverGenerator()
        result = gen.generate("   ")
        assert not result.success
        assert "Empty" in result.error

    def test_speed_affects_duration(self):
        gen = VoiceoverGenerator()
        slow = gen.generate("Hello world", spec=VoiceoverSpec(speed=0.5))
        fast = gen.generate("Hello world", spec=VoiceoverSpec(speed=2.0))
        assert slow.duration_seconds > fast.duration_seconds


# ── VideoGenerator ──


class TestVideoGenerator:
    def test_default_provider(self):
        gen = VideoGenerator()
        assert gen.provider == VideoProvider.MOVIEPY

    def test_generate_video(self):
        gen = VideoGenerator()
        result = gen.generate(script_text="Product demo script")
        assert isinstance(result, GeneratedVideo)
        assert result.metadata["script_length"] > 0

    def test_custom_spec(self):
        gen = VideoGenerator()
        spec = VideoSpec(duration_seconds=15, width=720, height=1280)
        result = gen.generate(script_text="Short ad", spec=spec)
        assert result.duration_seconds == 15
        assert result.width == 720

    def test_generate_short_snaps_duration(self):
        gen = VideoGenerator()
        result = gen.generate_short("Script text", duration=20)
        # Should snap to nearest valid: 15
        assert result.duration_seconds == 15

    def test_generate_short_valid_durations(self):
        gen = VideoGenerator()
        for d in (15, 30, 60):
            result = gen.generate_short("Script", duration=d)
            assert result.duration_seconds == d

    def test_image_count_in_metadata(self):
        gen = VideoGenerator()
        result = gen.generate(
            script_text="Script",
            image_urls=["http://img1.jpg", "http://img2.jpg"],
        )
        assert result.metadata["image_count"] == 2
