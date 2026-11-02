# 第 18 輪：#38 文件收尾、public-api 合併、README 獨立分支、回覆 AIunusual

日期：2026-11-02

## 結果

步驟 0–9 都做完了，沒有在 GitHub 留言或開 PR。

| 分支 | 變化 | 檢查 |
| --- | --- | --- |
| `feat/stats-py314`（PR #38） | `a055f9a..8994a61`，3 個 docs commit，fast-forward push | check-docs 通過（22 份）、check-fast 通過 |
| `feat/stats-public-api` | `3f29c9e..0cf2c90`：merge `d9e28bc`，再加 `0cf2c90` | check-docs 通過（23 份）、check-fast 通過 |
| `docs/readme-final-evaluation-data`（新） | 從上游 main `a77babf` 開，cherry-pick `c205256` 成為 `a68f1e4` | check-docs 通過（20 份） |

## 步驟 0：讀到的新動態

- **前置檢查**：public-api、session-notes 都和 origin 一致。`feat/stats-py314` 本機是 `9222541`，比 origin 的 `a055f9a` 多 1 個 commit。這是我在上一版指示中途（被叫停前）做好的步驟 1，內容就是這一輪的步驟 1，所以接著做，沒有停下來。
- **Kuan-Lun 還沒回答** AIunusual 的問題。#38 在 issuecomment-6563407857 之後沒有新留言，也沒有新的 review。所以步驟 3、6、7 都照原計畫做。
- **AIunusual 的留言**（20:24 UTC，21:12 編輯過）：介面原文和前提 A 逐字相同。問題共 4 題，都是問 Kuan-Lun。第 1 題（MCP 預算）他已經自己劃掉，註明 "Solved in PR #139"。上游 `a77babf`（#139）把 `model_tools` 調到 76000、`initial_total` 調到 86000，註解寫明是為了一個新工具加上較寬的 `compare_runs` schema。
- **#62**：只有 cklivse 的兩則留言，沒有新動態。
- **#136**：head 仍是 `d22e380`，沒有留言也沒有 review。

## 各步驟

1. **`9222541`**：整合文件 #62 一節。引文改成和 #62 第一則留言逐字相同（之前有三處破折號被改成其他標點；我用程式比對過，現在完全一致）。開頭寫明引文從 *Why* 開始、標題改成粗體、省略了開頭幾段，並說明 "one-field delta" 的說法已撤回，附上兩則留言的連結。第 2 項修正補上 "A consumer must not read 'no training data' as held out."。新增第 4 項修正（序列產物記錄「沒有擬合步驟」與「未知」的區別，以及訊號來源）。
2. **`fb4495e`**：bootstrap 方法文件。5 筆 *to verify* 都改掉了，全文搜尋已經沒有 "verify"。
   - BL12：補上 December 2012 和 DOI，並加上附錄程式所在的 preprint 連結。
   - ET93：寫成第 13 章 §13.3，含章節標題。
   - LW08：我下載原文核對過，時間序列的檢定在 §3.2.2，區塊大小 `b` 固定。Replaced 段落寫明 circular block bootstrap、HAC 用 prewhitened QS kernel、重抽樣內用 block sums。另加兩個差異與理由：對稱區間 vs 等尾區間；以 Algorithm 3.1 校準區塊長度 vs PW04 自動估計。Politis–Romano 1992、Andrews–Monahan 1992、Götze–Künsch 1996、Loh 1987 都標成 "as cited in [LW08]"，沒有另立參考文獻條目，以免又出現沒核對過的書目細節。
   - PW04：改寫成 20 是專案自訂的下限，遠低於該文研究過的 200 和 800。
   - PSR 動差：我從 BL12 preprint 附錄確認 `PSR_Opt.get_Moments` 是除以 `self.obs`。**但有一處和作者程式不同**：作者的 Sharpe 用母體標準差（`get_Stats` 取 `m[1]**.5`），我們的 `sharpe._period_sharpe` 用樣本標準差（`ddof=1`）。文件照實寫了，兩者差 `sqrt(n/(n-1))` 倍。程式沒改。
3. **`8994a61`**：整合文件新增 "Proposed Shared Ranking Core (AIunusual, 2026-11-01)" 一節：
   - 照錄他的四項分工、介面原文，以及他對介面的說明（說明段和原文逐字比對一致）。
   - 統計端需求 7 點，每點都寫出對應的上游函式與行為。
   - 另列 4 點「他的提案已涵蓋」：方向取自 catalog、兩種 Sharpe 已是不同 id、fold summary 不排名、trial scope 的 DSR。
   - Three Responsibilities 表加上 "Who builds it" 欄。
   - Follow-up Work 每項標上負責人，並新增第 7 項（#62 序列儲存，未指派）、第 8 項（統計分析，cklivse）。
   - Open Items 新增第 6 項（#136 的合併順序）。
