# 2026-11-01 第 15 輪：環境收尾與團隊報告

## 結果

- 團隊報告：`2026-11-01-status-for-team.md`（bb7c403）。PyMarkdown 依 check-fast 的設定檢查通過；依指示沒有跑 check-full。
- 本機兩條 round14 分支已經刪除。
- 主工作樹的修改已經 stash；本機 `feat/stats-py314` 已 fast-forward 到 c5fff7a，工作樹乾淨。
- 沒有碰 PR #38 的程式碼，沒有留言，也沒有同步上游。

## 任務 1：round14 分支

- `git diff round14/merge-sync origin/feat/stats-py314`：差異只有 `docs/statistics_leaderboard_integration.md` 新增的 8 行，沒有其他差異。
  - 比對對象用的是 origin 而不是本機的 `feat/stats-py314`，因為本機那條當時還停在 610e612。
- `round14/merge-sync-2` 就是 c5fff7a。
- 兩條都已刪除：merge-sync 原本在 0ceb3f7，merge-sync-2 原本在 c5fff7a。
- **備份推送那一步：沒有做。** 我收到的第 14 輪指示裡沒有「第 0 步：把 round14/merge-sync 推到 origin」這一項，所以不是做了但失敗。

## 任務 2：主工作樹的未提交修改（共 20 檔，已 stash）

stash 訊息：`main-worktree WIP on feat/stats-py314@610e612 (pinned KD fixture, validate_run/demo pinning, public API doc+__all__, periods_per_year finite check); stashed 2026-11-01 for user review, do not drop`

狀態欄：S 表示已暫存，W 表示未暫存，U 表示未追蹤。

| 檔案 | 狀態 | 改動 |
| --- | --- | --- |
| `ARCHITECTURE.md` | 修改（W） | 新增 `domain/statistics/` 一列的模組說明 |
| `demo_output/METHODS.md` | 修改（S） | KD 輸入改成以 SHA-256 釘死的 pickle，不再依 mtime 挑「最新」的 |
| `demo_output/kd_inference.md` | 修改（S） | 加上來源 pickle 的 SHA-256 |
| `docs/statistics_leaderboard_integration.md` | 修改（W） | 加一句指向 `statistics_public_api.md` |
| `scripts/demo_statistics.py` | 修改（S＋W） | 暫存：釘死 KD_SOURCE 與雜湊、新增 `--kd-pickle`。未暫存：`display_path`，報告不寫入本機絕對路徑 |
| `scripts/validate_run.py` | 修改（S） | 路徑改成必填參數，不再用 glob 挑最新的檔案 |
| `src/tradingdev/domain/statistics/__init__.py` | 修改（W） | 新增約 100 行公開 API 匯出（`__all__`） |
| `src/tradingdev/domain/statistics/performance.py` | 修改（W） | `periods_per_year` 拒絕 NaN 和 inf，原本只拒絕 ≤ 0 |
| `tests/domain/statistics/test_statistics_performance.py` | 修改（W） | 上一列的測試：0、−1、NaN、inf 都要拒絕 |
| `tests/domain/statistics/fixtures/kd_btcusdt_1h_2024/README.md` | 新增（S）＋修改（W） | KD fixture 說明 |
| `…/kd_btcusdt_1h_2024/equity.parquet` | 新增（S） | fixture 權益曲線 |
| `…/kd_btcusdt_1h_2024/trades.parquet` | 新增（S） | fixture 交易紀錄 |
| `…/kd_btcusdt_1h_2024/run.json` | 新增（S） | fixture 的回測設定與來源 |
| `…/kd_btcusdt_1h_2024/extract.py` | 新增（S）＋修改（W） | 從 pickle 產生 fixture 的腳本 |
| `tests/domain/statistics/kd_fixture.py` | 新增（S） | fixture 載入器 |
| `tests/domain/statistics/test_statistics_kd_fixture.py` | 新增（S）＋修改（W） | 四個釘值的測試，以及和報告的比對 |
| `tests/scripts/test_validate_run.py` | 新增（S） | validate_run 的測試 |
| `docs/statistics_public_api.md` | 新增（U） | 給 MCP 介接者的公開 API 交接文件，269 行 |
| `tests/domain/statistics/test_statistics_public_api.py` | 新增（U） | `__all__` 和文件一致的測試 |
| `tests/scripts/test_demo_statistics.py` | 新增（U） | demo 選擇與引用 KD 輸入的測試 |

看起來是 `feat/stats-pinned-fixtures` 的工作，加上之後的一部分公開 API 工作。去留由你決定。

## 任務 4：環境

- 每條本機分支的 commit 都已存在於遠端（origin 或 upstream），沒有只存在本機的 commit。
  - 有幾條分支在 origin 上沒有同名分支：`docs/leaderboard-rewrite`、`feat/optimization-trials`、`feat/stats-sync-upstream`、`feat/stats-sync-upstream-2`、`round7/stats-review-fixes`、`round8/validate-run-and-docs`。它們的 commit 都已經包含在遠端的歷史裡。
- **例外：stash 只存在這台機器上。** 這是依你的指示放的；如果 codespace 被刪除，stash 會一起消失。
- 沒有殘留行程，scratchpad 的暫存檔已清除。
- `git status`：`On branch feat/stats-py314`，up to date with `origin/feat/stats-py314`，`nothing to commit, working tree clean`。
- `git worktree list`：只剩 `/workspaces/tradingdev c5fff7a [feat/stats-py314]`。

## `_scaling` 的問題

你問的情境是「數值約 1e200、標準差約 1e-200」。這種輸入在 float64 裡不存在：

- 1e200 附近相鄰兩個浮點數的間距（ulp）約是 1.7e184。
- 所以只要數值不是全部相同，離散度至少是 1e184 等級；全部相同時，Sharpe 會明確回傳 None。

一般化來說：

- 非常數輸入的「最大量級 ÷ 離散度」上限約是 2^53。實測隨機 2 萬組，最壞是 2^53.0。
- 把離散度縮到 [0.5, 1) 之後，量級最多約 2^53，落在安全範圍 2^60 以內。
- 因此單一個 2 的冪次一定足夠，不會出現「兩個目標需要不同倍率」的情況，也不需要走 ValueError。

實測結果：

- 數值約 1e200、相對雜訊 1e-3：結果和精確有理數計算到第 12 位都相同。
- 數值約 1e200，加上幾個 1e-200 量級的值：結果和同樣形狀但量級 1 的輸入相同。

另外看到一個不同的限制，和 `_scaling` 無關：

- 如果離散度只有 1 個 ulp（Sharpe 約 1e17），算出的值會比精確值小約 √2。
- 量級 1.0 的普通輸入，完全不經過縮放，也有同樣的誤差。這是 float64 計算平均和標準差時的抵銷誤差。
- 程式不會偵測這種情況，會直接回傳數字。實務上報酬序列不會只有 1 個 ulp 的離散度，所以沒有修，只記在這裡。

## 和指示不一致的地方

- 你寫「八個統計模組」；公開模組是七個（periods、performance、sharpe、comparison、benchmark、breakeven、plateau），另外有兩個內部模組（_validation、_scaling）。團隊報告寫的是七個公開模組，加上兩個內部模組。
