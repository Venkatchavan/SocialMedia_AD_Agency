"""export.exporter_md — Write Markdown deliverables to run directory."""

from __future__ import annotations

from pathlib import Path

from core.config import run_path
from core.logging import get_logger

_log = get_logger(__name__)


def export_md(
    workspace_id: str,
    run_id: str,
    brief_md: str,
    insights_md: str,
    qa_md: str | None = None,
) -> Path:
    """Write markdown files to the run directory."""
    rp = run_path(workspace_id, run_id)

    _write_md(rp / "brief.md", brief_md)
    _write_md(rp / "insights.md", insights_md)
    if qa_md:
        _write_md(rp / "qa_report.md", qa_md)

    _log.info("Exported MD files to %s", rp)
    return rp


def render_qa_md(qa_report_dict: dict) -> str:
    """Render a QAReport dict into readable Markdown."""
    lines: list[str] = ["# QA Report\n"]
    lines.append(f"**Result:** {qa_report_dict.get('result', 'unknown')}\n")
    lines.append(f"**PII found:** {qa_report_dict.get('pii_found', False)}\n")
    lines.append(f"**Copy risk:** {qa_report_dict.get('copy_risk', 'low')}\n")
    lines.append(f"**Claim risk:** {qa_report_dict.get('claim_risk', 'low')}\n")

    violations = qa_report_dict.get("violations", [])
    if violations:
        lines.append("\n## Violations\n")
        for v in violations:
            lines.append(f"- **[{v.get('severity', '?')}]** {v.get('rule', '?')}: {v.get('detail', '')}\n")

    fixes = qa_report_dict.get("fixes_required", [])
    if fixes:
        lines.append("\n## Fixes Required\n")
        for f in fixes:
            lines.append(f"- {f}\n")

    return "\n".join(lines)


def _write_md(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
