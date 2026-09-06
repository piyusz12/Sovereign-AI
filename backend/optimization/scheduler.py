"""Priority-aware serialization of local GPU work.

The laptop has one 8 GB GPU, so interactive generation must not compete with
an indexing or reranking job for KV cache and VRAM. This scheduler executes one
job per event loop and starts higher-priority queued work first.
"""

from __future__ import annotations

import asyncio
import itertools
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Coroutine
from uuid import uuid4

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class InferenceJob(BaseModel):
    id: str
    task_type: str
    priority: int  # 1 = interactive, larger values = background work


@dataclass(order=True)
class _QueuedJob:
    priority: int
    sequence: int
    enqueued_at: float
    job: InferenceJob = field(compare=False)
    coroutine: Coroutine[Any, Any, Any] = field(compare=False)
    result: asyncio.Future[Any] = field(compare=False)


@dataclass
class _LoopState:
    queue: asyncio.PriorityQueue[_QueuedJob]
    semaphore: asyncio.Semaphore
    worker: asyncio.Task[None] | None = None
    active_jobs: int = 0


class GPUScheduler:
    """Runs at most one GPU request at a time and exposes real queue depth."""

    def __init__(self) -> None:
        self._states: dict[int, _LoopState] = {}
        self._sequence = itertools.count()

    def _state(self) -> _LoopState:
        loop = asyncio.get_running_loop()
        key = id(loop)
        state = self._states.get(key)
        if state is None:
            state = _LoopState(queue=asyncio.PriorityQueue(), semaphore=asyncio.Semaphore(1))
            self._states[key] = state
        return state

    @property
    def queue_depth(self) -> int:
        return sum(state.queue.qsize() for state in self._states.values())

    @property
    def active_jobs(self) -> int:
        return sum(state.active_jobs for state in self._states.values())

    @property
    def semaphore(self) -> asyncio.Semaphore:
        """Compatibility accessor for legacy streaming call sites."""
        return self._state().semaphore

    async def schedule(self, task_type: str, priority: int, coro: Coroutine[Any, Any, Any]) -> Any:
        if priority < 1:
            raise ValueError("GPU priority must be at least 1")
        state = self._state()
        job = InferenceJob(id=str(uuid4()), task_type=task_type, priority=priority)
        result: asyncio.Future[Any] = asyncio.get_running_loop().create_future()
        queued = _QueuedJob(
            priority=priority,
            sequence=next(self._sequence),
            enqueued_at=perf_counter(),
            job=job,
            coroutine=coro,
            result=result,
        )
        await state.queue.put(queued)
        if state.worker is None or state.worker.done():
            state.worker = asyncio.create_task(self._run_queue(state))
        logger.info("Queued GPU job %s (%s); waiting=%d", job.id, task_type, state.queue.qsize())
        try:
            return await result
        except asyncio.CancelledError:
            result.cancel()
            raise

    async def _run_queue(self, state: _LoopState) -> None:
        while True:
            try:
                queued = state.queue.get_nowait()
            except asyncio.QueueEmpty:
                # Give jobs enqueued by the current event-loop turn a chance to
                # enter the priority queue before declaring the worker idle.
                await asyncio.sleep(0)
                try:
                    queued = state.queue.get_nowait()
                except asyncio.QueueEmpty:
                    return

            try:
                if queued.result.cancelled():
                    queued.coroutine.close()
                    continue
                state.active_jobs += 1
                wait_ms = round((perf_counter() - queued.enqueued_at) * 1000, 2)
                logger.info("Executing GPU job %s (%s); queue wait=%.2fms", queued.job.id, queued.job.task_type, wait_ms)
                async with state.semaphore:
                    value = await queued.coroutine
                if not queued.result.cancelled():
                    queued.result.set_result(value)
            except Exception as exc:
                if not queued.result.cancelled():
                    queued.result.set_exception(exc)
            finally:
                state.active_jobs -= 1
                state.queue.task_done()

    @asynccontextmanager
    async def exclusive(self):
        """Serialize legacy streaming operations that cannot be queued as a coroutine."""
        state = self._state()
        await state.semaphore.acquire()
        state.active_jobs += 1
        try:
            yield
        finally:
            state.active_jobs -= 1
            state.semaphore.release()


gpu_scheduler = GPUScheduler()
