# LEGAL_COMPLIANCE.md
**Creative Intelligence OS — Legal + Security + Agentic Compliance Policy (Global Baseline)**  
Version: 1.0  
Scope: Meta + TikTok + X + Pinterest collectors, analyzers, synthesis, brief generation, exports

> This document is a **risk control baseline**, not legal advice. Laws and platform rules vary by country and change frequently. Treat this as a minimum standard; tighten it per jurisdiction and client.

---

## 1) Purpose
This project handles **competitor intelligence** and **ad/creative analysis**. That area can become illegal or contract-breaching if you:
- bypass platform security,
- scrape restricted content,
- store personal data,
- reproduce copyrighted creative,
- violate platform Terms,
- or misrepresent data in client deliverables.

This policy enforces:
- **legal compliance**, **privacy**, **security**, and **ethical** boundaries
- **safe-by-default** execution and data retention
- **auditability** (evidence-first, provenance logs)

---

## 2) Definitions (tight)
- **Public data**: Content accessible without login or special permissions, in compliance with platform rules and your access method.
- **Authorized collector**: A tool/API you’re permitted to use (official APIs, paid datasets, vendor agreements, or manual exports).
- **Personal data / PII**: Any data identifying a person directly or indirectly (handles, usernames, faces, emails, phone numbers, unique IDs, exact quotes linked to a person).
- **Competitor creative**: Ads, posts, videos, images, captions, and comments published by other entities.
- **Derived insights**: Aggregations, tags, summaries, hypotheses, test plans (not raw data).

---

## 3) Global “Hard Stop” Rules (MUST)
If any rule below is violated, the system must **FAIL** the run (QA FAIL) and **block export**.

### 3.1 No security bypass
- No instructions/code for bypassing:
  - CAPTCHAs
  - login walls
  - anti-bot protections
  - rate-limit evasion
  - fingerprint spoofing / stealth browser methods for protected endpoints
- Only use **official APIs**, **authorized vendors** (e.g., Apify actors used under proper authorization), or **manual exports**.

### 3.2 No PII retention/output
- Do not store or export:
  - usernames/handles of commenters/creators
  - faces or biometric identifiers
  - contact details
  - persistent personal IDs
  - long verbatim comment quotes linked to individuals
- Comments may be processed in-memory for **theme extraction**, then discarded. Persist only **anonymized themes**.

### 3.3 No competitor-copy replication
- Do not output competitor ad copy/captions verbatim.
- Do not output “scripts” that are near-duplicates of competitor scripts.
- Allowed: short paraphrased summaries; short snippets only when required for evidence (keep extremely minimal).

### 3.4 Client isolation
- All data must be scoped to `workspace_id`.
- No mixing competitor assets, insights, or briefs across client workspaces.

### 3.5 Truthfulness in reporting
- Do not present impression/view metrics as exact if they are ranges or incomplete.
- Always label uncertainty:
  - “Directional” / “Range-based” / “Unavailable”
- Never invent metrics.

---

## 4) Platform Compliance (Minimum Baseline)
> Platform policies differ; when uncertain, default to **manual export** or **official API**.

### 4.1 Meta
- Prefer official Ad Library/API coverage where applicable.
- If using a third-party collector, it must be authorized by your org and comply with platform rules.
- Treat impressions as **directional** (often ranges/limited fields).

### 4.2 TikTok
- Prefer authorized collection services or official/partner routes.
- Avoid any method that requires bypassing protections.

### 4.3 X (Twitter)
- Prefer **manual CSV export** from transparency repositories where applicable (e.g., EU/DSA context).
- For organic post analysis, use official API access or compliant provider.
- No scraping behind login or protected endpoints.

### 4.4 Pinterest
- Prefer repository/transparency collection where available or compliant provider tooling.
- Pinterest official APIs are primarily for advertisers managing their own campaigns; do not misuse.

---

## 5) Jurisdiction Risk Matrix (Practical)
Because laws vary, we enforce a strict baseline.

### 5.1 High-risk jurisdictions/scenarios
- Any region with strong privacy/data regulations (e.g., EU/UK) where personal data processing triggers GDPR/UK GDPR obligations.
- Any country where automated data collection is restricted by local law or litigation trends.
- Any case involving minors, health, finance, politics → **extra hard checks**.

