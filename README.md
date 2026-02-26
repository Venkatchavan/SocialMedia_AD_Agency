# SocialMedia AD Agency — Creative Intelligence OS

[![CI](https://github.com/Venkatchavan/SocialMedia_AD_Agency/actions/workflows/ci.yml/badge.svg)](https://github.com/Venkatchavan/SocialMedia_AD_Agency/actions/workflows/ci.yml)

> An automated, multi-platform ad research pipeline that turns raw social data into production-ready creative briefs — driven by AI, compliant by design.

---

## What It Does

| Step | Description |
|------|-------------|
| **Collect** | Pull live ads from TikTok, Meta, Pinterest via Apify |
| **Analyze** | Tag hooks, angles, formats with vision AI (Gemini / OpenAI) |
| **Synthesize** | Cluster winning patterns, extract insights, build AoT atoms |
| **Brand Enhancement** | Auto-update & version the Brand Book with new market signals |
| **Brief** | Generate AI-enriched creative briefs with SMP, RTBs, hooks, scripts |
| **QA Gate** | Block PII, competitor copy, unsubstantiated claims |
| **Export** | JSON bundle + Markdown brief + ZIP for delivery |

---

## Key Features

- **Multi-provider LLM Router** — OpenAI, Gemini, Anthropic, Mistral; priority-ordered via env var
- **Brand Enhancement Engine** — incremental, versioned Brand Book updated from keywords/hashtags each run
- **Compliance Suite** — SSRF guard, per-client policy, preflight gate, retention cleanup, incident response
- **Industry-agnostic** — SaaS, e-commerce, healthcare, fashion, finance, B2B, creators
- **250-line file limit** enforced by CI
- **Fully tested** — test suite across 6 modules

---

## Repo Layout

```
.github/workflows/ci.yml   ← Lint (ruff) + Test (py3.11, py3.12) + Smoke CI
Instrutctions_File/        ← Agent instruction documents (AGENTS.md, Brain.md, …)
workspace/                 ← All Python source, tests, and client data
  cli.py + cli_commands.py ← CLI entry points
  brand_enchancement/      ← Brand Enhancement Engine
  analyzers/               ← LLMRouter + Gemini + media analysis
  briefs/                  ← Brief writer + template loader
  collectors/              ← Apify + TikTok / Meta / Pinterest
  compliance/              ← Preflight, cleanup, incident, policy
  core/                    ← Schemas, config, enums, logging
  db/                      ← SQLite repositories
  export/                  ← JSON + MD + ZIP export
  orchestration/           ← Pipeline, scheduler, CrewAI crew
  qa/                      ← QA gate, PII redaction, claim checks
  synthesis/               ← Clustering, insights, AoT writer
  tests/                   ← Full test suite
  clients/sample_client/   ← Example workspace with Brand_Book.md
```

---

## Quick Start

```bash
cd workspace
pip install -r requirements.txt
cp .env.example .env        # add your API keys
python cli.py run --workspace sample_client
```

See [workspace/README.md](workspace/README.md) for the complete guide including all CLI commands,
Brand Enhancement Engine docs, LLM Router configuration, and compliance reference.

---

## License

Internal use only.
