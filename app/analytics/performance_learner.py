"""Performance-weighted learning (U-29).

Re-scores hook/angle/format patterns from real post-publish metrics.
Top 10% → +0.1 score delta; Bottom 10% → -0.05 score delta.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

REINFORCE_DELTA = 0.1
PENALIZE_DELTA = -0.05


@dataclass
class PatternScore:
    """A scored content pattern (hook type, angle, format)."""

    pattern_id: str
    pattern_type: str  # hook, angle, format
    label: str
    base_score: float = 0.5
    adjustment: float = 0.0
    sample_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def score(self) -> float:
        """Effective score = base + adjustment, clamped to [0, 1]."""
        return max(0.0, min(1.0, self.base_score + self.adjustment))


@dataclass
class LearningEvent:
    """A single learning signal from a published post."""

    post_id: str
    pattern_id: str
    engagement_rate: float
    platform: str


class PerformanceLearner:
    """Learn from real metrics to re-score content patterns.

    Feeds back into synthesis stage cluster weights.
    """

    def __init__(self) -> None:
        self._patterns: dict[str, PatternScore] = {}
        self._events: list[LearningEvent] = []

    def register_pattern(
        self,
        pattern_id: str,
        pattern_type: str,
        label: str,
        base_score: float = 0.5,
    ) -> PatternScore:
        """Register a content pattern for tracking."""
        ps = PatternScore(
            pattern_id=pattern_id,
            pattern_type=pattern_type,
            label=label,
            base_score=base_score,
        )
        self._patterns[pattern_id] = ps
        return ps

    def record_event(self, event: LearningEvent) -> None:
        """Record a performance data point for a pattern."""
        self._events.append(event)
        ps = self._patterns.get(event.pattern_id)
        if ps is not None:
            ps.sample_count += 1

    def learn(self) -> dict[str, float]:
        """Run learning pass: re-score patterns based on performance.

        Top 10% posts → reinforce (+0.1)
        Bottom 10% → penalize (-0.05)
        Returns: {pattern_id: new_score}
        """
        if not self._events:
            return {}

        # Sort events by engagement
        sorted_events = sorted(self._events, key=lambda e: e.engagement_rate, reverse=True)
        n = len(sorted_events)
        top_cutoff = max(1, n // 10)
        bottom_cutoff = max(1, n // 10)

        top_ids = {e.pattern_id for e in sorted_events[:top_cutoff]}
        bottom_ids = {e.pattern_id for e in sorted_events[-bottom_cutoff:]}

        # Remove overlap (if same pattern in both, net zero)
        overlap = top_ids & bottom_ids
        top_ids -= overlap
        bottom_ids -= overlap

        adjustments: dict[str, float] = {}

        for pid in top_ids:
            ps = self._patterns.get(pid)
            if ps is not None:
                ps.adjustment += REINFORCE_DELTA
                adjustments[pid] = ps.score
                logger.info("pattern_reinforced", pattern_id=pid, new_score=ps.score)

        for pid in bottom_ids:
            ps = self._patterns.get(pid)
            if ps is not None:
                ps.adjustment += PENALIZE_DELTA
                adjustments[pid] = ps.score
                logger.info("pattern_penalized", pattern_id=pid, new_score=ps.score)

        return adjustments

    def get_pattern(self, pattern_id: str) -> PatternScore | None:
        return self._patterns.get(pattern_id)

    def get_top_patterns(
        self, pattern_type: str | None = None, limit: int = 10
    ) -> list[PatternScore]:
        """Get highest-scoring patterns."""
        patterns = list(self._patterns.values())
        if pattern_type:
            patterns = [p for p in patterns if p.pattern_type == pattern_type]
        patterns.sort(key=lambda p: p.score, reverse=True)
        return patterns[:limit]

    def reset_adjustments(self) -> None:
        """Reset all learned adjustments (fresh start)."""
        for ps in self._patterns.values():
            ps.adjustment = 0.0
            ps.sample_count = 0
        self._events.clear()
