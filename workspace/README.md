# Creative Intelligence OS — Workspace

[![CI](https://github.com/Venkatchavan/SocialMedia_AD_Agency/actions/workflows/ci.yml/badge.svg)](https://github.com/Venkatchavan/SocialMedia_AD_Agency/actions/workflows/ci.yml)

An automated ad research pipeline: **Collect → Analyze → Brand Enhance → Brief → QA → Export**

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Environment Variables](#environment-variables)
3. [CLI Reference](#cli-reference)
4. [Pipeline Stages](#pipeline-stages)
5. [Brand Enhancement Engine](#brand-enhancement-engine)
6. [LLM Router](#llm-router)
7. [Compliance Suite](#compliance-suite)
8. [Project Structure](#project-structure)
9. [Tests](#tests)
10. [Key Constraints](#key-constraints)
11. [Roadmap](#roadmap)

---

## Quick Start

```bash
cd workspace
pip install -r requirements.txt
cp .env.example .env          # fill in your keys

# Demo pipeline (no collection)
python cli.py run --workspace sample_client

# Collect 20 live TikTok ads then run full pipeline
python cli.py collect \
  --workspace sample_client \
  --platform tiktok \
  --keywords "AI,SaaS,automation" \
  --count 20 \
  --run

# Update the Brand Book with new market signals
python cli.py enhance-brand \
  --workspace sample_client \
  --keywords "productivity,B2B,enterprise" \
  --hashtags "#SaaS2026,#AItools" \
  --context "Launching enterprise tier in Q2"

# Run all tests
pytest tests/ -v
```

---

## Environment Variables

Set in `workspace/.env` (never committed to git):

| Variable | Required | Description |
|----------|----------|-------------|
| `APIFY_TOKEN` | Yes (collect) | Apify API token for TikTok/Meta/Pinterest collection |
| `OPENAI_API_KEY` | Recommended | GPT-4o-mini brief enrichment + brand enhancement |
| `GEMINI_API_KEY` | Optional | Gemini 2.0 Flash fallback |
| `ANTHROPIC_API_KEY` | Optional | Claude fallback |
| `MISTRAL_API_KEY` | Optional | Mistral fallback |
| `OPENAI_MODEL` | Optional | Default: `gpt-4o-mini` |
| `LLM_PROVIDER_ORDER` | Optional | Default: `openai,gemini,anthropic,mistral` |
| `LLM_TEMPERATURE` | Optional | Default: `0.4` |
| `X_BEARER_TOKEN` | Optional | X/Twitter organic API |

---

## CLI Reference

All commands: `python cli.py <command> [options]`

### `run` — Full pipeline

```bash
python cli.py run --workspace sample_client
python cli.py run --workspace sample_client --csv path/to/ads.csv
```

### `collect` — Live ad collection via Apify

```bash
python cli.py collect \
  --workspace sample_client \
  --platform tiktok          # tiktok | meta | pinterest
  --brand "my_brand" \
  --keywords "AI,SaaS,automation" \
  --count 20 \
  --run                      # run full pipeline after collecting
```

### `enhance-brand` — Brand Book update

```bash
# Update brand bible with new signals (LLM-assisted, incremental)
python cli.py enhance-brand \
  --workspace sample_client \
  --keywords "keyword1,keyword2" \
  --hashtags "#tag1,#tag2" \
  --context "Optional free-text context for this run" \
  --run-id "custom_run_id"    # optional

# List all saved versions
python cli.py enhance-brand --workspace sample_client --list-versions
```

### `schedule` — Weekly scheduler

```bash
python cli.py schedule           # continuous loop
python cli.py schedule --once    # single cycle and exit
```

### `check` — Line-count enforcement

```bash
python cli.py check    # fails CI if any file > 250 lines
```

### `crew` — CrewAI agents pipeline

```bash
python cli.py crew --workspace sample_client
```

### `preflight` — Compliance pre-run gate

```bash
python cli.py preflight --workspace sample_client
```

### `cleanup` — Data retention purge

```bash
python cli.py cleanup --workspace sample_client --dry-run   # preview
python cli.py cleanup                                        # all workspaces
```

### `incident` — Incident response

```bash
python cli.py incident \
  --workspace sample_client \
  --run-id 2026-02-27_143355 \
  --type pii_leaked \
  --description "Accidental PII in tags.json" \
  --rotate-keys
```

Incident types: `pii_leaked` | `unauthorized_collection` | `competitor_copy_exported` |
`bypass_instruction_detected` | `cross_workspace_contamination` | `other`

---

## Pipeline Stages

| # | Stage | Module | Output |
|---|-------|--------|--------|
| 0 | **Preflight** | `compliance/preflight.py` | Blocks run on hard errors |
| 1 | **Doc Update** | `core/doc_updater.py` | `phase_notes.md` |
| 2 | **Plan** | `orchestration/pipeline.py` | `plan.json` |
| 3 | **Collect** | `collectors/` | `assets.json`, `raw_refs.json` |
| 4 | **Analyze** | `analyzers/` | `tags.json`, `comment_themes.json` |
| 5 | **Synthesize** | `synthesis/` | `clusters.json`, `insights.md`, `aot_ledger.jsonl` |
| 6 | **Brief** | `briefs/` | `brief.md`, `brief.json` |
| 7 | **QA Gate** | `qa/` | `qa_report.json` (blocks export on FAIL) |
| 8 | **Export** | `export/` | JSON bundle + ZIP |
| 9 | **Scheduler** | `orchestration/scheduler.py` | Weekly auto-refresh |

---

## Brand Enhancement Engine

The `brand_enchancement` package automatically updates a versioned Brand Book every run.

### How It Works

```
Input (each run):
  --keywords "AI,automation"     new market signals
  --hashtags "#SaaS2026"         trend signals
  --context "product launch"     free-form notes

Engine steps:
  1. Load    → BrandBible.json (structured) or Brand_Book.md (legacy) or fresh doc
  2. Merge   → deduplicate keywords/hashtags; LLM proposes field-by-field patches
  3. Version → save snapshot to brand_enchancement_versions/v{N}_{run_id}.json
  4. Render  → write updated Brand_Book.md (human-readable)

Output:
  clients/<workspace>/BrandBible.json               ← live structured doc
  clients/<workspace>/Brand_Book.md                 ← human-readable markdown
  clients/<workspace>/brand_enchancement_versions/  ← full version history
```

### Brand Book Sections (Industry-Agnostic)

Works for SaaS, e-commerce, healthcare, fashion, finance, B2B, creators — any industry.

| Section | Key Fields |
|---------|-----------|
| Brand Summary | `what_we_sell`, `what_we_stand_for`, `what_we_never_do`, `industry` |
| Audience | `primary`, `secondary`, `awareness_level`, `pain_points` |
| Voice & Tone | `adjectives`, `use`, `avoid`, `examples` |
| Proof & Claims | `allowed`, `forbidden`, `substantiation_required` |
| Visual Style | `do`, `dont`, `references` |
| Offers | `typical`, `constraints` |
| Competitors | `main`, `positioning_difference` |
| Signals (accumulated) | `keywords[]`, `hashtags[]`, `extra_context_log[]` |
| Change Log | Per-run diff table: version, fields updated, summary |

### Programmatic Usage

```python
from brand_enchancement.engine import update_brand_bible

result = update_brand_bible(
    workspace_id="acme_saas",
    keywords=["productivity", "AI", "B2B"],
    hashtags=["#SaaS2026", "#AItools"],
    extra_context="Launching enterprise tier in Q2",
)
print(result.version)    # new version number
print(result.report)     # human-readable diff summary
print(result.md_path)    # path to updated Brand_Book.md
```

---

## LLM Router

`analyzers/llm_router.py` provides a provider-agnostic LLM interface used by the brief writer
and brand enhancement engine.

### Provider Priority

Controlled by `LLM_PROVIDER_ORDER` in `.env`:

```
LLM_PROVIDER_ORDER=openai,gemini,anthropic,mistral
```

The router tries each provider in order, skipping any without an API key set.

### Supported Providers

| Provider | Env Var | Default Model |
|----------|---------|---------------|
| OpenAI | `OPENAI_API_KEY` | `gpt-4o-mini` |
| Gemini | `GEMINI_API_KEY` | `gemini-2.0-flash` |
| Anthropic | `ANTHROPIC_API_KEY` | `claude-3-haiku-20240307` |
| Mistral | `MISTRAL_API_KEY` | `mistral-small-latest` |

### Adding a New Provider

1. Subclass `LLMProvider` in `llm_router.py`
2. Implement `name`, `is_available()`, `generate()`
3. Register in `_REGISTRY`
4. Add its name to `LLM_PROVIDER_ORDER`

No other code changes required.

---

## Compliance Suite

| Module | Purpose | Policy Section |
|--------|---------|----------------|
| `policy_loader.py` | Per-client `CompliancePolicy.yaml` override | §13 |
| `url_validator.py` | SSRF + domain allowlist guard | §7.2 |
| `preflight.py` | Pre-run checklist gate | §11 |
| `cleanup.py` | Automated data retention + purge | §6.3 |
| `incident.py` | Incident response handler | §14 |

### Per-Client Policy (`clients/<workspace>/CompliancePolicy.yaml`)

```yaml
require_brand_bible: true
require_competitors_file: true
max_run_age_days: 30
allowed_domains:
  - example.com
block_keywords:
  - competitor_name
```

---

## Project Structure

```
workspace/
├── cli.py                         CLI entry point
├── cli_commands.py                Command implementations
│
├── brand_enchancement/            Brand Enhancement Engine
│   ├── __init__.py
│   ├── schemas.py                 BrandBibleDoc, UpdateSignal, ChangeRecord (Pydantic)
│   ├── loader.py                  Load: JSON → MD → fresh bootstrap
│   ├── merger.py                  LLM-assisted incremental field merge
│   ├── versioning.py              Versioned snapshots + diff_summary()
│   ├── renderer.py                BrandBibleDoc → Brand_Book.md
│   └── engine.py                  update_brand_bible() public entry point
│
├── analyzers/
│   ├── llm_router.py              Pluggable LLM provider registry
│   ├── gemini_client.py           Gemini 2.0 Flash (image + text)
│   ├── media_analyzer.py
│   ├── comment_miner.py
│   └── tagger_rules.py
│
├── briefs/
│   ├── brief_writer.py            LLM-enriched SMP + RTBs + hooks + scripts
│   ├── template_loader.py         Loads Brand_Book.md + BriefTemplate.md
│   └── brief_renderer_md.py
│
├── collectors/
│   ├── apify_client.py            Apify REST client (TikTok / Meta / Pinterest)
│   ├── tiktok_collector.py
│   ├── meta_collector.py
│   ├── pinterest_collector.py
│   ├── x_collector.py
│   └── csv_importer.py
│
├── compliance/
│   ├── policy_loader.py
│   ├── url_validator.py
│   ├── preflight.py
│   ├── cleanup.py
│   └── incident.py
│
├── core/
│   ├── config.py                  All env vars + USE_LLM_BRIEF feature flag
│   ├── enums.py                   Platform, FormatType, HookTactic, MessagingAngle, …
│   ├── schemas_asset.py
│   ├── schemas_tag.py
│   ├── schemas_brief.py
│   ├── schemas_qa.py
│   ├── schemas_aot.py
│   ├── errors.py
│   ├── logging.py
│   ├── utils_hash.py
│   ├── utils_urls.py
│   ├── utils_time.py
│   └── doc_updater.py
│
├── db/
│   ├── sqlite.py
│   ├── repo_assets.py
│   └── repo_runs.py
│
├── export/
│   ├── exporter_json.py
│   ├── exporter_md.py
│   └── packager.py
│
├── orchestration/
│   ├── crew.py                    CrewAI agents
│   ├── pipeline.py                Full end-to-end pipeline
│   └── scheduler.py               Weekly cadence loop
│
├── qa/
│   ├── qa_gate.py
│   ├── pii_redaction.py
│   ├── no_copy_checks.py
│   └── claim_checks.py
│
├── synthesis/
│   ├── clustering.py
│   ├── insights.py
│   ├── ranking.py
│   └── aot_writer.py
│
├── scripts/
│   └── check_linecount.py         Enforces 250-line limit
│
├── tests/
│   ├── test_schemas.py
│   ├── test_redaction.py
│   ├── test_template_engine.py
│   ├── test_compliance_policy.py
│   ├── test_compliance_runtime.py
│   └── test_brand_enchancement.py  20 tests for the brand engine
│
├── pyproject.toml                 ruff + pytest config
├── requirements.txt
└── clients/
    └── sample_client/
        ├── Brand_Book.md              Human-readable brand bible (auto-generated)
        ├── BrandBible.json            Structured brand bible (auto-generated)
        ├── BriefTemplate.md
        ├── CompliancePolicy.yaml
        ├── Competitors.yml
        ├── brand_enchancement_versions/   Per-run versioned snapshots
        └── runs/                          Pipeline run outputs
```

---

## Tests

```bash
pytest tests/ -v    # run all
pytest tests/ -q    # quiet
```

| Module | Coverage |
|--------|---------|
| `test_schemas.py` | Asset, Tag, Brief, QA, AoT schema round-trips |
| `test_redaction.py` | PII detection + redaction |
| `test_template_engine.py` | Brief template rendering |
| `test_compliance_policy.py` | URL validator, policy loader, preflight |
| `test_compliance_runtime.py` | Cleanup job, incident handler |
| `test_brand_enchancement.py` | Schemas, merger, renderer, versioning (20 tests) |

---

## Key Constraints

| Rule | Enforced By |
|------|------------|
| No file > 250 lines | `scripts/check_linecount.py` + CI |
| No PII stored or exported | `qa/pii_redaction.py` + QA gate |
| No verbatim competitor copy | `qa/no_copy_checks.py` + QA gate |
| Deterministic enum-only tagging | `core/enums.py` |
| Evidence-first insights | Every insight traces to `asset_id(s)` |
| Client workspace isolation | Strict path separation |
| Secrets in `.env` only | Never logged, never committed |
| LLM always optional | Graceful fallback to heuristics |

---

## Roadmap

- [ ] Additional enhancements coming soon
- [x] Multi-provider LLM Router (OpenAI, Gemini, Anthropic, Mistral)
- [x] Brand Enhancement Engine with incremental versioning
- [x] Live TikTok/Meta/Pinterest collection via Apify
- [x] Compliance suite (preflight, cleanup, incident response)
- [x] CI/CD — ruff lint + pytest matrix (py3.11 + py3.12)
- [x] CrewAI agent pipeline
- [x] QA gate (PII, copy, unsubstantiated claims)
- [x] Weekly scheduler
