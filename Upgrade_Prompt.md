# UPGRADES.md

## Mission
Transform **Creative Intelligence OS** from a local CLI research tool into a **production-grade SaaS** that closes the full loop: **Collect → Analyze → Generate → Publish → Learn**.

## North Star
```
Competitor Ads → Creative Intel → AI Content → Human Approval → Auto-Publish → Real Metrics → Learn
       ↑                                                                                    ↓
       └──────────────────────── Recursive Performance Learning ────────────────────────────┘
```

## Current State → Shipping State

| Dimension | Current | Required |
|---|---|---|
| Interface | CLI only | Web dashboard + REST API |
| Auth | None | JWT / OAuth2 / SSO + RBAC |
| Multi-tenancy | Manual workspace folders | Isolated per-client DB + storage |
| Billing | None | Stripe subscription tiers |
| Deployment | Manual `pip install` | Docker + cloud infra + CI/CD |
| Monitoring | Basic Python logs | Structured logs + alerts + uptime |
| Data safety | SQLite, no backups | PostgreSQL + automated backups |
| Client delivery | ZIP file | Web UI, PDF, PPTX, shareable link |
| Onboarding | README + manual | Self-serve onboarding flow |
| Security | .env secrets | Vault, RBAC, audit log, encrypted PII |
| Publishing | Stops at brief | AI-generate + auto-post all platforms |
| Learning | Market averages only | Real metrics feedback per client |
| SEO/GEO | None | Brand visibility audit (AI search engines) |
| Video | None | AI short-form video pipeline |

## Non-Negotiables (Hard Rules)
1. Evidence-first: no insight without traceable asset IDs.
2. Client isolation: never mix data across workspaces.
3. Privacy safe: no PII storage or output.
4. Original output: never copy competitor creative verbatim.
5. Compliance safe: no bypassing platform security or ToS.
6. **No single code file/module/script > 250 lines.** Split into small, testable modules.
7. Human approval gate before any auto-publish. No exceptions.
8. All OAuth tokens AES-256 encrypted at rest.
9. Every upgrade must include tests. No untested code ships.

---

## Competitive Intelligence (Reddit / X Research)

Sources analyzed to identify integrable improvements from builders who shipped similar products:

### Similar Products Found
| Product | What They Do | Revenue/Traction | Key Differentiator |
|---|---|---|---|
| **Luce.sh** | Full growth marketing AI: SEO audit, GEO, competitor ad spy, content gen, 12-week calendar | Early-stage, users 5x'd monthly new users | Single-URL onboarding, AI assistant chat over growth data |
| **PostPlanify** | Social media scheduler | $900→$20k MRR in months | Simple scheduling + distribution focus |
| **Creatives Hub** | AI ad creative generator (images+copy) | Early launch, 6 upvotes | Non-designer focus, platform-optimized outputs |
| **Content Automation Engine** | Script→voiceover→images→effects→video pipeline | Personal use (not monetized) | Claude Sonnet + ElevenLabs + Stability.ai + MoviePy |
| **Buffer / Later / Hootsuite** | Legacy schedulers | $10M+ ARR | Multi-platform scheduling, analytics |

### Integrable Improvements Identified
| # | Improvement | Source | Integration Point |
|---|---|---|---|
| I-1 | SEO/GEO audit — check brand visibility on ChatGPT, Perplexity, Google AI Overview | Luce.sh | New `analyzers/seo_auditor.py` module |
| I-2 | Canonical tag + H1 + title tag validation before content goes live | Reddit feedback on Luce.sh | `qa/` pre-publish checks |
| I-3 | 12-week growth calendar generation from brief data | Luce.sh | `briefs/calendar_planner.py` |
| I-4 | Trend-aware hook generation (current formats feel "old-school" per user feedback) | Reddit thread on content automation | `content_generation/trend_hooks.py` — scrape trending formats |
| I-5 | ElevenLabs voiceover integration for video ads | Content automation engine builder | `content_generation/voiceover.py` |
| I-6 | Multi-format video pipeline: script→voice→images→effects→captions→video | Content automation engineer (MoviePy + FFmpeg) | `content_generation/video_gen.py` |
| I-7 | Single-URL brand deep-dive onboarding (drop URL → auto-analyze) | Luce.sh | `onboarding/url_scanner.py` |
| I-8 | AI assistant chat over growth/analytics data | Luce.sh | `api/routes/chat.py` — RAG over metrics |
| I-9 | Best-time-to-post optimization from real engagement data | PostPlanify, Buffer | `analytics/best_time.py` |
| I-10 | Platform-native preview rendering (show exactly how post will appear) | Creatives Hub | `dashboard/preview_renderer.py` |

