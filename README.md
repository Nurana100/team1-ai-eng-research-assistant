# AI Research Assistant

> An async research assistant that queries Wikipedia, arXiv, and web search concurrently, then synthesizes a single cited answer using an LLM.

**Team:** Team1  •  **Topic:** 4 — Async Research Assistant  •  **Course:** AI-ENG-110 Software Engineering, AI Academy

---

## Quick start

```bash
# 1. Clone & install
git clone https://github.com/Nurana100/team1-ai-eng-research-assistant
cd team1-ai-eng-research-assistant
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure (a .env in the project root is loaded automatically)
cp topic-4-research-assistant/.env.example .env
# then fill in a real API key (see Environment variables below)
# DO NOT commit .env — it is in .gitignore

# 3. Run the provided smoke tests
pytest topic-4-research-assistant/tests/test_ai_smoke.py -v

# 4. Run the full test suite
pytest --cov=src --cov-report=term-missing

# 5. Run the demo
python -m src.cli ask "what is quantum computing"
```

## Run with Docker

```bash
docker build -t research-assistant .
docker run --rm --env-file .env research-assistant python -m src.cli ask "Quantum Entanglement"
```

Image size: 409 MB on disk (96.8 MB compressed). The container runs as a non-root user and never bakes `.env` into the image — keys are supplied only at `docker run` time.

## Environment variables

| Variable | Required? | Default | What it controls |
|---|---|---|---|
| `LLM_PROVIDER` | yes | `anthropic` | `anthropic` \| `openai` \| `gemini` |
| `LLM_MODEL` | yes | (provider-specific) | model id, e.g. `gemini-3.6-flash` |
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `GOOGLE_API_KEY` | one of, yes | — | key for the chosen provider |
| `WEB_SEARCH_PROVIDER` | no | `tavily` | `tavily` \| `serper` \| `duckduckgo` |
| `TAVILY_API_KEY` / `SERPER_API_KEY` | one of, if using that provider | — | web search provider key |
| `LOG_LEVEL` | no | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `CACHE_TTL_SECONDS` | no | `86400` | how long fetched sources are cached |
| `MAX_PARALLEL` | no | `5` | semaphore bound for concurrent source fetches |

The full list with defaults is in `topic-4-research-assistant/.env.example`. **Do not commit a real `.env`.**

**Recommended free-tier setup** (no billing required): `LLM_PROVIDER=gemini` with a free key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey), and `WEB_SEARCH_PROVIDER=duckduckgo` (no key needed, requires `pip install duckduckgo-search`).

## How to run the demo

```bash
# Ask a single question
python -m src.cli ask "how do transformer models handle long context windows?"

# Restrict to specific sources
python -m src.cli ask "explain CRISPR-Cas9" --sources wiki,arxiv

# Bypass the cache
python -m src.cli ask "current state of fusion energy" --no-cache

# Run all 5 required demo questions end-to-end
python scripts/run_demo.py
```

Example output:

```
Answer:
Quantum computing exploits phenomena such as superposition, interference,
and entanglement to process information [1]. ...

Sources:
[1] Quantum computing
    https://en.wikipedia.org/wiki/Quantum_computing
[2] Quantum computing scaling laws
    https://en.wikipedia.org/wiki/Quantum_computing_scaling_laws
```

## Sequential vs concurrent benchmark

Reproduce with:

```bash
python scripts/bench.py
```

Query "Quantum Entanglement", 3 runs, cache off, one shared httpx client, live network:

| Mode       | Mean wall-clock (s) |
|------------|---------------------|
| Sequential | 1.19                |
| Parallel   | 0.57                |

**Speedup: 2.10x.** Sequential time is roughly the sum of the three fetches (Wikipedia ≈ 0.45 s, arXiv ≈ 0.40 s, web ≈ 0.34 s); parallel time is close to the slowest single fetch plus overhead. Raw output: `artefacts/bench_results.txt`. Numbers vary slightly between runs because of network timing.

## Testing

```bash
pytest --cov=src --cov-report=term-missing
```

