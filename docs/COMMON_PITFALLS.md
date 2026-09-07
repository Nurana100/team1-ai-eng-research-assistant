# Common Pitfalls

This is the long-form version of the pitfall list in `SOFTWARE_PROJECT.pdf` Appendix D. Every pitfall below has cost previous students real grade points. Read once at the start of the project; re-read on Day 9 before robustness work.

For each pitfall: **symptom** (what you see), **why it happens**, **how to detect**, **how to fix**.

---

## 1. Naked `except` / `except Exception: pass`

**Symptom.** Bugs vanish. Tests pass mysteriously. Then production silently produces wrong answers for hours and you can't reconstruct what happened.

**Why.** `except Exception:` swallows *everything* — `KeyError`, `ZeroDivisionError`, your own `ValueError`. Without a `raise`, the program continues as if nothing went wrong. `except:` (without a class) also catches `KeyboardInterrupt` and `SystemExit`, which is worse.

**How to detect.** Grep your repo:
```bash
git grep -nE "except\s*:|except\s+Exception\s*:\s*pass"
```
Both forms are a rubric deduction.

**Fix.** Always catch a specific class, log the failure with context, then either re-raise, return a structured error, or transform it into a domain-specific exception. Example:
```python
try:
    response = self._ai.complete(prompt)
except ProviderError as e:
    logger.warning("ai_call_failed", extra={"prompt_id": pid, "error": str(e)})
    raise   # or: return ErrorResponse(reason="ai_unavailable")
```

---

## 2. Unbounded concurrency

**Symptom.** Locally things are fine. Then you run 200 articles through the pipeline at once and the provider returns HTTP 429 for everything for the next hour. Your tests pass; your demo fails on grading day.

**Why.** `await asyncio.gather(*[fetch(u) for u in urls])` with 200 URLs means 200 simultaneous HTTP calls. Every provider rate-limits.

**How to detect.** Look at your `gather`s. If there's no `Semaphore` around them, you have this bug.

**Fix.** Bound concurrency with a semaphore:
```python
sem = asyncio.Semaphore(10)
async def _one(u):
    async with sem:
        return await fetch(u)
results = await asyncio.gather(*[_one(u) for u in urls], return_exceptions=True)
```
Configure the bound via env var so you can tune it.

---

## 3. Hard-coded API keys

**Symptom.** A teammate pushes a key in `src/config.py` because "we'll move it later". You don't. The repo goes public. Within hours, your key is being used by strangers.

**Why.** Pressure + laziness + "I'll fix it before merging". You won't.

**How to detect.** Grep before every commit:
```bash
git grep -E "sk-[a-zA-Z0-9_-]{20,}|AIza[a-zA-Z0-9_-]{20,}"
```
GitHub also scans public repos and emails you if it finds one.

**Fix.**
- Every secret lives in `.env`. `.env` is in `.gitignore`. `.env.example` lists keys with empty values.
- If a real key has been committed, **rotate it immediately**. Don't try to "delete" it — the git history still has it.

This is a **−10 point automatic deduction**, so it costs more than any other mistake on this list.

---

## 4. `print()` for runtime diagnostics

**Symptom.** Hard to filter logs. Hard to suppress in production. Hard to switch log level without editing code. Your Docker logs are a wall of unstructured text.

**Why.** Habits from notebooks. `print` is fast to type and "works".

**How to detect.**
```bash
git grep -n "print(" src/
```
If you find `print(...)` anywhere in `src/`, replace it.

**Fix.** Use the stdlib `logging` module. Configure level from env:
```python
import logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

logger.info("registering_item", extra={"id": item_id, "kind": "lost"})
```
`print` is allowed in CLI output (stuff the user sees in their terminal). It is *not* allowed for diagnostics.

---

## 5. Tests that hit the network

**Symptom.** Tests pass locally. Tests fail in CI when GitHub Actions is rate-limited or the provider has an outage. Coverage looks high but the offline contract is broken.

**Why.** Easier to write a test that just calls the real API than to mock it.

**How to detect.** Pull the network cable and run `pytest`. If anything fails, you have network-dependent tests.

**Fix.** Mock at the right boundary:
```python
# pytest-httpx for httpx-based code
async def test_fetches_wikipedia(httpx_mock):
    httpx_mock.add_response(
        url="https://en.wikipedia.org/w/api.php",
        json=[None, ["Photosynthesis"], None, None],
    )
    sources = await fetch_wikipedia("photosynthesis")
    assert sources[0].origin == "wikipedia"

# unittest.mock for the AI module
def test_register_calls_describe(monkeypatch):
    fake = FakeVLM()
    item = register("img.png", "umbrella", vlm=fake)
    assert fake.calls
```

**Rule of thumb.** If you can run your test suite on a plane, you've done it right.

---

## 6. Dockerfile that doesn't actually build

**Symptom.** You only ran `docker build` once, two weeks ago, on the laptop where you wrote it. On Day 12 you re-run it on a clean clone and it fails because you forgot to commit `requirements.txt` updates, or you assumed a system library was installed.

**Why.** Docker builds were treated as a one-time exercise rather than part of the workflow.

**How to detect.** Build from a clean clone on a different machine **at the end of every phase**, not just on Day 11.

