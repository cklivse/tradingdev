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

Merge order: this PR first, then 2, 3 and 4 in any order, then 5 after 4. Until a prerequisite merges, a PR's diff against `main` also shows the prerequisite's commits.

Code and tests are copied file by file from `feat/stats-py314` without rewriting. After the split, two changes were made only on the split branches: PR 3 picks up an upstream rename, and PR 5 rewords one docstring. Both PRs explain them. What #38 has beyond this series is documentation (the full package guide in `__init__.py`, the methods documents, and the ARCHITECTURE/README sections). A KD fixture test PR follows once 2, 3 and 5 are in.

## This PR

- Shared input validation, exact power-of-two rescaling for extreme magnitudes, and UTC daily/monthly P&L and returns from an equity curve.
- `__init__.py` carries a one-line docstring; the full package guide comes later from #38.
- Depends on: nothing (based on `main`).

This PR creates `src/tradingdev/domain/statistics/`, a directory that does not exist on `main`. Nothing on `main` imports it, and the PR changes no existing file: its diff is five added files (four under `src/tradingdev/domain/statistics/`, one test file).

## Verification

This repository has no CI, so nothing on GitHub runs these checks. Checks were run locally on this branch merged into `main`, verified at `main` 1ea5276:

- `scripts/check-fast.sh`: passes.
- This part's tests (`tests/domain/statistics`): 36 passed.

Why there is no full-suite result: `scripts/check-full.sh` starts with the repository's own prerequisite check, `python -m tooling.environment full`. In this environment that check fails (exit 1), so pytest never starts:

```text
Environment check failed: Strategy runtime is unavailable: Strategy runtime image 'tradingdev-strategy-runtime:0.1.0' is unavailable; build the Dockerfile strategy-runtime target first. Prepare the local Docker Engine and Dockerfile strategy-runtime image; TRADINGDEV_STRATEGY_IMAGE selects a custom image. See docs/development.md (container build and verification).
```

The `fast` profile of the same checker passes, so the checks listed above are `scripts/check-fast.sh` and this part's own tests. If a reviewer's environment has the strategy-runtime image, their `scripts/check-full.sh` run will be the first complete result.

For reference only: on an older `main` (741fd84, before this prerequisite check existed), 225 of the 7588 tests failed for the same missing image, with no statistics code present ([list](https://github.com/cklivse/tradingdev/blob/eeec7235e956db8ab1d8cf68af898b4a5480460c/evidence/2026-11-08-round26/container-failures-741fd84.md)).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
