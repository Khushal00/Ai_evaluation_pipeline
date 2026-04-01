"""HTTP routes for the evaluation service."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Literal, Optional

from fastapi import APIRouter, BackgroundTasks, Request
from pydantic import BaseModel, ConfigDict, Field

from batch.batch_processor import process_batch
from task_queue.queue_manager import QueueManager

router = APIRouter()
logger = logging.getLogger(__name__)


class KeywordRuleConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    keywords: list[str] = Field(
        default_factory=list,
        description="List of allowed/required keywords to check in the output",
    )
    match_mode: Literal["any", "all"] = Field(
        default="any",
        description="Whether any or all keywords must appear in the output",
    )
    case_sensitive: bool = Field(
        default=False,
        description="Whether keyword matching should be case-sensitive",
    )
    critical: bool = Field(
        default=True,
        description="If true, a failure marks the evaluation as INCORRECT",
    )


class LengthRuleConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    max_length: Optional[int] = Field(
        default=None,
        description="Maximum allowed output length in characters",
    )
    critical: bool = Field(
        default=False,
        description="If true, a failure marks the evaluation as INCORRECT",
    )


class RuleSet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    keyword: Optional[KeywordRuleConfig] = None
    length: Optional[LengthRuleConfig] = None


class BatchRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input: str = Field(..., description="Prompt or input text")
    output: str = Field(..., description="Model or system output to evaluate")


class EvaluateBatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rows: list[BatchRow]
    rules: Optional[RuleSet] = Field(
        default=None,
        description="Optional batch-level evaluation rules applied to all rows",
    )


async def _run_batch(
    dataset: list[dict],
    queue: QueueManager,
    batch_id: str,
    batch_rules: Optional[dict],
    observer,
) -> None:
    logger.info("batch %s: enqueueing %d tasks onto queue", batch_id, len(dataset))
    started_at = time.perf_counter()
    await process_batch(dataset, queue, batch_id=batch_id, batch_rules=batch_rules)
    observer.record_enqueue_time(batch_id, time.perf_counter() - started_at)
    logger.info("batch %s: finished enqueueing %d tasks", batch_id, len(dataset))


@router.post("/evaluate-batch")
async def evaluate_batch(
    request: Request,
    background_tasks: BackgroundTasks,
    payload: EvaluateBatchRequest,
) -> dict:
    """
    Accept async batch evaluations with one shared rules configuration.
    Returns immediately without waiting for evaluation to finish.
    """
    rows = payload.rows
    batch_rules = payload.rules.model_dump(exclude_none=True) if payload.rules else None
    dataset = [row.model_dump() for row in rows]
    queue: QueueManager = request.app.state.queue
    observer = request.app.state.observer

    batch_id = str(uuid.uuid4())
    observer.start_job(batch_id, len(rows), request.app.state.n_workers)

    background_tasks.add_task(_run_batch, dataset, queue, batch_id, batch_rules, observer)

    return {
        "status": "submitted",
        "message": "Batch processing started",
        "batch_id": batch_id,
        "row_count": len(rows),
    }
