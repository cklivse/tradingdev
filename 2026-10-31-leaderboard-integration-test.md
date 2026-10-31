# 2026-10-31 排行榜曲面 × 統計模組 接合實測

對象：Kuan-Lun/tradingdev PR #60（feat(ml): make the leaderboard reproducible and
surface-ready），回覆他提出的三個問題。本輪沒有碰 PR #38，沒有 merge，沒有同步
upstream，也沒有改 `docs/statistics_leaderboard_integration.md`。

## 0. 測試版本與環境

- PR #60 已於 2026-10-28 合併進 upstream main（merge commit a858168），
  `feat/leaderboard-parameter-surface` 分支已刪，
  `git fetch upstream feat/leaderboard-parameter-surface` 會失敗。改由
  `refs/pull/60/head` 取得 PR 最終 head **12293d5**，cc1344f 是其中第一個 commit。
- 主要結果在 **12293d5**（實際合併進 main 的版本）上跑。同一腳本在 **cc1344f** 上
  也跑過一次：所有數值、接受／拒絕結果都相同，差別只有文字——cc1344f 的 skip
  理由是 `'ic_mean' was measured but is not finite`，12293d5 改成
  `'ic_mean' is unavailable or not finite`；cc1344f 少一條「cross-horizon source
  and raw-data equivalence is not verified」的 caveat。「一個 horizon 只能有一個
  dataset 版本」的檢查在 cc1344f 就已經有。
- 統計模組：feat/stats-recut **ed9de31**（含 7d59d82 的輸入驗證）。
- 環境：這個 Codespace 的 `.venv`（Python 3.14.2，有 `arch`）。他的程式從
  `sys.path` 最前面載入，我們的 `statistics` 套件掛到 `tradingdev.domain.__path__`；
  腳本會 assert 兩邊各自從哪裡 import。沒有複製檔案，也沒有安裝東西。
- 驗證腳本（丟棄式，未 commit）：Codespace scratchpad 的 `verify_leaderboard.py`，
  完整輸出在同目錄的 `verify_output.txt`。
- 資料：Task 1、2 用他的 API 直接造的 `LeaderboardEntry`，透過他的
  `LeaderboardStore.record()` 寫入，再經 `MLService.leaderboard()` 讀出——走的是
  真的 JSONL 讀寫和真的回應組裝，但指標是造的。Task 3 是端到端實跑（合成價格
  → build_dataset → train_model → predict → evaluate_signal(record=True) →
  leaderboard → 重跑 predict）。

測試格點：horizon ∈ {1, 4, 12} × window ∈ {20, 40, 60, 120}，n_quantiles = 5，共
12 個 entry。**window = 40 整排失敗**（三個 horizon 都是），每個 horizon 對應自己
的 dataset_id / data_fingerprint（因為 horizon 會重建 label）。

## A. 失敗那一排會不會留在軸上？

**會。兩邊接起來之後軸是完整的，dropped_count = 3 正確。**

存進 JSONL 的失敗列（寫入時傳的是 `float("nan")`，store 自己投影成 null）：

```
"context.window": 40, "context.horizon": 4,
"metrics": {"ic_mean": null, "ic_std": null, "icir": null},
"parameters": {"learning_rate": 0.05, "max_depth": 3, "objective": "binary"}
```

讀回後：`{'ic_mean': None, 'ic_std': None, 'icir': None}`——key 保留、值是 None。

`leaderboard('ic_mean', allow_parameter_axes=True)`：

```
n_candidates: 12, n_ranked: 9
parameter_axes: {"horizon": [1, 4, 12], "window": [20, 40, 60, 120], "n_quantiles": [5]}
skipped: (h=4,w=40) (h=12,w=40) (h=1,w=40)，reason "'ic_mean' is unavailable or not finite"
```

entries → rows → `trials_from_metrics(direction=metric_direction("ic_mean"))`：

```
n_rows: 12, n_trials: 9, dropped_count: 3
axes: {"horizon": [1.0, 4.0, 12.0], "n_quantiles": [5.0], "window": [20.0, 40.0, 60.0, 120.0]}
warnings: ["dropped 3 trial(s) with a non-finite metric"]
```

