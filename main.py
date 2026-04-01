"""FastAPI application: queue, workers, and evaluation API."""

from __future__ import annotations

import asyncio
import logging
import os
from concurrent.futures import ProcessPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI

LOG_PATH = Path(__file__).resolve().parent / "run.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_PATH, mode="a"),
    ],
)

from api.routes import router
from db.batch_writer import AsyncBatchWriter
from db.repository import init_db
from observability import RuntimeObserver
from task_queue.queue_manager import QueueManager
from worker.worker_pool import start_workers, stop_workers

logger = logging.getLogger(__name__)

DEFAULT_WORKERS = int(os.getenv("DEFAULT_WORKERS", "8"))
DB_BATCH_SIZE = int(os.getenv("DB_BATCH_SIZE", "250"))
DB_FLUSH_INTERVAL = float(os.getenv("DB_FLUSH_INTERVAL", "0.2"))
EVAL_BATCH_SIZE = int(os.getenv("EVAL_BATCH_SIZE", "100"))


def resolve_eval_processes() -> int:
    default_processes = os.cpu_count() or 4
    return max(1, int(os.getenv("EVAL_PROCESSES", str(default_processes))))


@asynccontextmanager
async def lifespan(app: FastAPI):
    eval_processes = resolve_eval_processes()
    init_db()
    queue = QueueManager()
    observer = RuntimeObserver()
    batch_writer = AsyncBatchWriter(
        observer=observer,
        batch_size=DB_BATCH_SIZE,
        flush_interval=DB_FLUSH_INTERVAL,
    )
    batch_writer.start()
    process_pool = None
    if eval_processes > 1:
        process_pool = ProcessPoolExecutor(max_workers=eval_processes)
        logger.info("Process pool enabled with %d workers", eval_processes)
    else:
        logger.info("Process pool disabled; evaluation will run in-process")
    worker_tasks = start_workers(
        DEFAULT_WORKERS,
        queue,
        batch_writer,
        observer,
        process_pool,
        EVAL_BATCH_SIZE,
    )
    app.state.queue = queue
    app.state.batch_writer = batch_writer
    app.state.observer = observer
    app.state.n_workers = DEFAULT_WORKERS
    app.state.worker_tasks = worker_tasks
    app.state.process_pool = process_pool
    app.state.eval_processes = eval_processes
    app.state.eval_batch_size = EVAL_BATCH_SIZE

    yield

    await stop_workers(app.state.n_workers, app.state.queue)
    await app.state.batch_writer.stop()
    await asyncio.gather(*app.state.worker_tasks)
    if app.state.process_pool is not None:
        app.state.process_pool.shutdown(wait=True, cancel_futures=False)


app = FastAPI(title="Evaluation system", lifespan=lifespan)
app.include_router(router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False, access_log=False)
