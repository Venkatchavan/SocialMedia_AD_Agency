"""Multi-tenancy — workspace isolation for queries and storage.

Provides workspace-scoped session filters and storage path builders.
Enforces row-level isolation per workspace_id (U-3).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Query, Session


@dataclass(frozen=True)
class TenantContext:
    """Immutable context identifying the current tenant."""

    workspace_id: str
    user_id: str


class TenantScopedSession:
    """Wraps a SQLAlchemy session to automatically filter by workspace_id."""

    def __init__(self, session: Session, tenant: TenantContext) -> None:
        self._session = session
        self._tenant = tenant

    @property
    def workspace_id(self) -> str:
        return self._tenant.workspace_id

    @property
    def user_id(self) -> str:
        return self._tenant.user_id

    @property
    def raw(self) -> Session:
        """Access underlying session (for non-tenant-scoped ops)."""
        return self._session

    def query(self, model: Any) -> Query:
        """Return a query pre-filtered by workspace_id."""
        if hasattr(model, "workspace_id"):
            return self._session.query(model).filter(
                model.workspace_id == self._tenant.workspace_id
            )
        return self._session.query(model)

    def add(self, instance: Any) -> None:
        """Add entity, auto-setting workspace_id if applicable."""
        if hasattr(instance, "workspace_id"):
            instance.workspace_id = self._tenant.workspace_id
        self._session.add(instance)

    def add_all(self, instances: list[Any]) -> None:
        """Add multiple entities with workspace_id injection."""
        for inst in instances:
            self.add(inst)

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()

    def close(self) -> None:
        self._session.close()


def storage_path(workspace_id: str, *parts: str) -> str:
    """Build an isolated S3/storage path for a workspace.

    Example:
        storage_path("ws-123", "assets", "image.png")
        → "ws-123/assets/image.png"

    Args:
        workspace_id: Workspace identifier.
        *parts: Path segments after workspace prefix.

    Returns:
        Forward-slash joined path.
    """
    if not workspace_id:
        raise ValueError("workspace_id cannot be empty")
    segments = [workspace_id, *parts]
    return "/".join(segments)


def validate_workspace_access(
    workspace_id: str,
    allowed_workspaces: list[str],
) -> bool:
    """Check if a workspace_id is in the user's allowed list.

    Prevents cross-workspace data leakage.

    Args:
        workspace_id: The workspace being accessed.
        allowed_workspaces: Workspaces the user has bindings for.

    Returns:
        True if access is permitted.
    """
    return workspace_id in allowed_workspaces
