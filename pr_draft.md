# feat: add domain statistics for strategy inference, with the branch synced to Python 3.14 / pandas 3

**分支：** 這個 PR 的來源分支是 `feat/stats-py314`。`feat/stats-on-latest` 停在 `814b05a`，是同步到 Python 3.14 / pandas 3 之前保留的退路，不要拿它開 PR。合併基準是 upstream `main` 的 `3fa0852`，PR 差異只含本分支自己的檔案：統計模組與測試、demo 腳本與產出、`docs/statistics_leaderboard_integration.md`、`tests/mcp/test_optimization_failed_trials.py`、`scripts/validate_run.py`，以及 `pyproject.toml`／`uv.lock` 中的 `arch`。

## 這個分支做了什麼

新增 `src/tradingdev/domain/statistics/`，只吃呼叫端給的權益曲線、時間戳、交易紀錄或報酬序列，不讀 run、artifact 或快取，也不參考引擎自己的 `metrics`，因此可以拿來交叉檢查引擎回報的數字。

- **periods**：權益曲線在 UTC 日／月邊界上的收盤權益、損益與報酬是多少？沒有資料的期間直接省略、不補零，所以各期損益加總一定等於整段損益。
- **performance**：只看原始輸出，這次執行的報酬、波動、回撤與勝率是多少？用來檢查引擎自己報的數字對不對。
- **breakeven**：在現有的盈虧比下，勝率要多少才能打平？實際勝率離那條線有多遠？成交名目（進場加出場兩腿）與周轉率又是多少？
- **sharpe**：日報酬的年化 Sharpe 有多可信？stationary bootstrap 給信賴區間；PSR 給「真實 Sharpe > 0」的機率；DSR 修正 N 次試驗挑最好那個造成的選擇偏誤。
- **comparison**：同一段資料上的兩個策略差異是否顯著？做法是對齊時間軸後用同一組 block 索引做 paired bootstrap，保留兩者報酬的共變異。
- **plateau**：最佳參數是站在一片表現都不錯的平原上，還是網格裡孤立的尖峰？鄰域以網格索引的 Chebyshev 距離定義。
- **benchmark**：策略和買進持有比較起來如何？Sharpe 差異交給 comparison；這裡回答策略和標的怎麼共動（beta 是平均淨曝險，不是 CAPM 的系統風險）。

另外：`arch>=8.0.0`（stationary bootstrap 與 Politis–White 最適 block 長度），以及 `scripts/demo_statistics.py`、`scripts/demo_plateau.py`、`scripts/validate_run.py` 和已提交的 `demo_output/`。

### 審查後修正的四個缺口（`610e612`）

- **`scripts/validate_run.py`**
  - V3 原本斷言 `max_drawdown <= 0`，但 catalog 定義它是非負的幅度，所以對目前引擎的每一份結果都判 FAIL、exit 1。現在改照 catalog 的定義只檢查 `>= 0`。
  - 成本原本用 `2 × total_volume`，但 `total_volume` 已含進出場兩腿，出場那一腿被重複計算：KD 的成本占比印成 173%，正確是 86.3%。現在和 demo 一樣，從 breakeven 的 traded notional 推導。
- **`align_returns`**：naive 和 tz-aware 的索引混用時，原本會靜默得到 overlap 0，下游只看到「觀測數不足」，看不出真正原因是時區不一致。現在明確 raise，訊息指出是時區不一致、不是期間不重疊。五個呼叫端都經過這裡，包括 `compare_to_benchmark`。
- **breakeven 的未平倉 trade**：原本會用最後的標記價補上一條沒發生的出場腿，高估成交名目與周轉率。測試案例中 breakeven 算出 3,990，引擎的 `total_volume` 是 3,010。行為選擇見下段。
- **demo 的 fee 說明**：原本無條件寫「trade 的 `fee = 0`」，這只對舊引擎成立；目前引擎的 trade 會記錄手續費。現在依實際值決定：fee 總和為 0 時保留原句，否則寫出實際的手續費總額，並說明 slippage 已併入成交價。

### breakeven 對未平倉 trade 的行為：納入，但只算進場腿

`status == "open"` 的 trade 仍然計入，但成交名目只算進場那一腿。理由已寫在模組 docstring：

- 進場確實成交、也付了成本。整筆排除會低估周轉率和成本；引擎的 `total_volume` 也只計已成交的單。
- 它的 `exit_price` 是最後的標記價，不是成交價，所以不能算出場腿。
- 它的 `net_pnl` 是按市價計算的，已經反映在權益曲線裡，所以仍算勝或敗。這樣才能維持「交易淨損益總和 = 整段損益」，以及「edge 為正若且唯若總損益為正」這條恆等式。

**和引擎勝率的差異是刻意的，不是 bug：** 引擎的 `total_trades` 和 `win_rate` 只算已平倉的交易，所以期末有未平倉時，breakeven 的交易筆數與勝率會和引擎指標不同。docstring 已寫明這點。

另外，沒有 `status` 的舊格式紀錄視為已平倉，其他 status 值一律 raise。

