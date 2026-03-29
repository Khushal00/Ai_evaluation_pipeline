"""SQLite schema for persisted evaluation rows."""

from __future__ import annotations

TABLE_NAME = "evaluations"

# id: auto-increment; created_at: set by SQLite default
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    job_id TEXT NOT NULL,
    input TEXT NOT NULL,
    output TEXT NOT NULL,
    score REAL NOT NULL,
    flag TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""
