# Operations Guide

## Quick Start

```bash
# 1. Clone
git clone https://github.com/Venkatchavan/SocialMedia_AD_Agency.git
cd SocialMedia_AD_Agency

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # Linux/macOS

# 3. Install dependencies
pip install -e ".[dev]"

# 4. Set environment variables (see below)

# 5. Run database migrations
alembic upgrade head

# 6. Start the API server
uvicorn app.api.main:app --reload --port 8000

# 7. Run tests
pytest --cov=app --cov-fail-under=70
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for LLM calls |
| `AWS_ACCESS_KEY_ID` | Yes | AWS credentials for S3 + PA-API |
| `AWS_SECRET_ACCESS_KEY` | Yes | AWS secret key |
| `AWS_DEFAULT_REGION` | No | AWS region (default: `us-east-1`) |
| `AMAZON_ASSOCIATE_TAG` | Yes | Amazon affiliate tag |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | No | Redis URL for caching/queues |
| `STRIPE_API_KEY` | No | Stripe billing integration |
| `JWT_SECRET_KEY` | Yes | JWT signing secret |
| `MEDIA_BUCKET` | Yes | S3 bucket for media assets |
| `LOG_LEVEL` | No | Logging level (default: `INFO`) |

All secrets must be loaded from a secrets manager in production — never stored in code or logs (Rule 6).

---

## CI Pipeline

GitHub Actions runs on every push and PR to `main`:

| Job | Steps |
|-----|-------|
| **Lint** | `ruff check app/ tests/` — enforces E, F, W rules (E501 ignored) |
| **Test** | `pytest --cov=app --cov-fail-under=70` — 401 tests, 75% coverage |

CI config: `.github/workflows/ci.yml`

---

## Database

- **Engine:** PostgreSQL (SQLAlchemy 2.0 async engine)
- **Migrations:** Alembic (`alembic/`)
- **Models:** `app/db/models.py`

### Common Commands

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1

# Show current revision
alembic current
```

---

## Monitoring

### Structured Logging

All logs are structured JSON via `structlog`:

```json
{
  "event": "pipeline_finalized",
  "pipeline_id": "abc-123",
  "status": "completed",
  "duration": 12.5,
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### Audit Trail

Every agent decision creates an audit event (`app/services/audit_logger.py`):

| Field | Description |
|-------|-------------|
| `agent_id` | Which agent made the decision |
| `action` | What action was taken |
| `decision` | APPROVE / REWRITE / REJECT / ERROR |
| `reason` | Human-readable justification |
| `input_hash` | SHA-256 of input data |
| `output_hash` | SHA-256 of output data |
| `timestamp` | UTC timestamp |
| `session_id` | Pipeline session ID |

### Incident Management

Critical failures trigger incidents (`app/services/incident_manager.py`):

- Rights uncertainty → REWRITE or REJECT (never publish)
- API auth failure → Queue and alert
- Policy reject → Stop retries, create incident
- Missing disclosure → Auto-rewrite, re-QA

---

## Testing

```bash
# Full test suite
pytest

# With coverage report
pytest --cov=app --cov-report=html

# Specific test module
pytest tests/unit/test_rights_engine.py -v

# Integration tests only
pytest tests/integration/ -v
```

### Test Organization

| Directory | Count | Purpose |
|-----------|-------|---------|
| `tests/unit/` | ~30 modules | Unit tests for all services, policies, schemas |
| `tests/integration/` | 1 module | End-to-end MVP flow test |

---

## Project Layout

```
app/
├── adapters/        # Platform adapters (Amazon, Instagram, TikTok, etc.)
├── agents/          # CrewAI agent definitions
├── analytics/       # Analytics + AI chat engine
├── api/             # FastAPI REST API
├── approval/        # Human approval gates
├── billing/         # Stripe billing
├── collectors/      # YouTube, LinkedIn data collectors
├── content_generation/  # Copy, image, video generation
├── core/            # Auth, RBAC, logging, multi-tenancy
├── db/              # SQLAlchemy models + Alembic
├── export/          # Multi-format export (JSON, MD, HTML, PDF, PPTX)
├── flows/           # Pipeline orchestration
├── onboarding/      # Tenant onboarding
├── policies/        # Compliance policies
├── publishers/      # Multi-platform publishers
├── scheduling/      # Content scheduling
├── schemas/         # Pydantic data models
├── services/        # Core services (audit, hashing, rights, QA)
└── tools/           # CrewAI tool wrappers
```
