"""Shared test scaffolding for the research assistant.

The suite is graded on running offline, so nothing in here may touch the
network or read a real API key. Three groups of helpers live below:

* stub providers - drop-in replacements for the LLM and the web-search
  backend, both of which record what they were asked for;
* a stub service - duck-typed twin of ``AIService`` so the orchestration in
  ``fetch_all_sources`` can be tested on its own;
* data factories - ready-made ``Source`` objects plus a builder for custom ones.

Everything here is deliberately dumb: no sleeps unless a test asks for them,
no state shared between tests.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

import httpx
import pytest

# pytest only puts the tests/ folder on sys.path, so ``import src...`` breaks
# when the suite is started from anywhere but the repo root. Pin the root once
# here instead of repeating a path hack in every test module.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ai import AnswerWithCitations, Source, synthesize
from ai.providers.base import LLMProvider, ProviderError
from ai.sources import WebSearchProvider

CREDENTIAL_ENV_VARS = (
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "GOOGLE_API_KEY",
    "TAVILY_API_KEY",
    "SERPER_API_KEY",
)


@pytest.fixture(autouse=True)
def scrub_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Hide every real key from the tests.

    Autouse on purpose: if a stub is ever forgotten, the call underneath fails
    with a missing-key error instead of quietly spending someone's quota.
    """
    for name in CREDENTIAL_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


class StubLLM(LLMProvider):
    """LLM that answers from memory and remembers what it was asked.

    ``prompts`` lets a test assert that the synthesizer really passed the
    sources along; ``fail_with`` turns the same stub into a broken provider
    for the retry and error paths.
    """

    DEFAULT_ANSWER = (
        "Running the three lookups concurrently costs roughly what the "
        "slowest single lookup costs [1], because the work is I/O bound "
        "rather than CPU bound [2]."
    )

    def __init__(
        self,
        answer: str | None = None,
        *,
        fail_with: Exception | None = None,
    ) -> None:
        self.answer = answer if answer is not None else self.DEFAULT_ANSWER
        self.fail_with = fail_with
        self.prompts: list[str] = []

    def complete(
        self,
        prompt: str,
        *,
        json_schema: dict | None = None,
        max_tokens: int = 1024,
    ) -> str:
        self.prompts.append(prompt)
        if self.fail_with is not None:
            raise self.fail_with
        return self.answer


class StubWebSearch(WebSearchProvider):
    """Web-search backend backed by a list instead of an HTTP API.

    ``latency`` exists for the parallel-vs-sequential benchmark: give a source
    a fake delay and the timing test stays deterministic and fast.
    """

    def __init__(
        self,
        results: Iterable[Source] | None = None,
        *,
        latency: float = 0.0,
    ) -> None:
        self.results = list(results) if results is not None else [_WEB_RESULT]
        self.latency = latency
        self.queries: list[str] = []

    async def search(
        self,
        query: str,
        *,
        max_results: int = 3,
        client: Any = None,
    ) -> list[Source]:
        self.queries.append(query)
        if self.latency:
            await asyncio.sleep(self.latency)
        return self.results[:max_results]


