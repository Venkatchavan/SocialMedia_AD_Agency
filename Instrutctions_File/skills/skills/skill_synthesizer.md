# skill_synthesizer.md

## Purpose
Cluster winners, extract patterns, produce test hypotheses and playbooks.

## Inputs
- assets.json
- tags.json
- comment_themes.json (optional)
- recency window
- ranking proxy (impressions range / views)

## Outputs
- clusters.json
- insights.md
- aot_ledger.jsonl (atoms)

## AoT Requirements
- Create EVIDENCE atoms for top winners
- TAG atoms for recurring patterns
- HYPOTHESIS atoms for why pattern works
- DECISION atoms for what to recommend
- TEST atoms for how to validate

## Guardrails
- Every insight must cite asset IDs.
- If a “winner” is unclear, mark uncertainty.

## Validation
- evidence density: each insight references ≥1 asset_id
- AoT chain integrity: decision cites hypothesis; hypothesis cites evidence