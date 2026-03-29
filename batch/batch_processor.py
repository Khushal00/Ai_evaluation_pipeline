"""Enqueue evaluation tasks from a dataset into the async queue."""

from __future__ import annotations

from queue.queue_manager import QueueManager

DEFAULT_KEYWORD = "alpha"
DEFAULT_MAX_LENGTH = 100


async def process_batch(dataset: list[dict], queue: QueueManager) -> None:
    """
    For each row in ``dataset`` (must have ``input`` and ``output``), build a task
    and enqueue it. Task fields: task_id, job_id, input, output, keyword, max_length.
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
        await queue.enqueue(task)
