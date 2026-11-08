"""Repro for #190 on the checked-out main.

One dataset, one trained model. Entry A: the backend generates the signal from
the model (evaluate_prediction). Entry B: the caller supplies a random series
unrelated to the model and reports the same model_id (evaluate_signal). Both
are recorded; the two LeaderboardEntry rows are then compared field by field.
"""

from __future__ import annotations

import dataclasses
import json
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from tests.data_cache import seed_market_cache

from tradingdev.adapters.storage.filesystem import WorkspacePaths
from tradingdev.app.ml_service import MLService
from tradingdev.domain.ml.leaderboard import LeaderboardEntry
from tradingdev.domain.ml.registry import LeaderboardStore

ROWS = 600


def write_bars(workspace: WorkspacePaths) -> None:
    index = np.arange(ROWS, dtype=float)
    close = 100.0 + 10.0 * np.sin(index / 5.0) + index * 0.01
    seed_market_cache(workspace.processed_data, pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=ROWS, freq="h", tz="UTC"),
        "open": close, "high": close + 1.0, "low": close - 1.0, "close": close,
        "volume": np.full(ROWS, 10.0)}), symbol="BTC/USDT")


def as_dict(entry: LeaderboardEntry) -> dict:
    if dataclasses.is_dataclass(entry):
        return dataclasses.asdict(entry)
    return entry.model_dump(mode="json")


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        ws = WorkspacePaths(Path(tmp) / "workspace")
        ws.ensure()
        write_bars(ws)
        svc = MLService(workspace=ws)
        dataset_id = svc.build_dataset(symbol="BTC/USDT", timeframe="1h", start_date="2024-01-01",
                                       end_date="2024-01-12", feature_set="technical")["dataset"]["dataset_id"]
        model_id = svc.train_model(dataset_id=dataset_id, model_kind="xgboost_direction",
                                   parameters={"n_estimators": 5, "max_depth": 2})["model"]["model_id"]
        print(f"[setup] dataset_id={dataset_id} model_id={model_id}")

        a = svc.evaluate_prediction(model_id=model_id, dataset_id=dataset_id, window=20, record=True)
        snap_a = {e.entry_id: as_dict(e) for e in LeaderboardStore(ws.ml_leaderboard).entries()}
        print(f"[rows after A] {len(snap_a)}")
        frame = pd.read_parquet(ws.ml_datasets / dataset_id / "dataset.parquet")
        fwd = frame["forward_return"].astype(float).tolist()
        caller_signal = np.random.default_rng(7).normal(size=len(fwd)).tolist()
        b = svc.evaluate_signal(caller_signal, fwd, window=20, record=True,
                                model_id=model_id, dataset_id=dataset_id)

        entries = {e.entry_id: e for e in LeaderboardStore(ws.ml_leaderboard).entries()}
        print(f"[rows after B] {len(entries)}; A entry_id={a['recorded']['entry_id']} B entry_id={b['recorded']['entry_id']} B replaced={b['recorded']['replaced']}")
        ea = snap_a[a["recorded"]["entry_id"]]
        eb = as_dict(entries[b["recorded"]["entry_id"]])
        print(f"[A backend]  recorded = {json.dumps(a['recorded'], default=str, ensure_ascii=False)}")
        print(f"[B caller]   recorded = {json.dumps(b['recorded'], default=str, ensure_ascii=False)}")
        print(f"[fields] same field set: {sorted(ea) == sorted(eb)}; fields = {sorted(ea)}")
        print("[field-by-field] (same = identical value in both rows)")
        for k in sorted(ea):
            same = ea[k] == eb[k]
            va, vb = ea[k], eb[k]
            if not same and isinstance(va, (dict, list)):
                va, vb = "<differs>", "<differs>"
            print(f"  {k:<24} {'same' if same else 'DIFF'}   A={str(va)[:70]!s}   B={str(vb)[:70]!s}")
        origin = [k for k in ea if any(w in k for w in ("source", "origin", "produced", "generated"))]
        print(f"[origin-like fields] {origin or 'none'}")
        print(f"[family property] B row={entries[b['recorded']['entry_id']].family}")
        ma, mb = ea["metrics"], eb["metrics"]
        print("[metrics differing]", {k: (ma[k], mb.get(k)) for k in ma if ma[k] != mb.get(k) and k in ("ic_mean", "rank_ic_mean", "ic", "sharpe_ratio")} or sorted(k for k in ma if ma[k] != mb.get(k))[:8])


if __name__ == "__main__":
    main()
