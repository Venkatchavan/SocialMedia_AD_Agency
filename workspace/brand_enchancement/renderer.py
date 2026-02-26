"""brand_enchancement.renderer — Render BrandBibleDoc to human-readable markdown.

Produces a rich, industry-agnostic markdown document at:
  clients/<workspace>/Brand_Book.md

The rendered markdown is always re-generated from the structured JSON;
never edited by hand (hand edits get overwritten on next run).
"""

from __future__ import annotations

from pathlib import Path

from brand_enchancement.schemas import BrandBibleDoc
from core.logging import get_logger

_log = get_logger(__name__)

_CLIENTS_ROOT = Path(__file__).resolve().parent.parent / "clients"


# ── Public API ───────────────────────────────────────────────────────────────

def render_markdown(doc: BrandBibleDoc) -> str:
    """Return the full markdown string for *doc*."""
    parts: list[str] = []
    _h1(parts, f"Brand Bible — {doc.workspace_id}")
    _meta_block(parts, doc)
    _brand_summary_section(parts, doc)
    _audience_section(parts, doc)
    _voice_tone_section(parts, doc)
    _proof_claims_section(parts, doc)
    _visual_style_section(parts, doc)
    _offers_section(parts, doc)
    _competitors_section(parts, doc)
    _keywords_section(parts, doc)
    _changelog_section(parts, doc)
    return "\n".join(parts) + "\n"


def write_brand_markdown(doc: BrandBibleDoc, workspace_id: str) -> Path:
    """Write the rendered markdown to ``clients/<workspace>/Brand_Book.md``."""
    client_dir = _CLIENTS_ROOT / workspace_id
    client_dir.mkdir(parents=True, exist_ok=True)
    out_path = client_dir / "Brand_Book.md"
    out_path.write_text(render_markdown(doc), encoding="utf-8")
    _log.info("brand_enchancement: wrote markdown → %s", out_path)
    return out_path


# ── Section renderers ────────────────────────────────────────────────────────

def _meta_block(parts: list[str], doc: BrandBibleDoc) -> None:
    parts.append(
        f"> **Version {doc.version}** | Run: `{doc.run_id}` | Updated: {doc.updated_at}\n"
    )


def _brand_summary_section(parts: list[str], doc: BrandBibleDoc) -> None:
    _h2(parts, "Brand Summary")
    bs = doc.brand_summary
    _kv(parts, "Industry", bs.industry)
    _kv(parts, "What we sell", bs.what_we_sell)
    _kv(parts, "What we stand for", bs.what_we_stand_for)
    _kv(parts, "What we never do", bs.what_we_never_do)
    _extra(parts, bs.extra)
    parts.append("")


def _audience_section(parts: list[str], doc: BrandBibleDoc) -> None:
    _h2(parts, "Audience")
    a = doc.audience
    _kv(parts, "Primary", a.primary)
    _kv(parts, "Secondary", a.secondary)
    _kv(parts, "Awareness level", a.awareness_level)
    _bullets(parts, "Pain points", a.pain_points)
    _extra(parts, a.extra)
    parts.append("")


def _voice_tone_section(parts: list[str], doc: BrandBibleDoc) -> None:
    _h2(parts, "Voice & Tone")
    vt = doc.voice_tone
    _bullets(parts, "Tone adjectives", vt.adjectives)
    _bullets(parts, "Use", vt.use)
    _bullets(parts, "Avoid", vt.avoid)
    _bullets(parts, "Examples", vt.examples)
    _extra(parts, vt.extra)
    parts.append("")


def _proof_claims_section(parts: list[str], doc: BrandBibleDoc) -> None:
    _h2(parts, "Proof & Claims")
    pc = doc.proof_claims
    _bullets(parts, "Allowed claims", pc.allowed)
    _bullets(parts, "Forbidden claims", pc.forbidden)
    _kv(parts, "Substantiation required", str(pc.substantiation_required))
    _extra(parts, pc.extra)
    parts.append("")


def _visual_style_section(parts: list[str], doc: BrandBibleDoc) -> None:
    _h2(parts, "Visual Style")
    vs = doc.visual_style
    _bullets(parts, "Do", vs.do)
    _bullets(parts, "Don't", vs.dont)
    _bullets(parts, "References", vs.references)
    _extra(parts, vs.extra)
    parts.append("")


def _offers_section(parts: list[str], doc: BrandBibleDoc) -> None:
    _h2(parts, "Offers")
    o = doc.offers
    _bullets(parts, "Typical offers", o.typical)
    _bullets(parts, "Constraints", o.constraints)
    _extra(parts, o.extra)
    parts.append("")


def _competitors_section(parts: list[str], doc: BrandBibleDoc) -> None:
    _h2(parts, "Competitors")
    c = doc.competitors
    _bullets(parts, "Main competitors", c.main)
    _kv(parts, "Positioning difference", c.positioning_difference)
    _extra(parts, c.extra)
    parts.append("")


def _keywords_section(parts: list[str], doc: BrandBibleDoc) -> None:
    _h2(parts, "Accumulated Signals")
    _bullets(parts, "Keywords", doc.keywords)
    _bullets(parts, "Hashtags", doc.hashtags)
    if doc.extra_context_log:
        parts.append("\n**Context log:**")
        for i, ctx in enumerate(doc.extra_context_log[-10:], 1):
            parts.append(f"{i}. {ctx}")
    parts.append("")


def _changelog_section(parts: list[str], doc: BrandBibleDoc) -> None:
    _h2(parts, "Change Log")
    if not doc.change_log:
        parts.append("_No changes recorded yet._")
        return
    parts.append("| Version | Run ID | Updated | Fields | Summary |")
    parts.append("|---------|--------|---------|--------|---------|")
    for entry in reversed(doc.change_log[-20:]):
        fields = ", ".join(entry.fields_updated) or "—"
        rid = entry.run_id[:16]
        ts = entry.timestamp[:16]
        summary = entry.summary[:60]
        parts.append(f"| +{doc.version - doc.change_log.index(entry)} "
                     f"| {rid} | {ts} | {fields} | {summary} |")
    parts.append("")


# ── Formatting helpers ───────────────────────────────────────────────────────

def _h1(parts: list[str], text: str) -> None:
    parts.append(f"# {text}\n")


def _h2(parts: list[str], text: str) -> None:
    parts.append(f"## {text}")


def _kv(parts: list[str], key: str, val: str) -> None:
    if val:
        parts.append(f"- **{key}:** {val}")


def _bullets(parts: list[str], label: str, items: list) -> None:
    if items:
        parts.append(f"\n**{label}:**")
        for item in items:
            parts.append(f"- {item}")


def _extra(parts: list[str], extra: dict) -> None:
    for k, v in extra.items():
        if v:
            parts.append(f"- **{k}:** {v}")
