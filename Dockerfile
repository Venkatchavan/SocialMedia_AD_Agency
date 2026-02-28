# ── Stage 1: Build ──────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies for compiled packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir hatchling

COPY pyproject.toml ./
COPY app/ ./app/

# Build wheel
RUN pip wheel --no-cache-dir --wheel-dir /wheels .


# ── Stage 2: Runtime ───────────────────────────────────
FROM python:3.12-slim AS runtime

LABEL maintainer="affiliate-ad-agency"
LABEL description="CrewAI-powered affiliate ad agency"

# Security: run as non-root
RUN groupadd --gid 1000 agency \
    && useradd --uid 1000 --gid agency --shell /bin/bash --create-home agency

WORKDIR /app

# Install runtime deps from pre-built wheels
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl \
    && rm -rf /wheels

# Copy application code
COPY app/ ./app/

# Create directories for data
RUN mkdir -p /app/clients /app/logs \
    && chown -R agency:agency /app

USER agency

# Health check (basic Python import check)
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "from app.config import get_settings; get_settings()" || exit 1

# Default: run the pipeline CLI
ENTRYPOINT ["python", "-m", "app.main"]
