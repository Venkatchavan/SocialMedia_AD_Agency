"""Unit tests for RightsEngine — deterministic rights verification."""

from __future__ import annotations

from app.services.rights_engine import RightsEngine


class TestRightsEngine:
    """Test suite for rights verification logic."""

    def test_licensed_direct_approved(
        self, rights_engine: RightsEngine, sample_reference_licensed: dict
    ):
        """Licensed direct references with valid license in registry should be APPROVED."""
        # First add a registry entry so it can be approved
        from app.schemas.rights import RightsRecord
        record = RightsRecord(
            id="rec-1",
            reference_title="Licensed Music Track",
            reference_type="licensed_direct",
            ip_owner="Test Publisher",
            license_id="LIC-001",
            license_scope={"commercial": True, "social": True, "derivative": False},
            status="active",
            risk_score=10,
            license_proof_url="https://example.com/license-proof.pdf",
        )
        rights_engine.add_to_registry(record)
        decision = rights_engine.verify(sample_reference_licensed)
        assert decision.decision == "APPROVE"
        assert decision.is_approved()

    def test_style_only_approved(
        self, rights_engine: RightsEngine, sample_reference_style: dict
    ):
        """Style-only references should be APPROVED."""
        decision = rights_engine.verify(sample_reference_style)
        assert decision.decision == "APPROVE"
        assert decision.is_approved()

    def test_missing_license_rejected(self, rights_engine: RightsEngine):
        """Licensed direct without license_id should be REJECTED."""
        ref = {
            "reference_id": "ref-no-license",
            "title": "Some licensed content",
            "reference_type": "licensed_direct",
            "risk_score": 30,
        }
        decision = rights_engine.verify(ref)
        assert decision.decision in ("REJECT", "REWRITE")
        assert not decision.is_approved()

    def test_unknown_type_rejected(self, rights_engine: RightsEngine):
        """Reference without registry match for licensed_direct should be REJECTED."""
        ref = {
            "reference_id": "ref-unknown",
            "title": "Unknown Content No Registry",
            "reference_type": "licensed_direct",
            "risk_score": 50,
        }
        decision = rights_engine.verify(ref)
        assert decision.decision == "REJECT"

    def test_public_domain_approved(self, rights_engine: RightsEngine):
        """Public domain references with registry entry should be APPROVED."""
        from app.schemas.rights import RightsRecord
        record = RightsRecord(
            id="rec-pd",
            reference_title="Pride and Prejudice",
            reference_type="public_domain",
            status="active",
            risk_score=5,
        )
        rights_engine.add_to_registry(record)
        ref = {
            "reference_id": "ref-pd",
            "title": "Pride and Prejudice",
            "reference_type": "public_domain",
            "risk_score": 5,
        }
        decision = rights_engine.verify(ref)
        assert decision.decision == "APPROVE"

    def test_commentary_with_high_risk_rewrite(self, rights_engine: RightsEngine):
        """Commentary references with blocked elements should trigger REWRITE."""
        from app.schemas.rights import RightsRecord
        record = RightsRecord(
            id="rec-tm",
            reference_title="Some trademarked thing",
            reference_type="commentary",
            status="active",
            risk_score=65,
            blocked_elements=["trademarked thing"],
        )
        rights_engine.add_to_registry(record)
        ref = {
            "reference_id": "ref-commentary",
            "title": "Some trademarked thing",
            "medium": "other",
            "reference_type": "commentary",
            "allowed_usage_mode": "Discussion about trademarked thing in context",
            "risk_score": 65,
        }
        decision = rights_engine.verify(ref)
        # Blocked elements present → REWRITE
        assert decision.decision in ("REWRITE", "REJECT")

    def test_every_decision_has_reason(self, rights_engine: RightsEngine):
        """Every rights decision must include a reason string."""
        refs = [
            {"reference_type": "licensed_direct", "license_id": "X", "risk_score": 5},
            {"reference_type": "public_domain", "risk_score": 5},
            {"reference_type": "style_only", "risk_score": 10},
            {"reference_type": "commentary", "risk_score": 30},
        ]
        for ref in refs:
            decision = rights_engine.verify(ref)
            assert decision.reason  # Must have a reason
