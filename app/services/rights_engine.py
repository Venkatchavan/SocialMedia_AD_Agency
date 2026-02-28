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
from datetime import datetime, timezone
from typing import Optional

import structlog

from app.schemas.reference import Reference, ReferenceBundle, ScoredReference
from app.schemas.rights import RightsDecision, RightsRecord
from app.services.audit_logger import AuditLogger

logger = structlog.get_logger(__name__)


# Known IP elements that must be blocked in style_only references
KNOWN_TRADEMARK_PATTERNS: list[str] = [
    # These are examples — the production registry would be much larger
    "mario", "luigi", "pokemon", "pikachu", "naruto", "sasuke",
    "goku", "vegeta", "spider-man", "spiderman", "batman", "superman",
    "iron man", "ironman", "captain america", "thor", "hulk",
    "mickey mouse", "disney", "marvel", "dc comics",
    "tanjiro", "nezuko", "demon slayer", "jujutsu kaisen",
    "one piece", "luffy", "zoro",
]


class RightsEngine:
    """Deterministic rights verification. No LLM opinion allowed.

    Every decision is logged to the audit trail.
    On uncertainty, the default is REJECT (never publish).
    """

    def __init__(
        self,
        audit_logger: AuditLogger,
        registry: Optional[dict[str, RightsRecord]] = None,
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
        if reference.reference_type == "licensed_direct":
            decision = self._check_licensed(reference, record)
        elif reference.reference_type == "public_domain":
            decision = self._check_public_domain(reference, record)
        elif reference.reference_type == "style_only":
            decision = self._check_style_only(reference, record)
        elif reference.reference_type == "commentary":
            decision = self._check_commentary(reference, record)
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
        decision.timestamp = datetime.now(tz=timezone.utc)

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

    def _check_licensed(
        self, ref: Reference, record: Optional[RightsRecord]
    ) -> RightsDecision:
        """Check licensed_direct: requires active license with commercial+social scope."""
        base = {
            "reference_id": ref.reference_id,
            "reference_title": ref.title,
            "reference_type": ref.reference_type,
        }

        if not record:
            return RightsDecision(
                **base,
                decision="REJECT",
                reason="No license record found for direct use",
                risk_score=95,
            )

        if record.status != "active":
            return RightsDecision(
                **base,
                decision="REJECT",
                reason=f"License status is '{record.status}', not active",
                risk_score=90,
            )

        if record.license_expiry and record.license_expiry < datetime.now(tz=timezone.utc):
            return RightsDecision(
                **base,
                decision="REJECT",
                reason="License has expired",
                risk_score=90,
            )

        if not record.license_scope.get("commercial"):
            return RightsDecision(
                **base,
                decision="REJECT",
                reason="License does not cover commercial use",
                risk_score=85,
            )

        if not record.license_scope.get("social"):
            return RightsDecision(
                **base,
                decision="REJECT",
                reason="License does not cover social media distribution",
                risk_score=80,
            )

        if not record.license_proof_url:
            return RightsDecision(
                **base,
                decision="REJECT",
                reason="No license proof document on file",
                risk_score=85,
            )

        return RightsDecision(
            **base,
            decision="APPROVE",
            reason="Valid active license with commercial + social scope",
            risk_score=10,
        )

    def _check_public_domain(
        self, ref: Reference, record: Optional[RightsRecord]
    ) -> RightsDecision:
        """Check public_domain: must be confirmed public domain."""
        base = {
            "reference_id": ref.reference_id,
            "reference_title": ref.title,
            "reference_type": ref.reference_type,
        }

        # Check if we have a registry entry confirming public domain
        if record and record.reference_type == "public_domain" and record.status == "active":
            return RightsDecision(
                **base,
                decision="APPROVE",
                reason="Confirmed public domain in registry",
                risk_score=5,
            )

        # If no record but it's a well-known public domain work, we could check
        # For now, without confirmation, we REJECT (fail-safe)
        if not record:
            return RightsDecision(
                **base,
                decision="REJECT",
                reason="Public domain status unconfirmed — no registry entry",
                risk_score=60,
            )

        return RightsDecision(
            **base,
            decision="REJECT",
            reason=f"Registry entry exists but type is '{record.reference_type}', not public_domain",
            risk_score=70,
        )

    def _check_style_only(
        self, ref: Reference, record: Optional[RightsRecord]
    ) -> RightsDecision:
        """Check style_only: must not include specific IP elements."""
        base = {
            "reference_id": ref.reference_id,
            "reference_title": ref.title,
            "reference_type": ref.reference_type,
        }

        # Check for trademarked/copyrighted elements in usage mode and title
        violations = self._find_ip_violations(ref)

        if violations:
            return RightsDecision(
                **base,
                decision="REWRITE",
                reason=f"Style reference contains IP elements that must be removed: {violations}",
                risk_score=65,
                rewrite_instructions=(
                    f"Remove these specific elements: {violations}. "
                    "Replace with generic style/aesthetic descriptors."
                ),
            )

        # Check if auto-blocked in registry
        if record and record.auto_block:
            return RightsDecision(
                **base,
                decision="REJECT",
                reason="Reference is auto-blocked in rights registry",
                risk_score=100,
            )

        return RightsDecision(
            **base,
            decision="APPROVE",
            reason="Style reference with no IP elements detected",
            risk_score=max(ref.risk_score, 15),
        )

    def _check_commentary(
        self, ref: Reference, record: Optional[RightsRecord]
    ) -> RightsDecision:
        """Check commentary: must be genuine commentary, not promotional impersonation."""
        base = {
            "reference_id": ref.reference_id,
            "reference_title": ref.title,
            "reference_type": ref.reference_type,
        }

        # Check for auto-block
        if record and record.auto_block:
            return RightsDecision(
                **base,
                decision="REJECT",
                reason="Reference is auto-blocked in rights registry",
                risk_score=100,
            )

        # Commentary with known blocked elements
        if record and record.blocked_elements:
            usage_lower = ref.allowed_usage_mode.lower()
            found_blocked = [
                elem for elem in record.blocked_elements if elem.lower() in usage_lower
            ]
            if found_blocked:
                return RightsDecision(
                    **base,
                    decision="REWRITE",
                    reason=f"Commentary references blocked elements: {found_blocked}",
                    risk_score=55,
                    rewrite_instructions=f"Remove references to: {found_blocked}",
                )

        return RightsDecision(
            **base,
            decision="APPROVE",
            reason="Legitimate commentary reference",
            risk_score=max(ref.risk_score, 25),
        )

    @staticmethod
    def _find_ip_violations(ref: Reference) -> list[str]:
        """Find trademarked/copyrighted elements in the reference usage description."""
        violations: list[str] = []
        text_to_check = f"{ref.title} {ref.allowed_usage_mode}".lower()

        for pattern in KNOWN_TRADEMARK_PATTERNS:
            if pattern in text_to_check:
                violations.append(pattern)

        return violations

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
        from datetime import datetime, timezone

        defaults = {
            "reference_id": data.get("reference_id", "unknown"),
            "title": data.get("title", "Unknown"),
            "medium": data.get("medium", "other"),
            "reference_type": data.get("reference_type", "commentary"),
            "allowed_usage_mode": data.get("allowed_usage_mode", ""),
            "risk_score": data.get("risk_score", 50),
            "audience_overlap_score": data.get("audience_overlap_score", 0.0),
            "trending_relevance": data.get("trending_relevance", 0.0),
            "created_at": datetime.now(tz=timezone.utc),
            "updated_at": datetime.now(tz=timezone.utc),
        }
        if "license_id" in data:
            defaults["source_metadata"] = {"license_id": data["license_id"]}
        return Reference(**defaults)
