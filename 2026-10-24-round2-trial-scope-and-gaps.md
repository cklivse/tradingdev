# 2026-10-24 第二輪：trial scope 驗證、push、hooks、四個缺口

分支：`feat/stats-py314`。本報告與對話中的回報內容相同。

## 結論

- **trial scope：** 15 組都留下了各自完整的 `trial/{i}/train` scope，包含 oversold=0 那 5 組。失敗的組合不會消失：33 個指標欄位全都在，算不出來的指標值為 `None`，原因寫在 `metadata.unavailable`。
- **4b：** 時區混用改成明確 raise。
- **4c：** 未平倉的 trade 改成只算進場腿，仍留在勝敗樣本中。
- **check-full：** 通過，4243 passed
- **五個驗證數字：** 沒有任何一個因為 4a 或其他修正而改變，全精度相同。

## 任務 1：trial/{index}/train 的實際內容

### 執行方式

- 這個 session 的 tradingdev MCP 原生連線在開始時逾時，所以用 MCP SDK 的 stdio client 腳本，呼叫同一個真實伺服器。
- 依序呼叫 `prepare_optimization`、`submit_execution_decision(decision="approve")`、`get_job_status`、`get_run_metrics(scope=...)`。
- approve 是在使用者讀過確認單、在對話中明確同意後才送出的。

### 計畫設定

- 計畫 ID：`f245f73b6ebb4c4b9c06b2ee08457339`，manifest `56739a09…`。
- KD，BTC/USDT 1h。
- 訓練期 2024-01-01～2024-06-30，測試期 2024-07-01～2024-12-31。
- overbought=100，經 `parameters` 傳入。
- 格點：k_period ∈ {9,14,21,28,35} × oversold，共 15 組。
- 暖機申報 45 根，目標指標為 `sharpe_ratio`。

### 和原規劃不同的兩處

- **oversold 順序改為 `[20, 10, 0]`：** preflight 只取每個範圍的第一個值，在 512 根的訓練樣本上試跑（`src/tradingdev/adapters/execution/preflight_worker.py:232-293`）。原順序 `[10, 20, 0]` 的第一組是 k=9、oversold=10，在樣本內 Sharpe 未定義，prepare 回傳 `unrankable_sample_objective`，沒有建立計畫。改順序後格點仍是同樣 15 組。
  - 這本身就是 plateau 契約的限制：會失敗的組合不能放在第一個。
- **`/fit_config` 需要說明：** 它在 bundled config 中是空值，所以策略不會自行調參。

### 結果

job 狀態 `done`，`selected_train_scope = trial/1/train`（k=9、oversold=10）。

| scope | 參數 | 交易數 | sharpe_ratio |
| --- | --- | ---: | ---: |
| trial/0/train | k=9, os=20 | 57 | -4.348 |
| trial/1/train | k=9, os=10 | 2 | -1.695 |
| trial/2/train | k=9, os=0 | 0 | None |
| trial/3/train | k=14, os=20 | 74 | -4.938 |
| trial/4/train | k=14, os=10 | 4 | -2.571 |
| trial/5/train | k=14, os=0 | 0 | None |
| trial/6/train | k=21, os=20 | 83 | -4.752 |
| trial/7/train | k=21, os=10 | 8 | -2.240 |
| trial/8/train | k=21, os=0 | 0 | None |
| trial/9/train | k=28, os=20 | 79 | -4.254 |
| trial/10/train | k=28, os=10 | 12 | -3.425 |
| trial/11/train | k=28, os=0 | 0 | None |
| trial/12/train | k=35, os=20 | 83 | -3.713 |
| trial/13/train | k=35, os=10 | 13 | -3.120 |
| trial/14/train | k=35, os=0 | 0 | None |

### 一筆原始結構：trial/2/train（k=9, oversold=0）

`definitions`、`settings`、`observations` 已節錄；完整內容由 `get_run_metrics` 讀回。

