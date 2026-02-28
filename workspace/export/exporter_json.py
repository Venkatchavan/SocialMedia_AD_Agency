"""export.exporter_json — Write JSON bundle to run directory."""

from __future__ import annotations

import json
from pathlib import Path

from core.config import run_path
from core.logging import get_logger
from core.schemas_brief import BriefObject
from core.schemas_qa import QAReport

_log = get_logger(__name__)


def export_json_bundle(
    workspace_id: str,
    run_id: str,
    brief: BriefObject,
    qa_report: QAReport,
    assets_json: list[dict] | None = None,
    tags_json: list[dict] | None = None,
    clusters_json: list[dict] | None = None,
) -> Path:
    """Write all pipeline outputs as JSON files to the run directory."""
    rp = run_path(workspace_id, run_id)

    _write_json(rp / "brief.json", brief.model_dump())
    _write_json(rp / "qa_report.json", qa_report.model_dump())

    if assets_json is not None:
        _write_json(rp / "assets.json", assets_json)
    if tags_json is not None:
        _write_json(rp / "tags.json", tags_json)
    if clusters_json is not None:
        _write_json(rp / "clusters.json", clusters_json)

    _log.info("Exported JSON bundle to %s", rp)
    return rp


def _write_json(path: Path, data: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
