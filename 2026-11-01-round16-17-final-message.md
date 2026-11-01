# 第 16、17 輪結束時的回報訊息

日期：2026-11-01

這是第 16、17 輪結束時在對話中給使用者的回報原文。各輪的詳細報告見
`2026-11-01-round16-active-return-rename.md` 和 `2026-11-01-round17-ranking-scope-docs.md`。

## 結果

第 16、17 輪都做完並 push 了。check-full 是 7480 passed、0 failed，四個釘值逐位相同。紀錄已存到 session-notes。

## 第 16 輪：改名 `active_return_annualised`

- 改了 3 個檔案（+40 / −31）：`benchmark.py`、它的測試、ARCHITECTURE.md。四個釘值（天數 366、Sharpe、traded notional、成本占比）都和改名前相同。
- check-full 在乾淨 worktree 跑，58 分 48 秒，exit 0。第一次跑到 76% 時被 SIGTERM 中止，找不到是誰送的；用同一個 commit 重跑就通過了。
- `feat/stats-py314` 已 fast-forward push（`8b4336e..988cf54`）。
- `feat/stats-public-api` 用 **merge** 接上，沒有用 rebase，因為這條分支已經 push 過，rebase 要 force push。merge commit 是 `6b7b689`。之後補了 `3f29c9e`：在公開 API 文件加一段命名說明。check-docs、check-fast 都通過，已 push。
- 團隊報告補上三條分支的切分與不另開 PR 的原因。公開 API 文件實際是 292 行，不是指示寫的 269 行。

## 第 17 輪：依 Kuan-Lun 回覆補的文件

- 4 個 docs commit：`8a63dbb`、`6edff42`、`c205256`、`a055f9a`，已 fast-forward push。PR #38 現在 head 是 `a055f9a`，GitHub 顯示可合併，32 個檔案。
- 這 4 個 commit 只改文件，沒有另跑 check-full；程式和測試沒變，由第 16 輪的 check-full 涵蓋。push 前在 `a055f9a` 重跑 check-docs（22 份文件）和 check-fast，都通過。
- 團隊報告第 3、5 節已更新（`39914d3`），第 1 節的檔案數同步改成 32。
- `feat/stats-public-api` 目前只接到 `988cf54`。要併進 PR #38，還要再 merge 一次 `a055f9a`，整合文件的 Purpose 段落預計會有衝突。
- 文件和程式不符的地方：
  - `ml_report_block` 自己直接呼叫 `rank_entries`，沒有經過 service。
  - `compare_runs` 不產生名次，一個 scope 套用到全部 run。
  - walk-forward 沒有保存每個 fold 的預測。
  - PR #136 用 `""` 同時表示「沒有模型」和「未知」。
- 方法文件裡標成「待核對」的引用：
  - Bailey & López de Prado 2012 的卷期頁碼 15(2), 3–44。
  - Efron & Tibshirani 1993 的第 13 章。
  - Ledoit & Wolf 2008 的建構細節。
  - Politis & White 2004 是否建議最小樣本數。
  - 用母體動差估計偏態與峰態是否出自文獻。

## 收尾紀錄（session-notes）

- 第 16 輪報告 `38a380d`，第 17 輪報告 `b31f594`。
- check-full 的 wrapper 和啟動腳本存到 `tools/`（`fcc74a3`），之後的 session 可以直接用。
- memory 已更新，暫用的 worktree 已刪除。

## 要貼的文字（沒有在 GitHub 留言）

### (a) PR #38 給 Kuan-Lun 的回覆