4. **push**：check-docs、check-fast 都通過，fast-forward push `a055f9a..8994a61`。
5. **public-api**：merge `d9e28bc`（父 commit `3f29c9e`、`8994a61`），兩處衝突照指示解：
   - ARCHITECTURE.md 取 py314 的版本，句尾依序接 bootstrap_methods 和 public_api 兩個連結。
   - 整合文件 Purpose 第一段取 py314 的版本，再接回 public_api 那一句。

   檢查舊說法時另做了 `0cf2c90`：
   - `__init__.py` docstring 和公開 API 文件結尾描述整合文件的方式太窄（只說 plateau 與配對比較怎麼讀排行榜），改成「排名涵蓋訊號與回測，本套件在排名後分析、不決定名次」。
   - `__init__.py` 的 "only out-of-sample returns … are comparable" 會被讀成「排名也需要樣本外」，改成「統計比較需要樣本外報酬；在調過參數的樣本內報酬上它量的是擬合；排名沒有這個要求」。

   只改 docstring，沒有改行為或 `__all__`。public API 測試 3 passed，check-docs、check-fast 通過後 push。
6. **README**：Kuan-Lun 還沒回答，所以照計畫 push 了 `docs/readme-final-evaluation-data`（`a68f1e4`），沒有開 PR。
7. **(a)**：定稿見下方。
8. **(b)**：#136 head 仍是 `d22e380`，兩點不用改寫。依指示在開頭加連結、在結尾加一句。
9. 本報告與團隊報告第 3 節。

## 前提 B 逐點核對（上游 main `a77babf`，`domain/ml/leaderboard.py` 與 `app/ml_service.py`）

1. **對**。`rank = index + 1`，是 competition rank（1, 1, 3）。現有整合文件 "What Exists Today" 早就這樣寫（例子用 1, 2, 2, 4）。
2. **對**，再補一點：`math.isclose` 用預設值 `rel_tol=1e-9`、`abs_tol=0.0`，所以剛好是 `0.0` 的值只會和 `0.0` 同分。
3. **對**，再補兩點：`_stored_metric` 寫入時就把非有限值存成 `null`，存檔後「非有限」和「量測失敗」已經分不開；`reason` 目前是自由文字。
4. **對 `rank_entries` 和提案的簽名來說是對的**，但要補充：服務層已經有 `allow_mixed` 和 `allow_parameter_axes`（`MLService.leaderboard`），拒絕的檢查做在 `rank_entries` 外面。混合排名的回覆只寫 `"context": "mixed"`。
5. **部分不精確**。回覆其實有數字欄位：`n_candidates` 是 `len(entries)`，含被跳過的；`n_ranked` 是 `len(result.ranked)`，是 `top_k` 截斷後的數量。「可排名數」本身確實只出現在 caveat 文字，也確實是篩選後的數量。
6. **方向對，但例子錯了**。回測的 `sharpe_ratio` 是用日報酬算的（`DAILY_EQUITY_METRICS`），所以 1h 和 1d K 棒不會讓它的定義不同。真正會讓定義不同的，是 backtest 設定的 `periods_per_year`（例如 365 和 252）和 `risk_free_rate`（`calculate_metrics`）。這兩個都不在 `MetricDefinitionSnapshot` 裡，那裡只有 `unit` 和 `requires_annualization`。1h 和 1d 的例子只適用於訊號端的 `sharpe`（`periods_per_year(timeframe, horizon)`）。回覆和文件都已經改用正確的例子。
7. **對**，再補一點：現行 `RankedEntry` 帶著整個 `LeaderboardEntry`，所以改成字串對現況是退步。
8. **對**：`git diff upstream/main...feat/stats-py314 -- src/tradingdev/domain/ml/` 沒有輸出。

其他和前提不同的地方：#62 引文除了省略段落，原本也改了三處破折號（已修正）；LW08 的時間序列做法精確位置在 §3.2.2；PSR 的 Sharpe 標準差和作者程式不同（見步驟 2）。

## 文件和程式碼不符的地方

