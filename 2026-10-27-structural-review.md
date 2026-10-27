# 2026-10-27 結構審查：PR #38 的範圍、型別漏洞與整合契約

> **後續：** 同日稍晚改成實作輪（重新切分，見 `2026-10-27-recut-proposal.md`）。本文件是那之前的
> 純分析，數字以 `df88dd1` 為準；實作採用了 R1，R2 改為提案，R3–R5 尚未決定。

寫這份文件時只做分析，沒有修改程式。所有判斷都以 PR #38 head `df88dd1`、base `5f8d14d` 為準，
在 scratchpad 的 detached worktree 唯讀檢視。`feat/stats-py314` 的本機與遠端 ref 都沒有動，
沒有對 PR 發留言，也沒有 push 到任何程式分支。

> 版本說明：會議資料寫的「30 個檔案、7622 行」，是本機 `feat/stats-py314`（`610e612`，
> 落後 origin）相對其 merge-base 的數字。PR 實際的 head `df88dd1` 是 **33 個檔案、+9286／−7**，
> 下文一律使用這組數字。

## 0. 會議定案（記錄，不再列為未決）

| # | 定案 | 本文件的處理 |
| --- | --- | --- |
| D1 | 排行榜只排 ML signal model，不排策略或回測。`comparison.py`、`benchmark.py` 與排行榜沒有重疊，不需要分工。 | 作為第 1 節模組歸屬的前提。 |
| D2 | `rolling_ic` 的暖機期填 0，不留 NaN。 | 第 4 節記錄統計後果與契約須寫明的項目。 |
| D3 | 呼叫層級：有一個 list 呼叫，才往下呼叫統計模組。 | 第 0.1 節對照程式碼；有一部分找不到對應，列為要回去問的問題。 |
| D4 | （會中補充）要 push 的內容只放程式碼，不放以展示為目的的程式。 | 第 1 節依此評估 `demo_output/` 與兩支 demo 腳本的去留。 |

### 0.1 D3「list 呼叫」對照程式碼的結果

**找到的機制：**

- 上游 `809ae68 feat!: page growing MCP discovery lists`，分頁的是五個探索清單：
  `list_strategies`、`list_runs`、`list_jobs`、`list_available_data`、`list_artifacts`。
  它們由 `app/pagination.py` 的 `paginate()` 投影成 `Page[T]`。**這五個都和 ML 排行榜無關**，
  其中沒有任何 ML 評估紀錄。
- 排行榜本身另外有分頁，是在 `9ddcdf8` 加入的，不屬於 `809ae68`。呼叫鏈為：
  MCP `leaderboard`（`mcp/tools/ml.py:224`）→ `MLService.leaderboard_page`
  （`app/ml_service.py:591`）→ `MLService.leaderboard`（`:491`，讀取全部 entries、做
  `comparability_error`、`rank_entries`）→ 排序完才依 `offset`／`limit` 切頁。
  docstring 明寫 "Page output only after ranking and comparing the full candidate set"。

**我的解讀（待確認）：** 「list 呼叫」最可能指 MCP `leaderboard` 這個分頁查詢。統計模組在
讀取時（read-time）才計算，不在 `evaluate_signal(record=True)` 寫入時計算。若是這樣，
契約須寫明三件事：

1. 統計（Bonferroni 的 N、DSR 的 N、配對 bootstrap）必須掛在 `MLService.leaderboard`
   這一層，用的是**全部候選**，不能掛在切頁之後；否則 N 會變成頁面大小。
2. 每次翻頁都會重算整個排行榜。bootstrap 要固定 seed，第 1 頁和第 2 頁的數字才會一致；
   計算量也會乘上翻頁次數，需要決定是否快取。
3. 排行榜目前不保存 IC 序列（`statistics_leaderboard_integration.md` 第 2 節）。所以
   讀取時計算，等於要在查詢時重建序列，或者寫入時就先存好序列。

**要回去問的問題：**

- Q1：「list 呼叫」是指 MCP `leaderboard`，還是 `809ae68` 的某個 `list_*` 工具？如果是後者，
  它們只列 strategy／run／job／data／artifact，和 D1「只排 ML signal model」互相矛盾。
- Q2：統計是在每次 `leaderboard` 查詢時計算，還是在 `evaluate_signal(record=True)` 時先算好、
  存在 entry 上，再由 list 讀取？兩者的快取、seed 與儲存格式需求不同。
- Q3：是否會新增一個 ML 評估紀錄的 list 工具（例如列出 entries 但不排名）？目前程式裡
  沒有這種工具。

## 1. 結構審查（任務 1）

### 1.1 33 個檔案按實際用途分類

分類依據是「誰會讀它、誰會執行它」，不是目錄。

| 用途 | 檔案 | 檔案數 | 行數 | 實際使用端 |
| --- | --- | ---: | ---: | --- |
| 核心：統計本體（全部 7 個模組加 `__init__`） | `src/tradingdev/domain/statistics/*.py` | 8 | 2687 | 只有 scripts 與 tests；`src/` 內沒有任何 import |
| 核心：對應測試 | `tests/domain/statistics/test_statistics_*.py` | 7 | 3197 | pytest |
| 核心：跨層回歸測試 | `tests/mcp/test_optimization_failed_trials.py` | 1 | 142 | 用真實 worker 驗證失敗 trial 進 plateau |
| 契約文件 | `docs/statistics_leaderboard_integration.md`、`ARCHITECTURE.md`、`docs/development.md` | 3 | 284 | 排行榜負責人、開發者 |
| 依賴 | `pyproject.toml`（`arch`）、`uv.lock`（新增 arch、statsmodels、patsy、formulaic、interface-meta、wrapt） | 2 | 128 | runtime |
| **工具** | `scripts/validate_run.py`、`tests/scripts/test_validate_run.py` | 2 | 1279 | 開發者手動核對引擎指標 |
| **展示程式** | `scripts/demo_plateau.py`、`scripts/demo_statistics.py` | 2 | 816 | 只產生 `demo_output/` |
| **展示產物** | `demo_output/` 四份 md、四張 png | 8 | 753（另有 566 KB 圖檔） | 人工閱讀；沒有程式或測試讀取 |

