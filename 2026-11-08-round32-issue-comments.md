# 第 32 輪：#189 和 #190 的實測留言

日期：2026-11-08。只寫檔案，沒有在 GitHub 留言，沒有改程式，沒有跑測試。

留言檔：

- `2026-11-08-round32-issue-comments/comment-189.md`
- `2026-11-08-round32-issue-comments/comment-190.md`

## 核對結果

**`build_entry_id` 那一行：和你說的一致。** `main` 1ea5276 的 `src/tradingdev/app/ml_service.py` 第 650–660 行（`_record_evaluation` 裡），第 656 行是：

```python
                signal_fingerprint="" if (model_id or identity.name) else fingerprint,
```

上方的註解（第 654–655 行）：

```python
                # Named methods use family/name/settings; anonymous signals
                # need the fingerprint to distinguish candidates.
```

另外確認了 `build_entry_id`（`src/tradingdev/domain/ml/leaderboard.py`）：有 `model_id` 時走第 378 行 `payload = "|".join((model_id, dataset_id, context.key, signal_fingerprint))`；docstring 第 355 行寫「Repeated evaluation replaces that row without inflating candidate count.」。兩處都引進了 #190 的留言。

**DSR 門檻：你的數字全部成立。** 我用兩種方式驗算：

- 公式直接算。
- 在 `stats/4-sharpe`（#209）的 worktree 呼叫 `deflated_sharpe_ratio`，取 `hurdle_annualised`。輸入是第 31 輪輸出裡印到小數第四位的試驗 Sharpe；門檻和 returns 無關。

```text
narrow: N=2  sigma=0.456579 E[max]=0.519755 hurdle formula=0.237309 hurdle fn=0.237309 best trial=-12.7992
wide:   N=24 sigma=4.329117 E[max]=1.979773 hurdle formula=8.570670 hurdle fn=8.570670 best trial=0.0804
ratio fn=36.1160
gamma 0.5772156649015329
```

`deflated_sharpe_ratio` 的 σ 是 `ddof=1`，年化門檻是 σ_SR × E[max_N]，和你給的公式一致。

## 和你的指示不同的地方

1. **#189 第 4 點改了說法。** 你寫的是「σ_SR = 4.3291 本身就是訊號，表示勝出那組大概是雜訊」。這句不能直接寫：參數真的影響結果時，試驗 Sharpe 一樣會很分散，所以離散度大不單獨證明勝出那組是運氣。離散度的作用是決定門檻的高度。所以留言改成三點：
   - 門檻主要由 σ_SR 決定（N 從 2 到 24，E[max_N] 是 3.81 倍；σ_SR 是 9.48 倍）。
   - `wide` 選中的那組訓練期 Sharpe 0.0804，遠低於門檻 8.571，這個比較要讀得到 σ_SR 才做得出來。
   - 明寫這裡的 K 線是隨機漫步，本來就沒有規律，所以這是示範機制。

   結論仍是你要的「離散度本身有診斷價值，要的不只是計數器」。
2. **#189 加了一句獨立性的限制。** 公式假設 N 個試驗獨立，網格試驗彼此相關，門檻誤差方向未知（`deflated_sharpe_ratio` docstring 的 Limitation）。我補了一句：兩個 run 用同樣的公式，比較仍然有意義。這是新補的限制，不是重複 issue 正文。
3. **#189 提到 #209**，作為驗算用的 `deflated_sharpe_ratio` 所在的 PR。這不是 #189 和 #190 之間的依賴。不要的話，改成「statistics 拆分第 4 包」即可。
4. **兩則都附了重現指令**（`PYTHONPATH=. .venv/bin/python repro_*.py`），並註明不需要映像。#189 另外註明 `conditions` 的 timeframe 和期間是 fixture 的值。

連結：

