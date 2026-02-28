# Agent Documentation Index

## Agent Registry

| Agent ID | Module | Type | Phase |
|----------|--------|------|-------|
| `manager` | `app/agents/manager.py` | Hybrid (LLM + deterministic) | P6 |
| `product_intake` | `app/agents/product_intake.py` | Hybrid | P1 |
| `product_enrichment` | `app/agents/product_enrichment.py` | LLM | P1 |
| `reference_intelligence` | `app/agents/reference_intelligence.py` | LLM | P1 |
| `scriptwriter` | `app/agents/scriptwriter.py` | LLM | P1 |
| `caption_seo` | `app/agents/caption_seo.py` | LLM | P1 |
| `orchestrator` | `app/agents/orchestrator.py` | Deterministic | P1 |

---

## Supporting Modules (Phase 2–5)

| Module | Path | Purpose | Phase |
|--------|------|---------|-------|
| Copy Writer | `app/content_generation/copy_writer.py` | Generate ad copy with disclosure | P5 |
| Image Gen | `app/content_generation/image_gen.py` | Generate product images via AI | P5 |
| Video Gen | `app/content_generation/video_gen.py` | Generate video storyboards/clips | P5 |
| Calendar Planner | `app/content_generation/calendar_planner.py` | Growth calendar + scheduling | P4 |
| Trend Hooks | `app/content_generation/trend_hooks.py` | Trending hooks + viral patterns | P4 |
| SEO Auditor | `app/analyzers/seo_auditor.py` | SEO scoring + keyword analysis | P4 |
| Performance Learner | `app/analytics/performance_learner.py` | Learn from past metrics | P5 |
| Chat Engine | `app/analytics/chat_engine.py` | AI chat for analytics queries | P5 |
| Approval Gate | `app/approval/__init__.py` | Human-in-the-loop with audit | P5 |
| Publisher | `app/publishers/__init__.py` | Multi-platform publish + dedup | P5 |
| Token Vault | `app/publishers/token_vault.py` | AES-256 OAuth token storage | P6 |
| Scheduler | `app/scheduling/__init__.py` | Post scheduling engine | P5 |
| LLM Client | `app/services/llm_client.py` | OpenAI wrapper + dry-run mode | P6 |
| Script Templates | `app/agents/script_templates.py` | Extracted script angle templates | P6 |
| Rights Checks | `app/services/rights_checks.py` | Per-type rights verification funcs | P6 |
| Rights Data | `app/services/rights_data.py` | Trademark pattern registry | P6 |
| Pipeline State | `app/flows/pipeline_state.py` | PipelineStatus enum + PipelineState model | P6 |
| Pipeline Steps | `app/flows/pipeline_steps.py` | Heavy step method mixin | P6 |

---

## Agent: product_intake

| Attribute | Value |
|-----------|-------|
| **ID** | `product_intake` |
| **Module** | `app/agents/product_intake.py` |
| **Role** | Ingest Amazon product data from API, CSV, or manual input |
| **Inputs** | `source`, `asin`, `title`, `price`, `category`, `csv_data` |
| **Outputs** | `products` (list of `ProductRecord`) |
| **Tools** | `AmazonLookupTool` (future) |
| **Guardrails** | ASIN format validation, no web scraping, audit logged |
| **Fail Condition** | Invalid ASIN → ValueError |

---

## Agent: product_enrichment

| Attribute | Value |
|-----------|-------|
| **ID** | `product_enrichment` |
| **Module** | `app/agents/product_enrichment.py` |
| **Role** | Enrich products with category taxonomy, persona, use cases |
| **Inputs** | `product` (ProductRecord dict) |
| **Outputs** | `enriched_product` (EnrichedProduct dict) |
| **Guardrails** | Input validation, output secret check |
| **KPI** | Persona relevance accuracy |

---

## Agent: reference_intelligence

| Attribute | Value |
|-----------|-------|
| **ID** | `reference_intelligence` |
| **Module** | `app/agents/reference_intelligence.py` |
| **Role** | Map products to culturally resonant references |
| **Inputs** | `product_id`, `category`, `primary_persona`, `use_cases` |
| **Outputs** | `reference_bundle` (ReferenceBundle dict) |
| **Guardrails** | Default to `style_only`, never suggest character likenesses without license |
| **Fail Condition** | No matches → returns safe fallback references |

---

## Agent: scriptwriter

| Attribute | Value |
|-----------|-------|
| **ID** | `scriptwriter` |
| **Module** | `app/agents/scriptwriter.py` |
| **Role** | Generate short-form video scripts |
| **Inputs** | `brief`, `product_title`, `product_category`, `use_cases`, `reference_style` |
| **Outputs** | `script` (Script dict with hook, scenes, CTA) |
| **Angles** | comparison, top_3, story, problem_solution, aesthetic, meme_style |
| **Guardrails** | No unverifiable claims, no fake testimonials, CTA includes `{{AFFILIATE_DISCLOSURE}}` |

---

## Agent: caption_seo

| Attribute | Value |
|-----------|-------|
| **ID** | `caption_seo` |
| **Module** | `app/agents/caption_seo.py` |
| **Role** | Generate platform-optimized captions with affiliate disclosure |
| **Inputs** | `hook`, `value_prop`, `category`, `affiliate_link`, `target_platforms` |
| **Outputs** | `caption_bundle` (CaptionBundle dict) |
| **CRITICAL** | Every caption MUST pass `validate_disclosure()` |
| **Auto-fix** | Missing disclosure → `add_disclosure()` applied automatically |

---

## Agent: orchestrator

| Attribute | Value |
|-----------|-------|
| **ID** | `orchestrator` |
| **Module** | `app/agents/orchestrator.py` |
| **Role** | Manage pipeline flow, route decisions, enforce retry limits |
| **Inputs** | `action`, `compliance_status`, `qa_status` |
| **Outputs** | `next_step`, `should_continue`, `reason` |
| **Max Retries** | 3 rewrite loops before forced REJECT |
| **Guardrails** | Deterministic — no LLM involved in routing decisions |

---

## Agent: manager (Phase 6)

| Attribute | Value |
|-----------|-------|
| **ID** | `manager` |
| **Module** | `app/agents/manager.py` |
| **Role** | Supervises all worker agents; routes decisions; LLM quality review |
| **Type** | Hybrid — deterministic routing + LLM content review |
| **Inputs** | `action` (route_rights / route_qa / review_content / track_agent / get_status) |
| **Outputs** | `next_step`, `should_continue`, `reason`, `quality_score` |
| **Max Retries** | 3 rewrite loops per scope before forced REJECT |
| **LLM Usage** | `review_content` action uses LLM to score quality (0–100) and check brand safety |
| **Guardrails** | All routing is deterministic; LLM only used for quality scoring |

### Actions

| Action | Purpose | LLM? |
|--------|---------|------|
| `route_rights` | Route APPROVE/REWRITE/REJECT from rights check | No |
| `route_qa` | Route APPROVE/REWRITE/REJECT from QA check | No |
| `review_content` | Score content quality, check disclosure/brand safety | Yes |
| `track_agent` | Record agent run metrics (duration, failures) | No |
| `get_status` | Return supervision status + health metrics | No |

---

## Base Agent Contract

All agents extend `BaseAgent` which enforces:

1. **Pre-execution**: `AgentConstitution.validate_input()` on all string inputs
2. **Post-execution**: `AgentConstitution.validate_no_secret_exposure()` on all outputs
3. **Audit logging**: Start, complete, violation, and error events logged
4. **Error handling**: Exceptions caught, logged, and re-raised
