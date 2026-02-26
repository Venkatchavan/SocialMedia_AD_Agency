"""core.config — Centralised configuration loaded from .env / environment."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


def _get(key: str, default: str = "") -> str:
    return os.getenv(key, default)


# ── Paths ───────────────────────────────────────────
PROJECT_ROOT: Path = _PROJECT_ROOT
CLIENTS_DIR: Path = PROJECT_ROOT / "clients"
DATA_DIR: Path = PROJECT_ROOT / "data"

# ── API keys ────────────────────────────────────────
APIFY_TOKEN: str = _get("APIFY_TOKEN")
GEMINI_API_KEY: str = _get("GEMINI_API_KEY")
OPENAI_API_KEY: str = _get("OPENAI_API_KEY")
X_BEARER_TOKEN: str = _get("X_BEARER_TOKEN")

# ── Database ────────────────────────────────────────
DATABASE_URL: str = _get("DATABASE_URL", f"sqlite:///{DATA_DIR / 'creative_os.db'}")

# ── Workspace defaults ──────────────────────────────
DEFAULT_WORKSPACE: str = _get("DEFAULT_WORKSPACE", "sample_client")
DATE_RANGE_DAYS: int = int(_get("DATE_RANGE_DAYS", "30"))
MAX_ASSETS_PER_BRAND: int = int(_get("MAX_ASSETS_PER_BRAND", "30"))

# ── Logging ─────────────────────────────────────────
LOG_LEVEL: str = _get("LOG_LEVEL", "INFO")

# ── Feature flags ───────────────────────────────────
USE_VISION_MODEL: bool = bool(GEMINI_API_KEY)
_any_llm = bool(GEMINI_API_KEY or OPENAI_API_KEY or _get("ANTHROPIC_API_KEY") or _get("MISTRAL_API_KEY"))
USE_LLM_BRIEF: bool = _any_llm
LLM_PROVIDER_ORDER: str = _get("LLM_PROVIDER_ORDER", "gemini,openai,anthropic,mistral")


def workspace_path(workspace_id: str) -> Path:
    """Return the root path for a client workspace."""
    return CLIENTS_DIR / workspace_id


def run_path(workspace_id: str, run_id: str) -> Path:
    """Return the run directory for a workspace run."""
    p = workspace_path(workspace_id) / "runs" / run_id
    p.mkdir(parents=True, exist_ok=True)
    return p