合計 33 個檔案、9286 行。展示程式加展示產物共 10 個檔案、1569 行，占 17%。

### 1.2 建議一覽（累計效果已用一次性 clone 實際 `git rm` 量測）

| # | 建議 | PR 變化（累計） | Codex 文件審查證據量 |
| --- | --- | --- | --- |
| 現況 | — | 33 檔、+9286 | 1,105,831 bytes |
| R1 | 移除展示程式與展示產物 | 23 檔、+7717（−1569） | 949,329 |
| R2 | validator 與其測試移出本 PR | 21 檔、+6438（再 −1279） | 852,905 |
| R3 | `performance`、`breakeven`、`benchmark` 與其測試移出本 PR | 15 檔、+4945（再 −1493） | 724,019 |
| R4 | 刪除三組回傳 None 的 wrapper | 約再 −90（估計，未量測） | — |
| R5 | 抽出共用推論契約與驗證 helper | 約 ±0 | — |

R1–R3 合計 **−4341 行（−47%）**，檔案從 33 降到 15。**注意**：即使做完 R1–R3，證據量
724,019 bytes 仍超過 `check-pr` 預設的 600,000 上限，因為證據大部分是 repository 既有的
文件。縮減 PR 能降低審查負擔，但不能讓 gate 不加參數就通過（見第 5 節）。

上表各列沒有含必須同步修改的文件行數，每項影響 ±5–15 行（見各項「必要連帶修改」）。

### 1.3 R1：展示材料移出（−10 檔、−1569 行）

**判斷：應移出。** D4 定案「只 push 程式碼」，團隊也說「本機 test demo 不要推」。展示材料
本來就不是 runtime data 或 fixture，沒有程式讀它們。

- **審查者的差別：** Codex 三則留言中，有 7 項 finding 只存在於展示材料，移出後直接失效：
  第一則的 #4（開發指南說 demo 不經 service）、#5（METHODS 對重現的矛盾）、#6（fee=0 的歸因）；
  第二則的 #2（`run_kd_variants` 回傳 `dict[str, Any]`）；第三則的 #1（缺導覽）、#2（缺可重現輸入）、
  #3（重跑不會更新手工表）。審查者不必再讀 675 行的 METHODS.md。
- **必要連帶修改：**
  - `docs/development.md` 的腳本表刪掉兩列，並刪除指向 METHODS 的連結。
  - `ARCHITECTURE.md:442-443` 的使用端清單同步修改。
  - `statistics_leaderboard_integration.md:173-182` 引用 METHODS 2.12／2.13 的「配對區間寬度為獨立
    假設的 0.69 倍」：要改成固定 commit 的連結（指向移出後的位置），或者刪掉這個數字。這些數字
    原本就早於目前的區塊長度規則，文件自己也這樣註明。
- **風險：**
  - PR 失去唯一一條「真實回測 → 統計」的端到端示範。PR 說明裡的 KD 數字（Sharpe −7.565 等）
    在 repository 內就沒有出處了。
  - `feat/stats-pinned-fixtures` WIP 中「固定 demo 的 KD 輸入」那一半跟著失去目的；fixture
    與 validator 測試那一半仍有用。
- **去處：** 材料不必刪掉。可以放到 `session-notes` 的 `evidence/`，或放到一條不合併的
  `demo/statistics` 分支，用固定 commit 連結引用。

**對照 Codex 第四則的歸屬建議：** 它建議「兩個展示歸 `research/statistics`」，**我不採納**。
`research/` 在品質檢查範圍內（`tooling/quality.py:13`），放進去仍然會 push 進主線，和 D4
直接衝突。展示應該整個離開 PR，而不是換目錄。

### 1.4 R2：validator 移出（−2 檔、−1279 行）

**判斷：應移出 PR #38，另開工具 PR。** 它不是展示，但也不是統計模組的一部分：它核對的是
引擎的 metrics，只借用 `breakeven`。

- **審查者的差別：** PR #38 少掉一項尚未解決的 P2（第一則 #2，V1 放過 `None`／字串／bool 指標），
  以及 621 行測試。validator 改成獨立審查。
- **對照 Codex 建議「validator 歸 tooling」：同意方向，但要補一個前提。** 移到 `tooling/`
  （或其他可 import 的套件位置）有三個具體好處：
  1. 進入 Ruff／strict Mypy 的範圍。`scripts/` 目前完全不在 `tooling/quality.py` 的
     `PYTHON_PATHS` 裡。
  2. 測試可以正常 import。目前以 `spec_from_file_location` 載入，回傳 `ModuleType`，測試中
     9 處 `validator.*` 呼叫在 mypy 眼裡全是 `Any`（見 T14）。
  3. `Run` 可以改用 dataclass。`validate_run.py:113-114` 的註解說明了它是因為這種載入方式
     才不能用 dataclass。

  前提是：要先決定「對任意 pickle 做臨時核對」的 CLI 是否真的需要。它的核心價值是
  「從原始輸出重算引擎指標」，改寫成固定 fixture 上的 pytest 回歸測試也能達成
  （pinned-fixtures WIP 已經在做）。如果不需要 CLI，就只留測試，工具本身不進主線。
