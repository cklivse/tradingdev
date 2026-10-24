# feat: add domain statistics for strategy inference, with the branch synced to Python 3.14 / pandas 3

**Branches:** this PR comes from `feat/stats-py314`. `feat/stats-on-latest` stays at `814b05a` as the fallback from before the sync to Python 3.14 / pandas 3; do not open a PR from it. The merge base is upstream `main` at `3fa0852`, so the diff contains only this branch's own files: the statistics modules and their tests, the demo scripts and outputs, `docs/statistics_leaderboard_integration.md`, `tests/mcp/test_optimization_failed_trials.py`, `scripts/validate_run.py`, and `arch` in `pyproject.toml` / `uv.lock`.

**About the 3 deleted lines in `uv.lock`:** the `uv.lock` diff is +130/-3.

- The additions are arch 8.0.0 and its dependencies: statsmodels, patsy, formulaic, interface-meta and wrapt.
- The 3 deleted lines are simplified platform markers: httpcore2's on h11 and truststore, and pexpect's on ptyprocess. The packages that depend on them already carry the same markers, so the resolution is equivalent; the difference comes from the uv version.
- `uv lock --check` passes.

## What this branch does

It adds `src/tradingdev/domain/statistics/`. The modules take only what the caller passes in (equity curves, timestamps, trade records or return series). They never read runs, artifacts or caches, and never consult an engine's own `metrics`, so they can cross-check the figures an engine reports.

- **periods**: what are the closing equity, P&L and returns of an equity curve on UTC day and month boundaries? Periods without data are omitted rather than filled with zero, so period P&L always sums to the total P&L.
- **performance**: from raw outputs alone, what were this run's return, volatility, drawdown and win rate? Used to check the figures an engine reports about itself.
- **breakeven**: given the current payoff ratio, what win rate breaks even, and how far is the realised win rate from that line? What are the traded notional (entry plus exit legs) and the turnover?
- **sharpe**: how reliable is the annualised Sharpe of daily returns? A stationary bootstrap gives the confidence interval; PSR gives the probability that the true Sharpe is above 0; DSR corrects for the selection bias of picking the best of N trials.
- **comparison**: is the difference between two strategies on the same data significant? Both series are aligned on one timeline and resampled with the same block indices (a paired bootstrap), keeping the covariance of their returns.
- **plateau**: does the best parameter set sit on a broad plateau where nearby parameters also perform well, or is it an isolated spike in the grid? Neighbourhoods use Chebyshev distance on grid indices.
- **benchmark**: how does the strategy compare with buy-and-hold? The Sharpe difference is left to comparison; this module answers how the strategy co-moves with the instrument (beta is the average net exposure, not CAPM systematic risk).

Also included: `arch>=8.0.0` (stationary bootstrap and the Politis–White optimal block length), `scripts/demo_statistics.py`, `scripts/demo_plateau.py`, `scripts/validate_run.py` and the committed `demo_output/`.

### Four gaps fixed after review (`610e612`)

- **`scripts/validate_run.py`**
  - V3 asserted `max_drawdown <= 0`, but the catalog defines it as a nonnegative magnitude, so every result from the current engine failed with exit 1. It now follows the catalog definition and only checks `>= 0`.
  - Cost was `2 × total_volume`, but `total_volume` already counts both legs, so the exit leg was counted twice: KD's cost share printed as 173% instead of 86.3%. Cost is now derived from breakeven's traded notional, as in the demo.
- **`align_returns`**: mixing timezone-naive and timezone-aware indexes used to give overlap 0 silently. Downstream only saw "insufficient observations", with no sign that the cause was a timezone mismatch. It now raises explicitly, and the message says the cause is a timezone mismatch, not non-overlapping periods. All five callers go through it, including `compare_to_benchmark`.
- **breakeven and open trades**: an open trade used to get a phantom exit leg at the last mark price, overstating traded notional and turnover. In the test case breakeven computed 3,990 while the engine's `total_volume` was 3,010. The chosen behaviour is described below.
- **demo fee note**: the demo always said "Trade records carry `fee = 0`", which was only true of the old engine; the current engine records fees in its trades. The sentence now depends on the actual value: with a fee total of 0 it keeps the original wording, otherwise it states the actual fee total and explains that slippage is folded into fill prices.

