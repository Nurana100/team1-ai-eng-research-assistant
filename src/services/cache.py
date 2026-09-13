"""Simple in-memory TTL cache for AI service calls.

Keyed by (source_name, query) so re-asking the same question doesn't hit
Wikipedia/arXiv/web search again within the TTL window.
"""

from __future__ import annotations

import time
from typing import Any


class TTLCache:
    """A minimal time-to-live cache. Not thread-safe by design — this
    project is asyncio-based (single-threaded event loop), so a lock isn't
    needed for our use case.
    """

    def __init__(self, ttl_seconds: float = 86400) -> None:
        self.ttl_seconds = ttl_seconds
        self._store: dict[str, tuple[float, Any]] = {}

    def _make_key(self, source: str, query: str) -> str:
        return f"{source}:{query.strip().lower()}"

    def get(self, source: str, query: str) -> Any | None:
        key = self._make_key(source, query)
        entry = self._store.get(key)
        if entry is None:
            return None
        timestamp, value = entry
        if time.monotonic() - timestamp > self.ttl_seconds:
            del self._store[key]
            return None
        return value

    def set(self, source: str, query: str, value: Any) -> None:
        key = self._make_key(source, query)
        self._store[key] = (time.monotonic(), value)

    def clear(self) -> None:
        self._store.clear()

    def size(self) -> int:
        return len(self._store)
