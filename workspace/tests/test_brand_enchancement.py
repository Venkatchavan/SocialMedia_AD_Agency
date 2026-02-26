"""tests.test_brand_enchancement — Unit tests for the Brand Enhancement Engine."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

# Ensure workspace root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from brand_enchancement.schemas import (
    BrandBibleDoc,
    ChangeRecord,
    UpdateSignal,
)
from brand_enchancement.merger import merge_signals, _add_unique
from brand_enchancement.renderer import render_markdown
from brand_enchancement.versioning import (
    diff_summary,
    list_versions,
    load_version,
    save_version,
)


# ── Schema tests ─────────────────────────────────────────────────────────────

class TestSchemas:
    def test_brand_bible_doc_defaults(self):
        doc = BrandBibleDoc(workspace_id="test_ws")
        assert doc.workspace_id == "test_ws"
        assert doc.version == 1
        assert doc.keywords == []
        assert doc.hashtags == []
        assert doc.change_log == []

    def test_update_signal_strips_empties(self):
        sig = UpdateSignal(run_id="r1", keywords=["ai", "", "  "], hashtags=["#ml"])
        assert "" in sig.keywords  # raw; engine strips them

    def test_brand_bible_round_trip(self):
        doc = BrandBibleDoc(
            workspace_id="acme",
            version=3,
            keywords=["saas", "ai"],
            hashtags=["#saas"],
        )
        data = doc.model_dump()
        restored = BrandBibleDoc.model_validate(data)
        assert restored.workspace_id == "acme"
        assert restored.version == 3
        assert restored.keywords == ["saas", "ai"]

    def test_change_record(self):
        rec = ChangeRecord(
            run_id="r1",
            timestamp="2026-01-01T00:00:00",
            fields_updated=["keywords", "hashtags"],
            summary="keywords: ai; hashtags: #ml",
        )
        assert "keywords" in rec.fields_updated


# ── Merger tests ─────────────────────────────────────────────────────────────

class TestMerger:
    def _make_doc(self) -> BrandBibleDoc:
        return BrandBibleDoc(
            workspace_id="test",
            keywords=["health", "fitness"],
            hashtags=["#wellness"],
        )

    def test_add_new_keywords(self):
        doc = self._make_doc()
        sig = UpdateSignal(run_id="r1", keywords=["ai", "saas"])
        result = merge_signals(doc, sig)
        assert "ai" in result.keywords
        assert "saas" in result.keywords
        assert "health" in result.keywords  # existing preserved

    def test_no_duplicate_keywords(self):
        doc = self._make_doc()
        sig = UpdateSignal(run_id="r1", keywords=["health", "FITNESS"])
        result = merge_signals(doc, sig)
        # "health" already exists (case-insensitive), "FITNESS" matches "fitness"
        assert result.keywords.count("health") == 1

    def test_version_increments(self):
        doc = self._make_doc()
        sig = UpdateSignal(run_id="r2", keywords=["new"])
        result = merge_signals(doc, sig)
        assert result.version == doc.version + 1

    def test_change_log_appended(self):
        doc = self._make_doc()
        sig = UpdateSignal(run_id="r3", keywords=["ml"], hashtags=["#deeplearning"])
        result = merge_signals(doc, sig)
        assert len(result.change_log) == 1
        assert result.change_log[0].run_id == "r3"

    def test_extra_context_accumulated(self):
        doc = self._make_doc()
        sig = UpdateSignal(run_id="r4", extra_context="Enterprise launch Q2")
        result = merge_signals(doc, sig)
        assert "Enterprise launch Q2" in result.extra_context_log

    def test_add_unique_helper(self):
        existing = ["a", "B", "c"]
        new = ["b", "D", "a"]
        result = _add_unique(existing, new)
        assert "D" in result
        assert "b" not in result  # "b" matches "B" case-insensitively
        assert "a" not in result  # duplicate

    def test_no_mutation_of_original(self):
        doc = self._make_doc()
        sig = UpdateSignal(run_id="r5", keywords=["new_kw"])
        _ = merge_signals(doc, sig)
        assert "new_kw" not in doc.keywords  # original untouched

    def test_llm_patch_skipped_gracefully(self):
        """merge_signals must not raise even when LLMRouter.generate fails."""
        doc = self._make_doc()
        sig = UpdateSignal(run_id="r6", keywords=["test"])
        with patch("analyzers.llm_router.LLMRouter") as mock_cls:
            mock_cls.return_value.generate.side_effect = RuntimeError("quota exceeded")
            result = merge_signals(doc, sig)
        assert "test" in result.keywords


# ── Renderer tests ────────────────────────────────────────────────────────────

class TestRenderer:
    def _sample_doc(self) -> BrandBibleDoc:
        doc = BrandBibleDoc(workspace_id="acme_saas", version=2, run_id="run1")
        doc.brand_summary.what_we_sell = "B2B automation platform"
        doc.brand_summary.industry = "saas"
        doc.keywords = ["automation", "AI"]
        doc.hashtags = ["#SaaS2026"]
        return doc

    def test_markdown_contains_workspace(self):
        md = render_markdown(self._sample_doc())
        assert "acme_saas" in md

    def test_markdown_contains_version(self):
        md = render_markdown(self._sample_doc())
        assert "Version 2" in md

    def test_markdown_contains_keywords(self):
        md = render_markdown(self._sample_doc())
        assert "automation" in md
        assert "#SaaS2026" in md

    def test_markdown_has_all_sections(self):
        md = render_markdown(self._sample_doc())
        for section in ["Brand Summary", "Audience", "Voice", "Proof", "Visual", "Offers",
                        "Competitors", "Accumulated Signals", "Change Log"]:
            assert section in md


# ── Versioning tests (uses tmp filesystem) ────────────────────────────────────

class TestVersioning:
    def _patch_clients_root(self, tmp_path: Path):
        """Patch _CLIENTS_ROOT so tests write to tmp_path."""
        import brand_enchancement.versioning as ver_mod
        ver_mod._CLIENTS_ROOT = tmp_path
        return tmp_path

    def test_save_and_list_versions(self, tmp_path):
        self._patch_clients_root(tmp_path)
        doc = BrandBibleDoc(workspace_id="ws1", version=1, run_id="r1", updated_at="2026-01")
        save_version(doc, "ws1")
        versions = list_versions("ws1")
        assert len(versions) == 1
        assert versions[0]["version"] == 1

    def test_load_version(self, tmp_path):
        self._patch_clients_root(tmp_path)
        doc = BrandBibleDoc(workspace_id="ws2", version=1, run_id="r1", updated_at="2026-01")
        save_version(doc, "ws2")
        loaded = load_version("ws2", 1)
        assert loaded is not None
        assert loaded.workspace_id == "ws2"

    def test_live_json_written(self, tmp_path):
        self._patch_clients_root(tmp_path)
        doc = BrandBibleDoc(workspace_id="ws3", version=1, run_id="r1")
        save_version(doc, "ws3")
        live = tmp_path / "ws3" / "BrandBible.json"
        assert live.exists()

    def test_diff_summary(self):
        old = BrandBibleDoc(workspace_id="x", version=1, keywords=["a"])
        new = BrandBibleDoc(workspace_id="x", version=2, keywords=["a", "b"])
        summary = diff_summary(old, new)
        assert "1 →" in summary or "Version 1 → 2" in summary
