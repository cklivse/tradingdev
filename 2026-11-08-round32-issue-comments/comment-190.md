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