- **PSR 的 Sharpe 標準差**：作者附錄程式用母體標準差，我們用 `ddof=1`。已寫進方法文件，程式沒改。
- 以下 4 點是第 17 輪就記下的，仍未改，也都寫在文件裡：
  - `ml_report_block` 自己直接呼叫 `rank_entries`，沒有經過 service。
  - `compare_runs` 不產生名次，一個 scope 套用到全部 run。
  - walk-forward 沒有保存每個 fold 的預測。
  - PR #136 用 `""` 同時表示「沒有模型」和「未知」。
- 整合文件開頭仍寫 "merged upstream main at `a24594c`"。這是事實，因為這條分支沒有 merge `a77babf`；新的一節另外註明是對照 `a77babf` 核對的，兩者只差 `tooling/prompt_contracts.py`。

## 其他

- 有一個舊 session 留下的 session-notes worktree 紀錄，目錄已經不在，擋住了 checkout。我用 `git worktree prune` 清掉了，沒有影響任何檔案。
- 沒有刪除任何遠端分支，也沒有 force push。

## 要貼的文字

### (a) 給 AIunusual 的回覆（貼在 #38）

```markdown
@AIunusual Thanks. The four questions are Kuan-Lun's; here is the statistics side's view, plus notes on the interface, which I've added to the integration doc as the proposed core (`docs/statistics_leaderboard_integration.md`, "Proposed Shared Ranking Core", `feat/stats-py314` @ `8994a61`).

Interface notes, checked against `rank_entries` and `MLService.leaderboard` on main (`a77babf`):

1. `values: {metric: float | null}` can't carry the three missing states you list, so the core can't put the right reason in `skipped`. Today `rank_entries` has two: an absent key (`no '<metric>' recorded`) and a stored `None` or non-finite value (`'<metric>' is unavailable or not finite`); there is no "not applicable". Either keep "key absent = not recorded, null = not finite" and add a reason for not applicable, or make the value a tagged union. A fixed reason code in `skipped`, with the text beside it, would also let MCP, reports and statistics branch on it.
2. Ranks: `rank_entries` assigns competition ranks today (`rank = index + 1` when the value is not close to the previous one, so 1, 1, 3), not dense ranks. Switching to dense changes the `rank` field of the `leaderboard` tool and the ML report; worth choosing deliberately and saying so. Ties are also detected with `math.isclose(value, previous)` at the defaults (`abs_tol=0.0`), against the previous value, so a chain of near-equal values can share a rank even when its ends are not close; fine to keep, but worth stating.
3. The cross-group refusal needs a parameter in the `rank_candidates` signature (e.g. `allow_mixed_groups`), and the result should say which `group_key` values were mixed. Today that check sits outside `rank_entries` (`comparability_error`, skipped with `allow_mixed`), and a mixed result reports only `"context": "mixed"`.
4. For runs, `group_key` should include the annualisation basis and the risk-free setting, not only the metric definition and unit. A run's `sharpe_ratio` is computed from daily returns and annualised with the backtest's `periods_per_year` and `risk_free_rate`; neither is in `MetricDefinitionSnapshot`. Two runs annualised with 365 and 252 days per year carry the same definition snapshot but are not the same measurement.
5. Please return the number of rankable candidates, the number skipped, and the total before filters when a filter applied, as fields rather than only caveat text. Today the rankable count reaches `required_t_stat` and the caveat only; the response's `n_candidates` includes skipped entries and `n_ranked` is counted after `top_k`. The deflated Sharpe ratio needs N as a number, skipped candidates were still tried, and the filtered-N effect noted in the integration doc for `required_t_stat` carries over to any shared core.
6. Alongside the rendered `candidate_id`, a structured reference (kind plus `entry_id`, or kind plus `run_id` and `scope`), so analysis after ranking can fetch each candidate's returns and timestamps, or the reason they are unavailable, without parsing a string. `RankedEntry` holds the whole `LeaderboardEntry` today, so this keeps what the current code already has. De-duplication should use the same pair.
7. Agreed on keeping the two Sharpe ratios apart. They already have different catalog ids (the signal simulation's `sharpe`, the run's `sharpe_ratio`); keeping `MetricDefinition.name` the catalog id, never a display label, keeps them out of one column. Two related points: direction should come only from the catalog, refusing a run metric whose `optimization_direction` is `None` the way `metric_direction` refuses a signal metric; and trial scopes of one optimisation (`trial/0/train`, `trial/1/train`) are an in-sample selection, so the chosen trial's Sharpe should be read with the deflated Sharpe ratio over that run's trial count.

On the questions, for Kuan-Lun's decision:

- `compare_runs`: either works for statistics, as long as candidate identity and de-duplication use `(run_id, scope)` and the current `run_ids` + `scope` form keeps working. I see #139 already budgets for a wider `compare_runs`.
- README: I'm happy to move it to main now as a five-line standalone PR (branch `docs/readme-final-evaluation-data` on my fork, a cherry-pick onto `a77babf`), or leave it in #38, whichever Kuan-Lun prefers.
- Sequencing: the integration doc and the follow-up list are already on #38, and #38 does not touch `domain/ml/leaderboard.py`, so they need not hold up the core extraction. If #136 lands first, the two points I've raised on it (an explicit no_fit/unknown status and the signal source) are cheapest to settle before it merges, since they change the same entry schema.
```

