MASTER PROMPT — BUILD + MAINTAIN THE FULL “CREATIVE INTELLIGENCE OS” AGENTIC PROJECT (CrewAI)
(UPDATED: MUST auto-update docs after each phase)

You are a senior staff engineer + security reviewer. Build a COMPLETE, runnable, internal mini-SaaS backend project that matches the existing repository docs and folder structure.

CRITICAL CONSTRAINTS (HARD):
1) NO single code file/module/script may exceed 250 lines. If a file approaches 200 lines, split it.
2) Do NOT include any instructions/code for bypassing authentication, CAPTCHAs, anti-bot protections, or ToS evasion.
3) Only use approved collection paths:
   - Official APIs where feasible
   - Apify actors via Apify API (authorized use)
   - Manual CSV import for Ads repositories when needed
4) Evidence-first: every insight/brief claim must be traceable to asset_id(s).
5) Client isolation: strict workspace separation; never mix data across workspaces.
6) No PII storage/output: strip handles/usernames/comments verbatim; store only anonymized themes.
7) No competitor-copy generation: never output competitor copy verbatim; generate original creative only.
8) DOCUMENTATION IS PART OF THE PRODUCT:
   - After EACH phase (Plan, Collect, Analyze, Synthesize, Brief, QA, Export, Scheduler), you MUST update the relevant .md docs:
     - BRAIN.md (run state + decisions)
     - PLAYBOOK.md (any workflow changes)
     - AGENTS.md (if agent responsibilities change)
     - TOOLS.md (if tools/keys/limits change)
     - MEMORY.md + RECURSIVE_LEARNING.md (if prompts/taxonomy/playbooks evolve)
     - ENGINEERING_STANDARDS.md (if structure/rules change)
   - Also write a per-run `runs/<run_id>/phase_notes.md` containing:
     - what was executed
     - artifacts produced
     - errors/uncertainties
     - next actions