- **風險：** validator 依賴 `breakeven`，所以它的 PR 必須排在 R3 移出的模組之後，或與它們同一個 PR。
  pinned-fixtures WIP 和 round 8 的 `validate_run.py` 已有衝突，要再 rebase 一次。

### 1.5 R3：不服務排行榜的統計模組移出（−6 檔、−1493 行）

這是我自己的判斷，**和 Codex 第四則「統計核心位置合理」不同**。位置確實合理，問題在於
**這個 PR 裡有沒有使用端**。

移出 R1、R2 之後，七個模組的使用端如下：

| 模組 | 行數（本體＋測試） | 依賴 | 非測試使用端 | 和 D1 排行榜的關係 |
| --- | ---: | --- | --- | --- |
| `comparison` | 620 + 756 | `sharpe`（常數與 `IntervalUnavailable`）、`arch` | 無 | **IC 序列配對 bootstrap**（整合文件第 2 節） |
| `plateau` | 704 + 851 | 無 | 無（`tests/mcp` 有跨層測試） | **超參數平原**（整合文件第 1 節）；也服務策略最佳化 |
| `sharpe` | 482 + 563 | `arch` | `comparison`、`performance` | DSR 只用在報酬序列，排行榜用 Bonferroni；但 comparison 的契約與測試都依賴它 |
| `periods` | 165 + 249 | 無 | `performance`、`benchmark` | 無；但 comparison 測試用它產生報酬 |
| `performance` | 180 + 182 | `periods`、`sharpe._annualisation` | 無 | 無 |
| `breakeven` | 233 + 222 | 無 | `validate_run` | 無 |
| `benchmark` | 302 + 374 | `comparison`、`periods` | 無 | 無（D1 明確排除） |

`performance`、`breakeven`、`benchmark` 是策略／回測端的統計，在主線沒有使用端，D1 也排除了
它們和排行榜的關係。**切割線是乾淨的**：留下的四個模組沒有 import 這三個。唯一的痕跡是
`sharpe.py:19` docstring 提到 `performance`，需要改一行。

- **審查者的差別：** PR #38 收斂成「ML 排行榜要用的推論統計」，只剩一個主題。它們和 validator
  組成第二個 PR，主題是「從原始輸出重算引擎指標」，彼此內聚。
- **風險：**
  - 這三個模組已經過好幾輪審查。拆出後若長期沒有使用端就會腐化，重新提交時也要重審。
  - 如果團隊打算很快把它們接到回測報告，拆分只是延後，沒有省下工作。
  - `ARCHITECTURE.md` 的統計列要拿掉「損益兩平與買進持有基準」。
- **不建議再拆 `sharpe`／`periods`：** `comparison` 的 756 行測試以 `sharpe_ratio` 當 statistic、
  以 `period_returns` 產生輸入。拆掉要重寫大部分測試，代價高於少掉的行數。

### 1.6 R4：三組回傳 None 的 wrapper（約 −90 行，估計）

`sharpe_confidence_interval`／`sharpe_interval_outcome`、`difference_interval`／`difference_interval_outcome`、
`interval_table`／`interval_table_outcome` 是同一個運算的兩種回傳形式。回傳 None 的版本在 R1 之後，
除了測試沒有任何使用端（`benchmark.py` 裡只在 docstring 提到）。

- **差別：** 每個運算只剩一個公開 API。AGENTS.md 也要求「不保留 compatibility shim」。
- **風險：** 測試中 `difference_interval(` 有 32 處，要改寫成 outcome 加 `isinstance` 檢查，
  測試行數大致不變。整合文件第 2 節提到 `difference_interval` 的名稱也要改。

### 1.7 R5：模組內部結構（不減行數，但值得修）

1. **共用推論契約放在兄弟模組裡。** `comparison` 從 `sharpe` import
   `IntervalUnavailable`、`UnavailableReason`、`MIN_BOOTSTRAP_OBSERVATIONS`，所以 comparison
   依賴 sharpe 只是為了這份契約。建議抽成 `statistics/inference.py`（約 50 行），Codex 第二則也這樣建議。
2. **跨模組使用私有函式：** `performance` → `sharpe._annualisation`。若做了 R3，這個問題就跟著離開
   PR #38；否則應改成公開的共用 helper。
3. **驗證 helper 有四份，而且語意不一致：**
   - `_finite` 出現在 `sharpe` 與 `plateau`，plateau 版另外處理 `OverflowError`。
   - `_positive_int` 出現在 `comparison` 與 `plateau`；`benchmark._periods_per_year` 又是另一份。
   - comparison／sharpe 用 `isinstance(value, int)`，`reps=np.int64(5)` 會被拒絕；plateau 用
     `numbers.Integral`，`radius=np.int64(1)` 可以通過。同一個套件對同一類參數的規則不同。

   建議收斂到一個 `_validation.py`。
4. **docstring 占本體 38%**（2687 行中 1023 行；`benchmark` 52%，`sharpe` 45%）。內容大多正確，
   但和 METHODS.md 大量重複。R1 之後 METHODS 離開 repository，docstring 就成為唯一出處，所以
   不建議刪，只在這裡說明審查份量的來源。
5. **`arch` 帶進 6 個 runtime 套件**（包括 statsmodels），只為了 `StationaryBootstrap` 與
   `optimal_block_length`。自行實作的正確性風險高於依賴成本，**建議保留**，這裡只是記錄。
6. `plateau.py` 704 行，但只有一個主題（row adapter → grid → score → summary），**不建議拆**。

