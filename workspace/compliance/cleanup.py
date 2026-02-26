"""compliance.cleanup — Automated data retention and purge job (§6.3).

Deletes run directories older than the retention window and scrubs any
raw comments that may have been accidentally persisted.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path

from core.config import CLIENTS_DIR
from core.logging import get_logger
from compliance.policy_loader import load_policy

_log = get_logger(__name__)

# Files that contain raw or potentially sensitive data — must be purged first
_SENSITIVE_FILENAMES: frozenset[str] = frozenset(
    {"raw_comments.json", "comments.json", "raw_collector.json", "collector_raw.json"}
)


@dataclass
class CleanupReport:
    workspace_id: str
    runs_purged: list[str] = field(default_factory=list)
    sensitive_files_removed: list[str] = field(default_factory=list)
    bytes_freed: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def total_runs_purged(self) -> int:
        return len(self.runs_purged)


def _dir_size(path: Path) -> int:
    """Return total bytes in a directory tree."""
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def _purge_sensitive_files(run_dir: Path, report: CleanupReport) -> None:
    """Remove any raw/sensitive files inside a run directory."""
    for fname in _SENSITIVE_FILENAMES:
        target = run_dir / fname
        if target.exists():
            try:
                target.unlink()
                report.sensitive_files_removed.append(str(target))
                _log.info("Purged sensitive file: %s", target)
            except OSError as exc:
                report.errors.append(f"Failed to remove {target}: {exc}")


def purge_expired_runs(
    workspace_id: str,
    *,
    dry_run: bool = False,
    retention_days: int | None = None,
) -> CleanupReport:
    """Delete runs older than the retention window for a workspace.

    Args:
        workspace_id: The workspace to clean up.
        dry_run: If True, report what would be deleted but don't actually delete.
        retention_days: Override the policy retention window (for testing).

    Returns:
        CleanupReport with details of what was (or would be) purged.
    """
    policy = load_policy(workspace_id)
    effective_days = retention_days if retention_days is not None else policy.retention_days
    cutoff = datetime.now(timezone.utc) - timedelta(days=effective_days)

    report = CleanupReport(workspace_id=workspace_id)
    runs_dir = CLIENTS_DIR / workspace_id / "runs"

    if not runs_dir.is_dir():
        _log.debug("No runs directory for workspace=%s", workspace_id)
        return report

    for run_dir in sorted(runs_dir.iterdir()):
        if not run_dir.is_dir():
            continue

        # Always strip sensitive files regardless of age
        _purge_sensitive_files(run_dir, report)

        # Determine run age from directory mtime
        try:
            mtime = datetime.fromtimestamp(run_dir.stat().st_mtime, tz=timezone.utc)
        except OSError:
            continue

        if mtime < cutoff:
            size = _dir_size(run_dir)
            if not dry_run:
                try:
                    shutil.rmtree(run_dir)
                    report.runs_purged.append(run_dir.name)
                    report.bytes_freed += size
                    _log.info("Purged expired run: %s (age=%s)", run_dir.name,
                              datetime.now(timezone.utc) - mtime)
                except OSError as exc:
                    report.errors.append(f"Failed to remove {run_dir}: {exc}")
            else:
                report.runs_purged.append(run_dir.name)
                report.bytes_freed += size
                _log.info("[DRY RUN] Would purge: %s", run_dir.name)

    _log.info(
        "Cleanup complete for workspace=%s: %d runs purged, %d bytes freed, dry_run=%s",
        workspace_id, report.total_runs_purged, report.bytes_freed, dry_run,
    )
    return report


def purge_all_workspaces(*, dry_run: bool = False) -> list[CleanupReport]:
    """Run purge_expired_runs across every workspace directory."""
    reports = []
    if not CLIENTS_DIR.is_dir():
        return reports
    for ws_dir in sorted(CLIENTS_DIR.iterdir()):
        if ws_dir.is_dir():
            reports.append(purge_expired_runs(ws_dir.name, dry_run=dry_run))
    return reports
