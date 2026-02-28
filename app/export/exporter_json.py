"""JSON exporter — renders brief data as structured JSON."""

from __future__ import annotations

import json
from typing import Any

from app.export.base_exporter import BaseExporter, ExportResult


class JsonExporter(BaseExporter):
    """Export briefs as JSON (.json) files."""

    format_name = "json"

    def export(self, brief_data: dict[str, Any], output_path: str) -> ExportResult:
        """Render brief data to a JSON file with envelope."""
        path = self._ensure_dir(f"{output_path}.json")

        envelope = {
            "status": "ok",
            "format": "json",
            "brief": brief_data,
        }

        content = json.dumps(envelope, indent=2, default=str)
        path.write_text(content, encoding="utf-8")

        return ExportResult(
            format="json",
            output_path=str(path),
            file_size_bytes=len(content.encode()),
        )
