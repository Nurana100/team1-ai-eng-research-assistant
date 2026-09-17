import logging

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.services.cache import TTLCache
from src.services.rate_limiter import RateLimiter
from topic-4-research-assistant.ai import (
    fetch_arxiv,
    fetch_web,
    fetch_wikipedia,
    synthesize,
)

logger = logging.getLogger(__name__)

RETRYABLE_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ReadTimeout,
    httpx.RemoteProtocolError,
)


class AIService:
    def __init__(
        self,
        timeout_seconds: float = 10.0,
        rate_limiter: RateLimiter | None = None,
        cache: TTLCache | None = None,
        client: httpx.AsyncClient | None = None,
        use_cache: bool = True,
    ):
        self.timeout_seconds = timeout_seconds
        self.rate_limiter = rate_limiter or RateLimiter()
        self.cache = cache or TTLCache()
        self.client = client
        self.use_cache = use_cache

    @retry(
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
    )
    async def fetch_wikipedia(
        self,
        query: str,
        client: httpx.AsyncClient | None = None,
    ) -> list[Source]:
        if self.use_cache:
            cached = self.cache.get("wikipedia", query)

            if cached is not None:
                logger.info("cache_hit_wikipedia", extra={"query": query})
                return cached

        logger.info("fetching_wikipedia", extra={"query": query})
        result = await fetch_wikipedia(
            query,
            timeout=self.timeout_seconds,
            rate_limiter=self.rate_limiter,
            client=client or self.client,
        )

        if self.use_cache:
            self.cache.set("wikipedia", query, result)

        return result

    @retry(
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
    )
    async def fetch_arxiv(
        self,
        query: str,
        client: httpx.AsyncClient | None = None,
    ) -> list[Source]:
        if self.use_cache:
            cached = self.cache.get("arxiv", query)

            if cached is not None:
                logger.info("cache_hit_arxiv", extra={"query": query})
                return cached

        logger.info("fetching_arxiv", extra={"query": query})
        result = await fetch_arxiv(
            query,
            timeout=self.timeout_seconds,
            rate_limiter=self.rate_limiter,
            client=client or self.client,
        )

        if self.use_cache:
            self.cache.set("arxiv", query, result)

        return result

    @retry(
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
    )
    async def fetch_web(
        self,
        query: str,
        client: httpx.AsyncClient | None = None,
    ) -> list[Source]:
        if self.use_cache:
            cached = self.cache.get("web", query)

            if cached is not None:
                logger.info("cache_hit_web", extra={"query": query})
                return cached

        logger.info("fetching_web", extra={"query": query})
        result = await fetch_web(
            query,
            timeout=self.timeout_seconds,
            rate_limiter=self.rate_limiter,
            client=client or self.client,
        )

        if self.use_cache:
            self.cache.set("web", query, result)

        return result

    async def synthesize(
        self,
        question: str,
        sources: list[Source],
        client: httpx.AsyncClient | None = None,
    ) -> str:
        logger.info("synthesizing_answer", extra={"question": question})

        return await synthesize(
            question,
            sources,
            timeout=self.timeout_seconds,
            rate_limiter=self.rate_limiter,
            client=client or self.client,
        )