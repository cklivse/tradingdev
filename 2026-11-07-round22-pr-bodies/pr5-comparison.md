Title: feat(statistics): add paired comparison and benchmark comparison

Part 5 of the statistics split; #206 explains the split.

- Paired bootstrap comparison of strategies on the same data, and buy-and-hold benchmark returns with a strategy's regression on them.

Depends on #209 (and on #206 through it). Until those merge, this diff also shows their commits.

## Commits

1. 000c15e — the comparison and benchmark modules and tests, copied unchanged from `feat/stats-py314`.
2. a216dc4 — docstring only. The `benchmark` module docstring had listed the product benchmark's instruments (BTC/USDT, S&P 500), but that list belongs to `tradingdev.domain.benchmark`'s `BENCHMARKS` table, and upstream 947a372 has since added Taiwan equities. It now describes the rule: the upstream table decides the instruments, and BTC/USDT is kept only as an example. No code change.

## Verification

This repository has no CI, so nothing on GitHub runs these checks. Checks were run locally on this branch merged into `main`, verified at `main` 1ea5276:

- `uv sync --locked` succeeds on the merged tree.
- `scripts/check-fast.sh`: passes.
- Statistics tests on this branch (Parts 1, 4 and 5): 303 passed.
- All five parts merged together into the same `main`: statistics tests plus the Part 3 MCP test, 449 passed; `scripts/check-fast.sh` passes.
- The four pinned KD figures from #38's fixture (366 UTC days, annualised daily Sharpe, traded notional, cost share of net P&L), recomputed on that combined tree, are bitwise equal to the pinned values.

Why there is no full-suite result: `scripts/check-full.sh` starts with the repository's own prerequisite check, `python -m tooling.environment full`. In this environment that check fails (exit 1), so pytest never starts:

```text
Environment check failed: Strategy runtime is unavailable: Strategy runtime image 'tradingdev-strategy-runtime:0.1.0' is unavailable; build the Dockerfile strategy-runtime target first. Prepare the local Docker Engine and Dockerfile strategy-runtime image; TRADINGDEV_STRATEGY_IMAGE selects a custom image. See docs/development.md (container build and verification).
```

The `fast` profile of the same checker passes, so the checks listed above are `scripts/check-fast.sh` and this part's own tests. If a reviewer's environment has the strategy-runtime image, their `scripts/check-full.sh` run will be the first complete result.

For reference only: on an older `main` (741fd84, before this prerequisite check existed), 225 of the 7588 tests failed for the same missing image, with no statistics code present ([list](https://github.com/cklivse/tradingdev/blob/eeec7235e956db8ab1d8cf68af898b4a5480460c/evidence/2026-11-08-round26/container-failures-741fd84.md)).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
