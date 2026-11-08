Title: feat(statistics): add break-even and cost analysis

Part 2 of the statistics split; #<P1> explains the split. Code and tests are copied unchanged from `feat/stats-py314`.

- Break-even win rate and turnover cost, computed only from trade records.

Depends on #<P1>. Until #<P1> merges, this diff also shows #<P1>'s commit.

## Verification

This repository has no CI, so nothing on GitHub runs these checks. Checks were run locally on this branch merged into `main`, verified at `main` 741fd84:

- `scripts/check-fast.sh`: passes.
- Statistics tests on this branch (`tests/domain/statistics`, Part 1 + Part 2): 88 passed.

Why the full suite is not reported as green: since upstream aa2d3f4 (2026-11-06, `feat!: isolate generated strategies across product entrypoints`), the integration tests that execute generated strategies need a prebuilt `tradingdev-strategy-runtime` image, and this environment does not have one. `docs/development.md` states that a missing daemon, required capability or prebuilt image makes those tests fail, and the tests do not download the image themselves. The same tests fail for the same reason on a clean `main`, so they are unrelated to this part. If a reviewer's environment has that image, their run will be the first complete result.


🤖 Generated with [Claude Code](https://claude.com/claude-code)