## 2. 靜態檢查的漏洞（任務 2）

**盤點範圍：** 統計本體、三支腳本與相關測試。方法分兩步：

1. AST 掃描 `Any`（去掉 import 行，同一行只算一次）、`cast`、`type: ignore`。結果是 `Any`
   在本體 10 處、腳本 14 處、測試 5 處，沒有 `cast`。這和 Codex 的 11／15／5 只差計數方式。
2. 逐一閱讀公開入口，看「宣告了型別但邊界沒驗證」的地方。每一處都用同一份探針檔**同時**跑
   strict mypy 與實際執行（附錄 A）。

**結論：共 17 處。** 其中 8 處是邊界未驗證、6 處是 `Any` 盲點、2 處是檢查範圍漏洞、1 處是 `type: ignore`。
最嚴重的是 **T2、T4 兩處新發現**：mypy 接受，執行期也不報錯，但默默算出錯誤數字。

### 2.1 宣告了型別但邊界沒驗證（8 處）

| # | 位置 | 為什麼過得了 mypy | 實測會放過什麼 | 怎麼改 |
| --- | --- | --- | --- | --- |
| **T1** | `plateau.py:145,184-190` `trials_from_metrics` | `rows: Iterable[Mapping[str, Any]]`；`isinstance(raw_params, Mapping)` 只收窄到 `Mapping[Any, Any]`，之後寫入宣告為 `Mapping[str, float]` 的 `Trial.params` | `{1: 1.0}` → 回傳的參數名稱是 `int`；`{1: 1.0, "a": 2.0}` → 在 `sorted()` 拋出裸 `TypeError` | 逐鍵 `isinstance(name, str)`，不符就拋 `ValueError`；建立明確的 `dict[str, float]`；`rows` 改成 `Mapping[str, object]`；補非字串鍵與混合鍵的回歸測試 |
| **T2** | `breakeven.py:107-108,201-217` `start`／`end: Any` | 型別是 `Any`，什麼都能傳 | `start=2024, end=2025`（想寫年份）→ `pd.Timestamp(2024)` 被當成 epoch 奈秒，`years = 3.17e-17`，所有年化欄位放大約 3×10¹⁶ 倍，**沒有任何錯誤** | 型別改成 `pd.Timestamp \| datetime \| np.datetime64 \| str`；`_utc_timestamp` 明確拒絕 `int`／`float`／`bool` |
| **T3** | `breakeven.py:109,133` `capital: float \| None` | mypy 依 numeric tower 把 `bool` 視為 `float` 的子型別 | `capital=True` 被當成 1.0，`annual_turnover` = 年化成交額本身 | 改用拒絕 `bool` 的 `_finite` |
| **T4** | `periods.py:36-66` `timestamps: npt.ArrayLike`（`performance`、`period_*`、`buy_and_hold_returns` 都經過這裡） | `ArrayLike` 幾乎接受任何東西 | 以 **Unix 秒**的 int 陣列傳入 30 天的小時 K → `pd.DatetimeIndex(int)` 當成奈秒，全部落在 1970-01-01 → `n_days = 1`，Sharpe 變成 None，**沒有任何錯誤** | `to_utc_index` 拒絕整數與浮點 dtype（要求 datetime64、字串或 Timestamp）；型別縮成 `pd.DatetimeIndex \| npt.NDArray[np.datetime64] \| Sequence[pd.Timestamp \| str]` |
| **T5** | `periods.py:93` `equity_curve: npt.ArrayLike` | 同上 | `bool` 陣列被轉成 0／1 權益 | 拒絕 `bool` dtype |
| **T6** | `comparison.py:156-186` `align_returns`（所有 `difference_*`、`interval_table*` 都經過這裡） | 參數是未參數化的 `pd.Series`（即 `Series[Any]`） | `pd.to_numeric(errors="coerce")` 默默接受**數字字串**與 **bool**：把一個 0／1 的訊號 Series 誤當報酬傳入，會得到 `sufficient=True` | 要求數值 dtype 且不是 bool，拿掉 `to_numeric` 的強制轉型 |
| **T7** | `sharpe.py:461-467` `_returns`（`returns: Iterable[float]`） | mypy 抓得到 `Series[str]`（實測報 `arg-type`），但抓不到 DataFrame 欄位常見的 `Series[Any]`，也抓不到 bool | `np.asarray(dtype=float64)` 會轉換 `"0.01"` 與 `True` | 與 T6 共用同一個 dtype 檢查 |
| **T8** | `periods.py:118` `frequency: Frequency`（`Literal`） | `Literal` 只約束字面值；從設定讀進來的 `str` 或 `Any` 都會通過 | `"weekly"` → `KeyError: 'weekly'`，不是文件寫的 `ValueError` | 在 `period_closing_equity` 入口驗證，拋 `ValueError` |

T1 的本質（Codex 第二則）和 T2、T4、T6 相同：**型別宣告描述的是「應該收到什麼」，但邊界沒有把
「實際收到的」收窄到那個型別**，下游就以為契約成立。T2 與 T4 比 T1 更危險：T1 最後會在
`plateau_summary` 爆出 `ValueError`，T2／T4 則一路算完，回傳看起來合理的數字。

T4 的真實觸發機率要看呼叫端：引擎的 `BacktestResult` 時間戳不是整數，所以它主要是給未來
排行榜 adapter 的直接 API 風險。

### 2.2 `Any` 造成的靜態盲點（6 處）

