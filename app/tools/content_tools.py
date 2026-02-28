"""Content Tools — CrewAI tool wrappers for content generation services."""

from __future__ import annotations

from typing import Any


class ContentHashTool:
    """CrewAI-compatible tool for content hashing and dedup."""

    name: str = "content_hash"
    description: str = (
        "Generate a SHA-256 hash for content text. Used for deduplication "
        "and tamper detection. Returns hash and verification status."
    )

    def __init__(self, content_hasher: Any) -> None:
        self._hasher = content_hasher

    def run(self, text: str) -> dict:
        """Execute the tool — hash content text."""
        content_hash = self._hasher.hash_text(text)
        return {
            "content_hash": content_hash,
            "text_length": len(text),
        }


class QACheckTool:
    """CrewAI-compatible tool for QA checking."""

    name: str = "qa_check"
    description: str = (
        "Run quality assurance checks on content before publishing. "
        "Checks compliance status, disclosures, duplicates, and content quality. "
        "Returns APPROVE, REWRITE, or REJECT."
    )

    def __init__(self, qa_checker: Any) -> None:
        self._checker = qa_checker

    def run(
        self,
        content_hash: str,
        compliance_status: str,
        captions: dict[str, str],
        target_platforms: list[str],
    ) -> dict:
        """Execute the tool — run QA checks."""
        result = self._checker.check(
            content_hash=content_hash,
            compliance_status=compliance_status,
            captions=captions,
            target_platforms=target_platforms,
        )
        return {
            "decision": result.decision,
            "checks": [c.model_dump() for c in result.checks] if hasattr(result, "checks") else [],
            "reason": result.reason if hasattr(result, "reason") else "",
        }


class DisclosureValidationTool:
    """CrewAI-compatible tool for validating affiliate disclosures."""

    name: str = "disclosure_validation"
    description: str = (
        "Validate that a caption contains proper affiliate disclosure "
        "for a specific platform. Can auto-add disclosure if missing."
    )

    def __init__(self) -> None:
        pass

    def run(self, caption: str, platform: str, auto_fix: bool = True) -> dict:
        """Execute the tool — validate disclosure."""
        from app.policies.disclosure_rules import validate_disclosure, add_disclosure

        is_valid, reason = validate_disclosure(caption, platform)

        result: dict = {
            "is_valid": is_valid,
            "reason": reason,
            "platform": platform,
        }

        if not is_valid and auto_fix:
            fixed_caption = add_disclosure(caption, platform)
            result["fixed_caption"] = fixed_caption
            result["auto_fixed"] = True

        return result