### breakeven and open trades: kept, with the entry leg only

A trade with `status == "open"` is still counted, but its traded notional is the entry leg only. The reasons are in the module docstring:

- The entry was executed and paid its costs. Dropping the trade would understate turnover and cost; the engine's `total_volume` likewise counts only executed orders.
- Its `exit_price` is the last mark price, not a fill, so it cannot count as an exit leg.
- Its `net_pnl` is marked to market and already in the equity curve, so it still counts as a win or loss. This keeps "the trades' total net P&L equals the run's P&L" and the identity "the edge is positive exactly when total P&L is positive".

**The difference from the engine's win rate is intentional, not a bug:** the engine's `total_trades` and `win_rate` count closed trades only. So when a trade is still open at the end, breakeven's trade count and win rate differ from the engine's metrics. The docstring states this.

Records without a `status` (the old format) count as closed; any other status value raises.

### Synced to Python 3.14 / pandas 3

This branch has merged upstream `main` (3fa0852) and is verified under Python 3.14.2, pandas 3.0.6, numpy 2.5.4, vectorbt 1.2.0 and arch 8.0.0. Upstream removed `request_execution_confirmation` and native MCP elicitation in favour of `submit_execution_decision`. So this branch's earlier commit changing the confirmation form (be952d9) was superseded by the upstream version in the merge and is no longer in the PR diff.

Besides resolving conflicts, the merge commit contains changes needed for the merged tree to pass:

- `periods.to_utc_index` always returns a nanosecond index. This is a behaviour change: pandas 3 keeps the input's time resolution.
- The benchmark beta/alpha test now checks against `quantstats.stats.greeks`, because upstream removed empyrical.
- `tests/integration/mcp_harness.py` is restored to the upstream version.

The details are in the merge commit message.

## Verified figures

All five figures were recomputed to full precision under pandas 3.0.6 + numpy 2.5.4 and compared with the `demo_output/` committed under pandas 2. They were recomputed again after the four fixes in `610e612`, with identical results.

The KD(14,3,3) figures were verified two ways:

- Recomputing the statistics from the same cached pickle used for the committed output (`cd03bf19459b48af.pkl`).
- Re-running the backtest under pandas 3 with `BacktestService`.

Both give identical results to full precision, and the three regenerated markdown tables (`kd_inference.md`, `plateau_table.md`, `plateau_gridindex_table.md`) are byte-identical to the committed ones. All 412 trades of the re-run backtest are closed, so the open-trade fix does not affect these figures.

| We claim | How it was verified | pandas 3 result |
| --- | --- | --- |
| KD(14,3,3) (BTC/USDT 1h, full year 2024) annualised Sharpe of daily returns is -7.57 | `period_returns(..., "daily")` then `sharpe_ratio(periods_per_year=365)`, once from the cache and once from the re-run | -7.565103143673017 (same both ways) |
| Estimated cost / abs(net P&L) is 86.3% | traded notional × (fee 0.0006 + slippage 0.0005) ÷ abs(equity[-1] − equity[0]) | 0.863481526386825 |
| Traded notional (entry plus exit) is 5,014,735.72 | `summarize_breakeven(trades).traded_notional`, from the trade records, not the engine's `total_volume` | 5014735.715506879 |
| DSR hurdle_annualised is 0.6718 for annualised Sharpes -6.00/-6.67/-7.57, ppy=365, n_trials=3 | `deflated_sharpe_ratio(..., annualised_trial_sharpes=[-6.00, -6.67, -7.57], periods_per_year=365, n_trials=3).hurdle_annualised` (the hurdle depends only on the dispersion of the trial Sharpes, not on the returns) | 0.6718418141111412 |
| Plateau demo: true plateau metric_gap 0.000, plateau_best_score 1.056; false spike metric_gap 1.934, plateau_best_score 0.642 | `plateau_summary` on each demo script's synthetic 5×5 grid (seed 0) | true plateau 0.0 / 1.0557559467813422; false spike 1.9339414629589853 / 0.6423599963505668 (same in both scripts) |

The re-run backtest gives these annualised Sharpes for the three KD variants:

- KD(21,5,5): -6.004071680348325
- KD(9,3,3): -6.6715302187876615
- KD(14,3,3): -7.565103143673017

These are exactly the three trial Sharpes used in the DSR row.