| # | 位置 | 現在為什麼過得了 | 會放過什麼 | 怎麼改 |
| --- | --- | --- | --- | --- |
| T10 | `performance.py:97,158`、`breakeven.py:105,220,227` `Mapping[str, Any]` 交易紀錄 | `Any` 值 | 執行期已逐欄用 `numbers.Real` 驗證，所以**沒有實際漏洞**；只是呼叫端字典的形狀沒有靜態檢查 | 改成 `Mapping[str, object]`，行為不變。Codex 也認為這裡已有驗證 |
| T12 | `demo_statistics.py:109,279,385,433,437,445`（6 處） | 已知的 `BacktestResult \| None` 退化成 `Any` | 屬性拼錯也不報錯（Codex 用 `equity_curv` 實證） | **R1 之後不存在**；若保留，改回 `dict[str, BacktestResult]` 並先處理 `None` |
| T13 | `validate_run.py:118-124,147,194,271,297`（8 處） | `Run` 的四個欄位、`setting()`、`load()`、`validate(pr)` 都是 `Any` | **V1 就是這個漏洞的實例**：在 `Any` 的 metrics 上只過濾 `int`／`float` 的非有限值，`None`（無原因碼）、字串、bool 全部 PASS（Codex P2，已重現） | `load()` 回傳 `object`，再用 `isinstance(..., PipelineResult)` 收窄；所有指標統一經過 `Run.metric()` 的型別與原因碼檢查 |
| T14 | `tests/scripts/test_validate_run.py:35-40` fixture 回傳 `ModuleType` | `ModuleType` 的屬性是 `Any` | 測試中 9 處 `validator.*` 呼叫全部沒有靜態檢查，函式改名或改簽章 mypy 都不會發現 | 隨 R2 移到可 import 的位置，改成一般 import |
| T15 | `test_statistics_plateau.py:47-55` 三個 `**kwargs: Any` wrapper | `Any` kwargs | 正常呼叫的參數名稱與型別都失去檢查 | 改成明確的 keyword 參數 |
| T16 | `test_validate_run.py:68,70` `**engine: Any`、`settings: dict[str, Any]` | 同上 | 引擎參數拼錯不會被發現 | 用 `TypedDict` 或明確參數 |

（T11 是 `breakeven` 的 `Any` 日期在 helper 之間傳遞，與 T2 是同一個問題，合併計算。）

### 2.3 檢查範圍的漏洞（2 處）

| # | 現況 | 影響 | 怎麼改 |
| --- | --- | --- | --- |
| T17 | `tooling/quality.py:13` 的 `PYTHON_PATHS = ["src", "tests", "tooling", "research"]` 不含 `scripts/` | 三支腳本共 1474 行，commit hook、`check-fast`、`check-full` 都不會跑 Ruff／Mypy。之前「check-full 通過」從來不涵蓋它們；Codex 是另外手動跑的 | R1、R2 之後 `scripts/` 不再有 Python。否則就把 `scripts` 加進 `PYTHON_PATHS` |
| T18 | `demo_output/*.md` 不在 `check-docs` 範圍內 | METHODS.md 有 10 項 PyMarkdown MD049 沒被檢查 | R1 之後不存在 |

### 2.4 `type: ignore`（1 處值得改）

測試裡共 16 處，全部帶具體錯誤碼：

- 14 處是刻意傳入非法值，或刻意破壞資料（`arg-type`、`list-item`、`assignment`），有測試用途，應保留。
- 1 處是 quantstats 沒有型別（`no-untyped-call`），合理。
- **T19**：`test_statistics_sharpe.py:138` 的 `sorted(psrs)` 帶 `type-var`。`psrs` 是
  `list[float | None]`，這個 ignore 掩蓋了「裡面可能有 None」。應先 `assert all(p is not None ...)`
  收窄再排序。

### 2.5 關於「Claude Code 會繞過靜態檢查」

照實說：這個 PR **沒有**放寬 `pyproject.toml` 的 mypy 設定，也沒有新增 override。但它有三條
繞過的路徑，而且都是我（Claude Code）寫進來的：

1. 把 Python 放在品質檢查範圍外的 `scripts/`，並且在開發指南裡把這件事寫成例外（T17）。
2. 在不想定義型別的邊界用 `Any`（T12、T13）。
3. 宣告了精確型別，卻沒有在邊界收窄（T1–T8）。mypy 在這種情況下不是被繞過，而是**被誤導**：
   它相信宣告，所以下游的檢查全都建立在一個沒驗證的前提上。

第 3 種最不容易被看見，也是 T1 的本質。修正原則只有一條：**公開入口收到 `object`，驗證後才
產生宣告的型別。**

## 3. 展示材料的 README（任務 3）

依指示先不寫。R1 建議把展示材料移出 repository。若團隊採納，README 應該跟著材料放到新位置
（例如 `session-notes/evidence/statistics-demo/README.md`），不是放在 PR 裡。

### 3.1 README 該回答的問題

1. **這是什麼、給誰看？** 會議展示材料，不是產品輸出、不是測試 fixture，沒有程式讀它。
2. **先讀什麼？** 閱讀順序，以及每張圖對應哪一份表、哪一節方法說明。
3. **哪些是合成資料，哪些是真實回測？** 真實回測的部分，是讀取快取 pickle，還是重新執行？
4. **每份檔案是生成的還是手工維護的？** 由哪支腳本、哪個函式產生，在哪個 commit 產生？
5. **兩套 plateau 圖是什麼關係？** 是同一個案例的兩種視圖，不是兩份獨立證據。
6. **哪些數字已經過時？** 指產生後演算法有改過、尚未重新產生的部分（例如 forest plot 早於差值區塊長度規則）。
7. **能不能重現？** 需要哪些不在 Git 裡的輸入（`cd03bf19459b48af.pkl` 與它的 SHA-256），
   沒有這些輸入時能重現到哪裡。
