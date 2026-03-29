"""HTTP routes for the evaluation service."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Request
from pydantic import BaseModel, Field

from batch.batch_processor import process_batch
from queue.queue_manager import QueueManager

router = APIRouter()


class BatchRow(BaseModel):
    input: str = Field(..., description="Prompt or input text")
    output: str = Field(..., description="Model or system output to evaluate")


async def _run_batch(dataset: list[dict], queue: QueueManager) -> None:
    await process_batch(dataset, queue)


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

    background_tasks.add_task(_run_batch, dataset, queue)

    return {
        "status": "submitted",
        "message": "Batch processing started",
    }
