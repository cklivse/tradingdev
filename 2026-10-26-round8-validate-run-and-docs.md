# 2026-10-26 第 8 輪：PR #38 審查的 validate_run.py 三項與文件問題

## 範圍與狀態

這輪處理 PR #38 審查（Codex，Kuan-Lun 轉達）剩下的部分：

- `scripts/validate_run.py` 的第 2、3、4 項；
- 第 8 項（排行榜整合文件的跨 horizon 分組）；
- 「正式檢查與文件」一節列的文件問題。

`src/` 完全沒有修改，包括 `domain/statistics/` 和 `breakeven.py`。`trials_from_metrics` 的門檻、git hooks 和 LFS hooks 也都沒動。沒有回覆 PR 留言，沒有開 PR，也沒有 merge。

- **分支：** `feat/stats-py314` 從 `ff7933e` fast-forward push 到 `bbe2d8b`，PR #38 的 head 隨之更新。
- **commit：** 六個，見文末。

### 開工前的確認

- **第 6 輪（核心模組六項）已經乾淨完成：** `ff7933e` 在 origin 上，那輪的 check-full 是 exit 0、4314 passed。
- **主工作樹：** `/workspaces/tradingdev` 有與這輪無關、尚未 commit 的修改，和第 6 輪報告記錄的相同，屬於 pinned fixture WIP 等工作。依 AGENTS.md，這輪沒有碰，所有工作都在 scratchpad 的獨立 worktree 裡做。主工作樹的狀態在這輪開始和結束時完全相同。
- **前一個 session 留下的草稿：** 本機分支 `round8/validate-run-and-docs` 上有五個沒有 push 的 commit（`73e53ea..8b4c9a8`）。session-notes 和長期記憶都沒有記錄它們，而且它們是在 26 秒內一次 commit 的，所以沒有證據顯示做過獨立審查或 check-full。這輪沒有直接採用，而是把它們當成草稿：
  - 逐項對照這次的要求；
  - 對照原始碼核對事實；
  - 驗證測試在修正前會失敗；
  - 再送獨立審查。

  審查發現的問題修在第六個 commit `bbe2d8b`。

## 開工前的重現

在 `ff7933e` 版本的 `validate_run.py` 上執行審查給的原腳本：六根 K 棒、真實 `SignalBacktestEngine`、pickle 放在結束即刪的臨時目錄。結果與審查完全一致：

| 案例 | 修正前輸出 |
| --- | --- |
| no-trades | `TypeError: bad operand type for abs(): 'NoneType'` |
| open-trade | `[FAIL] A3 … 2 vs 3`、`[FAIL] A4 … 0.5000 vs 0.3333` |
| open-trade | `[FAIL] T3 … 報告 55.4534 vs 日頻重算 67.9100` |
| open-trade | `[FAIL] T6 … 報告 1.0036 \| bar 頻 1.0775 \| 日頻 0.0000` |
| 第 8 項 | horizon=1 保留 4 列（`cfeafe68…`），horizon=2 保留 3 列（`6d16dd29…`），兩個 hash 不同 |

修正後再跑同一個腳本：

- no-trades：exit 0，0 FAIL、4 N/A。A4、A5、V2 的原因是 `no_trades`，T6 的原因是 `zero_denominator`。
- open-trade：exit 0，0 FAIL。A3 為 `2 vs 2（未平倉 1 筆不計入）`，A4 為 0.5000 vs 0.5000，T3 為 55.4534 vs 55.4534（ddof=0），T6 為 1.0036 vs 1.0036。

## 各項修法與回歸測試

所有測試都在 `tests/scripts/test_validate_run.py`，共 42 個。每個案例都用真實的 signal 或 volume 引擎跑幾根合成 K 棒，把 pickle 寫進 `tmp_path` 再檢查。repository 的 `tests/conftest.py` 覆寫了 `tmp_path`，測試結束就刪除。

**「修正前會失敗」的驗證方式：** 把同一份測試檔放進 `ff7933e` 的獨立 worktree 執行。`ff7933e` 是第 6 輪結束、這輪開始前的版本。審查修正另外對 `8b4c9a8` 的 `validate_run.py` 驗證，見後文。關鍵測試逐一單獨執行，確認失敗原因就是審查描述的缺陷，而不是測試互相影響。

### 第 2 項：合法的 None 不再 traceback，報告有第三種狀態