### 5.2 Your default stance
- Treat all user-generated comments as **personal data**.
- Store **only aggregated themes** and delete raw comments immediately.

---

## 6) Data Handling & Retention Policy
### 6.1 What may be stored
- Asset identifiers (asset_id), platform, timestamps, public URLs
- Creative metadata (headline/copy/CTA where publicly accessible)
- Derived tags (format/hook/angle/offer/CTA)
- Aggregated comment themes (no identifiers)
- AoT ledger atoms (no PII)

### 6.2 What must NOT be stored
- Raw comments
- Commenter handles/usernames
- Faces/biometrics
- Private or gated content
- Session cookies, auth tokens in logs

### 6.3 Retention
- Raw collector logs: keep minimal, strip tokens, keep only for debugging.
- Assets/tags: retain per client policy (default 30–90 days).
- Anonymized themes: retain per client policy.
- Add an automated cleanup job.

---

## 7) Security Controls (Required)
### 7.1 Secrets management
- API keys only in environment variables / secrets manager.
- Never print secrets in logs.
- Rotate keys periodically.

### 7.2 SSRF + URL validation
- Allowlist domains for collectors.
- Reject:
  - localhost / private IP ranges
  - file://, ftp:// schemes
  - untrusted redirects
- Store normalized URLs.

### 7.3 Rate limiting + safe retries
- Rate limit all collectors.
- Use bounded retries with exponential backoff.
- Stop if error rate exceeds threshold.

### 7.4 Auditability
- Every run must produce:
  - provenance refs (source URLs, timestamps)
  - a run log
  - phase_notes.md

---

## 8) Agentic Rules (Compliance by Design)
### 8.1 Agent permissions
- Collectors: read-only, bounded, allowlist-only.
- Analyzers: can process media, but must not extract/store PII.
- Synthesis + Brief: can write creative, but must not copy competitors.
- QA Gate: blocking authority. If it FAILs, export is blocked.

### 8.2 Mandatory QA checks (blockers)
- PII detection (names/handles/unique identifiers)
- No-copy similarity detection vs competitor copy/captions
- Claim risk checks:
  - medical claims
  - financial claims
  - unsafe promises
- Cross-workspace contamination
- “Bypass instruction” detection

### 8.3 Evidence-first output
- insights.md must reference `asset_id` for each claim.
- AoT atoms must link evidence → hypothesis → decision → test.

---

## 9) Copyright & Creative Safety
- Competitor creatives are copyrighted (varies by jurisdiction).
- This tool must produce:
  - **original** hooks/scripts/angles
  - “inspired by patterns”, not copied phrasing
- Avoid using competitor brand names inside generated scripts unless required for comparison notes.

---

## 10) Allowed vs Forbidden Use Cases
### Allowed
- Competitive research using public data via authorized methods
- Pattern extraction (angles, offers, hooks)
- Generating original briefs and test matrices

### Forbidden
- Building a database of identifiable user comments/identities
- Publishing competitor creatives as your own
- Attempting to circumvent platform protections
- Harassment, surveillance, targeted profiling of individuals

---

## 11) Operator Checklist (Before Running)
1) Workspace files exist: BrandBible, BriefTemplate, CompliancePolicy, Competitors.yml
2) Approved collector methods selected (API/vendor/manual)
3) Budgets set (max assets, max analysis seconds)
4) Retention settings configured
5) QA Gate enabled (cannot be disabled)

---

## 12) Enforcement (Technical)
- QA FAIL blocks export.
- Scheduler must stop if violations occur repeatedly.
- Any code changes must keep files <250 lines and update docs.

---

## 13) Per-Client CompliancePolicy.md (Override Layer)
Each client workspace may tighten:
- allowed jurisdictions
- retention windows
- prohibited categories (health/finance)
- claim constraints
- brand safety rules

Default: If client policy conflicts with this global baseline, choose the **stricter** rule.

---

## 14) Incident Response (Minimal)
If you detect:
- PII stored accidentally
- unauthorized collection method used
- export with copied competitor content

Then:
1) Stop scheduler
2) Purge affected data
3) Rotate keys if exposure possible
4) Write incident note in runs/<run_id>/phase_notes.md
5) Patch QA checks to prevent recurrence

---