`plateau_summary(result.trials, axes=result.axes)`：

```
axis_sizes {horizon: 3, n_quantiles: 1, window: 4}
best_params {horizon: 4, window: 60}            best_metric 0.03
plateau_best_params {horizon: 1, window: 120}   plateau_best_score 0.0274375
metric_gap 0.0076875                            best_neighborhood_size 5
```

對照組：上游如果直接把失敗那排丟掉（不寫入），軸就塌了，結果也跟著變：

```
axes.window: [20.0, 60.0, 120.0]   dropped_count: 0
plateau_best_params {horizon: 1, window: 20}   metric_gap 0.0056875
best_neighborhood_size 8
```

也就是 20 和 60 被當成相鄰，最佳點的鄰域從 5 變成 8，plateau 的結論也換了。
這正是他保留 null 列要防的事，實測確認有效。

Minimize 指標也測了：`metric_direction('ic_std') = minimize`，直接當 direction
傳入，dropped_count = 3，best_params = {horizon: 12, window: 20}（ic_std 最小），
best_metric 是取負後的 -0.12。方向不用呼叫端自己翻。

**限制（要讓他知道）：**

1. `parameter_axes` 是「有記錄到的」數值，不是「搜尋過的」格點。評估在寫入之前
   就 raise 的話（例如 `evaluate_signal` 的輸入檢查沒過），那一點兩邊都看不到。
   我們的 contract 也寫明 "Rows omitted upstream cannot be recovered"。
2. 回應裡的 `skipped` 只帶 horizon/window/n_quantiles，**沒有 `parameters` 和
   `signal_fingerprint`**（`ranked` 有）。所以模型超參數如果也是曲面的軸，就沒辦法
   只從 leaderboard 回應組出失敗列的座標，必須讀 `LeaderboardStore.entries()`。
   建議 skipped 也帶 `parameters`。

## B. metrics 出現 null 之後，要當缺值跳過，還是需要 valid 旗標？

**不需要額外旗標。「key 存在、值為 None」正好就是 `trials_from_metrics` 期待的
失敗列形式。**實測三種狀態：

| 他的狀態 | 他的 `rank_entries` | 我們的 `trials_from_metrics` |
|---|---|---|
| key 存在、有限值 | 排名 | 成為 trial |
| key 存在、None（含存入前的 NaN/Inf） | skipped：`'ic_mean' is unavailable or not finite` | 從 trials 丟掉、座標留在 axes、計入 dropped_count |
| key 不存在 | skipped：`no 'ic_mean' recorded` | **raise** `ValueError: row 11 has no 'metric'` |

直接餵 None / NaN / inf 給 factory：

```
metric None: dropped_count=1 axes={'w': (1.0, 2.0)}
metric  NaN: dropped_count=1 axes={'w': (1.0, 2.0)}
metric  inf: dropped_count=1 axes={'w': (1.0, 2.0)}
metric '0.1' (str): ValueError: row 0 metric is not numeric
metric True: ValueError: row 0 metric is not numeric
```

**key 不存在會 raise，這是刻意的。**「沒記錄」和「測了但失敗」意思不同：前者表示
這一點根本不屬於這次搜尋，或者上游的記錄有漏。把它當成失敗列默默丟掉，會讓
dropped_count 多算、讓讀者以為那個座標失敗過，而 DSR 的 N 也是從同一個數算出來的。
所以 factory 寧可停下來，讓呼叫端決定。

**轉接層的唯一要求：保留 key 是否存在，不要用 `.get()`。**實測反例：

```
key absent, adapter uses .get() -> accepted silently, dropped_count = 4
  (12 surface rows: 3 failed + 1 never recorded)
```

`.get()` 把「沒記錄」壓成 None，factory 就分不出來了。回信可以這樣說：他的三態
設計我們這邊不需要旗標，但請保持「失敗就寫 null，不刪 key」。他現在的
`_record_evaluation` 對 NaN/Inf/None 都是這樣做；唯一會刪 key 的是非數值的值，
那本來就不是指標，沒問題。

## C. parameter_axes 能不能直接當 plateau 的 axes？

