
---

## `BRAIN.md`
```md
# BRAIN.md

## Working Memory (Per Run)
- workspace_id
- scope: {platforms, date_range, max_assets_per_brand}
- collector_status
- counts: {assets_loaded, analyzed, failed}
- open_questions
- decisions_made
- risk_flags

## AoT Ledger (Atom of Thought)
We reason with auditable atoms (no hidden chain-of-thought).

### Atom Types
- EVIDENCE: observed facts (asset ids, metrics, timestamps)
- TAG: structured labels (hook/angle/offer/format)
- HYPOTHESIS: falsifiable explanation (short)
- DECISION: recommendation for brief
- TEST: measurable validation plan

### Atom Format (JSONL recommended)
{
  "atom_id": "uuid",
  "type": "EVIDENCE|TAG|HYPOTHESIS|DECISION|TEST",
  "source_assets": ["asset_id1","asset_id2"],
  "content": "1-3 sentences",
  "confidence": "low|med|high",
  "next_check": "what data would increase confidence"
}

## Output Rule
Only output AoT atoms + summaries. Never output internal chain-of-thought.