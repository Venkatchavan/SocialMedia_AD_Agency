"""Tests for growth calendar planner (U-19) and trend hooks (U-20)."""

from __future__ import annotations

import pytest

from app.content_generation.calendar_planner import (
    CalendarPlanner,
    GrowthCalendar,
    CalendarEntry,
    WeekPlan,
)
from app.content_generation.trend_hooks import (
    TrendHookGenerator,
    TrendSignal,
    GeneratedHook,
)


# ── CalendarPlanner (U-19) ───────────────────────────────────────────

class TestCalendarPlanner:
    def test_default_12_weeks(self):
        planner = CalendarPlanner()
        cal = planner.generate("ws1")
        assert len(cal.weeks) == 12
        assert cal.workspace_id == "ws1"

    def test_custom_week_count(self):
        planner = CalendarPlanner()
        cal = planner.generate("ws1", weeks=4)
        assert len(cal.weeks) == 4

    def test_entries_have_platforms(self):
        planner = CalendarPlanner()
        cal = planner.generate("ws1", platforms=["instagram", "tiktok"])
        for week in cal.weeks:
            platforms = {e.platform for e in week.entries}
            assert "instagram" in platforms
            assert "tiktok" in platforms

    def test_themes_rotate(self):
        planner = CalendarPlanner()
        cal = planner.generate("ws1")
        themes = [w.theme for w in cal.weeks]
        assert themes[0] != themes[1]  # Different themes per week

    def test_total_entries_positive(self):
        planner = CalendarPlanner()
        cal = planner.generate("ws1")
        assert cal.total_entries > 0

    def test_ab_test_added_every_4_weeks(self):
        planner = CalendarPlanner()
        cal = planner.generate("ws1", platforms=["instagram"])
        ab_entries = [
            e for w in cal.weeks for e in w.entries if e.ab_test
        ]
        assert len(ab_entries) > 0

    def test_offers_added_every_3_weeks(self):
        planner = CalendarPlanner()
        cal = planner.generate("ws1", platforms=["instagram"], offers=["20% OFF"])
        offer_entries = [
            e for w in cal.weeks for e in w.entries if e.offer
        ]
        assert len(offer_entries) > 0
        assert offer_entries[0].offer == "20% OFF"

    def test_content_types_platform_specific(self):
        planner = CalendarPlanner()
        cal = planner.generate("ws1", platforms=["instagram", "x"])
        ig_types = {e.content_type for w in cal.weeks for e in w.entries if e.platform == "instagram"}
        x_types = {e.content_type for w in cal.weeks for e in w.entries if e.platform == "x"}
        assert "reel" in ig_types
        assert "tweet" in x_types

    def test_single_platform(self):
        planner = CalendarPlanner()
        cal = planner.generate("ws1", platforms=["pinterest"])
        platforms = {e.platform for w in cal.weeks for e in w.entries}
        assert platforms == {"pinterest"}


# ── TrendHookGenerator (U-20) ───────────────────────────────────────

class TestTrendHookGenerator:
    def test_generate_hooks(self):
        gen = TrendHookGenerator()
        hooks = gen.generate_hooks("curiosity", "tiktok", count=3)
        assert len(hooks) == 3
        assert all(isinstance(h, GeneratedHook) for h in hooks)

    def test_hook_has_platform(self):
        gen = TrendHookGenerator()
        hooks = gen.generate_hooks("fear", "instagram")
        assert all(h.platform == "instagram" for h in hooks)

    def test_hook_with_variables(self):
        gen = TrendHookGenerator()
        hooks = gen.generate_hooks(
            "curiosity", "tiktok",
            variables={"scenario": "your headphones break mid-workout"},
            count=1,
        )
        assert "headphones break" in hooks[0].text

    def test_available_hook_types(self):
        gen = TrendHookGenerator()
        types = gen.get_available_hook_types()
        assert "curiosity" in types
        assert "fear" in types
        assert "aspirational" in types
        assert "comparison" in types
        assert "story" in types

    def test_trend_signal_boosts_confidence(self):
        gen = TrendHookGenerator()
        gen.add_trend_signal(TrendSignal(
            platform="tiktok",
            signal_type="format",
            description="POV style trending",
            popularity_score=0.9,
        ))
        hooks = gen.generate_hooks("curiosity", "tiktok", count=1)
        assert hooks[0].confidence > 0.7
        assert hooks[0].trend_signal == "POV style trending"

    def test_get_trending_formats(self):
        gen = TrendHookGenerator()
        gen.add_trend_signal(TrendSignal(
            platform="tiktok", signal_type="format",
            description="Duet reaction",
        ))
        gen.add_trend_signal(TrendSignal(
            platform="tiktok", signal_type="audio",
            description="Trending sound",
        ))
        formats = gen.get_trending_formats("tiktok")
        assert len(formats) == 1
        assert formats[0].signal_type == "format"

    def test_unknown_hook_type_falls_back(self):
        gen = TrendHookGenerator()
        hooks = gen.generate_hooks("nonexistent_type", "instagram", count=2)
        # Falls back to curiosity templates
        assert len(hooks) >= 1