---

## Pipeline: Extended Stages

Original pipeline + new stages (8–12) for full-loop operation:

```
Stage 1  — Plan              (existing)
Stage 2  — Collect            (existing + YouTube + LinkedIn collectors)
Stage 3  — Analyze Media      (existing + SEO/GEO audit)
Stage 4  — Comment Mining     (existing)
Stage 5  — Synthesize         (existing + performance-weighted scoring)
Stage 6  — Brief              (existing + 12-week calendar)
Stage 7  — QA Gate            (existing + pre-publish checks)
Stage 8  — Content Generate   (NEW: copy + image + video + voiceover)
Stage 9  — Human Approval     (NEW: review UI, edit, approve/reject)
Stage 10 — Publish            (NEW: platform API posting + scheduling)
Stage 11 — Metrics Pull       (NEW: 6h/24h/72h post-publish metrics)
Stage 12 — Recursive Learn    (ENHANCED: real metrics → pattern re-scoring)
```

---

## Upgrade Registry

### U-1: Fix Module Typo
- **Priority:** CRITICAL | **Effort:** LOW
- `brand_enchancement/` → `brand_enhancement/`
- Global find-replace across all `.py`, `.md`, `.yml`, `.yaml`
- Re-run `pytest` to confirm no broken imports
- **Do this first. Cost increases exponentially with codebase age.**

### U-2: Auth + RBAC
- **Priority:** CRITICAL | **Effort:** MEDIUM
- JWT access tokens + refresh tokens
- Role model: `owner | admin | editor | viewer`
- Per-workspace role binding
- SSO support (Google OAuth2 initially)
- Middleware: `require_role("editor")` on all mutation endpoints
- Store hashed passwords (bcrypt), never plain text

### U-3: Multi-Tenancy Architecture
- **Priority:** CRITICAL | **Effort:** HIGH
- Row-level security (PostgreSQL RLS) per `workspace_id`
- Isolated file storage: `s3://{bucket}/{workspace_id}/...`
- Cross-workspace leakage = QA FAIL (per QA_POLICY.md)
- Connection pooling: separate pools per tenant tier

### U-4: FastAPI Web Layer
- **Priority:** HIGH | **Effort:** MEDIUM

API surface:
```
POST   /api/run                         → trigger full pipeline
POST   /api/collect                     → collect ads
POST   /api/enhance-brand               → update Brand Book
GET    /api/briefs/{workspace}           → list briefs
GET    /api/briefs/{workspace}/{run_id}  → brief detail
GET    /api/brand/{workspace}            → Brand Book
POST   /api/preflight/{workspace}       → compliance preflight
GET    /api/runs/{workspace}             → run history
POST   /api/incident                     → log incident
GET    /api/content/{workspace}          → pending content for approval
POST   /api/content/{id}/approve         → approve + schedule
POST   /api/content/{id}/reject          → discard
GET    /api/calendar/{workspace}         → content calendar
GET    /api/analytics/{workspace}        → performance dashboard data
POST   /api/chat/{workspace}             → AI assistant (RAG over metrics)
```

Stack:
```
FastAPI + Uvicorn       → REST API server
Pydantic (existing)     → request/response validation
BackgroundTasks         → non-blocking pipeline runs
```

### U-5: Upgrade LLM Model Defaults
- **Priority:** HIGH | **Effort:** LOW

| Provider | Current | Recommended | Reason |
|---|---|---|---|
| OpenAI | `gpt-4o-mini` | `gpt-4o` | Better reasoning for briefs |
| Anthropic | `claude-3-haiku` | `claude-3-5-sonnet` | 2x quality, similar speed |
| Gemini | `gemini-2.0-flash` | `gemini-2.0-flash-thinking-exp` | Chain-of-thought for synthesis |
| Mistral | `mistral-small` | `mistral-large` | Higher quality for production |

- Add `USE_PREMIUM_MODELS` env flag for cost control
- Default: false (keeps budget models for dev/test)

