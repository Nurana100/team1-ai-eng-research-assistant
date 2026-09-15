"""Persistent storage for research pipeline results.

Uses the abstract-base-class pattern (same shape as ai.providers.base.LLMProvider)
so we can swap SQLite for Postgres later without touching calling code.
"""

from __future__ import annotations

import abc
import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class StorageBackend(abc.ABC):
    """Contract for persisting research queries and their answers."""

    @abc.abstractmethod
    def save_query(
        self,
        question: str,
        answer_text: str,
        sources: list[dict[str, Any]],
    ) -> int:
        """Persist one research query + its synthesized answer. Returns the new record id."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_query(self, query_id: int) -> dict[str, Any] | None:
        """Fetch one saved query by id, or None if it doesn't exist."""
        raise NotImplementedError

    @abc.abstractmethod
    def list_queries(self, limit: int = 20) -> list[dict[str, Any]]:
        """List the most recent saved queries, newest first."""
        raise NotImplementedError


class SQLiteStorage(StorageBackend):
    """SQLite-backed implementation of StorageBackend."""

    def __init__(self, db_path: str = "research_history.db") -> None:
        self.db_path = Path(db_path)
        self._init_schema()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """Open a connection, commit or roll back, and always close it.

        `with conn:` only ends the transaction -- it does not close the handle,
        so the connection has to be closed explicitly or every call leaks one.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT NOT NULL,
                    answer_text TEXT NOT NULL,
                    sources_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def save_query(
        self,
        question: str,
        answer_text: str,
        sources: list[dict[str, Any]],
    ) -> int:
        created_at = datetime.now(timezone.utc).isoformat()
        sources_json = json.dumps(sources)
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO queries (question, answer_text, sources_json, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (question, answer_text, sources_json, created_at),
            )
            return cursor.lastrowid

    def get_query(self, query_id: int) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM queries WHERE id = ?", (query_id,)
            ).fetchone()
            if row is None:
                return None
            return {
                "id": row["id"],
                "question": row["question"],
                "answer_text": row["answer_text"],
                "sources": json.loads(row["sources_json"]),
                "created_at": row["created_at"],
            }

    def list_queries(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM queries ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            return [
                {
                    "id": row["id"],
                    "question": row["question"],
                    "answer_text": row["answer_text"],
                    "sources": json.loads(row["sources_json"]),
                    "created_at": row["created_at"],
                }
                for row in rows
            ]
