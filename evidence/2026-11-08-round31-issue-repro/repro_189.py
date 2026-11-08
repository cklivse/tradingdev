"""Repro for #189 on the checked-out main.

Two optimization runs of the bundled KD strategy on the same synthetic bars:
one searches 2 parameter sets, the other 24. Trials are evaluated by the
worker's own ``_run_single_combo``, persisted by the worker's own
``_performance_artifacts`` into real workspace storage, then ranked by
``RankingService.rank_run_scopes`` with the default scope (the test scope).
The script prints what the ranking result carries and what the bundle holds.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from tests.app.test_run_ranking import _manifest  # the suite's own manifest fixture

from tradingdev.adapters.execution.strategy_factory import StrategyFactory
from tradingdev.adapters.storage.execution_manifests import ExecutionManifestStore
from tradingdev.adapters.storage.filesystem import WorkspacePaths
from tradingdev.adapters.storage.performance import PerformanceStore
from tradingdev.adapters.storage.sqlite import SQLiteStore
from tradingdev.app.ranking_service import RankingService
from tradingdev.domain.backtest.schemas import BacktestConfig, ParallelConfig
from tradingdev.domain.optimization.grid_search import parameter_grid
from tradingdev.domain.run_candidates import RunCandidate
from tradingdev.mcp.workers import optimization

METRIC = "sharpe_ratio"
STRATEGY = {"id": "kd_crossover", "parameters": {}}


def bars(days: int) -> pd.DataFrame:
    n = 24 * days
    ts = pd.date_range("2024-01-01", periods=n, freq="h", tz="UTC")
    close = 40_000.0 * np.exp(np.cumsum(np.random.default_rng(0).normal(0, 0.004, n)))
    return pd.DataFrame({"timestamp": ts, "open": close, "high": close * 1.002,
                         "low": close * 0.998, "close": close, "volume": 1.0})


def config(start: str, end: str) -> BacktestConfig:
    return BacktestConfig(symbol="BTC/USDT", timeframe="1h", start_date=start, end_date=end,
                          init_cash=10_000.0, fees=0.0006, slippage=0.0005,
                          periods_per_year=365.0)


def run(params, frame, cfg):
    return optimization._run_single_combo(
        STRATEGY, StrategyFactory().resolve_execution(STRATEGY), cfg, frame, params,
        METRIC, ParallelConfig(), 42)


def optimize(run_id, grid, train, test, workspace, store):
    train_cfg = config("2024-01-01", "2024-01-30T23:59:59.999999")
    test_cfg = config("2024-01-31", "2024-02-29T23:59:59.999999")
    combos = parameter_grid(grid)
    evals = [run(p, train, train_cfg) for p in combos]
    usable = [(i, e.target_value) for i, e in enumerate(evals) if e.target_value is not None]
    selected = max(usable, key=lambda x: x[1])[0]
    oos = run(evals[selected].parameters, test, test_cfg)
    manifest = _manifest()
    ExecutionManifestStore(workspace).publish(run_id, manifest)
    artifacts = optimization._performance_artifacts(
        run_id, manifest.manifest_hash, evals, selected, oos)
    store.create_run(run_id=run_id, job_id=f"job-{run_id}", strategy_id="kd_crossover",
                     revision_id="rev-1", artifact_dir=workspace.runs / run_id,
                     metrics=artifacts.performance.scopes["test"].model_dump(mode="json")["values"],
                     manifest_hash=manifest.manifest_hash)
    PerformanceStore(workspace, store).publish(artifacts)
    train_sharpes = [e.target_value for e in evals]
    return len(combos), train_sharpes, selected


def main() -> None:
    frame = bars(60)
    train = frame[frame.timestamp < "2024-01-31"].reset_index(drop=True)
    test = frame[frame.timestamp >= "2024-01-31"].reset_index(drop=True)
    with tempfile.TemporaryDirectory() as tmp:
        workspace = WorkspacePaths(Path(tmp) / "workspace")
        store = SQLiteStore(workspace)
        searched = {
            "narrow": optimize("narrow", {"k_period": [9, 14]}, train, test, workspace, store),
            "wide": optimize("wide", {"k_period": [5, 7, 9, 11, 14, 21, 28, 35],
                                      "d_period": [3, 5, 7]}, train, test, workspace, store),
        }
        for run_id, (n, sharpes, sel) in searched.items():
            print(f"[search] {run_id}: combos searched={n}, selected trial={sel}, "
                  f"train Sharpe of all trials (None = undefined)={[None if s is None else round(s, 4) for s in sharpes]}")
        for run_id in searched:
            b = PerformanceStore(workspace, store).load(run_id)
            trials = sorted((k for k in b.scopes if k.startswith("trial/")), key=lambda k: int(k.split("/")[1]))
            vals = [b.scopes[k].values.get("sharpe_ratio") for k in trials]
            print(f"[bundle] {run_id}: default_scope={b.default_scope}, trial scopes={len(trials)}, "
                  f"selected_train_scope={getattr(b, 'selected_train_scope', None)}, "
                  f"stored train Sharpe std (ddof=1)={float(np.std([v for v in vals if v is not None], ddof=1)):.4f}")
        result = RankingService(workspace=workspace, store=store).rank_run_scopes(
            "run.sharpe_ratio", [("narrow", None), ("wide", None)])
        print("[ranking result, full JSON]")
        print(json.dumps(result, indent=2, default=str, ensure_ascii=False))
        print("[RunCandidate fields]", list(RunCandidate.__dataclass_fields__)
              if hasattr(RunCandidate, "__dataclass_fields__") else list(RunCandidate.model_fields))
        text = json.dumps(result, default=str)
        for word in ("n_trials", "trial_count", "combos", "trial/", "search", "dispersion", "std"):
            print(f"[search in ranking JSON] {word!r}: {'FOUND' if word in text else 'absent'}")


if __name__ == "__main__":
    sys.exit(main())
