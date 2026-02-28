"""qa.pii_redaction — Detect and redact PII from text outputs."""

from __future__ import annotations

import re

from core.logging import get_logger

_log = get_logger(__name__)

# PII patterns
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
_PHONE_RE = re.compile(r"\b(\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b")
_HANDLE_RE = re.compile(r"@[A-Za-z0-9_]{2,30}")
_URL_PERSONAL = re.compile(r"https?://(?:www\.)?(?:facebook|instagram|twitter|x)\.com/[A-Za-z0-9_.]+")
_NAME_INDICATORS = re.compile(
    r"\b(my name is|i'm|i am|contact me|call me)\s+[A-Z][a-z]+\b", re.I
)


def has_pii(text: str) -> bool:
    """Return True if PII is detected in text."""
    return bool(
        _EMAIL_RE.search(text)
        or _PHONE_RE.search(text)
        or _HANDLE_RE.search(text)
        or _URL_PERSONAL.search(text)
        or _NAME_INDICATORS.search(text)
    )


def redact(text: str) -> str:
    """Replace detected PII with [REDACTED]."""
    out = _EMAIL_RE.sub("[REDACTED-EMAIL]", text)
    out = _PHONE_RE.sub("[REDACTED-PHONE]", out)
    out = _HANDLE_RE.sub("[REDACTED-HANDLE]", out)
    out = _URL_PERSONAL.sub("[REDACTED-URL]", out)
    out = _NAME_INDICATORS.sub("[REDACTED-NAME]", out)
    return out


def scan_texts(texts: list[str]) -> tuple[bool, list[int]]:
    """Scan multiple texts; return (any_pii_found, list of indices with PII)."""
    found_indices: list[int] = []
    for i, t in enumerate(texts):
        if has_pii(t):
            found_indices.append(i)
    return bool(found_indices), found_indices
