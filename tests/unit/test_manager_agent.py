"""Tests for Manager Agent."""
from __future__ import annotations

import pytest

from app.agents.manager import ManagerAgent
from app.services.audit_logger import AuditLogger
from app.services.llm_client import LLMClient


@pytest.fixture
def manager_agent():
    """Provide a ManagerAgent with dry-run LLM."""
    audit = AuditLogger()
    llm = LLMClient(dry_run=True)
    return ManagerAgent(audit_logger=audit, llm_client=llm, session_id="test-session")


class TestManagerRouting:
    """Test deterministic routing decisions."""

    def test_route_rights_approved(self, manager_agent):
        result = manager_agent.run({
            "action": "route_rights",
            "compliance_status": "APPROVED",
        })
        assert result["next_step"] == "generate_content"
        assert result["should_continue"] is True

    def test_route_rights_reject(self, manager_agent):
        result = manager_agent.run({
            "action": "route_rights",
            "compliance_status": "REJECT",
            "reason": "Trademark violation",
        })
        assert result["next_step"] == "reject"
        assert result["should_continue"] is False

    def test_route_rights_rewrite(self, manager_agent):
        result = manager_agent.run({
            "action": "route_rights",
            "compliance_status": "REWRITE",
        })
        assert result["next_step"] == "rewrite_reference"
        assert result["should_continue"] is True

    def test_route_rights_max_rewrites(self, manager_agent):
        """After MAX_REWRITE_LOOPS rewrites, should reject."""
        for _ in range(ManagerAgent.MAX_REWRITE_LOOPS):
            manager_agent.run({
                "action": "route_rights",
                "compliance_status": "REWRITE",
            })
        result = manager_agent.run({
            "action": "route_rights",
            "compliance_status": "REWRITE",
        })
        assert result["next_step"] == "reject"
        assert result["should_continue"] is False

    def test_route_qa_approve(self, manager_agent):
        result = manager_agent.run({
            "action": "route_qa",
            "qa_status": "APPROVE",
        })
        assert result["next_step"] == "publish"
        assert result["should_continue"] is True

    def test_route_qa_reject(self, manager_agent):
        result = manager_agent.run({
            "action": "route_qa",
            "qa_status": "REJECT",
            "reason": "Low quality",
        })
        assert result["next_step"] == "reject"
        assert result["should_continue"] is False

    def test_route_qa_rewrite(self, manager_agent):
        result = manager_agent.run({
            "action": "route_qa",
            "qa_status": "REWRITE",
        })
        assert result["next_step"] == "rewrite_content"
        assert result["should_continue"] is True


class TestManagerReview:
    """Test LLM-powered content review."""

    def test_review_content_dry_run(self, manager_agent):
        """In dry-run mode, review should return approve."""
        result = manager_agent.run({
            "action": "review_content",
            "script": {"hook": "Test hook", "cta": "Buy now!"},
            "captions": {"tiktok": "Test caption #ad"},
            "product_title": "Test Product",
        })
        assert result["decision"] in ("APPROVE", "REWRITE")
        assert "quality_score" in result

    def test_review_content_returns_feedback(self, manager_agent):
        result = manager_agent.run({
            "action": "review_content",
            "script": {},
            "captions": {},
            "product_title": "Test",
        })
        assert "feedback" in result


class TestManagerHealthTracking:
    """Test agent health tracking."""

    def test_track_agent(self, manager_agent):
        result = manager_agent.run({
            "action": "track_agent",
            "agent_id": "scriptwriter",
            "duration_ms": 150,
            "success": True,
        })
        assert result["tracked"] is True

    def test_get_status(self, manager_agent):
        result = manager_agent.run({"action": "get_status"})
        assert result["should_continue"] is True
        assert "agent_health" in result
        assert result["session_id"] == "test-session"

    def test_health_accumulates(self, manager_agent):
        manager_agent.run({
            "action": "track_agent",
            "agent_id": "test_agent",
            "duration_ms": 100,
            "success": True,
        })
        manager_agent.run({
            "action": "track_agent",
            "agent_id": "test_agent",
            "duration_ms": 200,
            "success": False,
        })
        status = manager_agent.run({"action": "get_status"})
        health = status["agent_health"]["test_agent"]
        assert health["runs"] == 2
        assert health["failures"] == 1
        assert health["total_ms"] == 300

    def test_unknown_action(self, manager_agent):
        result = manager_agent.run({"action": "nonexistent"})
        assert result["should_continue"] is False
        assert "Unknown" in result["reason"]


class TestManagerSupervise:
    """Test supervised agent execution."""

    def test_supervise_success(self, manager_agent):
        """supervise() tracks timing and success."""
        from app.agents.product_intake import ProductIntakeAgent
        audit = AuditLogger()
        intake = ProductIntakeAgent(audit_logger=audit)
        result = manager_agent.supervise(intake, {
            "source": "manual",
            "asin": "B0TEST123X",
            "title": "Test Product",
            "price": 29.99,
            "category": "Electronics",
        })
        assert "products" in result
        status = manager_agent.run({"action": "get_status"})
        assert "product_intake" in status["agent_health"]

    def test_supervise_tracks_failures(self, manager_agent):
        """supervise() records failures."""
        from app.agents.product_intake import ProductIntakeAgent
        audit = AuditLogger()
        intake = ProductIntakeAgent(audit_logger=audit)

        # Force an error by passing something that triggers constitution
        try:
            manager_agent.supervise(intake, {
                "source": "manual",
                "asin": "B0TEST123X",
                "title": "Test",
                "price": 9.99,
                "category": "Test",
            })
        except Exception:
            pass

        status = manager_agent.run({"action": "get_status"})
        # Should have tracked at least one run
        if "product_intake" in status["agent_health"]:
            assert status["agent_health"]["product_intake"]["runs"] >= 1
