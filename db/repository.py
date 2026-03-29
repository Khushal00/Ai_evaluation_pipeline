"""SQLite persistence for evaluation results."""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

from db.models import CREATE_TABLE_SQL

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "evaluation.db"
_write_lock = threading.Lock()
_active_db_path: Path = DEFAULT_DB_PATH


def init_db(db_path: Path | None = None) -> None:
    """Create the evaluations table if it does not exist."""
    global _active_db_path
    _active_db_path = db_path or DEFAULT_DB_PATH
    with sqlite3.connect(_active_db_path) as conn:
        conn.execute(CREATE_TABLE_SQL)
        conn.commit()


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

    sql = """
        INSERT INTO evaluations (task_id, job_id, input, output, score, flag)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    params = (
        result["task_id"],
        result["job_id"],
        result["input"],
        result["output"],
        float(result["score"]),
        result["flag"],
    )

    with _write_lock:
        with sqlite3.connect(_active_db_path) as conn:
            conn.execute(sql, params)
            conn.commit()
