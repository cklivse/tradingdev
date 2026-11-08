Title: feat(statistics): add parameter plateau analysis

Part 3 of the statistics split; #<P1> explains the split.

- Parameter plateau analysis over grid-search trials (is the best parameter set on a broad plateau or an isolated spike), with an MCP test showing that failed trials stay recorded.

Depends on #<P1>. Until #<P1> merges, this diff also shows #<P1>'s commit.

## Commits

Unlike the other parts, this branch has three commits:

1. 8a7a82a — the plateau module and tests, copied unchanged from `feat/stats-py314`.
2. bfb62ae — a merge of `main` 35a2409. Nothing conflicted, but after the merge the MCP test no longer collected.
3. b1dac02 — follows upstream aa2d3f4 (`feat!: isolate generated strategies across product entrypoints`), which moved `tradingdev.domain.strategies.loader.StrategyLoader` to `tradingdev.adapters.execution.strategy_factory.StrategyFactory` with the same `resolve_execution` interface. Only the import and two call sites in `tests/mcp/test_optimization_failed_trials.py` change. This follows an upstream rename and is not a defect in the statistics code.

The merge was used instead of a rebase so the already-pushed branch is not rewritten.

## Verification

This repository has no CI, so nothing on GitHub runs these checks. Checks were run locally on this branch merged into `main`, verified at `main` 741fd84:

- `scripts/check-fast.sh`: passes.
- Statistics tests plus `tests/mcp/test_optimization_failed_trials.py` (Part 1 + Part 3): 130 passed. The MCP test runs the bundled KD strategy in process and does not need the container image.

Why the full suite is not reported as green: since upstream aa2d3f4 (2026-11-06, `feat!: isolate generated strategies across product entrypoints`), the integration tests that execute generated strategies need a prebuilt `tradingdev-strategy-runtime` image, and this environment does not have one. `docs/development.md` states that a missing daemon, required capability or prebuilt image makes those tests fail, and the tests do not download the image themselves. The same tests fail for the same reason on a clean `main`, so they are unrelated to this part. If a reviewer's environment has that image, their run will be the first complete result.


🤖 Generated with [Claude Code](https://claude.com/claude-code)
