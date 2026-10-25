# 2026-10-25 第 6 輪：PR #38 審查十項中 statistics 套件的六項

## 範圍與狀態

這輪處理 PR #38 審查（Codex 審查，Kuan-Lun 轉達）的第 1、5、6、7、9、10 項。修改範圍只在 `src/tradingdev/domain/statistics/` 和對應的測試，另外改了 `demo_output/METHODS.md` 的 §2.13。

validate_run.py 的第 2–4 項、第 8 項，以及其他文件問題，都留到下一輪。

- **分支：** `feat/stats-py314` 已從 `610e612` push 到 `ff7933e`，PR #38 的 head 隨之更新為 `ff7933e`，狀態仍是 OPEN。
- **commit：** 五個，見文末。
- **不受最小修改或向後相容限制：**
  - 新增了可選參數 `difference_interval(_outcome)(…, block_size=None)`。
  - 第 1 項與第 7 項會改變 `difference_interval` 回傳的 `block_size`、區間與 `p_value`。

### 工作樹

主工作樹 `/workspaces/tradingdev` 有與這輪無關、尚未 commit 的修改，例如 staged 的 fixture 檔、`statistics/__init__.py` 和 `performance.py`。其中包括另一份對第 9 項的修正，不是這輪做的。

依 AGENTS.md，這輪沒有碰那些修改，所有工作都在 scratchpad 的獨立 worktree 裡做，使用分支 `round7/stats-review-fixes`（從 `origin/feat/stats-py314` 建立），再以 `HEAD:feat/stats-py314` push。

因此：
- 本機的 `feat/stats-py314` ref 仍停在 `610e612`，落後 origin 5 個 commit。
- 主工作樹未 commit 的 `performance.py` 修改，和這輪的第 9 項修正會在同一段程式衝突。
- 整合時建議以這輪的 `_annualisation` 版本為準。新的 `block_size` 是參數，不影響 `__init__.py` 匯出的名稱。

## 開工前的重現

六項都先在 `610e612` 上用審查的原腳本重現，數字完全一致：

| 項目 | 結果 |
| --- | --- |
| 1 | raw：block 2，p = 0.002；residual：block 44，p = 0.26；精確 AR(1) 檢定 p = 0.4892017166151429 |
| 5 | `ValueError: Mixed timezones detected` |
| 6 | 兩種 peak 下 std 都是 1.3597399555105182e-16；peak 1.0 的 spikiness 是 2206304218569236.0；peak 0.7 的 spikiness 是 0.8164965809277261，plateau winner 是 (0,1)，grid_distance = 1 |
| 7 | 0.0011231185740203497 0.009210713400425613 0.1 |
| 9 | nan nan、inf inf |
| 10 | 兩種情況都是 years、annual_traded_notional、annual_cost 全為 nan |

## 各項修法與回歸測試

### 第 1 項：配對 bootstrap 的區塊長度（`ad5d959`，與第 7 項同一個 commit）

**選擇的路：** 兩條路都做了。

1. **自動推導：** 用「差額統計量的 jackknife 影響值」估計區塊長度。
   - 定義為 $I_t=(n-1)(\hat\Delta-\hat\Delta_{(-t)})$，其中 $\hat\Delta_{(-t)}$ 是從 a、b 同時去掉第 t 期後的 `statistic(a) - statistic(b)`。
   - 對這個序列做 Politis–White 估計（`optimal_block_length`），結果無條件進位，至少為 1。
   - 任一 leave-one-out 統計量無定義時（例如只有一個交易日、去掉後變成常數，Sharpe 為 None），改用原始差額 `a - b`。
2. **手動指定：** 新增 `block_size` 參數，給定時就略過估計，原樣使用並回報。

**理由：**
- 審查要求「讓區塊選擇反映目標統計量的依賴」。jackknife 影響值就是統計量影響函數的經驗版本，對任何平滑統計量（mean、Sharpe、Sortino 等）都通用，不必知道統計量的形式。
- 對平均數而言，$I_t$ 恰好是 $a_t-b_t$ 減去常數。arch 的估計量對位置與尺度不變，所以這和直接用差額序列等價。審查者另外驗證了符號與尺度不影響結果。
- 但 jackknife 對**不平滑**的統計量（中位數、分位數、最大回撤）不一致，而且要多算 $2n$ 次統計量，成本是 O(n²)。所以仍提供手動介面。docstring 寫明了：
  - 什麼時候**必須**指定：不平滑或昂貴的統計量。
  - 不指定的後果：區塊可能太短，使區間變窄、p 值變小，正是要防止的假陽性。區塊太長只損失一些精確度。
