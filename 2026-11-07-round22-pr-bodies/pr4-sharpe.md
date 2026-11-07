Title: feat(statistics): add Sharpe inference and performance summary

Part 4 of the statistics split; #<P1> explains the split. Code and tests are copied unchanged from `feat/stats-py314`.

- Sharpe ratio with a bootstrap interval, probabilistic and deflated Sharpe, and a performance summary computed from raw run outputs; adds the `arch` dependency (`pyproject.toml`, `uv.lock`).
- The literature behind each step is in `docs/statistics_bootstrap_methods.md` on #38.

Depends on #<P1>. Until #<P1> merges, this diff also shows #<P1>'s commit.

## Verification

This repository has no CI, so nothing on GitHub runs these checks. Checks run locally on this branch merged with `main` 741fd84:

- Merged with `main` 741fd84 without conflicts (`pyproject.toml` auto-merged); `uv sync --locked` succeeds on the merge.
- `scripts/check-fast.sh`: passes.
- Statistics tests on this branch (Part 1 + Part 4): 146 passed.

Why the full suite is not reported as green: since upstream aa2d3f4 (2026-11-06, `feat!: isolate generated strategies across product entrypoints`), the integration tests that execute generated strategies need a prebuilt `tradingdev-strategy-runtime` image, and this environment does not have one. `docs/development.md` states that a missing daemon, required capability or prebuilt image makes those tests fail, and the tests do not download the image themselves. The same tests fail for the same reason on a clean `main`, so they are unrelated to this part. If a reviewer's environment has that image, their run will be the first complete result.

Separately, the two local full-suite runs made so far (on a clean `main` 741fd84 and on Part 1 merged with it) were both stopped by an external SIGTERM at the same point, about 61% through, so no complete local full-suite result exists yet. That is being investigated on its own and happens on a clean `main` too.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
