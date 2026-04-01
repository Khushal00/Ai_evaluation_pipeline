"""Enqueue evaluation tasks from a dataset into the async queue."""

from __future__ import annotations

import logging
from typing import Optional

from task_queue.queue_manager import QueueManager

DEFAULT_MAX_LENGTH = 100
DEFAULT_RULES = {
    "keyword": {
        "enabled": False,
        "keywords": [],
        "match_mode": "any",
        "case_sensitive": False,
        "critical": True,
    },
    "length": {
        "enabled": True,
        "max_length": DEFAULT_MAX_LENGTH,
        "critical": False,
    },
}

logger = logging.getLogger(__name__)


def _build_rules(batch_rules: Optional[dict]) -> dict:
    rules = {
        "keyword": dict(DEFAULT_RULES["keyword"]),
        "length": dict(DEFAULT_RULES["length"]),
    }
    if not batch_rules:
        return rules

    for rule_name, config in batch_rules.items():
        if config is None:
            continue
        if rule_name not in rules:
            rules[rule_name] = {}
        rules[rule_name].update(config)
    return rules


async def process_batch(
    dataset: list[dict],
    queue: QueueManager,
    batch_id: Optional[str] = None,
    batch_rules: Optional[dict] = None,
) -> None:
    """
    For each row in ``dataset`` (must have ``input`` and ``output``), build a task
    with client-configurable rules and enqueue it.
    """
    rules = _build_rules(batch_rules)
    for index, row in enumerate(dataset):
        task = {
            "task_id": index,
            "job_id": f"job-{index}",
            "input": row["input"],
            "output": row["output"],
            "rules": {
                "keyword": dict(rules["keyword"]),
                "length": dict(rules["length"]),
            },
        }
        if batch_id is not None:
            task["batch_id"] = batch_id
        await queue.enqueue(task)
    if batch_id is not None:
        logger.info("batch %s: process_batch enqueued %d tasks", batch_id, len(dataset))
