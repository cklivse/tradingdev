# Statistics Public API

This is a handover for whoever exposes `src/tradingdev/domain/statistics/`
through MCP tools. It lists the entry points, the failure conventions an
adapter must translate, and the order of calls from a run's outputs to a
presentable result. The modules' docstrings remain the reference for formulas
and edge cases; this document says which of them to read and what is easy to
get wrong.

The modules are pure functions over caller-supplied data. They never read
runs, artifacts, caches or an engine's `metrics`; the adapter loads those and
passes arrays or `pandas.Series` in.

## Known Limitations

Read these before designing a tool; each one constrains what a tool may
claim.

- **One frequency per comparison.** Every figure is computed on returns of
  one frequency and annualised with one `periods_per_year`. Daily returns
  (`periods_per_year=365` for crypto, 252 for exchange-traded markets) are
  the reference. Monthly figures are another view of the same run, not a
  second dimension to compare against daily ones: a daily Sharpe and a
  monthly Sharpe of the same strategy differ for statistical reasons, and
  intraday returns annualised with `sqrt(periods_per_year)` are biased (one
  KD run measured -8.70 from hourly returns and -7.57 from daily ones).
- **Monthly returns rarely get a confidence interval.** The stationary
  bootstrap needs `MIN_BOOTSTRAP_OBSERVATIONS = 20` periods (20 common
  periods for comparisons). Twenty periods is 20 days of daily returns but
  20 months of monthly ones, so a one-year run never has a monthly interval.
  The `*_outcome` functions report this as `"insufficient_observations"`.
- **Plateau scores are not comparable across runs.** They depend on the
  radius and the grid density, so compare them only within one search. The
  only trial scopes upstream persists are `trial/{index}/train`, so a
  plateau built from them is in-sample and must be labelled as such.
- **The deflated Sharpe ratio over-corrects on grid searches.** It assumes
  `N` independent trials, but neighbouring grid points are nearly the same
  strategy, so the effective number of trials is smaller than `N`. The
  correction leans towards rejecting a real edge; this is deliberate and
  should be stated wherever a DSR is shown.
- **Comparisons are only as fair as their inputs.** Paired comparisons
  guarantee a common period, nothing more. Strategies on different
  instruments, windows or cost models are not comparable, and in-sample
  returns of tuned parameters measure overfitting, not quality; compare
  out-of-sample returns such as walk-forward test folds.

## Public Entry Points

`tradingdev.domain.statistics` re-exports every entry point and declares
them in `__all__`; import from the package, not from the modules. Importing
the package loads every module, including `arch` for the bootstrap, which
takes on the order of a second; import it where statistics are computed,
not at server start-up if that matters.

| Module | Question it answers | Entry points | Result types |
| --- | --- | --- | --- |
| `periods` | What are a run's daily or monthly P&L and returns on UTC boundaries? | `period_returns`, `period_pnl`, `period_closing_equity` | `pandas.Series`; `Frequency` is `"daily"` or `"monthly"` |
| `performance` | What were the run's return, volatility, drawdown and win rate, from raw outputs alone? | `summarize_performance` | `PerformanceSummary` |
| `breakeven` | What win rate breaks even, and what are the traded notional and turnover? | `summarize_breakeven` | `BreakevenSummary` |
| `sharpe` | How reliable is the annualised Sharpe, and does it survive selection bias? | `sharpe_ratio`, `sharpe_interval_outcome`, `sharpe_confidence_interval`, `probabilistic_sharpe_ratio`, `deflated_sharpe_ratio` | `SharpeInterval`, `IntervalUnavailable`, `UnavailableReason`, `DeflatedSharpe`; constant `MIN_BOOTSTRAP_OBSERVATIONS` |
| `comparison` | Is the difference between strategies on the same data significant? | `align_returns`, `difference_interval_outcome`, `difference_interval`, `interval_table_outcome`, `interval_table` | `AlignedReturns`, `DifferenceInterval`, `StatisticInterval` |
| `plateau` | Is the best parameter set on a plateau or an isolated spike? | `trials_from_metrics`, `plateau_summary`, `plateau_scores`, `plateau_grid` | `Trial`, `MetricTrials`, `PlateauSummary`, `PlateauScore`, `PlateauGrid`, `DroppedTrialsWarning`; constant `DEFAULT_RADIUS` |
| `benchmark` | How does the strategy compare with and co-move with buy-and-hold? | `buy_and_hold_returns`, `compare_to_benchmark` | `BenchmarkComparison` |

Everything else is internal: names starting with `_`, the helpers that
`periods` shares with the other modules (`to_utc_index`, `equity_series`,
`has_positive_equity`) and the modules' implementation constants
(`DEFAULT_PERIODS_PER_YEAR`, `DAYS_PER_YEAR`, `EULER_MASCHERONI`,
`MAX_LOCAL_DIMENSIONS`, `NEGLIGIBLE_SPREAD`). Do not build tools on them.

