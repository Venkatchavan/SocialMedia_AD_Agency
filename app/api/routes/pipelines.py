"""Pipeline execution routes."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel, Field

router = APIRouter()

# In-memory run store (will be replaced by DB)
_runs: dict[str, dict] = {}


class PipelineRunRequest(BaseModel):
    """Request to trigger a pipeline run."""

    asin: str
    workspace_id: str = Field(default="default")
    platforms: list[str] = Field(default_factory=lambda: ["tiktok", "instagram"])


class PipelineRunResponse(BaseModel):
    """Pipeline run status."""

    run_id: str
    status: str
    asin: str
    platforms: list[str]


def _execute_pipeline(run_id: str, asin: str, platforms: list[str]) -> None:
    """Background task — runs the content pipeline."""
    try:
        from app.main import run_pipeline

        result = run_pipeline(asin=asin, platforms=platforms)
        _runs[run_id]["status"] = result.get("status", "completed")
        _runs[run_id]["result"] = result
    except Exception as exc:
        _runs[run_id]["status"] = "failed"
        _runs[run_id]["error"] = str(exc)


@router.post("/run", response_model=PipelineRunResponse, status_code=202)
async def trigger_pipeline(
    request: PipelineRunRequest,
    background_tasks: BackgroundTasks,
) -> PipelineRunResponse:
    """Trigger a pipeline run (non-blocking)."""
    import uuid

    run_id = str(uuid.uuid4())
    _runs[run_id] = {
        "run_id": run_id,
        "status": "queued",
        "asin": request.asin,
        "platforms": request.platforms,
    }

    background_tasks.add_task(
        _execute_pipeline,
        run_id=run_id,
        asin=request.asin,
        platforms=request.platforms,
    )

    return PipelineRunResponse(
        run_id=run_id,
        status="queued",
        asin=request.asin,
        platforms=request.platforms,
    )


@router.get("/{run_id}", response_model=dict)
async def get_run_status(run_id: str) -> dict:
    """Get the status of a pipeline run."""
    from fastapi import HTTPException, status

    run = _runs.get(run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found",
        )
    return run
