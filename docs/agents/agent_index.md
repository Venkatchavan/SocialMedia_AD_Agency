# Agent Documentation Index

## Agent Registry

| Agent ID | Module | Type | Phase |
|----------|--------|------|-------|
| `product_intake` | `app/agents/product_intake.py` | Hybrid | P1 |
| `product_enrichment` | `app/agents/product_enrichment.py` | LLM | P1 |
| `reference_intelligence` | `app/agents/reference_intelligence.py` | LLM | P1 |
| `scriptwriter` | `app/agents/scriptwriter.py` | LLM | P1 |
| `caption_seo` | `app/agents/caption_seo.py` | LLM | P1 |
| `orchestrator` | `app/agents/orchestrator.py` | Deterministic | P1 |

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

## Base Agent Contract

All agents extend `BaseAgent` which enforces:

1. **Pre-execution**: `AgentConstitution.validate_input()` on all string inputs
2. **Post-execution**: `AgentConstitution.validate_no_secret_exposure()` on all outputs
3. **Audit logging**: Start, complete, violation, and error events logged
4. **Error handling**: Exceptions caught, logged, and re-raised
