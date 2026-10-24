"""Re-run both demos into the scratchpad and print full-precision figures.

The demos are imported, not edited: OUTPUT_DIR is redirected and the
committed KD source pickle is pinned (latest_cache() would pick a newer file).
"""

from __future__ import annotations

import importlib.util
import pickle
import sys
from pathlib import Path

import numpy as np

ROOT = Path("/workspaces/tradingdev")
OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
PINNED = ROOT / "workspace/data/processed/cache/cd03bf19459b48af.pkl"


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.OUTPUT_DIR = OUT
    return module


stats = load("demo_statistics")
plateau = load("demo_plateau")
stats.latest_cache = lambda: PINNED
stats.ROOT = ROOT

from tradingdev.domain.statistics.breakeven import summarize_breakeven  # noqa: E402
from tradingdev.domain.statistics.periods import period_returns  # noqa: E402
from tradingdev.domain.statistics.sharpe import deflated_sharpe_ratio, sharpe_ratio  # noqa: E402


def kd_figures(result, label: str) -> None:
    equity = np.asarray(result.equity_curve, dtype=float)
    daily = period_returns(equity, result.timestamps, "daily").to_numpy()
    sr = sharpe_ratio(daily, periods_per_year=365.0)
    be = summarize_breakeven(
        result.trades, start=result.timestamps[0], end=result.timestamps[-1],
        capital=result.init_cash,
    )
    cost = be.traded_notional * (stats.FEES + stats.SLIPPAGE)
    net = float(equity[-1] - equity[0])
    print(f"[{label}] sharpe_daily_ann={sr!r}")
    print(f"[{label}] traded_notional={be.traded_notional!r}")
    print(f"[{label}] cost_over_abs_net={cost / abs(net)!r}")
    print(f"[{label}] net={net!r} n_trades={be.total_trades} n_days={len(daily)}")


with PINNED.open("rb") as handle:
    pipeline = pickle.load(handle)  # noqa: S301
kd_figures(pipeline.backtest_result, "cached-pickle")

fresh = stats.run_kd_variants()
for label, result in fresh.items():
    eq = np.asarray(result.equity_curve, dtype=float)
    r = period_returns(eq, result.timestamps, "daily").to_numpy()
    print(f"[fresh {label}] sharpe_daily_ann={sharpe_ratio(r, periods_per_year=365.0)!r}")
kd_figures(fresh["KD(14, 3, 3)"], "fresh KD(14,3,3)")

rng = np.random.default_rng(0)
dsr = deflated_sharpe_ratio(
    rng.normal(0.001, 0.01, 400),
    annualised_trial_sharpes=[-6.00, -6.67, -7.57],
    periods_per_year=365.0,
    n_trials=3,
)
print(f"[dsr] hurdle_annualised={dsr.hurdle_annualised!r}")

for name, module, cases in (
    ("demo_plateau", plateau, plateau.build_cases()),
    ("demo_statistics", stats, stats.plateau_cases()),
):
    summaries = (module.plot if name == "demo_plateau" else module.plot_plateau)(
        cases, OUT / f"{name}_plateau.png"
    )
    for case, s in summaries.items():
        print(f"[{name} {case}] metric_gap={s.metric_gap!r} "
              f"plateau_best_score={s.plateau_best_score!r}")

stats.main()
plateau.main()
