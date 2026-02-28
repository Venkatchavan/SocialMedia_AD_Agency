DOCUMENTATION GENERATION RULES (MANDATORY)

After implementing any PHASE, TOOL, or AGENT, generate/update docs immediately.

1) Phase Documentation
File: docs/phases/phase-XX-name.md
Must include:
- objective
- scope
- architecture changes
- modules added/changed
- data schema changes
- tests added
- risks
- rollback steps
- next phase dependencies

2) Agent Documentation
File: docs/agents/<agent_name>.md
Must include:
- purpose
- inputs/outputs
- prompt version
- tools used
- guardrails
- failure modes
- example APPROVE/REWRITE/REJECT outputs
- KPIs and monitoring

3) Tool / Adapter Documentation
File: docs/tools/<tool_name>.md
Must include:
- auth method
- API endpoints used
- rate limits
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
- audit events emitted

5) Compliance Documentation
File: docs/compliance/rights-and-disclosure.md
Must include:
- rights decision logic
- disclosure rules
- risk scoring thresholds
- escalation policy
- incident process

6) Security Documentation
File: docs/security/
Must include:
- threat-model.md
- secrets-policy.md
- rbac-matrix.md
- incident-runbooks.md

7) ADRs (Architecture Decision Records)
File: docs/adrs/ADR-XXXX-title.md
Must be created for major decisions:
- queue choice
- storage choice
- rendering engine
- publishing adapters
- compliance engine design