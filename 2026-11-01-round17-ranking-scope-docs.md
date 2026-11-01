# 第 17 輪：依 Kuan-Lun 11/01 的回覆補齊文件與 #62 驗收標準

日期：2026-11-01

## 結果摘要

- 這輪只改文件，沒有改 `domain/statistics` 的程式行為或公開 API，也沒有動上游的 ML 排行榜模組。
- `feat/stats-py314` 新增 4 個 docs commit，接在第 16 輪的 `988cf54` 之後：
  - `8a63dbb` 新增 bootstrap 方法文件
  - `6edff42` 重寫整合文件，更新 ARCHITECTURE.md
  - `c205256` README 加入預留最終評估資料的建議
  - `a055f9a` #62 驗收標準對齊已貼出的版本，並加入三項修正
- 檢查：`check-docs` 通過，`check-fast` 通過。check-full：沒有另跑。`988cf54..a055f9a` 只改 4 份文件（ARCHITECTURE.md、README.md、兩份 statistics 文件），程式與測試和 `988cf54` 相同；`988cf54` 的 check-full 是 7480 passed、0 failed（58 分 48 秒）。push 前在 `a055f9a` 又跑了一次 `check-docs` 和 `check-fast`，都通過。
- push：已 fast-forward push（`988cf54..a055f9a`，沒有 force push）。GitHub 顯示 PR #38 head `a055f9a`、MERGEABLE、32 個檔案。
- session-notes：團隊報告第 3、5 節已更新（commit `39914d3`；第 1 節的檔案數同步改成 32 個（+9,040 / −3 行））。

## 步驟 0：前置檢查和指示不符

- 指示預期 head 是 `8b4336e`。本機 head 當時是 `988cf54`，也就是第 16 輪的改名 commit，那時還沒 push。
- 我照規則停下來詢問。你選擇先完成第 16 輪，再把這輪接在 `988cf54` 之後做。
- 因此 PR #38 這次 push 會同時帶入第 16 輪的改名。
- `upstream` remote 已存在（`Kuan-Lun/tradingdev`），已 fetch。

## 步驟 1：重寫 `docs/statistics_leaderboard_integration.md`

- 刪掉 Scope 引文和 "pending confirmation from Kuan-Lun"，改寫成 Kuan-Lun 確認的範圍。
- 新增「Three Responsibilities」：
  - 候選選取：application service
  - 排名：從 `rank_entries` 抽出的共用排序核心
  - 統計分析：`domain/statistics`
  - 依你列的 (1)–(4) 寫明各層的責任，並標明這是約定的分工，目前只有訊號來源存在。
- 新增「What Exists Today」，每個函式都在目前的樹裡核對過：
  - `rank_entries` 的簽名、排序方式、競賽式同分名次（1, 2, 2, 4）、缺值的兩種 skipped 原因。
  - `get_run_metrics` 讀保存值、不重跑，以及它支援的 scope。
  - `compare_runs` 不產生名次、拒絕重複 `run_id`，且一個 scope 套用全部 run。
  - walk-forward 沒有保存每個 fold 的預測。
- 新增「Statistical Comparison After Ranking」：
  - 寫明沒有共同期間時，目前回傳 `IntervalUnavailable(reason="insufficient_observations", observations=0)`。
  - `"no_overlap"` 列為待提案事項（Open Items 1），沒有改程式。
- 新增「Follow-up Work」，6 項：
  - 回測候選
  - 共用排序核心
  - 代表結果的標記與保存
  - fold 統計不冒充整段績效
  - ML 報告改走 service
  - 缺值原因的傳遞
- Open Items：PR #136 一項改成它實際做到的範圍，以 head `d22e380` 為準。

## 步驟 2：ARCHITECTURE.md

- statistics 那一列加上方法文件的連結。
- 「引擎無關的統計分析」一節的範圍改成新範圍，並註明目前只有訊號排名，回測候選、共用排序核心與代表結果都尚未實作。

## 步驟 3：新增 `docs/statistics_bootstrap_methods.md`

- 命名和語言沿用 `docs/statistics_*.md` 的慣例（英文、snake_case），ARCHITECTURE.md 和整合文件都連過去。
- 逐一寫出每個程序的文獻、實作來源（`arch` 8.0.0，以 `uv.lock` 為準）、照文獻做的步驟，以及省略、替換或組合的部分。涵蓋的程序：
  - Sharpe 區間
  - comparison 的單一序列區間（`interval_table_outcome`）
  - `difference_interval`
  - PSR、DSR
  - 區塊長度選擇
