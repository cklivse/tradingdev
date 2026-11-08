# 第 27 輪：證據連結釘到 commit、SIGTERM 收束紀錄、README 分支準備

日期：2026-11-08。沒有開 PR、沒有在 #189／#190 留言、沒有動五個 stats 分支的程式、沒有嘗試重現 SIGTERM、沒有建映像。

## 結論

- **任務 1 完成**（7ac57a2，已在本輪開頭回報）：五份 body 的清單連結改成 `https://github.com/cklivse/tradingdev/blob/eeec7235e956db8ab1d8cf68af898b4a5480460c/evidence/2026-11-08-round26/container-failures-741fd84.md`。連結回應 200，該檔從 eeec723 之後沒有改過。「on the `session-notes` branch」改成「pinned to `session-notes` commit eeec723」。
- **任務 2 完成**：`SIGTERM-INVESTIGATION.md`（本分支根目錄），只有事實和未解，沒有結論和下一步。
- **任務 3 完成，沒有衝突，分支沒有改動，所以沒有東西要 push**：`docs/readme-final-evaluation-data` 仍是 a68f1e4。PR body 全文在本檔最後。

## 任務 2：SIGTERM-INVESTIGATION.md

收了指示列的五項，另外加了兩項報告裡已有、但之前沒一起看的事實：

- **2026-11-07 之前也被殺過兩次**：2026-10-31（79%，exit 143）和 2026-11-01（76%，exit 241）。2026-11-01 那次重跑同一個 commit 就跑完了（7480 passed）。2026-10-31 到 2026-11-01 之間另有四次完整套件跑完。所以「只有完整套件會死」要加上「但完整套件也跑完過好幾次」。我把它放進表裡，沒有下結論。
- **2026-10-31 被殺的那次，報告沒有記錄是不是用 setsid 跑的**。第 9 輪是在第 2 次才寫明改用 `setsid --wait`。

整理時發現的缺口，都寫在「未解」：

- 2026-11-07 的三個時間點（16:15、16:51、17:05）各對應哪一次執行，報告沒有記錄。4705 是不是三次共同的被殺點，也沒有分開寫。原始 log 在 `/tmp`，codespace 2026-11-08 09:43 重開後已經不在，所以無法補。
- 被殺時 cgroup 以外的記憶體。`memory.peak` 只量得到這個 cgroup。

exit code 是查程式碼確認的：143 是 shell 的 128 + 15；241 是 wrapper 做 `sys.exit(-15)`（256 − 15）。兩者都是 signal 15。

## 任務 3：docs/readme-final-evaluation-data

- 分支 a68f1e4，一個 commit，base 是 upstream a77babf（`git merge-base`），只改 `README.md` +5。repo 不是淺複製（`--is-shallow-repository` 是 false）。
- 自 a77babf 以來，上游的 README 改了 +343／−211。
- 用 `git merge-tree --write-tree` 和實際 `git merge` 合併到 c246355：**沒有衝突**，README 自動合併，結果只有那 5 行新增。
- 照指示，沒有衝突就不 merge 進分支。所以分支沒有新 commit，沒有 push。
- **位置**：合併後那 5 行落在「### 使用樣本外驗證與最佳化」的最後，緊接參數最佳化那段（結尾「結果應同時查看訓練表現與樣本外表現；部分指標可能因交易或資料不足而無法計算。」），之後是「## 研究機器學習訊號」。這和在 a77babf 上的位置相同（同一節的結尾），上下文也對。
- 在合併樹上：`uv sync --locked` 成功，`scripts/check-fast.sh` 通過，`scripts/check-docs.sh` 通過，沒有留下檔案。沒有跑測試。
- 這 5 行和 #38（feat/stats-py314）README 裡的那段逐字相同。
- c246355 的 README 沒有重複的建議。相關的只有機器學習那節第 428 行：「若要驗證樣本外表現，請明確要求使用未參與訓練與選參的資料」。兩者講的不是同一件事。

**和你說的不一樣的地方**：範圍文件（#38 上的 `docs/statistics_leaderboard_integration.md` 第 36–40 行）引用的是 README 的**節名**「使用樣本外驗證與最佳化」，不是錨點連結。這一節在 c246355 上存在，缺的是建議那段。另外這份範圍文件本身也還不在 `main` 上。所以 PR body 寫成：引用要等這個 PR 合併後才成立，而那份文件會隨 #38 進來。

## README PR body 全文

檔案：`2026-11-08-round27-readme-pr/pr-readme-final-evaluation-data.md`。第一行 `Title:` 是 PR 標題。base 是 `main`，head 是 `docs/readme-final-evaluation-data`。

````markdown
Title: docs(readme): recommend reserving final evaluation data until the strategy is settled

## Summary

Adds one paragraph to the README, at the end of "使用樣本外驗證與最佳化", after the parameter optimization paragraph. It recommends setting aside a period of data as a final evaluation before development starts, and using it only after the rules, features and parameters are chosen. If the strategy is changed after looking at that period's results, the period is no longer an independent final test, and later results should be treated as part of development.

## This is advice to users, not a system rule

- The paragraph says so itself: the system does not check whether a user does this, and does not verify that any period of data has not been used.
- It also says that developing on the most recent data is fine, and that a reserved test period or out-of-sample evidence is not a condition for a result to be included in comparisons.
- No code, schema, tool description or check changes. The diff is five added lines in `README.md`.

## Why it is needed

The statistics integration document on #38 (`docs/statistics_leaderboard_integration.md`, "No holdout requirement for ranking") points to this recommendation by its README section, "使用樣本外驗證與最佳化". That section is on `main`, but the recommendation is not, so the reference only holds once this PR is merged. That document is not on `main` yet either; it arrives with #38.

This PR does not depend on #38 or on any of the statistics split PRs, and can be merged on its own.

## Verification

This repository has no CI, so nothing on GitHub runs these checks. Checks were run locally on this branch merged into `main`, verified at `main` c246355:

- `scripts/check-fast.sh`: passes (includes the Markdown and local link checks).
- Documentation only; no tests were run.

The branch is based on a77babf, and upstream has since revised the README substantially. With full history, the paragraph lands at the end of the same section, after the optimization paragraph and before "研究機器學習訊號".

🤖 Generated with [Claude Code](https://claude.com/claude-code)
````