### U-6: Add YouTube & LinkedIn Collectors
- **Priority:** MEDIUM | **Effort:** MEDIUM
- YouTube: Data API v3, `search.list` (type=video, videoDuration=short)
- LinkedIn: Marketing API v2, `/adAnalytics` + `/creatives`
- Register in Platform enum: `YOUTUBE = "youtube"`, `LINKEDIN = "linkedin"`
- Both require API keys in `.env`
- Follow existing collector pattern in `collectors/`

### U-7: Async Pipeline Execution
- **Priority:** HIGH | **Effort:** MEDIUM

Current: sequential → ~120s per run
Proposed: concurrent analysis + comment mining → ~45s (60% reduction)

```
Collect ─┬─→ Analyze (per asset, concurrent) ─┬─→ Synthesize → Brief
          └─→ Comment Mining (concurrent)      ┘
```

- Semaphore guard: max 5 concurrent LLM calls to avoid rate limits
- `asyncio.gather()` for parallel asset analysis

### U-8: PostgreSQL + Alembic
- **Priority:** HIGH | **Effort:** HIGH
- SQLAlchemy 2.0 (async) + asyncpg driver
- Alembic for schema migrations
- Connection pooling: `pool_size=10, max_overflow=20`
- Migrate when: 3+ workspaces or cloud deployment or FastAPI added
- Docker Compose includes Postgres 16

### U-9: Docker & Docker Compose
- **Priority:** CRITICAL | **Effort:** LOW

```yaml
services:
  pipeline:
    build: .
    env_file: workspace/.env
    volumes:
      - ./workspace/clients:/app/clients
    depends_on: [db]
  db:
    image: postgres:16-alpine
    volumes: [pgdata:/var/lib/postgresql/data]
  api:
    build: .
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000
    ports: ["8000:8000"]
    depends_on: [db]
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
```

### U-10: Vector DB for Semantic Ad Search
- **Priority:** MEDIUM | **Effort:** HIGH
- ChromaDB (local, no infra) or Qdrant (production)
- Index: AoT atoms, insights, hook patterns, generated content performance
- Query: "fear-based hooks in SaaS vertical" → returns matching ads + performance data
- CLI: `python cli.py search --workspace X --query "..."`

### U-11: Structured Logging & Observability
- **Priority:** HIGH | **Effort:** MEDIUM
- `structlog` → JSON log output (parseable by Datadog/Grafana/Loki)
- OpenTelemetry → distributed tracing per pipeline stage
- Prometheus client → `/metrics` endpoint
- Sentry → error tracking + alerting
- Per-stage trace IDs, LLM latency tracking, QA fail rate metrics

### U-12: Richer Brief Export Formats
- **Priority:** HIGH | **Effort:** MEDIUM
- Add PPTX: `python-pptx` (slides: overview, hooks, scripts, brand voice, visuals)
- Add PDF: `weasyprint` (styled HTML→PDF)
- Add HTML: single-page styled brief viewer with brand colors
- Add shareable link: S3/R2 hosted, expiring URL
- CLI: `python cli.py run --workspace X --export pptx,pdf,html,zip`

### U-13: Expand Test Coverage
- **Priority:** HIGH | **Effort:** MEDIUM
- Target: 75% coverage minimum
- **Coverage gaps requiring tests:**

| Module | Tests Needed |
|---|---|
| `collectors/apify_client.py` | Mock Apify HTTP responses |
| `collectors/tiktok_collector.py` | Fixture-based unit tests |
| `orchestration/pipeline.py` | End-to-end smoke test |
| `synthesis/clustering.py` | Property-based tests (`hypothesis`) |
| `analyzers/llm_router.py` | All 4 provider failure permutations |
| `briefs/brief_writer.py` | LLM-off heuristic fallback |
| `export/packager.py` | ZIP integrity |
| `content_generation/*` | Caption gen, image prompt, publish flow |
| `publishers/*` | Mock API responses per platform |

- Add to CI: `pytest --cov=workspace --cov-fail-under=70`

### U-14: Schema Versioning & Migrations
- **Priority:** HIGH | **Effort:** MEDIUM
- Add `schema_version` field to `BrandBibleDoc` and all JSON schemas
- Migration runner: sequential transforms `v1→v2→v3`
- Auto-migrate on load: `load_and_migrate(path)` checks version, runs upgrades
- Prevents silent data corruption from schema drift

### U-15: Stripe Billing + Usage Quotas
- **Priority:** HIGH | **Effort:** MEDIUM

