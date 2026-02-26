"""brand_enchancement.loader — Load or bootstrap a BrandBibleDoc.

Load order:
  1. ``clients/<workspace>/BrandBible.json``  (structured, from previous run)
  2. ``clients/<workspace>/BrandBible.md``    (legacy / hand-written markdown)
  3. Fresh empty BrandBibleDoc               (first-run bootstrap)

No side-effects: loader is read-only; writing is handled by versioning + renderer.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from brand_enchancement.schemas import (
    AudienceSection,
    BrandBibleDoc,
    BrandSummary,
    CompetitorsSection,
    OffersSection,
    ProofClaimsSection,
    VisualStyleSection,
    VoiceToneSection,
)
from core.logging import get_logger

_log = get_logger(__name__)

_CLIENTS_ROOT = Path(__file__).resolve().parent.parent / "clients"


def _clients_dir(workspace_id: str) -> Path:
    return _CLIENTS_ROOT / workspace_id


def load_brand_bible(workspace_id: str) -> BrandBibleDoc:
    """Return the current BrandBibleDoc for *workspace_id*.

    Tries JSON first, then MD, then returns a fresh empty doc.
    """
    client_dir = _clients_dir(workspace_id)
    json_path = client_dir / "BrandBible.json"
    md_path = client_dir / "BrandBible.md"

    if json_path.exists():
        _log.info("brand_enchancement: loading bible from %s", json_path)
        return _load_json(json_path, workspace_id)

    if md_path.exists():
        _log.info("brand_enchancement: bootstrapping bible from %s", md_path)
        return _parse_markdown(md_path, workspace_id)

    _log.info("brand_enchancement: starting fresh bible for workspace=%s", workspace_id)
    return BrandBibleDoc(workspace_id=workspace_id)


# ── JSON loader ──────────────────────────────────────────────────────────────

def _load_json(path: Path, workspace_id: str) -> BrandBibleDoc:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return BrandBibleDoc.model_validate(data)
    except Exception as exc:
        _log.warning("brand_enchancement: JSON load failed (%s) — starting fresh", exc)
        return BrandBibleDoc(workspace_id=workspace_id)


# ── Markdown bootstrap parser ────────────────────────────────────────────────

def _section_text(markdown: str, heading: str) -> str:
    """Extract text under a markdown heading until the next ## heading."""
    pattern = rf"##\s+{re.escape(heading)}\s*\n(.*?)(?=\n##\s|\Z)"
    m = re.search(pattern, markdown, re.DOTALL | re.IGNORECASE)
    return m.group(1).strip() if m else ""


def _bullet_lines(text: str) -> list[str]:
    lines = []
    for line in text.splitlines():
        stripped = re.sub(r"^[-*•]\s*", "", line.strip())
        if stripped:
            lines.append(stripped)
    return lines


def _parse_markdown(path: Path, workspace_id: str) -> BrandBibleDoc:
    """Best-effort parse of a hand-written brand bible markdown into BrandBibleDoc."""
    md = path.read_text(encoding="utf-8")

    # Brand Summary
    summary_txt = _section_text(md, "Brand Summary")
    sell = _extract_field(summary_txt, "What we sell")
    stand = _extract_field(summary_txt, "What we stand for")
    never = _extract_field(summary_txt, "What we never do")
    brand_summary = BrandSummary(
        what_we_sell=sell, what_we_stand_for=stand, what_we_never_do=never
    )

    # Audience
    aud_txt = _section_text(md, "Audience")
    audience = AudienceSection(
        primary=_extract_field(aud_txt, "Primary") or aud_txt[:120]
    )

    # Voice & Tone
    vt_txt = _section_text(md, "Voice")
    voice_tone = VoiceToneSection(
        adjectives=_bullet_lines(_extract_field(vt_txt, "Tone adjectives") or vt_txt)[:6]
    )

    # Proof & Claims
    proof_txt = _section_text(md, "Proof")
    proof = ProofClaimsSection(
        allowed=_bullet_lines(_extract_field(proof_txt, "Allowed") or "")[:8],
        forbidden=_bullet_lines(_extract_field(proof_txt, "Forbidden") or "")[:8],
    )

    # Visual Style
    vis_txt = _section_text(md, "Visual")
    visual = VisualStyleSection(
        do=_bullet_lines(_extract_field(vis_txt, "Do") or "")[:6],
        dont=_bullet_lines(_extract_field(vis_txt, "Don") or "")[:6],
    )

    # Offers
    off_txt = _section_text(md, "Offer")
    offers = OffersSection(typical=_bullet_lines(off_txt)[:6])

    # Competitors
    comp_txt = _section_text(md, "Competitor")
    competitors = CompetitorsSection(main=_bullet_lines(comp_txt)[:8])

    return BrandBibleDoc(
        workspace_id=workspace_id,
        brand_summary=brand_summary,
        audience=audience,
        voice_tone=voice_tone,
        proof_claims=proof,
        visual_style=visual,
        offers=offers,
        competitors=competitors,
    )


def _extract_field(text: str, key: str) -> str:
    """Return the value after `key:` or `- key:` on a single line."""
    for line in text.splitlines():
        if re.search(rf"{re.escape(key)}\s*:", line, re.IGNORECASE):
            _, _, val = line.partition(":")
            return val.strip().lstrip("-").strip()
    return ""
