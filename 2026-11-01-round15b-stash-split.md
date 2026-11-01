# 第 15 輪（15b）：團隊報告修正、stash 拆成三條分支、check-full

日期：2026-11-01

## 結果摘要

- 團隊報告的四點修正已推到 session-notes，commit `5eb4bfb`。
- stash 已拆成三組，三條分支都已推上 origin：
  - A 組 → `feat/stats-py314`（PR #38），head `8b4336e`
  - B 組 → `feat/stats-public-api`，head `eb28060`
  - C 組 → `feat/stats-demo-evidence`，head `2c05fd0`
- **stash 已 drop。** 遠端備份 `wip/stash-610e612-backup` 也已照指示刪除。
  - 另一份內容相同的遠端副本 `origin/wip/stash-610e612`（`53d7ed2`）是更早的 session 推的，這輪沒有刪。要不要刪由你決定。
- validate_run 的 ×2 重複計算已經不存在。
- check-full（只在 `feat/stats-py314` @ `8b4336e` 跑一次）：全綠，7480 passed、32 deselected，exit 0。

## 任務 1：團隊報告

- 報告其實已經推上去了（`bb7c403`），不是只在本機。上一輪的說明有誤。
- 四點修正 commit 在它上面，推到 `5eb4bfb`：
  - 公開模組改成七個（periods、performance、breakeven、sharpe、comparison、plateau、benchmark），不提 `_validation` 和 `_scaling`。
  - 訓練資料綁定寫明上游 PR #136（分支 `feat/ml-training-dataset-binding`，仍是 OPEN）。
  - 2b 節的例子寫出兩個門檻：只排規則時 2.807，涵蓋全部 40 個候選時 3.227；照上游推薦的 family 用法，顯示的門檻偏寬鬆。
  - 基準一節改成結論：產品基準只在進場付成本，不可比的主因是標的不同和超額報酬定義不同。「成本規則是否統一」移出待決清單。

## 任務 2：套用 stash 和解衝突

在 `c5fff7a` 上套用 stash 得到 5 個內容衝突、4 個 modify/delete：

- `src/tradingdev/domain/statistics/__init__.py`（內容衝突）
  - 保留 `c5fff7a` 的 docstring，加一句指向 `__all__` 和 `docs/statistics_public_api.md`。
  - 接上 stash 的 `__all__` 匯出（約 100 行）。舊 docstring 沒有回來。
  - `__all__` 的 40 個名稱全部存在且可匯入。
- `docs/statistics_leaderboard_integration.md`（內容衝突）
  - 不用 stash 的版本，取 `c5fff7a` 的重寫版。
  - 在「Purpose and Status」第一段結尾重新加上指向 `statistics_public_api.md` 的那句。
- `src/tradingdev/domain/statistics/performance.py` 和它的測試（各一個內容衝突）
  - stash 要加的「`periods_per_year` 拒絕 NaN 和 inf」已經被 `723aec3` 做掉了：`performance.py` 改用 `sharpe._annualisation`，它拒絕非有限值、非正值、布林和字串。
  - 測試 `test_statistics_performance.py:171` 已涵蓋 0、負值、NaN、±inf、True、"365"。
  - 所以兩個檔案都取 `c5fff7a` 的版本，stash 這部分沒有收進任何分支。這和指示的「保留」不同，原因是保留會變成第二份重複的檢查。
  - 和 `_scaling` 的驗證路徑沒有重疊：`_scaling` 只處理量級縮放，不檢查 `periods_per_year`。
- `ARCHITECTURE.md`（內容衝突）
  - stash 要加的模組說明列，`c5fff7a` 已經有了，所以取 `c5fff7a` 的版本。
  - 之後 A 改成本結論那句，B 在同一列加公開 API 的連結（見下）。
- modify/delete 四檔：`demo_output/METHODS.md`、`demo_output/kd_inference.md`、`scripts/demo_statistics.py`、`scripts/validate_run.py`
  - 這些在 `c5fff7a` 已被刪除（會議決議 demo 不進 PR #38）。
  - 取 stash 的版本，全部只放進 C 組。
  - `demo_statistics.py` 和 `validate_run.py` 的檔案權限恢復成原本的 100644。

## 任務 3：三組的去向

**A 組 → `feat/stats-py314`（PR #38），兩個 commit，fast-forward，沒有 force**

- `9c1abc8` test：KD 釘值 fixture
  - `tests/domain/statistics/fixtures/kd_btcusdt_1h_2024/`（README、兩個 parquet、`run.json`、`extract.py`，共約 37 KB）
  - `tests/domain/statistics/kd_fixture.py`、`test_statistics_kd_fixture.py`
  - 測試裡原本「比對 `demo_output/kd_inference.md`」的 `TestCommittedReport` 搬到 C 組，因為那份 markdown 不在 PR #38。