| Plan | Price | Runs/mo | Posts/mo | Platforms |
|---|---|---|---|---|
| Starter | $149/mo | 20 | 10 | 2 |
| Pro | $499/mo | 100 | 50 | All |
| Enterprise | $1,499/mo | Unlimited | Unlimited | All + video + white-label |

- Stripe Checkout for subscription
- Usage metering: count runs, posts, LLM tokens per workspace per billing cycle
- Overage blocking or overage billing (configurable per plan)

### U-16: Self-Serve Onboarding Flow
- **Priority:** HIGH | **Effort:** MEDIUM
- Step 1: Sign up (email/Google OAuth)
- Step 2: Drop your brand URL → auto-scan website, extract brand info (I-7)
- Step 3: Review auto-generated Brand Book → edit inline
- Step 4: Connect social accounts (OAuth per platform)
- Step 5: First pipeline run → see brief in <5 minutes

### U-17: White-Labeling Support
- **Priority:** MEDIUM | **Effort:** MEDIUM
- Custom domain per agency (CNAME)
- Custom logo, colors, email templates
- `white_label_config` per workspace
- Remove all "Creative Intelligence OS" branding in client-facing views
- Export PDFs/PPTXs use agency branding

### U-18: SEO/GEO Audit Module (I-1, from Luce.sh)
- **Priority:** MEDIUM | **Effort:** MEDIUM
- New module: `analyzers/seo_auditor.py`
- Capabilities:
  - 60+ on-page SEO metrics (H1, title, meta, canonical, structured data)
  - GEO check: how brand appears in ChatGPT, Perplexity, Google AI Overview
  - Competitor SEO comparison
  - Canonical tag validation (I-2 — prevents link authority fragmentation)
- Output: `seo_audit.json` + `seo_audit.md`
- Feeds into brief: "Your brand is invisible on AI search — here's how to fix it"

### U-19: 12-Week Growth Calendar (I-3, from Luce.sh)
- **Priority:** MEDIUM | **Effort:** MEDIUM
- New module: `briefs/calendar_planner.py`
- Auto-generates from brief data:
  - Weekly content themes
  - Platform-specific post schedule
  - Hook rotation plan
  - Offer cadence (avoid offer fatigue)
  - A/B test schedule
- Output: `growth_calendar.json` + `growth_calendar.md`
- Feeds into content calendar view (U-26)

### U-20: Trend-Aware Hook Generation (I-4, from Reddit feedback)
- **Priority:** HIGH | **Effort:** MEDIUM
- Problem: AI-generated content uses "old-school marketing styles" and misses current trends
- Solution: `content_generation/trend_hooks.py`
  - Scrape trending audio/formats from TikTok and Instagram Reels
  - Cross-reference with brand voice constraints
  - Generate hooks that match current platform culture, not textbook marketing
  - Update weekly via HEARTBEAT.md cycle
- Key learning from Reddit: "If AI-generated scripts stick too much to traditional marketing styles, they might not resonate"

---

## Stage 8 — Content Generation (Full Spec)

### U-21: AI Copy & Caption Generation
- **Priority:** HIGH | **Effort:** LOW
- Already possible with existing LLM Router
- Platform-specific rules:

| Platform | Max Chars | Hashtags | Tone |
|---|---|---|---|
| Instagram Feed | 2,200 | 5–10 | Brand voice |
| Instagram Reels | 2,200 | 3–5 | Punchy, hook-first |
| TikTok | 2,200 | 3–5 | Casual, trend-aware |
| LinkedIn | 3,000 | 3–5 | Professional |
| X / Twitter | 280 | 1–2 | Concise |
| Pinterest | 500 | 2–4 | Descriptive |
| YouTube Shorts | 5,000 | 3–5 | Searchable |

- Module: `content_generation/copy_writer.py`
- Input: `BriefDoc` + `BrandBibleDoc` + `Platform`
- Output: `GeneratedCaption` (caption, hashtags, CTA)

### U-22: AI Image Generation
- **Priority:** HIGH | **Effort:** MEDIUM
- Module: `content_generation/image_gen.py`
- Providers (configurable): DALL-E 3 | Stable Diffusion | Ideogram | Flux
- Input: brief visual direction + brand visual style from Brand Book
- Output: image URL + metadata
- Env: `IMAGE_PROVIDER=dalle3`, `DALLE_API_KEY=...`

