"""Tests for platform publishing (U-25) and scheduling (U-26)."""

from __future__ import annotations

import pytest

from app.publishers import (
    InstagramPublisher,
    LinkedInPublisher,
    PublishPlatform,
    PublishRequest,
    PublishResponse,
    SocialPublisher,
    TikTokPublisher,
    TokenVault,
    XPublisher,
    get_publisher,
)
from app.scheduling import (
    BEST_TIMES,
    PublishScheduler,
    ScheduledPost,
    ScheduleStatus,
)


# ── TokenVault ──


class TestTokenVault:
    def test_store_and_retrieve(self):
        vault = TokenVault()
        vault.store_token("ws-1", "instagram", "secret-token-123")
        token = vault.get_token("ws-1", "instagram")
        assert token == "secret-token-123"

    def test_missing_token_returns_none(self):
        vault = TokenVault()
        assert vault.get_token("ws-1", "tiktok") is None

    def test_revoke_token(self):
        vault = TokenVault()
        vault.store_token("ws-1", "x", "tok")
        assert vault.revoke_token("ws-1", "x")
        assert vault.get_token("ws-1", "x") is None

    def test_revoke_nonexistent_returns_false(self):
        vault = TokenVault()
        assert not vault.revoke_token("ws-1", "x")

    def test_different_workspaces_isolated(self):
        vault = TokenVault()
        vault.store_token("ws-1", "instagram", "token-1")
        vault.store_token("ws-2", "instagram", "token-2")
        assert vault.get_token("ws-1", "instagram") == "token-1"
        assert vault.get_token("ws-2", "instagram") == "token-2"


# ── Publishers ──


class TestPublishers:
    @pytest.fixture
    def vault(self) -> TokenVault:
        v = TokenVault()
        v.store_token("ws-1", "instagram", "ig-tok")
        v.store_token("ws-1", "tiktok", "tt-tok")
        v.store_token("ws-1", "linkedin", "li-tok")
        v.store_token("ws-1", "x", "x-tok")
        return v

    def test_instagram_publish(self, vault: TokenVault):
        pub = InstagramPublisher(vault)
        req = PublishRequest(content_id="c1", workspace_id="ws-1", platform=PublishPlatform.INSTAGRAM, caption="Hello")
        result = pub.publish(req, compliance_status="APPROVED", qa_status="APPROVE", content_hash="abc123")
        assert result.success
        assert "ig_" in result.post_id

    def test_tiktok_publish(self, vault: TokenVault):
        pub = TikTokPublisher(vault)
        req = PublishRequest(content_id="c2", workspace_id="ws-1", platform=PublishPlatform.TIKTOK, caption="Hey")
        result = pub.publish(req, compliance_status="APPROVED", qa_status="APPROVE", content_hash="def456")
        assert result.success
        assert "tt_" in result.post_id

    def test_linkedin_publish(self, vault: TokenVault):
        pub = LinkedInPublisher(vault)
        req = PublishRequest(content_id="c3", workspace_id="ws-1", platform=PublishPlatform.LINKEDIN, caption="Pro")
        result = pub.publish(req, compliance_status="APPROVED", qa_status="APPROVE", content_hash="ghi789")
        assert result.success

    def test_x_publish(self, vault: TokenVault):
        pub = XPublisher(vault)
        req = PublishRequest(content_id="c4", workspace_id="ws-1", platform=PublishPlatform.X, caption="Tweet")
        result = pub.publish(req, compliance_status="APPROVED", qa_status="APPROVE", content_hash="jkl012")
        assert result.success

    def test_no_token_fails(self):
        vault = TokenVault()
        pub = InstagramPublisher(vault)
        req = PublishRequest(content_id="c5", workspace_id="ws-1", platform=PublishPlatform.INSTAGRAM, caption="No tok")
        result = pub.publish(req, compliance_status="APPROVED", qa_status="APPROVE")
        assert not result.success
        assert "OAuth token" in result.error

    def test_factory_get_publisher(self, vault: TokenVault):
        pub = get_publisher(PublishPlatform.INSTAGRAM, vault)
        assert isinstance(pub, InstagramPublisher)

    def test_factory_unknown_raises(self, vault: TokenVault):
        with pytest.raises(ValueError, match="No publisher"):
            get_publisher(PublishPlatform.YOUTUBE, vault)

    # ── Rule 1: Compliance gate enforcement ──

    def test_publish_blocked_without_compliance(self, vault: TokenVault):
        """Rule 1: Cannot publish without compliance_status=APPROVED."""
        pub = InstagramPublisher(vault)
        req = PublishRequest(content_id="c6", workspace_id="ws-1", platform=PublishPlatform.INSTAGRAM, caption="Hey")
        result = pub.publish(req, compliance_status="PENDING", qa_status="APPROVE")
        assert not result.success
        assert "Compliance gate" in result.error

    def test_publish_blocked_without_qa(self, vault: TokenVault):
        """Rule 1: Cannot publish without qa_status=APPROVE."""
        pub = InstagramPublisher(vault)
        req = PublishRequest(content_id="c7", workspace_id="ws-1", platform=PublishPlatform.INSTAGRAM, caption="Hey")
        result = pub.publish(req, compliance_status="APPROVED", qa_status="REJECT")
        assert not result.success
        assert "QA gate" in result.error

    def test_publish_blocked_empty_compliance(self, vault: TokenVault):
        """Rule 1: Empty compliance_status is not APPROVED."""
        pub = InstagramPublisher(vault)
        req = PublishRequest(content_id="c8", workspace_id="ws-1", platform=PublishPlatform.INSTAGRAM, caption="Hey")
        result = pub.publish(req)  # no compliance/qa args
        assert not result.success

    # ── Rule 9: Anti-spam / dedup ──

    def test_duplicate_content_hash_blocked(self, vault: TokenVault):
        """Rule 9: No duplicate content hash on same platform."""
        pub = InstagramPublisher(vault)
        req = PublishRequest(content_id="c9", workspace_id="ws-1", platform=PublishPlatform.INSTAGRAM, caption="Dup")
        pub.publish(req, compliance_status="APPROVED", qa_status="APPROVE", content_hash="same_hash")
        req2 = PublishRequest(content_id="c10", workspace_id="ws-1", platform=PublishPlatform.INSTAGRAM, caption="Dup2")
        result = pub.publish(req2, compliance_status="APPROVED", qa_status="APPROVE", content_hash="same_hash")
        assert not result.success
        assert "Duplicate" in result.error


