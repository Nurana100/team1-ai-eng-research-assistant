import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from src.services.rate_limiter import RateLimiter


def test_first_call_does_not_wait() -> None:
    async def exercise() -> None:
        limiter = RateLimiter(min_interval_seconds=0.5)

        with (
            patch(
                "src.services.rate_limiter.time.monotonic",
                side_effect=[10.0, 10.0],
            ),
            patch(
                "src.services.rate_limiter.asyncio.sleep",
                new_callable=AsyncMock,
            ) as mock_sleep,
        ):
            await limiter.wait_if_needed("wiki")
            mock_sleep.assert_not_awaited()

    asyncio.run(exercise())


def test_repeated_call_waits_for_remaining_interval() -> None:
    async def exercise() -> None:
        limiter = RateLimiter(min_interval_seconds=0.5)

        with (
            patch(
                "src.services.rate_limiter.time.monotonic",
                side_effect=[10.0, 10.0, 10.2, 10.5],
            ),
            patch(
                "src.services.rate_limiter.asyncio.sleep",
                new_callable=AsyncMock,
            ) as mock_sleep,
        ):
            await limiter.wait_if_needed("wiki")
            await limiter.wait_if_needed("wiki")

            mock_sleep.assert_awaited_once()
            assert mock_sleep.await_args.args[0] == pytest.approx(0.3)

    asyncio.run(exercise())