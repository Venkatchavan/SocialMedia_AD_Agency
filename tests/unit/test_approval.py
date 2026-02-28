"""Tests for human approval gate (U-24)."""

from __future__ import annotations

import pytest

from app.approval import (
    ApprovalGate,
    ContentItem,
    ContentStatus,
)


@pytest.fixture
def gate() -> ApprovalGate:
    return ApprovalGate()


@pytest.fixture
def sample_item() -> ContentItem:
    return ContentItem(
        content_id="c-001",
        workspace_id="ws-1",
        platform="instagram",
        content_type="caption",
        caption="Check out this product!",
        hashtags=["ad", "product"],
    )


class TestSubmitForReview:
    def test_submit_sets_status(self, gate: ApprovalGate, sample_item: ContentItem):
        result = gate.submit_for_review(sample_item)
        assert result.status == ContentStatus.READY_FOR_REVIEW
        assert result.created_at != ""

    def test_submitted_appears_in_pending(self, gate: ApprovalGate, sample_item: ContentItem):
        gate.submit_for_review(sample_item)
        pending = gate.get_pending("ws-1")
        assert len(pending) == 1
        assert pending[0].content_id == "c-001"


class TestApproval:
    def test_approve_success(self, gate: ApprovalGate, sample_item: ContentItem):
        gate.submit_for_review(sample_item)
        decision = gate.approve("c-001", reviewer="alice@test.com")
        assert decision.success
        assert decision.action == "approve"
        item = gate.get_item("c-001")
        assert item is not None
        assert item.status == ContentStatus.APPROVED

    def test_approve_with_schedule(self, gate: ApprovalGate, sample_item: ContentItem):
        gate.submit_for_review(sample_item)
        decision = gate.approve("c-001", reviewer="alice", scheduled_at="2025-01-15T10:00:00Z")
        assert decision.success
        item = gate.get_item("c-001")
        assert item is not None
        assert item.status == ContentStatus.SCHEDULED

    def test_approve_nonexistent_fails(self, gate: ApprovalGate):
        decision = gate.approve("missing", reviewer="alice")
        assert not decision.success
        assert "not found" in decision.error

    def test_approve_already_rejected_fails(self, gate: ApprovalGate, sample_item: ContentItem):
        gate.submit_for_review(sample_item)
        gate.reject("c-001", reviewer="bob")
        decision = gate.approve("c-001", reviewer="alice")
        assert not decision.success
        assert "Cannot approve" in decision.error


class TestRejection:
    def test_reject_success(self, gate: ApprovalGate, sample_item: ContentItem):
        gate.submit_for_review(sample_item)
        decision = gate.reject("c-001", reviewer="bob", notes="Off-brand")
        assert decision.success
        item = gate.get_item("c-001")
        assert item is not None
        assert item.status == ContentStatus.REJECTED
        assert item.review_notes == "Off-brand"

    def test_reject_nonexistent_fails(self, gate: ApprovalGate):
        decision = gate.reject("missing", reviewer="bob")
        assert not decision.success


class TestEdit:
    def test_edit_caption(self, gate: ApprovalGate, sample_item: ContentItem):
        gate.submit_for_review(sample_item)
        decision = gate.edit("c-001", reviewer="alice", caption="New caption!")
        assert decision.success
        item = gate.get_item("c-001")
        assert item is not None
        assert item.caption == "New caption!"
        assert item.status == ContentStatus.IN_REVIEW

    def test_edit_hashtags(self, gate: ApprovalGate, sample_item: ContentItem):
        gate.submit_for_review(sample_item)
        gate.edit("c-001", reviewer="alice", hashtags=["new", "tags"])
        item = gate.get_item("c-001")
        assert item is not None
        assert item.hashtags == ["new", "tags"]

    def test_edit_nonexistent_fails(self, gate: ApprovalGate):
        decision = gate.edit("missing", reviewer="alice")
        assert not decision.success


class TestQueries:
    def test_get_pending_filters_workspace(self, gate: ApprovalGate):
        gate.submit_for_review(ContentItem(content_id="a", workspace_id="ws-1", platform="x", content_type="t"))
        gate.submit_for_review(ContentItem(content_id="b", workspace_id="ws-2", platform="x", content_type="t"))
        assert len(gate.get_pending("ws-1")) == 1
        assert len(gate.get_pending("ws-2")) == 1

    def test_get_approved_list(self, gate: ApprovalGate, sample_item: ContentItem):
        gate.submit_for_review(sample_item)
        gate.approve("c-001", reviewer="alice")
        approved = gate.get_approved("ws-1")
        assert len(approved) == 1

    def test_get_item_none(self, gate: ApprovalGate):
        assert gate.get_item("nonexistent") is None
