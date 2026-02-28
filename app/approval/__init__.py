"""Human approval gate (U-24).

Nothing auto-publishes without human approval. Non-negotiable.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class ContentStatus(str, Enum):
    """Content review lifecycle."""

    DRAFT = "draft"
    READY_FOR_REVIEW = "ready_for_review"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


@dataclass
class ContentItem:
    """A piece of content awaiting approval."""

    content_id: str
    workspace_id: str
    platform: str
    content_type: str  # caption, image, video
    caption: str = ""
    media_urls: list[str] = field(default_factory=list)
    hashtags: list[str] = field(default_factory=list)
    scheduled_at: str = ""
    status: ContentStatus = ContentStatus.DRAFT
    created_at: str = ""
    reviewed_by: str = ""
    review_notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReviewDecision:
    """Result of a content review action."""

    content_id: str
    action: str  # approve, reject, edit
    reviewer: str
    timestamp: str
    notes: str = ""
    success: bool = True
    error: str = ""


class ApprovalGate:
    """Manages the content review and approval workflow.

    Core rule: NOTHING publishes without explicit human approval.
    """

    def __init__(self) -> None:
        self._items: dict[str, ContentItem] = {}

    def submit_for_review(self, item: ContentItem) -> ContentItem:
        """Submit content for human review."""
        item.status = ContentStatus.READY_FOR_REVIEW
        item.created_at = datetime.now(UTC).isoformat()
        self._items[item.content_id] = item

        logger.info(
            "content_submitted_for_review",
            content_id=item.content_id,
            workspace_id=item.workspace_id,
            platform=item.platform,
        )
        return item

    def approve(
        self, content_id: str, reviewer: str,
        scheduled_at: str = "", notes: str = "",
    ) -> ReviewDecision:
        """Approve content for publishing."""
        item = self._items.get(content_id)
        if item is None:
            return self._not_found(content_id, "approve", reviewer)
        if item.status not in (ContentStatus.READY_FOR_REVIEW, ContentStatus.IN_REVIEW):
            return ReviewDecision(
                content_id=content_id, action="approve", reviewer=reviewer,
                timestamp=datetime.now(UTC).isoformat(), success=False,
                error=f"Cannot approve content in status: {item.status.value}",
            )

        item.status = ContentStatus.APPROVED if not scheduled_at else ContentStatus.SCHEDULED
        item.reviewed_by = reviewer
        item.review_notes = notes
        if scheduled_at:
            item.scheduled_at = scheduled_at

        # Rule 7: Audit event with hashes
        self._log_audit(
            action="approve",
            content_id=content_id,
            reviewer=reviewer,
            content_hash=self._hash_content(item),
            reason=notes,
        )
        return ReviewDecision(
            content_id=content_id,
            action="approve",
            reviewer=reviewer,
            timestamp=datetime.now(UTC).isoformat(),
            notes=notes,
        )

    def reject(
        self, content_id: str, reviewer: str, notes: str = "",
    ) -> ReviewDecision:
        """Reject content — will not be published."""
        item = self._items.get(content_id)
        if item is None:
            return self._not_found(content_id, "reject", reviewer)

        item.status = ContentStatus.REJECTED
        item.reviewed_by = reviewer
        item.review_notes = notes

        # Rule 7: Audit event
        self._log_audit(
            action="reject",
            content_id=content_id,
            reviewer=reviewer,
            content_hash=self._hash_content(item),
            reason=notes,
        )
        return ReviewDecision(
            content_id=content_id,
            action="reject",
            reviewer=reviewer,
            timestamp=datetime.now(UTC).isoformat(),
            notes=notes,
        )

    def edit(
        self, content_id: str, reviewer: str,
        caption: str | None = None, hashtags: list[str] | None = None,
    ) -> ReviewDecision:
        """Edit content inline before approving."""
        item = self._items.get(content_id)
        if item is None:
            return self._not_found(content_id, "edit", reviewer)

        if caption is not None:
            item.caption = caption
        if hashtags is not None:
            item.hashtags = hashtags
        item.status = ContentStatus.IN_REVIEW

        # Rule 7: Audit event for edits (no silent rewrites)
        self._log_audit(
            action="edit",
            content_id=content_id,
            reviewer=reviewer,
            content_hash=self._hash_content(item),
            reason="inline_edit",
        )
        return ReviewDecision(
            content_id=content_id,
            action="edit",
            reviewer=reviewer,
            timestamp=datetime.now(UTC).isoformat(),
        )

    def get_pending(self, workspace_id: str) -> list[ContentItem]:
        """Get all content pending review for a workspace."""
        return [
            item
            for item in self._items.values()
            if item.workspace_id == workspace_id
            and item.status in (ContentStatus.READY_FOR_REVIEW, ContentStatus.IN_REVIEW)
        ]

    def get_item(self, content_id: str) -> ContentItem | None:
        """Get a specific content item."""
        return self._items.get(content_id)

    def get_approved(self, workspace_id: str) -> list[ContentItem]:
        """Get approved content ready for scheduling/publishing."""
        return [
            item
            for item in self._items.values()
            if item.workspace_id == workspace_id
            and item.status in (ContentStatus.APPROVED, ContentStatus.SCHEDULED)
        ]

    # ── Rule 7: Auditability helpers ──

    @staticmethod
    def _not_found(content_id: str, action: str, reviewer: str) -> ReviewDecision:
        """Return a failure ReviewDecision when content is not found."""
        return ReviewDecision(
            content_id=content_id, action=action, reviewer=reviewer,
            timestamp=datetime.now(UTC).isoformat(),
            success=False, error="Content not found",
        )

    @staticmethod
    def _hash_content(item: ContentItem) -> str:
        """Compute deterministic hash of content for audit trail."""
        payload = f"{item.caption}|{','.join(item.hashtags)}|{item.platform}"
        return hashlib.sha256(payload.encode()).hexdigest()[:16]

    @staticmethod
    def _log_audit(
        action: str,
        content_id: str,
        reviewer: str,
        content_hash: str,
        reason: str = "",
    ) -> None:
        """Create an audit event per Rule 7 (who, input hash, decision, timestamp, reason)."""
        logger.info(
            "approval_audit_event",
            agent="approval_gate",
            action=action,
            content_id=content_id,
            reviewer=reviewer,
            content_hash=content_hash,
            timestamp=datetime.now(UTC).isoformat(),
            reason=reason,
        )
