# Git Workflow

This is the workflow the project rubric assumes. It mirrors what most engineering teams in industry do. If your team adapts it, document the changes in your README.

## Branch model

- **`main`** is protected. Direct pushes to `main` are not allowed.
- Every change goes through a **feature branch**: `<member>/<short-description>`. Examples:
  - `farid/config-loader`
  - `nigar/retry-decorator`
  - `kamran/sqlite-repository`
- Branch names are lowercase, hyphen-separated, and short enough to type from memory.

## Pull request rules

1. Open a PR as soon as you have something runnable. Draft PRs are fine for in-progress work.
2. **Every PR needs at least one teammate review** before merging.
3. Use the PR template (`templates/pull_request_template.md`) — place it at `.github/pull_request_template.md` in your repo so GitHub auto-fills it.
4. PRs should be **small enough to review in 15 minutes**. If a PR has more than ~300 lines of diff, split it.
5. Merge with **squash-and-merge** (cleaner history) unless the branch is genuinely a series of meaningful commits.
6. **Delete the branch after merging.** GitHub has a button for this; use it.

## Commit messages

Use the simple convention below — not strict Conventional Commits, but a recognizable shape:

```
<verb-in-present-tense>: <one-line summary, <50 chars>

<optional body explaining the why, wrapped at 72 chars>
```

Good:

```
add: SQLite repository with item lifecycle methods
fix: 429 handling — retry with jitter instead of hard sleep
refactor: pull retry policy into its own service
docs: README quickstart for Docker
test: cover empty-ingredients edge case in compute_totals
```

Bad: `wip`, `fix stuff`, `changes`, `final fix v2 actually`.

## When to rebase vs merge

- **Rebase your feature branch onto `main`** before opening a PR. This keeps the history linear and makes the diff readable. Run `git fetch origin && git rebase origin/main`.
- **Squash-and-merge** when landing the PR (preserves a clean `main`).
- Don't rebase a branch other people have pulled. If unsure, just merge.

## Code review etiquette

- Review PRs within 24 hours of being asked. Engineering teams stall when reviews pile up.
- Comments should be **specific** — point at lines, suggest changes, link to docs.
- Critique the code, not the person. "This will deadlock under load X" is good; "this is bad" is not.
- Use GitHub's "Request changes" status sparingly. Most issues are fine as "Comments".
- **The author merges**, not the reviewer. The reviewer approves; the author squashes and lands.

## Protecting `main`

Configure these in your repo's **Settings → Branches → Branch protection rules**:

- Require pull request before merging.
- Require approvals: 1.
- Dismiss stale approvals when new commits are pushed.
- Require status checks to pass (your CI, if you set up the GitHub Actions bonus).
- Do not allow force pushes to `main`.
- Do not allow deletions of `main`.

## Tagging the final commit

When the project is done:

```bash
# On main, after the last merge:
git pull origin main
git tag -a v1.0-final -m "Final submission for AI-ENG-110 Software Engineering Final Project"
git push origin v1.0-final
```

This is the tag the grader will check out. **Do not push more commits to `main` after this tag** — they will be ignored, and their presence may cost you the late penalty.

## Common pitfalls (specific to git on this project)

- **Committing `.env`.** Add it to `.gitignore` before your first commit. If you slip and push real keys, **rotate them immediately** and rewrite history if the repo is public.
- **Committing the SQLite database.** Add `*.db` and `*.sqlite3` to `.gitignore`.
- **Committing `__pycache__/` or `.venv/`.** Standard `.gitignore` should handle both.
- **One teammate doing all the commits.** Pair on bigger PRs but commit independently. Target roughly ≥20% per member; an undocumented share below 10% triggers the automatic deduction.
- **Force-pushing `main`.** Never. There is no recovering this gracefully.

## A minimal `.gitignore`

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/

# Project
.env
*.db
*.sqlite3
*.log

# OS / editor
.DS_Store
.idea/
.vscode/

# Build artefacts
dist/
build/
*.egg-info/
```
