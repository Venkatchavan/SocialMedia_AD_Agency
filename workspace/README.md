# Creative Intelligence OS

[![CI](https://github.com/Venkatchavan/SocialMedia_AD_Agency/actions/workflows/ci.yml/badge.svg)](https://github.com/Venkatchavan/SocialMedia_AD_Agency/actions/workflows/ci.yml)

A complete, runnable internal mini-SaaS backend that combines **TikTok + Meta + X + Pinterest** ad research into one pipeline:

**Collect → Analyze → Synthesize → Brief → QA Gate → Export**

Driven by [CrewAI](https://github.com/joaomdmoura/crewAI) agents, aligned to the skill specs in the instruction files.

---

## Quick Start

### 1. Prerequisites
- Python 3.11+
- pip

### 2. Install dependencies
```bash
cd workspace
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env with your API keys:
#   APIFY_TOKEN=...       (required for collection)
#   GEMINI_API_KEY=...    (optional — falls back to heuristic tagger)
#   X_BEARER_TOKEN=...    (optional — X organic API)
```

### 4. Run the pipeline
```bash
# Run with a CSV import
python cli.py run --workspace sample_client --csv path/to/ads.csv

# Run with empty demo (no collection)
python cli.py run --workspace sample_client

# Run via CrewAI agents
python cli.py crew --workspace sample_client
```

### 5. Line-count enforcement
```bash
python scripts/check_linecount.py
# or via CLI:
python cli.py check
```

### 6. Run tests
```bash
pytest tests/ -v
```

### 7. Start weekly scheduler
```bash
python cli.py schedule
```

---

## Project Structure

```
workspace/
├── cli.py                      # CLI entrypoint
├── core/                       # Config, schemas, enums, utils
│   ├── config.py
│   ├── enums.py
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
├── db/                         # SQLite + repositories
│   ├── sqlite.py
│   ├── repo_assets.py
│   └── repo_runs.py
├── collectors/                 # Platform collectors
│   ├── base.py
│   ├── apify_client.py
│   ├── tiktok_collector.py
│   ├── meta_collector.py
│   ├── x_collector.py
│   ├── pinterest_collector.py
│   └── csv_importer.py
├── analyzers/                  # Vision + heuristic tagging
│   ├── vision_client_base.py
│   ├── gemini_client.py
│   ├── media_analyzer.py
│   ├── comment_miner.py
│   └── tagger_rules.py
├── synthesis/                  # Ranking, clustering, insights
│   ├── ranking.py
│   ├── clustering.py
│   ├── insights.py
│   └── aot_writer.py
├── briefs/                     # Brief generation
│   ├── template_loader.py
│   ├── brief_writer.py
│   └── brief_renderer_md.py
├── qa/                         # QA gate
│   ├── pii_redaction.py
│   ├── no_copy_checks.py
│   ├── claim_checks.py
│   └── qa_gate.py
├── export/                     # JSON, MD, zip export
│   ├── exporter_json.py
│   ├── exporter_md.py
│   └── packager.py
├── orchestration/              # CrewAI agents + pipeline
│   ├── crew.py
│   ├── pipeline.py
│   └── scheduler.py
├── scripts/
│   └── check_linecount.py
├── tests/
│   ├── test_schemas.py
│   ├── test_redaction.py
│   └── test_template_engine.py
├── clients/
│   └── sample_client/
│       ├── BrandBible.md
│       ├── BriefTemplate.md
│       ├── CompliancePolicy.md
│       └── Competitors.yml
├── requirements.txt
└── .env.example
```

---

## Pipeline Stages

| # | Stage | Agent | Output |
|---|-------|-------|--------|
| 0 | Doc Update | (auto) | `phase_notes.md` |
| 1 | Plan | Research Planner | `plan.json` |
| 2 | Collect | Platform Collectors | `assets.json`, `raw_refs.json` |
| 3 | Analyze | Media Analyzer + Comment Miner | `tags.json`, `comment_themes.json` |
| 4 | Synthesize | Synthesizer | `clusters.json`, `insights.md`, `aot_ledger.jsonl` |
| 5 | Brief | Brief Writer | `brief.md`, `brief.json` |
| 6 | QA Gate | QA Agent | `qa_report.json` (blocks export on FAIL) |
| 7 | Export | Exporter | JSON bundle + zip |
| 8 | Scheduler | Scheduler | Weekly auto-refresh |

---

## Key Constraints

- **No file > 250 lines** — enforced by `scripts/check_linecount.py`
- **No PII** stored or exported
- **No verbatim competitor copy** — QA gate blocks
- **Deterministic enum-only tagging** — no free-form tags
- **Evidence-first** — every insight traces to `asset_id(s)`
- **Client workspace isolation** — strict separation
- **Secrets in `.env` only** — never logged

---

## Doc-Update Behaviour

After each pipeline phase, the system:
1. Appends to `clients/<workspace>/runs/<run_id>/phase_notes.md`
2. Updates top-level docs (BRAIN.md, PLAYBOOK.md, etc.) when workflow changes

This is implemented in `core/doc_updater.py` and called automatically by `orchestration/pipeline.py`.

---

## License

Internal use only.