**修法：**

- 每項檢查的結果是 `PASS`、`FAIL`、`N/A` 或 `WARN`。
- `N/A` 表示引擎依契約合法地不提供數值，並顯示 metric metadata 裡的原因碼。
- 原因碼也要核對：腳本由保存的資料推出應有的原因，順序與 `domain/backtest/metrics.py` 相同，依序是 mode → 資金基準 → 日頻取樣 → 年化設定，交易統計則看已平倉交易本身。推不出同一個原因就判 `FAIL`。
- 數值是 `None` 但 metadata 沒有原因、缺欄位、型別錯誤或資料無法讀取，都判 `FAIL`。每項檢查各自包在 guard 裡，不會中止整份報告。
- 同類情況按同一契約處理：
  - 全勝交易的 profit factor：`unbounded`；
  - 未指定年化：`missing_annualization`；
  - volume 模式的報酬指標：`not_applicable`；
  - 週線：`unsupported_daily_sampling`；未知頻率：`unknown_bar_frequency`；
  - 權益變負：`nonpositive_capital`。
- 退出碼：沒有 FAIL 為 0，有 FAIL 為 1，不是 simple backtest 為 2。明確指定的檔案讀不到，算一項 FAIL。

**回歸測試：**

- 零交易時報告完整產出，A4、A5、V2、T6 的狀態和原因如上，exit 0。
- 全勝交易、未指定年化、volume 模式、週線與未知頻率、權益變負。
- 原因與資料矛盾時判 FAIL，例如有交易卻宣稱 `no_trades`，或全勝卻宣稱 `zero_denominator`。
- None 沒有原因、缺欄位、時間戳重複、交易紀錄不是 mapping、equity 無法讀取、檔案不存在或不是 pickle：都判 FAIL，沒有 traceback。
- 用 subprocess 實際執行腳本，確認退出碼正確，stderr 沒有 `Traceback`。

**修正前：** 零交易等案例在 `abs(None)` 就拋出 `TypeError`。

### 第 3 項：A3–A5 只計已平倉，A2 包含未平倉

**修法：**

- A3（`total_trades`）、A4（`win_rate`）、A5（`profit_factor`）只用 `status == "closed"` 的交易，依 catalog 的定義。沒有 `status` 欄位的舊紀錄視為已平倉。
- A2 把全部交易的 `net_pnl`（含未平倉的 marked-to-market）和 `total_pnl` 對帳。
- `breakeven.py` 沒有修改。

**回歸測試：**

- 審查的 open-trade 案例：A3 為 `2 vs 2（未平倉 1 筆不計入）`，A4 為 0.5000 vs 0.5000。
- 多加一根 K 棒，讓未平倉部位的損益不為 0：A2 仍然 PASS，證明對帳確實包含了它。
- 把 `total_trades` 竄改成 3：A3 判 FAIL。

**修正前：** 前兩個測試會出現審查列出的 A3、A4 FAIL。

### 第 4 項：日波動與 Sharpe 依引擎定義重算

**修法：**

- 期間損益改為「該 UTC 日（月）最後一筆權益 − 前一個觀測期的收盤」，第一期從保存的初始資金算起；volume 模式從 0 算起。觀測日全部納入，不再以 `diff().dropna()` 丟掉第一天。
- 日報酬改為「當日收盤 / 前一觀測日收盤 − 1」，第一天以初始資金為分母，不再以當日第一筆權益為分母。
- `daily_pnl_std` 用 catalog 規定的 `ddof=0`。如果 metadata 宣稱其他 ddof，判 FAIL，而不是跟著改用。
- Sharpe 改讀保存的 `periods_per_year` 和 `risk_free_rate`：先把年利率換成每期利率 `expm1(log1p(rf)/ppy)`，再算 `mean/std(ddof=1)·√ppy`，不再寫死 365 和零利率。這是獨立重寫的公式，沒有呼叫引擎的程式碼，保留交叉驗證的意義；bar 頻年化的數值只作為診斷提示。

**回歸測試：**

- 審查的 open-trade 案例：T3、T6 都 PASS，數值是 1.0036 vs 1.0036。
- `periods_per_year=252`、`risk_free_rate=0.05`：T6 PASS。
- 四天的小時線，有成本，第一天收盤已經偏離初始資金：A1、T3、T4、T5、T6 都 PASS。
- 竄改 `daily_pnl_std` ×√24、`sharpe_ratio` ×1.1、`monthly_pnl_mean` ×0.5：分別只有 T3、T6、T4 判 FAIL。
- metadata 宣稱 `period_pnl_std_ddof=1`：T3 判 FAIL。

