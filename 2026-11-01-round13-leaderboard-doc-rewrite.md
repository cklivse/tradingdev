# 2026-11-01 第 13 輪：排行榜整合文件重寫與 #62 驗收標準

## 結果

- commit `1d1fff6`（docs only），已 push 到 `feat/stats-py314`，fast-forward 自 `63c44a4`，沒有 force。PR #38 head 現在是 `1d1fff6`。
- check-fast 綠燈（Ruff、格式、strict Mypy 660 檔、Markdown 21 份）。依指示沒有跑 check-full。
- 改了四個檔案：
  - `docs/statistics_leaderboard_integration.md`：整份重寫
  - `src/tradingdev/domain/statistics/sharpe.py`：只改 docstring
  - `src/tradingdev/domain/statistics/__init__.py`：只改 docstring
  - `ARCHITECTURE.md`：一段
- 為了不混進主工作樹裡那 20 個未提交的修改，在 scratchpad 另開 worktree，從 `origin/feat/stats-py314` 建 `docs/leaderboard-rewrite` 來做。

## 依據

文件內容是讀 upstream/main `a24594c` 的原始碼寫的，沒有用轉述。讀過的有：
- `domain/ml/leaderboard.py`
- `domain/ml/rules.py`
- `app/ml_service.py`
- `app/ml_training.py`
- `mcp/tools/ml.py`
- `domain/ml/registry/model_registry.py`
- `docs/ml_research.md`

要注意：本分支只合併到 `837f0c6`，method_family 和 rules.py（#131）是之後才進 main 的，所以還不在本分支的樹裡。文件開頭已經寫明這點。

## 文件結構與重點

結構是：目的與狀態 → 現有能力 → 兩個整合流程及失敗路徑 → 未決事項 → 統計依據。

- **範圍**：直接採用他提議的那段措辭，註明正在等 Kuan-Lun 確認。也寫了介面是「報酬序列」，以及排行榜的 sharpe 和 annual_return 是無成本模擬帳。
- **現有能力**：
  - LeaderboardEntry 全部欄位
  - metrics 的三態
  - method_family 和 resolve_method 的規則
  - allow_parameter_axes 和 `_surface_error` 的硬牆
  - parameter_axes 的形狀
  - 訓練來源在紀錄上的缺口：只有評估用的 dataset_id；n_train_samples 沒有資料身分；compute_model_id 不含資料
- **參數平原**：
  - 最小輸入表
  - parameter_axes 的四個使用條件：
    - 不能和 allow_mixed 一起用
    - 只放有掃的軸，避免 dimension_warning 誤報
    - 有超參數座標時改用 result.axes
    - 跨 horizon 不能用 dataset_id 過濾
  - 失敗路徑表，六種
  - 「每個座標一個候選」：跨 horizon 時 model_id 一定會變
- **門檻掃描的陷阱**：獨立一節，粗體寫明不要建 plateau。不從儲存的 level 反推格點，三個理由：
  - 存下來的 level 是試過什麼就是什麼，沒試和缺失分不出來
  - 讓訊號變成常數的 level 會在記錄前就被 `ThresholdRule.signal` 拒掉，失敗點不留列，破壞 plateau「失敗點保留座標」的前提
  - 看過資料才選的門檻屬於樣本內選擇
- **IC 配對 bootstrap**：分兩層寫。
  - 第一層：序列沒有存。重跑 predict 再比對 fingerprint 可行，但那不是保存下來的產物，#62 處理的是這一層。
  - 第二層：holdout 狀態未知。predict 給的是樣本內預測，紀錄也分不出樣本內和留出；rule 的門檻選擇也一樣沒有紀錄。
  - 寫明解決第一層不等於解決第二層。10/31 驗證過的操作步驟保留成「兩層都解決之後」的小節。
- **Bonferroni 改正**：Bonferroni 建立在聯集上界上，任何相依結構下都成立，相關只會讓它保守；需要獨立性假設的是 DSR。sharpe.py 裡的錯誤說法不在 374–376 行，而在 `deflated_sharpe_ratio` docstring「Two selection corrections」段的最後一句，已經一起改正。
- **行號**：全部改成函式名稱或常數名稱，檢查後沒有殘留。

## 順帶修正

- `ARCHITECTURE.md` 和 statistics `__init__.py` 原本寫著「該文件已過時、待改寫」，改成描述新內容。
- 文件裡沒有連到 `statistics_public_api.md`：那個檔案只是主工作樹裡未追蹤的檔案，不在分支上，連過去 check-fast 會報斷連結。

## 觀察到但沒動的

- `deflated_sharpe_ratio` docstring 的「Limitation」段仍然直接說用實際 N「over-corrects」。`__init__.py` 已經說明這只是「documented intent, not a measured result」。新文件採用後者的措辭，docstring 那段這次沒動（不在指示範圍內）。
- 上游有一個未合併的分支 `feat/ml-training-dataset-binding`（`0b0d3fc`，「record the dataset a model was trained on」），沒有 PR。文件只寫成「已宣布、不在 main」。
- check-fast 用主 `.venv` 跑時，prompt contract 快照會失敗，原因是 editable 安裝指向主工作樹的舊程式碼（`610e612`）。加上 `PYTHONPATH=<worktree>/src` 之後全綠。這是環境問題，不是這次的修改造成的。
- 另有一個 worktree `feat/stats-sync-upstream-2`（`733b521`，已合併 a24594c），可能是另一個 session 正在做的同步。這次 push 讓 `feat/stats-py314` 前進到 `1d1fff6`，那邊之後要先合併這個 commit，才能 fast-forward。
- 這一輪中途收到一段第 12 輪的同步指示（head 41fa0c7）。依這一輪「不要同步 upstream」的指示，沒有執行，等使用者確認。

## 給 #62 的驗收標準全文（可直接貼上）

**Proposed acceptance criterion: holdout eligibility**

*Why.* The paired comparison in `statistics/comparison.py` assumes it is comparing out-of-sample results. On in-sample series, a paired difference
measures which candidate overfits more thoroughly, not which one is better.
In an end-to-end test on the current pipeline, the deeper of two LightGBM
models (`max_depth` 6 with 200 trees against `max_depth` 2 with 50 trees)
"won" the paired IC comparison at p = 0, because both were scored on the
rows they had been fitted on. That is the overfitting artifact, not a
result. A saved series that cannot say whether it was held out would let a
downstream comparison reproduce that artifact with full provenance attached,
so we would suggest that the artifact not ship without the following.

*Criterion.* Each saved evaluation series either declares its holdout
status, or at minimum records the pairing of training-data identity and
evaluation-data identity, so that a downstream consumer can judge
eligibility itself. Concretely, a consumer holding two saved series can
tell from the record alone, for each one, whether it was evaluated on the
dataset its model was trained on, on a different dataset, or under an
unknown relationship. Candidates without a fitting step (rules and other
signals) record that they have no training data, distinctly from "unknown".
Older entries, and any entry whose training identity is missing, report the
relationship as unknown and are never treated as eligible by default.

*Limitation, stated as part of the criterion.* Recording the
training/evaluation pair makes the relationship auditable; it does not
establish a holdout. Two different dataset IDs can still cover overlapping
periods, and a rule's threshold may have been chosen after viewing the
evaluation data. A v1 that meets this criterion therefore records what
happened and does not assert `out_of_sample`. The rule for which pairs are
eligible (for example, non-overlapping date ranges after label horizons and
embargo) remains open, and the presence of the fields should not be read as
settling it.
