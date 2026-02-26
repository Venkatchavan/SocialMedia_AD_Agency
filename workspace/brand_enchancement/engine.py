"""brand_enchancement.engine — Main orchestrator for brand bible updates.

Usage (programmatic):
    from brand_enchancement.engine import update_brand_bible

    result = update_brand_bible(
        workspace_id="acme_saas",
        keywords=["productivity", "AI", "B2B"],
        hashtags=["#SaaS", "#AItools"],
        extra_context="Launching enterprise tier in Q2",
        run_id="run_20260101",              # optional
    )
    print(result.report)    # human-readable summary
    print(result.version)   # new version number

The engine is fully industry-agnostic and idempotent:
  - Running with the same signals twice produces no duplicate entries.
  - Running with no changed signals still records a run but skips LLM.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path

from brand_enchancement.loader import load_brand_bible
from brand_enchancement.merger import merge_signals
from brand_enchancement.renderer import write_brand_markdown
from brand_enchancement.schemas import BrandBibleDoc, UpdateSignal
from brand_enchancement.versioning import diff_summary, save_version
from core.logging import get_logger
from core.utils_time import utcnow_iso

_log = get_logger(__name__)


# ── Result container ─────────────────────────────────────────────────────────

@dataclass
class EnhanceResult:
    """Returned by update_brand_bible()."""

    workspace_id: str
    version: int
    run_id: str
    updated_at: str
    report: str
    json_path: Path
    md_path: Path
    snapshot_path: Path
    fields_updated: list[str] = field(default_factory=list)


# ── Public entry point ───────────────────────────────────────────────────────

def update_brand_bible(
    workspace_id: str,
    keywords: list[str] | None = None,
    hashtags: list[str] | None = None,
    extra_context: str = "",
    run_id: str | None = None,
) -> EnhanceResult:
    """Load, enrich, merge, version, and render the brand bible for *workspace_id*.

    Parameters
    ----------
    workspace_id:
        Folder name under ``clients/``.  Will be created on first run.
    keywords:
        New keyword signals to merge (e.g. ["AI", "automation", "SaaS"]).
    hashtags:
        New hashtag signals (e.g. ["#AItools", "#SaaS2026"]).
    extra_context:
        Free-form notes for this run (stored in context log, fed to LLM).
    run_id:
        Optional explicit run ID; auto-generated if omitted.

    Returns
    -------
    EnhanceResult with paths to each output file and a human-readable report.
    """
    run_id = run_id or f"enhance_{utcnow_iso()[:16].replace(':', '').replace('T', '_')}_{uuid.uuid4().hex[:6]}"
    signal = UpdateSignal(
        run_id=run_id,
        keywords=[k.strip() for k in (keywords or []) if k.strip()],
        hashtags=[h.strip() for h in (hashtags or []) if h.strip()],
        extra_context=extra_context.strip(),
    )

    _log.info(
        "brand_enchancement: starting run=%s workspace=%s kw=%d ht=%d",
        run_id, workspace_id, len(signal.keywords), len(signal.hashtags),
    )

    # 1 — Load existing (or bootstrap fresh) brand bible
    old_doc: BrandBibleDoc = load_brand_bible(workspace_id)

    # 2 — Merge signals (LLM-assisted; graceful fallback)
    new_doc: BrandBibleDoc = merge_signals(old_doc, signal)

    # 3 — Save versioned snapshot + live JSON
    snapshot_path = save_version(new_doc, workspace_id)

    # 4 — Write human-readable markdown
    md_path = write_brand_markdown(new_doc, workspace_id)

    # 5 — Build result report
    change_summary = diff_summary(old_doc, new_doc)
    report_lines = [
        f"Brand Bible updated for workspace '{workspace_id}'",
        change_summary,
        f"  JSON: {snapshot_path.parent.parent / 'BrandBible.json'}",
        f"  MD:   {md_path}",
        f"  Snapshot: {snapshot_path}",
    ]
    report = "\n".join(report_lines)
    _log.info("brand_enchancement: done run=%s version=%d", run_id, new_doc.version)

    # Derive fields_updated from latest change log entry
    fields_updated: list[str] = []
    if new_doc.change_log:
        fields_updated = new_doc.change_log[-1].fields_updated

    return EnhanceResult(
        workspace_id=workspace_id,
        version=new_doc.version,
        run_id=run_id,
        updated_at=new_doc.updated_at,
        report=report,
        json_path=snapshot_path.parent.parent / "BrandBible.json",
        md_path=md_path,
        snapshot_path=snapshot_path,
        fields_updated=fields_updated,
    )