```json
{
  "details_available": true,
  "provenance": "performance_artifact",
  "available_metric_ids": [
    "annual_return",
    "annual_volatility",
    "avg_holding_bars",
    "... (33)"
  ],
  "available_scopes": [
    "test",
    "trial/0/train",
    "trial/1/train",
    "... (16)"
  ],
  "default_scope": "test",
  "selected_train_scope": "trial/1/train",
  "detail_error": null,
  "success": true,
  "run_id": "f245f73b6ebb4c4b9c06b2ee08457339",
  "manifest_hash": "56739a0984f9e0a26159d66451ab26b6b949896a855ab7b8c37d0c60b1f48567",
  "scope": "trial/2/train",
  "kind": "backtest",
  "mode": "signal",
  "split": "train",
  "fold_index": null,
  "trial_index": 2,
  "parameters": {
    "k_period": 9,
    "oversold": 0
  },
  "metrics": {
    "annual_return": 0.0,
    "annual_volatility": 0.0,
    "avg_holding_bars": null,
    "calmar_ratio": null,
    "daily_max_drawdown": 0.0,
    "daily_pnl_max": 0.0,
    "daily_pnl_mean": 0.0,
    "daily_pnl_median": 0.0,
    "daily_pnl_min": 0.0,
    "daily_pnl_std": 0.0,
    "max_drawdown": 0.0,
    "max_drawdown_amount": 0.0,
    "monthly_pnl_max": 0.0,
    "monthly_pnl_mean": 0.0,
    "monthly_pnl_median": 0.0,
    "monthly_pnl_min": 0.0,
    "monthly_pnl_std": 0.0,
    "monthly_trades_mean": 0.0,
    "monthly_volume_mean": 0.0,
    "n_days": 182,
    "n_months": 6,
    "open_trades": 0,
    "profit_factor": null,
    "sharpe_ratio": null,
    "sortino_ratio": null,
    "total_fees": 0.0,
    "total_pnl": 0.0,
    "total_return": 0.0,
    "total_slippage": null,
    "total_trades": 0,
    "total_volume": 0.0,
    "trade_expectancy": null,
    "win_rate": null
  },
  "metadata": {
    "calculation_fallbacks": {},
    "execution_context": {
      "end_date": "2024-06-30T23:59:59.999999",
      "fees": 0.0006,
      "init_cash": 10000.0,
      "mode": "signal",
      "monthly_max_loss": 1500.0,
      "periods_per_year": 365.0,
      "position_size": null,
      "random_seed": null,
      "re_entry_after_sl": true,
      "required_return": 0.0,
      "risk_free_rate": 0.0,
      "signal_as_position": false,
      "slippage": 0.0005,
      "start_date": "2024-01-01T00:00:00",
      "stop_loss": null,
      "symbol": "BTC/USDT",
      "take_profit": null,
      "timeframe": "1h"
    },
    "mode": "signal",
    "observations": {
      "account_history_availability": "available",
      "account_history_mark": "bar_close",
      "accounting": "vectorbt_generic",
      "bar_count": 4368,
      "...": "(more)"
    },
    "providers": "(per-metric provider map)",
    "schema_version": 1,
    "settings": {
      "calendar_timezone": "UTC",
      "calmar_drawdown_sampling": "observed_daily",
      "cost_model": "commission_and_slippage_adjusted_fill_prices",
      "...": "(19 keys)"
    },
    "strategy_parameters": {
      "d_period": 3,
      "k_period": 9,
      "overbought": 100.0,
      "oversold": 0.0,
      "smooth_k": 3
    },
    "unavailable": {
      "avg_holding_bars": "no_trades",
      "calmar_ratio": "zero_denominator",
      "profit_factor": "no_trades",
      "sharpe_ratio": "zero_denominator",
      "sortino_ratio": "zero_denominator",
      "total_slippage": "embedded_in_fill_prices",
      "trade_expectancy": "no_trades",
      "win_rate": "no_trades"
    }
  },
  "definitions": {
    "sharpe_ratio": {
      "id": "sharpe_ratio",
      "unit": "ratio",
      "category": "risk",
      "provider": "quantstats",
      "description": "Annualized excess daily return divided by sample standard deviation. Requires a recognized bar frequency of one day or finer; coarser or unknown bars cannot establish daily equity observations or allocate PnL across calendar boundaries.",
      "summary": true,
      "optimization_direction": "maximize",
      "modes": [
        "signal"
      ],
      "requires_annualization": true
    },
    "...": "(33 entries, one per metric)"
  }
}
```

### 失敗那 5 組的形式

- **都有紀錄：** `available_scopes` 列出全部 15 個 trial scope，`success: true`，`trial_index` 和 `parameters` 齊全。
- **指標欄位不會消失：** 33 個鍵和成功的 trial 完全相同（已逐一比對）。
- **為 `None` 的 8 個：** `sharpe_ratio`、`sortino_ratio`、`calmar_ratio`、`win_rate`、`profit_factor`、`trade_expectancy`、`avg_holding_bars`，以及 `total_slippage`（成功的 trial 也是 None）。
- **為 0 而不是 None 的：** `total_trades`、`total_pnl`、`max_drawdown`、`annual_return` 等。
- **原因寫在 `metadata.unavailable`：**
  - `sharpe_ratio`、`sortino_ratio`、`calmar_ratio` 的原因是 `zero_denominator`，不是 `no_trades`。
  - `win_rate`、`profit_factor`、`trade_expectancy`、`avg_holding_bars` 的原因是 `no_trades`。
  - 所以如果要區分「零交易」和「權益曲線平坦」，要看 `total_trades == 0`，不能只看 Sharpe 的原因碼。