**可以，不需要轉換。**

```
type: dict    key order: ["horizon", "window", "n_quantiles"]
value types: 全部 int    values: 各軸遞增排序
equal to trials_from_metrics axes: {horizon: true, window: true, n_quantiles: true}
plateau_summary(axes=parameter_axes) == plateau_summary(axes=result.axes): True
```

- 型別：`dict[str, list[int]]`。我們接受任何 `Mapping[str, Iterable[real]]`，int 會
  轉成 float 比對（20 == 20.0），bool 會被拒（7d59d82）。他的值不會是 bool。
- 順序：key 順序無關，我們內部會依名稱排序；值他已經排好，而且我們本來也會自己排。
- 內容：他是對**同一批過濾後的 entries（含失敗列）**取值，跟我們從 rows 算出的
  axes 一致。

使用條件（三項都實測過）：

1. **只涵蓋 context 的三軸。**模型超參數如果也進座標，用 `parameter_axes` 當 axes
   會 raise：
   `ValueError: trial 0 parameter names differ from the axes`。
   這時要用 `trials_from_metrics` 的 `axes`，或自己把超參數軸補進去。
2. **`entry.parameters` 不能整包當座標**：裡面有非數值（`objective`），會 raise
   `row 0 parameter 'objective' is not numeric`。轉接層要明確選出被掃的數值超參數。
3. **固定不變的軸也算一個維度**：加入兩個沒變的超參數後是 5 維，
   `dimension_warning = True`
   （axis_sizes `{horizon: 3, learning_rate: 1, max_depth: 1, n_quantiles: 1, window: 4}`）。
   鄰域本身不受影響（單值軸的 rank 距離永遠是 0），但警告會誤報。建議轉接層只放
   真的有掃的軸；`n_quantiles` 只有一個值時也一樣。
4. `parameter_axes` 是在 comparability 檢查**之前**算的。用 `allow_mixed=True` 時，
   軸可能混了不同 identity 的 entries，不能拿來鋪曲面。只在
   `allow_parameter_axes=True` 且沒有 `allow_mixed` 時使用。

## 任務 2：allow_parameter_axes 的語意

### 能測的部分（已測）

- 預設（不開 allow_parameter_axes）跨 window/horizon 會被拒：
  `ValueError: entries were not measured on the same conditions (12 distinct contexts; ...`
- 開了之後 12 個 entry 一起排名：9 個 ranked、3 個 skipped（帶座標）。
  `parameter_axes = {horizon: [1, 4, 12], window: [20, 40, 60, 120], n_quantiles: [5]}`，
  正確。caveats 會講明這是曲面不是單一量測、失敗列保留了座標、
  best-of-9 的 Bonferroni 門檻（t > 2.773），以及跨 horizon 的來源等價性沒有驗證。
- 硬牆：
  - 同 horizon 4 出現第二個 dataset 版本 →
    `ValueError: horizon 4 was measured on 2 different dataset versions. ...`
  - 不同 feature_set →
    `ValueError: entries were not measured on the same instrument, dates, feature set or feature code ...`
- 只看 horizon=4 的切片：`parameter_axes = {horizon: [4], window: [20, 40, 60, 120], n_quantiles: [5]}`，
  n_ranked 3，skipped `[(4, 40)]`。失敗點在單一 horizon 的切片裡也保留著。

結論：放行三軸、其餘硬牆的語意，跟我們鋪曲面的方式相容。上面 A 和 C 都是在
這個模式下跑的。

### 不能測的部分（留給 cklivse 回答）

> **「同一個 horizon 不能混兩個 dataset 版本」會不會卡到我們的重建流程**——這是
> 作業流程問題，不是程式問題：重建資料（修正來源、延長日期）之後，舊版本的
> entries 要不要整批重記？這只有我們的流程能回答。程式行為已確認：混了就硬拒，
> 錯誤訊息建議 re-record against a single dataset_id，或每個版本分開排名。

## 任務 3：IC 配對 bootstrap 的可行性

**結論：機械上可行，已經端到端跑通。但有一個比 NaN 更根本的限制：predict
出來的是 in-sample 訊號。**

### 實跑輸出

