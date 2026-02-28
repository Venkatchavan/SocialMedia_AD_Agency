# skill_collector_tiktok.md

## Purpose
Collect TikTok assets (public data) for competitor research.

## Inputs
- keywords
- date range (if supported)
- max videos per keyword
- per-workspace storage target

## Outputs
- assets.json (list of Asset JSON records)
- raw_refs.json (collector logs + source refs)

## Guardrails (Hard)
- No bypassing login/CAPTCHA/anti-bot.
- Rate-limit and respect tool constraints.
- Store minimal fields only.
- Do not store usernames/handles.
- Comments are collected only as text blobs for immediate anonymized analysis; delete raw comment data after processing.

## Collector Output Rules
- Each asset must have stable asset_id.
- Include collected_at timestamp.
- If metrics missing → null.

## Validation Checks
- JSON schema valid
- asset_id uniqueness
- no PII fields present