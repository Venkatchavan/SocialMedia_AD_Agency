# skill_collector_pinterest.md (Pinterest)

## Purpose
Add **Pinterest** into Creative Intelligence OS (collect → analyze → brief) in a scalable, compliant way.

This collector supports **two modes**:
1) **Pinterest Ads Library / Ads Repository (Transparency)** — collect public ads from Pinterest’s transparency repository (commonly EU-focused). Some community/industry guides note the Ads Library visibility is EU-only for certain views. :contentReference[oaicite:7]{index=7}  
2) **Organic Pin Intelligence** — collect top Pins/boards for competitor domains/accounts (trend/creative direction support) when ads data is limited.

> Important: Pinterest’s official Ads/Marketing APIs are primarily for **advertisers managing their own campaigns**, not competitor scraping. :contentReference[oaicite:8]{index=8}  
For competitor intel, use the transparency repository or approved third-party collectors (authorized). :contentReference[oaicite:9]{index=9}

---

## Inputs
### Common
- workspace_id
- brand (string)
- mode: `ads_repository | organic_pins`
- date_range: `{start: YYYY-MM-DD, end: YYYY-MM-DD}`
- max_assets: integer

### Mode: ads_repository
- filters (optional):
  - country (ISO)
  - category
  - advertiser_name (string)
  - gender/age filters (only if available via repository interface)
- source: `manual_export | approved_collector`
  - **manual_export**: operator exports results and uploads
  - **approved_collector**: a compliant tool/service that returns structured results (example: an Apify actor that states it extracts ads from Pinterest’s Ad Library/Repository). :contentReference[oaicite:10]{index=10}

### Mode: organic_pins
- competitor_domain OR competitor_account
- keywords (optional)
- include_idea_pins: boolean
- include_video_pins: boolean

---

## Outputs
### Required
- `assets.json`
- `raw_refs.json`

### Asset JSON Mapping Notes (Pinterest)
- `platform`: `"pinterest"`
- `ad_url`: repository ad detail URL OR pin URL
- `media_url`: best-effort link to creative (image/video); else null
- `caption_or_copy`: pin title/description OR ad text fields if present
- `headline` / `cta`: if repository provides them; else null
- `metrics`:
  - repository may provide reach/impression-like ranges depending on jurisdiction/data availability
  - organic: repin/save counts if available (else null)

---

## Scaling & Reliability (Non-negotiable)
### Incremental refresh
- Keep per brand/workspace:
  - `last_run_at`
  - `last_seen_asset_ids`
- Collect only new/changed ads within date_range where possible.
- Weekly refresh is default; daily only if budgets allow.

### Deduplication
- stable `asset_id` rules:
  - repository: `pinterest:adsrepo:<advertiser>:<ad_id>`
  - organic pins: `pinterest:pin:<pin_id>`

### Work queue architecture
- Shard by `workspace_id` and `brand`
- Limit concurrency per domain to avoid hammering endpoints
- Hard timeouts + partial result returns

---

## Guardrails (Hard Rules)
1) No bypass instructions (CAPTCHA/auth/anti-bot).
2) Data minimization: never store personal identifiers (commenters/creators).
3) Client isolation: no cross-workspace mixing.
4) Evidence provenance: every asset must have traceable source in `raw_refs`.
5) Engineering rule: **no single code file/module/script > 250 lines**.

---

## Failure Modes & Graceful Degradation
- If Ads Library is region-limited / empty for your filters, record uncertainty and fall back to **organic pins** mode for creative direction signals. EU-only visibility is commonly reported for the Ads Library in some guides. :contentReference[oaicite:11]{index=11}
- If creative media isn’t accessible, store thumbnail only and continue.

---

## Validation Checks
- JSON schema valid (SCHEMA.md)
- asset_id uniqueness
- URL allowlist validation (Pinterest domains only)
- budget compliance: `len(assets) <= max_assets`
- PII scan: ensure no personal identifiers stored

---

## Recommended CrewAI Wiring
- Collector → `assets.json`
- Media Analyzer → `tags.json` (format/hook/angle/offer/CTA)
- Synthesizer → clusters + insights + AoT ledger
- Brief Writer → brief outputs (template + brand bible)
- QA Gate → blocks export on FAIL

---

## Notes on Available Data
- Pinterest offers official APIs for advertisers to manage and measure **their own** ads (campaign management + analytics). :contentReference[oaicite:12]{index=12}
- For competitor intel, use the public transparency repository workflow or an approved collector that states it extracts ads from the repository with filters (country/category/date range). :contentReference[oaicite:13]{index=13}
- Some industry guides note Ads Library visibility can be EU-only for certain views. :contentReference[oaicite:14]{index=14}