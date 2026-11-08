Title: feat(statistics): add paired comparison and benchmark comparison

Part 5 of the statistics split; #206 explains the split.

- Paired bootstrap comparison of strategies on the same data, and buy-and-hold benchmark returns with a strategy's regression on them.

Depends on #209 (and on #206 through it). Until those merge, this diff also shows their commits.

## Commits

1. 000c15e — the comparison and benchmark modules and tests, copied unchanged from `feat/stats-py314`.
2. a216dc4 — docstring only. The `benchmark` module docstring had listed the product benchmark's instruments (BTC/USDT, S&P 500), but that list belongs to `tradingdev.domain.benchmark`'s `BENCHMARKS` table, and upstream 947a372 has since added Taiwan equities. It now describes the rule: the upstream table decides the instruments, and BTC/USDT is kept only as an example. No code change.

## Verification

This repository has no CI, so nothing on GitHub runs these checks. Checks were run locally on this branch merged into `main`, verified at `main` c246355:

- `uv sync --locked` succeeds on the merged tree.
- `scripts/check-fast.sh`: passes.
- Statistics tests on this branch (Parts 1, 4 and 5): 303 passed.
- All five parts merged together into the same `main`: statistics tests plus the Part 3 MCP test, 449 passed; `scripts/check-fast.sh` passes.
- The four pinned KD figures from #38's fixture (366 UTC days, annualised daily Sharpe, traded notional, cost share of net P&L), recomputed on that combined tree, are bitwise equal to the pinned values.

Why the full suite is not reported as green: since upstream aa2d3f4 (2026-11-06, `feat!: isolate generated strategies across product entrypoints`), the integration tests that execute generated strategies need a prebuilt `tradingdev-strategy-runtime` image. `docs/development.md` states that the tests do not download the image and that a missing daemon, required capability or prebuilt image makes them fail; since upstream 51af970 (2026-11-08), `scripts/check-full.sh` also checks for the image first and does not start pytest without it. On a clean `main` 741fd84, with no statistics code, 225 of the 7588 tests fail for this reason: 219 report `runtime_unavailable`, and the other 6 fail because their container never starts. The full list, with the evidence for each test and how the suite was run, is in [`evidence/2026-11-08-round26/container-failures-741fd84.md`](https://github.com/cklivse/tradingdev/blob/eeec7235e956db8ab1d8cf68af898b4a5480460c/evidence/2026-11-08-round26/container-failures-741fd84.md), pinned to `session-notes` commit eeec723. This environment does not have that image, so the full-suite evidence attached here is limited to that list. If a reviewer's environment has the image, their run will be the first complete result.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