### U-23: AI Video Pipeline (I-5, I-6, from content automation builder)
- **Priority:** MEDIUM | **Effort:** HIGH
- Module: `content_generation/video_gen.py` + `content_generation/voiceover.py`
- Pipeline:
```
Script (from brief) → ElevenLabs voiceover → Stability.ai images → MoviePy+FFmpeg assembly → Captions → Output .mp4
```
- Providers:
  - Voice: ElevenLabs (I-5)
  - Images: Stability.ai / DALL-E 3
  - Video assembly: MoviePy + FFmpeg (I-6)
  - Full video gen alternative: Runway ML / Kling AI / Pika Labs
- Output: 15s / 30s / 60s .mp4 files
- Env: `VIDEO_PROVIDER=runway`, `VOICE_PROVIDER=elevenlabs`

---

## Stage 9 — Human Approval Gate

### U-24: Content Review & Approval
- **Priority:** CRITICAL | **Effort:** MEDIUM
- **Non-negotiable: nothing auto-publishes without human approval.**

Flow:
```
Pipeline complete → AI generates content → "Ready for Review" notification
    → Client opens dashboard → Content Review screen
    → Preview (platform-native rendering, I-10)
    → Edit caption / replace image inline
    → [✅ Approve & Schedule]  [✏️ Edit]  [❌ Reject]
    → Approved → Publishing queue → Posts at scheduled time
```

API:
```
GET    /workspaces/{id}/content               → list pending
GET    /workspaces/{id}/content/{cid}         → preview
PATCH  /workspaces/{id}/content/{cid}         → edit
POST   /workspaces/{id}/content/{cid}/approve → schedule
POST   /workspaces/{id}/content/{cid}/reject  → discard
POST   /workspaces/{id}/content/{cid}/publish-now → immediate
```

---

## Stage 10 — Publish

### U-25: Platform Publishing APIs
- **Priority:** HIGH | **Effort:** HIGH

| Platform | API | Post Types |
|---|---|---|
| Meta (Instagram) | Graph API v21 | Feed, Reels, Stories, Carousels |
| Meta (Facebook) | Graph API v21 | Feed, video, link posts |
| TikTok | Content Posting API | Videos, photo posts |
| LinkedIn | Marketing API v2 | Posts, images, videos |
| Pinterest | API v5 | Pins, Idea Pins |
| X / Twitter | API v2 | Tweets, threads, images, videos |
| YouTube | Data API v3 | Shorts, standard videos |

- OAuth token storage per workspace, per platform (AES-256 encrypted)
- Publisher pattern: `SocialPublisher(ABC)` → per-platform implementations
- Module: `publishers/{platform}.py`

### U-26: Scheduling Queue + Content Calendar
- **Priority:** HIGH | **Effort:** MEDIUM
- Redis + APScheduler for scheduled publishing
- Best-time-to-post optimization from real engagement data (I-9)
- Content calendar dashboard view:
```
🟡 = Pending approval   🟢 = Scheduled   🔵 = Published   🔴 = Failed
```
- Module: `orchestration/publisher_queue.py`

### U-27: Platform API Approval Warning
> **CRITICAL LEAD-TIME ITEM:** TikTok and Meta require **app review** before posting on behalf of users. This takes **2–6 weeks**. Start immediately, even if Phase 5 is months away.

| Platform | App Review Required | Wait Time |
|---|---|---|
| Meta (IG/FB) | Yes | 1–3 weeks |
| TikTok | Yes | 2–6 weeks |
| LinkedIn | Yes | 1–2 weeks |
| Pinterest | Yes | 1–2 weeks |
| X / Twitter | Yes (Elevated) | 1–2 weeks |
| YouTube | No (standard OAuth) | Instant |

---

## Stage 11 — Metrics Pull

### U-28: Performance Metrics Feedback
- **Priority:** HIGH | **Effort:** MEDIUM
- Module: `analytics/metrics_puller.py`
- Schedule: pull at 6h, 24h, 72h post-publish
- Metrics per platform:
  - Instagram: reach, impressions, likes, comments, saves, shares, profile visits
  - TikTok: views, likes, comments, shares, watch time, completion rate
  - LinkedIn: impressions, clicks, reactions, shares, CTR
  - Pinterest: impressions, saves, clicks, outbound clicks
  - X: impressions, likes, retweets, replies, link clicks
  - YouTube: views, likes, comments, watch time, CTR

