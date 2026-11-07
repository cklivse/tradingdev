# 第 21 輪：第 1–5 包和最新上游 main 的合併檢查

日期：2026-11-07。只做檢查，沒有修改或 push 任何程式分支，GitHub 上也沒有動作。

上游 main 現在是 35a2409，比第 20 輪的基底 b62ac97 多了 254 個 commit。
statistics 相關檔案、pyproject.toml 和 uv.lock 上游都沒動過。

## 結果

在暫存 worktree 裡把每一包 merge 進 upstream/main 35a2409，再跑 statistics 測試和 `scripts/check-fast.sh`。

| 分支 | merge 衝突 | 測試 | check-fast |
| --- | --- | --- | --- |
| stats/1-foundation | 無 | 36 passed | 通過 |
| stats/2-breakeven | 無 | 88 passed | 通過 |
| stats/3-plateau | 無 | **collection error** | **失敗（mypy）** |
| stats/4-sharpe | 無 | 146 passed | 通過 |
| stats/5-comparison | 無 | 303 passed | 通過 |

## 第 3 包的問題

`tests/mcp/test_optimization_failed_trials.py` 匯入 `tradingdev.domain.strategies.loader.StrategyLoader`，
上游 aa2d3f4（11-06）把它搬到了 `tradingdev.adapters.execution.strategy_factory.StrategyFactory`，
`resolve_execution` 的介面沒變。

試改後（3 行：import 和兩處 `StrategyLoader()` → `StrategyFactory()`），130 passed，check-fast 通過。
這個修正還沒 commit。#38 裡也有同一個檔案，收尾 merge main 時也要做同樣的修改。

## 其他發現

- 上游新增了 `src/tradingdev/domain/benchmark.py`（產品用的基準，依資產類別固定標的）。
  第 5 包的 `statistics/benchmark.py` 是研究用的比較，模組 docstring 已經明確區分兩者，沒有名稱衝突。
  但 docstring 只列出 BTC/USDT 和 S&P 500，上游 947a372（11-07）又加了台股 `^TWII`，這段描述已經不完整。