- 實測成本（審查者測量，Sharpe，reps = 2000）：
  - n = 730：jackknife 0.16 s
  - n = 3000：1.2 s
  - n = 10000：11.8 s
  - 一般日報酬下與 bootstrap 本身相當。目前唯一的呼叫端是 demo，約一年日資料、3 對。
- `interval_table` 刻意維持各欄估計值取最大，沒有改。它回答的是各自的精確度，不是差額。審查另外提到的「Sharpe 區塊只依原始報酬估計」只是未確認的疑慮，不在這輪範圍。

**修正後的審查案例：** raw 和 residual 都得到 block 44、p ≈ 0.26，95% CI 跨 0，不再判為顯著。改用 Sharpe 統計量也一樣（44、0.258）。

**回歸測試**（`TestDifferenceDependence`）：
- **共同雜訊案例：** 照審查腳本以 seed 2 生成。斷言：
  - raw 與 residual 的 block size 相同且大於 20；
  - 兩者的 p 值相同，且大於 0.05；
  - CI 跨 0。
- **block size 估計值：** 等於 `ceil(optimal_block_length(d - mean(d)))`。
- **指定 `block_size`：** 原樣回報，結果與另一個統計量物件相同；計數器確認沒有呼叫 jackknife（呼叫次數小於 2·reps + 10，jackknife 需要 2000 次）。
- **fallback：** leave-one-out 無定義時改用 `a - b`。
- **無效值：** `block_size` 為 0、`True`、`2.0` 都 raise，包括 overlap 不足時的 wrapper。

### 第 5 項：跨日光節約時間的 aware timestamps（`4194fdb`）

**原因：** 這是 `to_utc_index` 從一開始（`6a2d787`）就有的問題，**不是** 4b 造成的。4b 的時區檢查在 `comparison.align_returns`，檢查的是兩條 series 的 index，這輪沒有動。

**修法：**
- 非 `DatetimeIndex` 的輸入：字串與 object 陣列逐元素用 `pd.Timestamp` 解析，aware 的值各自轉成 UTC。其他 dtype（datetime64、整數 epoch）照舊走 `pd.DatetimeIndex`。
- 同一序列中 naive 與 aware 混用仍然 raise，訊息是 "timestamps mix timezone-naive and timezone-aware values"。
- 2 維輸入 raise `ValueError`。

**為什麼最後沒有照建議用 `pd.to_datetime(..., utc=True)`：** 第一版確實這樣做，但獨立審查重現了兩個退化：
1. 它只從第一個值推斷一種格式，所以原本接受的不同格式字串會被拒絕，例如 `["2024-01-01", "2024-01-01 01:00"]`，或 `isoformat()` 在微秒為 0 時省略小數的情況。
2. `utc=True` 會把 object 陣列裡的 datetime64 或字串默默當成 UTC，與 aware Timestamp 混用時不會報錯。

逐元素解析解決了這兩個問題。

**影響範圍：** period_pnl、period_returns、summarize_performance、buy_and_hold_returns 都經由 `equity_series → to_utc_index`，已逐一加測試。

**回歸測試：**
- **跨 DST：** 柏林 2024-03-31 的 +01:00/+02:00，用字串、固定 offset 的 Timestamp、zone Timestamp 三種形式，斷言 UTC 3/30、3/31 的 PnL 是 `[0.0, 1.0]`。zone Timestamp 在舊碼也會通過，作為對照。
- **其他入口：** performance 與 buy-and-hold 各有一個跨 DST 案例。
- **混用：** 六種 naive/aware 混用（Timestamp、字串，naive 在前或在後，object 陣列中的 datetime64 或字串搭配 aware）都以 `match` 驗證是時區混用的訊息。
- **格式不一的字串：** 三種格式不一的 naive 字串照舊接受。
- **2 維輸入：** raise。

### 第 6 項：常數鄰域的浮點誤差（`e6fb87a`）

