Title: feat(statistics): add paired comparison and benchmark comparison

Part 5 of the statistics split; #<P1> explains the split.

- Paired bootstrap comparison of strategies on the same data, and buy-and-hold benchmark returns with a strategy's regression on them.

Depends on #<P4> (and on #<P1> through it). Until those merge, this diff also shows their commits.

## Commits

1. 000c15e — the comparison and benchmark modules and tests, copied unchanged from `feat/stats-py314`.
2. a216dc4 — docstring only. The `benchmark` module docstring had listed the product benchmark's instruments (BTC/USDT, S&P 500), but that list belongs to `tradingdev.domain.benchmark`'s `BENCHMARKS` table, and upstream 947a372 has since added Taiwan equities. It now describes the rule: the upstream table decides the instruments, and BTC/USDT is kept only as an example. No code change.

## Verification

This repository has no CI, so nothing on GitHub runs these checks. Checks run locally on this branch merged with `main` 741fd84:

- Merged with `main` 741fd84 without conflicts (`pyproject.toml` auto-merged); `uv sync --locked` succeeds on the merge.
- `scripts/check-fast.sh`: passes.
- Statistics tests on this branch (Parts 1, 4 and 5): 303 passed.
- All five parts merged together onto `main` 741fd84: statistics tests plus the Part 3 MCP test, 449 passed; `scripts/check-fast.sh` passes.
- The four pinned KD figures from #38's fixture (366 UTC days, annualised daily Sharpe, traded notional, cost share of net P&L), recomputed on that combined tree, are bitwise equal to the pinned values.

Why the full suite is not reported as green: since upstream aa2d3f4 (2026-11-06, `feat!: isolate generated strategies across product entrypoints`), the integration tests that execute generated strategies need a prebuilt `tradingdev-strategy-runtime` image, and this environment does not have one. `docs/development.md` states that a missing daemon, required capability or prebuilt image makes those tests fail, and the tests do not download the image themselves. The same tests fail for the same reason on a clean `main`, so they are unrelated to this part. If a reviewer's environment has that image, their run will be the first complete result.

Separately, the two local full-suite runs made so far (on a clean `main` 741fd84 and on Part 1 merged with it) were both stopped by an external SIGTERM at the same point, about 61% through, so no complete local full-suite result exists yet. That is being investigated on its own and happens on a clean `main` too.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
