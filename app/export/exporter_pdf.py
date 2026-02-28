"""PDF exporter — renders brief data to PDF via HTML intermediate.

Uses weasyprint for HTML→PDF conversion. Falls back to error if not installed.
"""

from __future__ import annotations

from typing import Any

from app.export.base_exporter import BaseExporter, ExportResult
from app.export.exporter_html import HtmlExporter


class PdfExporter(BaseExporter):
    """Export briefs as PDF files via HTML→PDF pipeline."""

    format_name = "pdf"

    def __init__(self) -> None:
        self._html_exporter = HtmlExporter()

    def export(self, brief_data: dict[str, Any], output_path: str) -> ExportResult:
        """Render brief data to PDF.

        Pipeline: brief_data → HTML string → weasyprint → PDF file.
        """
        try:
            from weasyprint import HTML as WeasyprintHTML  # type: ignore[import-untyped]
        except ImportError:
            return ExportResult(
                format="pdf",
                output_path="",
                success=False,
                error="weasyprint not installed. pip install weasyprint",
            )

        # Generate HTML first (to temp path)
        html_result = self._html_exporter.export(brief_data, f"{output_path}_tmp")
        if not html_result.success:
            return ExportResult(
                format="pdf", output_path="", success=False, error=html_result.error
            )

        # Convert HTML → PDF
        pdf_path = self._ensure_dir(f"{output_path}.pdf")
        try:
            html_content = open(html_result.output_path, encoding="utf-8").read()
            WeasyprintHTML(string=html_content).write_pdf(str(pdf_path))

            file_size = pdf_path.stat().st_size
            return ExportResult(
                format="pdf",
                output_path=str(pdf_path),
                file_size_bytes=file_size,
            )
        except Exception as exc:
            return ExportResult(
                format="pdf",
                output_path="",
                success=False,
                error=f"PDF generation failed: {exc}",
            )
        finally:
            # Clean up temp HTML
            import os
            if html_result.output_path and os.path.exists(html_result.output_path):
                os.unlink(html_result.output_path)
