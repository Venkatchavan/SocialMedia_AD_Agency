# skill_qa_gate.md

## Purpose
Block risky output and enforce compliance.

## Inputs
- brief.md + brief.json
- assets.json + tags.json
- compliance policy

## Outputs
- qa_report.md + qa_report.json
{
  "result": "pass|warn|fail",
  "violations": [],
  "fixes_required": [],
  "pii_found": false,
  "copy_risk": "low|med|high",
  "claim_risk": "low|med|high"
}

## Hard FAIL Conditions
- PII present
- competitor copy replication
- unsupported medical/financial claims
- cross-workspace contamination
- bypass instructions

## Validation
- run redaction if needed
- re-check until pass/warn