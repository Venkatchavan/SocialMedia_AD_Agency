"""tests.test_compliance_runtime — Tests for cleanup job and incident handler (§6.3, §14)."""

from __future__ import annotations

import json
import os
from pathlib import Path


from compliance.cleanup import purge_expired_runs
from compliance.incident import IncidentType, trigger_incident


# ── Cleanup (§6.3) ────────────────────────────────────────────────────────────

class TestCleanup:
    def test_dry_run_does_not_delete(self, tmp_path: Path):
        import compliance.cleanup as cc

        ws = tmp_path / "clients" / "testws" / "runs" / "2000-01-01_000000"
        ws.mkdir(parents=True)
        (ws / "brief.json").write_text("{}", encoding="utf-8")
        os.utime(ws, (0.0, 0.0))  # epoch = ancient

        orig = cc.CLIENTS_DIR
        cc.CLIENTS_DIR = tmp_path / "clients"
        try:
            report = purge_expired_runs("testws", dry_run=True, retention_days=1)
        finally:
            cc.CLIENTS_DIR = orig

        assert report.total_runs_purged == 1
        assert ws.exists()  # dry_run → not actually deleted

    def test_live_run_deletes_expired(self, tmp_path: Path):
        import compliance.cleanup as cc

        ws = tmp_path / "clients" / "testws" / "runs" / "2000-01-01_000001"
        ws.mkdir(parents=True)
        (ws / "brief.json").write_text("{}", encoding="utf-8")
        os.utime(ws, (0.0, 0.0))

        orig = cc.CLIENTS_DIR
        cc.CLIENTS_DIR = tmp_path / "clients"
        try:
            report = purge_expired_runs("testws", dry_run=False, retention_days=1)
        finally:
            cc.CLIENTS_DIR = orig

        assert report.total_runs_purged == 1
        assert not ws.exists()  # actually deleted

    def test_sensitive_file_purged_always(self, tmp_path: Path):
        import compliance.cleanup as cc

        ws = tmp_path / "clients" / "testws" / "runs" / "fresh-run"
        ws.mkdir(parents=True)
        sensitive = ws / "raw_comments.json"
        sensitive.write_text('{"commenter": "user123"}', encoding="utf-8")

        orig = cc.CLIENTS_DIR
        cc.CLIENTS_DIR = tmp_path / "clients"
        try:
            purge_expired_runs("testws", dry_run=False, retention_days=9999)
        finally:
            cc.CLIENTS_DIR = orig

        assert not sensitive.exists()  # purged unconditionally regardless of age

    def test_no_runs_dir_returns_empty_report(self, tmp_path: Path):
        import compliance.cleanup as cc

        orig = cc.CLIENTS_DIR
        cc.CLIENTS_DIR = tmp_path
        try:
            report = purge_expired_runs("ghost_workspace")
        finally:
            cc.CLIENTS_DIR = orig

        assert report.total_runs_purged == 0
        assert report.bytes_freed == 0

    def test_recent_runs_not_purged(self, tmp_path: Path):
        import compliance.cleanup as cc

        ws = tmp_path / "clients" / "testws" / "runs" / "recent-run"
        ws.mkdir(parents=True)
        (ws / "brief.json").write_text("{}", encoding="utf-8")

        orig = cc.CLIENTS_DIR
        cc.CLIENTS_DIR = tmp_path / "clients"
        try:
            report = purge_expired_runs("testws", dry_run=False, retention_days=9999)
        finally:
            cc.CLIENTS_DIR = orig

        assert report.total_runs_purged == 0
        assert ws.exists()


# ── Incident (§14) ────────────────────────────────────────────────────────────

class TestIncident:
    def _setup_run(self, tmp_path: Path, run_id: str) -> Path:
        run_dir = tmp_path / "clients" / "testws" / "runs" / run_id
        run_dir.mkdir(parents=True)
        (run_dir / "phase_notes.md").write_text("## Existing notes\n", encoding="utf-8")
        (tmp_path / "data").mkdir(exist_ok=True)
        return run_dir

    def _patch(self, inc, tmp_path: Path):
        orig_c, orig_d = inc.CLIENTS_DIR, inc.DATA_DIR
        inc.CLIENTS_DIR = tmp_path / "clients"
        inc.DATA_DIR = tmp_path / "data"
        return orig_c, orig_d

    def test_incident_logged_to_jsonl(self, tmp_path: Path):
        import compliance.incident as inc
        self._setup_run(tmp_path, "run-log-test")
        orig_c, orig_d = self._patch(inc, tmp_path)
        try:
            trigger_incident("run-log-test", "testws", IncidentType.PII_LEAKED, "PII test")
        finally:
            inc.CLIENTS_DIR, inc.DATA_DIR = orig_c, orig_d

        log_path = tmp_path / "data" / "incident_log.jsonl"
        entry = json.loads(log_path.read_text().strip().splitlines()[-1])
        assert entry["type"] == "pii_leaked"
        assert entry["workspace_id"] == "testws"

    def test_incident_note_in_phase_notes(self, tmp_path: Path):
        import compliance.incident as inc
        run_dir = self._setup_run(tmp_path, "run-note-test")
        orig_c, orig_d = self._patch(inc, tmp_path)
        try:
            trigger_incident("run-note-test", "testws", "other", "Manual test")
        finally:
            inc.CLIENTS_DIR, inc.DATA_DIR = orig_c, orig_d

        content = (run_dir / "phase_notes.md").read_text(encoding="utf-8")
        assert "INCIDENT NOTE" in content

    def test_incident_purges_sensitive_files(self, tmp_path: Path):
        import compliance.incident as inc
        run_dir = self._setup_run(tmp_path, "run-purge-test")
        (run_dir / "raw_comments.json").write_text("[{}]", encoding="utf-8")
        orig_c, orig_d = self._patch(inc, tmp_path)
        try:
            incident = trigger_incident(
                "run-purge-test", "testws", IncidentType.PII_LEAKED, "Purge test", purge_run=True
            )
        finally:
            inc.CLIENTS_DIR, inc.DATA_DIR = orig_c, orig_d

        assert not (run_dir / "raw_comments.json").exists()
        assert len(incident.data_purged) >= 1

    def test_key_rotation_flag(self, tmp_path: Path):
        import compliance.incident as inc
        self._setup_run(tmp_path, "run-key-test")
        orig_c, orig_d = self._patch(inc, tmp_path)
        try:
            incident = trigger_incident(
                "run-key-test", "testws", "other", "Key test", key_rotation_required=True
            )
        finally:
            inc.CLIENTS_DIR, inc.DATA_DIR = orig_c, orig_d

        assert incident.key_rotation_required is True
        assert any("Rotate" in a for a in incident.actions_taken)