**Fix.**
- Add `docker build .` to your GitHub Actions CI if you set it up (it's a +2 bonus).
- Even without CI, run `docker build .` after every dependency change.
- Use a `.dockerignore` that excludes `.git`, `.venv`, `__pycache__`, `tests/` (unless you run tests in CI inside the container), `.env`, and `report/*.pdf`.

---

## 7. Commit imbalance

**Symptom.** One teammate has 200 commits, two have 5 each. The rubric targets roughly ≥20% per member; an undocumented share below 10% loses 5 points.

**Why.** Pair-programming via screen-share + one person typing is fine for learning but produces no commit signal for the silent partner.

**How to detect.**
```bash
git shortlog -sn
```

**Fix.**
- Distribute the 10 deliverables across members from Day 2.
- Open PRs from your own branch, even for small things — typo fixes, comment improvements, README updates.
- Pair on hard PRs, but split big files: one person does retries, another does logging, even if you sit together.
- The contribution statement is your chance to explain unusual imbalances (illness, real emergency). Be specific.

---

## 8. Test-set leakage analog

**Symptom.** Your tests use real provider responses captured during development. When you tune a prompt to fix a flaky test, you're effectively training on the test set.

**Why.** It feels productive. The test "fails", you change the prompt, the test "passes", you ship.

**How to detect.** Did anyone re-record a fixture to make a test pass without changing the underlying logic?

**Fix.**
- Captured fixtures are reference data, not ground truth. Don't re-record them every time something changes.
- When a test breaks, ask: did the production code change incorrectly, or did the contract change? Fix at that layer.
- For prompt-tuning, evaluate on a held-out set you don't see during iteration.

---

## 9. `.env` accidentally committed

**Symptom.** You see `.env` in `git log -- .env`. Your real API keys are now in the repo history.

**Why.** Either `.gitignore` was added after the first commit of `.env`, or someone `git add .`-ed too aggressively.

**How to detect.**
```bash
git log --all --oneline -- .env
```

**Fix.**
1. **Rotate the keys.** Right now. Before doing anything else.
2. Remove the file from history. `git filter-repo` is the right tool; `git rm --cached .env && commit` only removes it going forward.
3. Confirm `.env` is in `.gitignore`.
4. Push `--force-with-lease` (only if the repo is private and your team agrees).

If the repo was public for any window, **assume the keys are compromised**. Rotate.

---

## 10. Modifying `ai/`

**Symptom.** You find a small bug in `ai/vlm.py` and fix it in your repo. Smoke tests still pass locally. But the grader's harness checks for an unchanged interface.

**Why.** It's tempting; the bug looks one-line. But the `ai/` package is a contract you signed.

**How to detect.**
```bash
diff -r <provided-topic-folder>/ai/ <your-repo>/ai/
```
This should produce no output.

**Fix.**
- File an issue with the instructor describing the bug, the reproducer, and your proposed fix.
- Work around it in your service layer in the meantime.

---

## 11. Path traversal in blob storage (Topics 1, 2)

**Symptom.** A user uploads an image named `../../etc/passwd`. Your code happily writes to `/etc/passwd` (or reads from it).

**Why.** You used `os.path.join(storage_dir, user_supplied_name)` without sanitisation.

**How to detect.** Try uploading a file named `../../foo.png` to your HTTP endpoint. What does the resulting filesystem look like?

**Fix.**
```python
from pathlib import Path

def safe_storage_path(storage_dir: Path, name: str) -> Path:
    # generate the path from a UUID rather than user input
    safe = uuid.uuid4().hex + Path(name).suffix
    p = (storage_dir / safe).resolve()
    if not str(p).startswith(str(storage_dir.resolve())):
        raise ValueError("path escapes storage dir")
    return p
```

---

## 12. Naked dictionaries across module boundaries

**Symptom.** A function takes `dict` and returns `dict`. Six months later, nobody knows what shape the dict has. Tests break when a key is renamed.

**Why.** Faster to type in the moment.

**How to detect.** Look at your function signatures. Any `-> dict` or `: dict` parameter that flows between modules is a candidate.

**Fix.** Use `@dataclass` (or `pydantic.BaseModel`) for anything that crosses a module boundary. The provided AI module already does this — copy the pattern.

```python
@dataclass(frozen=True)
class RegisteredItem:
    id: int
    status: str          # "lost" | "found"
    description: ItemDescription
    created_at: datetime
```

---

## 13. TODOs left in shipped code

**Symptom.** A grader greps for `TODO`/`FIXME`/`XXX` and finds eleven. You lose 3 points.

**Why.** Markers added during development weren't cleaned up.

**How to detect.**
```bash
git grep -nE "TODO|FIXME|XXX" -- src/ tests/
```

**Fix.**
- If the TODO is real work, convert it to a GitHub issue and delete the comment.
- If the TODO is "explain later", write the explanation now.
- The report template uses red `[TODO: ...]` markers deliberately so they're visible in the PDF — those *should* be replaced before submission.

---

## 14. The "it works on my laptop" Docker bug

**Symptom.** `docker run` works on your Mac. Fails on the grader's Linux machine because of an architecture or library mismatch.

**Why.** You used `--platform=linux/arm64` implicitly. Or you depend on a binary that's only in Mac homebrew.

**How to detect.** Build explicitly for `linux/amd64`:
```bash
docker buildx build --platform linux/amd64 -t finalproj .
```

**Fix.** Always specify platform in the Dockerfile (or document the build command). Test on at least two machines before submission.
