"""Tests for multi-tenancy (U-3)."""

from __future__ import annotations

import pytest
from sqlalchemy import Column, String

from app.core.multi_tenancy import (
    TenantContext,
    TenantScopedSession,
    storage_path,
    validate_workspace_access,
)
from app.db.base import Base, generate_uuid
from app.db.engine import build_engine, build_session_factory, get_session
from app.db.models import AuditEventModel


# ── TenantContext ──────────────────────────────────────


class TestTenantContext:
    def test_immutable(self) -> None:
        ctx = TenantContext(workspace_id="ws-1", user_id="u-1")
        with pytest.raises(AttributeError):
            ctx.workspace_id = "ws-2"  # type: ignore[misc]

    def test_fields(self) -> None:
        ctx = TenantContext(workspace_id="ws-1", user_id="u-1")
        assert ctx.workspace_id == "ws-1"
        assert ctx.user_id == "u-1"


# ── TenantScopedSession ───────────────────────────────


class TestTenantScopedSession:
    def setup_method(self) -> None:
        self.engine = build_engine(url="sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.factory = build_session_factory(self.engine)
        self.tenant = TenantContext(workspace_id="ws-A", user_id="u-1")

    def test_add_injects_workspace_id(self) -> None:
        with get_session(self.factory) as session:
            scoped = TenantScopedSession(session, self.tenant)
            event = AuditEventModel(
                id="ae-1",
                agent="test",
                action="test",
                timestamp="2025-01-01T00:00:00Z",
            )
            scoped.add(event)
            assert event.workspace_id == "ws-A"

    def test_query_filters_by_workspace(self) -> None:
        # Insert events for two workspaces
        with get_session(self.factory) as session:
            session.add(AuditEventModel(
                id="ae-1", workspace_id="ws-A",
                agent="a", action="a", timestamp="t1",
            ))
            session.add(AuditEventModel(
                id="ae-2", workspace_id="ws-B",
                agent="b", action="b", timestamp="t2",
            ))

        with get_session(self.factory) as session:
            scoped = TenantScopedSession(session, self.tenant)
            results = scoped.query(AuditEventModel).all()
            assert len(results) == 1
            assert results[0].workspace_id == "ws-A"

    def test_add_all_sets_workspace(self) -> None:
        with get_session(self.factory) as session:
            scoped = TenantScopedSession(session, self.tenant)
            events = [
                AuditEventModel(
                    id=f"ae-{i}", agent="test", action="test",
                    timestamp="t",
                )
                for i in range(3)
            ]
            scoped.add_all(events)
            for e in events:
                assert e.workspace_id == "ws-A"


# ── Storage Path ──────────────────────────────────────


class TestStoragePath:
    def test_basic_path(self) -> None:
        assert storage_path("ws-1", "assets", "img.png") == "ws-1/assets/img.png"

    def test_workspace_only(self) -> None:
        assert storage_path("ws-1") == "ws-1"

    def test_empty_workspace_raises(self) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            storage_path("", "assets")


# ── Access Validation ─────────────────────────────────


class TestValidateWorkspaceAccess:
    def test_allowed(self) -> None:
        assert validate_workspace_access("ws-1", ["ws-1", "ws-2"]) is True

    def test_denied(self) -> None:
        assert validate_workspace_access("ws-3", ["ws-1", "ws-2"]) is False

    def test_empty_list(self) -> None:
        assert validate_workspace_access("ws-1", []) is False
