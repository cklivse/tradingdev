# leaderboard 紀錄分不出訊號是後端模型產生的還是呼叫端提供的，`LeaderboardEntry.training_dataset_id` 可能在描述另一條序列

**已開為** [#190](https://github.com/Kuan-Lun/tradingdev/issues/190)（2026-11-07）。貼上的正文省略了下方「依據 upstream main」那一行，其餘與本檔相同。

> 依據 upstream main `741fd848039aeaa3c2cb6f2c1663359964876d1c`。

## 問題

下面兩條路徑寫出的 `LeaderboardEntry` 形狀完全一樣：

- `MLService.evaluate_prediction(model_id=..., dataset_id=..., record=True)`：後端用 `predict` 從 model artifact 算出 signal，再以相同的 `model_id`、`dataset_id` 呼叫 `evaluate_signal`。
- `MLService.evaluate_signal(signal, forward_returns, model_id=..., dataset_id=..., record=True)`：呼叫端自己提供一條序列，並報一個 `model_id`。

兩條路徑都經過 `_record_evaluation` 和 `_candidate_identity`（`src/tradingdev/app/ml_service.py`）。`_candidate_identity` 有三條路徑：

1. 沒有 `model_id`：label 用 `identity.name`，沒有名稱時用 `"ad-hoc signal (<fingerprint 前 8 碼>)"`。parameters 用呼叫端宣告的設定，`training_dataset_id` 是 `""`。
2. 有 `model_id`，但 artifact 讀不到或無效（`FileNotFoundError`、`ValueError`）：label 用 `model_id`，parameters 是 `{}`，`training_dataset_id` 是 `""`。
3. 有 `model_id`，而且 artifact 讀得到：label 用 `f"{artifact.model_name} ({artifact.framework})"`，parameters 用 `artifact.parameters`，`training_dataset_id` 用 `artifact.training_dataset_id`。

第 3 條路徑不管 signal 是誰算的。所以兩種來源的紀錄都同樣有 `model_id`、`signal_fingerprint`，`training_dataset_id` 也都來自 artifact。紀錄裡沒有任何欄位說明這條被評分的序列是誰算的。`evaluate_signal` 的 docstring 自己也寫了：

> ``model_id`` is a caller label, not proof of signal origin.

## 已經寫下來的話

`LeaderboardEntry.training_dataset_id`（`src/tradingdev/domain/ml/leaderboard.py`）的 docstring 原文如下：

> Dataset the candidate's model was fitted on; ``""`` when unknown.
>
> Recorded so a reader can compare it with ``dataset_id``, the dataset the
> evaluation ran on. Equality means the score is in-sample when the backend
> produced the signal from that artifact; under a caller-supplied signal it
> says only where the named artifact was fitted. Inequality proves nothing
> about the rows: a dataset identity also covers the requested period and the
> build-time code fingerprint, and genuinely different versions can still cover
> overlapping periods. An empty value is unknown, including on every row written
> before the binding existed; it is never reconstructed from the model, the
> metrics or the current registry.

這段已經區分了「backend produced the signal from that artifact」和「a caller-supplied signal」兩種情況，但讀者只能從文件知道有這個區分，紀錄本身看不出來。這份 issue 只是請你把這段已經寫下的區分，變成程式讀得到的欄位。

## 對統計側的後果

#62 討論的準則把 eligible 定義為「可以作為配對比較的輸入」。配對比較是 statistics 套件的 `difference_interval`（`tradingdev.domain.statistics.comparison`，拆分的第 5 包，尚未合併）。消費端要逐個候選判斷能不能放進去，就得先知道 `training_dataset_id` 描述的是不是被評分那條序列的來源。

只要候選帶著 `model_id`，現在就判斷不了：這個欄位可能描述被評分序列的訓練來源，也可能只是一個無關 artifact 的訓練來源，就算欄位有值也一樣。所以帶 `model_id` 的候選裡，目前能只憑紀錄放進配對比較的是零筆。

## 要求

例如，在 entry 上記一個 `signal_source`，值可以是 `"backend_model"` 或 `"caller"`。這只是舉例，欄位的名稱、值和放的位置由擁有者決定。

## 先例

`method_family` 已經是這個形狀。它存成 `str = ""`，docstring 是：

> Which kind of method produced the signal; ``""`` when not declared.
>
> Read it through :attr:`family`, which infers the family of older rows from
> the model ID they carry instead of guessing from today's catalog.

型別由 `MethodFamily = Literal["ml_model", "rule", "other"]` 和 `family` property 提供：

```python
    @property
    def family(self) -> MethodFamily:
        """The declared family, or the one this row's identity implies.

        Rows written before families existed read as ``ml_model`` when they
        carry a model ID. That ID is the caller's declaration of a fitted
        model, not proof that one produced the signal, so the family records
        what the row claims. Rows without an ID stay ``other``: nothing in them
        says whether a rule built them, and claiming otherwise would overstate
        their provenance.
        """
        if self.method_family:
            return cast("MethodFamily", self.method_family)
        return "ml_model" if self.model_id else "other"
```

`from_record` 讀到不在 `METHOD_FAMILIES` 裡的值時會拒絕。換句話說，這份 issue 要的是把同一個模式再用一次：存成字串，空值代表沒有宣告，再用 property 提供型別。

有一點和 `family` 不同：讀取空值時，不能像 `family` 那樣從 `model_id` 推斷。上面的 docstring 也寫了，`model_id` 正是「not proof that one produced the signal」的那個欄位。所以空值應該讀成「未宣告」。

## 不要求的事

不要求遷移既有紀錄。和 `method_family` 一樣保留 `""`，不回填；舊紀錄讀成「未宣告」即可。
