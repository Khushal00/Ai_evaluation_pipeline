"""Start a pool of concurrent async workers."""

from __future__ import annotations

import asyncio

from queue.queue_manager import QueueManager
from worker.worker import SENTINEL, worker_loop


def start_workers(n: int, queue: QueueManager) -> list[asyncio.Task[None]]:
    return [
        asyncio.create_task(worker_loop(queue, worker_id=i), name=f"worker-{i}")
        for i in range(n)
    ]


async def stop_workers(n: int, queue: QueueManager) -> None:
    for _ in range(n):
        await queue.enqueue(SENTINEL)
    await queue.join()
