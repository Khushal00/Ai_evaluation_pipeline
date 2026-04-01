"""Asynchronous buffered writer for evaluation results."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Optional

from db.repository import save_results
from observability import RuntimeObserver

SENTINEL = object()


@dataclass
class WriteItem:
    row: dict
    job_id: str
    task_id: int
    worker_id: int
    flag: str


class AsyncBatchWriter:
    def __init__(
        self,
        observer: RuntimeObserver,
        batch_size: int = 250,
        flush_interval: float = 0.2,
    ) -> None:
        self._observer = observer
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._queue: "asyncio.Queue[object]" = asyncio.Queue()
        self._task: Optional[asyncio.Task[None]] = None

    def start(self) -> None:
        self._task = asyncio.create_task(self._run(), name="batch-writer")

    async def write(self, item: WriteItem) -> None:
        await self._queue.put(item)

    async def stop(self) -> None:
        await self._queue.put(SENTINEL)
        await self._queue.join()
        if self._task is not None:
            await self._task

    async def _run(self) -> None:
        buffer: list[WriteItem] = []
        while True:
            try:
                item = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=self._flush_interval,
                )
            except asyncio.TimeoutError:
                if buffer:
                    await self._flush(buffer)
                    buffer = []
                continue

            if item is SENTINEL:
                if buffer:
                    await self._flush(buffer)
                    buffer = []
                self._queue.task_done()
                break

            buffer.append(item)
            if len(buffer) >= self._batch_size:
                await self._flush(buffer)
                buffer = []

    async def _flush(self, items: list[WriteItem]) -> None:
        rows = [item.row for item in items]
        job_counts: dict[str, int] = {}
        for item in items:
            job_counts[item.job_id] = job_counts.get(item.job_id, 0) + 1
        started_at = time.perf_counter()
        await asyncio.to_thread(save_results, rows)
        self._observer.record_db_time(job_counts, time.perf_counter() - started_at)
        for item in items:
            self._observer.record_result(
                job_id=item.job_id,
                task_id=item.task_id,
                worker_id=item.worker_id,
                flag=item.flag,
            )
            self._queue.task_done()