- `8b4336e` docs：成本結論和 PR #136
  - `ARCHITECTURE.md`：把「成本規則是否統一尚待決定」改成已有結論（主因是標的與超額報酬定義，先統一命名）。
  - `benchmark.py` docstring：同樣的結論。
  - `docs/statistics_leaderboard_integration.md`：Open Item 2 寫明 PR #136。原本這份文件裡沒有「成本規則尚待決定」那句，只有 `ARCHITECTURE.md` 有。
- 合計 10 個檔案，+337 / −5。
- 四個釘值測試在 fixture 上通過（366 天、Sharpe −7.565103143673017、traded notional 5014735.715506879、成本占比 0.863481526386825）。

**B 組 → `feat/stats-public-api`（從 `c5fff7a` 出發），兩個 commit**

- `9a8825d` feat：`__init__.py` 的 `__all__`，加上 `test_statistics_public_api.py`（檢查每個名稱都能匯入，且公開 API 文件有提到它）。
- `eb28060` docs：`docs/statistics_public_api.md`、integration 文件的指路句、`ARCHITECTURE.md` 統計模組那一列加上公開 API 文件的連結。
- 合計 5 個檔案，+423 / −2。check-fast 通過，statistics 測試 659 passed。

**C 組 → `feat/stats-demo-evidence`（從 `8b4336e` 出發，因為要用 A 組的 fixture），一個 commit**

- `2c05fd0`：`scripts/demo_statistics.py`、`scripts/validate_run.py`、`demo_output/METHODS.md`、`demo_output/kd_inference.md`、`tests/scripts/test_demo_statistics.py`、`tests/scripts/test_validate_run.py`，以及從 A 搬來的 `tests/scripts/test_demo_kd_report.py`。
- 合計 7 個檔案，+1938。check-fast 通過，目標測試 27 passed，測試沒有留下輸出檔。

**validate_run 的 ×2 檢查**

- 已經沒有 `total_volume * 2 * (fees + slippage)`。
- 現在用 `breakeven.summarize_breakeven(...).traded_notional` 推導成本，它是進場加出場名目金額，每邊只算一次。
- 兩個回歸測試覆蓋：「每邊只算一次」和「不使用 total_volume」。
- 這輪不需要修。

**drop 前的核對**

- 逐一確認 stash 的 20 個檔案都落在某條分支上，內容是原樣或上面寫的解法。沒有遺漏。

## 任務 4：審公開 API 文件（對照 `c5fff7a`）

簽名和呼叫範例都和程式一致。改了文件、沒改程式的地方：

- DSR 那條：原本寫「過度修正、偏向拒絕真實優勢」。改成兩個相反效果、淨方向未經量測，並寫明不要把 DSR 說成保守的。這和 `3e2600a` 的 docstring 一致。
- 新增 `_scaling` 之後的失敗路徑：
  - `plateau_summary`、`plateau_scores`、`plateau_grid`：metric 跨度超出 float 範圍時 `ValueError`，要回報成「需要重新縮放」，不是「沒有 plateau」。
  - `PlateauSummary.spikiness`：未定義或比值超出 float 時都是 `None`。
  - `deflated_sharpe_ratio`：trial Sharpe 過度分散、門檻不是有限值時 `ValueError`；PSR 未定義，或 `N >= 2` 但 trial Sharpe 少於兩個時回傳 `None`。
- 輸入檢查補上：布林、數字字串、NumPy 整數當次數、數值型時間戳都會被拒絕，不會自動轉換。
- 序列化表補上 `plateau_scores` 回傳的是 `PlateauScore` 的 tuple。
- 序列化表的每一列都用實際程式跑過 `json.dumps(dataclasses.asdict(...))` 核對。

## check-full

- 上一個 session 啟動的 check-full 在 codespace 重啟時被中斷，沒有結果。這輪在新的 worktree（detached `8b4336e`，自己的 `.venv`）重跑，整輪只有這一次完整結果。
- 方法：Python 包裝程式先 fork，子行程 `setsid`、SIGINT 和 SIGQUIT 設回預設再 exec；沒有加 pytest 外掛。
- 結果：
  - `7480 passed, 32 deselected, 74 warnings in 3366.64s (0:56:06)`，exit 0，沒有失敗或錯誤。
  - pytest 的 `rootdir` 是該 worktree，HEAD `8b4336e`；收集 7512 項，選中 7480 項。
  - pytest 行程的 `SigIgn=0x1001000`，SIGINT（0x2）沒有被忽略。
  - 和第 14 輪（7476 passed）相比多 4 項，是 A 組新增的 KD fixture 測試。

## 待決事項（都是你的或團隊的決定）

- 範圍措辭請 Kuan-Lun 確認。
- 兩個「超額報酬」的命名（產品端和統計端）。
- 是否刪除 `origin/wip/stash-610e612`。
- 公開 API 文件和套件 docstring 有不少重複，要不要只留一處當契約。
- B 組和 C 組要不要開 PR、何時開。這輪沒有開任何 PR，也沒有在 PR #38 留言。