8. **重跑會更新哪些檔案、不會更新哪些？** METHODS 的手工表不會被更新。
9. **數字的限制。** 例如 KD 是單一年份、in-sample，Sharpe 區間有低覆蓋疑慮（第一則 #1）。

### 3.2 八個檔案的定位

| 檔案 | 資料性質 | 產生方式 | 對應 | 狀態 |
| --- | --- | --- | --- | --- |
| `METHODS.md` | 說明文件 | 手工 | 全部 | 675 行，混合公式、程式位置、歷史實測與重現步驟；內有手工表，重跑不會更新 |
| `plateau_demo.png` | 合成（5×5，seed 0） | `demo_plateau.py` | `plateau_table.md`；METHODS 一.1、2.9–2.11 | 參數標籤版 |
| `plateau_table.md` | 合成 | `demo_plateau.py` | `plateau_demo.png` | 與下一份同標題，容易混淆 |
| `plateau_gridindex.png` | 合成（同一案例） | `demo_statistics.py` | `plateau_gridindex_table.md` | 索引版，配色不同；不是獨立證據 |
| `plateau_gridindex_table.md` | 合成 | `demo_statistics.py` | `plateau_gridindex.png` | 同上 |
| `kd_equity.png` | 真實回測，讀快取 pickle | `demo_statistics.py` | `kd_inference.md`；METHODS 一.2、2.8 | 需要私人 pickle 才能重現 |
| `kd_inference.md` | 真實回測，讀快取 pickle | `demo_statistics.py` | `kd_equity.png`；METHODS 2.1–2.7 | fee=0 的歸因寫錯（第一則 #6） |
| `comparison_forest.png` | 真實回測，重新執行三組 KD | `demo_statistics.py` | METHODS 一.3、2.12–2.13 | 圖是舊演算法的輸出；沒有 pickle 時腳本會先退出，連這張圖也跑不到 |

## 4. IC 整合契約要補的內容（任務 4）

### 4.1 記錄 D2：暖機期填 0

會議定案 `rolling_ic` 的前 `window − 1` 筆填 0。Codex 第三則 #4 曾明確寫「不能填零……假裝
可配對」，所以契約需要記錄這是團隊的決定，並且寫出統計後果。

### 4.2 統計後果（以現行 `ic_statistics` 推導並實測）

記號：`m` 是有效 IC 筆數，`k = window − 1` 是填 0 的筆數，`N = m + k = n_bars`，
`μ`、`s` 是有效 IC 的平均數與樣本標準差。

| 量 | 填 0 後 | 方向 |
| --- | --- | --- |
| `ic_mean` | `μ · m/N` | **一定往 0 縮**，比例正好是 `m/N` |
| `ic_std` | `s'² = [(m−1)s² + μ²·mk/N] / (N−1)` | **不一定**：`μ² < s²·N/m` 時變小，反之變大 |
| `icir` | `μ'/s'` | **絕對值一定變小**（`m ≥ 2`、`k ≥ 1` 時可證明） |
| `ic_t_stat` | `icir' · √n_effective` | **一定往 0 縮**，比例和 ICIR 相同 |
| `ic_positive_rate` | 乘以 `m/N` | 一定變小（0 不算正） |
| `n_periods` | `m → N` | 增加 `k` |
| `n_effective_periods` | **不變** | 見下方更正 |

**更正會議資料的一個前提：** 「`n_effective` 會變大」在現行程式**不成立**。
`ic_statistics`（`domain/ml/evaluation/metrics.py:147-151`）的 `n_effective = n_bars // window`
用的是 `len(series)`，**本來就包含 NaN 暖機列**，所以填 0 不會改變它。附帶發現：這代表現行
`n_effective` 已經把 `k` 筆沒有 IC 的列算進去。例如 441 筆有效 IC、window 60，現行算出 8，
用有效筆數算是 7。只有將來把 `n_effective` 改成依有效筆數計算，填 0 才會讓它變大。

實測（`rolling_ic` 加 `ic_statistics`，window 60，同一份資料比較 NaN 與填 0）：

| 情境 | ic_mean | ic_std | ICIR | t | positive_rate | n_periods | n_eff |
| --- | --- | --- | --- | --- | --- | --- | --- |
| n=250，強訊號 | 0.211 → 0.161 | 0.102 → **0.126**（變大） | 2.07 → 1.27 | 4.13 → 2.55 | 1.00 → 0.76 | 191 → 250 | 4 → 4 |
| n=500，強訊號 | 0.120 → 0.106 | 0.106 → 0.107 | 1.13 → 0.99 | 3.20 → 2.80 | 0.94 → 0.83 | 441 → 500 | 8 → 8 |
| n=2000，弱訊號 | 0.0104 → 0.0101 | 0.134 → **0.132**（變小） | 0.078 → 0.076 | 0.445 → 0.439 | 0.55 → 0.53 | 1941 → 2000 | 33 → 33 |

樣本越短，影響越大：n=250 時 t 統計量少了 38%。

### 4.3 對排行榜與 Bonferroni 的影響

- **同一個 context 內的排名：** `comparability_error` 要求 dataset、window 相同，所以同組候選的
  `N`、`k` 相同。`ic_mean` 與 `ic_positive_rate` 的排序不變（同乘 `m/N`）。但 **ICIR 與 t 的
  排序可能改變**，因為 `s'` 的變化取決於每個候選自己的 `μ/s`。
- **Bonferroni 門檻：** `required_t_stat(N_candidates)` 不變，t 統計量變小，通過的候選變少。
  方向偏保守，但這是填充造成的，不是證據強度造成的。
