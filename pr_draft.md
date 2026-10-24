# feat: add domain statistics for strategy inference on Python 3.14 / pandas 3

## 這個分支做了什麼

新增 `src/tradingdev/domain/statistics/`，只吃呼叫端給的權益曲線、時間戳、交易紀錄或報酬序列，不讀 run、artifact 或快取，也不參考引擎自己的 `metrics`，因此可以拿來交叉檢查引擎回報的數字。

- **periods**：權益曲線在 UTC 日／月邊界上的收盤權益、損益與報酬是多少？沒有資料的期間直接省略、不補零，所以各期損益加總一定等於整段損益。
- **performance**：只看原始輸出，這次執行的報酬、波動、回撤與勝率是多少？用來檢查引擎自己報的數字對不對。
- **breakeven**：在現有的盈虧比下，勝率要多少才能打平？實際勝率離那條線有多遠？成交名目（進場加出場兩腿）與周轉率又是多少？
- **sharpe**：日報酬的年化 Sharpe 有多可信？stationary bootstrap 給信賴區間；PSR 給「真實 Sharpe > 0」的機率；DSR 修正 N 次試驗挑最好那個造成的選擇偏誤。
- **comparison**：同一段資料上的兩個策略差異是否顯著？做法是對齊時間軸後用同一組 block 索引做 paired bootstrap，保留兩者報酬的共變異。
- **plateau**：最佳參數是站在一片表現都不錯的平原上，還是網格裡孤立的尖峰？鄰域以網格索引的 Chebyshev 距離定義。
- **benchmark**：策略和買進持有比較起來如何？Sharpe 差異交給 comparison；這裡回答策略和標的怎麼共動（beta 是平均淨曝險，不是 CAPM 的系統風險）。

另外：`arch>=8.0.0`（stationary bootstrap 與 Politis–White 最適 block 長度），以及 `scripts/demo_statistics.py`、`scripts/demo_plateau.py` 和已提交的 `demo_output/`。

本分支已 merge upstream `main`（3fa0852），在 Python 3.14.2、pandas 3.0.6、numpy 2.5.4、vectorbt 1.2.0、arch 8.0.0 下驗證。upstream 移除了 `request_execution_confirmation` 與原生 MCP elicitation，改成 `submit_execution_decision`，所以本分支原本修改確認表單的 commit（be952d9）在 merge 時被 upstream 版本取代，PR 差異中已不含該變更。

merge commit 除了解衝突，還包含為了讓合併結果通過檢查而做的修改：
- `periods.to_utc_index` 一律回傳 ns 索引。這是行為變更：pandas 3 會保留輸入的時間解析度。
- benchmark 的 beta／alpha 測試改為對照 `quantstats.stats.greeks`，因為 upstream 移除了 empyrical。
- `tests/integration/mcp_harness.py` 還原成 upstream 版本。

各項細節寫在 merge commit 的訊息裡。

## 已驗證的數字

以下五項都在 pandas 3.0.6 + numpy 2.5.4 下重新計算到全精度，和 pandas 2 時提交的 `demo_output/` 比對。

KD(14,3,3) 的數字分兩條路驗證：
- 用原本提交時的同一個快取 pickle（`cd03bf19459b48af.pkl`）重算統計。
- 在 pandas 3 下用 `BacktestService` 重新回測。

兩條路的全精度結果完全相同；三張重新產生的 markdown 表格（`kd_inference.md`、`plateau_table.md`、`plateau_gridindex_table.md`）和已提交版本逐位元組相同。

| 我們宣稱 | 驗證方式 | pandas 3 結果 |
| --- | --- | --- |
| KD(14,3,3)（BTC/USDT 1h，2024 全年）日報酬年化 Sharpe 為 -7.57 | `period_returns(..., "daily")` 再 `sharpe_ratio(periods_per_year=365)`，快取與重新回測各算一次 | -7.565103143673017（兩條路相同） |
| 估計成本 / abs(淨損益) 為 86.3% | traded notional × (fee 0.0006 + slippage 0.0005) ÷ abs(equity[-1] − equity[0]) | 0.863481526386825 |
| traded notional（進場加出場）為 5,014,735.72 | `summarize_breakeven(trades).traded_notional`，來源是交易紀錄，不是引擎的 `total_volume` | 5014735.715506879 |
| DSR 的 hurdle_annualised 在年化 Sharpe -6.00/-6.67/-7.57、ppy=365、n_trials=3 時為 0.6718 | `deflated_sharpe_ratio(..., annualised_trial_sharpes=[-6.00, -6.67, -7.57], periods_per_year=365, n_trials=3).hurdle_annualised`（hurdle 只取決於試驗 Sharpe 的離散程度，與報酬無關） | 0.6718418141111412 |
| 平原 demo：真平原 metric_gap 0.000、plateau_best_score 1.056；假尖峰 metric_gap 1.934、plateau_best_score 0.642 | 用兩個 demo 腳本各自的合成 5×5 網格（seed 0）呼叫 `plateau_summary` | 真平原 0.0 / 1.0557559467813422；假尖峰 1.9339414629589853 / 0.6423599963505668（兩個腳本相同） |

重新回測得到的三組 KD 年化 Sharpe 分別是：
- KD(21,5,5)：-6.004071680348325
- KD(9,3,3)：-6.6715302187876615
- KD(14,3,3)：-7.565103143673017

這正是 DSR 那一行用的三個試驗 Sharpe。

檢查：`scripts/check-fast.sh` 通過；`scripts/check-full.sh` 通過（4233 passed、12 deselected 為 `live_llm`、約 46 分鐘）；`pytest tests/domain/statistics/ -W error::FutureWarning -W error::DeprecationWarning` 309 passed。

