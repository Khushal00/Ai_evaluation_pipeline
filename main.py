"""FastAPI application: queue, workers, and evaluation API."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from api.routes import router
from db.repository import init_db
from queue.queue_manager import QueueManager
from worker.worker_pool import start_workers, stop_workers

DEFAULT_WORKERS = 4


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    queue = QueueManager()
    worker_tasks = start_workers(DEFAULT_WORKERS, queue)
    app.state.queue = queue
    app.state.n_workers = DEFAULT_WORKERS
    app.state.worker_tasks = worker_tasks

    yield

    await stop_workers(app.state.n_workers, app.state.queue)
    await asyncio.gather(*app.state.worker_tasks)


app = FastAPI(title="Evaluation system", lifespan=lifespan)
app.include_router(router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
