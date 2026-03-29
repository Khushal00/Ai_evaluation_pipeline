"""Async worker loop: dequeue tasks and run evaluation."""

from __future__ import annotations

import logging

from db.repository import save_result
from evaluation.engine import evaluate

from task_queue.queue_manager import QueueManager

logger = logging.getLogger(__name__)

SENTINEL = object()


def _format_evaluation_log(worker_id: int, task: dict, result: dict) -> str:
    bid = task.get("batch_id", "?")
    lines = [
        f"[worker {worker_id}] batch_id={bid} task_id={task.get('task_id', '?')} "
        f"flag={result['flag']} final_score={result['final_score']:.2f}",
    ]
    for item in result["results"]:
        lines.append(
            f"    {item['metric']}: passed={item['passed']} score={item['score']:.0f} — {item['reason']}",
        )
    return "\n".join(lines)


async def worker_loop(queue: QueueManager, worker_id: int) -> None:
    while True:
        task = await queue.dequeue()
        if task is SENTINEL:
            queue.task_done()
            break

        try:
            result = evaluate(task)
        except Exception as exc:
            logger.exception(
                "[worker %s] evaluation failed: %s task_keys=%s",
                worker_id,
                exc,
                list(task) if isinstance(task, dict) else type(task),
            )
            queue.task_done()
            continue

        logger.info(_format_evaluation_log(worker_id, task, result))

        row = {
            "task_id": task["task_id"],
            "job_id": task["job_id"],
            "input": task["input"],
            "output": task["output"],
            "score": result["final_score"],
            "flag": result["flag"],
        }
        save_result(row)

        queue.task_done()
