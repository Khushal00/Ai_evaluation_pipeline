"""Start a pool of concurrent async workers."""

from __future__ import annotations

import asyncio
from concurrent.futures import Executor
from typing import Optional

from db.batch_writer import AsyncBatchWriter
from observability import RuntimeObserver
from task_queue.queue_manager import QueueManager
from worker.worker import SENTINEL, worker_loop


def start_workers(
    n: int,
    queue: QueueManager,
    batch_writer: AsyncBatchWriter,
    observer: Optional[RuntimeObserver] = None,
    evaluation_executor: Optional[Executor] = None,
    evaluation_batch_size: int = 100,
) -> list[asyncio.Task[None]]:
    return [
        asyncio.create_task(
            worker_loop(
                queue,
                worker_id=i,
                batch_writer=batch_writer,
                observer=observer,
                evaluation_executor=evaluation_executor,
                evaluation_batch_size=evaluation_batch_size,
            ),
            name=f"worker-{i}",
        )
        for i in range(n)
    ]


async def stop_workers(n: int, queue: QueueManager) -> None:
    for _ in range(n):
        await queue.enqueue(SENTINEL)
    await queue.join()
