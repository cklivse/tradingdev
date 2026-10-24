# 2026-10-24 第三輪：驗證 PR 差異、改寫 PR 草稿

分支 `feat/stats-py314`，HEAD `610e612`。本輪只動 `session-notes` 分支的文件，程式碼分支沒有變動，也沒有跑 check-full。

## 任務 1：PR 差異

- `git fetch upstream main`：upstream/main = `3fa0852`
- `git merge-base HEAD upstream/main`：`3fa0852`

`git diff --stat upstream/main...HEAD` 的完整輸出：

```text
 demo_output/METHODS.md                             | 639 +++++++++++++++++
 demo_output/comparison_forest.png                  | Bin 0 -> 135990 bytes
 demo_output/kd_equity.png                          | Bin 0 -> 90717 bytes
 demo_output/kd_inference.md                        |  46 ++
 demo_output/plateau_demo.png                       | Bin 0 -> 206787 bytes
 demo_output/plateau_gridindex.png                  | Bin 0 -> 132935 bytes
 demo_output/plateau_gridindex_table.md             |  16 +
 demo_output/plateau_table.md                       |  16 +
 docs/statistics_leaderboard_integration.md         | 169 +++++
 pyproject.toml                                     |   1 +
 scripts/demo_plateau.py                            | 250 +++++++
 scripts/demo_statistics.py                         | 566 +++++++++++++++
 scripts/validate_run.py                            | 299 ++++++++
 src/tradingdev/domain/statistics/__init__.py       |   1 +
 src/tradingdev/domain/statistics/benchmark.py      | 302 ++++++++
 src/tradingdev/domain/statistics/breakeven.py      | 228 ++++++
 src/tradingdev/domain/statistics/comparison.py     | 507 +++++++++++++
 src/tradingdev/domain/statistics/performance.py    | 182 +++++
 src/tradingdev/domain/statistics/periods.py        | 135 ++++
 src/tradingdev/domain/statistics/plateau.py        | 673 ++++++++++++++++++
 src/tradingdev/domain/statistics/sharpe.py         | 482 +++++++++++++
 .../domain/statistics/test_statistics_benchmark.py | 361 ++++++++++
 .../domain/statistics/test_statistics_breakeven.py | 204 ++++++
 .../statistics/test_statistics_comparison.py       | 606 ++++++++++++++++
 .../statistics/test_statistics_performance.py      | 157 ++++
 tests/domain/statistics/test_statistics_periods.py | 162 +++++
 tests/domain/statistics/test_statistics_plateau.py | 788 +++++++++++++++++++++
 tests/domain/statistics/test_statistics_sharpe.py  | 563 +++++++++++++++
 tests/mcp/test_optimization_failed_trials.py       | 142 ++++
 uv.lock                                            | 130 +++-
 30 files changed, 7622 insertions(+), 3 deletions(-)
```

結論：差異裡沒有 upstream 的檔案。`src/` 底下的 `mcp/`、`app/`、`domain/backtest/`、`domain/ml/` 都沒有出現。超出統計模組的只有三處：

- `tests/mcp/test_optimization_failed_trials.py`：本分支 `74184aa` 新增的測試檔，upstream 沒有這個檔。它是測試，不是 `src/tradingdev/mcp/` 的程式。
- `pyproject.toml` 多一行：`arch>=8.0.0`。
- `uv.lock` +130/-3：
  - 新增 arch 8.0.0 和它的依賴：statsmodels、patsy、formulaic、interface-meta、wrapt。
  - 刪掉的 3 行是 httpcore2 對 h11、truststore，以及 pexpect 對 ptyprocess 的 platform marker 被簡化。它們的上層依賴本來就帶有相同的 marker，解析結果等價（上一輪的審查已確認），差異來自 uv 版本。

## 任務 2：PR 草稿

`pr_draft.md` 已改寫，四個章節的結構保留：

- **開頭：** 新增分支說明。`feat/stats-py314` 是 PR 的來源；`feat/stats-on-latest` 停在 `814b05a`，是退路。
- **標題：** 改成以統計模組為主，同步到 Python 3.14 / pandas 3 是附帶的。
- **「這個分支做了什麼」：** 補上四個缺口各自原本的錯誤結果，以及 4c 選擇的行為、理由，和引擎勝率只算已平倉交易的差異（刻意的，不是 bug）。
- **新章節「plateau 契約已在真實資料上驗證」：** 寫明這次證明 `1b51608` 的行為在真實系統上成立。
- **「順帶發現」：** 新增兩條：preflight 只試跑每個範圍的第一個值（`preflight_worker.py:232-293`），以及零交易要看 `total_trades`、不能看原因碼（`metrics.py:201-208、236-240、355-356、382-386`）。逾時那段原本附的「先前的說法」也拿掉了。
- **「還沒做的事」：**
  - 移走 trial scope 的驗證，以及四個已修好的缺口。
  - 把「統計模組沒有對外出口」移到最前面。
  - 新增「`trials_from_metrics` 擋不住樣本太少」：最佳組合 (9, 10) 只有 2 筆交易。這項留作後續。
  - 保留三項仍然成立的：KD 數字沒有測試把關、demo 依 mtime 挑選輸入、validate_run 沒有自動化測試。
- **數字：** 檢查結果更新為 `610e612` 的版本：check-full 4243 passed，統計測試 319 passed。

沒有開 PR。
