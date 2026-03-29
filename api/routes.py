"""HTTP routes for the evaluation service."""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Request
from pydantic import BaseModel, Field

from batch.batch_processor import process_batch
from task_queue.queue_manager import QueueManager

router = APIRouter()
logger = logging.getLogger(__name__)


class BatchRow(BaseModel):
    input: str = Field(..., description="Prompt or input text")
    output: str = Field(..., description="Model or system output to evaluate")


async def _run_batch(dataset: list[dict], queue: QueueManager, batch_id: str) -> None:
    logger.info("batch %s: enqueueing %d tasks onto queue", batch_id, len(dataset))
    await process_batch(dataset, queue, batch_id=batch_id)
    logger.info("batch %s: finished enqueueing %d tasks", batch_id, len(dataset))


@router.post("/evaluate-batch")
async def evaluate_batch(
    request: Request,
    background_tasks: BackgroundTasks,
    rows: list[BatchRow],
) -> dict:
    """
    Accept a JSON array of ``{"input", "output"}`` rows and enqueue them for async processing.
    Returns immediately without waiting for evaluation to finish.
    """
    dataset = [row.model_dump() for row in rows]
    queue: QueueManager = request.app.state.queue

    batch_id = str(uuid.uuid4())
    logger.info(
        "POST /evaluate-batch accepted batch_id=%s row_count=%d",
        batch_id,
        len(rows),
    )

    background_tasks.add_task(_run_batch, dataset, queue, batch_id)

    return {
        "status": "submitted",
        "message": "Batch processing started",
        "batch_id": batch_id,
        "row_count": len(rows),
    }
