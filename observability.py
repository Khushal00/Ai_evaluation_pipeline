"""Lightweight runtime observability for async evaluation jobs."""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field

logger = logging.getLogger("runtime")

FIRST_TASK_LOGS = 20
PROGRESS_EVERY = 1000


@dataclass
class JobStats:
    total_tasks: int
    worker_count: int
    start_time: float
    processed_count: int = 0
    good_count: int = 0
    bad_count: int = 0
    incorrect_count: int = 0
    enqueue_time: float = 0.0
    evaluation_time: float = 0.0
    db_time: float = 0.0
    worker_task_counts: dict[int, int] = field(default_factory=dict)
    completion_logged: bool = False


class RuntimeObserver:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, JobStats] = {}

    def start_job(self, job_id: str, total_tasks: int, worker_count: int) -> None:
        now = time.perf_counter()
        with self._lock:
            self._jobs[job_id] = JobStats(
                total_tasks=total_tasks,
                worker_count=worker_count,
                start_time=now,
            )
        logger.info(
            "JOB START | job_id=%s total_tasks=%d workers=%d",
            job_id,
            total_tasks,
            worker_count,
        )
        if total_tasks == 0:
            logger.info(
                "JOB COMPLETE | job_id=%s total_time=0.00s throughput=0.00 tasks/s GOOD=0 BAD=0 INCORRECT=0",
                job_id,
            )

    def record_enqueue_time(self, job_id: str, elapsed: float) -> None:
        with self._lock:
            stats = self._jobs.get(job_id)
            if stats is None:
                return
            stats.enqueue_time += elapsed

    def record_evaluation_time(self, job_counts: dict[str, int], elapsed: float) -> None:
        total = sum(job_counts.values())
        if total <= 0:
            return
        with self._lock:
            for job_id, count in job_counts.items():
                stats = self._jobs.get(job_id)
                if stats is None:
                    continue
                stats.evaluation_time += elapsed * (count / total)

    def record_db_time(self, job_counts: dict[str, int], elapsed: float) -> None:
        total = sum(job_counts.values())
        if total <= 0:
            return
        with self._lock:
            for job_id, count in job_counts.items():
                stats = self._jobs.get(job_id)
                if stats is None:
                    continue
                stats.db_time += elapsed * (count / total)

    def record_result(self, job_id: str, task_id: int, worker_id: int, flag: str) -> None:
        with self._lock:
            stats = self._jobs.get(job_id)
            if stats is None:
                return

            stats.processed_count += 1
            if flag == "GOOD":
                stats.good_count += 1
            elif flag == "BAD":
                stats.bad_count += 1
            elif flag == "INCORRECT":
                stats.incorrect_count += 1
            stats.worker_task_counts[worker_id] = stats.worker_task_counts.get(worker_id, 0) + 1

            processed_count = stats.processed_count
            total_tasks = stats.total_tasks
            elapsed = time.perf_counter() - stats.start_time
            should_log_task = processed_count <= FIRST_TASK_LOGS
            should_log_progress = (
                processed_count > FIRST_TASK_LOGS
                and processed_count < total_tasks
                and processed_count % PROGRESS_EVERY == 0
            )
            should_log_summary = (
                processed_count >= total_tasks and not stats.completion_logged
            )
            if should_log_summary:
                stats.completion_logged = True

            good_count = stats.good_count
            bad_count = stats.bad_count
            incorrect_count = stats.incorrect_count
            enqueue_time = stats.enqueue_time
            evaluation_time = stats.evaluation_time
            db_time = stats.db_time
            worker_task_counts = dict(sorted(stats.worker_task_counts.items()))

        if should_log_task:
            logger.info(
                "[%6.2fs] Worker-%d processed task-%d -> %s",
                elapsed,
                worker_id,
                task_id,
                flag,
            )

        if should_log_progress:
            percentage = (processed_count / total_tasks) * 100 if total_tasks else 100.0
            logger.info(
                "Progress | job_id=%s %d/%d (%.1f%%)",
                job_id,
                processed_count,
                total_tasks,
                percentage,
            )

        if should_log_summary:
            throughput = processed_count / elapsed if elapsed > 0 else 0.0
            logger.info(
                "JOB COMPLETE | job_id=%s total_time=%.2fs throughput=%.2f tasks/s GOOD=%d BAD=%d INCORRECT=%d",
                job_id,
                elapsed,
                throughput,
                good_count,
                bad_count,
                incorrect_count,
            )
            logger.info(
                "TIMINGS | job_id=%s enqueue_time=%.2fs evaluation_time=%.2fs db_time=%.2fs",
                job_id,
                enqueue_time,
                evaluation_time,
                db_time,
            )
            worker_summary = " ".join(
                f"Worker-{worker_id}:{count}"
                for worker_id, count in worker_task_counts.items()
            )
            logger.info("WORKERS | job_id=%s %s", job_id, worker_summary)
