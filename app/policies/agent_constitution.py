"""Agent Constitution — Enforced rules for every agent in the system.

Derived from Agents.md (Agentic Rules) and Agents_Security.md.
These rules are NON-NEGOTIABLE and must be checked before any agent action.
"""

from __future__ import annotations

import re
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)


class ConstitutionViolation(Exception):
    """Raised when an agent action violates the constitution."""

    def __init__(self, rule: str, detail: str) -> None:
        self.rule = rule
        self.detail = detail
        super().__init__(f"CONSTITUTION VIOLATION [{rule}]: {detail}")


class AgentConstitution:
    """Enforce the Agent Constitution on all agent actions.

    Every agent must check against these rules before executing actions.
    Violations are logged and blocked.
    """

    # Patterns that indicate prompt injection attempts
    INJECTION_PATTERNS: list[str] = [
        r"ignore\s+(previous|above|all)\s+instructions",
        r"system\s*prompt",
        r"you\s+are\s+now",
        r"disregard\s+(your|all|previous)",
        r"<script>",
        r"javascript:",
        r"\{\{.*\}\}",
    ]

    # Words that should never appear in published captions without context
    FORBIDDEN_CLAIM_PATTERNS: list[str] = [
        r"guaranteed\s+results",
        r"100%\s+effective",
        r"miracle\s+(cure|solution)",
        r"get\s+rich\s+quick",
        r"limited\s+time\s+only",  # unless verified from product data
    ]

    @classmethod
    def validate_input(cls, text: str) -> str:
        """Validate and sanitize external text input.

        Checks for prompt injection and returns sanitized text.
        Raises ConstitutionViolation if malicious input detected.
        """
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.error("prompt_injection_detected", pattern=pattern)
                raise ConstitutionViolation(
                    "INPUT_VALIDATION",
                    f"Potentially malicious input detected (pattern: {pattern})",
                )
        return text.strip()

    @classmethod
    def validate_caption(cls, caption: str, platform: str = "") -> list[str]:
        """Validate a caption against the constitution.

        Args:
            caption: The caption text to validate.
            platform: Optional platform name for platform-specific rules.

        Returns list of violations (empty if valid).
        """
        violations: list[str] = []

        # Check for mandatory disclosure
        disclosure_markers = [
            "#ad", "#affiliate", "affiliate link",
            "commission", "paid partnership", "sponsored",
        ]
        caption_lower = caption.lower()
        has_disclosure = any(marker in caption_lower for marker in disclosure_markers)
        if not has_disclosure:
            violations.append("MISSING_DISCLOSURE: Caption must include affiliate disclosure")

        # Check for forbidden claims
        for pattern in cls.FORBIDDEN_CLAIM_PATTERNS:
            if re.search(pattern, caption, re.IGNORECASE):
                violations.append(
                    f"FORBIDDEN_CLAIM: Pattern '{pattern}' detected — "
                    "no unverifiable claims allowed"
                )

        return violations

    @classmethod
    def validate_publish_precondition(
        cls,
        compliance_status: str,
        qa_status: str,
        has_disclosure: bool,
        content_hash: str,
    ) -> list[str]:
        """Validate all preconditions before publishing.

        Returns list of violations (empty if all preconditions met).
        """
        violations: list[str] = []

        if compliance_status != "APPROVED":
            violations.append(
                f"COMPLIANCE_GATE: compliance_status is '{compliance_status}', "
                "must be 'APPROVED'"
            )

        if qa_status != "APPROVE":
            violations.append(
                f"QA_GATE: qa_status is '{qa_status}', must be 'APPROVE'"
            )

        if not has_disclosure:
            violations.append("DISCLOSURE_GATE: Affiliate disclosure missing from caption")

        if not content_hash:
            violations.append("HASH_GATE: Content hash not computed")

        if violations:
            logger.error(
                "publish_precondition_failed",
                violations=violations,
            )

        return violations

    @classmethod
    def validate_no_secret_exposure(cls, text: str) -> bool:
        """Check that text does not contain exposed secrets.

        Returns True if safe, False if potential secret exposure detected.
        """
        secret_patterns = [
            r"sk-[a-zA-Z0-9]{20,}",      # OpenAI-style keys
            r"AKIA[A-Z0-9]{16}",          # AWS access keys
            r"ghp_[a-zA-Z0-9]{36}",       # GitHub tokens
            r"Bearer\s+[a-zA-Z0-9\-._~+/]+=*",  # Bearer tokens
        ]
        for pattern in secret_patterns:
            if re.search(pattern, text):
                logger.critical("secret_exposure_detected", pattern=pattern)
                return False
        return True
