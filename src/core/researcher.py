"""Core pipeline logic for Topic 4 — Async Research Assistant."""

from __future__ import annotations

import asyncio
import logging
from typing import Sequence

import httpx

from ai import (
    AnswerWithCitations,
    Source,
    fetch_arxiv,
    fetch_web,
    fetch_wikipedia,
    synthesize,
)
from ai.providers.base import LLMProvider, ProviderError

logger = logging.getLogger(__name__)


async def fetch_all_sources(
    question: str,
    sources_to_include: Sequence[str] = ("wiki", "arxiv", "web"),
    per_source_timeout: float = 10.0,
    max_results_per_source: int = 3,
    client: httpx.AsyncClient | None = None,
) -> list[Source]:
    """Fetch sources concurrently with per-source timeouts and graceful degradation."""
    if not question.strip():
        return []

    close_client = False
    if client is None:
        client = httpx.AsyncClient(timeout=per_source_timeout)
        close_client = True

    try:
        tasks = []
        if "wiki" in sources_to_include:
            tasks.append(
                asyncio.wait_for(
                    fetch_wikipedia(question, max_results=max_results_per_source, client=client),
                    timeout=per_source_timeout,
                )
            )

        if "arxiv" in sources_to_include:
            tasks.append(
                asyncio.wait_for(
                    fetch_arxiv(question, max_results=max_results_per_source, client=client),
                    timeout=per_source_timeout,
                )
            )

        if "web" in sources_to_include:
            tasks.append(
                asyncio.wait_for(
                    fetch_web(question, max_results=max_results_per_source, client=client),
                    timeout=per_source_timeout,
                )
            )

        if not tasks:
            return []

        results = await asyncio.gather(*tasks, return_exceptions=True)

        combined_sources: list[Source] = []
        seen_urls: set[str] = set()

        for result in results:
            if isinstance(result, Exception):
                logger.warning("Source fetcher failed or timed out: %s", result)
                continue

            for source in result:
                if source.url not in seen_urls:
                    seen_urls.add(source.url)
                    combined_sources.append(source)

        return combined_sources

    finally:
        if close_client:
            await client.aclose()


async def run_research_pipeline(
    question: str,
    sources_to_include: Sequence[str] = ("wiki", "arxiv", "web"),
    per_source_timeout: float = 10.0,
    llm: LLMProvider | None = None,
    client: httpx.AsyncClient | None = None,
) -> AnswerWithCitations:
    """Runs research query execution and returns a synthesized answer with citations."""
    cleaned_question = question.strip()
    if not cleaned_question:
        raise ValueError("Question cannot be empty.")

    sources = await fetch_all_sources(
        question=cleaned_question,
        sources_to_include=sources_to_include,
        per_source_timeout=per_source_timeout,
        client=client,
    )

    if not sources:
        raise ValueError(f"Could not retrieve sources for '{cleaned_question}'.")

    try:
        return synthesize(
            question=cleaned_question,
            sources=sources,
            llm=llm,
        )
    except Exception as e:
        raise ProviderError(f"LLM synthesis error: {e}") from e
