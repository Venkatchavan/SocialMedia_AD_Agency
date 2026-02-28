"""SQLAlchemy models for users, workspaces, and pipeline runs."""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin, WorkspaceMixin, generate_uuid


class UserModel(Base, TimestampMixin):
    """Application user."""

    __tablename__ = "users"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    bindings = relationship("WorkspaceBindingModel", back_populates="user")


class WorkspaceModel(Base, TimestampMixin):
    """Isolated client workspace."""

    __tablename__ = "workspaces"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(128), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)

    bindings = relationship(
        "WorkspaceBindingModel",
        back_populates="workspace",
    )
    pipeline_runs = relationship("PipelineRunModel", back_populates="workspace")


class WorkspaceBindingModel(Base, TimestampMixin):
    """Maps user → workspace with a role."""

    __tablename__ = "workspace_bindings"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    user_id = Column(
        String(64),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workspace_id = Column(
        String(64),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(String(32), nullable=False, default="viewer")

    user = relationship("UserModel", back_populates="bindings")
    workspace = relationship("WorkspaceModel", back_populates="bindings")


class PipelineRunModel(Base, TimestampMixin):
    """Record of a single pipeline execution."""

    __tablename__ = "pipeline_runs"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    workspace_id = Column(
        String(64),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    asin = Column(String(20), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="pending")
    target_platforms = Column(JSON, nullable=False, default=list)
    product_data = Column(JSON, nullable=True)
    result_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    rewrite_count = Column(Integer, default=0)

    workspace = relationship("WorkspaceModel", back_populates="pipeline_runs")


class AuditEventModel(Base, WorkspaceMixin):
    """Immutable audit log entry."""

    __tablename__ = "audit_events"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    agent = Column(String(128), nullable=False)
    action = Column(String(128), nullable=False)
    input_hash = Column(String(128), nullable=True)
    output_hash = Column(String(128), nullable=True)
    decision = Column(String(64), nullable=True)
    reason = Column(Text, nullable=True)
    timestamp = Column(String(64), nullable=False)
