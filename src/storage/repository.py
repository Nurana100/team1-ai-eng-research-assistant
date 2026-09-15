"""Persistent storage for research pipeline results.

Uses the abstract-base-class pattern (same shape as ai.providers.base.LLMProvider)
so we can swap SQLite for Postgres later without touching calling code.
"""

from __future__ import annotations

import abc
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