- **新舊紀錄混排：** `code_fingerprint` 只雜湊 feature package（`domain/ml/feature_cache.py:110`），
  不含 `evaluation/metrics.py`。改成填 0 之後，新 entry 和舊 entry 的 `context.key` 相同，
  **會被默默排在一起**，但兩者的 `ic_mean`／ICIR／t 定義不同。契約需要指定：評估慣例版本要放進
  context，或者改版時重建排行榜。

### 4.4 對配對 bootstrap 的影響（若填 0 的序列直接交給 `difference_interval`）

- 兩個候選的前 `k` 筆都是 0，差值正好是 0。平均差往 0 縮，比例是 `m/N`。
- 開頭一段常數 0 是結構斷點，而 stationary bootstrap 假設序列平穩。單次模擬中，區間寬度從
  0.0649 變成 0.0825（**+27%**），區塊長度從 29 變成 33，點估計從 0.126 變成 0.107。
  寬度方向取決於資料，只有一次模擬，**不能推論為一般規律**。
- **樣本門檻會被填充繞過（已實測）：** n=70、window=60 時，有效 IC 只有 11 筆，低於
  `MIN_BOOTSTRAP_OBSERVATIONS = 20`，`dropna` 版本回傳 `IntervalUnavailable(insufficient_observations)`。
  填 0 後 overlap 變成 70，回傳 `DifferenceInterval`，也就是一個由 59 筆填充值構成多數的區間。

### 4.5 契約必須寫明的項目

1. 填 0 發生在哪一層：`rolling_ic` 本身（會連帶改變排行榜所有 IC 純量），還是只在 bootstrap
   adapter（排行榜純量不變）。
2. 每個 entry 填了幾筆（`k = window − 1`），要記錄在 entry 上，不能只能推算。
3. `n_periods`、`n_effective_periods` 的新定義，並明寫填充列是否計入。
4. `ic_mean`（縮 `m/N`）、ICIR（絕對值縮小）、t（同 ICIR）、positive rate（縮 `m/N`）的方向性影響，
   以及 `ic_std` 方向不定。
5. bootstrap 的最小觀測數是否以有效筆數判斷。建議以 `m` 判斷，否則門檻形同虛設。
6. 新舊 entry 的區分方式（評估慣例版本）。

**建議（不在本輪實作）：** 如果填 0 的目的只是讓兩條序列在同一個 index 上對齊，可以考慮「對齊時
填 0，但統計時遮罩掉填充列」。這樣兩個目的都能達成，又不改變 `ic_statistics`。

### 4.6 Bonferroni 寫錯的更正方式（本輪不改，只列改法）

Codex 第三則 #5 是對的。Bonferroni 來自聯集上界
`P(∪Aᵢ) ≤ Σ P(Aᵢ) ≤ N·(α/N) = α`，在**任何相依結構下都成立**。候選之間相關只會讓它更保守，
不是它的前提。需要「獨立試驗」假設的是 DSR。

**`docs/statistics_leaderboard_integration.md:27-29`**，現行：

> Both count `N` as independent candidates, while neighbouring candidates are
> correlated, so both over-correct.

建議改為：

> Bonferroni needs no independence: its family-wise bound follows from the
> union bound and holds under any dependence, so correlated candidates only make
> it conservative. It is valid only to the extent each single test is valid, and
> `required_t_stat` uses a normal approximation that is optimistic for short
> series. The deflated Sharpe ratio is different: its expected-maximum hurdle
> assumes `N` independent trials, so correlated trials violate its assumption;
> see the `deflated_sharpe_ratio` docstring.

**`src/tradingdev/domain/statistics/sharpe.py:374-376`**（`deflated_sharpe_ratio` docstring），現行：

> Both share one weakness: they count `N` as independent candidates, but
> neighbouring candidates are correlated, so `N` overstates the effective number
> of trials and both over-correct.

建議改為：

> They do not share their assumptions. Bonferroni holds under any dependence
> between the `N` tests, and correlation only makes it conservative. This
> function assumes `N` independent trials; see the limitation above.

**待驗證的疑慮（不是已確認的問題）：** 同一份 docstring 的 Limitation 段（`sharpe.py:343-349`）說
DSR 用實際 `N` 會「over-correct」，因此偏保守。但相關的 trial 也會讓 `std(SR_n)`（trial Sharpe 的
截面離散度）變小，進而壓低門檻。兩個效應方向相反，淨方向沒有在這裡證明。建議改寫時一起把
「conservative」限定為「若 `std(SR_n)` 反映虛無假設下的抽樣離散度」，或者用模擬驗證後再下結論。

## 5. check-pr 的實際狀況（任務 5）

**結論：我們這邊可以跑到 Codex 文件審查那一步，但跑不完 PR gate。** 原因是沒有 Codex CLI，
也沒有 Codex 登入。這不是缺 Python 依賴，也不是腳本壞掉。我們能自己驗證的是
`check-full.sh`，不是 PR gate。

我實際執行了三次（從乾淨的 detached worktree，`TRADINGDEV_CHECK_PYTHON` 指向主 `.venv`）：

| 嘗試 | 結果 | 原因 |
| --- | --- | --- |
| `check-pr.sh 38`（預設 `--remote origin`） | exit 1：`Reading GitHub PR failed (gh exit 1)` | `origin` 是 fork `cklivse/tradingdev`，PR #38 在 `Kuan-Lun/tradingdev`。要加 `--remote upstream` |
| `check-pr.sh 38 --remote upstream` | exit 1：`Documentation evidence is 1105831 bytes, exceeding the 600000-byte budget` | 證據量超過預設上限。沒有截斷，也沒有呼叫模型 |
| 再加 `--max-evidence-bytes 1200000` | exit 1：`Codex CLI was not found on PATH ... No model request was made.` | 本機沒有 `codex`，也沒有 `~/.codex` |

