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

This repository has no CI, so nothing on GitHub runs these checks. Checks were run locally on this branch merged into `main`, verified at `main` 1ea5276:

- `scripts/check-fast.sh`: passes.
- Statistics tests plus `tests/mcp/test_optimization_failed_trials.py` (Part 1 + Part 3): 130 passed. The MCP test runs the bundled KD strategy in process and does not need the container image.

Why there is no full-suite result: `scripts/check-full.sh` starts with the repository's own prerequisite check, `python -m tooling.environment full`. In this environment that check fails (exit 1), so pytest never starts:

```text
Environment check failed: Strategy runtime is unavailable: Strategy runtime image 'tradingdev-strategy-runtime:0.1.0' is unavailable; build the Dockerfile strategy-runtime target first. Prepare the local Docker Engine and Dockerfile strategy-runtime image; TRADINGDEV_STRATEGY_IMAGE selects a custom image. See docs/development.md (container build and verification).
```

The `fast` profile of the same checker passes, so the checks listed above are `scripts/check-fast.sh` and this part's own tests. If a reviewer's environment has the strategy-runtime image, their `scripts/check-full.sh` run will be the first complete result.

For reference only: on an older `main` (741fd84, before this prerequisite check existed), 225 of the 7588 tests failed for the same missing image, with no statistics code present ([list](https://github.com/cklivse/tradingdev/blob/eeec7235e956db8ab1d8cf68af898b4a5480460c/evidence/2026-11-08-round26/container-failures-741fd84.md)).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
