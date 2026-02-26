"""tests.test_schemas — Validate Pydantic schema round-trips and constraints."""

from __future__ import annotations

import json

import pytest

from core.enums import (
    AoTType,
    AssetStatus,
    Confidence,
    FormatType,
    HookTactic,
    MessagingAngle,
    Platform,
    QAResult,
    RiskLevel,
)
from core.schemas_aot import AoTAtom
from core.schemas_asset import Asset, Metrics, PlatformFields, Provenance
from core.schemas_brief import BriefObject
from core.schemas_qa import QAReport, QAViolation
from core.schemas_tag import TagSet


# ── Asset ───────────────────────────────────────────


def _make_asset(**overrides) -> Asset:
    defaults = dict(
        asset_id="tiktok:12345",
        platform=Platform.TIKTOK,
        workspace_id="sample_client",
        run_id="2026-01-01",
        brand="TestBrand",
        collected_at="2026-01-01T00:00:00Z",
        provenance=Provenance(
            collector="TestCollector",
            fetched_at="2026-01-01T00:00:00Z",
        ),
    )
    defaults.update(overrides)
    return Asset(**defaults)


def test_asset_creation():
    a = _make_asset()
    assert a.asset_id == "tiktok:12345"
    assert a.platform == Platform.TIKTOK
    assert a.status == AssetStatus.UNKNOWN


def test_asset_json_roundtrip():
    a = _make_asset(caption_or_copy="Hello world")
    data = json.loads(a.model_dump_json())
    a2 = Asset.model_validate(data)
    assert a2.caption_or_copy == "Hello world"


def test_asset_metrics_defaults():
    a = _make_asset()
    assert a.metrics.views is None
    assert a.metrics_extra.saves is None


# ── TagSet ──────────────────────────────────────────


def test_tagset_defaults():
    ts = TagSet(asset_id="test:1")
    assert ts.format_type == FormatType.UNKNOWN
    assert ts.hook_tactics == []


def test_tagset_roundtrip():
    ts = TagSet(
        asset_id="meta:brand:1",
        format_type=FormatType.UGC_SELFIE,
        hook_tactics=[HookTactic.CURIOSITY_GAP],
        messaging_angle=MessagingAngle.CONVENIENCE,
    )
    data = json.loads(ts.model_dump_json())
    ts2 = TagSet.model_validate(data)
    assert ts2.format_type == FormatType.UGC_SELFIE


# ── BriefObject ─────────────────────────────────────


def test_brief_creation():
    b = BriefObject(workspace_id="ws", run_id="r1", smp="Test SMP")
    assert b.smp == "Test SMP"
    assert b.rtbs == []


# ── QAReport ────────────────────────────────────────


def test_qa_report_pass():
    r = QAReport(workspace_id="ws", run_id="r1")
    assert r.result == QAResult.PASS
    assert r.pii_found is False


def test_qa_report_with_violations():
    r = QAReport(
        workspace_id="ws",
        run_id="r1",
        result=QAResult.FAIL,
        violations=[
            QAViolation(rule="pii_check", severity="fail", detail="email found")
        ],
        pii_found=True,
    )
    assert r.result == QAResult.FAIL
    assert len(r.violations) == 1


# ── AoTAtom ─────────────────────────────────────────


def test_aot_atom_creation():
    atom = AoTAtom(
        type=AoTType.EVIDENCE,
        source_assets=["tiktok:1"],
        content="Test evidence.",
        confidence=Confidence.HIGH,
    )
    assert atom.type == AoTType.EVIDENCE
    assert atom.atom_id  # auto-generated UUID


def test_aot_jsonl_format():
    atom = AoTAtom(
        type=AoTType.HYPOTHESIS,
        source_assets=["meta:b:1"],
        content="Test hypothesis.",
    )
    line = atom.model_dump_json()
    parsed = json.loads(line)
    assert parsed["type"] == "HYPOTHESIS"
