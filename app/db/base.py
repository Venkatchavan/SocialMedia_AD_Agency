"""SQLAlchemy 2.0 declarative base and shared model utilities."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String, text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all models."""

    pass


class TimestampMixin:
    """Add created_at / updated_at columns to any model."""

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
    )


class WorkspaceMixin:
    """Add workspace_id column for multi-tenancy (U-3)."""

    workspace_id = Column(
        String(64),
        nullable=False,
        index=True,
    )


def generate_uuid() -> str:
    """Generate a new UUID4 string for primary keys."""
    return str(uuid.uuid4())
