# Advanced Bonuses

Up to **+10 bonus points** total. Each bonus must be:

1. **Implemented end-to-end** (not just a stub).
2. **Tested** (you can demonstrate it works without manual narration).
3. **Documented in the report** with the design choice, the trade-offs, and one concrete observation.

If your core implementation is incomplete, bonus features are ignored. **Depth before breadth.**

---

## 1. Multi-provider failover (+3)

**Goal.** If the primary LLM/embedding/web-search provider fails, the system transparently retries against a configured secondary.

**Acceptance criteria.**
- A `FailoverProvider` class wraps two or more concrete providers and tries them in order.
- A failure is defined as: `ProviderError`, HTTP 5xx, HTTP 429 after the retry budget, or timeout.
- A chaos test demonstrates the failover: the primary is monkey-patched to raise, the secondary returns a valid result, the call succeeds.
- The report names which provider was primary and explains why.

**Skeleton:**
```python
class FailoverLLM(LLMProvider):
    def __init__(self, providers: list[LLMProvider]) -> None:
        if not providers:
            raise ValueError("at least one provider required")
        self.providers = providers
        self.logger = logging.getLogger(__name__)

    def complete(self, prompt: str, *, json_schema=None, max_tokens=1024) -> str:
        last_error: Exception | None = None
        for i, p in enumerate(self.providers):
            try:
                return p.complete(prompt, json_schema=json_schema, max_tokens=max_tokens)
            except ProviderError as e:
                self.logger.warning(
                    "provider_failed", extra={"index": i, "name": type(p).__name__, "error": str(e)}
                )
                last_error = e
        raise ProviderError(f"all providers failed; last: {last_error}")
```

**Test it:**
```python
def test_failover_uses_secondary_when_primary_fails():
    primary = Mock(spec=LLMProvider)
    primary.complete.side_effect = ProviderError("upstream down")
    secondary = FakeLLM(response="from secondary")
    out = FailoverLLM([primary, secondary]).complete("anything")
    assert out == "from secondary"
```

---

## 2. Cost telemetry (+2)

**Goal.** Every AI call records token counts and a $-per-call estimate. A CLI command `cost-report` summarises spend.

**Acceptance criteria.**
- A `CostMeter` class records (provider, model, prompt_tokens, completion_tokens, dollars, timestamp) for every AI call.
- Pricing comes from a configurable table (a JSON or Python dict). Defaults match each provider's published pricing.
- `python -m yourpackage cost-report --since 24h` prints totals: total $ spent, by-provider breakdown, top-5 most expensive prompts.
- Storage: SQLite or append-only JSONL.

**Skeleton (pricing table):**
```python
PRICING_USD_PER_1K_TOKENS: dict[tuple[str, str], tuple[float, float]] = {
    # (provider, model): (prompt_per_1k, completion_per_1k)
    ("anthropic", "claude-sonnet-4-6"):    (0.003, 0.015),
    ("openai", "gpt-4o-mini"):             (0.00015, 0.0006),
    ("openai", "text-embedding-3-small"):  (0.00002, 0.0),
    ("gemini", "gemini-2.0-flash"):        (0.000075, 0.0003),
}

def estimate_cost(provider: str, model: str, prompt_t: int, completion_t: int) -> float:
    p, c = PRICING_USD_PER_1K_TOKENS.get((provider, model), (0.0, 0.0))
    return (prompt_t / 1000) * p + (completion_t / 1000) * c
```

---

## 3. GitHub Actions CI (+2)

**Goal.** Every PR runs lint + type-check + tests + docker build before it can be merged.

**Acceptance criteria.**
- `.github/workflows/ci.yml` runs on `pull_request` events.
- Jobs: `lint` (ruff or flake8), `typecheck` (mypy or pyright), `test` (pytest + coverage gate), `docker` (`docker build .`).
- Failing checks block merge (configure branch protection accordingly).
- Coverage threshold is enforced (`pytest --cov-fail-under=60`).

**Skeleton (`.github/workflows/ci.yml`):**
```yaml
name: CI
on: [pull_request]

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"
      - run: pip install -r requirements.txt
      - run: pip install ruff mypy pytest-cov
      - name: Lint
        run: ruff check src/ tests/
      - name: Type check
        run: mypy src/
      - name: Test
        run: pytest --cov=src --cov-fail-under=60 --cov-report=term-missing
      - name: Docker build
        run: docker build -t finalproj .
```

**Bonus to the bonus:** publish the image to GHCR on `main` merges.

---

## 4. OpenTelemetry tracing (+2)

**Goal.** Every external call is a span with attributes (provider, model, latency, status). Traces export to console or to a docker-compose-attached Jaeger.

