"""Engine-independent performance statistics computed from raw run outputs.

The names in ``__all__`` are the public entry points; see
``docs/statistics_public_api.md`` for their failure conventions.
"""

from tradingdev.domain.statistics.benchmark import (
    BenchmarkComparison,
    buy_and_hold_returns,
    compare_to_benchmark,
)
from tradingdev.domain.statistics.breakeven import (
    BreakevenSummary,
    summarize_breakeven,
)
from tradingdev.domain.statistics.comparison import (
    AlignedReturns,
    DifferenceInterval,
    StatisticInterval,
    align_returns,
    difference_interval,
    difference_interval_outcome,
    interval_table,
    interval_table_outcome,
)
from tradingdev.domain.statistics.performance import (
    PerformanceSummary,
    summarize_performance,
)
from tradingdev.domain.statistics.periods import (
    Frequency,
    period_closing_equity,
    period_pnl,
    period_returns,
)
from tradingdev.domain.statistics.plateau import (
    DEFAULT_RADIUS,
    DroppedTrialsWarning,
    MetricTrials,
    PlateauGrid,
    PlateauScore,
    PlateauSummary,
    Trial,
    plateau_grid,
    plateau_scores,
    plateau_summary,
    trials_from_metrics,
)
from tradingdev.domain.statistics.sharpe import (
    MIN_BOOTSTRAP_OBSERVATIONS,
    DeflatedSharpe,
    IntervalUnavailable,
    SharpeInterval,
    UnavailableReason,
    deflated_sharpe_ratio,
    probabilistic_sharpe_ratio,
    sharpe_confidence_interval,
    sharpe_interval_outcome,
    sharpe_ratio,
)

__all__ = [
    "DEFAULT_RADIUS",
    "MIN_BOOTSTRAP_OBSERVATIONS",
    "AlignedReturns",
    "BenchmarkComparison",
    "BreakevenSummary",
    "DeflatedSharpe",
    "DifferenceInterval",
    "DroppedTrialsWarning",
    "Frequency",
    "IntervalUnavailable",
    "MetricTrials",
    "PerformanceSummary",
    "PlateauGrid",
    "PlateauScore",
    "PlateauSummary",
    "SharpeInterval",
    "StatisticInterval",
    "Trial",
    "UnavailableReason",
    "align_returns",
    "buy_and_hold_returns",
    "compare_to_benchmark",
    "deflated_sharpe_ratio",
    "difference_interval",
    "difference_interval_outcome",
    "interval_table",
    "interval_table_outcome",
    "period_closing_equity",
    "period_pnl",
    "period_returns",
    "plateau_grid",
    "plateau_scores",
    "plateau_summary",
    "probabilistic_sharpe_ratio",
    "sharpe_confidence_interval",
    "sharpe_interval_outcome",
    "sharpe_ratio",
    "summarize_breakeven",
    "summarize_performance",
    "trials_from_metrics",
]