Results are frozen dataclasses, `pandas.Series` or plain dicts, and not
all of them serialise as they are. `IntervalUnavailable.message` is a
ready-made sentence for a tool response.

| Result | `json.dumps(dataclasses.asdict(result))` | Convert before serialising |
| --- | --- | --- |
| `BreakevenSummary`, `SharpeInterval`, `IntervalUnavailable`, `DeflatedSharpe`, `DifferenceInterval`, `StatisticInterval`, `BenchmarkComparison` | works | nothing |
| `PerformanceSummary` | fails | `start` and `end` are `pandas.Timestamp`; use `isoformat()` |
| `Trial`, `PlateauScore`, `PlateauSummary`, `PlateauGrid`, `MetricTrials` | fails (`asdict` cannot copy a mapping proxy) | `params`, `best_params`, `plateau_best_params`, `axis_sizes`, `fixed_params` and `axes` are read-only mappings; copy them with `dict(...)` |
| `AlignedReturns` | fails | `frame` is a `DataFrame`; usually report `overlap`, `lengths` and `sufficient` only |
| `period_returns`, `period_pnl`, `period_closing_equity`, `buy_and_hold_returns` | not dataclasses | `pandas.Series` indexed by UTC period start |
| `interval_table_outcome`, `interval_table` | not dataclasses | dict from series name to a row result (or `None`) |

## Failure Conventions

These are spread across the modules and are the easiest part to misuse.

### `None` Versus `ValueError`

- **`ValueError` means the input is wrong**, and the adapter should report it
  as an invalid request: non-finite values, mismatched lengths, timestamps
  that are not strictly increasing, duplicate index labels, a
  `periods_per_year` that is not positive and finite, malformed trade
  records, an unknown `direction`, or inconsistent plateau rows.
- **`None` means the statistic is undefined for valid input**: fewer than
  two returns, zero dispersion, no wins or no losses, no neighbours. Show it
  as "not available", never as zero. Result fields follow the same rule;
  for example `BreakevenSummary.payoff_ratio` is `None` without losses.
- **Use the `*_outcome` functions in tools.** `sharpe_interval_outcome`,
  `difference_interval_outcome` and `interval_table_outcome` return an
  `IntervalUnavailable` instead of `None`. It carries `reason`
  (`"insufficient_observations"`, `"undefined_statistic"` or
  `"no_valid_resample"`), the point `estimate` when it is defined,
  `observations`, `min_observations` and `reps`, so a tool can say why an
  interval is missing. `sharpe_confidence_interval`, `difference_interval`
  and `interval_table` are the same computations with every reason collapsed
  to `None`.
- **Pass a `seed`** to every bootstrap call in a tool. Without one, intervals
  and p-values change from call to call.

### Plateau Inputs: Axes and Direction

- `plateau_summary`, `plateau_scores` and `plateau_grid` take `axes` as a
  required keyword. Pass `MetricTrials.axes` from `trials_from_metrics`; it
  holds every searched value, failed trials included, so a failed slice
  stays a missing grid point instead of disappearing from its axis.
- `Trial.metric` is higher-is-better. `trials_from_metrics` applies the
  metric's `optimization_direction` (`direction="maximize"` or
  `"minimize"`, never inferred) and negates minimised metrics. Building
  `Trial` objects by hand from a minimised metric such as `max_drawdown`
  silently selects the worst parameter set as the best.
- Pass every searched row, failed ones included, with the metric as `None`.
  Report `MetricTrials.dropped_count` next to the plateau result.
- A zero-trade trial is identified by `metrics.total_trades == 0`, not by its
  `metadata.unavailable` codes: the engine marks Sharpe, Sortino and Calmar
  `zero_denominator` (flat equity) and only the trade-based metrics
  `no_trades`.

### Deflated Sharpe: `n_trials`

`deflated_sharpe_ratio` must receive `n_trials = len(result.trials) +
result.dropped_count`, the number of trials searched. Its default is the
number of trial Sharpes passed in, which counts only the survivors:
`N` is underestimated, the selection bias under-corrected, and nothing
raises. The trial Sharpes must be annualised with the same
`periods_per_year` as the selected strategy's returns.

### Benchmark and Comparison Alignment

`align_returns`, and with it every comparison and `compare_to_benchmark`,
pairs series by index label. Mixing a timezone-naive index with a
timezone-aware one raises `ValueError` whose message names the naive and
aware series and calls it a timezone mismatch, not non-overlapping
periods. `period_returns` and `buy_and_hold_returns` always return UTC
indexes, so build both sides with them. When the overlap is short,
`compare_to_benchmark` raises only if the series share no period at all;
`difference_interval_outcome` and `interval_table_outcome` report an overlap
below 20 as `"insufficient_observations"`; `difference_interval` and
`interval_table` return `None`; and `align_returns` sets
`sufficient=False`.

### Other Conventions

- `probabilistic_sharpe_ratio(returns, benchmark_sr=...)` takes a per-period
  benchmark Sharpe, not an annualised one; divide an annual figure by
  `sqrt(periods_per_year)` before passing it.