**修法：** 相對容差 `_RELATIVE_TOLERANCE = 1e-12`。
- 鄰居 metric 的 `ptp <= 1e-12 × max|v|` 時視為零離散：std 回報 0.0，spikiness 為 None。
- 鄰域分數與最高分相差在相對 1e-12 以內時視為平手，由最早的 trial 勝出。尺度取「比較的兩個分數」的絕對值較大者。
- metric 本身是輸入，仍然只在完全相等時才算平手。

**審查修正：** 第一版的尺度用的是「所有候選分數的最大絕對值」。審查重現了問題：網格遠處若有 -1e8 的失敗區，容差會被放大到 2e-5，吃掉真實的 2e-7 領先。已改成兩兩比較的尺度。

**回歸測試**（`TestInexactConstantNeighbourhood`，用 0.7）：
- 完全平坦的網格：winner 是 (0,0)，grid_distance 0，metric_gap 0，std 0.0，spikiness None。
- peak 1.0：std 0.0，spikiness None。
- 正向對照 1：真實的 1e-9 離散保留，std > 0、spikiness 不是 None。
- 正向對照 2：真實的 2e-10 分數領先仍會勝出。
- 遠處 -1e8 不會放大容差。

### 第 7 項：p-value 與 percentile CI（`ad5d959`）

**選擇：** 統一判定定義，而不是移除保證。

**修法：** p 值改為反轉 CI 所用的同一個 `np.quantile` 線性內插分位數函數。
- 取「分位數仍 ≤ 0 的最高 level」和「分位數已 ≥ 0 的最低 level」，計算 $p=\min(1,2\min\{\cdot\})$。
- 因此「區間不含 0」恰好等於「p < 1 − confidence」，對任何 reps 與 confidence 都成立。只有兩者剛好相等時可能受浮點捨入影響。

**有限重抽樣的限制寫進了 docstring：** p < 2/(B−1) 時只是兩個最極端抽樣之間的內插。

**審查者的驗證：** 用 4000 組 draws（B = 1..29，包含 0 的 ties、重複值、全部同側、全為 0）× 1999 個 α，與 `np.quantile` 暴力比對，不一致為 0。

**審查的 reps = 20 案例：** p 從 0.1 變為 0.0105，與全為正的 CI 一致。

**METHODS.md §2.13** 依新定義改寫，包括：
- 區塊長度規則、jackknife 公式、必須手動指定的情況與後果；
- p 值定義、一致性保證、有限重抽樣的限制；
- 已移除的舊定義；
- 行號。

§2.13 的表格與 `comparison_forest.png` 要重跑 KD 回測才能更新，這輪沒有重跑，已在文中註明「尚未重新產生」。

**回歸測試**（`TestPValueMatchesInterval`）：
- 審查的 reps = 20 案例。
- reps ∈ {1, 2, 5, 20, 41, 200} × confidence ∈ {0.5, 0.9, 0.95, 0.99}，每組 25 個 seed，斷言一致性。
- 所有抽樣同側時 p = 0；兩序列相同時 p = 1。

### 第 9 項：非有限的年化期數（`723aec3`）

**修法：** `summarize_performance` 改用 `sharpe._annualisation`（內部經 `_finite`）驗證，與 sharpe.py 一致：必須是有限的正實數，且不能是 bool。

**回歸測試：** 對 0、−365、NaN、+inf、−inf、`True`、`"365"` 都斷言 raise。使用的是審查那條本來有有限 Sharpe 的曲線。

### 第 10 項：缺失的評估日期（`ff7933e`）

**修法：** `_utc_timestamp` 遇到 NaT 時先 raise "start is missing" 或 "end is missing"，之後才做 end > start 的檢查。

**回歸測試：** start 或 end 分別為 None、NaT、NaN、`""`，共 8 個案例。

## 測試能抓到問題的驗證

- **對照原始碼：** 把新的測試目錄放到 `610e612` 的原始碼上執行（用 `PYTHONPATH` 指向舊的 src，並確認匯入的是舊模組）。六項各自都有測試失敗：第 1 項 3 個、第 5 項 4 個、第 6 項 2 個、第 7 項 8 個、第 9 項 4 個、第 10 項 8 個，以及 `block_size` 參數驗證。
- **審查修正補的測試：** 格式不一的字串、遠處大值不放大容差，這兩組在 `610e612` 上本來就會通過。它們防的是第一版修正造成的退化，在那一版上會失敗（審查者已重現）。
- **混用測試：** 在舊碼上失敗，是因為訊息不同（舊碼的 ValueError 來自 pandas）。

