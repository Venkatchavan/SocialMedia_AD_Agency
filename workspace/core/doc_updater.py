"""core.doc_updater — Append phase notes and update top-level docs."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from core.config import PROJECT_ROOT, run_path
from core.logging import get_logger

_log = get_logger(__name__)


def append_phase_notes(
    workspace_id: str,
    run_id: str,
    phase: str,
    *,
    executed: str = "",
    artifacts: list[str] | None = None,
    errors: list[str] | None = None,
    next_actions: list[str] | None = None,
) -> Path:
    """Append a section to runs/<run_id>/phase_notes.md."""
    rp = run_path(workspace_id, run_id)
    fp = rp / "phase_notes.md"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        f"\n## Phase: {phase}  ({ts})\n",
        f"**Executed:** {executed}\n",
    ]
    if artifacts:
        lines.append("**Artifacts:**\n")
        for a in artifacts:
            lines.append(f"- {a}\n")
    if errors:
        lines.append("**Errors / Uncertainties:**\n")
        for e in errors:
            lines.append(f"- {e}\n")
    if next_actions:
        lines.append("**Next actions:**\n")
        for n in next_actions:
            lines.append(f"- {n}\n")
    lines.append("---\n")
    with open(fp, "a", encoding="utf-8") as f:
        f.writelines(lines)
    _log.info("Updated phase_notes for [bold]%s[/bold] / %s", phase, run_id)
    return fp


def update_top_level_doc(
    doc_name: str,
    section_title: str,
    content: str,
) -> Path:
    """Append a timestamped section to a top-level doc (e.g. BRAIN.md)."""
    instructions_dir = PROJECT_ROOT.parent / "Instrutctions_File"
    fp = instructions_dir / doc_name
    if not fp.exists():
        fp = PROJECT_ROOT / doc_name
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    block = f"\n\n## {section_title}  ({ts})\n{content}\n"
    with open(fp, "a", encoding="utf-8") as f:
        f.write(block)
    _log.info("Appended to %s: %s", doc_name, section_title)
    return fp