### 同步到 Python 3.14 / pandas 3

本分支已 merge upstream `main`（3fa0852），在 Python 3.14.2、pandas 3.0.6、numpy 2.5.4、vectorbt 1.2.0、arch 8.0.0 下驗證。upstream 移除了 `request_execution_confirmation` 與原生 MCP elicitation，改成 `submit_execution_decision`，所以本分支原本修改確認表單的 commit（be952d9）在 merge 時被 upstream 版本取代，PR 差異中已不含該變更。

merge commit 除了解衝突，還包含為了讓合併結果通過檢查而做的修改：

- `periods.to_utc_index` 一律回傳 ns 索引。這是行為變更：pandas 3 會保留輸入的時間解析度。
- benchmark 的 beta／alpha 測試改為對照 `quantstats.stats.greeks`，因為 upstream 移除了 empyrical。
- `tests/integration/mcp_harness.py` 還原成 upstream 版本。

各項細節寫在 merge commit 的訊息裡。

## 已驗證的數字

以下五項都在 pandas 3.0.6 + numpy 2.5.4 下重新計算到全精度，和 pandas 2 時提交的 `demo_output/` 比對。`610e612` 的四項修正之後又重跑一次，結果完全相同。

KD(14,3,3) 的數字分兩條路驗證：

- 用原本提交時的同一個快取 pickle（`cd03bf19459b48af.pkl`）重算統計。
- 在 pandas 3 下用 `BacktestService` 重新回測。

兩條路的全精度結果完全相同；三張重新產生的 markdown 表格（`kd_inference.md`、`plateau_table.md`、`plateau_gridindex_table.md`）和已提交版本逐位元組相同。重新回測的 412 筆交易都已平倉，所以未平倉 trade 的修正不影響這些數字。

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

`scripts/validate_run.py` 修正後對目前引擎的 KD 結果 24 項全部 PASS，算出的成本占比為 86%，和上表一致。

檢查（以 `610e612` 為準）：

- `scripts/check-fast.sh` 通過。
- `scripts/check-full.sh` 通過：4243 passed，12 deselected 為 `live_llm`，約 50 分鐘。
- `pytest tests/domain/statistics/` 319 passed。

merge 時另外用 `-W error::FutureWarning -W error::DeprecationWarning` 跑過統計測試，全部通過。

## plateau 契約已在真實資料上驗證

`1b51608`（fix: keep failed slices on the plateau grid axes）讓 plateau 的網格軸取自所有被搜尋的參數列，包括失敗的。這樣某個參數值的試驗全部失敗時，它不會從軸上消失。這個行為原本只在合成資料上測過；這次在真實系統上走完一次完整流程。

**做了什麼：**

- 真實的 KD 只做多參數搜尋：BTC/USDT 1h，2024 上半年訓練、下半年測試，overbought 固定為 100，所以不會做空。
- 格點是 k_period ∈ {9, 14, 21, 28, 35} × oversold ∈ {20, 10, 0}，共 15 組。oversold=0 的 5 組是刻意製造的失敗切片：%K 不會低於 0，所以零交易、Sharpe 未定義。
- 走完整的 MCP 流程：`prepare_optimization`，使用者讀過 HTML 確認單並在對話中明確同意後送出 `submit_execution_decision(decision="approve")`，再用 `get_job_status` 與 `get_run_metrics(scope="trial/{i}/train")` 讀回 15 個 trial scope。
- 計畫／run ID 為 `f245f73b6ebb4c4b9c06b2ee08457339`。

**結果：**

- 失敗的 5 組在 `available_scopes` 裡都有完整紀錄：`success: true`，`trial_index` 和 `parameters` 都在。
- 33 個指標欄位和成功的 trial 完全相同（逐一比對），算不出來的 8 個是 `None`：`sharpe_ratio`、`sortino_ratio`、`calmar_ratio`、`win_rate`、`profit_factor`、`trade_expectancy`、`avg_holding_bars`、`total_slippage`（成功的 trial 這個也是 None）。原因碼寫在 `metadata.unavailable`。
- 把 15 個 scope 的 `parameters` 和 `sharpe_ratio` 餵進 `trials_from_metrics(direction="maximize")`：`dropped_count=5`，並發出 `DroppedTrialsWarning`。軸上仍保留 `oversold=(0, 10, 20)`，那 5 格變成缺失格點，而不是從軸上消失。
- `plateau_summary` 也照預期反映缺失格點：最佳組合 (9, 10) 位於角落，本來有 5 個鄰居，其中 2 個是缺失格點，所以 `best_neighborhood_size=3`。

所以 `1b51608` 修的行為在真實系統上成立，不只是合成資料上的推論。

## 順帶發現、但屬於別人範圍的事

### preflight 只取每個範圍的第一個值試跑

`src/tradingdev/adapters/execution/preflight_worker.py:232-293`：

- 第 232-234 行只取每個參數範圍的第一個值，在一小段訓練樣本上試跑這一組。
- 第 284-290 行：如果這一組算不出目標指標，就 raise `unrankable_sample_objective`，整個計畫被擋掉，連 plan 都不會建立。

