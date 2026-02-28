"""Rights verification check functions (deterministic).

Extracted from RightsEngine. Each function checks a reference against
one reference_type (licensed_direct, public_domain, style_only, commentary).
All decisions are purely rule-based — no LLM involved.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.schemas.reference import Reference
from app.schemas.rights import RightsDecision, RightsRecord
from app.services.rights_data import KNOWN_TRADEMARK_PATTERNS


def check_licensed(ref: Reference, record: RightsRecord | None) -> RightsDecision:
    """Check licensed_direct: requires active license with commercial+social scope."""
    base = {
        "reference_id": ref.reference_id,
        "reference_title": ref.title,
        "reference_type": ref.reference_type,
    }

    if not record:
        return RightsDecision(
            **base, decision="REJECT",
            reason="No license record found for direct use", risk_score=95,
        )
    if record.status != "active":
        return RightsDecision(
            **base, decision="REJECT",
            reason=f"License status is '{record.status}', not active", risk_score=90,
        )
    if record.license_expiry and record.license_expiry < datetime.now(tz=UTC):
        return RightsDecision(
            **base, decision="REJECT",
            reason="License has expired", risk_score=90,
        )
    if not record.license_scope.get("commercial"):
        return RightsDecision(
            **base, decision="REJECT",
            reason="License does not cover commercial use", risk_score=85,
        )
    if not record.license_scope.get("social"):
        return RightsDecision(
            **base, decision="REJECT",
            reason="License does not cover social media distribution", risk_score=80,
        )
    if not record.license_proof_url:
        return RightsDecision(
            **base, decision="REJECT",
            reason="No license proof document on file", risk_score=85,
        )
    return RightsDecision(
        **base, decision="APPROVE",
        reason="Valid active license with commercial + social scope", risk_score=10,
    )


def check_public_domain(ref: Reference, record: RightsRecord | None) -> RightsDecision:
    """Check public_domain: must be confirmed public domain."""
    base = {
        "reference_id": ref.reference_id,
        "reference_title": ref.title,
        "reference_type": ref.reference_type,
    }

    if record and record.reference_type == "public_domain" and record.status == "active":
        return RightsDecision(
            **base, decision="APPROVE",
            reason="Confirmed public domain in registry", risk_score=5,
        )
    if not record:
        return RightsDecision(
            **base, decision="REJECT",
            reason="Public domain status unconfirmed — no registry entry",
            risk_score=60,
        )
    return RightsDecision(
        **base, decision="REJECT",
        reason=f"Registry entry exists but type is '{record.reference_type}', not public_domain",
        risk_score=70,
    )


def check_style_only(ref: Reference, record: RightsRecord | None) -> RightsDecision:
    """Check style_only: must not include specific IP elements."""
    base = {
        "reference_id": ref.reference_id,
        "reference_title": ref.title,
        "reference_type": ref.reference_type,
    }

    violations = find_ip_violations(ref)
    if violations:
        return RightsDecision(
            **base, decision="REWRITE",
            reason=f"Style reference contains IP elements that must be removed: {violations}",
            risk_score=65,
            rewrite_instructions=(
                f"Remove these specific elements: {violations}. "
                "Replace with generic style/aesthetic descriptors."
            ),
        )
    if record and record.auto_block:
        return RightsDecision(
            **base, decision="REJECT",
            reason="Reference is auto-blocked in rights registry", risk_score=100,
        )
    return RightsDecision(
        **base, decision="APPROVE",
        reason="Style reference with no IP elements detected",
        risk_score=max(ref.risk_score, 15),
    )


def check_commentary(ref: Reference, record: RightsRecord | None) -> RightsDecision:
    """Check commentary: must be genuine commentary, not promotional impersonation."""
    base = {
        "reference_id": ref.reference_id,
        "reference_title": ref.title,
        "reference_type": ref.reference_type,
    }

    if record and record.auto_block:
        return RightsDecision(
            **base, decision="REJECT",
            reason="Reference is auto-blocked in rights registry", risk_score=100,
        )
    if record and record.blocked_elements:
        usage_lower = ref.allowed_usage_mode.lower()
        found_blocked = [
            elem for elem in record.blocked_elements if elem.lower() in usage_lower
        ]
        if found_blocked:
            return RightsDecision(
                **base, decision="REWRITE",
                reason=f"Commentary references blocked elements: {found_blocked}",
                risk_score=55,
                rewrite_instructions=f"Remove references to: {found_blocked}",
            )
    return RightsDecision(
        **base, decision="APPROVE",
        reason="Legitimate commentary reference",
        risk_score=max(ref.risk_score, 25),
    )


def find_ip_violations(ref: Reference) -> list[str]:
    """Find trademarked/copyrighted elements in the reference usage description."""
    violations: list[str] = []
    text_to_check = f"{ref.title} {ref.allowed_usage_mode}".lower()
    for pattern in KNOWN_TRADEMARK_PATTERNS:
        if pattern in text_to_check:
            violations.append(pattern)
    return violations