---

## Stage 12 — Enhanced Recursive Learning

### U-29: Performance-Weighted Pattern Scoring
- **Priority:** HIGH | **Effort:** MEDIUM
- Module: `synthesis/performance_learner.py`
- After real metrics arrive, re-score hook/angle/format patterns
- Top 10% performing posts → reinforce patterns (+0.1 score delta)
- Bottom 10% → penalize patterns (-0.05 score delta)
- This means the system gets **smarter about each specific client's audience** over time
- Feeds back into Stage 5 (Synthesize) cluster weights

### U-30: AI Chat Over Analytics Data (I-8, from Luce.sh)
- **Priority:** MEDIUM | **Effort:** MEDIUM
- Module: `api/routes/chat.py`
- RAG over: run history, metrics, AoT atoms, insights, brief outputs
- Query: "What hooks worked best for us on Instagram last month?"
- Uses existing LLM Router + vector store (U-10)

---

## Shared Output Envelope (All New Modules)
```json
{
  "status": "ok|warn|fail",
  "evidence_assets": ["asset_id..."],
  "output": {},
  "uncertainties": [],
  "next_actions": []
}
```

## Code Size Rule
All implementations: **no single code file > 250 lines.** Split into modules.

---

## New Environment Variables

```env
# LLM (existing, upgraded)
USE_PREMIUM_MODELS=false

# Image generation (U-22)
IMAGE_PROVIDER=dalle3
DALLE_API_KEY=...
STABILITY_API_KEY=...

# Video generation (U-23)
VIDEO_PROVIDER=runway
RUNWAY_API_KEY=...
VOICE_PROVIDER=elevenlabs
ELEVENLABS_API_KEY=...

# New platform collectors (U-6)
YOUTUBE_API_KEY=...
LINKEDIN_CLIENT_ID=...
LINKEDIN_CLIENT_SECRET=...
LINKEDIN_ACCESS_TOKEN=...

# Database (U-8)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/socialmedia_ad

# Redis (U-26)
REDIS_URL=redis://localhost:6379/0

# Billing (U-15)
STRIPE_SECRET_KEY=...
STRIPE_WEBHOOK_SECRET=...

# Observability (U-11)
SENTRY_DSN=...

# Publishing (OAuth tokens stored in DB per workspace — connected via dashboard)
```

## New Dependencies

```txt
# API layer
fastapi>=0.115
uvicorn>=0.34
python-jose[cryptography]>=3.3    # JWT
passlib[bcrypt]>=1.7              # password hashing

# Database
sqlalchemy[asyncio]>=2.0
asyncpg>=0.30
alembic>=1.14

# Export
python-pptx>=1.0
weasyprint>=62

# Content generation
openai>=1.50              # DALL-E 3 + GPT-4o
elevenlabs>=1.0           # voiceover
moviepy>=2.0              # video assembly
ffmpeg-python>=0.2        # video processing
pillow>=10.0              # image processing

# Publishing
apscheduler>=3.10         # scheduled posting queue
aiohttp>=3.9              # async HTTP for publisher APIs
redis>=5.0                # publishing queue backend

# Observability
structlog>=24.0
sentry-sdk[fastapi]>=2.0
opentelemetry-api>=1.25
prometheus-client>=0.21

# Vector DB
chromadb>=0.5

# Testing
pytest-cov>=5.0
pytest-asyncio>=0.24
hypothesis>=6.100
respx>=0.21               # mock async HTTP
```

---

## CI/CD Pipeline Alignment

Current CI (`.github/workflows/ci.yml`):
```
Job 1: Lint (ruff) → ruff check workspace/ --select E,F,W --ignore E501
Job 2: Tests (py3.11, py3.12) → line-count enforcement + pytest
Job 3: Smoke test → demo pipeline + CSV pipeline + scheduler + crew + preflight + cleanup + incident
```

### Required CI Additions

