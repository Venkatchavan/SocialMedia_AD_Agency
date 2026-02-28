"""Workspace management routes."""

from __future__ import annotations

from pydantic import BaseModel

from fastapi import APIRouter, HTTPException, status

router = APIRouter()

# In-memory workspace store (will be replaced by DB)
_workspaces: dict[str, dict] = {}


class WorkspaceCreate(BaseModel):
    """Create workspace request."""

    name: str
    slug: str


class WorkspaceResponse(BaseModel):
    """Workspace response."""

    id: str
    name: str
    slug: str
    is_active: bool = True


@router.post("/", response_model=WorkspaceResponse, status_code=201)
async def create_workspace(request: WorkspaceCreate) -> WorkspaceResponse:
    """Create a new workspace."""
    if request.slug in _workspaces:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Workspace slug '{request.slug}' already exists",
        )

    import uuid

    ws_id = str(uuid.uuid4())
    _workspaces[request.slug] = {
        "id": ws_id,
        "name": request.name,
        "slug": request.slug,
        "is_active": True,
    }
    return WorkspaceResponse(**_workspaces[request.slug])


@router.get("/{slug}", response_model=WorkspaceResponse)
async def get_workspace(slug: str) -> WorkspaceResponse:
    """Get workspace by slug."""
    ws = _workspaces.get(slug)
    if ws is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace '{slug}' not found",
        )
    return WorkspaceResponse(**ws)


@router.get("/", response_model=list[WorkspaceResponse])
async def list_workspaces() -> list[WorkspaceResponse]:
    """List all workspaces."""
    return [WorkspaceResponse(**ws) for ws in _workspaces.values()]