- In volume mode the equity curve is cumulative P&L starting from zero
  (`BacktestResult.equity_curve`). Returns are undefined there:
  `period_returns`, the Sharpe functions, the benchmark comparison and the
  return-based fields of `summarize_performance` do not apply. Use
  `period_pnl`, and call `summarize_breakeven(..., capital=None)`.
- A run's first period return is measured against `equity_curve[0]`, the
  first bar's equity, not against `init_cash`.
- `trials_from_metrics` needs a `direction`; catalog metrics whose
  `optimization_direction` is `None` cannot be used for plateau analysis.
- `trials_from_metrics` also issues a `DroppedTrialsWarning` when it drops
  rows. Under an `"error"` warnings filter that warning is raised instead of
  returning, so a tool should not run it under such a filter; rely on
  `dropped_count`.
- `summarize_performance` defaults to `periods_per_year=365` and
  `summarize_breakeven` measures years as 365.25 days. Pass
  `periods_per_year` explicitly for markets that do not trade every day.

### One `periods_per_year`

Choose one frequency and one `periods_per_year` per tool call and use it for
every series and every statistic in that call, including the `statistic`
passed to the comparison functions and the trial Sharpes passed to the DSR.
Do not place figures computed at different frequencies side by side as if
they were comparable.

## Minimal Call Sequence

From one run's outputs to a presentable result. `result` is a backtest result
with `equity_curve`, `timestamps`, `trades` and `init_cash`; the adapter also
loads the close prices of the same bars for the benchmark.

```python
from functools import partial

from tradingdev.domain.statistics import (
    IntervalUnavailable,
    buy_and_hold_returns,
    compare_to_benchmark,
    difference_interval_outcome,
    period_returns,
    probabilistic_sharpe_ratio,
    sharpe_interval_outcome,
    sharpe_ratio,
)

PPY = 365.0  # one frequency, one periods_per_year, for every figure below

# 1. periods: per-bar equity -> one return per UTC day (empty days omitted).
#    Needs the raw equity curve and its bar timestamps, not daily returns.
#    Raises ValueError on inconsistent input or non-positive equity.
returns = period_returns(result.equity_curve, result.timestamps, "daily")

# 2. sharpe: point estimate, interval with its reason when missing, PSR.
sharpe = sharpe_ratio(returns, periods_per_year=PPY)  # None if undefined
interval = sharpe_interval_outcome(returns, periods_per_year=PPY, seed=0)
if isinstance(interval, IntervalUnavailable):
    note = interval.message  # e.g. "12 observations, fewer than the 20 ..."
psr = probabilistic_sharpe_ratio(returns)  # P(true Sharpe > 0) or None

# 3. comparison: another run on the same bars and cost model, built the
#    same way. The statistic fixes periods_per_year for both sides.
other = period_returns(other_result.equity_curve, other_result.timestamps, "daily")
statistic = partial(sharpe_ratio, periods_per_year=PPY)
versus = difference_interval_outcome(returns, other, statistic, seed=0)

# 4. benchmark: buy-and-hold on the prices the equity is marked at, same
#    timestamps and frequency, so both sides share UTC labels.
benchmark = buy_and_hold_returns(
    close_prices, timestamps=result.timestamps, frequency="daily"
)
beats_hold = difference_interval_outcome(returns, benchmark, statistic, seed=0)
regression = compare_to_benchmark(returns, benchmark, periods_per_year=PPY)
```

For a parameter search, add plateau analysis and the deflated Sharpe ratio
from the trial scopes:

```python
from tradingdev.domain.statistics import (
    deflated_sharpe_ratio,
    plateau_summary,
    trials_from_metrics,
)

# rows: one per searched parameter set, flattened from the trial scopes as
# {"parameters": ..., "sharpe_ratio": ...}; failed ones carry None.
# direction: the metric's optimization_direction from the metric catalog.
searched = trials_from_metrics(
    rows, params_key="parameters", metric_key="sharpe_ratio", direction=direction
)
plateau = plateau_summary(searched.trials, axes=searched.axes)  # in-sample

# The surviving trials' Sharpes, exactly the trials n_trials counts beside
# the dropped ones. Trial.metric equals the Sharpe because sharpe_ratio is
# maximised; a minimised metric would be negated here.
dsr = deflated_sharpe_ratio(
    selected_returns,
    [trial.metric for trial in searched.trials],
    periods_per_year=PPY,
    n_trials=len(searched.trials) + searched.dropped_count,
)
```

The trial Sharpes above are the engine's `metrics.sharpe_ratio` from the trial
scopes, computed with that run's settings, not with `PPY`. Before using
them, check that the scope's `metadata.settings.periods_per_year` equals
`PPY` and its `risk_free_rate` is 0, the same basis as
`sharpe_ratio(selected_returns, periods_per_year=PPY)`. If either differs,
the hurdle is silently computed on another scale.

`docs/statistics_leaderboard_integration.md` covers the separate question of
what the ML leaderboard must record before these modules can analyse its
candidates.
