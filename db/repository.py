"""Pluggable persistence for evaluation results with SQLite batching."""

from __future__ import annotations

import logging
import os
import sqlite3
import threading
from pathlib import Path
from typing import Optional

from db.models import CREATE_TABLE_SQL

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "evaluation.db"
DEFAULT_DB_URL = "sqlite:///" + str(DEFAULT_DB_PATH)
_write_lock = threading.Lock()


class SQLiteBackend:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def init(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute(CREATE_TABLE_SQL)
            conn.commit()

    def save_results(self, results: list[dict]) -> None:
        if not results:
            return

        sql = """
            INSERT INTO evaluations (task_id, job_id, input, output, score, flag)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        params = [
            (
                result["task_id"],
                result["job_id"],
                result["input"],
                result["output"],
                float(result["score"]),
                result["flag"],
            )
            for result in results
        ]

        with _write_lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.executemany(sql, params)
                conn.commit()


_active_backend = SQLiteBackend(DEFAULT_DB_PATH)


def init_db(db_path: Optional[Path] = None, db_url: Optional[str] = None) -> None:
    """Initialize the configured persistence backend."""
    global _active_backend

    effective_url = db_url or os.getenv("DATABASE_URL") or DEFAULT_DB_URL
    if db_path is not None:
        _active_backend = SQLiteBackend(db_path)
    elif effective_url.startswith("sqlite:///"):
        _active_backend = SQLiteBackend(Path(effective_url.replace("sqlite:///", "", 1)))
    else:
        raise NotImplementedError(
            "Only SQLite is configured in this project right now. "
            "The repository layer is pluggable, so PostgreSQL can be added next.",
        )

    _active_backend.init()


def save_result(result: dict) -> None:
    """
    Insert one evaluation row.

    ``result`` must include: task_id, job_id, input, output, score, flag.
    (``score`` is the final aggregate score from the evaluation engine.)
    """
    required = ("task_id", "job_id", "input", "output", "score", "flag")
    for key in required:
        if key not in result:
            raise KeyError(f"save_result: missing key {key!r}")

    save_results([result])


def save_results(results: list[dict]) -> None:
    """Insert many evaluation rows in one batch."""
    if not results:
        return

    required = ("task_id", "job_id", "input", "output", "score", "flag")
    for result in results:
        for key in required:
            if key not in result:
                raise KeyError(f"save_results: missing key {key!r}")

    _active_backend.save_results(results)
    logger.debug("saved %d evaluation rows", len(results))
