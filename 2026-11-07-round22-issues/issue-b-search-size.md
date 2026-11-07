# 跨策略排名的代表結果沒有帶上搜尋規模，`deflated_sharpe_ratio` 因此無法修正選擇偏誤

> 已開為 [#189](https://github.com/Kuan-Lun/tradingdev/issues/189)（2026-11-07）。貼上的正文省略了下方「依據 upstream main」那一行，其餘與本檔相同。

> 依據 upstream main `741fd848039aeaa3c2cb6f2c1663359964876d1c`。`deflated_sharpe_ratio` 在 statistics 套件拆分的第 4 包（`tradingdev.domain.statistics.sharpe`），尚未合併。

## 背景

已確認的排名範圍涵蓋完整策略表現，例如 `run.sharpe_ratio`、`run.max_drawdown`。跨策略排名時，每個策略只派出一組代表參數和它的回測結果：

- `RankingService.rank_run_scopes`（`src/tradingdev/app/ranking_service.py`）把每個 `(run_id, scope)` 當成一個候選；scope 為 null 時用該 run 的預設 scope。
- optimization run 的預設 scope 是 `test`。它是 `_run_optimization`（`src/tradingdev/mcp/workers/optimization.py`）用 `best_result` 從所有 combo 中選出的那組參數，在測試期間的結果。

## 問題

`deflated_sharpe_ratio` 需要兩個輸入：試驗的個數 `n_trials`，以及那些試驗的 Sharpe（`annualised_trial_sharpes`）。它的 docstring 寫明了門檻：

```text
SR*_0 = std(SR_n) * ((1 - gamma) * Z^-1(1 - 1/N)
+ gamma * Z^-1(1 - 1/(N * e)))
```

門檻是試驗 Sharpe 的標準差 `std(SR_n)`，乘上 N 個無技能試驗的期望最大值。離散度是線性乘進去的，所以只有個數不夠，兩個都要有。

跨策略排名只留下勝出的那一組，這兩個數字都不見了。排名核心已經記錄了排名這一層的選擇壓力，`RankingResult.ranked_total`（`src/tradingdev/domain/ranking.py`）的 docstring 寫道：

> ``ranked_total`` counts the candidates that had a usable value before
> ``top_k`` limited the returned slice, so a caller can still describe the
> selection pressure behind a short page.

但每個候選背後那一層搜尋沒有被記錄。`RunCandidate`（`src/tradingdev/domain/run_candidates.py`）的欄位是 `run_id`、`scope`、`strategy_id`、`revision_id`、`parameters`、`metadata`、`conditions`、`metric_source`，沒有一個描述這組參數是從多少組裡選出來的。

## 資料本來就存在，只是排名沒有去讀

這份 issue 不是要新增資料，而是請排名把已經存在的資料帶過來。

- `_performance_artifacts`（`src/tradingdev/mcp/workers/optimization.py`）把每個 combo 存成一個 `trial/{index}/train` scope。scope 由 `scope_from_backtest` 建立，帶有該試驗的指標值和 `equity_curve`、`returns`。選中的那一組以 `selected_train_scope=f"trial/{selected_index}/train"` 標出。
- `_verify_optimization`（`src/tradingdev/domain/research_scope.py`）用 `combos = parameter_grid(search.param_ranges)` 和 `expected_ids = [f"trial/{index}/train" for index in range(len(combos))] + ["test"]` 驗證完整網格都在 bundle 裡。

所以對 optimization run 來說，試驗個數和每個試驗的指標都在同一個 run 的 performance bundle 裡，算得出來。

## 後果

掃過 500 組參數的策略，光靠選擇的運氣就會贏過掃過 5 組的策略。`deflated_sharpe_ratio` 修不了這個偏誤：修正需要的兩個數字，在選代表結果那一步就被丟掉了。

## 要求

選代表結果的那一步，和選中的結果一起持久化搜尋的規模：

- **評估過的組態數**，包含失敗或被過濾掉的組態，因為它們仍然是試過的試驗。
- **那些試驗的指標值**，或至少它們的標準差。

欄位怎麼命名、放在 `RunCandidate`、`metadata` 還是排名結果裡，由擁有者決定。

**`n_trials` 要用 `len(combos)`**，也就是 `expected_ids` 去掉 `"test"` 之後的個數，不要用有可用指標值的 scope 數。在 optimization run 裡，失敗的 combo 也有自己的 `trial/{index}/train` scope（`_verify_optimization` 要求網格完整），只是它的指標值是 `None`。只數有值的 scope 會低估 N。`deflated_sharpe_ratio` 的 docstring 寫明了這一點：

> ``n_trials`` must be the total number of trials searched, including
> failed trials that were dropped because their metric was undefined.

plateau 分析的 `trials_from_metrics` 回傳 `dropped_count`，就是為了這個用途。

**這個要求的限制**：記下搜尋規模，只是讓選擇的幅度可以稽核。它不建立 holdout，也不證明代表結果是樣本外的。它也只涵蓋單一 optimization run 內的搜尋；使用者跨多個 run 手動嘗試的參數，不在這個範圍內。

## 時機

排名核心（`Candidate`、`rank_candidates`）和 run 候選（`RunCandidate`、`build_run_candidate`）已經在 main 上。目前在 `src` 裡用到 `RunCandidate` 的只有 `src/tradingdev/app/ranking_service.py`，所以現在加，要改的地方比較少。
