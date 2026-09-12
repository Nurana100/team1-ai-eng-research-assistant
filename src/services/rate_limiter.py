"""Simple sleep-on-429 rate limiting, separate from retry/backoff logic.

Tracks recent call timestamps per source and enforces a minimum gap
between calls, so we don't hammer a provider even when calls succeed.
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict


class RateLimiter:
    """Enforces a minimum delay between consecutive calls to the same source."""

    def __init__(self, min_interval_seconds: float = 1.0) -> None:
        self.min_interval = min_interval_seconds
        self._last_call: dict[str, float] = defaultdict(float)
        self._lock = asyncio.Lock()

    async def wait_if_needed(self, source_name: str) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_call[source_name]

            if elapsed < self.min_interval:
                await asyncio.sleep(self.min_interval - elapsed)

            self._last_call[source_name] = time.monotonic()