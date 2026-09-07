<!-- 
This is the pull-request template students should put in their repo at
.github/pull_request_template.md. It enforces a minimum standard of
PR hygiene: what changed, why, how it was tested, what isn't covered.
-->

## What this PR changes

<!-- 1-3 sentences. The reviewer should know the scope before reading any diff. -->

## Why

<!-- Link to the tracking issue, the rubric item, or the design decision. -->

Closes #_[issue]_

## How I tested it

- [ ] `pytest` passes locally
- [ ] `pytest tests/test_ai_smoke.py` (provided smoke tests) passes
- [ ] Coverage stayed at or above the threshold (run `pytest --cov`)
- [ ] If touching `Dockerfile` or `requirements.txt`: `docker build .` succeeds

<!-- Add any manual test steps reviewers should run. -->

## What this PR does NOT do

<!-- Honest scope statement. "Doesn't add retries to the embedding path yet — tracked in #N." -->

## Checklist

- [ ] No `.env`, secrets, or other private files in the diff
- [ ] No `TODO` / `FIXME` comments left in the changed code
- [ ] Type hints on every new public function / method
- [ ] No `except Exception: pass` or bare `except:`
- [ ] No `print()` for runtime diagnostics — use `logging`
- [ ] The provided `ai/` package's public interface is unchanged
- [ ] If using an AI assistant: I can explain every line of code below

## AI assistant disclosure

<!-- Be specific. "Cursor scaffolded retry.py; I rewrote the backoff logic." -->

_[none / describe]_

## Screenshots (if UI-affecting)

_[paste here]_
