# AI Engineering — Software Engineering Final Project (v2)

**AI Academy, National AI Center · Spring 2026**

This is the distributable package for the Software Engineering final project. It contains everything students need: the project brief, the topic codebases (with their provided AI modules), report and slide templates, and documentation.

**Released:** May 11, 2026
**Due:** **May 23, 2026 at 23:59 (UTC+4)**

---

## What to read first

1. **`SOFTWARE_PROJECT.pdf`** — the authoritative project description, requirements, rubric, deadlines. Start here.
2. **`docs/TIMELINE.md`** — recommended 12-day milestone schedule.
3. Your chosen topic's **`TOPIC.md`** — what the provided AI module does and what you build around it.
4. **`docs/COMMON_PITFALLS.md`** — every mistake previous students have made. Read before Day 9.

## What's where

```
AIENG_FinalProject_v2/
│
├── SOFTWARE_PROJECT.pdf         ← the project description (start here; authoritative)
├── SOFTWARE_PROJECT.tex         ← LaTeX source for the brief
├── README.md                    ← this file
│
├── templates/                   ← templates you fill in for submission
│   ├── REPORT_TEMPLATE.tex      → produces report/report.pdf
│   ├── REPORT_TEMPLATE.pdf      ← compiled preview
│   ├── SLIDES_TEMPLATE.tex      → produces your defense slides (Beamer)
│   ├── SLIDES_TEMPLATE.pdf      ← compiled preview
│   ├── CONTRIBUTION_STATEMENT.md
│   ├── STUDENT_README_TEMPLATE.md   ← model README for your repo
│   ├── Dockerfile.template      ← starting-point Dockerfile
│   └── pull_request_template.md ← put at .github/ in your repo
│
├── docs/                        ← guidance, not graded directly but read carefully
│   ├── TIMELINE.md              ← 12-day milestone schedule
│   ├── GIT_WORKFLOW.md          ← branch model, PR process, tagging
│   ├── COMMON_PITFALLS.md       ← what previous teams got wrong
│   └── ADVANCED_BONUSES.md      ← +10 bonus points for strong teams
│
├── topic-1-lost-and-found/      ← AI module + sample data + smoke tests
├── topic-2-food-analyzer/       ← (pick exactly ONE of the four topics)
├── topic-3-news-briefing/
└── topic-4-research-assistant/
```

## What you receive

For each of the four topics, the course provides a runnable, provider-agnostic `ai/` Python package (talks to Claude / GPT-4o / Gemini), sample data, a `demo_ai.py` that exercises it end-to-end, and offline smoke tests. **You do not build the AI side.** You build the software-engineering wrapping around it: config, storage, concurrency, retries, validation, logging, CLI, HTTP API (where required), testing, Docker, README, and the final report.

## What you submit on May 23

The authoritative brief says the headline submission is **one ZIP archive** due before **May 23, 2026 at 23:59 (UTC+4)** containing:

1. **Source code**.
2. **Compiled report** (`report/report.pdf`) using `templates/REPORT_TEMPLATE.tex`.
3. **Presentation deck** for the oral defense, using `templates/SLIDES_TEMPLATE.tex`.

Per `SOFTWARE_PROJECT.pdf` §7 and §10, the report/email must also include the GitHub repository URL and final tag `v1.0-final`; the signed contribution statement is submitted with the final package.

## Verify the provided AI module works

Before you write a single line of SE code, every team member should be able to run:

```bash
cd topic-N-<name>/
python data/_make_samples.py            # if the topic uses generated samples
python demo_ai.py --offline             # runs end-to-end without API keys
pytest tests/test_ai_smoke.py -v        # provided contract tests, must pass
```

If any of these fail on your machine, fix the environment before continuing.

## Quick rules

- **Do not** edit any file under `ai/`. The smoke tests are a contract; they must keep passing.
- **Do not** commit real API keys. Use `.env`; `.env` is in `.gitignore`; `.env.example` lists keys with empty values.
- **Do not** modify the public interface of the AI module — automatic deduction.
- **Do** read the **`SOFTWARE_PROJECT.pdf`** end-to-end before the kickoff meeting. The rubric is non-negotiable.
- **Do** use the timeline in `docs/TIMELINE.md` to plan.
- **Do** disclose AI-assistant use (Cursor / Claude / Copilot / etc.) in the report.

## Grading summary

100 points: **Code 60% · Report 25% · Presentation 15%.** Up to **+10 bonus points** for advanced features (`docs/ADVANCED_BONUSES.md`). Automatic deductions for hard-coded keys, broken Docker, network-dependent tests, severe commit imbalance, and modifying `ai/`.

Full rubric in **`SOFTWARE_PROJECT.pdf`** §8.

---

**Questions?** Open an issue against the course-wide repo or email the instructor. Do not delay on a blocker.

Good luck. Build something you would actually ship.
