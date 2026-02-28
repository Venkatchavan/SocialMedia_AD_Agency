# Architecture Decision Records (ADRs)

---

## ADR-001: Deterministic Compliance Services

**Date**: 2024-01-01
**Status**: Accepted

### Context
The system must verify rights, assess risk, and run QA checks on content
before publishing. These are compliance-critical decisions.

### Decision
Rights verification (`RightsEngine`), risk scoring (`RiskScorer`), and
QA checking (`QAChecker`) are implemented as **deterministic, rule-based
services** — not LLM-based agents.

### Rationale
- Compliance decisions must be reproducible and auditable
- LLM outputs are non-deterministic — unsuitable for legal/compliance gates
- Deterministic rules can be formally verified and tested
- Reduces cost (no LLM API calls for every rights check)

### Consequences
- Rights rules must be manually maintained as regulations change
- Complex edge cases may need human escalation
- Risk scoring thresholds are configurable (40/70 boundaries)

---

## ADR-002: SHA-256 Hash Chain for Audit Trail

**Date**: 2024-01-01
**Status**: Accepted

### Context
The system needs an immutable, tamper-evident audit trail per `Agents.md`
Rule 7 (Auditability) and `Agents_Security.md` requirements.

### Decision
Use an append-only SHA-256 hash chain where each audit event links to the
previous event's hash.

### Rationale
- Hash chain provides cryptographic tamper evidence
- Verification is O(n) and lightweight
- Compatible with future blockchain/immutable-ledger backing stores
- No external dependencies required for MVP

### Consequences
- Chain must be verified periodically
- Database-backed implementation needs REVOKE UPDATE/DELETE on audit tables
- Memory-based chain (MVP) is lost on restart — production needs PostgreSQL

---

## ADR-003: Auto-Fix vs. Reject for Missing Disclosures

**Date**: 2024-01-01
**Status**: Accepted

### Context
When a generated caption is missing affiliate disclosure, the system must
decide whether to reject it or auto-fix it.

### Decision
Missing disclosure triggers **REWRITE** with automatic `add_disclosure()`,
not REJECT. The auto-fixed caption is then re-validated.

### Rationale
- `Agents.md` Rule 10: "On missing disclosure → auto-rewrite caption only, then re-QA"
- Rejection would block pipeline unnecessarily when fix is trivial
- Auto-fix is deterministic and verifiable
- Final `verify_all_disclosures()` ensures compliance before publish

### Consequences
- Auto-added disclosures may not be optimally placed in caption
- Captions should be designed with disclosure templates (preferred path)
- If auto-fix somehow fails, `verify_all_disclosures()` catches it → REJECT

---

## ADR-004: Fail-Safe REJECT on Rights Uncertainty

**Date**: 2024-01-01
**Status**: Accepted

### Context
When the system encounters a reference with uncertain rights status, it must
decide whether to proceed, pause, or block.

### Decision
Unknown reference types or uncertain rights → **REJECT** (never publish).

### Rationale
- `Agents.md` Rule 10: "On rights uncertainty → REWRITE or REJECT (never publish)"
- Legal liability of publishing infringing content > opportunity cost of rejection
- Human admin can override with explicit reason code
- Overrides are logged and auditable

### Consequences
- May over-reject in edge cases
- Requires human-admin review for borderline references
- Reference knowledge base should be expanded to reduce uncertainty

---

## ADR-005: Platform Adapter Pattern with Circuit Breaker

**Date**: 2024-01-01
**Status**: Accepted

### Context
Publishing to external platform APIs is unreliable — APIs may rate-limit,
restrict accounts, or go down.

### Decision
Each platform adapter implements `RateLimiter` + `CircuitBreaker` pattern.
Circuit breaker has three states: CLOSED (normal) → OPEN (failing) → HALF_OPEN (testing).

### Rationale
- Prevents cascading failures from overwhelming a failing API
- Auto-recovery via HALF_OPEN state (test one request, re-close on success)
- Rate limiting enforces platform-specific posting cadence
- Combined pattern prevents both spam and crash loops

### Consequences
- Posts may be delayed when circuit is open
- Need queue/retry mechanism for deferred posts (Phase 2)
- Platform-specific rate configs need tuning per actual API docs