After the fix, `scripts/validate_run.py` passes all 24 checks on the current engine's KD result, and its cost share of 86% agrees with the table.

Checks (as of `610e612`):

- `scripts/check-fast.sh` passes.
- `scripts/check-full.sh` passes: 4243 passed, 12 deselected (`live_llm`), about 50 minutes.
- `pytest tests/domain/statistics/`: 319 passed.

During the merge, the statistics tests also passed with `-W error::FutureWarning -W error::DeprecationWarning`.

## Plateau contract verified on real data

`1b51608` (fix: keep failed slices on the plateau grid axes) takes the plateau grid axes from every searched parameter row, failed ones included. So when every trial at some parameter value fails, that value does not disappear from its axis. This behaviour had only been tested on synthetic data; this time it was run end to end on the real system.

**What was run:**

- A real long-only KD parameter search: BTC/USDT 1h, trained on 2024 H1 and tested on 2024 H2, with overbought fixed at 100 so the strategy never goes short.
- The grid is k_period ∈ {9, 14, 21, 28, 35} × oversold ∈ {20, 10, 0}, 15 combinations. The 5 with oversold=0 are a deliberate failure slice: %K never goes below 0, so they make no trades and their Sharpe is undefined.
- The full MCP flow: `prepare_optimization`; then, after the user read the HTML confirmation and explicitly approved in the conversation, `submit_execution_decision(decision="approve")`; then `get_job_status` and `get_run_metrics(scope="trial/{i}/train")` to read back all 15 trial scopes.
- Plan/run ID: `f245f73b6ebb4c4b9c06b2ee08457339`.

**Results:**

- The 5 failed trials each have a complete record in `available_scopes`: `success: true`, with `trial_index` and `parameters` present.
- Their 33 metric fields are exactly the same as a successful trial's (compared one by one), and the 8 that cannot be computed are `None`: `sharpe_ratio`, `sortino_ratio`, `calmar_ratio`, `win_rate`, `profit_factor`, `trade_expectancy`, `avg_holding_bars` and `total_slippage` (which is None for successful trials too). The reason codes are in `metadata.unavailable`.
- Feeding the 15 scopes' `parameters` and `sharpe_ratio` into `trials_from_metrics(direction="maximize")` gives `dropped_count=5` and a `DroppedTrialsWarning`. The axis still holds `oversold=(0, 10, 20)`: the 5 failed cells become missing grid points instead of disappearing from the axis.
- `plateau_summary` reflects the missing points as expected: the best combination (9, 10) sits in a corner with 5 neighbours, 2 of them missing, so `best_neighborhood_size=3`.

So the behaviour `1b51608` fixed holds on the real system, not only as an inference from synthetic data.

## Found along the way, outside this PR's scope

### preflight trials only the first value of each range

`src/tradingdev/adapters/execution/preflight_worker.py:232-293`:

- Lines 232-234 take only the first value of each parameter range and trial that one combination on a small training sample.
- Lines 284-290: if that combination cannot compute the objective, it raises `unrankable_sample_objective` and blocks the whole plan; no plan is even created.

In practice, writing ranges in ascending order is the most natural way (for example, oversold starting at 0), and the boundary value is often the one that makes no trades, so the most natural way is exactly the one that gets blocked. That is what happened in this search: submitting `oversold=[10, 20, 0]` was blocked, and only `[20, 10, 0]` went through, with an identical grid.

Suggestion: have the error message say that the trial run uses only the first value of each range, so users know reordering lets it through.

### Zero trades cannot be detected from Sharpe's unavailable reason code

For a zero-trade trial, `metadata.unavailable` gives `zero_denominator` for Sharpe, Sortino and Calmar, because the equity curve is flat. Only win rate, profit factor, expectancy and average holding bars carry `no_trades`. The evidence is in `src/tradingdev/domain/backtest/metrics.py`:

- Lines 201-208: without closed trades, only `win_rate`, `profit_factor`, `trade_expectancy` and `avg_holding_bars` are marked `no_trades`.
- Lines 236-240: non-finite values (including the Sharpe of a flat equity curve) are all marked `zero_denominator`.
- Lines 355-356 (Calmar) and 382-386 (Sortino) likewise mark `zero_denominator`.

