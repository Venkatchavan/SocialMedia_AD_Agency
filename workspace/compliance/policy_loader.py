"""compliance.policy_loader — Per-client CompliancePolicy.yaml loader (§13).

Each client workspace may override global defaults by placing a
CompliancePolicy.yaml inside clients/<workspace_id>/.
The loader merges client overrides with the global baseline, always choosing
the stricter value (lower retention windows, larger risk flags, etc.).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

import yaml

from core.config import CLIENTS_DIR
from core.logging import get_logger

_log = get_logger(__name__)

# ── Global baseline (mirrors LEGAL_COMPLIANCE.md defaults) ──────────────────
_GLOBAL_BASELINE: dict[str, Any] = {
    "retention_days": 90,
    "max_assets_per_brand": 30,
    "allowed_platforms": ["tiktok", "meta", "x", "pinterest"],
    "prohibited_categories": [],
    "allowed_jurisdictions": [],          # empty = unrestricted
    "require_brand_bible": True,
    "require_competitors_file": True,
    "claim_checks_enabled": True,
    "pii_checks_enabled": True,
    "copy_similarity_enabled": True,
    "bypass_detection_enabled": True,
    "high_risk_flags": ["health", "finance", "minors", "politics"],
    "extra_blocklist_domains": [],
}


@dataclass
class CompliancePolicy:
    retention_days: int = 90
    max_assets_per_brand: int = 30
    allowed_platforms: list[str] = field(default_factory=lambda: ["tiktok", "meta", "x", "pinterest"])
    prohibited_categories: list[str] = field(default_factory=list)
    allowed_jurisdictions: list[str] = field(default_factory=list)
    require_brand_bible: bool = True
    require_competitors_file: bool = True
    claim_checks_enabled: bool = True
    pii_checks_enabled: bool = True
    copy_similarity_enabled: bool = True
    bypass_detection_enabled: bool = True
    high_risk_flags: list[str] = field(default_factory=lambda: ["health", "finance", "minors", "politics"])
    extra_blocklist_domains: list[str] = field(default_factory=list)


def _stricter_merge(baseline: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Merge override into baseline, choosing the stricter option."""
    merged: dict[str, Any] = dict(baseline)
    for key, override_val in override.items():
        if key not in merged:
            merged[key] = override_val
            continue
        base_val = merged[key]
        if isinstance(base_val, bool):
            # True (enabled) is stricter — enable if either says True
            merged[key] = base_val or override_val
        elif isinstance(base_val, int) and key == "retention_days":
            # shorter retention = stricter
            merged[key] = min(base_val, int(override_val))
        elif isinstance(base_val, int) and key == "max_assets_per_brand":
            # lower cap = stricter
            merged[key] = min(base_val, int(override_val))
        elif isinstance(base_val, list):
            # union of lists (more items = more restrictions)
            merged[key] = list(set(base_val) | set(override_val))
        else:
            merged[key] = override_val
    return merged


def load_policy(workspace_id: str) -> CompliancePolicy:
    """Load the effective CompliancePolicy for a workspace."""
    client_dir = CLIENTS_DIR / workspace_id
    policy_path = client_dir / "CompliancePolicy.yaml"

    merged = dict(_GLOBAL_BASELINE)

    if policy_path.exists():
        try:
            with open(policy_path, encoding="utf-8") as f:
                client_cfg: dict[str, Any] = yaml.safe_load(f) or {}
            merged = _stricter_merge(merged, client_cfg)
            _log.info("Loaded CompliancePolicy for workspace=%s", workspace_id)
        except Exception as exc:
            _log.warning("Failed to parse CompliancePolicy.yaml for %s: %s", workspace_id, exc)
    else:
        env_days = os.getenv("RETENTION_DAYS")
        if env_days:
            merged["retention_days"] = min(merged["retention_days"], int(env_days))
        _log.debug("No CompliancePolicy.yaml found for %s — using global baseline", workspace_id)

    return CompliancePolicy(**{k: v for k, v in merged.items() if k in CompliancePolicy.__dataclass_fields__})
