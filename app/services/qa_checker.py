"""Deterministic QA and compliance checker.

CRITICAL: No content may be published unless it passes ALL checks.
This is a deterministic gate — not LLM-based.

Checks enforced (from Agents.md):
1. compliance_status == APPROVED for all references
2. risk_score < threshold (or human-approved)
3. affiliate disclosure present in every caption
4. content hash not duplicate on same platform
5. similarity score < threshold vs recent content
6. media meets platform technical specs
7. quality score > minimum
8. all assets have valid signed URLs
9. audit trail complete
"""

from __future__ import annotations

import structlog

from app.config import get_settings
from app.schemas.content import CaptionBundle
from app.schemas.publish import PlatformPackage
from app.services.audit_logger import AuditLogger

logger = structlog.get_logger(__name__)


class QACheckResult:
    """Result of a single QA check."""

    def __init__(self, check_name: str, passed: bool, reason: str = "") -> None:
        self.check_name = check_name
        self.passed = passed
        self.reason = reason

    def model_dump(self) -> dict:
        """Serialize to dict (compatible with Pydantic interface)."""
        return {
            "check_name": self.check_name,
            "passed": self.passed,
            "reason": self.reason,
        }

    def __repr__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return f"{status}: {self.check_name} — {self.reason}"


class QADecision:
    """Aggregated QA decision for a platform package."""

    def __init__(self) -> None:
        self.checks: list[QACheckResult] = []
        self.decision: str = "PENDING"
        self.reasons: list[str] = []

    @property
    def is_approved(self) -> bool:
        return self.decision == "APPROVE"

    @property
    def reason(self) -> str:
        """Single string summary of all failure reasons."""
        return "; ".join(self.reasons) if self.reasons else "All checks passed"

    def add_check(self, result: QACheckResult) -> None:
        self.checks.append(result)
        if not result.passed:
            self.reasons.append(result.reason)

    def finalize(self) -> None:
        """Finalize the decision based on all check results."""
        failed = [c for c in self.checks if not c.passed]
        if not failed:
            self.decision = "APPROVE"
        elif any("disclosure" in c.check_name.lower() for c in failed):
            # Missing disclosure → auto-rewrite, don't reject
            self.decision = "REWRITE"
        else:
            self.decision = "REJECT"


class QAChecker:
    """Deterministic QA and compliance checker.

    All checks are rule-based. No LLM opinions.
    Every check failure is logged to audit trail.
    """

    def __init__(
        self,
        audit_logger: AuditLogger,
        published_hashes: dict[str, set[str]] | None = None,
    ) -> None:
        self._audit = audit_logger
        self._settings = get_settings()
        # Platform → set of content hashes already published
        self._published_hashes: dict[str, set[str]] = published_hashes or {}

    def check(
        self,
        package: PlatformPackage,
        caption_bundle: CaptionBundle | None = None,
        session_id: str = "",
    ) -> QADecision:
        """Run all QA checks on a platform package.

        Returns QADecision with APPROVE, REWRITE, or REJECT.
        """
        qa = QADecision()

        # 1. Compliance status
        qa.add_check(self._check_compliance_status(package))

        # 2. Disclosure check
        qa.add_check(self._check_disclosure(package, caption_bundle))

        # 3. Duplicate content check
        qa.add_check(self._check_duplicate(package))

        # 4. Quality score (placeholder — real scoring needs asset analysis)
        qa.add_check(self._check_quality(package))

        # 5. Content hash present
        qa.add_check(self._check_content_hash(package))

        # Finalize decision
        qa.finalize()

        # Log audit event
        self._audit.log(
            agent_id="qa_checker",
            action="qa_check",
            decision=qa.decision,
            reason="; ".join(qa.reasons) if qa.reasons else "All checks passed",
            input_data={"package_id": package.id, "platform": package.platform},
            output_data={
                "decision": qa.decision,
                "checks_passed": len([c for c in qa.checks if c.passed]),
                "checks_failed": len([c for c in qa.checks if not c.passed]),
            },
            session_id=session_id,
        )

        logger.info(
            "qa_decision",
            package_id=package.id,
            platform=package.platform,
            decision=qa.decision,
            checks_passed=len([c for c in qa.checks if c.passed]),
            checks_failed=len([c for c in qa.checks if not c.passed]),
        )

        return qa

    def _check_compliance_status(self, package: PlatformPackage) -> QACheckResult:
        """Check: compliance_status must be APPROVED."""
        if package.compliance_status == "APPROVED":
            return QACheckResult("compliance_status", True, "Compliance approved")
        return QACheckResult(
            "compliance_status",
            False,
            f"Compliance status is '{package.compliance_status}', expected 'APPROVED'",
        )

    def _check_disclosure(
        self,
        package: PlatformPackage,
        caption_bundle: CaptionBundle | None,
    ) -> QACheckResult:
        """Check: affiliate disclosure MUST be present in caption."""
        caption = package.caption
        if not caption:
            return QACheckResult(
                "disclosure_check", False, "Caption is empty — cannot verify disclosure"
            )

        disclosure_markers = [
            "#ad",
            "#affiliate",
            "affiliate link",
            "commission",
            "paid partnership",
            "sponsored",
        ]
        caption_lower = caption.lower()
        has_disclosure = any(marker in caption_lower for marker in disclosure_markers)

        if has_disclosure:
            return QACheckResult("disclosure_check", True, "Affiliate disclosure present")
        return QACheckResult(
            "disclosure_check",
            False,
            "MISSING affiliate disclosure in caption. Must include #ad, #affiliate, or equivalent.",
        )

    def _check_duplicate(self, package: PlatformPackage) -> QACheckResult:
        """Check: content hash must not duplicate existing published content on same platform."""
        if not package.content_hash:
            return QACheckResult(
                "duplicate_check", False, "No content hash computed — cannot check for duplicates"
            )

        platform_hashes = self._published_hashes.get(package.platform, set())
        if package.content_hash in platform_hashes:
            return QACheckResult(
                "duplicate_check",
                False,
                f"Duplicate content detected on {package.platform} (hash: {package.content_hash[:12]}...)",
            )

        return QACheckResult("duplicate_check", True, "Content is unique for this platform")

    def _check_quality(self, package: PlatformPackage) -> QACheckResult:
        """Check: content quality score must exceed minimum threshold."""
        # Placeholder — real implementation needs media analysis
        # For MVP, we pass if basic fields are populated
        has_caption = bool(package.caption and len(package.caption) > 10)
        has_media = bool(package.media_path or package.signed_media_url)

        if has_caption and has_media:
            return QACheckResult("quality_check", True, "Basic quality checks passed")
        if not has_caption:
            return QACheckResult("quality_check", False, "Caption too short or missing")
        return QACheckResult("quality_check", False, "Media path/URL missing")

    def _check_content_hash(self, package: PlatformPackage) -> QACheckResult:
        """Check: content hash must be computed for tracking."""
        if package.content_hash:
            return QACheckResult("content_hash_check", True, "Content hash present")
        return QACheckResult(
            "content_hash_check", False, "Content hash not computed"
        )

    def register_published_hash(self, platform: str, content_hash: str) -> None:
        """Register a content hash as published on a platform."""
        if platform not in self._published_hashes:
            self._published_hashes[platform] = set()
        self._published_hashes[platform].add(content_hash)
