# _[Project Name]_

> _[One-sentence elevator pitch.]_ For example: *"A Smart Lost & Found service that matches lost and found items via a vision-language model and embedding similarity."*

**Team:** _[Team Name]_  •  **Topic:** _[1 / 2 / 3 / 4]_  •  **Course:** AI-ENG-110 Software Engineering, AI Academy

**Due:** **May 23, 2026 at 23:59 (UTC+4)**

---

## Quick start

```bash
# 1. Clone & install
git clone https://github.com/your-team/your-repo
cd your-repo
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env       # then fill in real API keys
# (DO NOT commit .env — it is in .gitignore)

# 3. Run the smoke tests
pytest tests/test_ai_smoke.py -v   # provided smoke tests
pytest                              # your full suite

# 4. Run the demo
python -m <yourpackage> demo
```

## Run with Docker

```bash
docker build -t finalproj .
docker run --env-file .env -p 8000:8000 finalproj
# for Topics 1 & 2 with HTTP server: hit http://localhost:8000
```

## Environment variables

| Variable | Required? | Default | What it controls |
|---|---|---|---|
| `LLM_PROVIDER` | yes | `anthropic` | `anthropic` \| `openai` \| `gemini` |
| `LLM_MODEL` | yes | (provider-specific) | model id |
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `GOOGLE_API_KEY` | one of, yes | — | key for the chosen provider |
| `EMBEDDING_PROVIDER` | sometimes | `openai` | `openai` \| `gemini` (Topics 1, 3 only) |
| `LOG_LEVEL` | no | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `DATABASE_URL` | no | `sqlite:///./app.db` | SQLite path |
| `MAX_PARALLEL` | no | `10` | semaphore bound for concurrent calls |
| _[...]_ | _[...]_ | _[...]_ | _[...]_ |

The full list is in `.env.example`. **Do not commit a real `.env`.**

## How to run the demo

```bash
# CLI
python -m <yourpackage> <command> [args]

# HTTP (Topics 1, 2)
uvicorn src.api:app --host 0.0.0.0 --port 8000
curl -X POST http://localhost:8000/<endpoint> ...
```

_[Add the exact curl commands here, with sample input and expected output.]_

## Sequential vs concurrent benchmark

| Workload | $N$ | Sequential | Concurrent (sem=10) | Speedup |
|---|---|---|---|---|
| _[describe the workload]_ | _[20]_ | _[42.1 s]_ | _[7.3 s]_ | _[5.8×]_ |

**Reproduce:**
```bash
python scripts/bench.py --N 20
```

Bottleneck after the parallelization is **_[what bottleneck — e.g. provider rate limit, RTT, DB writes]_**. See `report/report.pdf` §_[N]_ for details.

## Testing

```bash
pytest --cov=src --cov-report=term-missing
```

- Total coverage: **_[72]_%**
- Provided AI smoke tests: **passing**
- All tests run offline (AI module mocked; HTTP layer mocked with `respx` / `unittest.mock`).

## Project layout

```
.
├── ai/                       # PROVIDED — do not modify
├── src/
│   ├── config.py
│   ├── models.py
│   ├── services/             # wrappers around ai/, retries, logging
│   ├── core/                 # business logic
│   ├── concurrency/          # async orchestration
│   ├── storage/              # SQLite + filesystem
│   ├── cli.py
│   └── api.py                # HTTP server (Topics 1, 2)
├── tests/
├── data/                     # sample inputs
├── artefacts/                # outputs of demo runs
├── scripts/
│   ├── demo.py
│   └── bench.py
├── report/
│   ├── report.tex
│   └── report.pdf
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

## Architecture in one diagram

_[Embed your architecture diagram PNG here, the same one as in the report and slides.]_

```
+-------+   +----------+
|  CLI  |   | HTTP API |
+---+---+   +----+-----+
    |            |
    v            v
+---------+ +-----------+
|  core   | | concurrency|
+----+----+ +-----+-----+
     |             |
     v             v
+---------------------+   +----------+
| service (retries,   |-->|  ai/     | (provided)
| cache, logging)     |   +----------+
+----------+----------+
           |
           v
   +--------------+
   | SQLite + FS  |
   +--------------+
```

## Limitations

- _[Brittleness 1, e.g. no multi-provider failover]_
- _[Brittleness 2]_
- _[Brittleness 3]_

See `report/report.pdf` §_[N]_ for a full discussion.

## Tools & acknowledgements

We used AI assistants (Claude / Cursor / etc.) as described in §_[N]_ of the report and in `templates/CONTRIBUTION_STATEMENT.md`.

## License

This is academic coursework, not a published library. _[Optionally add MIT / Apache-2.0 etc. if you want it to be reusable.]_