PROJECT GOAL:
Combine TikTok + Meta + X + Pinterest into one pipeline:
Collect → Analyze (vision + comments) → Synthesize (clusters + AoT atoms) → Generate Brief → QA Gate → Export
All driven by CrewAI and aligned to the skill specs in /skills_skills/*.md.

YOU MUST USE THESE DOCS AS SOURCE OF TRUTH (READ THEM FIRST):
- SOUL.md, IDENTITY.md, ENGINEERING_STANDARDS.md, TOOLS.md, CLIENTS.md, BRAIN.md, MEMORY.md,
  HEARTBEAT.md, PLAYBOOK.md, VOICE.md, AGENTS.md, ATOM_OF_THOUGHT.md, RECURSIVE_LEARNING.md
- BRIEF_TEMPLATE.md, BRAND_TEMPLATE.md (Brand Bible), QA_POLICY.md
- skills_skills/skill_*.md (all skills including collectors for meta/tiktok/x/pinterest)

DELIVERABLES:
A) A complete Python project implementing the architecture with clean module boundaries.
B) A CLI to run a single workspace pipeline and a scheduler entrypoint for weekly refresh.
C) Minimal local storage (SQLite default) with an option to switch to Postgres later.
D) Deterministic JSON schemas using Pydantic models for:
   - Asset (with workspace_id/run_id/provenance/platform_fields/metrics_extra)
   - Tag (deterministic enums)
   - CommentThemes (anonymized)
   - Clusters/Insights
   - BriefObject
   - QAReport
   - AoTAtom (JSONL)
E) A line-count enforcement tool that fails if any .py file >250 lines.
F) Tests (pytest) for schemas, redaction, and template engine.
G) .env.example + README with setup/run commands.
H) Ensure code composes with CrewAI: Agents + Tasks defined in orchestration/crew.py.
I) A doc-updater utility that appends phase notes to `runs/<run_id>/phase_notes.md` and updates top-level docs when changes occur.

TECH STACK REQUIREMENTS:
- Python 3.11+
- crewai
- pydantic
- python-dotenv
- requests (or httpx)
- tenacity (retries)
- rich (CLI output)
- pytest

REPO STRUCTURE (FOLLOW ENGINEERING_STANDARDS.md; KEEP FILES <250 LOC):
workspace/
  core/
    config.py
    schemas_asset.py
    schemas_tag.py
    schemas_brief.py
    schemas_qa.py
    schemas_aot.py
    enums.py
    logging.py
    errors.py
    utils_hash.py
    utils_urls.py
    utils_time.py
    doc_updater.py
  db/
    sqlite.py
    repo_assets.py
    repo_runs.py
  collectors/
    base.py
    apify_client.py
    tiktok_collector.py
    meta_collector.py
    x_collector.py
    pinterest_collector.py
    csv_importer.py
  analyzers/
    vision_client_base.py
    gemini_client.py (stubbed; real call behind env flags)
    media_analyzer.py
    comment_miner.py
    tagger_rules.py (deterministic mapping helpers)
  synthesis/
    ranking.py
    clustering.py
    insights.py
    aot_writer.py
  briefs/
    template_loader.py
    brief_writer.py
    brief_renderer_md.py
  qa/
    pii_redaction.py
    no_copy_checks.py
    claim_checks.py
    qa_gate.py
  export/
    exporter_json.py
    exporter_md.py
    packager.py
  orchestration/
    crew.py
    pipeline.py
    scheduler.py
  scripts/
    check_linecount.py
  tests/
    test_schemas.py
    test_redaction.py
    test_template_engine.py
  clients/
    sample_client/
      BrandBible.md (copy from BRAND_TEMPLATE.md)
      BriefTemplate.md (copy from BRIEF_TEMPLATE.md)
      CompliancePolicy.md (simple)
      Competitors.yml (simple)
  README.md
  requirements.txt (or pyproject.toml)
  .env.example

PLATFORM COLLECTION RULES:
- TikTok/Meta/Pinterest: use Apify actors via Apify API only (no homegrown scraping).
- X:
  - Preferred: manual CSV import from X Ads Transparency repository (EU/DSA) OR official API for organic posts.
  - Provide x_collector.py with two modes: ads_repository_csv and organic_api (stub if keys missing).
- Pinterest:
  - Prefer repository collection via Apify actor OR manual export if necessary.
- All collectors must:
  - validate URLs against allowlists
  - rate-limit and retry with tenacity
  - return Asset objects with stable asset_id prefixes:
    meta:, tiktok:, x:, pinterest:
  - never store personal identifiers from commenters/creators

PIPELINE CONTRACTS (MUST IMPLEMENT):
0) DOC UPDATE (mandatory at every phase):
   - append to runs/<run_id>/phase_notes.md
   - if code/workflow changed, update relevant top-level docs
1) Plan stage (skill_research_planner.md): create plan.json with budgets.
2) Collect stage: write assets.json + raw_refs.json into clients/<workspace>/runs/<run_id>/
3) Analyze stage:
   - Media analyzer: tags.json from vision model or fallback heuristic tagger
   - Comment miner: comment_themes.json (anonymized). Raw comments must be deleted/never persisted.
4) Synthesize stage:
   - Rank winners by distribution proxy + recency
   - Cluster by (format_type + messaging_angle + hook_tactics + offer_type)
   - Generate insights.md with asset_id references
   - Write AoT ledger JSONL (EVIDENCE/TAG/HYPOTHESIS/DECISION/TEST)
5) Brief stage:
   - Load BrandBible + BriefTemplate from workspace
   - Output brief.md and brief.json
   - Must include: SMP (exactly one), RTBs, Mandatories, 2–4 directions, 10–20 hooks, 3–6 scripts, testing matrix.
6) QA Gate:
   - PII redaction check (fail if found)
   - No-copy check: detect long overlaps with competitor copy/captions; flag and require rewrite
   - Claim risk check: flag medical/financial claims; require “UNKNOWN” or safe phrasing
   - If FAIL: do not export; write qa_report.md + qa_report.json
7) Export:
   - Write json bundle + brief.md
   - Optional: package zip (no raw comments)
8) Scheduler:
   - weekly run per workspace with budgets
   - writes logs + updates docs for scheduler behavior

LLM/VISION CALLS:
- Make external model calls optional behind env flags:
  - If GEMINI_API_KEY missing, use heuristic tagger_rules.py and mark uncertainties.
- For brief writing, if no LLM key, output a “template-filled brief” using insights and deterministic phrasing.

SECURITY IMPLEMENTATION (MUST):
- Secrets only in env vars; never printed.
- URL allowlist validator (Meta Ad Library, TikTok, X, Pinterest, Apify).
- SSRF protection: reject non-http(s), private IP ranges, localhost.
- Output sanitization for markdown (basic).
- Minimal retention: no raw comments stored; only anonymized themes.

LINE COUNT ENFORCEMENT:
- scripts/check_linecount.py scans all *.py and fails if >250 lines.
- Add README command: python scripts/check_linecount.py

WHAT TO GENERATE NOW:
1) Generate all missing code files listed above (ensure each <250 LOC).
2) Generate README.md with setup/run commands and doc-update behavior.
3) Generate .env.example
4) Generate sample_client workspace files.
5) Ensure outputs match schemas and go to runs/<run_id>/.
6) Implement core/doc_updater.py and call it at the start/end of each phase.

STYLE:
- Clean, minimal, production-minded.
- Type hints everywhere.
- Deterministic, auditable outputs.
- When uncertain: set UNKNOWN and add to uncertainties list.
- Do not exceed 250 lines per file.

BEGIN BY:
- Reading and summarizing key constraints from existing md docs (briefly),
- Then generate the codebase file-by-file with correct paths and contents,
- Updating the docs after each phase as specified,
- Finally print a short “how to run” section.

DO NOT:
- Ask clarifying questions.
- Include scraping bypass tactics.
- Put more than 250 lines into any single file.