### (b) 給 PR #136

```markdown
Following up on my [second comment on #62](https://github.com/Kuan-Lun/tradingdev/issues/62#issuecomment-6560285324).

Thanks for #136. Two points, checked at head `d22e380`, against what Kuan-Lun asked for on #38 (2026-11-01) and the #62 criterion:

1. **`""` means two different things.** `training_dataset_id` is `""` for candidates with no fitting step (`rule`, `other`) and also when the training source is unknown: a missing or unreadable artifact, or a record written before schema 2 (`_candidate_identity` in `app/ml_service.py`). Kuan-Lun asked that "no model fitting step" and "training source unknown" be represented separately, and the #62 criterion requires rules and other signals to "record that they have no training data, distinctly from 'unknown'". Today only the HTML report separates the two, by inferring from `method_family`. Suggestion: record the state explicitly at evaluation time, for example `training_dataset_status: "recorded" | "no_fit" | "unknown"` next to `training_dataset_id`, and carry it to `LeaderboardEntry`, `RecordedEvaluation`, `LeaderboardRow` and `LeaderboardSkipped`. "no_fit" should not be read as independent of the evaluation data: a rule's threshold may have been tuned on it.

2. **Signal provenance is not recorded.** `evaluate_prediction` (the backend runs the model) and `evaluate_signal` with a `model_id` (the caller supplies the signal) produce identical entries. For a caller-supplied signal, `training_dataset_id` then says only where the named artifact was fitted, not that the evaluated signal came from it. Suggestion: record the source on the entry, for example `signal_source: "backend_model" | "caller"`, so a consumer can tell when the training identity actually describes the evaluated signal.

Neither needs a holdout rule; both only make the record say what happened. Since you plan to merge #136 before the ranking core work, both are cheapest to decide before it merges: they change the entry schema this PR introduces.
```

### (c) README PR 的標題與內文

```markdown
Title: docs(readme): recommend reserving final evaluation data

Body:
## Summary

Adds one paragraph to README, at the end of "使用樣本外驗證與最佳化": before development starts, users may set aside a period of data for final evaluation and use it only after rules, features and parameters are chosen. If the strategy is changed after seeing that period's results, the period is no longer an independent final test.

The paragraph is a usage recommendation. It says that the system neither checks nor verifies this, that development may use the most recent data, and that a reserved test period or out-of-sample evidence is not a condition for a result to be compared or ranked (the scope Kuan-Lun confirmed on #38).

## Notes

- Cherry-picked from `c205256` on #38 so the README change does not wait on #38's review (Kuan-Lun's question 3 on #38). Five added lines in `README.md`, no other files; applies cleanly to `a77babf`.
- #38 keeps the same commit; once this merges, #38's copy merges as an identical change.
- Checks: `scripts/check-docs.sh` passed (docs-only change).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

### (d) 需要你決定的事項

```text
1. 要不要貼 (a)：AIunusual 的四個問題是問 Kuan-Lun 的，(a) 只提供統計端的看法。要等 Kuan-Lun 先回答，還是現在就貼？
2. README PR 要現在開，還是等 Kuan-Lun 回答第 3 題？分支已經 push。#38 保留 c205256，兩邊內容相同，合併時不會衝突。
3. #136 的 (b) 要現在貼嗎？AIunusual 打算先合併 #136，所以越早貼，兩點越可能在合併前處理。
4. 0cf2c90 改了 __init__.py docstring 的 "only out-of-sample returns … are comparable"，這是我依「不能和新範圍矛盾」做的判斷。請確認這樣改可以。
5. PSR 的 Sharpe 要不要改成和作者一樣用母體標準差？目前只在文件記錄差異。這一輪不准改程式行為，所以沒改。
6. origin/wip/stash-610e612 要不要刪（照你的指示，這一輪沒刪）。
```
