"""Enqueue evaluation tasks from a dataset into the async queue."""

from __future__ import annotations

import logging

from task_queue.queue_manager import QueueManager

DEFAULT_KEYWORD = "alpha"
DEFAULT_MAX_LENGTH = 100

logger = logging.getLogger(__name__)


async def process_batch(
    dataset: list[dict],
    queue: QueueManager,
    batch_id: str | None = None,
) -> None:
    """
    For each row in ``dataset`` (must have ``input`` and ``output``), build a task
    and enqueue it. Task fields: task_id, job_id, input, output, keyword, max_length,
    and optional batch_id for log correlation across workers.
    """
    for index, row in enumerate(dataset):
        task = {
            "task_id": index,
            "job_id": f"job-{index}",
            "input": row["input"],
            "output": row["output"],
            "keyword": DEFAULT_KEYWORD,
            "max_length": DEFAULT_MAX_LENGTH,
        }
        if batch_id is not None:
            task["batch_id"] = batch_id
        await queue.enqueue(task)
    if batch_id is not None:
        logger.info("batch %s: process_batch enqueued %d tasks", batch_id, len(dataset))
