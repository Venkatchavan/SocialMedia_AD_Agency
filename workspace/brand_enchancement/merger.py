"""brand_enchancement.merger — Merge new signals into existing BrandBibleDoc.

Strategy:
  1. Accumulate keywords + hashtags (dedup, preserve history).
  2. Ask the LLM to review only sections relevant to the new signals.
  3. Apply LLM suggestions field-by-field (never blind-overwrite non-empty values).
  4. Record a ChangeRecord in the doc's change_log.

LLM is fully optional: if unavailable, signals are accumulated and log updated.
"""

from __future__ import annotations

import copy
import json

from brand_enchancement.schemas import (
    BrandBibleDoc,
    ChangeRecord,
    UpdateSignal,
)
from core.logging import get_logger
from core.utils_time import utcnow_iso

_log = get_logger(__name__)


# ── Public entry ─────────────────────────────────────────────────────────────

def merge_signals(
    doc: BrandBibleDoc,
    signal: UpdateSignal,
) -> BrandBibleDoc:
    """Return a *new* BrandBibleDoc with *signal* merged in.

    The original *doc* is never mutated.
    """
    updated = copy.deepcopy(doc)
    fields_changed: list[str] = []

    # 1 — Accumulate raw signals
    new_kw = _add_unique(updated.keywords, signal.keywords)
    new_ht = _add_unique(updated.hashtags, signal.hashtags)
    if new_kw:
        updated.keywords = sorted(set(updated.keywords) | set(new_kw))
        fields_changed.append("keywords")
    if new_ht:
        updated.hashtags = sorted(set(updated.hashtags) | set(new_ht))
        fields_changed.append("hashtags")
    if signal.extra_context:
        updated.extra_context_log.append(signal.extra_context)
        fields_changed.append("extra_context_log")

    # 2 — LLM-assisted section enrichment
    if signal.keywords or signal.hashtags or signal.extra_context:
        llm_patch = _call_llm(updated, signal)
        if llm_patch:
            applied = _apply_patch(updated, llm_patch)
            fields_changed.extend(applied)

    # 3 — Record change
    record = ChangeRecord(
        run_id=signal.run_id,
        timestamp=utcnow_iso(),
        fields_updated=sorted(set(fields_changed)),
        keywords_added=new_kw,
        hashtags_added=new_ht,
        summary=_build_summary(signal, fields_changed),
    )
    updated.change_log.append(record)
    updated.run_id = signal.run_id
    updated.updated_at = record.timestamp
    updated.version = doc.version + 1

    _log.info(
        "brand_enchancement: merged run=%s version=%d fields=%s",
        signal.run_id, updated.version, fields_changed,
    )
    return updated


# ── LLM enrichment ───────────────────────────────────────────────────────────

def _call_llm(doc: BrandBibleDoc, signal: UpdateSignal) -> dict:
    """Ask the LLM to suggest brand-bible updates given new signals.

    Returns a dict of field → new value, or {} on failure.
    """
    try:
        from analyzers.llm_router import LLMRouter
    except ImportError:
        return {}

    context_snippet = signal.extra_context[:400] if signal.extra_context else ""
    current_snapshot = json.dumps({
        "brand_summary": doc.brand_summary.model_dump(),
        "voice_tone": doc.voice_tone.model_dump(),
        "audience": doc.audience.model_dump(),
    }, indent=2)[:600]

    prompt = (
        "You are a brand strategist enriching a brand bible with new market signals.\n\n"
        f"CURRENT BRAND SNAPSHOT:\n{current_snapshot}\n\n"
        f"NEW KEYWORDS: {', '.join(signal.keywords[:20])}\n"
        f"NEW HASHTAGS: {', '.join(signal.hashtags[:20])}\n"
        f"EXTRA CONTEXT: {context_snippet}\n\n"
        "Return ONLY a JSON object (no markdown) with any of these keys that need updating:\n"
        "  what_we_sell, what_we_stand_for, what_we_never_do,\n"
        "  audience_primary, audience_pain_points,\n"
        "  voice_adjectives, voice_use, voice_avoid,\n"
        "  positioning_difference\n"
        "For list fields, return a JSON array of strings. "
        "Leave out any key you are not changing. "
        "Only update when new signals clearly add insight."
    )

    try:
        raw = LLMRouter().generate(prompt, max_tokens=500)
        if not raw:
            return {}
        # Strip accidental markdown fences
        raw = raw.strip().strip("```json").strip("```").strip()
        patch = json.loads(raw)
        _log.info("brand_enchancement: LLM patch keys=%s", list(patch.keys()))
        return patch
    except Exception as exc:
        _log.warning("brand_enchancement: LLM enrichment skipped (%s)", exc)
        return {}


# ── Patch applicator ─────────────────────────────────────────────────────────

def _apply_patch(doc: BrandBibleDoc, patch: dict) -> list[str]:
    """Apply a flat patch dict to doc sections. Returns list of field names changed."""
    applied: list[str] = []

    _str_field(doc.brand_summary, "what_we_sell", patch, applied)
    _str_field(doc.brand_summary, "what_we_stand_for", patch, applied)
    _str_field(doc.brand_summary, "what_we_never_do", patch, applied)
    _str_field(doc.audience, "primary", patch, applied, key="audience_primary")
    _list_field(doc.audience, "pain_points", patch, applied, key="audience_pain_points")
    _list_field(doc.voice_tone, "adjectives", patch, applied, key="voice_adjectives")
    _list_field(doc.voice_tone, "use", patch, applied, key="voice_use")
    _list_field(doc.voice_tone, "avoid", patch, applied, key="voice_avoid")
    _str_field(doc.competitors, "positioning_difference", patch, applied)

    return applied


def _str_field(obj, attr: str, patch: dict, log: list, key: str | None = None) -> None:
    k = key or attr
    val = patch.get(k)
    if val and isinstance(val, str) and val.strip():
        setattr(obj, attr, val.strip())
        log.append(k)


def _list_field(obj, attr: str, patch: dict, log: list, key: str | None = None) -> None:
    k = key or attr
    val = patch.get(k)
    if val and isinstance(val, list):
        existing: list = getattr(obj, attr, [])
        merged = list(dict.fromkeys(existing + [str(v) for v in val if v]))
        setattr(obj, attr, merged[:12])
        log.append(k)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _add_unique(existing: list[str], incoming: list[str]) -> list[str]:
    ex_set = {s.lower() for s in existing}
    return [s for s in incoming if s.lower() not in ex_set]


def _build_summary(signal: UpdateSignal, fields: list[str]) -> str:
    parts = []
    if signal.keywords:
        parts.append(f"keywords: {', '.join(signal.keywords[:5])}")
    if signal.hashtags:
        parts.append(f"hashtags: {', '.join(signal.hashtags[:5])}")
    if signal.extra_context:
        parts.append(f"context: {signal.extra_context[:80]}")
    base = "; ".join(parts) or "signals merged"
    return f"{base} → updated {len(fields)} field(s)"
