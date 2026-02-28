"""Multi-format export orchestrator.

Resolves format names → exporters and runs batch exports.
"""

from __future__ import annotations

from typing import Any

from app.export.base_exporter import BaseExporter, ExportResult


def _build_registry() -> dict[str, BaseExporter]:
    """Lazy-build the exporter registry."""
    from app.export.exporter_html import HtmlExporter
    from app.export.exporter_json import JsonExporter
    from app.export.exporter_md import MarkdownExporter
    from app.export.exporter_pdf import PdfExporter
    from app.export.exporter_pptx import PptxExporter

    return {
        "markdown": MarkdownExporter(),
        "md": MarkdownExporter(),
        "json": JsonExporter(),
        "html": HtmlExporter(),
        "pptx": PptxExporter(),
        "pdf": PdfExporter(),
    }


def export_brief(
    brief_data: dict[str, Any],
    output_path: str,
    formats: list[str] | None = None,
) -> list[ExportResult]:
    """Export brief data to one or more formats.

    Args:
        brief_data: Dictionary containing brief sections.
        output_path: Base path (without extension).
        formats: List of format names. If None, exports markdown + json.

    Returns:
        List of ExportResult for each attempted format.
    """
    if formats is None:
        formats = ["markdown", "json"]

    registry = _build_registry()
    results: list[ExportResult] = []

    for fmt in formats:
        fmt_lower = fmt.lower().strip()
        exporter = registry.get(fmt_lower)
        if exporter is None:
            results.append(
                ExportResult(
                    format=fmt_lower,
                    output_path="",
                    success=False,
                    error=f"Unknown format: {fmt_lower}. "
                    f"Available: {list(registry.keys())}",
                )
            )
            continue
        try:
            result = exporter.export(brief_data, output_path)
            results.append(result)
        except Exception as exc:
            results.append(
                ExportResult(
                    format=fmt_lower,
                    output_path="",
                    success=False,
                    error=str(exc),
                )
            )

    return results
