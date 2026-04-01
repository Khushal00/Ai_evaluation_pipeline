"""Async queue facade wrapping asyncio.Queue."""

from __future__ import annotations

import asyncio
from typing import Any


class QueueManager:
    def __init__(self) -> None:
        self._queue: asyncio.Queue[Any] = asyncio.Queue()

    async def enqueue(self, task: Any) -> None:
        await self._queue.put(task)

    async def dequeue(self) -> Any:
        return await self._queue.get()

    def get_nowait(self) -> Any:
        return self._queue.get_nowait()

    def task_done(self) -> None:
        self._queue.task_done()

    async def join(self) -> None:
        await self._queue.join()
