"""briefs.template_loader — Load BrandBible + BriefTemplate from workspace."""

from __future__ import annotations


from core.config import workspace_path
from core.logging import get_logger

_log = get_logger(__name__)

_BRAND_FILE = "Brand_Book.md"
_BRIEF_FILE = "BriefTemplate.md"
_COMPLIANCE_FILE = "CompliancePolicy.md"
_COMPETITORS_FILE = "Competitors.yml"


def load_brand_bible(workspace_id: str) -> str:
    """Return the raw markdown of the brand bible for a workspace."""
    return _read_file(workspace_id, _BRAND_FILE)


def load_brief_template(workspace_id: str) -> str:
    """Return the raw markdown of the brief template."""
    return _read_file(workspace_id, _BRIEF_FILE)


def load_compliance_policy(workspace_id: str) -> str:
    """Return the compliance policy markdown (may be empty)."""
    return _read_file(workspace_id, _COMPLIANCE_FILE)


def load_competitors_yml(workspace_id: str) -> str:
    """Return raw YAML string for competitors config."""
    return _read_file(workspace_id, _COMPETITORS_FILE)


def _read_file(workspace_id: str, filename: str) -> str:
    fp = workspace_path(workspace_id) / filename
    if not fp.exists():
        _log.warning("File not found: %s", fp)
        return ""
    return fp.read_text(encoding="utf-8")