合成 1h 價格 120 天 → `build_dataset(horizon=4)` → 兩個 `lightgbm_direction`（max_depth 2/50 棵 vs 6/200 棵）→ `predict` →
`evaluate_signal(window=60, record=True, model_id, dataset_id)` → 之後重跑 `predict`：

```
shallow: rerun fingerprint 98c9564a5edf796b == stored 98c9564a5edf796b: True
  rolling_ic: len=2841 index=RangeIndex leading NaN=59 NaN after warm-up=0
  nanmean(rolling IC)=0.8905109490 stored ic_mean=0.8905109490
deep: rerun fingerprint fc84c6171610c9fb == stored fc84c6171610c9fb: True
  rolling_ic: len=2841 index=RangeIndex leading NaN=59 NaN after warm-up=0
  nanmean(rolling IC)=0.8972560302 stored ic_mean=0.8972560302
align_returns on the raw rolling IC -> ValueError: returns 'a' must be finite
middle layer: warmup_dropped 59, invalid_dropped 0, kept_non_overlapping 47 (each)
align_returns: overlap=47 sufficient=True (min_overlap=20)
difference_interval_outcome(mean IC shallow - deep):
  difference=-0.00697, [-0.00917, -0.00504], p=0.0, block_size=2, correlation=0.718, overlap=47
for contrast, overlapping rolling IC (n=2782):
  difference=-0.00675, [-0.00847, -0.00518], p=0.0, block_size=92
```

（IC ≈ 0.89 是因為合成價格是正弦波，而且是 in-sample；這組數字只用來驗證管線，
不代表任何結論。）

已確認的事：重跑 predict 的 fingerprint 和 leaderboard 存的一致；用
`rolling_ic(method="pearson")` 重建的序列，nanmean 和存下來的 `ic_mean` 一致到小數
第 10 位，所以重建出來的就是當初評分用的那條序列。`align_returns` 確實會擋
前 window-1 個 NaN。

### 步驟

1. **找出候選**：從 `LeaderboardStore.entries()`（不是回應）取 `model_id`、
   `dataset_id`、`context.window`、`context.horizon`、`signal_fingerprint`。
   要配對的兩個候選必須在同一個 dataset 上（同一組列）。跨 horizon 是不同 dataset，
   只能靠時間戳取交集，而且 label 的區間不同，要另外判斷能不能比。
2. **重跑 `predict(model_id, dataset_id)`**，比對 `signal_fingerprint`。不一致就停，
   不要拿來比——模型或 dataset 已經變了。
3. **`rolling_ic(signal, forward_returns, window=context.window, method=...)`**，method
   對應要比的指標（ic_* 用 pearson，rank_ic_* 用 spearman）。
4. **中間那一層**（`align_returns` 之前）：
   - **貼時間標籤**：predict 不回傳索引，`rolling_ic` 給的是 RangeIndex。要用 dataset
     parquet 的 `timestamp` 欄，依存檔的列順序貼上（predict 保證是存檔的列順序）。
     不貼的話兩個模型會用 0..n-1 對齊，換成不同 dataset 就錯位。
   - **按位置去掉暖機段**：`iloc[window-1:]`，不要用全域 `dropna()`——暖機段是結構性的
     缺值，要和真正的失敗分開記。
   - **有效遮罩**：暖機段之後如果還有非有限值（例如某個窗口內的預測全是常數，相關
     係數未定義），用遮罩移除並**計數回報**，兩條序列各自記。**不填 0。**填 0 會
     捏造一個「IC 為零」的觀測，同時壓低平均和變異數（這跟他信裡的建議一致）。
     他的 `ic_statistics` 本身也是 `dropna()` 後取平均，所以移除才和存下的指標一致。
   - **去掉重疊**：rolling IC 相鄰點共用 window-1 根 K 棒，自相關極強。實測用重疊序列
     時 block_size 估到 92，比 window 還長，而且 n=2782 會讓讀者誤以為樣本很多。
     建議每 window 根取一點（`iloc[::window]`），跟他 `ic_statistics` 用
     `n_effective = bars // window` 算 t 統計量的假設一致。
   - **檢查樣本數**：取完之後至少要 20 期（`MIN_BOOTSTRAP_OBSERVATIONS`），也就是至少
     約 21 × window 根 K 棒。window=60 的 1h 資料大約要 53 天；更長的 window 要更長
     的資料，不夠的話 `difference_interval_outcome` 會回 `IntervalUnavailable`，帶原因。
