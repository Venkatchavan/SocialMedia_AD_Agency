# QA_POLICY.md

## Blockers (FAIL)
- Any PII found (names/handles/faces) → FAIL
- Verbatim competitor copy (beyond short snippets) → FAIL
- Unsupported medical/financial claims → FAIL
- Cross-workspace leakage → FAIL
- Bypass instructions (CAPTCHA/auth/anti-bot) → FAIL

## Soft Warnings (WARN)
- insights not tied to evidence assets
- missing SMP/RTBs/mandatories
- missing testing matrix
- too much uncertainty without next actions

## Output
- pass|warn|fail
- violations[]
- fixes_required[]