```yaml
# Add to Job 2 (test):
- name: Run tests with coverage
  run: pytest tests/ --cov=workspace --cov-report=xml --cov-fail-under=70

# Add new Job 4 (Docker build):
docker:
  name: Docker build
  runs-on: ubuntu-latest
  needs: test
  steps:
    - uses: actions/checkout@v4
    - name: Build Docker image
      run: docker build -t socialmedia-ad-agency .
    - name: Run container smoke test
      run: |
        docker run --rm socialmedia-ad-agency python cli.py preflight --workspace sample_client

# Add new Job 5 (API tests — when FastAPI added):
api-test:
  name: API integration tests
  runs-on: ubuntu-latest
  needs: test
  services:
    postgres:
      image: postgres:16-alpine
      env:
        POSTGRES_DB: test_db
        POSTGRES_USER: test
        POSTGRES_PASSWORD: test
      ports: ["5432:5432"]
    redis:
      image: redis:7-alpine
      ports: ["6379:6379"]
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: "3.12"
    - name: Install dependencies
      run: pip install -r workspace/requirements.txt
    - name: Run API tests
      working-directory: workspace
      run: pytest tests/test_api/ -v --tb=short

# Add new Job 6 (publisher dry-run — when publishers added):
publish-dry-run:
  name: Publisher dry-run (mock APIs)
  runs-on: ubuntu-latest
  needs: test
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: "3.12"
    - name: Install dependencies
      run: pip install -r workspace/requirements.txt
    - name: Test publish flow (mocked)
      working-directory: workspace
      run: pytest tests/test_publishers/ -v --tb=short -k "mock"
```

### Line-Count Enforcement
All new modules must pass `scripts/check_linecount.py` (250-line max). This is enforced in CI Job 2.

New directories that need line-count scanning:
```
content_generation/
publishers/
analytics/
onboarding/
api/
```

---

## Repo Structure (Extended)

```
workspace/
  core/
    config.py
    schemas.py
    schemas_social.py          # NEW: social connection schemas
    logging.py
    errors.py
    utils.py
    auth.py                    # NEW: JWT + RBAC
    billing.py                 # NEW: Stripe integration
  collectors/
    tiktok_client.py
    meta_client.py
    youtube_collector.py       # NEW (U-6)
    linkedin_collector.py      # NEW (U-6)
  analyzers/
    media_analyzer.py
    comment_miner.py
    tagger.py
    llm_router.py
    seo_auditor.py             # NEW (U-18)
  synthesis/
    clustering.py
    insights.py
    performance_learner.py     # NEW (U-29)
  briefs/
    template_engine.py
    brief_writer.py
    calendar_planner.py        # NEW (U-19)
  content_generation/          # NEW (Stage 8)
    copy_writer.py             # U-21
    image_gen.py               # U-22
    video_gen.py               # U-23
    voiceover.py               # U-23
    trend_hooks.py             # U-20
  publishers/                  # NEW (Stage 10)
    base.py
    instagram.py
    facebook.py
    tiktok.py
    linkedin.py
    pinterest.py
    twitter.py
    youtube.py
  analytics/                   # NEW (Stage 11)
    metrics_puller.py          # U-28
    best_time.py               # U-26
  onboarding/                  # NEW
    url_scanner.py             # U-16
  qa/
    pii_redaction.py
    claim_checks.py
    no_copy_checks.py
    pre_publish_checks.py      # NEW: canonical tag validation, etc.
  export/
    exporter_md.py
    exporter_json.py
    exporter_pptx.py           # NEW (U-12)
    exporter_pdf.py            # NEW (U-12)
    exporter_html.py           # NEW (U-12)
  orchestration/
    crew.py
    scheduler.py
    pipeline.py
    publisher_queue.py         # NEW (U-26)
  compliance/
    ssrf_guard.py
    policy_engine.py
    preflight.py
    cleanup.py
    incident.py
  db/
    sqlite.py
    engine.py                  # NEW: PostgreSQL (U-8)
    vector_store.py            # NEW (U-10)
  api/                         # NEW (U-4)
    main.py
    routes/
      run.py
      briefs.py
      brand.py
      content.py               # review + approval
      calendar.py
      analytics.py
      chat.py                  # U-30
      auth.py
      billing.py
  tests/
    test_schemas.py
    test_redaction.py
    test_template_engine.py
    test_compliance_policy.py
    test_compliance_runtime.py
    test_brand_enchancement.py
    test_collectors.py         # NEW
    test_pipeline_smoke.py     # NEW
    test_llm_router.py         # NEW
    test_clustering.py         # NEW
    test_exporters.py          # NEW
    test_content_gen.py        # NEW
    test_publishers/           # NEW
    test_api/                  # NEW
```

---

## Priority Summary

