"""Database initialization utilities.

Creates tables for dev/testing. In production, use Alembic migrations.
"""
from __future__ import annotations

import structlog

from app.config import get_settings
from app.db.base import Base
from app.db.engine import build_engine

logger = structlog.get_logger(__name__)


def init_db(url: str | None = None) -> None:
    """Create all tables (dev/test only). Production uses Alembic."""
    settings = get_settings()
    db_url = url or settings.database_url

    engine = build_engine(url=db_url)

    # Import models so they register with Base.metadata
    import app.db.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info("db_tables_created", url=db_url.split("@")[-1] if "@" in db_url else db_url)
