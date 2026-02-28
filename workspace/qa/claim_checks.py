"""qa.claim_checks — Flag medical / financial claims requiring substantiation."""

from __future__ import annotations

import re

from core.enums import RiskLevel
from core.logging import get_logger

_log = get_logger(__name__)

_MEDICAL_PATTERNS = [
    re.compile(r"\b(cure|treat|heal|diagnos|prevent|remedy)\b", re.I),
    re.compile(r"\b(clinically\s+proven|FDA\s+approved)\b", re.I),
    re.compile(r"\b(weight\s+loss|lose\s+\d+\s*(lbs?|kg|pounds?))\b", re.I),
]

_FINANCIAL_PATTERNS = [
    re.compile(r"\b(guaranteed\s+income|guaranteed\s+return)\b", re.I),
    re.compile(r"\b(get\s+rich|make\s+money\s+fast)\b", re.I),
    re.compile(r"\b(invest\s+now|double\s+your\s+money)\b", re.I),
]


def check_claims(text: str) -> tuple[RiskLevel, list[str]]:
    """Scan text for medical/financial claims.

    Returns (risk_level, list of flagged phrases).
    """
    flags: list[str] = []
    for pat in _MEDICAL_PATTERNS:
        m = pat.search(text)
        if m:
            flags.append(f"Medical claim: '{m.group()}'")
    for pat in _FINANCIAL_PATTERNS:
        m = pat.search(text)
        if m:
            flags.append(f"Financial claim: '{m.group()}'")

    if not flags:
        return RiskLevel.LOW, []
    if len(flags) <= 1:
        return RiskLevel.MED, flags
    return RiskLevel.HIGH, flags
