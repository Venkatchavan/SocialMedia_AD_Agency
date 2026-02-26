"""compliance.preflight — Operator pre-run checklist gate (§11).

Validates that a workspace is properly configured before the pipeline starts.
Hard blockers raise PreflightError; soft warnings are returned as strings.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.config import CLIENTS_DIR
from core.logging import get_logger
from compliance.policy_loader import load_policy, CompliancePolicy

_log = get_logger(__name__)

_REQUIRED_FILES = {
    "Brand_Book.md": "required_brand_bible → Brand_Book.md missing",
    "Competitors.yaml": "required_competitors_file → Competitors.yaml missing (also accepts .yml)",
}
_COMPETITORS_ALT = "Competitors.yml"


class PreflightError(RuntimeError):
    """Raised when a hard preflight blocker is found."""


@dataclass
class PreflightReport:
    workspace_id: str
    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    policy: CompliancePolicy | None = None

    def summary(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        lines = [f"Preflight {status} for workspace={self.workspace_id}"]
        for e in self.errors:
            lines.append(f"  [ERROR] {e}")
        for w in self.warnings:
            lines.append(f"  [WARN]  {w}")
        return "\n".join(lines)


def run_preflight(workspace_id: str, *, raise_on_error: bool = True) -> PreflightReport:
    """Run all preflight checks for a workspace.

    Args:
        workspace_id: The workspace to validate.
        raise_on_error: If True, raises PreflightError on hard failures.

    Returns:
        PreflightReport with pass/fail status, errors, and warnings.
    """
    policy = load_policy(workspace_id)
    client_dir = CLIENTS_DIR / workspace_id
    errors: list[str] = []
    warnings: list[str] = []

    # ── 1) Workspace directory exists ────────────────────────────────────────
    if not client_dir.is_dir():
        errors.append(f"Workspace directory not found: {client_dir}")

    # ── 2) Brand_Book.md ─────────────────────────────────────────────────────
    if policy.require_brand_bible:
        if not (client_dir / "Brand_Book.md").exists():
            alt_paths = ["BrandBible.json", "BrandBible.yaml", "brand_bible.md"]
            if not any((client_dir / p).exists() for p in alt_paths):
                warnings.append("Brand_Book.md not found — brief will use defaults")

    # ── 3) Competitors file ──────────────────────────────────────────────────
    if policy.require_competitors_file:
        has_competitors = (
            (client_dir / "Competitors.yaml").exists()
            or (client_dir / "Competitors.yml").exists()
        )
        if not has_competitors:
            warnings.append("Competitors.yaml not found — competitor analysis will be skipped")

    # ── 4) CompliancePolicy.yaml recommended ─────────────────────────────────
    if not (client_dir / "CompliancePolicy.yaml").exists():
        warnings.append(
            "No CompliancePolicy.yaml found — using global baseline. "
            "Create one to tighten per-client rules."
        )

    # ── 5) Prohibited categories check ──────────────────────────────────────
    if policy.prohibited_categories:
        warnings.append(
            f"Prohibited categories active: {policy.prohibited_categories} — "
            "QA will block any brief mentioning these topics."
        )

    # ── 6) Retention settings surface ────────────────────────────────────────
    if policy.retention_days < 7:
        errors.append(
            f"retention_days={policy.retention_days} is dangerously low. Minimum is 7."
        )

    # ── 7) High-risk flag awareness ──────────────────────────────────────────
    for flag in policy.high_risk_flags:
        if flag in ("health", "finance", "minors", "politics"):
            warnings.append(
                f"High-risk category '{flag}' is flagged — extra claim checks will run."
            )

    passed = len(errors) == 0
    report = PreflightReport(
        workspace_id=workspace_id,
        passed=passed,
        errors=errors,
        warnings=warnings,
        policy=policy,
    )

    _log.info("Preflight %s for workspace=%s (%d errors, %d warnings)",
              "PASS" if passed else "FAIL", workspace_id, len(errors), len(warnings))

    if not passed and raise_on_error:
        raise PreflightError(report.summary())

    return report
