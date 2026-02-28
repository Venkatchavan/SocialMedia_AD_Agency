"""Tests for database engine, models, and session management (U-8)."""

from __future__ import annotations

from sqlalchemy import inspect, text

from app.db.base import Base, TimestampMixin, WorkspaceMixin, generate_uuid
from app.db.engine import build_engine, build_session_factory, get_session
from app.db.models import (
    AuditEventModel,
    PipelineRunModel,
    UserModel,
    WorkspaceBindingModel,
    WorkspaceModel,
)


# ── Helpers ────────────────────────────────────────────


def _sqlite_engine():
    """In-memory SQLite engine for testing (no PostgreSQL needed)."""
    return build_engine(url="sqlite:///:memory:")


def _create_tables(engine):
    """Create all tables in the test DB."""
    Base.metadata.create_all(engine)


# ── Model Tests ────────────────────────────────────────


class TestGenerateUuid:
    def test_returns_string(self) -> None:
        uid = generate_uuid()
        assert isinstance(uid, str)
        assert len(uid) == 36  # UUID4 format

    def test_unique(self) -> None:
        ids = {generate_uuid() for _ in range(100)}
        assert len(ids) == 100


class TestModelsExist:
    """All expected models have proper table names."""

    def test_user_table(self) -> None:
        assert UserModel.__tablename__ == "users"

    def test_workspace_table(self) -> None:
        assert WorkspaceModel.__tablename__ == "workspaces"

    def test_binding_table(self) -> None:
        assert WorkspaceBindingModel.__tablename__ == "workspace_bindings"

    def test_pipeline_run_table(self) -> None:
        assert PipelineRunModel.__tablename__ == "pipeline_runs"

    def test_audit_event_table(self) -> None:
        assert AuditEventModel.__tablename__ == "audit_events"


class TestMixins:
    """TimestampMixin and WorkspaceMixin add expected columns."""

    def test_timestamp_mixin_has_columns(self) -> None:
        assert hasattr(TimestampMixin, "created_at")
        assert hasattr(TimestampMixin, "updated_at")

    def test_workspace_mixin_has_column(self) -> None:
        assert hasattr(WorkspaceMixin, "workspace_id")

    def test_pipeline_run_has_workspace_id(self) -> None:
        # PipelineRunModel uses WorkspaceMixin
        cols = {c.name for c in PipelineRunModel.__table__.columns}
        assert "workspace_id" in cols


# ── Engine Tests ───────────────────────────────────────


class TestBuildEngine:
    """build_engine() creates a working SQLAlchemy engine."""

    def test_sqlite_engine(self) -> None:
        engine = _sqlite_engine()
        assert engine is not None
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_create_all_tables(self) -> None:
        engine = _sqlite_engine()
        _create_tables(engine)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        assert "users" in tables
        assert "workspaces" in tables
        assert "workspace_bindings" in tables
        assert "pipeline_runs" in tables
        assert "audit_events" in tables


# ── Session Tests ──────────────────────────────────────


class TestSession:
    """get_session() provides commit/rollback context."""

    def setup_method(self) -> None:
        self.engine = _sqlite_engine()
        _create_tables(self.engine)
        self.factory = build_session_factory(self.engine)

    def test_insert_user(self) -> None:
        with get_session(self.factory) as session:
            user = UserModel(
                id="u1",
                email="test@example.com",
                password_hash="abc123",
            )
            session.add(user)

        # Verify persisted
        with get_session(self.factory) as session:
            u = session.get(UserModel, "u1")
            assert u is not None
            assert u.email == "test@example.com"

    def test_insert_workspace_with_binding(self) -> None:
        with get_session(self.factory) as session:
            user = UserModel(id="u2", email="a@b.com", password_hash="h")
            ws = WorkspaceModel(id="ws1", name="Test WS", slug="test-ws")
            binding = WorkspaceBindingModel(
                id="b1",
                user_id="u2",
                workspace_id="ws1",
                role="editor",
            )
            session.add_all([user, ws, binding])

        with get_session(self.factory) as session:
            ws = session.get(WorkspaceModel, "ws1")
            assert ws is not None
            assert ws.slug == "test-ws"

    def test_insert_pipeline_run(self) -> None:
        with get_session(self.factory) as session:
            run = PipelineRunModel(
                id="r1",
                workspace_id="ws1",
                asin="B0XXXXXXXXX",
                status="completed",
                target_platforms=["tiktok", "instagram"],
            )
            session.add(run)

        with get_session(self.factory) as session:
            r = session.get(PipelineRunModel, "r1")
            assert r is not None
            assert r.asin == "B0XXXXXXXXX"
            assert r.target_platforms == ["tiktok", "instagram"]

    def test_insert_audit_event(self) -> None:
        with get_session(self.factory) as session:
            evt = AuditEventModel(
                id="ae1",
                workspace_id="ws1",
                agent="rights_engine",
                action="verify",
                decision="APPROVE",
                timestamp="2025-01-01T00:00:00Z",
            )
            session.add(evt)

        with get_session(self.factory) as session:
            e = session.get(AuditEventModel, "ae1")
            assert e is not None
            assert e.decision == "APPROVE"

    def test_rollback_on_error(self) -> None:
        try:
            with get_session(self.factory) as session:
                session.add(
                    UserModel(id="u3", email="c@d.com", password_hash="x"),
                )
                raise ValueError("Simulated error")
        except ValueError:
            pass

        # u3 should NOT be persisted
        with get_session(self.factory) as session:
            assert session.get(UserModel, "u3") is None