## 順帶發現、但屬於別人範圍的事

### 試驗回測逾時會讓整個 job 結束，不會只少一列

`src/tradingdev/mcp/workers/optimization.py`：
- 第 334 行先設 `trial_result = None`。
- 試驗回測（第一組 combo）逾時的話，第 352–365 行的 `except _TrialTimeoutError` 會把 job 標成 `estimation_timeout` 後直接 `return`；其他例外由第 366–370 行 `_fail()` 後 `return`。
- 因此第 413 行的 `if trial_result is not None` 實際上走不到 `None` 分支。

結果是：逾時那組參數不是「從 plateau 的軸上消失」，而是整個 job 沒有任何結果。值得處理的地方有兩個：
- 一支策略只要第一組參數慢，整個最佳化就做不了。
- 第 413 行的防禦式判斷容易讓人誤以為存在「少一列」的路徑。

（先前的說法是「trial_result is None 時該列 combo 不進 all_results」；讀過目前程式碼後更正如上。）

### 單一 combo 拋例外會讓整個 job 失敗

同一檔案：
- 第 106–146 行的 `_evaluate_combo` 和它呼叫的 `_run_single_combo` 都沒有 try/except。
- 只要 joblib 任何一個 worker 拋例外，`Parallel(...)` 就會整批重拋，被第 440–442 行的 `except Exception` 接住後呼叫 `_fail(job_id, "Optimization error at batch ...")`。
- 已完成批次的結果全部丟棄，plateau 也拿不到「這一格失敗了」的資訊。

零交易不屬於這種情況：它會回傳 metric 為 `None` 的 `ComboEvaluation`，由 `tests/mcp/test_optimization_failed_trials.py` 的 `test_zero_trade_combo_returns_an_undefined_objective` 與 `test_parallel_transport_also_returns_the_zero_trade_combo` 釘住（序列與 joblib 兩條路徑）。

### 確認表單的 approved 勾選框（upstream 已移除）

在 merge 前的程式碼（`src/tradingdev/mcp/tools/execution.py` 的 `UserApproval.approved: bool = Field(default=False)`，以及 `accepted = answer.action == "accept" and answer.data.approved`）下，Claude Code 的 elicitation 表單無法勾選這個 boolean。按 Enter 送出的是 `approved=False`，被判為拒絕，計畫就無法核准。

upstream 3fa0852（ce8cfb8 `build!: migrate MCP integration to SDK 2`）已經移除 `request_execution_confirmation` 與原生 elicitation，改為 `submit_execution_decision(plan_id, decision)`：
- `ARCHITECTURE.md` 寫明原工具已移除。
- `docs/strategy_contract.md` 寫明原工具已移除。

這個問題在目前的 main 上已不存在。列在這裡只是說明本分支原本的 be952d9 為何不在 PR 差異中。

### Leaderboard 整合缺的兩樣東西

詳見 `docs/statistics_leaderboard_integration.md`。

- 「Missing for Plateau Analysis」：每筆 entry 的參數座標；把只差在搜尋設定的 entry 分在同一組的方法（和排名用的 `comparability_error` 分開）；失敗的候選也要留成 entry，metric 記為缺值。
- 「Missing for the Paired Bootstrap」：每個候選逐 bar 的 IC 序列（或預測值，搭配被排名訊號的 fingerprint）；這些序列共用的 bar 索引，讓 `align_returns` 能配對。

## 還沒做的事

- **`trial/{index}/train` scope 的實際內容沒有驗證過。** 寫入點在 `src/tradingdev/mcp/workers/optimization.py` 第 213 行。離線測試 `test_persisted_trial_scopes_feed_plateau_with_the_failed_slice` 只涵蓋替身資料。先前真實 MCP 執行卡在上面那個勾選框；upstream 改成 `submit_execution_decision` 之後這個阻礙已經不在，但還沒有重新跑過。
- **引擎或策略在執行中拋例外的路徑沒有驗證過。**
- **統計模組目前沒有任何對外出口：** 沒有 MCP 工具或 CLI 指令呼叫它們。要不要變成 `provider="statistics"` 的 catalog 指標還沒有決議。
- **`scripts/validate_run.py` 對目前引擎的結果會誤判失敗。**
  - 第 230 行的 V3 斷言 `max_drawdown <= 0`，但 catalog 定義它是非負的幅度（`src/tradingdev/domain/performance/catalog.py:137`）。
  - 第 240 行的 `2 * fee_rate * total_volume` 重複計算了出場一側：`total_volume` 已包含進出場兩腿，所以 KD 的成本占比印成 173%，正確是 86.3%。
- **KD 那幾個數字沒有測試把關：** -7.57、86.3%、5,014,735.72 只存在於 `demo_output/`。資料與快取 pickle 不進 Git，所以 check-full 偵測不到它們的變化。會受 pandas 影響的切期邏輯由 periods 的手算測試涵蓋；DSR hurdle 與平原的數字則由單元測試以 rel 1e-6 固定。
- **demo 成本段落寫死了「trade 的 `fee = 0`」：** 這只對舊格式的快取成立，目前引擎的 trade 會記錄 fee。另外 `latest_cache()` 依 mtime 挑選輸入，重跑時不一定讀到 `kd_inference.md` 所引用的那個 pickle。
- **`align_returns` 遇到 naive 和 tz-aware 索引混用時，會靜默得到 overlap 0：** 結果只是 `insufficient_observations`，沒有指出真正原因是時區不一致。
- **breakeven 用 `size × exit / entry` 推算出場名目：** 未平倉的 trade 會被算進一個沒有發生的出場。這種情況目前沒有測試。

🤖 Generated with [Claude Code](https://claude.com/claude-code)