class StubAIService:
    """Stand-in for ``src.services.ai_service.AIService``.

    ``fetch_all_sources`` takes the service as an argument, so injecting this
    exercises the real orchestration - timeouts, de-duplication by URL,
    degradation when one source dies - with no HTTP involved at all.

    Break a single source with ``failures``, or slow one down past a timeout
    with ``latencies``::

        StubAIService(failures={"arxiv": ProviderError("arXiv is down")})
        StubAIService(latencies={"wiki": 5.0})
    """

    def __init__(
        self,
        *,
        wikipedia: Sequence[Source] | None = None,
        arxiv: Sequence[Source] | None = None,
        web: Sequence[Source] | None = None,
        failures: dict[str, Exception] | None = None,
        latencies: dict[str, float] | None = None,
        llm: LLMProvider | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        self.results = {
            "wiki": list(wikipedia) if wikipedia is not None else [_WIKI_RESULT],
            "arxiv": list(arxiv) if arxiv is not None else [_ARXIV_RESULT],
            "web": list(web) if web is not None else [_WEB_RESULT],
        }
        self.failures = failures or {}
        self.latencies = latencies or {}
        self.llm = llm or StubLLM()
        self.timeout_seconds = timeout_seconds
        self.calls: list[tuple[str, str]] = []

    async def _serve(self, name: str, query: str, max_results: int) -> list[Source]:
        self.calls.append((name, query))
        delay = self.latencies.get(name, 0.0)
        if delay:
            await asyncio.sleep(delay)
        problem = self.failures.get(name)
        if problem is not None:
            raise problem
        return self.results[name][:max_results]

    async def fetch_wikipedia(
        self,
        query: str,
        max_results: int = 3,
        client: Any = None,
    ) -> list[Source]:
        return await self._serve("wiki", query, max_results)

    async def fetch_arxiv(
        self,
        query: str,
        max_results: int = 3,
        client: Any = None,
    ) -> list[Source]:
        return await self._serve("arxiv", query, max_results)

    async def fetch_web(
        self,
        query: str,
        max_results: int = 3,
        client: Any = None,
    ) -> list[Source]:
        return await self._serve("web", query, max_results)

    def synthesize(
        self,
        question: str,
        sources: Sequence[Source],
        llm: LLMProvider | None = None,
    ) -> AnswerWithCitations:
        # Delegate to the real synthesizer so citation numbering stays honest;
        # only the model behind it is fake.
        self.calls.append(("synthesize", question))
        return synthesize(question=question, sources=list(sources), llm=llm or self.llm)


_WIKI_RESULT = Source(
    title="Asynchronous I/O (Wikipedia)",
    url="https://en.wikipedia.org/wiki/Asynchronous_I/O",
    snippet="Asynchronous I/O lets a program carry on with other work while a "
            "slow transfer is still in flight.",
    origin="wikipedia",
)

_ARXIV_RESULT = Source(
    title="Scheduling Concurrent Network Requests",
    url="https://arxiv.org/abs/2401.00001",
    snippet="We compare sequential and fan-out request strategies under "
            "several latency distributions.",
    origin="arxiv",
)

_WEB_RESULT = Source(
    title="A practical guide to asyncio.gather",
    url="https://example.org/asyncio-gather",
    snippet="gather() starts every coroutine at once and returns once the "
            "last of them has finished.",
    origin="web",
)


@pytest.fixture
def make_source() -> Callable[..., Source]:
    """Build a ``Source`` with one field changed and defaults everywhere else."""

    def _make(
        *,
        title: str = "Placeholder article",
        url: str = "https://example.org/placeholder",
        snippet: str = "Short excerpt used by the tests.",
        origin: str = "web",
    ) -> Source:
        return Source(title=title, url=url, snippet=snippet, origin=origin)

    return _make


@pytest.fixture
def wikipedia_sources() -> list[Source]:
    return [_WIKI_RESULT]


@pytest.fixture
def arxiv_sources() -> list[Source]:
    return [_ARXIV_RESULT]


@pytest.fixture
def web_sources() -> list[Source]:
    return [_WEB_RESULT]


@pytest.fixture
def all_sources() -> list[Source]:
    """One source per origin, in the order the pipeline fans out."""
    return [_WIKI_RESULT, _ARXIV_RESULT, _WEB_RESULT]


@pytest.fixture
def stub_llm() -> StubLLM:
    return StubLLM()


@pytest.fixture
def failing_llm() -> StubLLM:
    return StubLLM(fail_with=ProviderError("stub provider refused the call"))


@pytest.fixture
def stub_web_search() -> StubWebSearch:
    return StubWebSearch()


@pytest.fixture
def stub_ai_service(stub_llm: StubLLM) -> StubAIService:
    return StubAIService(llm=stub_llm)


@pytest.fixture
def offline_client_factory() -> Callable[..., httpx.AsyncClient]:
    """Hand out ``AsyncClient``s that refuse to leave the machine.

    Every request raises instead of dialling out, so a test that accidentally
    reaches the real Wikipedia fails loudly rather than depending on the CI
    runner having internet. The test owns the client and closes it.
    """

    def _refuse(request: httpx.Request) -> httpx.Response:
        raise RuntimeError(
            f"network access blocked in tests: {request.method} {request.url}"
        )

    def _build(**kwargs: Any) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=httpx.MockTransport(_refuse), **kwargs)

    return _build
