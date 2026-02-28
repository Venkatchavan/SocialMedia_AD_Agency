"""Database engine & session factory — SQLAlchemy 2.0 with connection pooling.

Supports both sync and async engines. The async engine uses asyncpg when
DATABASE_URL starts with 'postgresql+asyncpg://'.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


def _get_sync_url(url: str) -> str:
    """Convert async URL to sync (psycopg2) for Alembic/sync usage."""
    return url.replace("postgresql+asyncpg://", "postgresql://")


def build_engine(
    url: str | None = None,
    pool_size: int = 10,
    max_overflow: int = 20,
    echo: bool = False,
):
    """Create a sync SQLAlchemy engine with connection pooling.

    Args:
        url: Database URL. Defaults to settings.database_url.
        pool_size: Base pool size.
        max_overflow: Max connections above pool_size.
        echo: Log all SQL statements.

    Returns:
        SQLAlchemy Engine.
    """
    if url is None:
        url = get_settings().database_url

    sync_url = _get_sync_url(url)

    # Use NullPool for SQLite (testing), real pool for PostgreSQL
    is_sqlite = sync_url.startswith("sqlite")
    pool_kwargs = {}
    if not is_sqlite:
        pool_kwargs = {
            "pool_size": pool_size,
            "max_overflow": max_overflow,
            "pool_pre_ping": True,
        }

    engine = create_engine(sync_url, echo=echo, **pool_kwargs)
    return engine


def build_session_factory(engine=None) -> sessionmaker:
    """Create a session factory bound to the given (or default) engine."""
    if engine is None:
        engine = build_engine()
    return sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def get_session(
    factory: sessionmaker | None = None,
) -> Generator[Session, None, None]:
    """Context manager that yields a session and handles commit/rollback."""
    if factory is None:
        factory = build_session_factory()

    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
