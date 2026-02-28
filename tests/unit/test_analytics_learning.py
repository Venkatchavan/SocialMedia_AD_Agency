"""Tests for metrics pull (U-28), performance learning (U-29), chat engine (U-30)."""

from __future__ import annotations

import pytest

from app.analytics import (
    MetricInterval,
    MetricsPuller,
    PLATFORM_METRICS,
    PostMetrics,
)
from app.analytics.performance_learner import (
    LearningEvent,
    PatternScore,
    PerformanceLearner,
    PENALIZE_DELTA,
    REINFORCE_DELTA,
)
from app.analytics.chat_engine import (
    AnalyticsChatEngine,
    ChatMessage,
    ChatResponse,
)


# ── PostMetrics ──


class TestPostMetrics:
    def test_engagement_rate(self):
        m = PostMetrics(
            post_id="p1", platform="instagram", interval="24h",
            impressions=1000, likes=50, comments=10, shares=5, saves=15,
        )
        assert m.engagement_rate == 0.08  # 80/1000

    def test_zero_impressions(self):
        m = PostMetrics(post_id="p1", platform="instagram", interval="6h")
        assert m.engagement_rate == 0.0


# ── MetricsPuller ──


class TestMetricsPuller:
    @pytest.fixture
    def puller(self) -> MetricsPuller:
        return MetricsPuller()

    def test_record_and_get(self, puller: MetricsPuller):
        m = PostMetrics(post_id="p1", platform="instagram", interval="6h", impressions=100)
        puller.record_metrics(m)
        results = puller.get_metrics("p1")
        assert len(results) == 1
        assert results[0].pulled_at != ""

    def test_filter_by_interval(self, puller: MetricsPuller):
        puller.record_metrics(PostMetrics(post_id="p1", platform="ig", interval="6h"))
        puller.record_metrics(PostMetrics(post_id="p1", platform="ig", interval="24h"))
        assert len(puller.get_metrics("p1", interval="6h")) == 1
        assert len(puller.get_metrics("p1", interval="24h")) == 1

    def test_get_latest(self, puller: MetricsPuller):
        puller.record_metrics(PostMetrics(post_id="p1", platform="ig", interval="6h", impressions=50))
        puller.record_metrics(PostMetrics(post_id="p1", platform="ig", interval="24h", impressions=200))
        latest = puller.get_latest("p1")
        assert latest is not None
        assert latest.impressions == 200

    def test_get_latest_empty(self, puller: MetricsPuller):
        assert puller.get_latest("missing") is None

    def test_top_posts(self, puller: MetricsPuller):
        puller.record_metrics(PostMetrics(post_id="p1", platform="ig", interval="24h", impressions=1000, likes=100))
        puller.record_metrics(PostMetrics(post_id="p2", platform="ig", interval="24h", impressions=1000, likes=50))
        top = puller.get_top_posts(limit=2)
        assert top[0].post_id == "p1"

    def test_top_posts_platform_filter(self, puller: MetricsPuller):
        puller.record_metrics(PostMetrics(post_id="p1", platform="ig", interval="24h", impressions=100))
        puller.record_metrics(PostMetrics(post_id="p2", platform="tiktok", interval="24h", impressions=100))
        assert len(puller.get_top_posts(platform="ig")) == 1

    def test_average_engagement(self, puller: MetricsPuller):
        puller.record_metrics(PostMetrics(post_id="p1", platform="ig", interval="24h", impressions=100, likes=10))
        puller.record_metrics(PostMetrics(post_id="p2", platform="ig", interval="24h", impressions=100, likes=20))
        avg = puller.get_average_engagement("ig")
        assert avg == pytest.approx(0.15, abs=0.01)

    def test_platform_metric_keys(self, puller: MetricsPuller):
        keys = puller.get_platform_metrics_keys("instagram")
        assert "reach" in keys
        assert "saves" in keys


# ── PerformanceLearner ──


