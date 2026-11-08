## #189、#190 的實測是怎麼跑的

兩個重現都在 `main` 1ea5276 的乾淨 checkout 上，用 `uv sync --locked --all-extras` 建環境，在**同一個 Python 程序內**直接呼叫產品程式碼。沒有經過 MCP、job store、背景 worker 程序或確認流程；行情是合成的，沒有下載；不需要 strategy-runtime 映像。

### #189（最佳化試驗 → 排名）

腳本：[`repro_189.py`](https://github.com/cklivse/tradingdev/blob/7b66c0c839a2cf8b6c33da888811344b3c57f271/evidence/2026-11-08-round31-issue-repro/repro_189.py)，輸出：[`repro_189.out`](https://github.com/cklivse/tradingdev/blob/7b66c0c839a2cf8b6c33da888811344b3c57f271/evidence/2026-11-08-round31-issue-repro/repro_189.out)

| 步驟 | 用的程式碼 | 誰做的 |
| --- | --- | --- |
| 行情：60 天小時 K 線，常態步長的隨機漫步（seed 0），前 30 天訓練、後 30 天測試 | — | 腳本 |
| 每組參數回測：內建 `kd_crossover`、真實回測引擎 | `optimization._run_single_combo` | 產品（worker 對每個 combo 呼叫的同一個函式） |
| 網格：2 組（`k_period` ∈ {9, 14}）和 24 組（8 個 `k_period` × 3 個 `d_period`） | `parameter_grid` | 產品 |
| 選出最好的一組 | 取訓練期 `target_value` 最大者 | **腳本**。worker 用的是 `best_result(candidates, direction=...)`；這裡是 maximize，選法相同，但沒有走那個函式 |
| 選中那組在測試期重跑 | `_run_single_combo` | 產品 |
| 產生 bundle（每組一個 `trial/{i}/train`，加上 `test`） | `optimization._performance_artifacts` | 產品 |
| 存進 workspace | `ExecutionManifestStore`、`SQLiteStore`、`PerformanceStore` | 產品 |
| manifest | `tests/app/test_run_ranking.py` 的 `_manifest()` | **測試 fixture**。它是 `kind="backtest"`、timeframe `1d`，不是真正的 optimization manifest；只影響排名結果裡的 `conditions` |
| 排名 | `RankingService.rank_run_scopes("run.sharpe_ratio", ...)`，scope 用預設 | 產品 |
| DSR 門檻驗算 | `deflated_sharpe_ratio`（statistics 拆分第 4 包，#209） | 拆分分支上的程式碼，不在 `main` |

所以「每組怎麼回測、bundle 怎麼存、排名怎麼讀」都是產品程式碼；「選哪一組」和「manifest」是腳本或 fixture 代替的。完整的 `_run_optimization`（job、資料下載、joblib 平行、`best_result`）沒有跑。

### #190（模型訊號 vs 呼叫端訊號）

腳本：[`repro_190.py`](https://github.com/cklivse/tradingdev/blob/7b66c0c839a2cf8b6c33da888811344b3c57f271/evidence/2026-11-08-round31-issue-repro/repro_190.py)，輸出：[`repro_190.out`](https://github.com/cklivse/tradingdev/blob/7b66c0c839a2cf8b6c33da888811344b3c57f271/evidence/2026-11-08-round31-issue-repro/repro_190.out)

| 步驟 | 用的程式碼 | 誰做的 |
| --- | --- | --- |
| 行情：600 根小時 K 線，正弦加趨勢，寫進行情快取 | `tests.data_cache.seed_market_cache` | 測試 helper（和 `tests/app/test_ml_training_binding.py` 相同） |
| 建資料集（2024-01-01..2024-01-12，`technical`） | `MLService.build_dataset` | 產品 |
| 訓練模型：`xgboost_direction`，`n_estimators=5`、`max_depth=2` | `MLService.train_model` | 產品 |
| A：後端用模型算訊號並記錄（評估和訓練用同一個資料集） | `MLService.evaluate_prediction(..., record=True)` | 產品 |
| B：呼叫端給一條隨機序列（`np.random.default_rng(7)`），報同一個 `model_id` 並記錄 | `MLService.evaluate_signal(..., model_id=..., record=True)` | 產品的 Python API；隨機序列由腳本產生 |
| 讀回紀錄、逐欄位比較 | `LeaderboardStore.entries()` | 產品；比較由腳本做 |

B 只能經由 Python API 寫入；MCP 工具帶 `model_id` 時一律走 `evaluate_prediction`。

### 怎麼重跑

在 repo 根目錄：

```bash
uv sync --locked --all-extras
PYTHONPATH=. .venv/bin/python repro_189.py   # 約 1 分鐘
PYTHONPATH=. .venv/bin/python repro_190.py
```

腳本需要 import `tests.`，所以要 `PYTHONPATH=.`。另外，同一份實測期間，這四個既有測試檔在 1ea5276 上 136 passed：`tests/app/test_run_ranking.py`、`test_ml_training_binding.py`、`test_ml_leaderboard.py`、`test_ml_predict.py`。