## 檢查

- **迭代：** `uv run pytest tests/domain/statistics/ -q`，最終 390 passed。
- **呼叫端：**
  - `tests/mcp/test_optimization_failed_trials.py`：3 passed。
  - `scripts/demo_plateau.py` 重跑後 `plateau_table.md` 沒有變化；PNG 的位元不同，已還原。
- **每個中間 commit：** 用獨立 worktree 跑 statistics 測試、ruff、mypy，全部通過：
  - `ad5d959`：356 passed
  - `4194fdb`：371 passed
  - `e6fb87a`：376 passed
  - `723aec3`：382 passed
- **check-fast：** commit 前執行，exit 0。git hooks 仍未安裝，依先前決定沒有動。
- **check-full：** 所有審查修正都套用並 commit 之後，在 `ff7933e` 跑了一次，執行前開了 keepalive：
  - exit 0；
  - 4314 passed，12 deselected（`live_llm`），74 warnings；
  - pytest 耗時 50 分 03 秒；
  - 執行期間工作樹沒有修改，結束後沒有殘留的 pytest 程序。
- **未涵蓋：**
  - 沒有重跑需要回測的 KD demo，所以 §2.13 的表格與 forest 圖的新數字未驗證。
  - 沒有執行真實 LLM 情境：沒有修改 MCP schema 或模型整合。
  - `tests/scripts/` 不在這個 base 上，沒有執行。

## 開發階段審查

由未參與實作、獨立上下文的 reviewer 唯讀審查完整差異。

**已重現並修正：**
1. plateau 平手容差的尺度。
2. `to_utc_index` 對格式不一的字串產生退化。
3. object 陣列中 naive 與 aware 混用被默默接受。
4. 2 維輸入改成 raise `TypeError`。

以上都已補回歸測試。

**疑慮：** jackknife 的 O(n²) 成本。docstring 已寫明，並提供 `block_size` 繞過，沒有其他修改。

**審查者確認沒有問題的部分：**
- `_percentile_p_value` 的邊界；
- jackknife 的符號、尺度與 fallback；
- `interval_table` 行為不變；
- breakeven、performance 的驗證；
- 其他 `to_utc_index` 輸入（epoch、datetime64、date、Series、None、空序列）與舊版一致；
- §2.13 的行號與公式。

套用修正後由我自行複查：statistics 測試、mypy、ruff、輸入類型掃描，以及每個中間 commit 的測試。依 AGENTS.md，沒有再安排第二輪 reviewer。

## commit

| commit | 內容 |
| --- | --- |
| `ad5d959` | fix(statistics): fit paired bootstrap blocks to the difference（第 1、7 項） |
| `4194fdb` | fix(statistics): accept aware timestamps across a DST change（第 5 項） |
| `e6fb87a` | fix(statistics): treat rounding-level plateau differences as ties（第 6 項） |
| `723aec3` | fix(statistics): reject non-finite periods_per_year in summarize_performance（第 9 項） |
| `ff7933e` | fix(statistics): reject missing breakeven period dates（第 10 項） |

第 1 與第 7 項放在同一個 commit：兩者改寫的是同一段 `difference_interval_outcome` 推論契約，在 docstring 與 METHODS §2.13 中相互交錯，commit message 已說明。

`test_statistics_performance.py` 同時有第 5 與第 9 項的測試，已按 hunk 分開放進各自的 commit。

## 留給下一輪

- **validate_run.py：** 第 2–4 項。
- **文件：** 第 8 項，以及審查列出的文件問題。另外，這輪的程式修改讓 METHODS.md 其他節，以及 `docs/statistics_leaderboard_integration.md` 中指向 `plateau.py`、`periods.py`、`breakeven.py`、`comparison.py` 的行號偏移了。這輪只更新了 §2.13。
- **重跑 demo：** 更新 §2.13 的表格與 `comparison_forest.png`。§2.12 中「區間不同但 block size 都是 2」那段說明也要一起核對。
- **本機整合：** 本機的 `feat/stats-py314` 落後 origin 5 個 commit，主工作樹未 commit 的 `performance.py` 修改會與第 9 項衝突。