class TestPerformanceLearner:
    @pytest.fixture
    def learner(self) -> PerformanceLearner:
        return PerformanceLearner()

    def test_register_pattern(self, learner: PerformanceLearner):
        ps = learner.register_pattern("h1", "hook", "fear-based")
        assert ps.score == 0.5
        assert ps.label == "fear-based"

    def test_score_clamped(self):
        ps = PatternScore(pattern_id="x", pattern_type="hook", label="t", base_score=0.95, adjustment=0.2)
        assert ps.score == 1.0
        ps2 = PatternScore(pattern_id="y", pattern_type="hook", label="t", base_score=0.02, adjustment=-0.1)
        assert ps2.score == 0.0

    def test_learn_reinforces_top(self, learner: PerformanceLearner):
        learner.register_pattern("h1", "hook", "good")
        learner.register_pattern("h2", "hook", "bad")
        # 10+ events needed for 10% cutoff
        for i in range(10):
            learner.record_event(LearningEvent(f"p{i}", "h1", engagement_rate=0.95, platform="ig"))
        for i in range(10):
            learner.record_event(LearningEvent(f"q{i}", "h2", engagement_rate=0.01, platform="ig"))
        adjustments = learner.learn()
        assert "h1" in adjustments
        assert adjustments["h1"] > 0.5  # reinforced
        assert "h2" in adjustments
        assert adjustments["h2"] < 0.5  # penalized

    def test_learn_no_events(self, learner: PerformanceLearner):
        assert learner.learn() == {}

    def test_get_top_patterns(self, learner: PerformanceLearner):
        learner.register_pattern("h1", "hook", "A", base_score=0.9)
        learner.register_pattern("h2", "hook", "B", base_score=0.3)
        learner.register_pattern("a1", "angle", "C", base_score=0.8)
        top_hooks = learner.get_top_patterns(pattern_type="hook")
        assert top_hooks[0].pattern_id == "h1"

    def test_reset_adjustments(self, learner: PerformanceLearner):
        ps = learner.register_pattern("h1", "hook", "X")
        ps.adjustment = 0.3
        learner.reset_adjustments()
        assert ps.adjustment == 0.0


# ── AnalyticsChatEngine ──


class TestAnalyticsChatEngine:
    @pytest.fixture
    def chat(self) -> AnalyticsChatEngine:
        engine = AnalyticsChatEngine(workspace_id="ws-1")
        engine.add_knowledge("Instagram hooks with fear-based messaging got 12% engagement", source_type="metric")
        engine.add_knowledge("TikTok videos under 15 seconds had 2x completion rate", source_type="insight")
        engine.add_knowledge("LinkedIn posts on Tuesday mornings got highest CTR", source_type="metric")
        return engine

    def test_ask_returns_response(self, chat: AnalyticsChatEngine):
        resp = chat.ask("What hooks work best on Instagram?")
        assert isinstance(resp, ChatResponse)
        assert resp.answer != ""
        assert resp.query == "What hooks work best on Instagram?"

    def test_sources_found(self, chat: AnalyticsChatEngine):
        resp = chat.ask("Instagram hooks engagement")
        assert len(resp.sources) > 0

    def test_no_context_fallback(self):
        engine = AnalyticsChatEngine(workspace_id="ws-1")
        resp = engine.ask("What is quantum physics?")
        assert "don't have enough data" in resp.answer

    def test_history_tracked(self, chat: AnalyticsChatEngine):
        chat.ask("Hello")
        chat.ask("How are things?")
        history = chat.get_history()
        assert len(history) == 4  # 2 user + 2 assistant

    def test_clear_history(self, chat: AnalyticsChatEngine):
        chat.ask("Hello")
        chat.clear_history()
        assert len(chat.get_history()) == 0

    def test_confidence_scales_with_sources(self, chat: AnalyticsChatEngine):
        resp = chat.ask("Instagram hooks")
        assert resp.confidence > 0

    def test_chat_message_has_timestamp(self):
        msg = ChatMessage(role="user", content="Hi")
        assert msg.timestamp != ""
