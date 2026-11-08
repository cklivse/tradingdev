Title: feat(statistics): add parameter plateau analysis

Part 3 of the statistics split; #206 explains the split.

- Parameter plateau analysis over grid-search trials (is the best parameter set on a broad plateau or an isolated spike), with an MCP test showing that failed trials stay recorded.

Depends on #206. Until #206 merges, this diff also shows #206's commit.

## Commits

Unlike the other parts, this branch has three commits:

1. 8a7a82a — the plateau module and tests, copied unchanged from `feat/stats-py314`.
2. bfb62ae — a merge of `main` 35a2409. Nothing conflicted, but after the merge the MCP test no longer collected.
3. b1dac02 — follows upstream aa2d3f4 (`feat!: isolate generated strategies across product entrypoints`), which moved `tradingdev.domain.strategies.loader.StrategyLoader` to `tradingdev.adapters.execution.strategy_factory.StrategyFactory` with the same `resolve_execution` interface. Only the import and two call sites in `tests/mcp/test_optimization_failed_trials.py` change. This follows an upstream rename and is not a defect in the statistics code.

The merge was used instead of a rebase so the already-pushed branch is not rewritten.

## Verification

This repository has no CI, so nothing on GitHub runs these checks. Checks were run locally on this branch merged into `main`, verified at `main` c246355:

- `scripts/check-fast.sh`: passes.
- Statistics tests plus `tests/mcp/test_optimization_failed_trials.py` (Part 1 + Part 3): 130 passed. The MCP test runs the bundled KD strategy in process and does not need the container image.

Why the full suite is not reported as green: since upstream aa2d3f4 (2026-11-06, `feat!: isolate generated strategies across product entrypoints`), the integration tests that execute generated strategies need a prebuilt `tradingdev-strategy-runtime` image. `docs/development.md` states that the tests do not download the image and that a missing daemon, required capability or prebuilt image makes them fail; since upstream 51af970 (2026-11-08), `scripts/check-full.sh` also checks for the image first and does not start pytest without it. On a clean `main` 741fd84, with no statistics code, 225 of the 7588 tests fail for this reason: 219 report `runtime_unavailable`, and the other 6 fail because their container never starts. The full list, with the evidence for each test and how the suite was run, is in [`evidence/2026-11-08-round26/container-failures-741fd84.md`](https://github.com/cklivse/tradingdev/blob/eeec7235e956db8ab1d8cf68af898b4a5480460c/evidence/2026-11-08-round26/container-failures-741fd84.md), pinned to `session-notes` commit eeec723. This environment does not have that image, so the full-suite evidence attached here is limited to that list. If a reviewer's environment has the image, their run will be the first complete result.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
