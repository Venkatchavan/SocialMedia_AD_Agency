# skill_brief_writer.md

## Purpose
Generate a client-ready brief using BriefTemplate + BrandBible + Insights.

## Inputs
- BrandBible.md
- BriefTemplate.md
- insights.md + clusters.json
- constraints: mandatories, compliance policy

## Outputs
- brief.md (human)
- brief.json (structured)

## Brief Rules
- 1-page core, append research as needed
- Exactly one SMP
- Include RTBs, mandatories, testing matrix
- Produce 2–4 directions, 10–20 hooks, 3–6 scripts

## Guardrails
- Original creative only (no competitor copy).
- No unsafe claims.
- Unknowns explicitly labeled.

## Validation
- required sections present
- SMP present exactly once
- test matrix present