| # | Upgrade | Priority | Effort | Phase |
|---|---|---|---|---|
| U-1 | Fix `enchancement` typo | CRITICAL | LOW | 1 |
| U-2 | Auth + RBAC | CRITICAL | MEDIUM | 1 |
| U-3 | Multi-tenancy | CRITICAL | HIGH | 1 |
| U-9 | Docker + Compose | CRITICAL | LOW | 1 |
| U-24 | Human approval gate | CRITICAL | MEDIUM | 5 |
| U-4 | FastAPI REST API | HIGH | MEDIUM | 2 |
| U-5 | Upgrade LLM defaults | HIGH | LOW | 1 |
| U-7 | Async pipeline | HIGH | MEDIUM | 2 |
| U-8 | PostgreSQL + Alembic | HIGH | HIGH | 1 |
| U-11 | Structured logging + Sentry | HIGH | MEDIUM | 2 |
| U-12 | PPTX + PDF exports | HIGH | MEDIUM | 3 |
| U-13 | Expand test coverage 75% | HIGH | MEDIUM | 2 |
| U-14 | Schema versioning | HIGH | MEDIUM | 2 |
| U-15 | Stripe billing | HIGH | MEDIUM | 3 |
| U-16 | Self-serve onboarding | HIGH | MEDIUM | 3 |
| U-20 | Trend-aware hooks | HIGH | MEDIUM | 4 |
| U-21 | AI copy/caption gen | HIGH | LOW | 5 |
| U-22 | AI image gen | HIGH | MEDIUM | 5 |
| U-25 | Platform publishing APIs | HIGH | HIGH | 5 |
| U-26 | Scheduling queue + calendar | HIGH | MEDIUM | 5 |
| U-28 | Performance metrics pull | HIGH | MEDIUM | 5 |
| U-29 | Performance-weighted learning | HIGH | MEDIUM | 5 |
| U-6 | YouTube + LinkedIn collectors | MEDIUM | MEDIUM | 3 |
| U-10 | Vector DB (ChromaDB) | MEDIUM | HIGH | 4 |
| U-17 | White-labeling | MEDIUM | MEDIUM | 4 |
| U-18 | SEO/GEO audit | MEDIUM | MEDIUM | 4 |
| U-19 | 12-week growth calendar | MEDIUM | MEDIUM | 4 |
| U-23 | AI video pipeline | MEDIUM | HIGH | 5 |
| U-27 | Platform API approvals | N/A | N/A | START NOW |
| U-30 | AI chat over analytics | MEDIUM | MEDIUM | 5 |

---

## Shipping Phases

```
Phase 1 — Foundation     (Weeks 1–3)    U-1, U-2, U-3, U-5, U-8, U-9
Phase 2 — Product        (Weeks 4–7)    U-4, U-7, U-11, U-13, U-14
Phase 3 — Client-Facing  (Weeks 8–12)   U-6, U-12, U-15, U-16
Phase 4 — Scale          (Weeks 13–20)  U-10, U-17, U-18, U-19, U-20
Phase 5 — Full Loop      (Weeks 21–30)  U-21–U-30 (generate, approve, publish, learn)
```

## Quick Wins (Do This Week)

```
1. Fix spelling typo             → 30 min, zero risk
2. Add Dockerfile                → 2 hours, unlocks deployment
3. Upgrade LLM defaults          → 20 min, better briefs immediately
4. Add Sentry error tracking     → 1 hour, know about bugs before clients
5. Submit TikTok + Meta app review → 2 hours, 2–6 week wait starts NOW
```

Item 5 is the most time-sensitive — platform API approvals have mandatory waiting periods. Start immediately even if Phase 5 is months away.

---

## Testing Baselines (per ENGINEERING_STANDARDS.md)
- Unit tests for: schemas, tagger, redaction, template engine, copy writer, publishers (mocked)
- Golden-set regression test for tagging + brief sections
- Mock collectors for CI (no live scraping in tests)
- Mock publishers for CI (no live posting in tests)
- Property-based tests for clustering (hypothesis)
- 75% coverage minimum enforced in CI

## Security Baselines (per ENGINEERING_STANDARDS.md)
- Secrets in env vars only (never logs)
- URL allowlist + SSRF protections (existing)
- Output sanitization (XSS-safe rendering)
- Least privilege DB roles
- OAuth tokens AES-256 encrypted at rest
- RBAC enforcement on all mutation endpoints
- Cross-workspace leakage = QA FAIL


*Last updated: February 28, 2026*