- Total coverage: **76%** (target: ≥60%)
- 51 tests pass: 35 written by the team + 16 provided AI smoke tests (16/16 passing)
- Our tests run fully offline — the AI module and HTTP calls are mocked via `StubAIService`, `StubLLM`, `StubWebSearch`, and an offline `httpx` client factory (see `tests/conftest.py`).

## Project layout

```
.
├── ai/                         # PROVIDED — do not modify
│   ├── sources.py              # fetch_wikipedia, fetch_arxiv, fetch_web
│   ├── synthesizer.py          # synthesize()
│   └── providers/              # LLMProvider ABC: Anthropic, OpenAI, Gemini
├── src/
│   ├── config.py               # typed settings from .env (pydantic-settings)
│   ├── cli.py                  # CLI entry point, input validation, clean errors
│   ├── core/
│   │   └── researcher.py       # orchestration: concurrency, graceful degradation
│   ├── services/
│   │   ├── ai_service.py       # wraps ai/* with retries, timeouts, logging, caching
│   │   ├── cache.py            # TTLCache
│   │   └── rate_limiter.py     # per-source RateLimiter
│   └── storage/
│       └── repository.py       # StorageBackend (ABC) + SQLiteStorage
├── tests/                      # 35 tests, fully offline
├── data/                       # sample research questions
├── scripts/
│   ├── run_demo.py             # runs all 5 required demo questions
│   └── bench.py                # sequential vs parallel benchmark
├── artefacts/                  # demo and benchmark outputs
├── docs/
│   └── architecture.md         # module map and design rationale
├── topic-4-research-assistant/ # course-provided folder (ai/, data/, smoke tests, .env.example)
├── Dockerfile
├── .dockerignore
├── requirements.txt
├── mypy_report.txt
└── README.md
```

## Architecture

See `docs/architecture.md` for the full module map and design rationale, including:
- Why `AIService` is the single seam for retries/timeouts/logging/caching/rate-limiting around the provided `ai/` package
- How switching LLM providers (we run on Gemini by default) costs one `.env` line, not a code change
- The `StorageBackend` abstract base class as our own inheritance/composition example, separate from `ai/`'s own `LLMProvider` pattern

## Failure modes

- **arXiv HTTP 406:** during development the arXiv fetch failed with `406 Not Acceptable`. The pipeline still produced a cited answer from Wikipedia and DuckDuckGo, because sources are fetched with `asyncio.gather(return_exceptions=True)` and per-source timeouts (graceful degradation). The failure was transient; later runs used all three sources.
- **Missing keys / retired model:** the CLI prints one clean `Error: ...` line instead of a stack trace (for example, a `404` after Google retired `gemini-2.0-flash`).

## Limitations

- **Wikipedia's opensearch endpoint is sensitive to query phrasing.** Full natural-language questions (e.g. "what is quantum computing") sometimes return zero matches even when a keyword-style query ("quantum computing") succeeds. A production system might strip leading question words before querying.
- **Truncated answers with Gemini.** In the Docker run, the synthesized answer was once cut off mid-sentence. The synthesizer lives in the provided `ai/` package, which we did not modify.
- **No multi-provider failover.** If the configured LLM provider is down or the account has no credit, the pipeline returns a clear error rather than automatically trying a second provider.
- **DuckDuckGo web search can rate-limit or return empty results** without warning when queried repeatedly in a short window; this is a known constraint of the free, keyless backend.
- **SQLite storage is single-writer**, chosen for simplicity within course scope; a production deployment would need Postgres for concurrent writers.

See `report/report.pdf` for a full discussion, including the required failure-mode analysis.

## Tools & acknowledgements

We used Claude (Anthropic) as an AI coding assistant throughout development — for debugging import/path issues, writing test scaffolding, wiring the retry/caching/storage layers, and drafting this README. All code was reviewed and is understood by the team; every PR went through review before merging. Full disclosure is in `templates/report.pdf` §9 and `templates/CONTRIBUTION_STATEMENT.pdf`.

## License

This is academic coursework for AI-ENG-110, AI Academy, not a published library.
