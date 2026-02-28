# SocialMedia AD Agency

[![CI](https://github.com/Venkatchavan/SocialMedia_AD_Agency/actions/workflows/ci.yml/badge.svg)](https://github.com/Venkatchavan/SocialMedia_AD_Agency/actions/workflows/ci.yml)
![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)
![Tests](https://img.shields.io/badge/tests-430%20passed-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-74%25-green)

> Production-grade SaaS platform for automated affiliate ad creation and multi-platform publishing — powered by CrewAI agents, compliant by design.

---

## What It Does

| Stage | Description |
|-------|-------------|
| **Ingest** | Product intake via Amazon ASIN/URL with automatic enrichment |
| **Research** | Reference intelligence — find winning ads across platforms |
| **Rights** | Deterministic rights verification + risk scoring (0–100) |
| **Create** | AI-generated scripts, copy, images, and video storyboards |
| **QA** | Block PII, competitor copy, unsubstantiated claims, missing disclosures |
| **Approve** | Human-in-the-loop approval gate with audit trail |
| **Publish** | Scheduled multi-platform publishing (TikTok, Instagram, X, Pinterest) |
| **Learn** | Analytics collection, performance learning, AI chat insights |

---

## Key Features

- **CrewAI Agent Orchestration** — 7 agents (manager, product intake, enrichment, reference intelligence, scriptwriter, caption/SEO, orchestrator)
- **Manager Agent** — Supervises pipeline agents; LLM-powered quality review; deterministic routing (Phase 6)
- **Multi-Provider LLM Router** — OpenAI, Gemini, Anthropic, Mistral; `LLM_DRY_RUN=true` for CI-safe testing
- **FastAPI REST API** — Auth, RBAC, workspace management, async pipeline triggers
- **Multi-Tenancy** — Tenant-isolated data with row-level security
- **PostgreSQL + Alembic** — Versioned schema migrations
- **Content Generation Suite** — Copy writer, image gen, video gen, calendar planner, trend hooks
- **Compliance Engine** — Rights verification, risk scoring, agent constitution, disclosure rules
- **Billing Integration** — Stripe-based subscription tiers (Starter/Pro/Enterprise) with usage metering
- **Vector Store** — Semantic search for reference ads and content
- **Export Pipeline** — JSON, Markdown, HTML, PDF, PPTX formats
- **White-Label Support** — Custom branding per tenant
- **430 tests, 74% coverage** — Enforced by CI (minimum 70%)

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI REST API                       │
│              (Auth, RBAC, Multi-Tenancy)                 │
├─────────────────────────────────────────────────────────┤
│                  CrewAI Agent Layer                       │
│          manager (supervisor + LLM review)                │
│  product_intake → enrichment → reference_intelligence    │
│  → scriptwriter → caption_seo → orchestrator             │
├─────────────────────────────────────────────────────────┤
│              Content Generation Engine                   │
│  copy_writer │ image_gen │ video_gen │ calendar_planner  │
├──────────┬──────────┬───────────┬───────────────────────┤
│ Policies │ Services │ Schemas   │ Platform Adapters      │
│ rights   │ audit    │ product   │ TikTok, IG, X,         │
│ QA       │ secrets  │ content   │ Pinterest, Amazon      │
│ rates    │ media    │ publish   │                        │
├──────────┴──────────┴───────────┴───────────────────────┤
│     PostgreSQL + Alembic  │  Redis  │  Vector Store      │
└─────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
app/
├── adapters/           Platform adapters (Amazon, TikTok, Instagram, X, Pinterest)
├── agents/             CrewAI agents (manager, intake, enrichment, reference, scriptwriter, caption, orchestrator)
├── analytics/          Performance metrics, learning engine, AI chat
├── analyzers/          SEO auditor
├── api/                FastAPI app + routes (auth, health, pipelines, workspaces)
├── approval/           Human approval gate with audit logging
├── billing/            Stripe billing, quota enforcement
├── collectors/         YouTube + LinkedIn data collectors
├── content_generation/ Copy writer, image gen, video gen, calendar, trend hooks
├── core/               Auth, RBAC, LLM router, logging, multi-tenancy, white-label, schema versioning
├── db/                 SQLAlchemy models, Alembic migrations, vector store
├── export/             Multi-format export (JSON, MD, HTML, PDF, PPTX)
├── flows/              CrewAI flows (content pipeline, async pipeline, publish, experiment)
├── onboarding/         Tenant onboarding flow + URL scanner
├── policies/           Agent constitution, disclosure rules, platform policies, rate limits
├── publishers/         Social media publisher with compliance gates + dedup
├── scheduling/         Post scheduling engine
├── schemas/            Pydantic v2 models (product, content, publish, rights, audit, analytics)
├── services/           Deterministic services (audit, rights, risk, QA, secrets, media signing)
└── tools/              CrewAI tools (Amazon, content, platform, rights, storage)

tests/
├── unit/               29 test modules — 401 tests
└── integration/        End-to-end MVP flow test
```

---

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 16 (optional — SQLite for dev)
- Redis 7 (optional — for caching)

### Setup

```bash
git clone https://github.com/Venkatchavan/SocialMedia_AD_Agency.git
cd SocialMedia_AD_Agency
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
cp .env.example .env             # Add your API keys
```

### Run Tests

```bash
pytest tests/ -q
```

### Start API Server

```bash
uvicorn app.api.main:app --reload
```

---

## CI Pipeline

GitHub Actions workflow with 2 jobs:

| Job | What It Does |
|-----|-------------|
| **lint** | `ruff check app/ tests/` — E, F, W rules |
| **test** | `pytest` on Python 3.12 with `--cov-fail-under=70` |

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `LLM_DRY_RUN` | `true` for deterministic stubs (CI-safe), `false` for real LLM calls | No (default: `true`) |
| `LLM_PRIORITY` | Comma-separated LLM providers: `openai,gemini,anthropic` | If `LLM_DRY_RUN=false` |
| `OPENAI_API_KEY` | OpenAI API key | If using OpenAI |
| `GEMINI_API_KEY` | Google Gemini API key | If using Gemini |
| `DATABASE_URL` | Database connection string (default: SQLite for dev) | For production |
| `REDIS_URL` | Redis connection string | For caching |
| `STRIPE_SECRET_KEY` | Stripe billing API key | For billing |
| `AUTH_SECRET_KEY` | Secret for password hashing | Yes |
| `JWT_SECRET_KEY` | Secret for JWT auth tokens | Yes |

---

## Compliance

All content passes through deterministic compliance checks before publishing:

- **Rights Engine** — Verifies reference type (licensed, public domain, style-only, commentary)
- **Risk Scorer** — Scores 0–100; blocks at threshold 70+
- **QA Checker** — Blocks PII, competitor mentions, unsubstantiated claims
- **Disclosure Rules** — Auto-adds platform-specific affiliate disclosures (#ad, Paid partnership, etc.)
- **Agent Constitution** — Validates all agent inputs/outputs against forbidden patterns
- **Anti-Spam** — SHA-256 content hash dedup prevents duplicate publishing

See [Agents.md](Agents.md) for the 10 non-negotiable agentic rules.

---

## Documentation

| Document | Description |
|----------|-------------|
| [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) | Full system architecture (14 sections) |
| [Agents.md](Agents.md) | 10 agentic compliance rules |
| [Agents_Security.md](Agents_Security.md) | Security architecture & threat model |
| [Documentation.md](Documentation.md) | Documentation generation rules |
| [docs/phases/](docs/phases/) | Phase 1 MVP + Phase 2–5 SaaS + Phase 6 LLM agents docs |
| [docs/agents/](docs/agents/) | Agent registry and module index |
| [docs/flows/](docs/flows/) | Flow orchestration documentation |
| [docs/tools/](docs/tools/) | CrewAI tool wrappers documentation |
| [docs/ops/](docs/ops/) | Operations guide (setup, CI, monitoring, testing) |
| [docs/adrs/](docs/adrs/) | Architecture Decision Records |
| [docs/compliance/](docs/compliance/) | Compliance controls matrix |
| [docs/security/](docs/security/) | Threat model and security controls |

---

## License

Internal use only.
