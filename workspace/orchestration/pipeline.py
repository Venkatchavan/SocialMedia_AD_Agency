"""orchestration.pipeline — End-to-end pipeline runner (non-CrewAI path)."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from core.config import run_path
from core.doc_updater import append_phase_notes
from core.enums import QAResult
from core.errors import QAFailError
from core.logging import get_logger
from core.schemas_asset import Asset
from analyzers.media_analyzer import analyze_batch
from briefs.brief_renderer_md import render_brief_md
from briefs.brief_writer import write_brief
from briefs.template_loader import load_brand_bible
from db.repo_runs import create_run, finish_run
from db.sqlite import init_db
from export.exporter_json import export_json_bundle
from export.exporter_md import export_md, render_qa_md
from export.packager import package_run
from qa.qa_gate import run_qa_gate
from synthesis.aot_writer import write_aot_ledger
from synthesis.clustering import cluster_tags
from synthesis.insights import generate_insights
from synthesis.ranking import rank_assets

_log = get_logger(__name__)


def run_pipeline(
    workspace_id: str,
    assets: list[Asset],
    comment_items: list[dict] | None = None,
    competitor_texts: list[str] | None = None,
) -> dict:
    """Execute the full pipeline: Analyze → Synthesize → Brief → QA → Export."""
    run_id = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    init_db()
    create_run(run_id, workspace_id, notes="pipeline run")
    rp = run_path(workspace_id, run_id)

    # Phase 1: Analyze
    append_phase_notes(workspace_id, run_id, "ANALYZE", executed="Tag assets")
    tags = analyze_batch(assets)
    tags_data = [t.model_dump() for t in tags]
    _write(rp / "tags.json", tags_data)
    append_phase_notes(workspace_id, run_id, "ANALYZE", artifacts=["tags.json"])

    # Phase 2: Synthesize
    append_phase_notes(workspace_id, run_id, "SYNTHESIZE", executed="Rank + cluster")
    ranked = rank_assets(assets, tags)
    clusters = cluster_tags(tags)
    insights_md = generate_insights(clusters, ranked)
    write_aot_ledger(clusters, tags, rp / "aot_ledger.jsonl")
    _write(rp / "clusters.json", [c.model_dump() for c in clusters])
    _write(rp / "insights.md", insights_md, is_text=True)
    append_phase_notes(
        workspace_id, run_id, "SYNTHESIZE",
        artifacts=["clusters.json", "insights.md", "aot_ledger.jsonl"],
    )

    # Phase 3: Brief
    append_phase_notes(workspace_id, run_id, "BRIEF", executed="Generate brief")
    brand_bible = load_brand_bible(workspace_id)
    brief = write_brief(workspace_id, run_id, clusters, insights_md, brand_bible)
    brief_md = render_brief_md(brief)
    append_phase_notes(workspace_id, run_id, "BRIEF", artifacts=["brief.md", "brief.json"])

    # Phase 4: QA Gate
    append_phase_notes(workspace_id, run_id, "QA", executed="Run QA checks")
    qa_report = run_qa_gate(brief, brief_md, competitor_texts)
    qa_md = render_qa_md(qa_report.model_dump())
    append_phase_notes(
        workspace_id, run_id, "QA",
        artifacts=["qa_report.json", "qa_report.md"],
        errors=[v.detail for v in qa_report.violations],
    )

    # Phase 5: Export (blocked if QA FAIL)
    if qa_report.result == QAResult.FAIL:
        _write(rp / "qa_report.json", qa_report.model_dump())
        _write(rp / "qa_report.md", qa_md, is_text=True)
        finish_run(run_id, status="qa_fail")
        append_phase_notes(
            workspace_id, run_id, "EXPORT",
            executed="BLOCKED — QA FAIL", errors=qa_report.fixes_required,
        )
        raise QAFailError(f"QA gate FAIL for run {run_id}")

    append_phase_notes(workspace_id, run_id, "EXPORT", executed="Export deliverables")
    assets_data = [a.model_dump() for a in assets]
    export_json_bundle(
        workspace_id, run_id, brief, qa_report,
        assets_json=assets_data, tags_json=tags_data,
        clusters_json=[c.model_dump() for c in clusters],
    )
    export_md(workspace_id, run_id, brief_md, insights_md, qa_md)
    package_run(workspace_id, run_id)
    finish_run(run_id, status="completed")
    append_phase_notes(
        workspace_id, run_id, "EXPORT",
        artifacts=["packaged_run.zip", "brief.json", "brief.md"],
    )

    _log.info("Pipeline completed: workspace=%s run=%s", workspace_id, run_id)
    return {"workspace_id": workspace_id, "run_id": run_id, "qa": qa_report.result.value}


def _write(path, data, *, is_text: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if is_text:
        path.write_text(data, encoding="utf-8")
    else:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
