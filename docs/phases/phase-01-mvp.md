# Phase 01 — MVP: Core Pipeline

## Phase Overview

| Attribute | Value |
|-----------|-------|
| **Phase** | 01 — MVP |
| **Duration** | 2-3 weeks |
| **Goal** | End-to-end pipeline: ASIN → Script + Caption with compliance |
| **Success Criteria** | Pipeline completes for 1 product on 2 platforms with full audit trail |

## Scope

### In Scope
- Product intake (manual + CSV)
- Product enrichment (category mapping, persona assignment)
- Reference intelligence (style_only references only)
- Deterministic rights verification
- Script generation (problem_solution angle)
- Caption generation with auto-disclosure
- QA checking (compliance, disclosure, dedup)
- Audit logging with hash chain
- Rate limiting and circuit breaker scaffolding
- Platform adapter stubs (TikTok, Instagram)

### Out of Scope (Future Phases)
- Actual platform API publishing
- Video/image asset generation
- A/B experimentation
- Analytics dashboard
- Production database (PostgreSQL)
- Production secrets manager (AWS/Vault)

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   main.py                           │
│         CLI entry + Component Wiring                │
├─────────────────────────────────────────────────────┤
│              ContentPipelineFlow                     │
│  intake → enrich → ref → rights → script → qa      │
├──────────┬──────────┬───────────┬──────────────────┤
│ Agents   │ Services │ Policies   │ Adapters (stubs) │
│ 6 agents │ 7 svc    │ 4 policy   │ 6 adapters       │
└──────────┴──────────┴───────────┴──────────────────┘
```

## Deliverables

| # | Deliverable | File(s) | Status |
|---|------------|---------|--------|
| 1 | System Design Document | `SYSTEM_DESIGN.md` | ✅ Complete |
| 2 | Project config | `pyproject.toml`, `.env.example`, `.gitignore` | ✅ Complete |
| 3 | Pydantic schemas (10 modules) | `app/schemas/` | ✅ Complete |
| 4 | Core services (7 modules) | `app/services/` | ✅ Complete |
| 5 | Policy modules (4 modules) | `app/policies/` | ✅ Complete |
| 6 | Agent modules (7 modules) | `app/agents/` | ✅ Complete |
| 7 | Flow modules (3 flows) | `app/flows/` | ✅ Complete |
| 8 | Adapter modules (7 modules) | `app/adapters/` | ✅ Complete |
| 9 | Tool wrappers (5 modules) | `app/tools/` | ✅ Complete |
| 10 | Entry point | `app/main.py` | ✅ Complete |
| 11 | Unit tests (7 suites) | `tests/unit/` | ✅ Complete |
| 12 | Integration tests | `tests/integration/` | ✅ Complete |
| 13 | Security docs | `docs/security/` | ✅ Complete |
| 14 | Compliance docs | `docs/compliance/` | ✅ Complete |

## Agents (Phase 1)

| Agent ID | Type | Role |
|----------|------|------|
| `product_intake` | Deterministic + LLM | Ingest Amazon product data |
| `product_enrichment` | LLM | Enrich with category, persona, use cases |
| `reference_intelligence` | LLM | Map products to cultural references |
| `scriptwriter` | LLM | Generate short-form video scripts |
| `caption_seo` | LLM | Generate platform-optimized captions |
| `orchestrator` | Deterministic | Manage pipeline flow and branching |

## Key Design Decisions

1. **Rights/QA/Risk are deterministic** — no LLM involved in compliance decisions
2. **Disclosure auto-fix** — missing disclosure triggers REWRITE with auto-add, not REJECT
3. **Fail-safe on uncertainty** — unknown reference types → REJECT
4. **Max rewrite loops = 3** — prevents infinite loops on persistent issues
5. **Hash chain audit** — SHA-256 linked chain for tamper detection
