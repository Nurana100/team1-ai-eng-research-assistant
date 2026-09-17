\# AI Research Assistant

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

# 2. Configure
cp topic-4-research-assistant/.env.example topic-4-research-assistant/.env
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
docker run --rm --env-file topic-4-research-assistant/.env research-assistant
```

This runs the 5-question demo (`scripts/run_demo.py`) end-to-end, printing a cited answer for each question. The container runs as a non-root user and never bakes `.env` into the image — keys are supplied only at `docker run` time.

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
Answer:
Quantum computing exploits phenomena such as superposition, interference,
and entanglement to process information [1]. Large-scale quantum computers
could break widely used encryption schemes [1] ...
Sources:
[1] Quantum computing
https://en.wikipedia.org/wiki/Quantum_computing
[2] Quantum computing scaling laws
https://en.wikipedia.org/wiki/Quantum_computing_scaling_laws

## Testing

```bash
pytest --cov=src --cov-report=term-missing
```

- Total coverage: **65%** (target: ≥60%)
- Provided AI smoke tests: **passing** (16/16)
- All 49 tests run fully offline — the AI module and all HTTP calls are mocked via `StubAIService`, `StubLLM`, `StubWebSearch`, and an offline `httpx` client factory that refuses real network calls (see `tests/conftest.py`).
- `src/cli.py` shows 0% in the coverage report by design: its tests run the CLI as a subprocess to exercise real end-user behavior, which `pytest-cov` does not track across process boundaries. The CLI's actual logic (argument parsing, validation) is covered by 4 passing subprocess tests.

## Project layout
.
├── ai/ # PROVIDED — do not modify
│ ├── sources.py # fetch_wikipedia, fetch_arxiv, fetch_web
│ ├── synthesizer.py # synthesize()
│ └── providers/ # LLMProvider ABC: Anthropic, OpenAI, Gemini
├── src/
│ ├── config.py # typed settings from .env (pydantic-settings)
│ ├── cli.py # CLI entry point, input validation
│ ├── core/
│ │ └── researcher.py # orchestration: concurrency, graceful degradation
│ ├── services/
│ │ ├── ai_service.py # wraps ai/* with retries, timeouts, logging, caching
│ │ ├── cache.py # TTLCache
│ │ └── rate_limiter.py # per-source RateLimiter
│ └── storage/
│ └── repository.py # StorageBackend (ABC) + SQLiteStorage
├── tests/ # 49 tests, fully offline
├── data/ # sample research questions
├── scripts/
│ └── run_demo.py # runs all 5 required demo questions
├── docs/
│ └── architecture.md # module map and design rationale
├── topic-4-research-assistant/ # course-provided folder (ai/, data/, smoke tests, .env.example)
├── Dockerfile
├── .dockerignore
├── requirements.txt
├── mypy_report.txt
└── README.md

## Architecture

See `docs/architecture.md` for the full module map and design rationale, including:
- Why `AIService` is the single seam for retries/timeouts/logging/caching/rate-limiting around the provided `ai/` package
- How switching LLM providers (we run on Gemini by default) costs one `.env` line, not a code change
- The `StorageBackend` abstract base class as our own inheritance/composition example, separate from `ai/`'s own `LLMProvider` pattern

## Limitations

- **Wikipedia's opensearch endpoint is sensitive to query phrasing.** Full natural-language questions (e.g. "what is quantum computing") sometimes return zero matches even when a keyword-style query ("quantum computing") succeeds. Confirmed during development; a production system might strip leading question words before querying.
- **No multi-provider failover.** If the configured LLM provider is down or the account has no credit, the pipeline returns a clear error rather than automatically trying a second provider.
- **DuckDuckGo web search can rate-limit or return empty results** without warning when queried repeatedly in a short window; this was observed during testing and is a known constraint of the free, keyless search backend.
- **SQLite storage is single-writer**, chosen for simplicity within course scope; a production deployment would need Postgres for concurrent writers.

See `report/report.pdf` for a full discussion, including the required failure-mode analysis.

## Tools & acknowledgements

We used Claude (Anthropic) as an AI coding assistant throughout development — for debugging import/path issues, writing test scaffolding, wiring the retry/caching/storage layers, and drafting this README. All code was reviewed and is understood by the team; every PR went through review before merging. Full disclosure is in `report/report.pdf` §9 and `templates/CONTRIBUTION_STATEMENT.md`.

## License

This is academic coursework for AI-ENG-110, AI Academy, not a published library.
