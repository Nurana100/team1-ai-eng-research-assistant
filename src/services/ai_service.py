"""Service layer wrapping the provided ai/ module with retries, timeouts, and logging."""

from __future__ import annotations

import logging
from typing import Sequence

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.services.cache import TTLCache
from ai import AnswerWithCitations, Source, fetch_arxiv, fetch_web, fetch_wikipedia, synthesize
from ai.providers.base import LLMProvider, ProviderError

logger = logging.getLogger(__name__)

RETRYABLE_EXCEPTIONS = (
    ProviderError,
    httpx.HTTPStatusError,
    httpx.TimeoutException,
)


class AIService:
    """Wraps every call to ai.* with retries, timeouts, and structured logging."""

    def __init__(
        self,
        timeout_seconds: float = 10.0,
        cache_ttl_seconds: float = 86400,
    ):
        self.timeout_seconds = timeout_seconds
        self.cache = TTLCache(ttl_seconds=cache_ttl_seconds)

    @retry(
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def fetch_wikipedia(
        self,
        query: str,
        max_results: int = 3,
        client: httpx.AsyncClient | None = None,
    ) -> list[Source]:
        cached = self.cache.get("wikipedia", query)

        if cached is not None:
            logger.info("cache_hit_wikipedia", extra={"query": query})
            return cached

        logger.info("fetching_wikipedia", extra={"query": query})
        result = await fetch_wikipedia(
            query,
            max_results=max_results,
            client=client,
        )
        logger.info(
            "fetched_wikipedia",
            extra={"query": query, "count": len(result)},
        )

        self.cache.set("wikipedia", query, result)
        return result

    @retry(
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def fetch_arxiv(
        self,
        query: str,
        max_results: int = 3,
        client: httpx.AsyncClient | None = None,
    ) -> list[Source]:
        cached = self.cache.get("arxiv", query)

        if cached is not None:
            logger.info("cache_hit_arxiv", extra={"query": query})
            return cached

        logger.info("fetching_arxiv", extra={"query": query})
        result = await fetch_arxiv(
            query,
            max_results=max_results,
            client=client,
        )
        logger.info(
            "fetched_arxiv",
            extra={"query": query, "count": len(result)},
        )

        self.cache.set("arxiv", query, result)
        return result

    @retry(
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def fetch_web(
        self,
        query: str,
        max_results: int = 3,
        client: httpx.AsyncClient | None = None,
    ) -> list[Source]:
        cached = self.cache.get("web", query)

        if cached is not None:
            logger.info("cache_hit_web", extra={"query": query})
            return cached

        logger.info("fetching_web", extra={"query": query})
        result = await fetch_web(
            query,
            max_results=max_results,
            client=client,
        )
        logger.info(
            "fetched_web",
            extra={"query": query, "count": len(result)},
        )

        self.cache.set("web", query, result)
        return result

    @retry(
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def synthesize(
        self,
        question: str,
        sources: Sequence[Source],
        llm: LLMProvider | None = None,
    ) -> AnswerWithCitations:
        logger.info(
            "synthesizing_answer",
            extra={
                "question": question,
                "source_count": len(sources),
            },
        )
        result = synthesize(
            question=question,
            sources=sources,
            llm=llm,
        )
        logger.info(
            "synthesized_answer",
            extra={"question": question},
        )
        return result
