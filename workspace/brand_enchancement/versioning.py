"""brand_enchancement.versioning — Save and read versioned snapshots of BrandBibleDoc.

Each run that changes the brand bible saves a snapshot to:
  clients/<workspace>/brand_enchancement_versions/v{N}_{run_id}.json

The latest live copy is always at:
  clients/<workspace>/BrandBible.json

Listing and loading any past version is fully supported.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from brand_enchancement.schemas import BrandBibleDoc
from core.logging import get_logger

_log = get_logger(__name__)

_CLIENTS_ROOT = Path(__file__).resolve().parent.parent / "clients"
_VERSIONS_DIR = "brand_enchancement_versions"


# ── Public API ───────────────────────────────────────────────────────────────

def save_version(doc: BrandBibleDoc, workspace_id: str) -> Path:
    """Write a versioned snapshot and update the live BrandBible.json.

    Returns the path of the snapshot file.
    """
    client_dir = _ensure_client_dir(workspace_id)
    versions_dir = client_dir / _VERSIONS_DIR
    versions_dir.mkdir(parents=True, exist_ok=True)

    snapshot_name = f"v{doc.version}_{_safe(doc.run_id)}.json"
    snapshot_path = versions_dir / snapshot_name
    _write_json(snapshot_path, doc)

    live_path = client_dir / "BrandBible.json"
    _write_json(live_path, doc)

    _log.info(
        "brand_enchancement: saved v%d snapshot → %s",
        doc.version, snapshot_path.name,
    )
    return snapshot_path


def list_versions(workspace_id: str) -> list[dict]:
    """Return a list of version metadata dicts sorted newest-first.

    Each dict contains: version, run_id, updated_at, path.
    """
    versions_dir = _ensure_client_dir(workspace_id) / _VERSIONS_DIR
    if not versions_dir.exists():
        return []

    results = []
    for p in sorted(versions_dir.glob("v*.json"), reverse=True):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            results.append({
                "version": data.get("version"),
                "run_id": data.get("run_id", ""),
                "updated_at": data.get("updated_at", ""),
                "path": str(p),
            })
        except Exception:
            continue
    return results


def load_version(workspace_id: str, version: int) -> BrandBibleDoc | None:
    """Load a specific version by number. Returns None if not found."""
    versions_dir = _ensure_client_dir(workspace_id) / _VERSIONS_DIR
    if not versions_dir.exists():
        return None

    for p in versions_dir.glob(f"v{version}_*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            return BrandBibleDoc.model_validate(data)
        except Exception as exc:
            _log.warning("brand_enchancement: failed to load version %d: %s", version, exc)
            return None
    return None


def diff_summary(old: BrandBibleDoc, new: BrandBibleDoc) -> str:
    """Return a human-readable diff summary between two versions."""
    lines: list[str] = [
        f"Version {old.version} → {new.version}",
        f"Run: {new.run_id}  |  Updated: {new.updated_at}",
    ]
    new_kw = [k for k in new.keywords if k not in old.keywords]
    new_ht = [h for h in new.hashtags if h not in old.hashtags]
    if new_kw:
        lines.append(f"  + Keywords: {', '.join(new_kw)}")
    if new_ht:
        lines.append(f"  + Hashtags: {', '.join(new_ht)}")
    if new.change_log:
        last = new.change_log[-1]
        lines.append(f"  Fields updated: {', '.join(last.fields_updated) or 'none'}")
        lines.append(f"  Summary: {last.summary}")
    return "\n".join(lines)


# ── Internals ────────────────────────────────────────────────────────────────

def _ensure_client_dir(workspace_id: str) -> Path:
    d = _CLIENTS_ROOT / workspace_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _write_json(path: Path, doc: BrandBibleDoc) -> None:
    path.write_text(
        json.dumps(doc.model_dump(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _safe(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", text)[:40]