5. `align_returns` / `difference_interval_outcome(a, b, np.mean)`。平均數是平滑統計量，
   jackknife 估 block 長度的前提成立。

### 根本限制：in-sample

`train_model` 的最終 artifact 是用**全部**列擬合的，`predict` 對同一個 dataset 的
輸出就是訓練資料上的預測（他的 docstring 也寫了 "prediction does not establish
out-of-sample provenance"；walk-forward 只回傳分數，不保留 out-of-fold 預測）。
我們 comparison 模組的前提是「只比較 out-of-sample 報酬」——in-sample 的配對差異
量的是哪個模型過擬合得比較徹底。實測裡 max_depth 6 / 200 棵的模型「顯著」勝出
（p = 0），正好是這個現象。

所以這條路要有意義，需要下列其中一項（要請他評估）：

- 在一個**沒參與訓練**的 dataset（往後的日期）上跑 predict。現有 API 可以做到，但
  feature 欄位必須一致，而 leaderboard entry 也要在那個 dataset 上記錄；
- 或讓 walk-forward 保存每個 fold 的 out-of-fold 預測。

fingerprint 只能證明「跟當初記錄的訊號是同一條」，不能證明那條訊號是 OOS。

## 給回信的重點

1. 失敗列保留 null 的設計，接上我們的 plateau 是正確的；軸完整、dropped_count 正確，
   而對照組證明丟掉的話結論會變。
2. 不需要 valid 旗標，「key 存在、值為 null」就是我們要的形式；請保持不刪 key。
   「key 不存在」我們刻意 raise。
3. `parameter_axes` 可以直接當 axes，條件是座標只包含這三軸（或者自己補上超參數軸）。
4. 建議：回應的 `skipped` 也帶 `parameters`（和 `signal_fingerprint`）。
5. IC 配對 bootstrap 靠重跑 predict 機械上可行（fingerprint 和 ic_mean 都對得上），
   但 predict 目前是 in-sample，要有 OOS 的預測來源才有統計意義。
6. 同 horizon 單一 dataset 版本會不會卡重建流程：由 cklivse 回答。

## 本機狀態（任務 0）

- `feat/stats-recut`：在，HEAD **ed9de31**，在 df88dd1 之上 6 個 commit：
  dc25ac9、631dde0、a674ea2（10/27 重切分），f044ab1、7d59d82、ed9de31（10/27 那一輪）。
  本輪依指示推到 origin 存檔（`origin/feat/stats-recut` = ed9de31，新分支，沒有 force）。
- 10/27 那一輪：
  - 任務 1（validate_run 移出）、2（四個型別漏洞）、3（README）已 commit。
  - 任務 4 的固定連結保留在第 178 行（指向 b74fd7e）。
  - session-notes 的 evidence commit **6e16e12** 只在本機，未 push。本報告是 commit
    在 origin/session-notes 上，沒有帶上它。
  - 任務 5 的獨立審查、check-fast/check-full、fast-forward 合併、push PR #38、本輪
    報告：**找不到跑過的紀錄**，應視為沒做。
  - 當時的 worktree 在 /tmp 底下，已經被清掉。如果當時有未 commit 的修改，已經遺失。
- 主工作樹：checkout `feat/stats-py314` @ 610e612（比 origin 落後 31），20 項未提交
  （17 項修改／暫存，3 項 untracked）。本輪沒有動它。
- upstream main = **f7a217c**。recut 和 PR #38 head（df88dd1）的合併基準都是
  **5f8d14d**（PR #40），落後 upstream main **246** 個 commit；recut 領先 47，
  df88dd1 領先 41。PR #38 目前在 GitHub 上是 33 檔 +9286/−7；recut 相對合併基準是
  22 檔 +6953/−3（比 10/27 預估的 21 檔 / +6568 多，原因還沒查）。