實際影響：用升冪寫範圍是最自然的寫法（例如 oversold 從 0 開始），而邊界值常常就是不會產生交易的那個，所以最自然的寫法恰好會被擋。這次的搜尋就是這樣：原本照 `oversold=[10, 20, 0]` 送出時被擋下，改成 `[20, 10, 0]` 才通過，格點完全相同。

建議：在錯誤訊息裡提示「試跑只取每個範圍的第一個值」，讓使用者知道調整順序就能通過。

### 判斷零交易不能看 Sharpe 的 unavailable 原因碼

零交易的 trial 在 `metadata.unavailable` 裡，Sharpe、Sortino、Calmar 的原因碼都是 `zero_denominator`，因為權益曲線平坦。只有勝率、獲利因子、期望值和平均持有 K 棒數才是 `no_trades`。證據在 `src/tradingdev/domain/backtest/metrics.py`：

- 第 201-208 行：沒有已平倉交易時，只把 `win_rate`、`profit_factor`、`trade_expectancy`、`avg_holding_bars` 標成 `no_trades`。
- 第 236-240 行：非有限值（包括平坦權益的 Sharpe）一律標成 `zero_denominator`。
- 第 355-356 行（Calmar）與第 382-386 行（Sortino）同樣標成 `zero_denominator`。

所以判斷零交易要看 `total_trades == 0`。權益平坦但有交易的情況，Sharpe 的原因碼也會一樣，光看原因碼分不出來。任何消費 scope 的人都會踩到這個，值得寫進文件。

### 試驗回測逾時會讓整個 job 結束

`src/tradingdev/mcp/workers/optimization.py`：

- 第 334 行先設 `trial_result = None`。
- 試驗回測（第一組 combo）逾時的話，第 352–365 行的 `except _TrialTimeoutError` 會把 job 標成 `estimation_timeout` 後直接 `return`；其他例外由第 366–370 行 `_fail()` 後 `return`。
- 因此第 413 行的 `if trial_result is not None` 實際上走不到 `None` 分支。

結果是整個 job 沒有任何結果，不會只少一組參數。值得處理的地方有兩個：

- 一支策略只要第一組參數慢，整個最佳化就做不了。
- 第 413 行的防禦式判斷容易讓人誤以為存在「少一列」的路徑。

### 單一 combo 拋例外會讓整個 job 失敗

同一檔案：

- 第 106–146 行的 `_evaluate_combo` 和它呼叫的 `_run_single_combo` 都沒有 try/except。
- 只要 joblib 任何一個 worker 拋例外，`Parallel(...)` 就會整批重拋，被第 440–442 行的 `except Exception` 接住後呼叫 `_fail(job_id, "Optimization error at batch ...")`。
- 已完成批次的結果全部丟棄，plateau 也拿不到「這一格失敗了」的資訊。

零交易不屬於這種情況：它會回傳 metric 為 `None` 的 `ComboEvaluation`，由 `tests/mcp/test_optimization_failed_trials.py` 的 `test_zero_trade_combo_returns_an_undefined_objective` 與 `test_parallel_transport_also_returns_the_zero_trade_combo` 釘住（序列與 joblib 兩條路徑）。上面的真實搜尋也印證了這一點。

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

- **統計模組目前沒有任何對外出口：** 沒有 MCP 工具或 CLI 指令呼叫它們。要不要變成 `provider="statistics"` 的 catalog 指標還沒有決議。這是最需要團隊回應的一項。
- **引擎或策略在執行中拋例外的路徑沒有驗證過。**
- **`trials_from_metrics` 只擋得住「指標未定義」，擋不住「指標算得出來但樣本太少」。**
  - 上面那次搜尋裡，最佳組合 (9, 10) 只有 2 筆交易。它的 Sharpe 算得出來，所以不會被丟掉，就這樣成了 `best_params`。但 2 筆交易的 Sharpe 沒有統計意義：它排第一只是因為交易少、虧得少。
  - 可能的做法：加一個最小觀測數門檻，低於門檻當成失敗處理，但軸照樣保留，和 `min_neighborhood` 同一個設計模式。
  - 這項留作後續，不在這個 PR 裡做。
- **KD 那幾個數字沒有測試把關：** -7.57、86.3%、5,014,735.72 只存在於 `demo_output/`。資料與快取 pickle 不進 Git，所以 check-full 偵測不到它們的變化。會受 pandas 影響的切期邏輯由 periods 的手算測試涵蓋；DSR hurdle 與平原的數字則由單元測試以 rel 1e-6 固定。
- **demo 的輸入依 mtime 挑選：** `latest_cache()` 選最新的 pickle，重跑時不一定讀到 `kd_inference.md` 所引用的那一個。
- **`scripts/validate_run.py` 沒有自動化測試：** 它的修正只靠手動對兩份 pickle 實跑驗證。

🤖 Generated with [Claude Code](https://claude.com/claude-code)
