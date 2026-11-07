Title: feat(statistics): add input validation, scaling and period returns

## Why this is split into five PRs

At the 2026-10-27 meeting the review feedback on #38 was that the PR was too large to review. #38 is a single PR against `main` that currently adds 32 files, +9404/−3 (GitHub's count today). This series splits out its code and tests into five PRs, one commit per module group. Each PR's base matches what its code actually imports:

| PR | Branch | Modules | Imports from the statistics package |
| --- | --- | --- | --- |
| 1 (this PR) | `stats/1-foundation` | `_validation`, `_scaling`, `periods` | nothing |
| 2 | `stats/2-breakeven` | `breakeven` | `_validation` (1) |
| 3 | `stats/3-plateau` | `plateau` | `_validation`, `_scaling` (1) |
| 4 | `stats/4-sharpe` | `sharpe`, `performance`; adds `arch` | `_validation`, `_scaling`, `periods` (1) |
| 5 | `stats/5-comparison` | `comparison`, `benchmark` | `sharpe` (4), `periods` (1) |

Merge order: this PR first, then 2, 3 and 4 in any order, then 5 after 4. Until a prerequisite merges, a PR's diff against `main` also shows the prerequisite's commits. The split was agreed on #38 (<AGREEMENT_URL>).

Code and tests are copied file by file from `feat/stats-py314` without rewriting. After the split, two changes were made only on the split branches: PR 3 picks up an upstream rename, and PR 5 rewords one docstring. Both PRs explain them. What #38 has beyond this series is documentation (the full package guide in `__init__.py`, the methods documents, and the ARCHITECTURE/README sections). A KD fixture test PR follows once 2, 3 and 5 are in.

## This PR

- Shared input validation, exact power-of-two rescaling for extreme magnitudes, and UTC daily/monthly P&L and returns from an equity curve.
- `__init__.py` carries a one-line docstring; the full package guide comes later from #38.
- Depends on: nothing (based on `main`).

This PR creates `src/tradingdev/domain/statistics/`, a directory that does not exist on `main`. Nothing on `main` imports it, and the PR changes no existing file: its diff is five added files (four under `src/tradingdev/domain/statistics/`, one test file). So apart from its own 36 tests, the full suite cannot be affected by it. As a check, the three test files that scan the whole source tree or package (`tests/integration/test_import_migration.py`, `tests/mcp/test_strategy_contracts.py`, `tests/mcp/test_strategy_save_failures.py`) give identical per-test results with and without this PR (44 tests; the same 5 fail on both, all with `runtime_unavailable`, see below).

## Verification

This repository has no CI, so nothing on GitHub runs these checks. Checks run locally on this branch merged with `main` 741fd84:

- Merged with `main` 741fd84 without conflicts.
- `scripts/check-fast.sh`: passes.
- This part's tests (`tests/domain/statistics`): 36 passed.

Why the full suite is not reported as green: since upstream aa2d3f4 (2026-11-06, `feat!: isolate generated strategies across product entrypoints`), the integration tests that execute generated strategies need a prebuilt `tradingdev-strategy-runtime` image, and this environment does not have one. `docs/development.md` states that a missing daemon, required capability or prebuilt image makes those tests fail, and the tests do not download the image themselves. The same tests fail for the same reason on a clean `main`, so they are unrelated to this part. If a reviewer's environment has that image, their run will be the first complete result.

Separately, the two local full-suite runs made so far (on a clean `main` 741fd84 and on Part 1 merged with it) were both stopped by an external SIGTERM at the same point, about 61% through, so no complete local full-suite result exists yet. That is being investigated on its own and happens on a clean `main` too.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
