# Flow Documentation

## Overview

The `app/flows/` package contains the orchestration layer that drives the entire content pipeline. Flows coordinate agents, services, and tools into end-to-end workflows.

| Flow | Module | Purpose |
|------|--------|---------|
| Content Pipeline | `content_pipeline.py` | Main 8-step synchronous pipeline |
| Pipeline State | `pipeline_state.py` | PipelineStatus enum + PipelineState model (P6 extraction) |
| Pipeline Steps | `pipeline_steps.py` | Heavy step methods mixin (P6 extraction) |
| Async Pipeline | `async_pipeline.py` | Concurrent stage executor (U-7) |
| Publish Flow | `publish_flow.py` | Post-QA multi-platform publishing |
| Experiment Flow | `experiment_flow.py` | A/B testing and variant management |

---

## Content Pipeline Flow

**Module:** `app/flows/content_pipeline.py` (imports `pipeline_state.py`, mixes in `pipeline_steps.py`)  
**Class:** `ContentPipelineFlow(PipelineStepsMixin)`

The master orchestration flow that drives the full ad creation lifecycle:

```
Product Intake → Enrichment → Reference Mapping → Rights Check →
Content Generation → QA → Platform Adaptation → Publish
```

### Pipeline State

Uses `PipelineState` (from `app/flows/pipeline_state.py`) as shared state:

| Field | Type | Purpose |
|-------|------|---------|
| `pipeline_id` | `str` | Unique execution ID (UUID) |
| `status` | `PipelineStatus` | Current stage enum |
| `asin` | `str` | Amazon product identifier |
| `target_platforms` | `list[str]` | Platforms to publish to |
| `product` | `dict` | Raw product data |
| `enriched_product` | `dict` | Enriched product data |
| `reference_bundle` | `dict` | Cultural reference mappings |
| `rights_decision` | `dict` | Rights verification result |
| `script` | `dict` | Generated script |
| `caption_bundle` | `dict` | Platform-specific captions |
| `qa_decision` | `dict` | QA check result |
| `rewrite_count` | `int` | Number of REWRITE loops |

### Pipeline Stages

| Step | Method | Agent/Service | Branching |
|------|--------|---------------|-----------|
| 1. Intake | `_step_intake` | `product_intake_agent` | Error if no products |
| 2. Enrichment | `_step_enrichment` | `product_enrichment_agent` | — |
| 3. Reference Mapping | `_step_reference_mapping` | `reference_intelligence_agent` | — |
| 4. Rights Check | `_step_rights_check` | `rights_engine` + `orchestrator` | APPROVE / REWRITE / REJECT |
| 5. Content Gen | `_step_content_generation` | `scriptwriter` + `caption_seo` | — |
| 5b. Manager Review | `_step_manager_review` | `manager_agent` (LLM) | APPROVE / REWRITE |
| 6. QA | `_step_qa` | `qa_checker` + `orchestrator` | APPROVE / REWRITE / REJECT |
| 7. Publish | `_step_publish` | Platform adapters | — |

> Steps 4–7 and `_finalize` live in `pipeline_steps.py` (PipelineStepsMixin).  
> Steps 1–3 and 5b remain in `content_pipeline.py`.

### Branching Logic

- **APPROVE** → Continue to next step
- **REWRITE** → Loop back (rights → re-map references; QA → re-generate content). Max `max_retries` (default 3)
- **REJECT** → Pipeline terminates, state finalized with rejection reason

### Audit Trail

Every pipeline execution logs a finalization event via `AuditLogger` with:
- Pipeline ID, ASIN, status, platforms, rewrite count
- Input/output data hashes
- Duration in seconds

---

## Async Pipeline Executor

**Module:** `app/flows/async_pipeline.py`  
**Class:** `AsyncPipelineExecutor`

Concurrent stage execution with semaphore-based concurrency control. Reduces pipeline execution time ~60% by running independent stages in parallel.

### Usage Pattern

```python
executor = AsyncPipelineExecutor(max_concurrent=5)

# Sequential stage
executor.add_sequential("intake", intake_fn, arg1, arg2)

# Parallel group
executor.add_parallel("analysis", [
    ("analyze_media", analyze_fn, arg1),
    ("mine_comments", mining_fn, arg1),
])

# Another sequential stage
executor.add_sequential("synthesize", synthesize_fn, data)

result = await executor.run()
```

### Concurrency Controls

- **Semaphore:** Limits concurrent LLM calls (default: 5)
- **Fail-fast:** Pipeline stops on first `FAILED` stage
- **Timing:** Each stage reports `duration_ms`

### Result Types

| Type | Fields |
|------|--------|
| `StageResult` | `name`, `status`, `duration_ms`, `output`, `error` |
| `PipelineResult` | `stages[]`, `total_duration_ms`, `succeeded`, `failed_stages` |

---

## Publish Flow

**Module:** `app/flows/publish_flow.py`  
**Class:** `PublishFlow`

Post-QA publishing to platform adapters with safety controls.

### Safety Controls

| Control | Rule | Behavior |
|---------|------|----------|
| Duplicate Detection | Rule 9 | SHA-256 hash dedup — blocks repeated content |
| Circuit Breaker | Rule 10 | Platform failure isolation — queues on open circuit |
| Rate Limiting | Rule 9 | Per-platform post cadence enforcement |
| Audit Logging | Rule 7 | Every publish/block/error creates audit event |

### Publish Sequence

1. **Hash check** — Compute SHA-256 of caption; reject if already published
2. **Circuit breaker** — Check platform health; queue if circuit is open
3. **Rate limit** — Enforce posting cadence; queue if exceeded
4. **Adapter publish** — Delegate to platform-specific adapter
5. **Record success/failure** — Update circuit breaker state + audit log

### Platform Adapter Protocol

```python
class PlatformAdapter(Protocol):
    def publish(self, package: dict) -> dict: ...
    @property
    def platform_name(self) -> str: ...
```

---

## Experiment Flow

**Module:** `app/flows/experiment_flow.py`  
**Class:** `ExperimentFlow`

A/B testing framework for content variants.

### API

| Method | Purpose |
|--------|---------|
| `create_experiment(name, variants, traffic_split)` | Create experiment with ≥2 variants |
| `assign_variant(experiment_id)` | Weighted random variant assignment |
| `record_result(experiment_id, variant_id, metric, value)` | Record metric observation |
| `get_experiment_summary(experiment_id)` | Aggregate metrics (count, mean, total) |
| `conclude_experiment(experiment_id, winner_id)` | End experiment, declare winner |

### Constraints

- Minimum 2 variants per experiment
- Traffic split must sum to 1.0
- Experiment must be `active` to assign variants
- All operations are audit-logged
