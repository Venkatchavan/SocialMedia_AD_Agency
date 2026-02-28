"""Tests for brief export formats (U-12)."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from app.export.base_exporter import ExportResult, get_available_formats
from app.export.exporter_md import MarkdownExporter
from app.export.exporter_json import JsonExporter
from app.export.exporter_html import HtmlExporter
from app.export.export_orchestrator import export_brief


SAMPLE_BRIEF = {
    "title": "Summer Headphones Campaign",
    "workspace_id": "ws_test_001",
    "run_id": "run_abc",
    "overview": "Target college students with wireless headphones.",
    "hooks": [
        {"text": "POV: Your roommate asks what you're listening to", "score": 92},
        {"text": "The $49 headphones that sound like $200", "score": 88},
    ],
    "angles": [
        {"name": "comparison", "description": "vs. AirPods at 3x the price"},
        {"name": "story", "description": "Day in the life with these headphones"},
    ],
    "scripts": [
        {
            "hook": "POV: Your roommate asks",
            "scenes": [
                {"scene_number": 1, "scene_type": "hook", "dialogue": "Wait, those are HOW much?", "visual_direction": "Close-up on headphones"},
                {"scene_number": 2, "scene_type": "body", "dialogue": "Let me show you", "visual_direction": "Product demo"},
            ],
        }
    ],
    "brand_voice": {"tone": "casual", "audience": "Gen Z", "avoid": "corporate jargon"},
    "references": [
        {"title": "Lo-fi hip hop aesthetic", "reference_type": "style_only"},
    ],
}


class TestExportResult:
    def test_frozen(self):
        r = ExportResult(format="md", output_path="/tmp/x.md")
        with pytest.raises(AttributeError):
            r.format = "json"  # type: ignore[misc]

    def test_default_success(self):
        r = ExportResult(format="test", output_path="x")
        assert r.success is True
        assert r.error == ""


class TestAvailableFormats:
    def test_all_listed(self):
        fmts = get_available_formats()
        assert "markdown" in fmts
        assert "json" in fmts
        assert "html" in fmts
        assert "pptx" in fmts
        assert "pdf" in fmts


class TestMarkdownExporter:
    def test_creates_file(self, tmp_path):
        exp = MarkdownExporter()
        result = exp.export(SAMPLE_BRIEF, str(tmp_path / "brief"))
        assert result.success
        assert result.format == "markdown"
        assert os.path.exists(result.output_path)

    def test_contains_title(self, tmp_path):
        exp = MarkdownExporter()
        result = exp.export(SAMPLE_BRIEF, str(tmp_path / "brief"))
        content = open(result.output_path, encoding="utf-8").read()
        assert "# Summer Headphones Campaign" in content

    def test_contains_hooks(self, tmp_path):
        exp = MarkdownExporter()
        result = exp.export(SAMPLE_BRIEF, str(tmp_path / "brief"))
        content = open(result.output_path, encoding="utf-8").read()
        assert "POV: Your roommate" in content

    def test_contains_workspace(self, tmp_path):
        exp = MarkdownExporter()
        result = exp.export(SAMPLE_BRIEF, str(tmp_path / "brief"))
        content = open(result.output_path, encoding="utf-8").read()
        assert "ws_test_001" in content

    def test_file_size_populated(self, tmp_path):
        exp = MarkdownExporter()
        result = exp.export(SAMPLE_BRIEF, str(tmp_path / "brief"))
        assert result.file_size_bytes > 0


class TestJsonExporter:
    def test_creates_valid_json(self, tmp_path):
        exp = JsonExporter()
        result = exp.export(SAMPLE_BRIEF, str(tmp_path / "brief"))
        assert result.success
        data = json.loads(open(result.output_path, encoding="utf-8").read())
        assert data["status"] == "ok"
        assert data["format"] == "json"
        assert data["brief"]["title"] == "Summer Headphones Campaign"

    def test_envelope_structure(self, tmp_path):
        exp = JsonExporter()
        result = exp.export(SAMPLE_BRIEF, str(tmp_path / "brief"))
        data = json.loads(open(result.output_path, encoding="utf-8").read())
        assert "status" in data
        assert "brief" in data


class TestHtmlExporter:
    def test_creates_html(self, tmp_path):
        exp = HtmlExporter()
        result = exp.export(SAMPLE_BRIEF, str(tmp_path / "brief"))
        assert result.success
        assert result.output_path.endswith(".html")

    def test_contains_styled_content(self, tmp_path):
        exp = HtmlExporter()
        result = exp.export(SAMPLE_BRIEF, str(tmp_path / "brief"))
        content = open(result.output_path, encoding="utf-8").read()
        assert "<style>" in content
        assert "Summer Headphones Campaign" in content

    def test_html_escaping(self, tmp_path):
        brief = {"title": "Test <script>alert('xss')</script>"}
        exp = HtmlExporter()
        result = exp.export(brief, str(tmp_path / "brief"))
        content = open(result.output_path, encoding="utf-8").read()
        assert "<script>" not in content
        assert "&lt;script&gt;" in content


class TestExportOrchestrator:
    def test_default_formats(self, tmp_path):
        results = export_brief(SAMPLE_BRIEF, str(tmp_path / "brief"))
        assert len(results) == 2
        formats = {r.format for r in results}
        assert "markdown" in formats
        assert "json" in formats

    def test_specific_formats(self, tmp_path):
        results = export_brief(SAMPLE_BRIEF, str(tmp_path / "brief"), ["html", "json"])
        assert len(results) == 2
        assert all(r.success for r in results)

    def test_unknown_format_error(self, tmp_path):
        results = export_brief(SAMPLE_BRIEF, str(tmp_path / "brief"), ["docx"])
        assert len(results) == 1
        assert not results[0].success
        assert "Unknown format" in results[0].error

    def test_mixed_valid_invalid(self, tmp_path):
        results = export_brief(
            SAMPLE_BRIEF, str(tmp_path / "brief"), ["markdown", "docx"]
        )
        assert results[0].success
        assert not results[1].success

    def test_empty_brief(self, tmp_path):
        results = export_brief({}, str(tmp_path / "brief"), ["markdown"])
        assert len(results) == 1
        assert results[0].success  # Should still generate with defaults
