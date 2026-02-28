# Security Architecture Document

## 1. Threat Model

| Threat | Impact | Mitigation | Status |
|--------|--------|------------|--------|
| Prompt injection via product data | Agent executes unintended instructions | `AgentConstitution.validate_input()` scans all string inputs | ✅ Implemented |
| Secret leakage in agent outputs | API keys exposed in captions/logs | `AgentConstitution.validate_no_secret_exposure()` on all outputs | ✅ Implemented |
| Unauthorized platform publishing | Content posted without compliance check | Pipeline requires `compliance_status = APPROVED` before publish | ✅ Implemented |
| Credential theft from logs | Secrets visible in audit trail | `SecretsManager` never logs secret values; audit logger hashes only | ✅ Implemented |
| IP infringement via references | Copyright/trademark violation in published content | `RightsEngine` deterministic verification + fail-safe REJECT | ✅ Implemented |
| Duplicate spam | Same content posted multiple times | `ContentHasher` + `QAChecker` duplicate detection | ✅ Implemented |
| Platform API abuse | Rate limit exceeded, account restricted | `RateLimiter` + `CircuitBreaker` per platform | ✅ Implemented |
| Tampered audit log | Evidence of violations destroyed | SHA-256 hash chain with `verify_chain_integrity()` | ✅ Implemented |
| Hardcoded auth secrets | Default keys allow token forgery | `PasswordHasher` / `TokenManager` reject insecure defaults at startup (P6) | ✅ Implemented |
| Manager Agent prompt injection | LLM review manipulated | Manager only reviews content via `_review_content`; routing is deterministic (P6) | ✅ Implemented |

## 2. Authentication & Authorization

### RBAC Roles

| Role | Permissions | Can Publish? | Can Override? |
|------|-------------|-------------|---------------|
| `orchestrator` | Run pipeline, coordinate agents | No | No |
| `compliance` | Run rights checks, QA | No | No |
| `renderer` | Generate scripts, captions, assets | No | No |
| `publisher` | Publish to platform APIs | Yes | No |
| `analyst` | Read metrics, run experiments | No | No |
| `human-admin` | Override decisions, manage incidents | Yes | Yes (with reason) |

### Credential Management

- **Backend**: Configurable via `SECRETS_BACKEND` env var (`env` | `aws` | `vault`)
- **Access**: Only via `SecretsManager.get()` — never direct env reads in agents
- **Platform credentials**: Retrieved by platform prefix (e.g., `TIKTOK_*`, `INSTAGRAM_*`)
- **OAuth tokens**: Stored via `TokenVault` (`app/publishers/token_vault.py`) with HMAC-based encryption (production: AES-256-GCM)
- **Auth secrets**: `AUTH_SECRET_KEY` and `JWT_SECRET_KEY` must be set via env vars; startup guard rejects insecure defaults
- **Never logged**: Secrets manager ensures no secret values appear in logs or audit trail

## 3. Media Security

- All media URLs are **signed and time-limited** (default: 24 hours)
- Generated via `MediaSigner.generate_signed_url()` using boto3 S3 presigned URLs
- No permanent public URLs for any asset
- `StorageAdapter` enforces signed URL requirement on all downloads

## 4. Audit Trail

- **Append-only**: Events are only added, never modified or deleted
- **Hash chain**: Each event contains SHA-256 hash of `agent_id + action + timestamp + input_hash + output_hash + previous_hash`
- **Verification**: `AuditLogger.verify_chain_integrity()` validates entire chain
- **Coverage**: Every agent execution, rights decision, QA check, publish attempt, and error is logged

## 5. Input Validation

### Prompt Injection Defense

The `AgentConstitution.validate_input()` method scans for:
- "ignore previous instructions"
- "SYSTEM:" / "system prompt"
- "pretend you are"
- Role hijacking attempts
- Template escape sequences

### Content Validation

- ASIN format: regex `^[A-Z0-9]{10}$`
- Caption length: per-platform limits enforced
- Media specs: format, resolution, file size validated against `PLATFORM_SPECS`

## 6. Incident Response

| Incident Type | Automated Response | Human Action |
|---------------|-------------------|--------------|
| DMCA takedown | Unpublish all variants, disable reference | Review and update rights registry |
| Token leak detected | Rotate token, audit exposure window | Verify no unauthorized access |
| Account restriction | Circuit breaker OPEN, stop all posts | Contact platform support |
| Rights uncertainty | REWRITE or REJECT (never publish) | Manual rights verification |
| API auth failure | Queue post, create alert | Check API credentials |

## 7. Security Coding Standards

- **No hardcoded secrets**: All credentials via `SecretsManager`; auth defaults rejected at startup (P6 hardening)
- **No scraping**: Only official APIs (`Agents.md` Rule 3)
- **No browser automation**: All platform interactions via REST APIs
- **Fail-safe defaults**: Unknown = REJECT, missing disclosure = REWRITE
- **Type safety**: Pydantic v2 models with strict validation
- **Audit coverage**: Every decision produces an `AuditEvent`
- **SQLite persistence**: Dev/local audit logs written to SQLite via `session_factory` (P6)
