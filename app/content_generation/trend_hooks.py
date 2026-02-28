"""Trend-aware hook generation (U-20).

Generates hooks that match current platform culture instead of
textbook marketing. Cross-references with brand voice constraints.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class TrendSignal:
    """A trending format/audio/style signal from a platform."""

    platform: str
    signal_type: str  # "format" | "audio" | "style" | "hashtag"
    description: str
    example_url: str = ""
    popularity_score: float = 0.0
    detected_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class GeneratedHook:
    """A generated hook optimized for platform trends."""

    text: str
    platform: str
    hook_type: str  # "curiosity" | "fear" | "aspirational" | etc.
    trend_signal: str = ""
    confidence: float = 0.0
    brand_voice_aligned: bool = True


# Hook templates organized by type and platform culture
_HOOK_TEMPLATES: dict[str, list[str]] = {
    "curiosity": [
        "POV: {scenario}",
        "Wait for it... {reveal}",
        "Nobody talks about {topic}",
        "The {thing} that changed everything",
        "What happens when {action}",
    ],
    "fear": [
        "Stop {bad_action} before it's too late",
        "You're losing {value} every day by {mistake}",
        "The mistake 90% of {audience} make",
        "{number} signs you're {problem}",
    ],
    "aspirational": [
        "How I {achievement} in {timeframe}",
        "From {before} to {after}",
        "This is what {goal} actually looks like",
        "Day {number} of {challenge}",
    ],
    "comparison": [
        "${price_a} vs ${price_b} — can you tell the difference?",
        "I tried {product_a} so you don't have to",
        "{brand} WHO? Try this instead",
        "Cheap vs expensive: the truth about {category}",
    ],
    "story": [
        "Storytime: {setup}",
        "I can't believe {event} actually happened",
        "The time I {action} and {result}",
    ],
    "question": [
        "What do you think about {topic}?",
        "Am I the only one who {behavior}?",
        "Rate this {thing} 1-10",
    ],
    "statistic": [
        "{percentage}% of {audience} don't know this",
        "This product saved me {amount} per {period}",
        "{number} reasons why {claim}",
    ],
}


class TrendHookGenerator:
    """Generate trend-aware hooks for content."""

    def __init__(self) -> None:
        self._trend_signals: list[TrendSignal] = []

    def add_trend_signal(self, signal: TrendSignal) -> None:
        """Register a detected trend signal."""
        self._trend_signals.append(signal)

    def generate_hooks(
        self,
        hook_type: str,
        platform: str,
        variables: dict[str, str] | None = None,
        count: int = 3,
    ) -> list[GeneratedHook]:
        """Generate hooks for a given type and platform.

        Args:
            hook_type: Type of hook (curiosity, fear, etc.)
            platform: Target platform.
            variables: Template variables to fill in.
            count: Number of hooks to generate.
        """
        templates = _HOOK_TEMPLATES.get(hook_type, _HOOK_TEMPLATES.get("curiosity", []))
        if not templates:
            return []

        variables = variables or {}
        hooks: list[GeneratedHook] = []

        for i, template in enumerate(templates[:count]):
            text = template
            for key, value in variables.items():
                text = text.replace(f"{{{key}}}", value)

            # Find relevant trend signal
            trend = self._find_trend(platform, hook_type)

            hooks.append(GeneratedHook(
                text=text,
                platform=platform,
                hook_type=hook_type,
                trend_signal=trend.description if trend else "",
                confidence=0.7 + (0.1 if trend else 0.0),
            ))

        return hooks

    def get_trending_formats(self, platform: str) -> list[TrendSignal]:
        """Get current trending formats for a platform."""
        return [
            s for s in self._trend_signals
            if s.platform == platform and s.signal_type == "format"
        ]

    def get_available_hook_types(self) -> list[str]:
        """List all available hook types."""
        return list(_HOOK_TEMPLATES.keys())

    def _find_trend(self, platform: str, hook_type: str) -> TrendSignal | None:
        """Find the most relevant trend signal."""
        for signal in reversed(self._trend_signals):
            if signal.platform == platform:
                return signal
        return None