- 要求的自行設計項目都讀過程式碼再寫：
  - 差額的區塊長度用 jackknife 影響值估計
  - Sharpe 的區塊長度取報酬與平方報酬兩個估計中較大的
  - 用 percentile 區間，不用 studentized 或 BCa，並說明和 Ledoit & Wolf 2008 的差別
  - p 值由內插的 percentile 區間反推，以及 reps 少時的限制
  - `MIN_BOOTSTRAP_OBSERVATIONS = 20`
  - 丟掉統計量未定義的重抽樣（`valid_reps`）
  - Bonferroni 和 DSR 不疊用
- 標成 *to verify* 的引用細節：
  - Bailey & López de Prado (2012) 的卷期頁碼：*Journal of Risk* 15(2), 3–44。
  - Efron & Tibshirani (1993) 的 percentile 區間章節（第 13 章）。
  - Ledoit & Wolf (2008) studentized 做法的建構細節（原樣本用 kernel HAC 標準誤，重抽樣內用區塊式標準誤）。
  - Politis & White (2004) 是否建議最小樣本數。
  - Bailey & López de Prado (2012) 是否指定用母體動差估計偏態與峰態。
- 差額區塊長度用 jackknife 影響值這個做法，我找不到直接出處，文件寫明是本專案的組合。Künsch (1989) 只作為線性化想法的背景引用。

## 步驟 4：#62 驗收標準（依你中途更新的指示）

- 標準已在 2026-11-01 貼到 #62（cklivse 的留言 6554320220），Kuan-Lun 在 #38 同意方向。
- 整合文件的段落改成和已貼出的版本一致，包括原本缺的 "The pairing has to travel with the series artifact, not only sit on the leaderboard entry..." 一段。標題由 "Proposed Acceptance Criterion for #62" 改為 "Acceptance Criterion for #62"。
- 拿掉 "one-field delta" 的說法：文件沒有收那段開場。
- 三項修正放在引文之後，註明是依 Kuan-Lun 11/01 在 #38 的回覆加入：
  1. eligible 指可作為配對比較的輸入，不是收錄排名的條件；
  2. 沒有擬合步驟只表示沒有訓練資料，不代表規則或門檻沒用評估資料調過；
  3. walk-forward 序列保存原評估流程各 fold 的實際預測與訓練／評估範圍，不能用最終重訓模型的預測代替；歷史缺序列時回報不可取得，不重新生成、不推定合格。
- 「記錄配對只讓關係可查核，不等於證明留出」保留在 Limitation 段。
- 依指示，報告不重貼整份標準，只附修正留言，見下方 (b)。
- 你說已有修正留言的草稿，但訊息裡沒有附上；還沒比對，等你貼上後再比對。

## 步驟 5：README

- 在「使用樣本外驗證與最佳化」末尾加了一段「建議預留最終評估資料」。
- 語氣是建議。寫明系統不檢查、不驗證，可以使用最近期間的資料開發，保留測試期也不是列入比較的條件。

## 步驟 6：檢查

- `scripts/check-docs.sh`：通過（22 份文件）。
- `scripts/check-fast.sh`：通過。
- check-full：沒有另跑。這輪只改文件，程式與測試和 `988cf54` 相同，由第 16 輪在 `988cf54` 的 check-full 涵蓋（7480 passed、0 failed）。
- push 前在 `a055f9a` 重跑 `check-docs` 和 `check-fast`，都通過。

## 審查

- 一個獨立 reviewer 對照程式碼、arch 8.0.0 和 PR #136 審了四份文件。8 個確認的錯誤都修正了：
  1. 整合文件寫「報告不自己排名」。實際上 `domain/ml/report.py` 的 `ml_report_block` 自己呼叫 `rank_entries`。改成目標與現況分開寫，並加進 Follow-up Work。
  2. #62 還沒做的「保存的序列帶有身分」寫成了現在式，改成「依提案標準，必須……」。
  3. ARCHITECTURE.md 讀起來像排名已經支援回測，已補上「尚未實作」。
  4. DSR 的 `N` 實際上由呼叫端傳入，預設是 trial Sharpe 的個數；有 trial 被丟掉時會少算。已寫明。
  5. 重新縮放只在離散度低於 2⁻⁶⁰ 或量級高於 2⁶⁰ 時發生，原本寫成每次都做。
  6. PSR 和 DSR 回傳 `None` 的情況原本列得不完整，已補齊。
  7. 「用母體動差」原本寫成照文獻，改列為本專案的選擇，並標 to verify。
  8. 回測 scope 的報酬和時間戳可能是 `None`，原本寫成一定有。
