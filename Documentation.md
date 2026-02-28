DOCUMENTATION GENERATION RULES (MANDATORY)

After implementing any PHASE, TOOL, or AGENT, generate/update docs immediately.

Current project: SocialMedia AD Agency — Production SaaS
Architecture: app/ (19 subpackages) + tests/ (401 tests, 75% coverage)
Stack: Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, CrewAI, structlog

---

1) Phase Documentation
File: docs/phases/phase-XX-name.md
Must include:
- objective
- scope
- architecture changes
- modules added/changed (reference app/ paths)
- data schema changes
- tests added (reference tests/unit/ paths)
- risks
- rollback steps
- next phase dependencies

2) Agent Documentation
File: docs/agents/<agent_name>.md
Must include:
- purpose
- inputs/outputs (reference app/schemas/)
- prompt version
- tools used (reference app/tools/)
- guardrails (reference app/policies/)
- failure modes
- example APPROVE/REWRITE/REJECT outputs
- KPIs and monitoring

3) Tool / Adapter Documentation
File: docs/tools/<tool_name>.md
Must include:
- auth method (via app/services/secrets.py)
- API endpoints used
- rate limits (reference app/policies/rate_limits.py)
- request/response schema
- retries/backoff
- common errors
- fallback behavior

4) Flow Documentation
File: docs/flows/<flow_name>.md
Must include:
- state machine
- transition rules
- retry policy
- compensation/rollback actions
- audit events emitted (via app/services/audit_logger.py)

5) Compliance Documentation
File: docs/compliance/compliance_controls.md
Must include:
- rights decision logic (app/services/rights_engine.py)
- disclosure rules (app/policies/disclosure_rules.py)
- risk scoring thresholds (app/services/risk_scorer.py)
- agent constitution (app/policies/agent_constitution.py)
- QA checker rules (app/services/qa_checker.py)
- escalation policy
- incident process (app/services/incident_manager.py)

6) Security Documentation
File: docs/security/
Must include:
- threat_model.md
- secrets management (app/services/secrets.py)
- auth & RBAC (app/core/auth.py)
- media signing (app/services/media_signer.py)
- audit trail (app/services/audit_logger.py)

7) ADRs (Architecture Decision Records)
File: docs/adrs/ADR-XXXX-title.md
Must be created for major decisions:
- deterministic compliance services (vs LLM)
- SHA-256 hash chain for audit trail
- auto-fix vs reject for missing disclosures
- fail-safe reject on rights uncertainty
- platform adapter pattern with circuit breaker