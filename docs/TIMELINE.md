# Two-Week Timeline

This is the recommended schedule for the 12-day window between project release (**May 11, 2026**) and submission (**May 23, 2026 at 23:59 (UTC+4)**). Adjust to your team's calendar, but treat the milestone gates as hard deadlines — falling behind by more than a day at any gate means you're going to ship something rushed.

## Phase 1 — Setup (Days 1–2)

**Goal:** team aligned, repo healthy, everyone can run the provided AI module.

- [ ] **Day 1 morning** — Team picks topic. Read the topic's `TOPIC.md` end to end (every member, no skimming).
- [ ] **Day 1 afternoon** — Repo created on GitHub. `main` is protected. `.gitignore` is in place. `.env.example` is committed; nobody pushes a real `.env`.
- [ ] **Day 1 afternoon** — Every team member can run:
  ```bash
  python demo_ai.py --offline
  pytest tests/test_ai_smoke.py
  ```
  in the topic folder. If one teammate can't, fix it before continuing.
- [ ] **Day 2** — Open the tracking issue for the project, listing the 10 build requirements from `SOFTWARE_PROJECT.pdf` §1.1 as checkboxes. Assign owners.
- [ ] **Day 2** — Draft an architecture diagram (one page, boxes and arrows). Discuss as a team. Commit it to `docs/architecture.md`.
- [ ] **Day 2 evening** — Decide your provider stack (LLM, embedding, web search if Topic 4). Document the choice and why.

**Gate to clear:** every member has pushed at least one commit. Architecture diagram is in `main`.

## Phase 2 — Skeleton (Days 3–5)

**Goal:** end-to-end vertical slice working against the provided AI module — one CLI command, one storage write, one happy-path test.

- [ ] **Day 3** — `src/config.py` reads env vars (use `pydantic-settings`). Typed settings exposed.
- [ ] **Day 3–4** — One CLI command works end-to-end: takes input, calls `ai.*`, persists to SQLite, prints output.
- [ ] **Day 4** — First PR merged into `main` (with at least one teammate review).
- [ ] **Day 5** — First three of your own tests written (one per: service layer, storage layer, CLI). All offline.
- [ ] **Day 5** — `requirements.txt` is pinned (every dep has a version).

**Gate to clear:** one happy-path scenario runs from a clean clone via the CLI, persists results, and a test mocks the AI module to confirm the wiring.

## Phase 3 — Concurrency (Days 6–8)

**Goal:** parallel pipeline working and benchmarked. HTTP API up (Topics 1, 2).

- [ ] **Day 6** — Concurrent version of the workload is implemented (`asyncio.gather` or `ProcessPoolExecutor`). Semaphore bound is configurable.
- [ ] **Day 7** — `scripts/bench.py` runs sequential vs concurrent on the same workload, same cache state, and prints a table. Commit the numbers and the command line into the README.
- [ ] **Day 7–8** — HTTP API stood up (Topics 1, 2). The same operations work via `curl`. Curl examples in the README.
- [ ] **Day 8** — At least one concurrency-specific test (e.g.\ "one task raises, gather degrades gracefully").

**Gate to clear:** the README has a table of sequential-vs-concurrent timings and the exact command to reproduce them.

## Phase 4 — Robustness (Days 9–10)

**Goal:** the system handles failures honestly. Coverage ≥ 60%.

- [ ] **Day 9** — Every call to `ai.*` is wrapped: retries with exponential backoff, per-call timeout, structured logging at INFO / DEBUG.
- [ ] **Day 9** — Rate-limit policy implemented (token bucket, sleep-on-429, or equivalent). Configurable.
- [ ] **Day 9** — Input validation at every entry point (CLI, HTTP, file, env). Bad input returns a clean error, not a stack trace.
- [ ] **Day 10** — Inject at least one failure (provider 5xx, timeout, malformed response) and verify the system degrades gracefully. Capture the log output for the report.
- [ ] **Day 10** — `pytest --cov` reports ≥ 60%. Print the result in the README.
- [ ] **Day 10** — `mypy` (or `pyright`) run at least once; record the result.

**Gate to clear:** coverage gate met; one concrete failure-mode story documented and tested.

## Phase 5 — Containerise (Day 11)

**Goal:** `docker build` and `docker run` work from a clean clone on a different machine.

- [ ] **Day 11 morning** — Dockerfile builds successfully from a clean clone. Image size noted.
- [ ] **Day 11 afternoon** — `docker run --env-file .env <image>` runs the demo end-to-end.
- [ ] **Day 11** — `pytest tests/test_ai_smoke.py` (provided) still passes after all your changes. **If it doesn't, stop and fix it.** This is a contract.
- [ ] **Day 11** — `requirements.txt` has every dep pinned. No floating versions.

**Gate to clear:** a teammate who didn't write the Dockerfile can build and run it from scratch.

## Phase 6 — Polish & submit (Day 12)

**Goal:** report, slides, contribution statement, and v1.0-final tag submitted before **May 23, 2026 at 23:59 (UTC+4)**.

- [ ] **Day 12 morning** — Report drafted from `templates/REPORT_TEMPLATE.tex`. Every section answered, no leftover guidance text.
- [ ] **Day 12 midday** — Slides prepared from `templates/SLIDES_TEMPLATE.tex`. ~10 slides, every member knows which slides they own.
- [ ] **Day 12 afternoon** — Contribution statement filled in, signed by all three members.
- [ ] **Day 12 afternoon** — Self-assessment checklist (`SOFTWARE_PROJECT.pdf` §12) ticked. If a box can't be ticked, fix it now.
- [ ] **Day 12 evening** — Tag the final commit on `main` as `v1.0-final`. Push the tag.
- [ ] **Day 12 evening** — Submission email sent to the instructor with: GitHub URL + tag, report PDF, slides PDF, contribution statement PDF, artefacts folder (or link).

## What to do if you fall behind

The right answer is **shrink scope, not skip phases**. Pick one of these in order:

1. Drop the HTTP API if it's not strictly required for your topic (Topic 1 / 2 *do* need it).
2. Drop bonus features (web UI, multi-provider failover, etc.). These are optional.
3. Reduce test coverage from your ambitious 80% target to the minimum 60%.
4. Pre-record the demo so you don't depend on a flaky live network during the defense.

What **not** to drop:
- The provided AI smoke tests must pass.
- The Dockerfile must build.
- The report and slides must be submitted from the provided templates.
- Every member must have a meaningful commit history. Target roughly ≥20%; an undocumented share below 10% triggers the automatic deduction.

## Slack times

Build in slack on Day 4 and Day 9 evenings — these are good moments to catch up on small things that slipped (PR reviews, missing tests, README drift). Don't schedule any deliverable for these slots and your team won't burn out by Day 12.
