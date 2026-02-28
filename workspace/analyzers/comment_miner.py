"""analyzers.comment_miner — Extract anonymized themes from comments.

Raw comments are NEVER persisted — only anonymized themes are stored.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field

from core.logging import get_logger

_log = get_logger(__name__)


class CommentThemes(BaseModel):
    """Anonymized comment analysis output for one asset."""
    asset_id: str
    top_questions: list[str] = Field(default_factory=list)
    repeated_objections: list[str] = Field(default_factory=list)
    desire_language: list[str] = Field(default_factory=list)
    confusion_points: list[str] = Field(default_factory=list)
    suggested_angles_to_test: list[str] = Field(default_factory=list)
    pii_detected: bool = False


def mine_comments(asset_id: str, comments: list[str]) -> CommentThemes:
    """Process raw comments into anonymized themes, then discard originals."""
    cleaned = [_strip_pii(c) for c in comments]
    pii_found = any(_has_pii(c) for c in comments)

    themes = CommentThemes(
        asset_id=asset_id,
        top_questions=_extract_questions(cleaned),
        repeated_objections=_extract_objections(cleaned),
        desire_language=_extract_desires(cleaned),
        confusion_points=_extract_confusion(cleaned),
        suggested_angles_to_test=_suggest_angles(cleaned),
        pii_detected=pii_found,
    )
    # Raw comments are NOT stored anywhere
    _log.info("Mined %d comments for %s (pii=%s)", len(comments), asset_id, pii_found)
    return themes


def mine_batch(items: list[dict[str, Any]]) -> list[CommentThemes]:
    """Process batch: each item has 'asset_id' and 'comments' keys."""
    return [mine_comments(it["asset_id"], it.get("comments", [])) for it in items]


# ── Internal helpers ────────────────────────────────

_PII_PATTERN = re.compile(
    r"(@\w+|https?://\S+|\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.\w+\b|\b\d{3}[-.]?\d{3}[-.]?\d{4}\b)"
)


def _has_pii(text: str) -> bool:
    return bool(_PII_PATTERN.search(text))


def _strip_pii(text: str) -> str:
    return _PII_PATTERN.sub("[REDACTED]", text)


def _extract_questions(comments: list[str]) -> list[str]:
    qs = [c.strip() for c in comments if "?" in c]
    return _dedupe_themes(qs)[:5]


def _extract_objections(comments: list[str]) -> list[str]:
    kw = re.compile(r"(doesn't work|scam|fake|waste|too expensive|not worth)", re.I)
    hits = [c for c in comments if kw.search(c)]
    return _dedupe_themes(hits)[:5]


def _extract_desires(comments: list[str]) -> list[str]:
    kw = re.compile(r"(i wish|i need|i want|would love|please make)", re.I)
    hits = [c for c in comments if kw.search(c)]
    return _dedupe_themes(hits)[:5]


def _extract_confusion(comments: list[str]) -> list[str]:
    kw = re.compile(r"(confused|don't understand|what does|how do|unclear)", re.I)
    hits = [c for c in comments if kw.search(c)]
    return _dedupe_themes(hits)[:5]


def _suggest_angles(comments: list[str]) -> list[str]:
    # Simple: top desires rephrased as ad angles
    desires = _extract_desires(comments)
    return [f"Address: {d}" for d in desires[:3]]


def _dedupe_themes(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for it in items:
        key = it.strip().lower()[:60]
        if key not in seen:
            seen.add(key)
            out.append(it.strip())
    return out