**修正前：** open-trade、252/rf 和小時線三個案例都 exit 1。

### 第 8 項：跨 horizon 分組（`docs/statistics_leaderboard_integration.md`）

- 拿掉「以 horizon 為搜尋軸，其餘 context 含 `data_fingerprint` 保持相同」這個不可能成立的要求。
- 新增一節「Grouping Across Horizons Is Not Possible Yet」，說明原因並對照原始碼：
  - `_record_evaluation` 把 dataset 的 `content_hash` 當成 `data_fingerprint`（`app/ml_service.py:378`），排行榜也用同一個值核對（`:473`）；
  - 那個 hash 是整份已標記 Parquet 的 SHA-256（`adapters/storage/ml_datasets.py:43`）；
  - `_symbol_frame` 在存檔前用 horizon 產生 `forward_return`、`target`、`label_end`，並丟掉 label 超出資料的列（`app/ml_service.py:896-906`）；
  - 附上重現：五根相同的日 K，horizon 1 保留 4 列、horizon 2 保留 3 列，hash 不同。
- 指出方向：
  - 區分「原始行情身分」與「horizon 派生的 dataset 身分」。feature cache 已經對原始 OHLCV 算了 fingerprint（`:860`），但沒有記錄在 entry 上。
  - 還需要定義不同 horizon 共同比較的評估列，因為每個 horizon 丟掉的尾端列數不同。
- 兩個定義都**明確標為待與排行榜負責人議定**，文件沒有替它們定案。在那之前，不得從排行榜 entry 建立 horizon 平原。
- 說明以 `window` 或 `n_quantiles` 分組不受影響：兩者在 dataset 建好之後才使用。
- 「Missing for Plateau Analysis」第 2 點同步註明這個開放項目。

這一項是純文件修改，沒有程式行為可測。重現結果記錄在上表。

### 文件問題

每一條都先對照原始碼確認現況，再修改。

- **METHODS.md「可重現性」表：**
  - 目前的 `uv.lock` 鎖定 vectorbt 1.2.0、pandas 3.0.6、numpy 2.5.4、quantstats 0.0.86、arch 8.0.0；
  - 合併前的 `814b05a`／`6826e41` 是 vectorbt 1.0.0、pandas 2.3.3、numpy 2.2.6；
  - 表格把兩組版本分開列出，並註明重現指令使用的是目前的 lock。
  - 開頭的「分析對象」也註明，vectorbt 1.0.0 是分析合併前引擎時的版本。
- **METHODS.md「真實與合成資料對照」：** 成本來源改為交易紀錄推得的 `traded_notional`（`summarize_breakeven`）× 寫死的費率，與 §2.7 和 `write_kd_inference()` 一致。
- **`validate_run.py` 的 usage：** 改為 `uv run python scripts/validate_run.py …`，並註明從 repository 根目錄執行。
- **開發指南（`docs/development.md`）：**
  - 原本寫「scripts 是 Shell 入口，Python 實作集中在 tooling」，現在註明 `scripts/` 下三個獨立 Python 腳本是例外，也不在 `tooling/quality.py` 的 Ruff／Mypy 範圍內（`PYTHON_PATHS` 只有 src、tests、tooling、research）。
  - 新增一節「統計展示與執行結果驗證腳本」，涵蓋：執行方式；只支援 simple backtest；必須是可信任的 pickle；自動選檔順序（依名稱排序取最後一個 run，沒有 run 才用 cache，路徑相對於目前目錄，不讀 `TRADINGDEV_WORKSPACE`／`TRADINGDEV_DATA_ROOT`）；實際重算的指標清單；四種狀態；退出碼。
- **架構文件（`ARCHITECTURE.md`）：** 模組表新增 `domain/statistics/`，並新增一節「引擎無關的統計分析」，說明它和其他部分的關係。每一點都對照原始碼確認過：
  - 只讀呼叫端傳入的資料，不讀寫檔案；
  - 與引擎 metrics 的慣例差異：第一期的基準、`ddof=1` 對 `ddof=0`、Sharpe 不扣無風險利率；
  - 不註冊 catalog 指標；
  - 目前沒有 service、MCP 工具或報告引用它，grep 確認只有三個 scripts 使用。
