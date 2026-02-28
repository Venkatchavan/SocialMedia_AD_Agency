"""qa.qa_gate — Orchestrate all QA checks; produce QAReport."""

from __future__ import annotations

from core.enums import QAResult, RiskLevel
from core.logging import get_logger
from core.schemas_brief import BriefObject
from core.schemas_qa import QAReport, QAViolation
from qa.claim_checks import check_claims
from qa.no_copy_checks import check_copy_overlap
from qa.pii_redaction import has_pii

_log = get_logger(__name__)


def run_qa_gate(
    brief: BriefObject,
    brief_md: str,
    competitor_texts: list[str] | None = None,
) -> QAReport:
    """Run all QA checks against a generated brief.

    Returns QAReport with result = pass | warn | fail.
    """
    violations: list[QAViolation] = []
    fixes: list[str] = []
    pii_found = False
    copy_risk = RiskLevel.LOW
    claim_risk = RiskLevel.LOW

    # 1. PII check
    if has_pii(brief_md):
        pii_found = True
        violations.append(QAViolation(
            rule="pii_check",
            severity="fail",
            detail="PII detected in brief output",
        ))
        fixes.append("Remove or redact all PII from brief")

    # 2. Copy overlap check
    if competitor_texts:
        gen_texts = [brief_md, brief.smp] + brief.hook_bank
        copy_risk, copy_flags = check_copy_overlap(gen_texts, competitor_texts)
        for f in copy_flags:
            violations.append(QAViolation(
                rule="no_copy",
                severity="fail" if copy_risk == RiskLevel.HIGH else "warn",
                detail=f,
            ))
        if copy_risk == RiskLevel.HIGH:
            fixes.append("Rewrite flagged sections to remove verbatim competitor copy")

    # 3. Claim risk check
    claim_risk, claim_flags = check_claims(brief_md)
    for f in claim_flags:
        violations.append(QAViolation(
            rule="claim_check",
            severity="fail" if claim_risk == RiskLevel.HIGH else "warn",
            detail=f,
        ))
    if claim_risk in (RiskLevel.MED, RiskLevel.HIGH):
        fixes.append("Substantiate or rephrase flagged claims; use 'UNKNOWN' if uncertain")

    # 4. Structural checks (soft warns)
    if not brief.smp or brief.smp.startswith("UNKNOWN"):
        violations.append(QAViolation(rule="smp_missing", severity="warn", detail="SMP is missing or unknown"))
    if len(brief.rtbs) < 3:
        violations.append(QAViolation(rule="rtbs_short", severity="warn", detail=f"Only {len(brief.rtbs)} RTBs (need 3+)"))
    if not brief.testing_matrix:
        violations.append(QAViolation(rule="matrix_missing", severity="warn", detail="Testing matrix is empty"))

    # Determine overall result
    result = _determine_result(violations, pii_found, copy_risk, claim_risk)

    report = QAReport(
        workspace_id=brief.workspace_id,
        run_id=brief.run_id,
        result=result,
        violations=violations,
        fixes_required=fixes,
        pii_found=pii_found,
        copy_risk=copy_risk,
        claim_risk=claim_risk,
    )
    _log.info("QA gate result: %s (%d violations)", result.value, len(violations))
    return report


def _determine_result(
    violations: list[QAViolation],
    pii_found: bool,
    copy_risk: RiskLevel,
    claim_risk: RiskLevel,
) -> QAResult:
    if pii_found:
        return QAResult.FAIL
    if copy_risk == RiskLevel.HIGH:
        return QAResult.FAIL
    if claim_risk == RiskLevel.HIGH:
        return QAResult.FAIL
    if any(v.severity == "fail" for v in violations):
        return QAResult.FAIL
    if violations:
        return QAResult.WARN
    return QAResult.PASS
