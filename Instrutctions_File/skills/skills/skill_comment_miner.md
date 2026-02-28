# skill_comment_miner.md

## Purpose
Extract anonymized themes from comments (FAQs, objections, desire language).

## Inputs
- comments text array
- asset_id
- anonymization policy

## Outputs
- comment_themes.json
{
  "asset_id": "...",
  "top_questions": ["..."],
  "repeated_objections": ["..."],
  "desire_language": ["rewritten phrases only"],
  "confusion_points": ["..."],
  "suggested_angles_to_test": ["..."],
  "pii_detected": false
}

## Guardrails (Hard)
- Do not output usernames/handles.
- Do not quote verbatim long comments.
- Rewrite phrases; keep meaning.

## Validation
- PII scan must pass
- JSON schema valid