### 接上我們的 plateau 模組

把 15 個 scope 的 `parameters` 和 `metrics.sharpe_ratio` 直接餵給 `trials_from_metrics(direction="maximize")` 與 `plateau_summary`：

- **失敗試驗：** `dropped_count=5`，並發出 `DroppedTrialsWarning`。
- **軸：** `axes` 仍然保留 `oversold=(0, 10, 20)`，失敗的 5 格成為缺失格點，不會從軸上消失。
- **摘要結果：**
  - best = (9, 10)，Sharpe -1.695
  - plateau_best = (9, 20)，score -3.068
  - metric_gap 2.653，grid_distance 1
  - best_neighborhood_size 3：角落點本來有 5 個鄰居，其中 2 個是缺失格點。

旁註：最佳組合只有 2 筆交易，它「最好」是因為交易少、虧得少。這個結果不能當作參數有效的證據。

## 任務 2：push

- `origin/feat/stats-py314` 從 `9a3e331` 起建立：包含 `aac83b8`（merge）和 `9a3e331`（docs）。
- `feat/stats-on-latest` 維持在 `814b05a`，沒有動。
- 沒有建立 PR。

## 任務 3：git hooks

沒有裝上。`./scripts/install-git-hooks.sh` 拒絕執行：`Refusing to disable existing hook: .git/hooks/post-checkout`。

- **現有 hook 的內容：** `.git/hooks/` 裡的 post-checkout、post-commit、post-merge、pre-push 都是 Git LFS 的 hook。
- **repo 實際沒用 LFS：** `git lfs ls-files` 為 0 筆，也沒有 `.gitattributes`。
- **影響：** 設定 `core.hooksPath=.githooks` 會讓這些 LFS hook 失效。依目前的證據不會有影響，但腳本刻意要求人來決定，所以我沒有刪除或搬移它們。
- **需要決定：** 要不要移除這 4 個 LFS hook，再重跑安裝。
- **在那之前：** 每次 commit 前仍手動跑 check-fast。

## 任務 4：四個缺口

### 4a scripts/validate_run.py

- **V3：** 改為對照 `METRIC_CATALOG["max_drawdown"]`。只在 catalog 適用的模式（signal）下檢查，條件是 `>= 0`。
  - catalog 沒有定義上限；放空可能讓虧損超過 100%，所以依審查意見拿掉了原本暫設的 `<= 1`。
- **成本：** 改成 `fee_rate × summarize_breakeven(...).traded_notional`，和 `demo_statistics.py` 一致，不再用 `2 × total_volume`。
  - 只在有成本率時才計算。
  - 交易紀錄有問題時記為 `C2` FAIL，不會讓整支腳本 traceback。
- **實跑：**
  - 目前引擎的 pickle：24 項 PASS，exit 0，成本占比 86%（原本是 173%）。
  - 舊格式 pickle `cd03bf…`：V3 與 T1–T4 仍判 FAIL。這是舊引擎輸出的真實差異（負號回撤、把 K 棒數當天數），屬預期。

### 4b align_returns 的時區混用（選擇：明確 raise）

- 偵測到 naive 和 aware 的 `DatetimeIndex` 混用時，raise `ValueError`。訊息會寫出哪些序列是 naive、哪些是 aware，並明講是「timezone mismatch, not non-overlapping periods」。
- 檢查放在 `align_returns` 開頭，所以五個呼叫端都涵蓋：`difference_interval`、`difference_interval_outcome`、`interval_table`、`interval_table_outcome`、`compare_to_benchmark`。
- 不同時區的 aware 序列（例如 UTC 對 Asia/Taipei）仍然正常對齊，全部 naive 也一樣。
- `compare_to_benchmark` 原本在這種情況會給出含糊的「share no period」錯誤。原有的那個測試改為預期新的訊息，docstring 也已更新。
- **範圍外：** DatetimeIndex 和 RangeIndex 或字串 index 混用仍會得到 overlap 0。專案的來源都產生 UTC DatetimeIndex，所以不擴大處理。

