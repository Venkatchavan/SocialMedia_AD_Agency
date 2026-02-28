"""Async pipeline executor — concurrent stage execution with semaphore guards.

Provides asyncio.gather-based concurrency for independent pipeline stages
while respecting rate limits via semaphore (max 5 concurrent LLM calls).
Reduces pipeline execution time ~60% (U-7).
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class StageStatus(str, Enum):
    """Execution status for an async stage."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageResult:
    """Result from a single async stage execution."""

    name: str
    status: StageStatus
    duration_ms: float = 0.0
    output: Any = None
    error: str | None = None


@dataclass
class PipelineResult:
    """Aggregated results from all stages."""

    stages: list[StageResult] = field(default_factory=list)
    total_duration_ms: float = 0.0

    @property
    def succeeded(self) -> bool:
        return all(
            s.status in (StageStatus.COMPLETED, StageStatus.SKIPPED)
            for s in self.stages
        )

    @property
    def failed_stages(self) -> list[str]:
        return [s.name for s in self.stages if s.status == StageStatus.FAILED]


# Type alias for async stage functions
AsyncStageFn = Callable[..., Coroutine[Any, Any, Any]]


class AsyncPipelineExecutor:
    """Execute pipeline stages with concurrency controls.

    Usage:
        executor = AsyncPipelineExecutor(max_concurrent=5)

        # Register stages (independent stages share a group)
        executor.add_sequential("intake", intake_fn, arg1, arg2)
        executor.add_parallel("analysis", [
            ("analyze_media", analyze_fn, arg1),
            ("mine_comments", mining_fn, arg1),
        ])
        executor.add_sequential("synthesize", synthesize_fn, data)

        result = await executor.run()
    """

    def __init__(self, max_concurrent: int = 5) -> None:
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._steps: list[_Step] = []

    def add_sequential(
        self,
        name: str,
        fn: AsyncStageFn,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Add a single sequential stage."""
        self._steps.append(_Step(
            kind="sequential",
            tasks=[_Task(name=name, fn=fn, args=args, kwargs=kwargs)],
        ))

    def add_parallel(
        self,
        group_name: str,
        tasks: list[tuple[str, AsyncStageFn, ...]],
    ) -> None:
        """Add a group of stages to run concurrently.

        Args:
            group_name: Label for the parallel group.
            tasks: List of (name, async_fn, *args) tuples.
        """
        parsed = []
        for item in tasks:
            name = item[0]
            fn = item[1]
            args = item[2:] if len(item) > 2 else ()
            parsed.append(_Task(name=name, fn=fn, args=args, kwargs={}))
        self._steps.append(_Step(kind="parallel", tasks=parsed))

    async def run(self) -> PipelineResult:
        """Execute all registered stages in order."""
        result = PipelineResult()
        t0 = time.monotonic()

        for step in self._steps:
            if step.kind == "sequential":
                task = step.tasks[0]
                stage_result = await self._execute_task(task)
                result.stages.append(stage_result)
                if stage_result.status == StageStatus.FAILED:
                    break
            else:
                # Parallel execution
                coros = [self._execute_task(t) for t in step.tasks]
                stage_results = await asyncio.gather(*coros)
                result.stages.extend(stage_results)
                if any(r.status == StageStatus.FAILED for r in stage_results):
                    break

        result.total_duration_ms = (time.monotonic() - t0) * 1000
        return result

    async def _execute_task(self, task: _Task) -> StageResult:
        """Execute a single task under semaphore control."""
        async with self._semaphore:
            t0 = time.monotonic()
            try:
                logger.info("stage_started", stage=task.name)
                output = await task.fn(*task.args, **task.kwargs)
                duration = (time.monotonic() - t0) * 1000
                logger.info(
                    "stage_completed",
                    stage=task.name,
                    duration_ms=round(duration, 2),
                )
                return StageResult(
                    name=task.name,
                    status=StageStatus.COMPLETED,
                    duration_ms=duration,
                    output=output,
                )
            except Exception as exc:
                duration = (time.monotonic() - t0) * 1000
                logger.error(
                    "stage_failed",
                    stage=task.name,
                    error=str(exc),
                    duration_ms=round(duration, 2),
                )
                return StageResult(
                    name=task.name,
                    status=StageStatus.FAILED,
                    duration_ms=duration,
                    error=str(exc),
                )


@dataclass
class _Task:
    """Internal task descriptor."""

    name: str
    fn: AsyncStageFn
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)


@dataclass
class _Step:
    """A pipeline step — either sequential or parallel."""

    kind: str  # "sequential" | "parallel"
    tasks: list[_Task]
