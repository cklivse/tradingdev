<!--
marp: true
theme: tradingdev
size: 16:9
paginate: true
lang: zh-Hant
title: TradingDev｜統計模組
description: 以架構為框架，說明 domain/statistics 各模組回答的問題、選用方式與目前邊界
-->

<!-- _class: cover -->

# 統計模組

從回測輸出到可以檢驗的結論

架構是框架，`domain/statistics` 是主體。

*草稿 · 2026 年 11 月。統計程式都還在 PR 上，尚未合併到 main。*

<!--
本簡報引用的統計程式以各分支 2026-11-09 的 head 為準：
stats/1-foundation c8154a8、stats/2-breakeven fc62da5、stats/3-plateau dfb383d、stats/4-sharpe bede2d0、stats/5-comparison a216dc4。
主線引用 Kuan-Lun/tradingdev main ad2fb75。
-->

---

<!-- _class: compact -->

## 閱讀路線

| 章節 | 主題 | 內容 |
| --- | --- | --- |
| 01 | [架構：統計模組的位置](index.html#3) | 四層分工、為何只在 domain、和績效管線的界線 |
| 02 | [統計模組](index.html#8) | 七個公開模組各回答什麼問題，以及怎麼選 |
| 03 | [現況與邊界](index.html#21) | PR 拆分、介面缺口、兩個 issue 與修不掉的限制 |

<!-- _footer: "點選章名跳轉。方向鍵換頁，P 開啟講者模式。" -->

---

<!-- header: "01　架構" -->
<!-- _class: chapter -->
<!-- _header: "" -->

## 01　架構：統計模組的位置

四層分工沿用主線架構；這一章只補統計模組需要的部分。

<!--
來源：https://github.com/Kuan-Lun/tradingdev/blob/ad2fb75/ARCHITECTURE.md
-->

---

<!-- _class: compact -->

## 四層分工

| 層 | 位置 | 和統計模組的關係 |
| --- | --- | --- |
| MCP | `mcp/server.py`、`mcp/tools/`、`mcp/workers/` | 協定轉換與背景工作；沒有匯入統計模組 |
| Application | `app/` | 協調策略、計畫、工作與結果查詢；沒有匯入統計模組 |
| Domain | `domain/` | 策略、回測、績效與排名邏輯；**統計模組加在這裡** |
| Adapters | `adapters/` | SQLite、檔案、程序、CLI 與 Dashboard；沒有匯入統計模組 |

<!-- _footer: "模組責任、訊號流程與 MCP 工具分組見[介紹簡報的「01 系統架構」](https://github.com/Kuan-Lun/tradingdev/blob/ad2fb75/docs/talks/tradingdev-introduction/slides.md)，這裡不重複。" -->

<!--
「沒有匯入」是在五個統計分支的 head（c8154a8、fc62da5、dfb383d、bede2d0、a216dc4）以 git grep 檢查 src/tradingdev/app、mcp、adapters 對 domain.statistics 的引用，結果皆為零。
來源：https://github.com/Kuan-Lun/tradingdev/blob/ad2fb75/ARCHITECTURE.md
-->

---

<!-- _class: compact -->

## 為什麼統計模組只在 domain

- **輸入由呼叫端提供**：權益曲線、時間戳、交易紀錄、報酬序列或試驗列，都以參數傳入
- **不讀 run、artifact 或快取**：各模組的 docstring 都寫明這一點
- **只依賴計算套件**：匯入只有標準函式庫、NumPy、pandas，以及 bootstrap 用的 `arch`
- **可以交叉核對引擎**：`performance` 不讀引擎的 `metrics`，只從原始輸出重算

主線架構提醒 domain 並非全是純計算（crawlers、ML stores 會做 I/O）；統計模組不做 I/O。

<!--
各模組 docstring：「never read runs, artifacts, or caches」（periods、sharpe、comparison、benchmark）、「never reads jobs, runs, artifacts, or caches」（plateau）、「computed only from trade records」（breakeven）、「never consults an engine's metrics dictionary」（performance）。
匯入清單是對九個檔案逐一列出 import 的結果。
來源：https://github.com/cklivse/tradingdev/blob/bede2d0/src/tradingdev/domain/statistics/performance.py
來源：https://github.com/cklivse/tradingdev/blob/bede2d0/ARCHITECTURE.md（domain/statistics 一列，只在 #209 的分支上）
來源：https://github.com/Kuan-Lun/tradingdev/blob/ad2fb75/ARCHITECTURE.md（「這是目前實作的責任分組，尚未形成全面的依賴反轉」一段）
-->

---

<!-- _class: compact -->

## 和主線績效管線的界線

| | 主線績效管線 | 統計模組 |
| --- | --- | --- |
| 資料來源 | 引擎觀察值，保存為 performance artifacts | 呼叫端傳入的序列與紀錄 |
| 無風險利率 | `risk_free_rate` 可設定 | 一律為零 |
| `max_drawdown` | K 棒層級的比例 | 金額；比例另見 `max_drawdown_pct` |
| 交易統計 | 已平倉交易 | 所有提供的紀錄 |
| 保存與查詢 | 發佈、MCP 查詢、排行榜 | 不保存，未接入發佈或 MCP |

同名欄位不能互相套用。

<!--
ARCHITECTURE.md（#209 分支）：「其摘要採零無風險利率、金額型 max_drawdown，交易統計計入所有提供的紀錄，不能直接套用已保存績效指標的同名欄位契約。」
performance_artifacts.md：「Bar-level max_drawdown is a nonnegative fraction」；交易數、勝率等「refer to closed trades」。
來源：https://github.com/cklivse/tradingdev/blob/bede2d0/ARCHITECTURE.md
來源：https://github.com/Kuan-Lun/tradingdev/blob/ad2fb75/docs/performance_artifacts.md
-->

---

<!-- _class: compact -->

## 介紹簡報引用的架構版本之後的變化

介紹簡報的架構章引用 `9e502ce`（2026-11-07）。到 main `ad2fb75` 有 136 個 commit，其中 6 個修改 ARCHITECTURE.md（+31／−5）。

| 變化 | 章節 |
| --- | --- |
| 新增 `tooling/environment.py`、`tooling/llm_check.py` | Repository 開發工具 |
| CLI 改稱「直接回測 CLI」；`tradingdev-codex` 對話入口走 MCP 流程 | 研究需求、執行回測 |
| `ArtifactService.read_download` 與 MCP `ArtifactDownloads` 的短效網址 | 保存與查詢結果 |
| 新增「可見對話紀錄」（`ConversationService`） | 新章節 |

四層的責任表沒有變。`domain/statistics` 那一列只在 #209 的分支上，main 還沒有。

<!--
git rev-list --count 9e502ce..ad2fb75 = 136；git log 9e502ce..ad2fb75 -- ARCHITECTURE.md 為 0eb1370、cf66214、2893047、0b21e81、3be69ff、2312d6d。
來源：https://github.com/Kuan-Lun/tradingdev/compare/9e502ce...ad2fb75
-->

---

<!-- header: "02　統計模組" -->
<!-- _class: chapter -->
<!-- _header: "" -->

## 02　統計模組

七個公開模組、兩個私有模組；每頁回答「它回答什麼問題」。

<!--
所有模組都是獨立計算，尚未接入績效發佈或 MCP 結果查詢。
-->

---

<!-- _class: compact -->

## 模組地圖

| 模組 | 回答的問題 | 所在 PR |
| --- | --- | --- |
| `periods` | 權益曲線怎麼切成日和月 | #206 |
| `performance` | 從原始輸出重算，這次回測表現如何 | #209 |
| `breakeven` | 成本吃掉多少、勝率夠不夠 | #207 |
| `sharpe` | 這個 Sharpe 可信嗎、挑出來的還算嗎 | #209 |
| `comparison` | A 真的比 B 好嗎 | 第 5 包，尚未開 PR |
| `plateau` | 最佳參數是高原還是尖峰 | #208 |
| `benchmark` | 相對買進持有多了什麼 | 第 5 包，尚未開 PR |

私有的 `_validation`、`_scaling` 在 #206；`comparison`、`benchmark` 依賴 `sharpe` 與 `periods`。

<!--
來源：https://github.com/Kuan-Lun/tradingdev/pull/206（拆分表）
-->

---

<!-- header: "02　統計模組　／　periods" -->
<!-- _class: compact -->

## `periods`：權益曲線怎麼切成日和月

**問題**：引擎給的是逐根 K 棒的權益；Sharpe 和配對比較需要日或月報酬。

- 期間邊界一律是 UTC 日曆；naive 時間戳視為 UTC，帶時區的先轉成 UTC
- 每個觀測歸入時間戳標籤所在的期間：以開盤時間標記的 23:00 小時棒歸當天
- 沒有觀測的期間直接省略，不補零（週末、資料缺口）
- 拒絕數字時間戳：數字沒有單位，`1_704_067_200` 會被當成奈秒
- 報酬需要權益全為正；從零起算的累積損益曲線沒有報酬基礎

入口：`period_returns`、`period_pnl`、`period_closing_equity`、`to_utc_index`

<!--
來源：https://github.com/cklivse/tradingdev/blob/c8154a8/src/tradingdev/domain/statistics/periods.py（模組 docstring、to_utc_index、period_returns）
-->

---

<!-- header: "02　統計模組　／　performance" -->
<!-- _class: compact -->

## `performance`：從原始輸出重算一次績效

**問題**：不看引擎的 `metrics`，只用權益、時間戳和交易紀錄，這次回測表現如何？

| 類別 | `PerformanceSummary` 欄位 |
| --- | --- |
| 報酬 | `total_pnl`、`total_return` |
| 回撤 | `max_drawdown`（金額）、`max_drawdown_pct` |
| 波動 | `daily_pnl_std`、`monthly_pnl_std`（金額，`ddof=1`） |
| 風險調整 | `sharpe_ratio`：日報酬，乘 `sqrt(periods_per_year)` |
| 交易 | 筆數、勝負、`win_rate`、`profit_factor` |

沒有年化報酬與報酬率波動欄位。`periods_per_year` 預設 365；權益不全為正時，報酬類欄位為 `None`。

<!--
DEFAULT_PERIODS_PER_YEAR = 365.0。「Return-based figures are None unless every equity value is strictly positive」。
來源：https://github.com/cklivse/tradingdev/blob/bede2d0/src/tradingdev/domain/statistics/performance.py
-->

---

<!-- header: "02　統計模組　／　breakeven" -->
<!-- _class: compact -->

## `breakeven`：成本吃掉多少，勝率還夠不夠

**問題**：照這個盈虧比，勝率要多高才打平？交易成本占多少？

- 打平勝率 `p* = L / (W + L)`；`win_rate_edge` 是實際勝率減 `p*`，只計有輸贏的交易
- 周轉計入進出兩腿的名目金額；未平倉交易只計進場腿
- 成本是 `fee` 欄位加總，得出 `cost_per_turnover`；有 `capital` 時另算 `annual_cost_drag`
- 評估期間由呼叫端給 `start`、`end`，一年以 365.25 天計

**限制**：引擎若把成本併入 `net_pnl` 而沒寫進 `fee`，這裡會低估成本。

<!--
入口 summarize_breakeven；DAYS_PER_YEAR = 365.25。
來源：https://github.com/cklivse/tradingdev/blob/fc62da5/src/tradingdev/domain/statistics/breakeven.py
-->

---

<!-- header: "02　統計模組　／　sharpe" -->
<!-- _class: compact -->

## `sharpe`（一）：這個 Sharpe 有多不確定

**問題**：Sharpe 是點估計；換一段樣本，它可能差多少？

- `sharpe_ratio`：平均除以樣本標準差（`ddof=1`），無風險利率為零，乘 `sqrt(periods_per_year)`
- `sharpe_interval_outcome`：stationary bootstrap 百分位區間，預設 1000 次重抽、95%
- 區塊長度取報酬與報酬平方兩個自動估計的較大者，保留波動聚集
- 至少 `MIN_BOOTSTRAP_OBSERVATIONS` = 20 期；一年的月報酬一定不夠，`sharpe_interval_outcome` 回傳 `IntervalUnavailable` 說明原因

**限制**：自動區塊長度不保證名目覆蓋率；平方根年化不消除頻率差異，只比較同頻率的比率。

<!--
來源：https://github.com/cklivse/tradingdev/blob/bede2d0/src/tradingdev/domain/statistics/sharpe.py（模組 docstring、sharpe_interval_outcome、IntervalUnavailable）
-->

---

<!-- _class: compact -->

## `sharpe`（二）：是真的嗎？從 N 個裡挑最好的還算嗎？

| 函式 | 回答 | 比較的門檻 |
| --- | --- | --- |
| `probabilistic_sharpe_ratio`（PSR） | 真實 Sharpe 超過基準的機率 | 呼叫端給的 `benchmark_sr`，每期單位 |
| `deflated_sharpe_ratio`（DSR） | 挑出的最佳者，贏得過純運氣嗎 | N 個無技能試驗的期望最大 Sharpe |

- PSR 計入偏態與峰態，但假設報酬獨立，沒有序列相關項；DSR 沿用這個假設
- `n_trials` 必須含失敗、被丟掉的試驗；只傳存活數會修正不足，而且不報錯
- 網格試驗高度相關，對門檻有兩個相反的效果，淨方向未知

<!--
DSR 的門檻 SR*_0 = std(SR_n) * ((1 - gamma) * Z^-1(1 - 1/N) + gamma * Z^-1(1 - 1/(N * e)))，gamma 為 EULER_MASCHERONI。
來源：https://github.com/cklivse/tradingdev/blob/bede2d0/src/tradingdev/domain/statistics/sharpe.py（probabilistic_sharpe_ratio、deflated_sharpe_ratio）
-->

---

<!-- header: "02　統計模組　／　comparison" -->
<!-- _class: compact -->

## `comparison`：A 真的比 B 好嗎

**問題**：兩個策略跑在同一段行情上，差距是真的還是雜訊？

- 同一行情的策略共享衝擊；差的變異數是 `var(A) + var(B) − 2 cov(A, B)`
- `difference_interval`：先對齊共同期間，以同一組區塊索引重抽 A 與 B，回傳差、區間與 p 值
- 區塊長度由差的 jackknife influence 估計，不用 A、B 各自的
- 個別區間不重疊代表差異顯著；重疊不代表不顯著
- 預設 2000 次重抽；共同期間至少 20 期

**只比較樣本外報酬**。期間、標的或成本假設不同的策略不可比，統計修不了。

<!--
第 5 包尚未開 PR，引用分支 head。
來源：https://github.com/cklivse/tradingdev/blob/a216dc4/src/tradingdev/domain/statistics/comparison.py（模組 docstring、align_returns、difference_interval_outcome）
-->

---

<!-- header: "02　統計模組　／　plateau" -->
<!-- _class: compact -->

## `plateau`：穩定高原還是運氣好的尖峰

**問題**：最佳參數旁邊的參數也表現好嗎？

- 鄰域用網格索引的 Chebyshev 距離，`DEFAULT_RADIUS` = 1，不用原始參數距離
- 平台分數是鄰居的平均指標，不含自己；孤立尖峰拿不到自己的分數
- 主要統計 `metric_gap`：最佳試驗與平台最佳試驗的指標差；`spikiness` 為次要
- 失敗試驗留在軸上成為缺點；`trials_from_metrics` 回報 `dropped_count`
- 超過 `MAX_LOCAL_DIMENSIONS` = 3 個參數時鄰域不再局部，標記 `dimension_warning`

**限制**：整個參數區擬合同一種行情時會出現假高原，不能取代樣本外驗證。

<!--
用最佳化的 trial/{index}/train scope 建的平台是樣本內，須標明。平台分數只能在同一次 run、同一 radius 內比較。
來源：https://github.com/cklivse/tradingdev/blob/dfb383d/src/tradingdev/domain/statistics/plateau.py（模組 docstring、trials_from_metrics、PlateauSummary）
-->

---

<!-- header: "02　統計模組　／　benchmark" -->
<!-- _class: compact -->

## `benchmark`：相對買進持有多了什麼

**問題**：策略相對於單純持有標的，多出了什麼？和它怎麼一起變動？

- `buy_and_hold_returns`：用呼叫端給的價格建買進持有報酬，不計成本
- `compare_to_benchmark`：beta、alpha、主動報酬、追蹤誤差、資訊比率、上下行捕獲率
- 「贏不贏買進持有」本身是 Sharpe 差，交給 `comparison.difference_interval`
- 交易同一標的時，beta 量的是平均淨曝險，不是系統風險

**名稱**：「超額報酬」保留給總報酬差；每期差的年化平均叫 `active_return_annualised`。這不是產品基準（`domain/benchmark.py` 的 `BENCHMARKS`）。

<!--
產品基準依資產類別固定標的，只在進場收成本；本模組用呼叫端的價格、不計成本。兩者數字不同主要來自標的與報酬差的定義。
來源：https://github.com/cklivse/tradingdev/blob/a216dc4/src/tradingdev/domain/statistics/benchmark.py（模組 docstring、BenchmarkComparison）
-->

---

<!-- header: "02　統計模組　／　私有模組" -->
<!-- _class: compact -->

## 為什麼需要 `_validation` 和 `_scaling`

| 模組 | 要防的問題 | 做法 |
| --- | --- | --- |
| `_validation` | 型別註記在執行時不強制：`True` 會變 1.0，`"0.01"` 會變 1% | 拒絕布林、字串與其他物件；計數與 `seed` 須為內建 `int` |
| `_scaling` | 四階動差在偏差約 `1e77` 時溢位；離散極小時平方下溢 | 幅度超過 `2**60` 或離散小於 `2**-60` 時，以 2 的冪次縮放 |

- `_validation` 對不支援的型別報 `ValueError`，不默默轉成數字；NumPy 轉換失敗等錯誤仍照原樣拋出
- `_scaling` 對正常浮點數是精確縮放，但不保證統計量有限；`sharpe`、`plateau` 使用它

<!--
來源：https://github.com/cklivse/tradingdev/blob/c8154a8/src/tradingdev/domain/statistics/_validation.py（模組 docstring、real_array、positive_int、seed_value）
來源：https://github.com/cklivse/tradingdev/blob/c8154a8/src/tradingdev/domain/statistics/_scaling.py（模組 docstring、_LOWER、_UPPER）
-->

---

<!-- header: "02　統計模組　／　怎麼選" -->
<!-- _class: compact -->

## 怎麼選：從問題到方法

| 想回答的問題 | 用這個 | 輸入要求 |
| --- | --- | --- |
| Sharpe 有多不確定 | `sharpe_interval_outcome` | 至少 20 期報酬 |
| Sharpe 是否大於某個基準 | `probabilistic_sharpe_ratio` | 每期單位的基準 |
| 從 N 次試驗挑出的最佳者 | `deflated_sharpe_ratio` | 全部試驗數，含失敗 |
| A 是否比 B 好 | `difference_interval` | 同一行情的樣本外報酬 |
| 最佳參數是否穩定 | `plateau_summary` | 完整網格列，含失敗 |
| 打平勝率與成本 | `summarize_breakeven` | 交易紀錄與評估起訖 |
| 相對持有的共同變動 | `compare_to_benchmark` | 同一組 K 棒、同頻率 |

<!--
報酬序列由 periods.period_returns 產生。各列的輸入要求出自對應函式的 docstring（見前面各頁來源）。
-->

---

<!-- _class: compact -->

## 三條不可混用的規則

1. **DSR 和 Bonferroni 不套在同一個數字上。** DSR 修正 Sharpe 家族（回測與最佳化試驗）；排行榜的 `required_t_stat` 以 Bonferroni 修正 IC t 統計量。兩者回答的問題、候選母體與獨立性假設都不同；並列時標明指標、修正方法與母體。
2. **樣本內序列不做配對比較。** 調過參數的樣本內報酬，比的是誰過擬合得更徹底，不是誰更好。
3. **門檻掃描不是參數曲面。** 每個門檻存成一個候選；`parameter_axes` 只含 horizon、IC window 與 quantile 數，曲面的警語與平台分析不適用。

<!--
來源：https://github.com/cklivse/tradingdev/blob/bede2d0/src/tradingdev/domain/statistics/sharpe.py（deflated_sharpe_ratio 的「Two selection corrections」）
來源：https://github.com/cklivse/tradingdev/blob/a216dc4/src/tradingdev/domain/statistics/comparison.py（「Compare out-of-sample returns only」）
來源：https://github.com/Kuan-Lun/tradingdev/blob/ad2fb75/docs/ml_research.md（Method families：「A threshold sweep is stored as one candidate per level」）
來源：https://github.com/Kuan-Lun/tradingdev/blob/ad2fb75/src/tradingdev/app/ml_service.py
-->

---

<!-- header: "03　現況與邊界" -->
<!-- _class: chapter -->
<!-- _header: "" -->

## 03　現況與邊界

統計程式都還在 PR 上；main 沒有 `domain/statistics`。

<!--
git ls-tree ad2fb75 src/tradingdev/domain/ 沒有 statistics。PR 狀態以 2026-11-09 的 GitHub API 查詢為準。
-->

---

<!-- _class: compact -->

## 拆分狀態

| PR | 分支 | 內容 | 狀態 |
| --- | --- | --- | --- |
| #205 | `docs/readme-final-evaluation-data` | README：保留最終評估資料的建議 | open |
| #206 | `stats/1-foundation` | `_validation`、`_scaling`、`periods` | open |
| #207 | `stats/2-breakeven` | `breakeven` | open |
| #208 | `stats/3-plateau` | `plateau` | open |
| #209 | `stats/4-sharpe` | `sharpe`、`performance`，新增 `arch` | open |
| — | `stats/5-comparison` | `comparison`、`benchmark` | 尚未開 PR |

第 5 包的基底是 `b62ac97`，還不含 #209 目前的 head。#38 仍 open。

<!--
2026-11-09 GitHub API：#205–#209 皆 open、非 draft、未合併；head 依序為 a68f1e4、c8154a8、fc62da5、dfb383d、bede2d0。#38 head 005854f。
來源：https://github.com/Kuan-Lun/tradingdev/pulls
-->

---

<!-- _class: compact -->

## 為什麼拆

- **審查負擔**：2026-10-27 會議認為 #38 太大，難以審查（32 個檔案，+9404／−3）
- **依賴決定基底**：第 1 包不依賴其他統計模組；2、3、4 依賴 1；5 依賴 4 與 1
- **合併順序**：#206 → #207、#208、#209 不限順序 → 第 5 包
- **程式不改寫**：程式與測試從 `feat/stats-py314` 逐檔複製；#38 多出的是文件

<!--
#38 多出的部分：__init__.py 的完整套件導覽、方法文件，以及 ARCHITECTURE／README 段落。
來源：https://github.com/Kuan-Lun/tradingdev/pull/206（Why this is split into five PRs）
-->

---

<!-- _class: compact -->

## 介面上還缺的東西

統計模組要的輸入，和 main 保存的 `ScopeObservations` 對不上：

| 統計模組需要 | main `ad2fb75` 的現況 |
| --- | --- |
| `periods_per_year`：有限正數 | 不在 `ScopeObservations`；在 `BacktestConfig`，可為 `None`，預設 `None` |
| `equity_curve`：每個元素都是有限數字 | 型別是 `list[float or None]`，元素可為 `None` |
| `timestamps`：必填、嚴格遞增 | 型別是 `list[str] or None`，整個欄位可為 `None` |

統計模組遇到 `None` 會報錯，不猜值；但 `summarize_performance` 省略 `periods_per_year` 時會用 365。

<!--
表中 "or" 代表型別聯集（原文為 float | None、list[str] | None）。
來源：https://github.com/Kuan-Lun/tradingdev/blob/ad2fb75/src/tradingdev/domain/performance/artifacts.py（ScopeObservations）
來源：https://github.com/Kuan-Lun/tradingdev/blob/ad2fb75/src/tradingdev/domain/backtest/schemas.py（BacktestConfig.periods_per_year）
來源：https://github.com/cklivse/tradingdev/blob/c8154a8/src/tradingdev/domain/statistics/periods.py（equity_series）
來源：https://github.com/cklivse/tradingdev/blob/bede2d0/src/tradingdev/domain/statistics/performance.py（DEFAULT_PERIODS_PER_YEAR）
-->

---

<!-- _class: compact -->

## #189：搜尋規模沒有跟著代表結果

- 跨策略排名時，每個策略只派一組代表結果；最佳化 run 的預設 scope 是 `test`
- `RunCandidate` 沒有欄位說明這組參數是從多少組選出來的
- **擋住的是 DSR**：`deflated_sharpe_ratio` 需要 `n_trials` 和試驗 Sharpe 的離散度，兩者在選代表結果時就丟了
- **資料其實存在**：最佳化 run 的 performance bundle 保存每組的 `trial/{index}/train` scope

issue 自己寫明：記下搜尋規模只讓選擇幅度可以稽核，不建立 holdout。

<!--
來源：https://github.com/Kuan-Lun/tradingdev/issues/189
-->

---

<!-- _class: compact -->

## #190：分不出訊號是誰算的

- `evaluate_prediction`（後端用模型算訊號）和 `evaluate_signal`（呼叫端提供序列）寫出形狀相同的紀錄
- 帶 `model_id` 時，`training_dataset_id` 都來自 artifact，與序列是誰算的無關
- **擋住的是配對比較的資格判斷**：帶 `model_id` 的候選，目前只憑紀錄能放進 `difference_interval` 的是零筆
- issue 的提議是例如 `signal_source` 欄位；名稱與位置由擁有者決定

<!--
docs/ml_research.md：「the row's fields do not say which entry point wrote it」。
來源：https://github.com/Kuan-Lun/tradingdev/issues/190
來源：https://github.com/Kuan-Lun/tradingdev/blob/ad2fb75/docs/ml_research.md
-->

---

<!-- _class: compact -->

## 修不掉的限制：配對紀錄不是 holdout

記下訓練與評估資料集的配對，只能描述關係，不能建立 holdout。

| `training_dataset_id` 與 `dataset_id` | 能說明什麼 |
| --- | --- |
| 相等 | 只有後端用該 artifact 產生訊號時，才代表分數是樣本內 |
| 不相等 | 什麼都證明不了：身分也涵蓋期間與程式指紋，不同版本仍可能重疊 |
| 空值 | 未知，包括綁定出現之前寫入的所有紀錄 |

同理，用最佳化訓練 scope 建出的平台是樣本內。#205 建議策略定案前保留最終評估資料。

<!--
來源：https://github.com/Kuan-Lun/tradingdev/blob/ad2fb75/src/tradingdev/domain/ml/leaderboard.py（LeaderboardEntry.training_dataset_id）
來源：https://github.com/Kuan-Lun/tradingdev/blob/ad2fb75/docs/ml_research.md（「A different value does not establish a holdout either way」）
來源：https://github.com/cklivse/tradingdev/blob/dfb383d/src/tradingdev/domain/statistics/plateau.py（Integration contract）
來源：https://github.com/Kuan-Lun/tradingdev/pull/205
-->

---

<!-- _class: compact -->

## 目前不能說的事

- 統計模組**沒有**接入績效發佈、MCP 結果查詢或排行榜
- main **沒有** `domain/statistics`；本簡報引用的程式都在 PR 分支上
- `comparison` 與 `benchmark` **還沒有** PR
- `arch` 依賴只在 #209 加入，main 沒有

<!--
來源：https://github.com/cklivse/tradingdev/blob/bede2d0/ARCHITECTURE.md（「也未接入績效發佈或 MCP 結果查詢」）
來源：https://github.com/cklivse/tradingdev/blob/bede2d0/pyproject.toml
-->

---

<!-- _class: closing -->
<!-- _header: "" -->

## 統計模組的定位

回答「這個結果可信到什麼程度」，不取代研究設計：
樣本外資料要事先保留，選擇的規模要事先記錄。

<!--
plateau：「plateau analysis cannot replace out-of-sample validation」；comparison：「That is an experimental design problem that no statistic can repair」。
-->

---

<!-- _class: references -->
<!-- _header: "" -->

## 參考資料

- [系統架構（main `ad2fb75`）](https://github.com/Kuan-Lun/tradingdev/blob/ad2fb75/ARCHITECTURE.md) · [#209 分支的版本](https://github.com/cklivse/tradingdev/blob/bede2d0/ARCHITECTURE.md)
- 程式：[`periods`](https://github.com/cklivse/tradingdev/blob/c8154a8/src/tradingdev/domain/statistics/periods.py) · [`breakeven`](https://github.com/cklivse/tradingdev/blob/fc62da5/src/tradingdev/domain/statistics/breakeven.py) · [`plateau`](https://github.com/cklivse/tradingdev/blob/dfb383d/src/tradingdev/domain/statistics/plateau.py) · [`sharpe`](https://github.com/cklivse/tradingdev/blob/bede2d0/src/tradingdev/domain/statistics/sharpe.py) · [`performance`](https://github.com/cklivse/tradingdev/blob/bede2d0/src/tradingdev/domain/statistics/performance.py) · [`comparison`](https://github.com/cklivse/tradingdev/blob/a216dc4/src/tradingdev/domain/statistics/comparison.py) · [`benchmark`](https://github.com/cklivse/tradingdev/blob/a216dc4/src/tradingdev/domain/statistics/benchmark.py)
- [績效產物](https://github.com/Kuan-Lun/tradingdev/blob/ad2fb75/docs/performance_artifacts.md) · [ML research](https://github.com/Kuan-Lun/tradingdev/blob/ad2fb75/docs/ml_research.md)
- PR：[#205](https://github.com/Kuan-Lun/tradingdev/pull/205) · [#206](https://github.com/Kuan-Lun/tradingdev/pull/206) · [#207](https://github.com/Kuan-Lun/tradingdev/pull/207) · [#208](https://github.com/Kuan-Lun/tradingdev/pull/208) · [#209](https://github.com/Kuan-Lun/tradingdev/pull/209) · [#38](https://github.com/Kuan-Lun/tradingdev/pull/38)
- Issue：[#189](https://github.com/Kuan-Lun/tradingdev/issues/189) · [#190](https://github.com/Kuan-Lun/tradingdev/issues/190)

<!--
版型沿用 docs/talks/tradingdev-introduction/theme.css（ad2fb75，原檔複製，未修改）。
-->