- 腳本和輸出指向 session-notes commit 7b66c0c（`https://github.com/cklivse/tradingdev/blob/7b66c0c839a2cf8b6c33da888811344b3c57f271/evidence/2026-11-08-round31-issue-repro/...`）。
- 程式碼行號指向上游 commit 1ea5276（`https://github.com/Kuan-Lun/tradingdev/blob/1ea5276ba088bac5795da6614b9668f08a2f88cd/...`）。
- 都測過，回應 200。

## #189 留言全文

````markdown
## 實測結果（`main` 1ea5276）

在 `main` 1ea5276 上重現了。從本 issue 依據的 741fd84 到 1ea5276，`src/` 沒有改動。

### 重現方式

- 資料：60 天合成小時 K 線，前 30 天訓練、後 30 天測試。
- 策略：內建 `kd_crossover`，在程序內執行。
- 用 worker 自己的 `optimization._run_single_combo` 跑兩次網格，各選訓練期 Sharpe 最高的一組在測試期重跑：
  - `narrow`：`k_period` ∈ {9, 14}，共 2 組
  - `wide`：`k_period` 8 個值 × `d_period` 3 個值，共 24 組
- 用 worker 自己的 `_performance_artifacts` 產生 bundle，存進真實的 workspace storage。
- 最後交給 `RankingService.rank_run_scopes("run.sharpe_ratio", [("narrow", None), ("wide", None)])`，scope 是預設的 `test`。

結果：搜尋 24 組的 `wide` 排第 1（測試期 Sharpe −8.222），搜尋 2 組的 `narrow` 排第 2（−16.207）。

### 排名結果裡沒有的

每個候選只帶 `rank`、`tied`、`value`、`run_id`、`scope`、`strategy_id`、`revision_id`、`parameters`、`metadata`、`conditions`、`metric_source`。沒有搜尋了幾組，也沒有各組的指標。

這兩樣都在同一個 run 的 bundle 裡：

| run | `trial/{i}/train` scope | `selected_train_scope` | 試驗 Sharpe 的標準差 σ_SR（`ddof=1`） |
| --- | ---: | --- | ---: |
| `narrow` | 2 | `trial/0/train` | 0.4566 |
| `wide` | 24 | `trial/17/train` | 4.3291 |

每個 `trial/{i}/train` scope 都存了 `sharpe_ratio`。

### 把門檻算出來

DSR 的門檻是：

```text
SR*_0 = σ_SR × E[max_N]
E[max_N] = (1 − γ) Φ⁻¹(1 − 1/N) + γ Φ⁻¹(1 − 1/(N e))
```

γ 是 Euler–Mascheroni 常數（0.5772156649…），σ_SR 是試驗年化 Sharpe 的樣本標準差。

| 搜尋組數 N | σ_SR | E[max_N] | DSR 門檻 SR*_0（年化） |
| ---: | ---: | ---: | ---: |
| 2 | 0.4566 | 0.520 | 0.237 |
| 24 | 4.3291 | 1.980 | 8.571 |

兩個門檻差 36.1 倍。排第 1 的 `wide` 要越過的門檻是 `narrow` 的 36 倍，而排名結果裡這兩個數字都沒有。

驗算方式：上表用公式直接算，並另外用 statistics 拆分第 4 包（#209）的 `deflated_sharpe_ratio`，對同一組試驗 Sharpe 取 `hurdle_annualised`。兩者到小數第六位一致（0.237309、8.570670）。

公式假設 N 個試驗互相獨立。網格試驗彼此相關，所以這兩個門檻的誤差方向未知（`deflated_sharpe_ratio` docstring 的 Limitation 一段）。但兩個 run 用同樣的公式，兩者的比較仍然有意義。

### 離散度本身就是要讀的資訊

門檻高低主要由 σ_SR 決定，不只由 N 決定：N 從 2 到 24，E[max_N] 只變成 3.8 倍；σ_SR 從 0.4566 到 4.3291，是 9.5 倍。

`wide` 選中的那組（`trial/17/train`）訓練期 Sharpe 是 0.0804，比它的門檻 8.571 低得多。這個比較只有讀得到 σ_SR 才做得出來。所以需要帶上的不只是組數，試驗指標的離散度本身也有診斷價值。

