"""Deterministic rights verification engine.

CRITICAL: This is NOT LLM-based. All decisions are rule-based and deterministic.
Compliance decisions MUST be reproducible and logged.

Security rules enforced (from Agents.md):
- compliance_status must be APPROVED before any content is rendered or published
- Every reference must be tagged with reference_type
- Direct visual/audio reuse only for licensed_direct or public_domain
- style_only cannot include exact character names/logos/signature elements
- All decisions logged to audit trail
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import structlog

from app.schemas.reference import Reference, ReferenceBundle
from app.schemas.rights import RightsDecision, RightsRecord
from app.services.audit_logger import AuditLogger
from app.services.rights_checks import (
    check_commentary,
    check_licensed,
    check_public_domain,
    check_style_only,
)

logger = structlog.get_logger(__name__)


class RightsEngine:
    """Deterministic rights verification. No LLM opinion allowed.

    Every decision is logged to the audit trail.
    On uncertainty, the default is REJECT (never publish).
    """

    def __init__(
        self,
        audit_logger: AuditLogger,
        registry: dict[str, RightsRecord] | None = None,
    ) -> None:
        self._audit = audit_logger
        self._registry: dict[str, RightsRecord] = registry or {}

    def verify_bundle(
        self, bundle: ReferenceBundle, session_id: str = ""
    ) -> list[RightsDecision]:
        """Verify all references in a bundle. Returns a decision for each."""
        decisions: list[RightsDecision] = []
        for reference in bundle.references:
            decision = self.verify(reference, session_id=session_id)
            decisions.append(decision)
        return decisions

    def verify(self, reference: Reference | dict, session_id: str = "") -> RightsDecision:
        """Verify a single reference against the rights registry.

        Accepts a Reference object or a dict with reference fields.
        Returns APPROVE, REWRITE, or REJECT with deterministic reasoning.
        """
        if isinstance(reference, dict):
            reference = self._dict_to_reference(reference)

        # Look up in registry
        record = self._registry.get(reference.title.lower())

        # Route by reference type
        checkers = {
            "licensed_direct": check_licensed,
            "public_domain": check_public_domain,
            "style_only": check_style_only,
            "commentary": check_commentary,
        }
        checker = checkers.get(reference.reference_type)
        if checker:
            decision = checker(reference, record)
        else:
            decision = RightsDecision(
                reference_id=reference.reference_id,
                reference_title=reference.title,
                reference_type=reference.reference_type,
                decision="REJECT",
                reason=f"Unknown reference_type: {reference.reference_type}",
                risk_score=100,
            )

        # Set audit ID
        decision.audit_id = str(uuid.uuid4())
        decision.timestamp = datetime.now(tz=UTC)

        # Log audit event (MANDATORY — never skip)
        self._audit.log(
            agent_id="rights_engine",
            action="verify_reference",
            decision=decision.decision,
            reason=decision.reason,
            input_data={
                "reference_id": reference.reference_id,
                "title": reference.title,
                "type": reference.reference_type,
            },
            output_data={
                "decision": decision.decision,
                "risk_score": decision.risk_score,
            },
            session_id=session_id,
            metadata={"audit_id": decision.audit_id},
        )

        logger.info(
            "rights_decision",
            reference_id=reference.reference_id,
            title=reference.title,
            decision=decision.decision,
            risk_score=decision.risk_score,
        )

        return decision

    def add_to_registry(self, record: RightsRecord) -> None:
        """Add or update a rights record in the registry."""
        self._registry[record.reference_title.lower()] = record
        self._audit.log(
            agent_id="rights_engine",
            action="registry_update",
            decision="UPDATED",
            reason=f"Registry entry added/updated for '{record.reference_title}'",
            input_data={"title": record.reference_title, "type": record.reference_type},
        )

    @staticmethod
    def _dict_to_reference(data: dict) -> Reference:
        """Convert a dict to a Reference, filling defaults for missing fields."""
        defaults = {
            "reference_id": data.get("reference_id", "unknown"),
            "title": data.get("title", "Unknown"),
            "medium": data.get("medium", "other"),
            "reference_type": data.get("reference_type", "commentary"),
            "allowed_usage_mode": data.get("allowed_usage_mode", ""),
            "risk_score": data.get("risk_score", 50),
            "audience_overlap_score": data.get("audience_overlap_score", 0.0),
            "trending_relevance": data.get("trending_relevance", 0.0),
            "created_at": datetime.now(tz=UTC),
            "updated_at": datetime.now(tz=UTC),
        }
        if "license_id" in data:
            defaults["source_metadata"] = {"license_id": data["license_id"]}
        return Reference(**defaults)
