AGENTIC RULES — LEGAL, SAFE, SECURE (NON-NEGOTIABLE)

1) Compliance Gate First
- No content can be rendered or published unless compliance_status = APPROVED.
- Compliance is deterministic and logged.

2) Rights-Scoped Reference Usage
- Every reference must be tagged with:
  reference_type = {licensed_direct, public_domain, style_only, commentary}
- Direct visual/audio reuse is allowed ONLY for licensed_direct or public_domain.
- style_only references may influence prompts but cannot include exact character names/logos/signature elements unless explicitly licensed.
- commentary references must follow platform/policy-safe usage and be logged.

3) No Illegal Automation
- Use official APIs or approved tools only.
- No browser automation to bypass platform restrictions.
- No scraping where prohibited by terms.
- No evasion of rate limits, captchas, or review systems.

4) Affiliate Transparency
- Every publishable caption must include clear affiliate disclosure.
- Disclosure checks are required per platform variant.
- No deceptive “organic recommendation” phrasing if affiliate links are present.

5) No Deceptive Marketing Claims
- No fake testimonials, fake scarcity, fake before/after, fake discounts.
- No unverifiable claims.
- No health/medical/financial claims unless product category and evidence pipeline explicitly support them.

6) Security by Default
- Agents never print secrets.
- Agents never store raw tokens in logs.
- All credentials come from secrets manager.
- Media URLs must be signed and time-limited.
- Only approved agents can access publish credentials.

7) Auditability
- Every decision must create an audit event:
  who/what agent, input hash, decision, timestamp, reason, output hash
- No silent rewrites.

8) Human Override (Controlled)
- Human can override REWRITE/REJECT only with explicit reason code.
- Overrides are logged and tied to account identity.

9) Anti-Spam / Anti-Repetition
- No duplicate content hash publishing on same platform.
- Similarity score threshold blocks near-duplicate spam.
- Posting cadence and quotas are enforced by platform adapter.

10) Fail Safe Behavior
- On rights uncertainty -> REWRITE or REJECT (never publish)
- On API auth failure -> queue and alert
- On policy reject -> stop retries, create incident
- On missing disclosure -> auto-rewrite caption only, then re-QA