### 4c breakeven 的未平倉 trade（選擇：納入，但只算進場腿）

- **原本的行為（已重現）：** 未平倉 trade 以 `size × exit/entry` 加上一條沒發生的出場腿。測試案例中 breakeven 算出 3,990，引擎的 `total_volume` 是 3,010。
- **選這個做法的理由（已寫進模組 docstring）：**
  - 進場確實成交、也付了成本。排除它會低估周轉率和成本。
  - 引擎的 `total_volume` 也只計已成交的單。
  - 它的 `net_pnl` 是按市價計算的，已經反映在權益曲線裡。所以它仍算勝或敗，維持「交易淨損益總和 = 整段損益」，也維持 edge 正負號的恆等式。
  - 與引擎的差異也寫明了：引擎的 `total_trades` 和 `win_rate` 只算已平倉的交易，所以期末有未平倉時，筆數和勝率會不同。
- **status 欄位：** 沒有 `status` 的舊紀錄視為已平倉；其他值一律 raise。
- **審查者的實測：** 用 vectorbt 跑了含反手、期末留倉的情境，traded_notional 和 orders 的 `size × price` 總和完全相等。
- **測試：**
  - 只算進場腿，並等於引擎 `total_volume` 的算法。
  - 留在勝敗樣本中。
  - 缺 status 視為已平倉。
  - 未知 status 會 raise。

### 4d demo 的 fee 說明

- 這句改成依實際值決定：trades 的 fee 總和為 0 時保留原句（舊 pickle）；否則寫出實際的 fee 總額，並說明 slippage 已併入成交價。
- 目前引擎的 pickle 會產生「fees of 3,008.84」。3,008.84 = 0.0006 × 5,014,736，所以 trades 只記了手續費。

### 文件

- `demo_output/METHODS.md`：指向 `breakeven.py` 和 `comparison.py` 的行號全部重新對應並逐一抽查過，另外補了 4b、4c 各一句說明。
- `benchmark.py` 的 docstring 已隨 4b 更新。

## 五個驗證數字（4a～4d 之後重跑）

全部和已提交的 `demo_output/` 一致，三張 md 表逐位元組相同。新的 KD 回測 412 筆都已平倉，所以 4c 不影響。

| 項目 | 結果 |
| --- | --- |
| KD(14,3,3) 年化 Sharpe | -7.565103143673017 |
| 成本 / abs(淨損益) | 0.863481526386825 |
| traded notional | 5014735.715506879 |
| DSR hurdle_annualised | 0.6718418141111412 |
| 平原 metric_gap / plateau_best_score | 真平原 0.0 / 1.0557559467813422；假尖峰 1.9339414629589853 / 0.6423599963505668 |

另外，validate_run 修正後算出的成本占比為 86%，和 `kd_inference.md` 的 86.3% 一致；修正前印成 173%。

## 檢查與審查

- **統計測試：** `uv run pytest tests/domain/statistics/ -q`，319 passed。
- **check-fast：** 通過。
- **check-full：** 在所有審查修正都套用之後只跑了一次：exit 0，4243 passed（上一輪 4233，加上本輪新增的 10 個測試），12 deselected 為 `live_llm`，耗時 51 分鐘。執行前開了 keepalive，執行期間沒有修改任何檔案。
- **獨立審查：** 唯讀，使用新的上下文。我逐項核實其結論，處理如下：
  - benchmark docstring 和新行為矛盾：已修。
  - validate_run 遇到壞的交易紀錄會崩潰：已修，並用探針驗證改成 C2 FAIL。
  - V3 不該設上限 1：已修。
  - 4c 與引擎「只算已平倉」的勝率差異沒寫：已補進 docstring。
  - 4b 的範圍：接受，理由見上。
  - 建議拆成多個 commit：沒採納，因為使用者明確要求四項一起 commit。
- **未涵蓋：**
  - validate_run 沒有自動化測試（原本就沒有），只靠手動跑 pickle 驗證。
  - 沒有跑真實模型測試：模型看得到的 MCP 介面沒有變動。

## Commit 與分支

- `aac83b8` Merge upstream/main (3fa0852) into feat/stats-py314（上一輪）
- `9a3e331` docs: update statistics references after merging upstream（上一輪）
- `610e612` fix: close four statistics gaps found in review（本輪，四項缺口合為一個 commit）

- **push：** 已 push 到 `origin/feat/stats-py314`。
- **其他分支：** 沒有建立 PR；`feat/stats-on-latest` 沒有動。
- **本報告：** 放在 `session-notes` 分支（只有報告），已 push。
