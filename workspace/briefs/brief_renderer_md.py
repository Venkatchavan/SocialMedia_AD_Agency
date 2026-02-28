"""briefs.brief_renderer_md — Render a BriefObject into Markdown."""

from __future__ import annotations

from core.schemas_brief import BriefObject
from core.logging import get_logger

_log = get_logger(__name__)


def render_brief_md(brief: BriefObject) -> str:
    """Convert a BriefObject to a human-readable Markdown document."""
    sections: list[str] = []
    sections.append(f"# Creative Brief — {brief.workspace_id} / {brief.run_id}\n")

    sections.append("## 1. Background\n")
    sections.append(f"{brief.background}\n")

    sections.append("## 2. Objective\n")
    sections.append(f"- **Primary:** {brief.objective_primary}\n")
    sections.append(f"- **Secondary:** {brief.objective_secondary}\n")

    sections.append("## 3. Audience\n")
    sections.append(f"- **Persona:** {brief.audience.persona}\n")
    sections.append(f"- **Situation:** {brief.audience.situation}\n")
    sections.append(f"- **Barriers:** {', '.join(brief.audience.barriers)}\n")

    sections.append("## 4. Insight\n")
    sections.append(f"- **Tension:** {brief.insight.tension}\n")
    sections.append(f"- **Why now:** {brief.insight.why_now}\n")

    sections.append("## 5. Single-Minded Proposition (SMP)\n")
    sections.append(f"> {brief.smp}\n")

    sections.append("## 6. Reasons To Believe (RTBs)\n")
    for r in brief.rtbs:
        sections.append(f"- {r}\n")

    sections.append("## 7. Offer + Terms\n")
    sections.append(f"- **Type:** {brief.offer.type}\n")
    sections.append(f"- **Terms:** {brief.offer.terms}\n")
    sections.append(f"- **Urgency:** {brief.offer.urgency}\n")

    sections.append("## 8. Mandatories\n")
    sections.append("**Must include:** " + ", ".join(brief.mandatories.must_include) + "\n")
    sections.append("**Must avoid:** " + ", ".join(brief.mandatories.must_avoid) + "\n")
    sections.append("**Legal:** " + ", ".join(brief.mandatories.legal) + "\n")

    sections.append("## 9. Creative Directions\n")
    for i, d in enumerate(brief.creative_directions, 1):
        sections.append(f"### Direction {i}\n")
        sections.append(f"- Angle: {d.angle} | Hook: {d.hook} | Proof: {d.proof} | CTA: {d.cta}\n")
        sections.append(f"- Notes: {d.notes}\n")

    sections.append("## 10. Hook Bank\n")
    for h in brief.hook_bank:
        sections.append(f"- {h}\n")

    sections.append("## 11. Scripts\n")
    for s in brief.scripts:
        sections.append(f"### {s.title}\n")
        for b in s.beats:
            sections.append(f"| {b.time_range} | {b.action} | {b.on_screen_text} | {b.b_roll} |\n")
        sections.append(f"**CTA line:** {s.cta_line}\n")

    sections.append("## 12. Testing Matrix\n")
    sections.append("| Variant | Hook | Angle | Offer | CTA | Format |\n")
    sections.append("|---------|------|-------|-------|-----|--------|\n")
    for v in brief.testing_matrix:
        sections.append(f"| {v.variant} | {v.hook} | {v.angle} | {v.offer} | {v.cta} | {v.format} |\n")

    sections.append("## 13. Risks / Compliance\n")
    sections.append("**Claim risks:** " + ", ".join(brief.risks.claim_risks) + "\n")
    sections.append("**Platform risks:** " + ", ".join(brief.risks.platform_risks) + "\n")

    sections.append("\n---\n")
    sections.append(f"*Evidence assets: {len(brief.evidence_assets)} referenced.*\n")

    md = "\n".join(sections)
    _log.info("Rendered brief.md (%d chars)", len(md))
    return md