這次成功的部分：`gh` 已用 `cklivse` 登入並能讀取 PR；合併候選計算正確（tree `15408fa`，
和 Codex 留言相同）。文件證據是 1 批，`996,592 / 1,024,000` 字元，**離單批上限只差 3%**。

在我們的環境還有另一個障礙沒有實際觸發：主 worktree 有 20 項使用者既有的未提交修改，而
`check_pr.py:90-91` 要求乾淨的 checkout。所以必須像這次一樣，從獨立的乾淨 worktree 執行。

**流程順序決定了能驗證到哪裡：** `tooling/git/candidates.py:234-283` 的 `verify_candidate`
先跑 Codex 文件審查，再跑 `check_snapshot(..., "full")`。所以 Codex 那一步失敗時，完整
pytest 根本不會開始。

**我們能做與不能做的事：**

- 能：對同一個候選 tree 跑 `scripts/check-full.sh`，得到 Ruff、Mypy、完整離線 pytest 的結果。
  Codex 第一則也是這樣另外跑的。但這**不等於 PR gate 通過**。
- 不能：Codex 文件一致性審查。要做到，需要安裝 Codex CLI（或設 `TRADINGDEV_CODEX_BIN`），
  並用一個 OpenAI／ChatGPT 帳號登入。這是要回去問的問題：我們有沒有這個帳號？
- 即使有 Codex：證據超過預設上限，必須明確給 `--max-evidence-bytes`（Codex 用的是 1,200,000）。
  做完 R1–R3 後是 724,019 bytes，仍然超過 600,000，但單批字元數會從 97% 降到約 63%。

**清理：** 三次執行建立的臨時候選 repository 都已自動刪除（沒有殘留的
`/tmp/tradingdev-pr-candidate-*`），也沒有殘留程序。

## 6. 待決事項彙整

| # | 問題 | 誰決定 |
| --- | --- | --- |
| Q1–Q3 | D3「list 呼叫」的確切對象與計算時機（第 0.1 節） | 會議／排行榜負責人 |
| Q4 | 是否採納 R1（展示移出），以及材料改放哪裡 | 團隊（D4 已傾向採納） |
| Q5 | 是否採納 R2、R3；validator 的 CLI 是否需要，還是只留 fixture 測試 | 團隊 |
| Q6 | 暖機填 0 發生在 `rolling_ic` 還是 adapter；新舊 entry 如何區分 | 排行榜負責人 |
| Q7 | 有沒有可用的 Codex 帳號，讓我們能自己跑 PR gate | 使用者 |
| — | 既有未決：horizon 分組契約、validate_run S1／T6、Sharpe 區塊長度（第一則 #1） | 不變 |

## 附錄 A：型別探針（同一份檔案跑 strict mypy 與執行期）

在 PR head 的 `src` 上執行。mypy 只對 T7 的 `Series[str]` 報了 1 個錯誤，其餘全部接受。

```text
P1 int key: OK -> int
P1 mixed keys: TypeError: '<' not supported between instances of 'str' and 'int'
P2 start=2024 end=2025 years: OK -> 3.168808781402895e-17
P3 capital=True turnover: OK -> 2005.8811475409834
P4 sharpe bool Series: OK -> 22.060522810365722
P5 align bool: OK -> True
P5 align str: OK -> True
P6 unix-second timestamps daily periods: OK -> 1
P6 performance n_days: OK -> 1
P6b bool equity: OK -> 3
P7 np.bool_ net_pnl: ValueError: trade 0 has no numeric net_pnl   # 正確拒絕
P8 frequency='weekly': KeyError: 'weekly'
mypy: probe_types.py:47: error: Argument 1 to "sharpe_ratio" has incompatible
      type "Series[str]"; expected "Iterable[float]"  [arg-type]   # 只有這一個
```

核心呼叫（重現用）：

```python
summarize_breakeven([trade], start=2024, end=2025, capital=1000.0).years  # 3.2e-17
secs = np.arange(1_704_067_200, 1_704_067_200 + 86400 * 30, 3600)        # Unix 秒
summarize_performance(np.linspace(100, 110, secs.size), secs, []).n_days  # 1
align_returns({"a": pd.Series([True, False] * 15),
               "b": pd.Series([0.1] * 30)}).sufficient                   # True
```

## 附錄 B：本輪做了什麼、沒做什麼

- **做了：**
  - 唯讀檢視 `df88dd1`，讀完 Codex 三則留言。
  - 用一次性 shared clone 的 `git rm` 加 `write-tree` 量測 R1–R3 的行數與證據量；clone 不屬於任何分支，已刪除。
  - 跑了型別探針、IC 填 0 模擬，以及三次 `check-pr.sh`。
- **沒做：**
  - 沒有修改程式、沒有 commit 或 push 到程式分支、沒有在 PR #38 留言。
  - 沒有跑 `check-full.sh`（本輪沒有程式變更，需要時再跑）。
  - 沒有驗證 Sharpe 區塊長度的修正方案，也沒有驗證 DSR 疑慮。
  - R4 的 −90 行是估計，沒有量測。
- **分支狀態：**
  - `feat/stats-py314` 的遠端是 `df88dd1`，本機 ref 仍是 `610e612`（落後），兩者都沒有動。
  - 主 worktree 開始時就有 20 項使用者既有的未提交修改，本輪沒有碰。
