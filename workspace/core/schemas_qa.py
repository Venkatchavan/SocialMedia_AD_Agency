"""core.schemas_qa — Pydantic models for QA gate reports."""

from __future__ import annotations

from pydantic import BaseModel, Field

from core.enums import QAResult, RiskLevel


class QAViolation(BaseModel):
    rule: str
    severity: str  # "fail" | "warn"
    detail: str
    asset_ids: list[str] = Field(default_factory=list)


class QAReport(BaseModel):
    workspace_id: str
    run_id: str
    result: QAResult = QAResult.PASS
    violations: list[QAViolation] = Field(default_factory=list)
    fixes_required: list[str] = Field(default_factory=list)
    pii_found: bool = False
    copy_risk: RiskLevel = RiskLevel.LOW
    claim_risk: RiskLevel = RiskLevel.LOW