- 也採納了幾個小建議：
  - Bonferroni 和 DSR 的說明集中到方法文件，整合文件只留排行榜特有的部分。
  - 影響值的正負號寫法修正。
  - GARCH 的覆蓋率改成「在 100 個樣本的抽樣誤差內」。
  - 還沒實作的功能改用「將會」的寫法。

## 文件描述和程式碼不符的地方

- `rank_entries` 只收 `LeaderboardEntry`。排序、同分和缺值的邏輯寫在函式裡面，沒有可以單獨呼叫的共用函式，所以「抽出共用核心」是真的要重構，不是換個呼叫方式。
- `compare_runs` 不產生名次，會拒絕重複的 `run_id`，而且一個 `scope` 套用到全部 run，比較不了同一次最佳化內的多組 trial。這和 Kuan-Lun 的描述一致。
- ML 報告（`ml_report_block`）目前自己呼叫 `rank_entries`，沒有經過 application service。這和「MCP 與報告共用 service 結果」的目標不符。
- walk-forward 沒有保存每個 fold 的預測。`ScopeObservations` 只有權益、報酬、時間戳和交易等欄位。
- 回測 scope 保存的報酬可能是 `None`，例如初始資金未知時。
- PR #136：`""` 同時表示「沒有模型」和「未知」，只有 HTML 報告依 `method_family` 分開顯示；它也沒有記錄訊號來源，以及訓練期間、標籤長度和 embargo。
- 指示寫上游 `domain/benchmark.py` 用 excess return 指總報酬差。實際上總報酬差是在 `adapters/reporting/tables.py` 算的（第 16 輪已記錄）。

## feat/stats-public-api 的狀態

- 照指示這輪沒有碰。它從 `c5fff7a` 分出，第 16 輪已 merge 到 `988cf54`。
- 要併進 PR #38，需要先接到新的 head（這輪的 `a055f9a`）上。第 16 輪已把 `988cf54` merge 進去（`6b7b689`），之後還要再 merge 一次 `a055f9a`。
- 會有衝突：這輪重寫了整合文件的 Purpose 一段，而 public-api 在同一段加了一句指向 `statistics_public_api.md` 的話。

## 要貼的文字

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

### (c) 給 PR #136 維護者的留言

```markdown
Thanks for #136. Two points, checked at head `d22e380`, against what Kuan-Lun asked for on #38 (2026-11-01) and the #62 criterion:

1. **`""` means two different things.** `training_dataset_id` is `""` for candidates with no fitting step (`rule`, `other`) and also when the training source is unknown: a missing or unreadable artifact, or a record written before schema 2 (`_candidate_identity` in `app/ml_service.py`). Kuan-Lun asked that "no model fitting step" and "training source unknown" be represented separately, and the #62 criterion requires rules and other signals to "record that they have no training data, distinctly from 'unknown'". Today only the HTML report separates the two, by inferring from `method_family`. Suggestion: record the state explicitly at evaluation time, for example `training_dataset_status: "recorded" | "no_fit" | "unknown"` next to `training_dataset_id`, and carry it to `LeaderboardEntry`, `RecordedEvaluation`, `LeaderboardRow` and `LeaderboardSkipped`. "no_fit" should not be read as independent of the evaluation data: a rule's threshold may have been tuned on it.

2. **Signal provenance is not recorded.** `evaluate_prediction` (the backend runs the model) and `evaluate_signal` with a `model_id` (the caller supplies the signal) produce identical entries. For a caller-supplied signal, `training_dataset_id` then says only where the named artifact was fitted, not that the evaluated signal came from it. Suggestion: record the source on the entry, for example `signal_source: "backend_model" | "caller"`, so a consumer can tell when the training identity actually describes the evaluated signal.

Neither needs a holdout rule; both only make the record say what happened.
```
