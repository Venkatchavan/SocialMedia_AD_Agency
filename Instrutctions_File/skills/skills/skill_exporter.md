# skill_exporter.md

## Purpose
Export artifacts for humans and systems.

## Inputs
- brief.md
- brief.json
- tags.json
- qa_report.json

## Outputs
- packaged_run.zip (optional)
- final exports:
  - markdown
  - json bundle
  - pdf/doc/notion (optional)

## Guardrails
- Do not export if QA FAIL.
- Strip any remaining sensitive fields.

## Validation
- verify QA pass/warn
- checksum bundle