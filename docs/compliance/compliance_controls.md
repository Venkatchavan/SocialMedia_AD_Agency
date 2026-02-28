# Compliance Controls

## 1. Compliance Gate

**Rule**: No content can be rendered or published unless `compliance_status = APPROVED`.

### Implementation

| Component | Enforcement Point | Behavior |
|-----------|------------------|----------|
| `RightsEngine.verify()` | Before content generation | Returns APPROVED / REWRITE / REJECT |
| `QAChecker.check()` | Before publishing | Validates compliance, disclosure, quality |
| `ContentPipelineFlow._step_rights_check()` | Pipeline step 4 (in `pipeline_steps.py`) | Blocks pipeline on REJECT |
| `ContentPipelineFlow._step_qa()` | Pipeline step 6 (in `pipeline_steps.py`) | Blocks publish on REJECT |
| `ManagerAgent._review_content()` | Pipeline step 5b (LLM quality gate, P6) | Blocks on low quality score |
| `OrchestratorAgent._route_rights_decision()` | Decision routing | Enforces max rewrite loops |

### Fail-Safe Behavior

- Rights uncertainty → REWRITE or REJECT (never publish)
- API auth failure → queue and alert
- Policy reject → stop retries, create incident
- Missing disclosure → auto-rewrite caption, then re-QA

## 2. Affiliate Disclosure

**Rule**: Every publishable caption MUST include clear affiliate disclosure.

### Per-Platform Requirements

| Platform | Required Markers | Auto-Fix |
|----------|-----------------|----------|
| TikTok | `#ad` or `#affiliate` or `#sponsored` | ✅ `add_disclosure()` |
| Instagram | `#ad` or `#affiliate` or `#sponsored` | ✅ `add_disclosure()` |
| X | `#ad` or `#affiliate` | ✅ `add_disclosure()` |
| Pinterest | `#ad` or `#affiliate` or `#sponsored` | ✅ `add_disclosure()` |

### Enforcement Chain

1. `CaptionSEOAgent` generates captions with disclosure templates
2. `validate_disclosure()` checks each caption per platform
3. If missing → `add_disclosure()` auto-adds (not rejected)
4. `CaptionBundle.verify_all_disclosures()` final verification
5. `QAChecker` re-validates before publish clearance

### Deceptive Language Detection

Blocked patterns:
- "just happened to find"
- "organically discovered"
- "not sponsored but"
- "honest review" (without disclosure)

## 3. Rights & Licensing

### Reference Types

| Type | Direct Visual Use | Style Influence | Required Proof |
|------|-------------------|-----------------|----------------|
| `licensed_direct` | ✅ | ✅ | `license_id` + valid expiry |
| `public_domain` | ✅ | ✅ | Pre-1928 or explicit PD status |
| `style_only` | ❌ | ✅ | No character names/logos/signature elements |
| `commentary` | ❌ | ✅ (limited) | Platform/policy-safe usage, logged |

### Deterministic Rules

Rights checking logic is in `app/services/rights_checks.py` (P6 extraction). Trademark patterns live in `app/services/rights_data.py`.

- `licensed_direct` without `license_id` → REJECTED
- `style_only` with trademark elements → REWRITE
- Unknown `reference_type` → REJECTED (fail-safe)
- `commentary` with `risk_score ≥ 70` → REJECTED

## 4. Anti-Spam Controls

| Control | Implementation | Threshold |
|---------|---------------|-----------|
| Duplicate hash detection | `ContentHasher` SHA-256 | Exact match = BLOCK |
| Similarity threshold | Content hash comparison | Same hash = BLOCK |
| Posting cadence | `RateLimiter` per platform | Platform-specific daily limits |
| Rate limiting | `RateLimiter.check_and_consume()` | Min interval enforced |

## 5. Marketing Claims

### Forbidden Claims
- Fake testimonials
- Fake scarcity ("only 3 left!")
- Fake before/after comparisons
- Fake discount claims
- Unverifiable health/medical/financial claims
- "Guaranteed" results

### Enforcement
- `AgentConstitution.validate_caption()` checks for forbidden patterns
- `QAChecker` validates content quality markers

## 6. Human Override Protocol

- Only `human-admin` role can override REWRITE/REJECT decisions
- Every override requires explicit `reason_code`
- Overrides are logged in audit trail with account identity
- Override does not bypass disclosure requirements
