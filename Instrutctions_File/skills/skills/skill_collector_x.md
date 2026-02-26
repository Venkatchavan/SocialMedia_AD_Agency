# skill_collector_x.md (X)

## Purpose
Add **X** into the same Creative Intelligence OS pipeline (collect → analyze → brief) in a scalable, compliant way.

This collector supports **two modes**:
1) **X Ads Repository (EU / DSA)** — collect *ads served in the EU* via X’s Ads Transparency Center workflow (CSV export / API where available). :contentReference[oaicite:0]{index=0}  
2) **Organic Creative Intelligence** — collect top public posts from a brand account (or keyword search) and treat them as “creative assets” when ads data is unavailable.

> Reality: X provides an **EU Ads Repository** under the DSA with advertiser + targeting parameters + impression/reach fields and CSV export; it is not the same as Meta’s universal ad library. :contentReference[oaicite:1]{index=1}

---

## Inputs
### Common
- workspace_id
- brand (string)
- mode: `ads_repository_eu | organic_posts`
- date_range: `{start: YYYY-MM-DD, end: YYYY-MM-DD}`
- max_assets: integer
- country: ISO code (required for ads_repository_eu)

### Mode: ads_repository_eu
- advertiser_account_handle (string)
- country (EU country filter)
- date_range
- csv_source: `manual_upload | api_download`  
  - **manual_upload**: operator downloads CSV from X Ads Repository UI and uploads it
  - **api_download**: only if your org has a supported programmatic method (must be compliant)

X states the repository can be accessed via UI or API, generating a CSV per advertiser/country/date-range query. :contentReference[oaicite:2]{index=2}

### Mode: organic_posts
- brand_handle OR user_id
- query (optional) for keyword-based collection
- include_replies: boolean (default false)

Organic collection uses X API v2 (or an approved data provider). X API v2 supports modern JSON and metrics; pricing/limits vary. :contentReference[oaicite:3]{index=3}

---

## Outputs
### Required
- `assets.json` (list of Asset JSON objects from SCHEMA.md)
- `raw_refs.json` (collector provenance, run metadata, source pointers)

### Asset JSON Mapping Notes (X)
- `platform`: `"x"`
- `ad_url`: link to ad record (ads repo) OR post URL (organic)
- `media_url`: best-effort (image/video URL if publicly accessible); else null
- `caption_or_copy`: ad copy if present; else post text
- `metrics`:
  - `impressions_range`: from Ads Repository if present (directional)
  - organic: public metrics (likes/reposts/replies) if available

---

## Scaling & Reliability (Non-negotiable)
### Bounded collection
- Never exceed `max_assets` per run.
- Prefer **incremental refresh**:
  - store `last_collected_at` per brand/workspace
  - collect only new/changed items since last run where possible

### Deduplication
- stable `asset_id` rules:
  - Ads repository: `x:adsrepo:<advertiser>:<ad_id>`
  - Organic posts: `x:post:<post_id>`

### Concurrency control
- Use a queue + workers (per-workspace sharding).
- Hard timeouts per collection job.
- Rate-limit requests; fail gracefully and return partial results.

---

## Guardrails (Hard Rules)
1) **No bypass instructions**: do not automate CAPTCHA/auth bypass or anti-bot evasion.
2) **Data minimization**:
   - do not store usernames/handles from commenters
   - do not store personal identifiers
3) **Client isolation**: never mix outputs across workspaces.
4) **Evidence provenance**: every asset must include `raw_refs` link back to source.
5) **Engineering rule**: **no single code file/module/script > 250 lines** (split into modules).

---

## Failure Modes & Graceful Degradation
- If Ads Repository returns blank/no ads for period: mark `uncertainties += ["No EU ads found for advertiser/country/date range"]` and optionally fall back to organic mode. X explicitly notes blank CSV may indicate no ads served. :contentReference[oaicite:4]{index=4}
- If media URLs aren’t accessible: store thumbnails only; analysis still runs on whatever is accessible.

---

## Validation Checks
- JSON schema validity (SCHEMA.md)
- asset_id uniqueness
- URL allowlist checks for repository/post URLs
- PII scan: ensure no personal identifiers are stored
- run budget compliance: `len(assets) <= max_assets`

---

## Recommended CrewAI Wiring
- Collector: returns `assets.json`
- Media Analyzer: tags creative (format/hook/angle/offer/CTA)
- Synthesizer: clusters winners by distribution proxy + recency
- Brief Writer: uses template + brand bible + insights
- QA Gate: blocks export on policy violations

---

## Notes on Available Data
- X provides an EU Ads Repository (DSA) containing advertiser, targeting parameters, impression and reach fields, accessible via UI/API producing CSV. :contentReference[oaicite:5]{index=5}
- X API v2 exists for public posts and metrics; pricing/limits vary by plan. :contentReference[oaicite:6]{index=6}