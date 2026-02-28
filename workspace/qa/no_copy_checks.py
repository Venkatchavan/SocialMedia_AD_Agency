"""qa.no_copy_checks — Detect verbatim competitor copy overlap."""

from __future__ import annotations

from core.enums import RiskLevel
from core.logging import get_logger

_log = get_logger(__name__)

_MIN_OVERLAP_LEN = 40  # chars — below this we consider it coincidental


def check_copy_overlap(
    generated_texts: list[str],
    competitor_texts: list[str],
) -> tuple[RiskLevel, list[str]]:
    """Check for long overlaps between generated copy and competitor captions.

    Returns (risk_level, list of flagged overlaps).
    """
    flags: list[str] = []
    for gen in generated_texts:
        for comp in competitor_texts:
            overlap = _longest_common_substring(gen.lower(), comp.lower())
            if len(overlap) >= _MIN_OVERLAP_LEN:
                flags.append(
                    f"Overlap ({len(overlap)} chars): '{overlap[:60]}...'"
                )
    if not flags:
        return RiskLevel.LOW, []
    if len(flags) <= 2:
        return RiskLevel.MED, flags
    return RiskLevel.HIGH, flags


def _longest_common_substring(a: str, b: str) -> str:
    """Simple O(n*m) LCS for moderate-length strings."""
    if not a or not b:
        return ""
    # Use suffix-based approach for strings up to ~2000 chars
    max_len = 0
    end_idx = 0
    prev = [0] * (len(b) + 1)
    for i in range(1, len(a) + 1):
        curr = [0] * (len(b) + 1)
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                curr[j] = prev[j - 1] + 1
                if curr[j] > max_len:
                    max_len = curr[j]
                    end_idx = i
        prev = curr
    return a[end_idx - max_len : end_idx]
