# Phase 6 — LLM Agents, Manager Agent & Structural Hardening

| Field   | Value |
|---------|-------|
| Status  | ✅ Complete |
| Started | 2025-06 |
| Scope   | Real LLM integration, supervisory Manager Agent, module extractions, security hardening |

---

## Objectives

1. Convert deterministic agents to **real LLM agents** (with dry-run fallback).
2. Add a **Manager Agent** that supervises all worker agents.
3. **Extract oversized modules** to enforce the 250-line limit.
4. **Harden auth** — remove hardcoded secrets, add startup guards.
5. Add **SQLite persistence** for audit logs (dev/local).

---

## Deliverables

| # | Deliverable | Status |
|---|-------------|--------|
| 1 | `app/services/llm_client.py` — LLM client (OpenAI, dry-run) | ✅ |
| 2 | `LLM_DRY_RUN=true` flag in Settings | ✅ |
| 3 | `app/agents/manager.py` — Manager Agent (routing, LLM review, health tracking) | ✅ |
| 4 | Wired LLM into ScriptwriterAgent, CaptionSEOAgent, ProductEnrichmentAgent | ✅ |
| 5 | `app/agents/script_templates.py` — extracted templates | ✅ |
| 6 | SQLite persistence for AuditLogger | ✅ |
| 7 | `app/db/init_db.py` — database bootstrap | ✅ |
| 8 | Manager review step (`_step_manager_review`) in ContentPipelineFlow | ✅ |
| 9 | Updated `build_pipeline()` with LLM + Manager wiring | ✅ |
| 10 | 27 new tests (llm_client + manager_agent) | ✅ |
| 11 | Module extractions (pipeline_state, pipeline_steps, rights_checks, rights_data, token_vault) | ✅ |
| 12 | Auth hardening — startup guard on PasswordHasher / TokenManager secrets | ✅ |
| 13 | Inline import cleanup (product_enrichment) | ✅ |

---

## Module Extractions

| Original File (lines before) | Extracted To | Purpose |
|------------------------------|-------------|---------|
| `content_pipeline.py` (445) | `pipeline_state.py` (61) + `pipeline_steps.py` (209) | State/enum + heavy step methods |
| `rights_engine.py` (355) | `rights_checks.py` (157) + `rights_data.py` (15) | Reference-type checkers + trademark list |
| `publishers/__init__.py` (279) | `token_vault.py` (59) | OAuth token vault |

---

## Architecture Changes

### Manager Agent

The Manager Agent (`app/agents/manager.py`) sits above all worker agents:

- **Routing**: Deterministic APPROVE / REWRITE / REJECT decisions for rights and QA.
- **LLM Review**: Quality gate on generated scripts and captions (quality score, brand safety, disclosure check).
- **Health Tracking**: Records agent run count, failure count, and timing.
- **Supervised Execution**: `supervise()` wraps any agent call with timing and error tracking.
- **Rewrite Limits**: Max 3 rewrites per scope (rights, QA) before hard REJECT.

### LLM Integration

- `LLMClient` wraps OpenAI API (or dry-run stubs).
- `LLM_DRY_RUN=true` (default) returns deterministic placeholders — safe for CI.
- Three agents now call LLM when `LLM_DRY_RUN=false`: Scriptwriter, CaptionSEO, ProductEnrichment.

### Auth Hardening

- `PasswordHasher` and `TokenManager` no longer accept empty or default secret keys.
- Startup guard raises `ValueError` if insecure defaults are used.
- Auth secrets sourced from `AUTH_SECRET_KEY` / `JWT_SECRET_KEY` env vars.

---

## Test Coverage

- 430 tests passing, 74% coverage (exceeds 70% threshold).
- New tests: `test_llm_client.py` (12), `test_manager_agent.py` (15), auth insecure-default guards (2).