這裡的 K 線是隨機漫步（常態步長），本來就沒有可交易的規律，所以這個例子示範的是機制，不是某個真實策略的結論。σ_SR 大也不單獨證明勝出那組是運氣：參數確實影響結果時，σ_SR 一樣會大。它的作用是把門檻放在對的高度。

### 這次沒有驗到的

24 組全部成功，沒有指標為 `None` 的試驗。所以本 issue 裡「`n_trials` 要包含失敗的組」那一點，這次沒有驗到。

### 重現腳本和輸出

- 腳本：[`repro_189.py`](https://github.com/cklivse/tradingdev/blob/7b66c0c839a2cf8b6c33da888811344b3c57f271/evidence/2026-11-08-round31-issue-repro/repro_189.py)
- 輸出：[`repro_189.out`](https://github.com/cklivse/tradingdev/blob/7b66c0c839a2cf8b6c33da888811344b3c57f271/evidence/2026-11-08-round31-issue-repro/repro_189.out)

在 repo 根目錄、`uv sync --locked --all-extras` 之後執行 `PYTHONPATH=. .venv/bin/python repro_189.py`。不需要 strategy-runtime 映像。腳本沿用 `tests/app/test_run_ranking.py` 的 `_manifest()`，所以輸出裡 `conditions` 的 `timeframe` 和期間是 fixture 的值，和本 issue 無關。
````

## #190 留言全文

````markdown
## 實測結果（`main` 1ea5276）

在 `main` 1ea5276 上重現了。從本 issue 依據的 741fd84 到 1ea5276，`src/` 沒有改動。

### 先說範圍：比本 issue 讀起來小

透過 MCP 走不到「呼叫端自己給序列＋報 `model_id`」這條路：

- `src/tradingdev/mcp/tools/ml.py` 帶 `model_id` 時呼叫 `evaluate_prediction`（[第 116 行](https://github.com/Kuan-Lun/tradingdev/blob/1ea5276ba088bac5795da6614b9668f08a2f88cd/src/tradingdev/mcp/tools/ml.py#L116)），由後端從 model artifact 算訊號；否則呼叫 `evaluate_rule`（[第 124 行](https://github.com/Kuan-Lun/tradingdev/blob/1ea5276ba088bac5795da6614b9668f08a2f88cd/src/tradingdev/mcp/tools/ml.py#L124)）。
- 沒有任何 MCP 工具會把呼叫端的陣列連同 `model_id` 交給 `evaluate_signal`。
- `docs/ml_research.md` 也寫明：

  > The MCP path verifies which saved model produced the signal; it does not prove
  > a held-out evaluation. Python array callers and existing records may use a
  > caller-declared `model_id` label.

所以下面的 B 這種紀錄，只會來自直接呼叫 Python API `MLService.evaluate_signal` 的程式，或是既有的舊紀錄。問題存在，但目前不是對外可達的路徑。

### 重現

- 600 根合成小時 K 線，建一個資料集（2024-01-01..2024-01-12，`technical`），訓練一個 `xgboost_direction` 模型。
- **A**：`evaluate_prediction(model_id=..., dataset_id=..., record=True)`，訊號由後端用模型算。寫完先把這筆紀錄存成快照。
- **B**：`evaluate_signal(隨機序列, 資料集的 forward_return, model_id=同一個, dataset_id=同一個, record=True)`。隨機序列和模型無關。

逐欄位比較 A 的快照和 B 寫入後的紀錄：

| 欄位 | A 和 B |
| --- | --- |
| `context`、`dataset_id`、`entry_id`、`method_family`、`method_name`、`model_id`、`n_observations`、`parameters` | 相同 |
| `label` | 相同：`xgboost_direction (xgboost)` |
| `training_dataset_id` | 相同，而且等於 `dataset_id` |
| `signal_fingerprint` | 不同 |
| `metrics` | 不同 |

兩筆的欄位集合完全相同。不同的只有 `signal_fingerprint` 和 `metrics`，而這兩個描述的是序列的內容，不是來源。隨機序列那筆也拿到了模型的名稱、參數和訓練資料集。

### 覆蓋，以及它的機制

A 和 B 的 `entry_id` 相同（`a55da38aea2f299b`），B 回傳 `replaced: true`。寫完 B 之後 leaderboard 只剩一筆：

| | A（後端模型） | 寫入 B 之後留下的那筆 |
| --- | ---: | ---: |
| `ic_mean` | 0.3967 | −0.0702 |
| `rank_ic_mean` | 0.3008 | −0.0712 |
| `label` | `xgboost_direction (xgboost)` | `xgboost_direction (xgboost)` |
| `training_dataset_id` | `ds_fa575b4d7a2fef68` | `ds_fa575b4d7a2fef68` |

機制在 entry ID 的組成。`_record_evaluation`（[`src/tradingdev/app/ml_service.py` 第 650–660 行](https://github.com/Kuan-Lun/tradingdev/blob/1ea5276ba088bac5795da6614b9668f08a2f88cd/src/tradingdev/app/ml_service.py#L650-L660)）：

```python
            entry_id=build_entry_id(
                model_id=model_id or "",
                dataset_id=dataset_id,
                context=context,
                # Named methods use family/name/settings; anonymous signals
                # need the fingerprint to distinguish candidates.
                signal_fingerprint="" if (model_id or identity.name) else fingerprint,
                method_name=identity.name,
                method_family=identity.family,
                method_parameters=identity.parameters,
            ),
```

有 `model_id` 時，訊號指紋傳進去的是 `""`，不參與候選識別。`build_entry_id` 在這種情況用 `"|".join((model_id, dataset_id, context.key, signal_fingerprint))`（[`src/tradingdev/domain/ml/leaderboard.py` 第 378 行](https://github.com/Kuan-Lun/tradingdev/blob/1ea5276ba088bac5795da6614b9668f08a2f88cd/src/tradingdev/domain/ml/leaderboard.py#L378)）。所以同一個 `model_id`、同一個資料集和量測情境下，兩條不同的序列會得到同一個 `entry_id`。

覆蓋本身是寫明的設計。`build_entry_id` 的 docstring（[第 355 行](https://github.com/Kuan-Lun/tradingdev/blob/1ea5276ba088bac5795da6614b9668f08a2f88cd/src/tradingdev/domain/ml/leaderboard.py#L355)）寫：

> Repeated evaluation replaces that row without inflating candidate count.

所以覆蓋不是意外，而是識別方式的直接結果。問題在覆蓋之後：留下的那筆分不出訊號是誰算的。

這比本 issue 原本的說法更進一步。原本是「兩種來源的紀錄分不出來」；實測顯示的是：後來由呼叫端寫入的序列，會取代那個模型自己的評估，並繼承它的名稱、參數和訓練資料集。而且留下那筆的 `training_dataset_id` 等於 `dataset_id`。照 `LeaderboardEntry.training_dataset_id` 的 docstring，這在後端產生訊號時表示樣本內評估；但這筆的訊號不是後端產生的，紀錄本身看不出來。

### 重現腳本和輸出

- 腳本：[`repro_190.py`](https://github.com/cklivse/tradingdev/blob/7b66c0c839a2cf8b6c33da888811344b3c57f271/evidence/2026-11-08-round31-issue-repro/repro_190.py)
- 輸出：[`repro_190.out`](https://github.com/cklivse/tradingdev/blob/7b66c0c839a2cf8b6c33da888811344b3c57f271/evidence/2026-11-08-round31-issue-repro/repro_190.out)

在 repo 根目錄、`uv sync --locked --all-extras` 之後執行 `PYTHONPATH=. .venv/bin/python repro_190.py`。不需要 strategy-runtime 映像。
````
