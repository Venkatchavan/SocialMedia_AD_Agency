"""Tests for async pipeline executor (U-7)."""

from __future__ import annotations

import asyncio

import pytest

from app.flows.async_pipeline import (
    AsyncPipelineExecutor,
    PipelineResult,
    StageResult,
    StageStatus,
)

# ── Helper async functions ─────────────────────────────


async def _succeed(value: str = "ok") -> str:
    await asyncio.sleep(0.01)
    return value


async def _fail() -> None:
    await asyncio.sleep(0.01)
    raise RuntimeError("Stage exploded")


async def _slow(seconds: float = 0.05) -> str:
    await asyncio.sleep(seconds)
    return "done"


# ── Tests ──────────────────────────────────────────────


class TestStageResult:
    def test_completed(self) -> None:
        r = StageResult(name="test", status=StageStatus.COMPLETED)
        assert r.status == StageStatus.COMPLETED
        assert r.error is None

    def test_failed(self) -> None:
        r = StageResult(name="test", status=StageStatus.FAILED, error="boom")
        assert r.error == "boom"


class TestPipelineResult:
    def test_succeeded_all_completed(self) -> None:
        pr = PipelineResult(stages=[
            StageResult(name="a", status=StageStatus.COMPLETED),
            StageResult(name="b", status=StageStatus.COMPLETED),
        ])
        assert pr.succeeded is True

    def test_succeeded_with_skipped(self) -> None:
        pr = PipelineResult(stages=[
            StageResult(name="a", status=StageStatus.COMPLETED),
            StageResult(name="b", status=StageStatus.SKIPPED),
        ])
        assert pr.succeeded is True

    def test_failed_stage(self) -> None:
        pr = PipelineResult(stages=[
            StageResult(name="a", status=StageStatus.COMPLETED),
            StageResult(name="b", status=StageStatus.FAILED, error="x"),
        ])
        assert pr.succeeded is False
        assert pr.failed_stages == ["b"]


class TestAsyncPipelineExecutor:
    @pytest.mark.asyncio
    async def test_sequential_stages(self) -> None:
        executor = AsyncPipelineExecutor()
        executor.add_sequential("step1", _succeed, "hello")
        executor.add_sequential("step2", _succeed, "world")

        result = await executor.run()
        assert result.succeeded
        assert len(result.stages) == 2
        assert result.stages[0].output == "hello"
        assert result.stages[1].output == "world"

    @pytest.mark.asyncio
    async def test_parallel_stages(self) -> None:
        executor = AsyncPipelineExecutor()
        executor.add_parallel("group1", [
            ("task_a", _succeed, "a"),
            ("task_b", _succeed, "b"),
        ])

        result = await executor.run()
        assert result.succeeded
        assert len(result.stages) == 2
        names = {s.name for s in result.stages}
        assert names == {"task_a", "task_b"}

    @pytest.mark.asyncio
    async def test_parallel_is_faster_than_sequential(self) -> None:
        executor = AsyncPipelineExecutor()
        executor.add_parallel("group", [
            ("slow_a", _slow, 0.05),
            ("slow_b", _slow, 0.05),
        ])

        result = await executor.run()
        assert result.succeeded
        # If parallel, total should be ~50ms not ~100ms
        assert result.total_duration_ms < 150  # generous bound

    @pytest.mark.asyncio
    async def test_failure_stops_pipeline(self) -> None:
        executor = AsyncPipelineExecutor()
        executor.add_sequential("ok", _succeed)
        executor.add_sequential("bad", _fail)
        executor.add_sequential("never", _succeed)

        result = await executor.run()
        assert not result.succeeded
        assert len(result.stages) == 2  # "never" was not reached
        assert result.stages[1].status == StageStatus.FAILED

    @pytest.mark.asyncio
    async def test_semaphore_limits_concurrency(self) -> None:
        executor = AsyncPipelineExecutor(max_concurrent=2)

        executor.add_parallel("group", [
            ("a", _slow, 0.02),
            ("b", _slow, 0.02),
            ("c", _slow, 0.02),
        ])

        result = await executor.run()
        assert result.succeeded
        assert len(result.stages) == 3

    @pytest.mark.asyncio
    async def test_duration_tracked(self) -> None:
        executor = AsyncPipelineExecutor()
        executor.add_sequential("step", _slow, 0.02)

        result = await executor.run()
        assert result.total_duration_ms >= 15  # ~20ms sleep
        assert result.stages[0].duration_ms >= 15

    @pytest.mark.asyncio
    async def test_empty_pipeline(self) -> None:
        executor = AsyncPipelineExecutor()
        result = await executor.run()
        assert result.succeeded
        assert len(result.stages) == 0

    @pytest.mark.asyncio
    async def test_mixed_sequential_and_parallel(self) -> None:
        executor = AsyncPipelineExecutor()
        executor.add_sequential("intake", _succeed, "product")
        executor.add_parallel("analyze", [
            ("media", _succeed, "media_data"),
            ("comments", _succeed, "comment_data"),
        ])
        executor.add_sequential("synthesize", _succeed, "synthesis")

        result = await executor.run()
        assert result.succeeded
        assert len(result.stages) == 4
        assert result.stages[0].name == "intake"
        assert result.stages[3].name == "synthesize"
