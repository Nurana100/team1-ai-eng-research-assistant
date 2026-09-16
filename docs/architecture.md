# Architecture

## Module map
                ┌─────────────┐
                │   src/cli.py │  ← user entry point (P3)
                │  (validation,│
                │  arg parsing)│
                └──────┬──────┘
                       │
                       ▼
          ┌────────────────────────┐
          │ src/core/researcher.py │  ← orchestration layer
          │  - fetch_all_sources() │
          │  - run_research_       │
          │    pipeline()          │
          │  - concurrency         │
          │    (asyncio.gather)    │
          │  - graceful            │
          │    degradation         │
          └───────────┬────────────┘
                       │
                       ▼
       ┌───────────────────────────────┐
       │ src/services/ai_service.py    │  ← AI wrapping layer
       │  - AIService class            │
       │  - retries (tenacity)         │
       │  - timeouts                   │
       │  - structured logging         │
       │  - caching (TTLCache)         │
       │  - rate limiting              │
       │    (RateLimiter)              │
       └──────┬─────────────────┬──────┘
              │                 │
              ▼                 ▼
    ┌──────────────────┐  ┌─────────────────────┐
    │ src/services/     │  │ src/services/        │
    │ cache.py          │  │ rate_limiter.py      │
    │ (TTLCache)        │  │ (RateLimiter)         │
    └──────────────────┘  └─────────────────────┘
              │
              ▼
       ┌─────────────────────────────────┐
       │  ai/  (PROVIDED — do not modify) │
       │  - sources.py:                   │
       │      fetch_wikipedia()           │
       │      fetch_arxiv()               │
       │      fetch_web()                 │
       │  - synthesizer.py:                │
       │      synthesize()                │
       │  - providers/ (LLMProvider ABC:   │
       │      Anthropic, OpenAI, Gemini)   │
       └───────────────┬───────────────────┘
                        │
                        ▼
          Wikipedia API / arXiv API /
          DuckDuckGo / Tavily / Serper /
          Anthropic / Gemini / OpenAI

       ┌────────────────────────────────┐
       │ src/storage/repository.py      │  ← persistence layer
       │  - StorageBackend (ABC)        │  (our own OOP example,
       │  - SQLiteStorage               │   separate from ai/'s
       │      save_query()              │   LLMProvider pattern)
       │      get_query()               │
       │      list_queries()            │
       └────────────────────────────────┘
          called from researcher.py after
          a successful synthesize() call

## Boundary explanation

**The `ai/` package boundary.** Everything below the dashed line in the diagram
is the provided, unmodified `ai/` package — we treat it exactly like an
external SDK. Our own code never calls `ai.sources.fetch_wikipedia()` (etc.)
directly; every call goes through `AIService`, which is the single seam where
retries, timeouts, logging, caching, and rate limiting live. This means if we
ever needed to add a new cross-cutting concern (e.g. cost telemetry), there is
exactly one file to change.

**Swapping providers costs one config line, not a rewrite.** Because `ai/`
already implements the abstract-base-class pattern (`LLMProvider` with
concrete `AnthropicLLM`/`GeminiLLM`/`OpenAILLM` subclasses, selected via
`LLM_PROVIDER` in `.env`), we proved during development that switching from
Anthropic to Gemini required zero code changes — only an environment variable
change. This is documented directly in the report's "Provider choice" section.

**Our own OOP example.** `StorageBackend` (`src/storage/repository.py`) is an
abstract base class with one concrete implementation, `SQLiteStorage`. It
mirrors the shape of `ai.providers.base.LLMProvider` deliberately, so a future
Postgres-backed implementation could be swapped in without touching any
calling code. This is the inheritance/composition example the rubric asks us
to demonstrate independently of the provided `ai/` package's own pattern.

**Concurrency and graceful degradation.** `fetch_all_sources()` in
`researcher.py` calls Wikipedia, arXiv, and web search concurrently via
`asyncio.gather(..., return_exceptions=True)`, with a per-source timeout. If
one or two sources fail (confirmed in testing: Wikipedia occasionally returns
403 without a proper `User-Agent`, arXiv can time out, DuckDuckGo can
rate-limit), the pipeline still produces a cited answer from whichever
sources succeeded, rather than failing the whole request. This was verified
against real, live failures during development, not just simulated ones.

**Data crossing module boundaries.** No naked dictionaries flow between our
own modules. `ai/sources.py` returns `Source` (a frozen pydantic model);
`ai/synthesizer.py` returns `AnswerWithCitations`. The one deliberate
exception is `StorageBackend`, which accepts plain `dict`s by design — this
keeps the storage layer decoupled from `ai/`'s schemas, so swapping the AI
package's internal types later would not require touching storage code. The
conversion (`[s.model_dump() for s in sources]`) happens once, at the call
site in `researcher.py`.

## If we had to swap providers (Anthropic → OpenAI)

Exactly one file changes: `.env` (`LLM_PROVIDER=openai`, `OPENAI_API_KEY=...`).
No source file needs editing, because `ai.providers.factory.get_llm()` already
handles provider selection, and `AIService`/`researcher.py` only ever depend
on the abstract `LLMProvider` interface, never on a concrete implementation.