So zero trades must be detected with `total_trades == 0`. A flat equity curve with trades gives the same Sharpe reason code, so the code alone cannot tell them apart. Anyone consuming scopes will hit this, and it is worth documenting.

### A trial-run timeout ends the whole job

`src/tradingdev/mcp/workers/optimization.py`:

- Line 334 first sets `trial_result = None`.
- If the trial run (the first combo) times out, the `except _TrialTimeoutError` at lines 352–365 marks the job `estimation_timeout` and hits `return`; other exceptions go through `_fail()` at lines 366–370 and then `return`.
- So the `None` branch of `if trial_result is not None` at line 413 is unreachable.

The result is that the whole job produces nothing, rather than missing just one parameter set. Two things are worth addressing:

- A strategy whose first parameter set is slow cannot be optimised at all.
- The defensive check at line 413 suggests a "one row missing" path that does not exist.

### One combo raising fails the whole job

Same file:

- `_evaluate_combo` at lines 106–146, and the `_run_single_combo` it calls, have no try/except.
- If any joblib worker raises, `Parallel(...)` re-raises for the whole batch; the `except Exception` at lines 440–442 catches it and calls `_fail(job_id, "Optimization error at batch ...")`.
- All results from completed batches are discarded, and plateau never learns that this cell failed.

Zero trades are not this case: they return a `ComboEvaluation` whose metric is `None`. This is pinned by `test_zero_trade_combo_returns_an_undefined_objective` and `test_parallel_transport_also_returns_the_zero_trade_combo` in `tests/mcp/test_optimization_failed_trials.py` (sequential and joblib paths). The real search above confirms it as well.

### The confirmation form's approved checkbox (removed upstream)

Before the merge (`UserApproval.approved: bool = Field(default=False)` and `accepted = answer.action == "accept" and answer.data.approved` in `src/tradingdev/mcp/tools/execution.py`), Claude Code's elicitation form could not toggle this boolean. Pressing Enter submitted `approved=False`, which was treated as a refusal, so the plan could never be approved.

Upstream 3fa0852 (ce8cfb8 `build!: migrate MCP integration to SDK 2`) removed `request_execution_confirmation` and native elicitation in favour of `submit_execution_decision(plan_id, decision)`:

- `ARCHITECTURE.md` states that the old tool is removed.
- `docs/strategy_contract.md` states that the old tool is removed.

The problem no longer exists on current main. It is listed here only to explain why this branch's earlier be952d9 is not in the PR diff.

### Two things missing for leaderboard integration

See `docs/statistics_leaderboard_integration.md`.

- "Missing for Plateau Analysis": parameter coordinates per entry; a way to group entries that differ only in the searched settings (separate from the `comparability_error` check used for ranking); failed candidates kept as entries with the metric recorded as missing.
- "Missing for the Paired Bootstrap": each candidate's per-bar IC series (or predictions, with a fingerprint of the ranked signal); a shared bar index for those series so `align_returns` can pair them.

## Not done yet

- **The statistics modules have no external entry point yet:** no MCP tool or CLI command calls them. Whether they should become catalog metrics with `provider="statistics"` is still undecided. This is the item that most needs a response from the team.
- **The path where the engine or a strategy raises during execution has not been verified.**
- **`trials_from_metrics` only rejects undefined metrics, not metrics that are computable from too small a sample.**
  - In the search above, the best combination (9, 10) has only 2 trades. Its Sharpe is computable, so it is not dropped and becomes `best_params`. But a Sharpe from 2 trades has no statistical meaning: it ranks first only because fewer trades lose less.
  - A possible approach: a minimum-observations threshold, treating trials below it as failed while keeping the axes, in the same design pattern as `min_neighborhood`.
  - This is left for follow-up and is not part of this PR.
- **The KD figures are not guarded by tests:** -7.57, 86.3% and 5,014,735.72 exist only in `demo_output/`. The data and the cached pickles are not in Git, so check-full cannot detect a change in them. The pandas-sensitive period logic is covered by hand-computed periods tests, and the DSR hurdle and plateau figures are pinned by unit tests at rel 1e-6.
- **The demo picks its input by mtime:** `latest_cache()` selects the newest pickle, so a re-run does not necessarily read the one `kd_inference.md` cites.
- **`scripts/validate_run.py` has no automated tests:** its fixes were verified only by running it by hand on two pickles.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