- **METHODS.md §2.13 的 p 值／CI 保證：** 第 6 輪已經改過，不再寫「永遠一致」，而是說明有限重抽樣的限制，這輪沒有再動。
- **連帶更新：** 第 6 輪的修正讓 `periods`、`breakeven`、`comparison`、`plateau` 的程式行數移動，METHODS.md 和排行榜文件裡的行號引用都對應更新，逐一核對過。METHODS.md 也補上第 6 輪的行為：offset 不同的時間戳、1e-12 平手規則、零離散鄰域、缺少起訖日期時 raise。排行榜文件註明，那些 KD 配對區間數字早於目前的 block length 規則，還沒有重新產生。

## 獨立審查

依 AGENTS.md 安排了一個沒有參與實作、獨立上下文的唯讀 reviewer。範圍是 `ff7933e..` 的全部差異。reviewer 除了讀程式，還做了：

- 用真實引擎跑 550 次隨機回測：signal 和 volume 兩種模式；1h／4h／15m／1d／1w 頻率；UTC、Asia/Taipei、America/New_York 時區；有缺口的資料、SL/TP、熔斷、未平倉交易、權益變負；不同的 ppy 與 rf，含負值和 None。
- 逐一核對全部文件引用的行號與版本。

結論：第 2、3、4、8 項都已達成，文件沒有事實錯誤。另外找到下列問題，我逐一重現後，修在 `bbe2d8b`：

| # | 問題 | 修法 | 回歸測試（`8b4c9a8` 版本會失敗） |
| --- | --- | --- | --- |
| 1 | 引擎允許日曆缺口，但營業日 K 棒會讓 S4/S5 判 FAIL，exit 1 | S4/S5 改為 WARN | 營業日 K 棒：exit 0，S4/S5 為 WARN，T1/T3/T5/T6 PASS |
| 2 | A4–A7 的 2% 容差（對小於 1 的值等於絕對 0.02）讓竄改通過 | 改用嚴格容差 `TOL`（1e-6） | win_rate、profit_factor、max_drawdown、total_return、daily_pnl_mean 各 ×1.01，都只有對應一項 FAIL |
| 3 | 文件說「每個指標都重算」，實際只有部分 | docstring 與開發指南列出實際重算的 12 個指標，其餘只檢查有限值或附原因的 None | 純文件 |
| 4 | T5 的日／月加總必然等於權益變化，等於沒有驗證任何回報值 | T5 改為驗證原本沒有檢查的 `daily_pnl_mean` | 同第 2 列的 daily_pnl_mean 案例 |
| 5 | 沒有 settings 的舊 run：volume 模式的 T6 判 FAIL；頻率回退讀 config 的 `frequency`，但 `BacktestConfig` 的欄位叫 `timeframe` | T6 先判 mode 為 `not_applicable`；回退改讀 `timeframe` | 舊 run、volume 模式：T6 為 N/A；舊 run、`timeframe: 1w`：T3/T4/T5 為 N/A `unsupported_daily_sampling` |
| — | 我自己找到的：`mode="simple"` 但沒有 `backtest_result` 的 pickle 會拋 `AttributeError` | 改用 `getattr`，exit 2 | 對應的測試 |

reviewer 也指出，自動選檔順序和找不到檔案時的 exit 2 沒有測試。這輪補上三個 subprocess 測試：

- 有 run 時，依名稱取最後一個 run，不取 cache；
- 沒有 run 時，依名稱取最後一個 cache；
- 什麼都沒有時，exit 2，沒有 traceback。

這三個測試在舊版本也會通過，因為舊版這部分的行為本來就對；它們是補上的覆蓋，不是 bug 的回歸測試。

**修正後的複查：**

- 修正前（`8b4c9a8` 的 `validate_run.py`）：9 failed、33 passed。失敗的就是上表的 9 個案例。
- 修正後：42 passed。
- reviewer 的隨機測試在嚴格容差下：250/250 OK，沒有任何合法結果被判 FAIL。

**沒有處理、留作開放項目：**

