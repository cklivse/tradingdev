Title: feat(statistics): add break-even and cost analysis

Part 2 of the statistics split; #206 explains the split. Code and tests are copied unchanged from `feat/stats-py314`.

- Break-even win rate and turnover cost, computed only from trade records.

Depends on #206. Until #206 merges, this diff also shows #206's commit.

## Verification

This repository has no CI, so nothing on GitHub runs these checks. Checks were run locally on this branch merged into `main`, verified at `main` 1ea5276:

- `scripts/check-fast.sh`: passes.
- Statistics tests on this branch (`tests/domain/statistics`, Part 1 + Part 2): 88 passed.

Why there is no full-suite result: `scripts/check-full.sh` starts with the repository's own prerequisite check, `python -m tooling.environment full`. In this environment that check fails (exit 1), so pytest never starts:

```text
Environment check failed: Strategy runtime is unavailable: Strategy runtime image 'tradingdev-strategy-runtime:0.1.0' is unavailable; build the Dockerfile strategy-runtime target first. Prepare the local Docker Engine and Dockerfile strategy-runtime image; TRADINGDEV_STRATEGY_IMAGE selects a custom image. See docs/development.md (container build and verification).
```

The `fast` profile of the same checker passes, so the checks listed above are `scripts/check-fast.sh` and this part's own tests. If a reviewer's environment has the strategy-runtime image, their `scripts/check-full.sh` run will be the first complete result.

For reference only: on an older `main` (741fd84, before this prerequisite check existed), 225 of the 7588 tests failed for the same missing image, with no statistics code present ([list](https://github.com/cklivse/tradingdev/blob/eeec7235e956db8ab1d8cf68af898b4a5480460c/evidence/2026-11-08-round26/container-failures-741fd84.md)).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
