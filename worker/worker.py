"""Async worker loop: dequeue tasks and run evaluation."""

from __future__ import annotations

import asyncio
from concurrent.futures import Executor
import logging
import time
from typing import Optional

from db.batch_writer import AsyncBatchWriter, WriteItem
from evaluation.engine import evaluate

from observability import RuntimeObserver
from task_queue.queue_manager import QueueManager

logger = logging.getLogger(__name__)

SENTINEL = object()


def evaluate_task_batch(tasks: list[dict]) -> list[dict]:
    return [evaluate(task) for task in tasks]


def _job_counts(tasks: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for task in tasks:
        job_id = task.get("batch_id", "unknown")
        counts[job_id] = counts.get(job_id, 0) + 1
    return counts


async def _evaluate_task_batch(
    tasks: list[dict],
    executor: Optional[Executor],
) -> list[dict]:
    if executor is None:
        return evaluate_task_batch(tasks)

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, evaluate_task_batch, tasks)


async def _dequeue_task_batch(
    queue: QueueManager,
    first_task: dict,
    batch_size: int,
) -> tuple[list[dict], bool]:
    tasks = [first_task]
    stop_requested = False

    while len(tasks) < batch_size:
        try:
            next_task = queue.get_nowait()
        except asyncio.QueueEmpty:
            break

        if next_task is SENTINEL:
            queue.task_done()
            stop_requested = True
            break

        tasks.append(next_task)

    return tasks, stop_requested


async def worker_loop(
    queue: QueueManager,
    worker_id: int,
    batch_writer: AsyncBatchWriter,
    observer: Optional[RuntimeObserver] = None,
    evaluation_executor: Optional[Executor] = None,
    evaluation_batch_size: int = 100,
) -> None:
    while True:
        task = await queue.dequeue()
        if task is SENTINEL:
            queue.task_done()
            break

        tasks, stop_requested = await _dequeue_task_batch(
            queue,
            task,
            evaluation_batch_size,
        )

        try:
            started_at = time.perf_counter()
            results = await _evaluate_task_batch(tasks, evaluation_executor)
            if observer is not None:
                observer.record_evaluation_time(
                    _job_counts(tasks),
                    time.perf_counter() - started_at,
                )
        except Exception as exc:
            logger.exception(
                "[worker %s] evaluation failed: %s task_keys=%s",
                worker_id,
                exc,
                list(tasks[0]) if isinstance(tasks[0], dict) else type(tasks[0]),
            )
            for _ in tasks:
                queue.task_done()
            if stop_requested:
                break
            continue

        for task, result in zip(tasks, results):
            row = {
                "task_id": task["task_id"],
                "job_id": task["job_id"],
                "input": task["input"],
                "output": task["output"],
                "score": result["final_score"],
                "flag": result["flag"],
            }
            await batch_writer.write(
                WriteItem(
                    row=row,
                    job_id=task.get("batch_id", "unknown"),
                    task_id=int(task["task_id"]),
                    worker_id=worker_id,
                    flag=result["flag"],
                ),
            )
            queue.task_done()

        if stop_requested:
            break
