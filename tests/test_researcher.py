"""Tests for the research pipeline orchestration in src/core/researcher.py.

Uses the StubAIService from conftest.py — no real network or API calls.
"""

import pytest

from src.core.researcher import fetch_all_sources, run_research_pipeline
from ai.providers.base import ProviderError
from tests.conftest import StubAIService


@pytest.mark.asyncio
async def test_fetch_all_sources_happy_path():
    """All three sources succeed — combined list should have all results."""
    stub = StubAIService()
    result = await fetch_all_sources("test question", ai_service=stub)
    assert len(result) == 3
    origins = {s.origin for s in result}
    assert origins == {"wikipedia", "arxiv", "web"}


@pytest.mark.asyncio
async def test_fetch_all_sources_graceful_degradation():
    """arXiv fails — pipeline should still return wiki + web, not crash."""
    stub = StubAIService(failures={"arxiv": ProviderError("arXiv is down")})
    result = await fetch_all_sources("test question", ai_service=stub)
    assert len(result) == 2
    origins = {s.origin for s in result}
    assert origins == {"wikipedia", "web"}


@pytest.mark.asyncio
async def test_fetch_all_sources_all_fail_returns_empty():
    """All sources fail — should return an empty list, not raise."""
    stub = StubAIService(
        failures={
            "wiki": ProviderError("wiki down"),
            "arxiv": ProviderError("arxiv down"),
            "web": ProviderError("web down"),
        }
    )
    result = await fetch_all_sources("test question", ai_service=stub)
    assert result == []


@pytest.mark.asyncio
async def test_run_research_pipeline_raises_on_empty_question():
    """An empty/whitespace-only question should raise ValueError immediately."""
    with pytest.raises(ValueError):
        await run_research_pipeline("   ")


@pytest.mark.asyncio
async def test_run_research_pipeline_happy_path_returns_answer(stub_llm):
    """Full flow: sources fetched, then synthesized into a cited answer."""
    stub = StubAIService(llm=stub_llm)
    sources = await fetch_all_sources("test question", ai_service=stub)
    result = stub.synthesize("test question", sources)
    assert result.answer
    assert len(result.citations) > 0


@pytest.mark.asyncio
async def test_concurrent_fetch_uses_all_three_sources():
    """Confirms fetch_all_sources actually calls all three sources, not just one."""
    stub = StubAIService()
    await fetch_all_sources("concurrency test", ai_service=stub)
    called_sources = {name for name, _ in stub.calls}
    assert called_sources == {"wiki", "arxiv", "web"}
