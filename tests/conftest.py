"""Shared test scaffolding for the research assistant.

The suite is graded on running offline, so nothing in here may touch the
network or read a real API key.
"""


from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ai import Source
from ai.providers.base import LLMProvider, ProviderError

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