**Acceptance criteria.**
- `opentelemetry-api`, `opentelemetry-sdk`, and an exporter (console at minimum) installed.
- Every call to `ai.*`, every HTTP fetch, every SQLite query is wrapped in a span.
- Spans have meaningful attributes: `provider`, `model`, `http.url`, `db.statement`, `duration_ms`, `error`.
- A `docker-compose.yml` (optional) spins up Jaeger so you can view the traces in a UI.

**Skeleton:**
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor

trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(ConsoleSpanExporter())
)
tracer = trace.get_tracer(__name__)

def describe(image_path: str) -> ItemDescription:
    with tracer.start_as_current_span("ai.describe_item") as span:
        span.set_attribute("provider", os.getenv("LLM_PROVIDER"))
        span.set_attribute("model",    os.getenv("LLM_MODEL"))
        try:
            result = ai.describe_item(image_path, "")
            span.set_attribute("status", "ok")
            return result
        except ProviderError as e:
            span.set_attribute("status", "error")
            span.record_exception(e)
            raise
```

---

## 5. Web UI (+2)

**Topics 1, 2, 4.** A simple front-end exercising the same business logic the CLI / HTTP API use.

**Acceptance criteria.**
- Streamlit, Gradio, or htmx (your choice).
- The UI **does not** call providers directly; it goes through your service layer.
- At least one realistic workflow works end-to-end (e.g. upload meal photo → see kcal table).
- The UI is one file or a small directory. Don't over-engineer it.
- Loads inside the Docker image (extra port exposed if needed).

**Streamlit skeleton (Topic 2):**
```python
import streamlit as st
from src.core.analyzer import analyze_meal

st.title("Food Analyzer")
uploaded = st.file_uploader("Upload a meal photo", type=["png", "jpg", "jpeg"])
if uploaded:
    result = analyze_meal(uploaded)
    st.dataframe(result.to_dataframe())
    st.metric("Total kcal", f"{result.totals.kcal:.0f}")
```

---

## 6. Streaming responses (+2)

**Topics 3, 4.** Use streaming where supported so the CLI prints tokens as they arrive.

**Acceptance criteria.**
- The LLM provider call uses the streaming endpoint (not the blocking one).
- The CLI command writes tokens to stdout as they arrive.
- Backpressure is handled (you don't buffer the whole response before printing).
- The report explains where streaming is appropriate vs. where it isn't.

**Skeleton (OpenAI streaming via the SDK):**
```python
def complete_stream(client, prompt: str) -> Iterator[str]:
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )
    for event in stream:
        chunk = event.choices[0].delta.content
        if chunk:
            yield chunk

# CLI:
for tok in complete_stream(client, prompt):
    print(tok, end="", flush=True)
```

**Caveat.** Streaming and JSON-schema enforcement don't always play nicely. If your project depends on structured outputs, stream only the prose parts.

---

## 7. Token-aware rate limiter (+2)

**Goal.** Beyond request-count limiting, track tokens-per-minute against the provider's documented limit and back off when nearing it.

**Acceptance criteria.**
- A `TokenBudget` class tracks tokens consumed in a sliding window.
- Before each AI call, the wrapper checks the budget; if the next call would exceed it, the wrapper sleeps until headroom opens.
- The TPM limit is configurable per provider (each has different limits).
- The report shows a test that forces budget exhaustion and observes correct back-off.

**Skeleton:**
```python
import asyncio, time
from collections import deque

class TokenBudget:
    def __init__(self, tokens_per_minute: int) -> None:
        self.tpm = tokens_per_minute
        self._events: deque[tuple[float, int]] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self, estimated_tokens: int) -> None:
        while True:
            wait = 0.0
            async with self._lock:
                now = time.monotonic()
                # drop events older than 60s
                while self._events and self._events[0][0] < now - 60:
                    self._events.popleft()
                used = sum(t for _, t in self._events)
                if used + estimated_tokens <= self.tpm:
                    self._events.append((now, estimated_tokens))
                    return
                wait = 60 - (now - self._events[0][0])
            await asyncio.sleep(max(wait, 0.1))
```

---

## 8. Multi-stage Dockerfile (+1)

**Goal.** Build stage compiles wheels; runtime stage ships only what's needed. Final image ≤ 250 MB.

**Acceptance criteria.**
- Two `FROM` directives.
- Build stage installs dependencies into a virtualenv or wheelhouse.
- Runtime stage copies only the venv + the application code.
- Image size reported in the README (use `docker images`).

**Skeleton:**
```dockerfile
# ---- Build stage ----
FROM python:3.12-slim AS builder
WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Runtime stage ----
FROM python:3.12-slim
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY . .
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser
CMD ["python", "-m", "yourpackage", "demo"]
```

Expected size reduction: ~150 MB (full python:3.12-slim with deps) → ~80 MB (slim with just the venv layer).