# ── PublishScheduler ──


class TestPublishScheduler:
    @pytest.fixture
    def scheduler(self) -> PublishScheduler:
        return PublishScheduler()

    def test_schedule_post(self, scheduler: PublishScheduler):
        post = scheduler.schedule("p1", "c1", "ws-1", "instagram", "2025-01-15T10:00:00Z")
        assert post.status == ScheduleStatus.SCHEDULED
        assert post.post_id == "p1"

    def test_cancel_post(self, scheduler: PublishScheduler):
        scheduler.schedule("p1", "c1", "ws-1", "instagram", "2025-01-15T10:00:00Z")
        assert scheduler.cancel("p1")

    def test_cancel_nonexistent(self, scheduler: PublishScheduler):
        assert not scheduler.cancel("missing")

    def test_mark_published(self, scheduler: PublishScheduler):
        scheduler.schedule("p1", "c1", "ws-1", "instagram", "2025-01-15T10:00:00Z")
        scheduler.mark_published("p1", {"url": "https://ig.com/p1"})
        cal = scheduler.get_calendar("ws-1")
        assert cal[0].status == ScheduleStatus.PUBLISHED

    def test_mark_failed_retries(self, scheduler: PublishScheduler):
        scheduler.schedule("p1", "c1", "ws-1", "instagram", "2025-01-15T10:00:00Z")
        scheduler.mark_failed("p1", error="API error")
        cal = scheduler.get_calendar("ws-1")
        assert cal[0].status == ScheduleStatus.QUEUED  # retry
        assert cal[0].retry_count == 1

    def test_mark_failed_max_retries(self, scheduler: PublishScheduler):
        scheduler.schedule("p1", "c1", "ws-1", "instagram", "2025-01-15T10:00:00Z")
        for _ in range(3):
            scheduler.mark_failed("p1")
        cal = scheduler.get_calendar("ws-1")
        assert cal[0].status == ScheduleStatus.FAILED

    def test_get_due_returns_past_posts(self, scheduler: PublishScheduler):
        scheduler.schedule("p1", "c1", "ws-1", "instagram", "2020-01-01T00:00:00Z")
        due = scheduler.get_due()
        assert len(due) == 1

    def test_calendar_filters_workspace(self, scheduler: PublishScheduler):
        scheduler.schedule("p1", "c1", "ws-1", "instagram", "2025-01-15T10:00:00Z")
        scheduler.schedule("p2", "c2", "ws-2", "x", "2025-01-15T10:00:00Z")
        assert len(scheduler.get_calendar("ws-1")) == 1
        assert len(scheduler.get_calendar("ws-2")) == 1

    def test_best_time(self, scheduler: PublishScheduler):
        best = scheduler.get_best_time("instagram")
        assert best is not None
        assert "day" in best and "hour" in best

    def test_best_time_unknown(self, scheduler: PublishScheduler):
        assert scheduler.get_best_time("threads") is None

    def test_count_by_status(self, scheduler: PublishScheduler):
        scheduler.schedule("p1", "c1", "ws-1", "ig", "2025-01-15T10:00:00Z")
        scheduler.schedule("p2", "c2", "ws-1", "ig", "2025-01-16T10:00:00Z")
        scheduler.mark_published("p1")
        counts = scheduler.count_by_status("ws-1")
        assert counts.get("published", 0) == 1
        assert counts.get("scheduled", 0) == 1

    def test_best_times_data(self):
        assert "instagram" in BEST_TIMES
        assert "tiktok" in BEST_TIMES
