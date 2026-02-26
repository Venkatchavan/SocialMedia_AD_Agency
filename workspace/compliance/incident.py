"""compliance.incident — Incident response handler (§14).

Triggered when PII leakage, unauthorized collection method, or exported
competitor content is detected. Orchestrates: stop → purge → note → patch.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from core.config import CLIENTS_DIR, DATA_DIR
from core.logging import get_logger

_log = get_logger(__name__)


class IncidentType(str, Enum):
    PII_LEAKED = "pii_leaked"
    UNAUTHORIZED_COLLECTION = "unauthorized_collection"
    COMPETITOR_COPY_EXPORTED = "competitor_copy_exported"
    BYPASS_INSTRUCTION_DETECTED = "bypass_instruction_detected"
    CROSS_WORKSPACE_CONTAMINATION = "cross_workspace_contamination"
    OTHER = "other"


@dataclass
class Incident:
    run_id: str
    workspace_id: str
    incident_type: IncidentType
    description: str
    detected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    actions_taken: list[str] = field(default_factory=list)
    data_purged: list[str] = field(default_factory=list)
    key_rotation_required: bool = False
    resolved: bool = False


# Files to purge immediately on incident
_PURGE_ON_INCIDENT: frozenset[str] = frozenset(
    {"raw_comments.json", "comments.json", "raw_collector.json", "collector_raw.json", "tags.json"}
)


def _write_incident_note(run_dir: Path, incident: Incident) -> None:
    """Append an incident note to phase_notes.md inside the run directory."""
    notes_path = run_dir / "phase_notes.md"
    ts = incident.detected_at
    lines = [
        f"\n\n---\n### ⚠️ INCIDENT NOTE — {ts}",
        f"**Type**: {incident.incident_type.value}",
        f"**Description**: {incident.description}",
        "**Actions taken**:",
    ]
    for action in incident.actions_taken:
        lines.append(f"  - {action}")
    if incident.key_rotation_required:
        lines.append("**⚠️ KEY ROTATION REQUIRED** — rotate all API keys in this workspace.")
    lines.append("---\n")

    with open(notes_path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines))

    _log.warning("Incident note written to %s", notes_path)


def _purge_run_data(run_dir: Path, incident: Incident) -> None:
    """Remove sensitive files from the affected run directory."""
    for fname in _PURGE_ON_INCIDENT:
        target = run_dir / fname
        if target.exists():
            try:
                target.unlink()
                incident.data_purged.append(str(target))
                _log.warning("Incident purge: removed %s", target)
            except OSError as exc:
                _log.error("Failed to purge %s: %s", target, exc)


def _write_global_incident_log(incident: Incident) -> None:
    """Append a summary line to the global incident log."""
    log_dir = DATA_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "incident_log.jsonl"
    import json
    entry = {
        "detected_at": incident.detected_at,
        "workspace_id": incident.workspace_id,
        "run_id": incident.run_id,
        "type": incident.incident_type.value,
        "description": incident.description,
        "data_purged": incident.data_purged,
        "key_rotation_required": incident.key_rotation_required,
        "resolved": incident.resolved,
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    _log.warning("Incident logged to %s", log_path)


def trigger_incident(
    run_id: str,
    workspace_id: str,
    incident_type: IncidentType | str,
    description: str,
    *,
    purge_run: bool = True,
    key_rotation_required: bool = False,
) -> Incident:
    """Trigger the incident response workflow.

    Steps (§14):
    1. Stop — log immediately (scheduler is not called here; caller must stop it).
    2. Purge — remove sensitive files from the affected run.
    3. Note — write incident note to phase_notes.md.
    4. Log — append to global incident log.
    5. Patch hint — note key rotation requirement.

    Args:
        run_id: The affected pipeline run.
        workspace_id: The affected workspace.
        incident_type: Type of incident (IncidentType enum or string).
        description: Human-readable description.
        purge_run: If True, delete sensitive files from the run directory.
        key_rotation_required: If True, flag that API keys should be rotated.

    Returns:
        Incident dataclass with full details.
    """
    if isinstance(incident_type, str):
        incident_type = IncidentType(incident_type) if incident_type in IncidentType._value2member_map_ else IncidentType.OTHER

    incident = Incident(
        run_id=run_id,
        workspace_id=workspace_id,
        incident_type=incident_type,
        description=description,
        key_rotation_required=key_rotation_required,
    )

    _log.error(
        "INCIDENT [%s] workspace=%s run=%s: %s",
        incident.incident_type.value, workspace_id, run_id, description,
    )

    run_dir = CLIENTS_DIR / workspace_id / "runs" / run_id

    # Step 2: Purge sensitive files
    if purge_run and run_dir.is_dir():
        _purge_run_data(run_dir, incident)
        incident.actions_taken.append(f"Purged {len(incident.data_purged)} sensitive file(s) from {run_id}")

    # Step 3: Write incident note
    if run_dir.is_dir():
        _write_incident_note(run_dir, incident)
        incident.actions_taken.append("Incident note appended to phase_notes.md")

    # Step 4: Global log
    _write_global_incident_log(incident)
    incident.actions_taken.append("Entry appended to data/incident_log.jsonl")

    # Step 5: Key rotation hint
    if key_rotation_required:
        incident.actions_taken.append(
            "ACTION REQUIRED: Rotate all API keys referenced in .env for this workspace"
        )

    return incident