```markdown
@Kuan-Lun 謝謝回覆。各點的處理位置如下（`feat/stats-py314` @ `a055f9a`）：

1. **排名範圍與分工** → `docs/statistics_leaderboard_integration.md` 的 *Scope* 與 *Three Responsibilities*。候選選取（application service）、排名（從 `rank_entries()` 抽出的共用排序核心；訊號候選用 `entry_id`，回測候選用 `run_id + scope` 並保留策略版本與參數）、統計分析（`statistics`）。代表結果的明確標記與保存、交易條件一併呈現、缺值保留原因不補零、fold 統計不冒充整段績效、快速排名讀保存指標，都寫在這兩節。回測候選、共用排序核心、代表結果、ML 報告改走 service、缺值原因傳遞列在 *Follow-up Work*，這次只寫文件，沒有實作。
   - 核對目前程式時確認：`rank_entries()` 只收 `LeaderboardEntry`，排序／同分／缺值邏輯寫在函式內；`compare_runs()` 不產生名次、拒絕重複 `run_id`，且一個 `scope` 套用全部 run；另外 `domain/ml/report.py` 的 `ml_report_block` 目前自己呼叫 `rank_entries()`，沒有經過 service。
2. **統計比較是排名後的選用分析** → *Statistical Comparison After Ranking*。目前兩筆序列沒有共同期間時，`difference_interval_outcome` 回傳 `IntervalUnavailable(reason="insufficient_observations", observations=0)`；另列 `"no_overlap"` 原因為待提案事項（*Open Items* 1），這次沒有改程式。
3. **bootstrap 文獻與版本** → 新增 `docs/statistics_bootstrap_methods.md`。逐一列出 Sharpe 區間、單一序列區間、配對差、PSR、DSR、區塊長度選擇採用的文獻、實作（`arch` 8.0.0，以 `uv.lock` 為準），以及省略、替換或自行組合的步驟與理由：差額區塊長度用 jackknife 影響值估計、Sharpe 區塊長度取報酬與平方報酬兩個估計中較大者、用 percentile 而非 studentized（與 Ledoit & Wolf 2008 的差別）或 BCa、p 值由內插 percentile 區間反推及 reps 少時的限制、`MIN_BOOTSTRAP_OBSERVATIONS = 20`、丟掉統計量未定義的重抽樣、Bonferroni 與 DSR 不疊用。卷期頁碼不確定的引用標為 *to verify*。
4. **README** → 「使用樣本外驗證與最佳化」末尾加入預留最終評估資料的使用建議，寫明系統不檢查、不驗證，可使用最近期間的資料，保留測試期也不是列入比較的條件。
5. **#62** → 整合文件的 *Acceptance Criterion for #62* 已對齊 #62 上貼出的版本，並依你的回覆加入三項修正（另在 #62 留言說明）。PR #136 實際做到的範圍寫在 *Open Items* 2：`""` 同時表示「沒有模型」和「未知」，也沒有記錄訊號是後端產生還是呼叫端提供，這兩點和你的要求不一致，會另在 #136 說明。

這次 push 也包含 `988cf54`：`BenchmarkComparison.excess_return_annualised` 改名為 `active_return_annualised`（逐期差的平均年化就是 active return；"excess return" 留給報告用的總報酬差），數字沒有改變。
```

### (b) 給 #62 的修正留言

```markdown
Follow-up to my comment above, after Kuan-Lun's reply on #38 (2026-11-01). The criterion stands, with these changes:

- **Withdrawn: the "one-field delta" framing.** Addition 3 below asks for per-fold predictions and their ranges, which is more than one training-dataset field.

**Additions**

1. **"Eligible" means usable as input to a paired comparison.** It is not a condition for being ranked; ranking does not require a holdout.
2. **"No fitting step" means no training data, nothing more.** It does not mean a rule's form or threshold was never tuned on the evaluation data, so it is not evidence of a holdout.
3. **Walk-forward series and historical records.** A walk-forward series saves, from the original evaluation run, each fold's actual predictions with that fold's training and evaluation ranges. Predictions of a model retrained at the end on the same data do not substitute for them. A historical record without a saved series reports the series as unavailable; it is not regenerated and not presumed eligible.

Unchanged, including the limitation: recording the training/evaluation pair makes the relationship auditable; it does not establish a holdout. The pairing still has to travel with the series artifact, not only sit on the leaderboard entry.
```

### (c) 給 PR #136 維護者

```markdown
Thanks for #136. Two points, checked at head `d22e380`, against what Kuan-Lun asked for on #38 (2026-11-01) and the #62 criterion:

1. **`""` means two different things.** `training_dataset_id` is `""` for candidates with no fitting step (`rule`, `other`) and also when the training source is unknown: a missing or unreadable artifact, or a record written before schema 2 (`_candidate_identity` in `app/ml_service.py`). Kuan-Lun asked that "no model fitting step" and "training source unknown" be represented separately, and the #62 criterion requires rules and other signals to "record that they have no training data, distinctly from 'unknown'". Today only the HTML report separates the two, by inferring from `method_family`. Suggestion: record the state explicitly at evaluation time, for example `training_dataset_status: "recorded" | "no_fit" | "unknown"` next to `training_dataset_id`, and carry it to `LeaderboardEntry`, `RecordedEvaluation`, `LeaderboardRow` and `LeaderboardSkipped`. "no_fit" should not be read as independent of the evaluation data: a rule's threshold may have been tuned on it.

2. **Signal provenance is not recorded.** `evaluate_prediction` (the backend runs the model) and `evaluate_signal` with a `model_id` (the caller supplies the signal) produce identical entries. For a caller-supplied signal, `training_dataset_id` then says only where the named artifact was fitted, not that the evaluated signal came from it. Suggestion: record the source on the entry, for example `signal_source: "backend_model" | "caller"`, so a consumer can tell when the training identity actually describes the evaluated signal.

Neither needs a holdout rule; both only make the record say what happened.
```

## 待使用者處理

- 貼上 (a)、(b)、(c)。
- 使用者已有 #62 修正留言的草稿，但沒有附上；貼上後再和文件定稿比對。
