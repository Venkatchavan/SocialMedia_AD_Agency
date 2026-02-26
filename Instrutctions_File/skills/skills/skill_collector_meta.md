# skill_collector_meta.md

## Purpose
Collect Meta Ads Library creative metadata from a brand Ad Library URL.

## Inputs
- meta_ad_library_url
- max ads
- date range (if supported)
- per-workspace storage target

## Outputs
- assets.json
- raw_refs.json

## Guardrails (Hard)
- No security bypass.
- Treat impressions as directional (often ranges).
- If impressions sorting/fields unavailable → continue with best available ordering + mark uncertainty.

## Validation Checks
- URL allowlist validation (Ad Library domains only)
- schema valid
- no secrets in logs