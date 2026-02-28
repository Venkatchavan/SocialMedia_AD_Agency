"""Unit tests for AuditLogger — hash chain integrity."""

from __future__ import annotations

from app.services.audit_logger import AuditLogger


class TestAuditLogger:
    """Test suite for audit logging and hash chain."""

    def test_log_creates_event(self, audit_logger: AuditLogger):
        """Logging should create an audit event."""
        audit_logger.log(
            agent_id="test_agent",
            action="test_action",
            decision="APPROVED",
            reason="Test",
        )
        assert len(audit_logger._events) == 1

    def test_hash_chain_links(self, audit_logger: AuditLogger):
        """Each event should link to the previous event's hash."""
        audit_logger.log(
            agent_id="agent1",
            action="action1",
            decision="APPROVED",
            reason="First",
        )
        audit_logger.log(
            agent_id="agent2",
            action="action2",
            decision="APPROVED",
            reason="Second",
        )
        assert len(audit_logger._events) == 2
        # Second event should reference the first event's hash
        assert audit_logger._events[1].previous_event_hash != ""

    def test_chain_integrity_verification(self, audit_logger: AuditLogger):
        """Chain integrity verification should pass for untampered chain."""
        for i in range(5):
            audit_logger.log(
                agent_id=f"agent_{i}",
                action=f"action_{i}",
                decision="APPROVED",
                reason=f"Event {i}",
            )
        assert audit_logger.verify_chain_integrity()

    def test_empty_chain_is_valid(self, audit_logger: AuditLogger):
        """An empty chain should be considered valid."""
        assert audit_logger.verify_chain_integrity()

    def test_single_event_chain_valid(self, audit_logger: AuditLogger):
        """A single-event chain should be valid."""
        audit_logger.log(
            agent_id="solo",
            action="single",
            decision="APPROVED",
            reason="Only event",
        )
        assert audit_logger.verify_chain_integrity()