- `timestamps` 為 None 時，引擎合法地回報 `missing_timestamps`，但腳本在 S1 就判 FAIL。BacktestService 的資料一定帶 timestamp，所以實務上應該碰不到，而且要改就得決定整組時間類檢查略過後要怎麼呈現。這輪只記錄，不改。
- T6 在日報酬接近常數時，原因碼可能因浮點誤差而與引擎不同。reviewer 沒有重現出來。

## 第 6 輪釘住的數字

這輪沒有修改 `src/`，`git diff ff7933e -- src` 是空的。

我另外取出 `feat/stats-pinned-fixtures`（`49de1b7`）的 fixture 和釘值測試，強制匯入這輪 worktree 的 `src` 執行。結果 6 passed，rel 1e-9 內全部不變：

| 數字 | 值 |
| --- | --- |
| Sharpe | −7.565103143673017 |
| traded notional | 5014735.715506879 |
| cost/\|net\| | 0.863481526386825 |
| 日報酬天數 | 366 |

`tests/domain/statistics/` 的 390 個測試也都通過。

## 檢查結果

- **迭代：** `uv run pytest tests/domain/statistics/ tests/scripts/ -q`：審查前 421 passed，套用審查修正後 432 passed（390 + 42）。
- **check-fast：** commit 前執行，exit 0。git hooks 仍未安裝，依先前的決定沒有動。
- **check-full：** 在 `bbe2d8b` 跑了一次，執行前開了 keepalive。
  - 結果：exit 0；4356 passed，12 deselected（`live_llm`），74 warnings；pytest 耗時 49 分 20 秒（02:24–03:15 UTC）
  - 執行期間工作樹沒有修改，結束後沒有殘留的 pytest 或 keepalive 程序。
- **check-full 的第一次啟動用錯了工作樹，必須說明：** 我的指令寫成 `cd wt && … && ( keepalive ) &`，`&` 把含 `cd` 的整串命令都放到背景，所以 check-full 在主工作樹 `/workspaces/tradingdev` 執行。
  - 那次的結果：exit 0，4276 passed，49 分 29 秒。它測的是使用者未 commit 的狀態，不是這輪的分支，所以不算數。
  - 我是從 log 的 `rootdir` 和收集數發現的：4288 項，正確應該是 4368。
  - 主工作樹的 `git status` 在那次執行前後完全相同。
  - 修正後改用獨立腳本執行：先 `cd`，確認 `pwd` 是這輪的 worktree 才開始。重跑的 log 顯示 `rootdir` 是這輪的 worktree，收集 4368 項，選取 4356 項。上面列的 check-full 結果是這次重跑。
- **未涵蓋：**
  - 沒有跑真實 LLM 情境。這輪沒有改模型可見的 MCP schema、回覆或策略流程。
  - 沒有重跑需要私人 pickle 的 KD demo，所以 METHODS.md §2.13 的表格與 forest 圖仍是舊輸出；文件已經註明。
  - 沒有跑 `check-pr.sh`，它需要呼叫 Codex 做文件審查。

## 待決事項（都需要使用者決定）

1. **排行榜跨 horizon 的身分與共同評估列：** 需要與排行榜負責人議定，目前文件標為 OPEN。
2. **`feat/stats-pinned-fixtures`（`49de1b7`）會與這輪衝突：** 它也修改了 `scripts/validate_run.py` 和 `tests/scripts/test_validate_run.py`。之後整合時，應以這輪的版本為基礎，再把 fixture 測試併進來。fixture PR 要 stacked 還是等 #38 合併，仍未決定。
3. **`validate_run.py` 剩下的開放疑慮：** `timestamps` 為 None 判 FAIL；T6 浮點邊界的原因碼。
4. 沿用先前的決定：git hooks 不安裝；`trials_from_metrics` 的最小觀測數門檻另案處理。
5. **PR #38：** head 已更新，可以重新執行 `check-pr.sh 38`。這輪依指示沒有回覆審查留言。

## Commit

| commit | 內容 |
| --- | --- |
| `73e53ea` | fix(scripts): make validate_run follow the engine's metric contract（第 2–4 項與 usage） |
| `079eef9` | docs(statistics): follow the reviewed statistics code in METHODS and the contract |
| `ce23224` | docs: correct the METHODS versions and cost source |
| `257b3d1` | docs: mark horizon grouping in the leaderboard contract as open（第 8 項） |
| `8b4c9a8` | docs: describe the statistics layer and the Python scripts |
| `bbe2d8b` | fix(scripts): close validate_run gaps found in stage review |
