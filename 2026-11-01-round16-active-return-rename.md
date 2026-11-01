# 第 16 輪：`excess_return_annualised` 改名為 `active_return_annualised`

日期：2026-11-01

## 結果摘要

- `BenchmarkComparison.excess_return_annualised` 已改名為 `active_return_annualised`，沒有保留舊名別名。
- `feat/stats-py314`（PR #38）：commit `988cf54`，已 fast-forward push（`8b4336e..988cf54`，沒有 force push）。
- `feat/stats-public-api`：用 **merge** 接上 `988cf54`（不是 rebase），merge commit `6b7b689`，加上文件 commit `3f29c9e`，已 push（`eb28060..3f29c9e`）。用 merge 是因為這條分支已經 push 過，rebase 需要 force push，沒有授權。
- 四個釘值逐位相同，改名沒有動到任何數字。
- check-full（`988cf54`，乾淨 worktree）：7480 passed，32 deselected，0 failed（58 分 48 秒，exit 0）。

## 改了哪些檔案

`feat/stats-py314` 上 3 個檔案（+40 / −31）：

- `src/tradingdev/domain/statistics/benchmark.py`
  - 欄位名、`compare_to_benchmark` 的公式說明與 docstring、`information_ratio` 的描述、內部變數。
  - 模組頂端比較兩個基準的那段改寫，並加上命名約定。
- `tests/domain/statistics/test_statistics_benchmark.py`：4 處斷言改用新欄位名，期望值不變。
- `ARCHITECTURE.md`：「與產品基準」一段改寫，另加「命名約定」一條。

`feat/stats-public-api` 上：`docs/statistics_public_api.md` 原本沒有寫出欄位名。在「Benchmark and Comparison Alignment」一節末尾加一段（+8 行）：`active_return_annualised`（原名 `excess_return_annualised`）是逐期差的平均年化，也是 `information_ratio` 的分子；它不是產品報告在基準旁顯示的 excess return，adapter 要分開標示。merge 後 `check-docs`（22 份文件）和 `check-fast` 都通過。

## 命名約定（寫成本套件採用的約定，不是團隊已同意）

- 模組說明：The convention this package adopts in benchmark comparisons: "excess return" is reserved for the total-return difference … the annualised mean of the per-period differences is the active return.
- ARCHITECTURE.md：「本套件在基準比較上採用的約定是，『excess return』（超額報酬）保留給總報酬差……逐期差的平均年化叫 active return。兩者回答不同問題，數值不能互換。」
- 加上「在基準比較上」這個範圍，是因為 repo 裡還有第三種 excess return：`domain/backtest/metrics.py` 的 `excess_return_adjustment` 和 confirmation 的「夏普比率（每單位波動的超額報酬）」指的是超過無風險利率的報酬。沒有範圍限定的話，「保留給總報酬差」會和它們衝突。

## 搜尋範圍

- 全樹搜 `excess_return_annualised`：只有 `statistics/benchmark.py` 和它的測試，改完後全樹找不到舊名。
- 沒有改的 excess return：
  - 上游報告的 `excess_return`（`adapters/reporting/tables.py`、`html.py`、README、`docs/reports.md`、`docs/performance_artifacts.md`）：都是總報酬差，正是約定保留給 excess return 的意思。
  - `excess_return_adjustment`（無風險利率換算）：第三種意思，和這次無關。
- `docs/statistics_public_api.md` 原本沒有寫出這個欄位名，所以沒有可改名的地方；改為加一段命名提醒（見上）。
- `feat/stats-demo-evidence` 沒有引用這個欄位，照指示沒有碰。
- 小差異：指示寫「上游 `domain/benchmark.py` 用 excess return 指總報酬差」。實際上 `domain/benchmark.py` 只定義基準本身；總報酬差是在 `adapters/reporting/tables.py` 算的。約定文字因此寫成「報告在產品基準旁呈現的」總報酬差。

## 四個釘值（`988cf54`，`repr` 逐位比對 `8b4336e` 測試裡的常數）

- 天數：366 == 366
- Sharpe：-7.565103143673017 == -7.565103143673017
- traded notional：5014735.715506879 == 5014735.715506879
- 成本占比：0.863481526386825 == 0.863481526386825

## 審查

- 獨立 reviewer 檢查改名完整性、事實正確性、有無行為改變、有無寫成「團隊已同意」。沒有可重現的問題。
- 採納兩個措辭建議：約定加上「在基準比較上」的範圍；刪掉重複的「兩者回答不同問題，數值不能互換」。

## check-full

- 第一次（15:15 UTC 開始）在 pytest 76%（`tests/e2e/test_workflow_verifier.py`）被 SIGTERM 終止，exit 241。之前沒有任何測試失敗。
  - 找不到送出 SIGTERM 的來源：核心沒有 OOM 紀錄，兩個審查子代理沒有 kill 指令，程式裡對 process group 送訊號的地方都先核對 group 屬於自己的子行程。
  - 因為沒有完整結果，不算數，不據此 push。
- 第二次（同一個 worktree、同一個 `988cf54`）：7480 passed，32 deselected，74 warnings，0 failed，耗時 3528 秒（58 分 48 秒），16:50 UTC 結束，exit 0。用同一個 fork + setsid + SIG_DFL wrapper，沒有 PYTEST_ADDOPTS 外掛。

## 團隊報告

`2026-11-01-status-for-team.md`：

- 交付狀態一節補上三條分支的切分與後兩條不另開 PR 的原因。
- PR #38 的檔案數改為目前的數字（原本寫 23 個，第 15 輪 A 組加入後已是 30 個）。
- 第 4 節的表格與「先統一命名」改用新欄位名，並說明這是統計套件自己採用的約定，還沒和產品端談過。
- 指示寫公開 API 文件「269 行」；那是 stash 裡的版本，第 15 輪任務 4 補完後是 292 行，團隊報告寫 292。

## 沒有做的事

沒有開 PR、沒有在 PR #38 或 issue 留言、沒有刪 `origin/wip/stash-610e612`、沒有碰 `feat/stats-demo-evidence`、沒有同步上游。
