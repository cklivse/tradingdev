# 2026-10-27 重新切分提案：feat/stats-recut

這一輪的工作是重新切分，不是重寫。統計邏輯沒有改，對合法輸入算出的數字也完全不變。

- 新分支 `feat/stats-recut` 從 `df88dd1` 開出，有三個 commit，**只在本機，沒有 push**。
- `feat/stats-py314` 的本機 ref（`610e612`）和遠端 ref（`df88dd1`）都沒有動，沒有 force-push，
  也沒有改寫歷史。
- 只有 `session-notes` 有 push，內容是 evidence、本報告和同日稍早的 `2026-10-27-structural-review.md`。

## 1. 數字

| | 檔案數 | 新增 | 刪除 |
| --- | ---: | ---: | ---: |
| 移出前：PR #38 head `df88dd1` | 33 | 9286 | 7 |
| 只移出展示材料（commit 1 之後） | 23 | 7710 | 7 |
| `feat/stats-recut` 目前（三個 commit 之後） | **23** | **7847** | **7** |

移出展示材料讓 PR 少了 10 個檔案、1576 行新增：1569 行展示材料，加上修正引用時刪掉的 7 行文件。
另外少了 4 張 PNG（566 KB）。

型別邊界與 README 兩個 commit 加回 137 行：

- 型別邊界：+108／−29，主要是回歸測試。
- README：+60／−2，大部分是模組說明 docstring。

### `git diff --stat upstream/main...HEAD` 完整輸出

`upstream/main` = `5f8d14d`，與 merge-base 相同。

```text
 ARCHITECTURE.md                                    |  24 +-
 docs/development.md                                |  47 +-
 docs/statistics_leaderboard_integration.md         | 211 +++++
 pyproject.toml                                     |   1 +
 scripts/validate_run.py                            | 658 ++++++++++++++++
 src/tradingdev/domain/statistics/__init__.py       |  58 ++
 src/tradingdev/domain/statistics/benchmark.py      | 302 +++++++
 src/tradingdev/domain/statistics/breakeven.py      | 248 ++++++
 src/tradingdev/domain/statistics/comparison.py     | 620 +++++++++++++++
 src/tradingdev/domain/statistics/performance.py    | 180 +++++
 src/tradingdev/domain/statistics/periods.py        | 175 +++++
 src/tradingdev/domain/statistics/plateau.py        | 710 +++++++++++++++++
 src/tradingdev/domain/statistics/sharpe.py         | 482 ++++++++++++
 .../domain/statistics/test_statistics_benchmark.py | 374 +++++++++
 .../domain/statistics/test_statistics_breakeven.py | 242 ++++++
 .../statistics/test_statistics_comparison.py       | 756 ++++++++++++++++++
 .../statistics/test_statistics_performance.py      | 182 +++++
 tests/domain/statistics/test_statistics_periods.py | 263 +++++++
 tests/domain/statistics/test_statistics_plateau.py | 865 +++++++++++++++++++++
 tests/domain/statistics/test_statistics_sharpe.py  | 563 ++++++++++++++
 tests/mcp/test_optimization_failed_trials.py       | 142 ++++
 tests/scripts/test_validate_run.py                 | 621 +++++++++++++++
 uv.lock                                            | 130 +++-
 23 files changed, 7847 insertions(+), 7 deletions(-)
```

差異中已經沒有 `demo_output/`，也沒有 `scripts/demo_plateau.py`、`scripts/demo_statistics.py`。
用 `git grep` 確認，也已經沒有任何指向它們的引用。

## 2. Commit

| Commit | 分支 | 內容 |
| --- | --- | --- |
| `b74fd7e` | `session-notes` | `evidence/2026-10-27-statistics-demo/`：8 個 `demo_output` 檔案與 2 支腳本，用 `git archive df88dd1` 原樣搬過來，逐檔核對過 hash |
| `dc25ac9` | `feat/stats-recut` | `chore:` 把展示材料移出 PR，並修正所有引用 |
| `631dde0` | `feat/stats-recut` | `fix(statistics):` 在型別宣告沒被檢查的地方驗證輸入 |
| `a674ea2` | `feat/stats-recut` | `docs(statistics):` 在 package docstring 加入模組地圖 |

### 移出展示材料時一起處理的引用

- **tests：** PR 裡沒有任何測試引用兩支 demo 腳本。主 worktree 裡有一份未追蹤的
  `tests/scripts/test_demo_statistics.py`，但它不在 PR 裡，我沒有碰。
- **`docs/development.md`：** 原本的「統計展示與執行結果驗證腳本」一節改名為「執行結果驗證腳本」，
  拿掉兩個 demo 的表格列和 METHODS 連結，開頭的例外說明也一併修改。
- **`ARCHITECTURE.md`：** 目錄表和「現有使用端」兩處都改成只列 `validate_run.py`，錨點連結也跟著更新。
- **`docs/statistics_leaderboard_integration.md:178`：** 你說不要改這份文件的內容，但這一行指向
  `demo_output/METHODS.md`，不修就會壞掉。所以**只改了引用位置**：`demo_output/METHODS.md`
  改成 session-notes 上固定 commit `b74fd7e` 的 evidence 連結。數字、Bonferroni 那段與其他文字都沒動。
  這個連結要等 session-notes push 之後才有效（本輪已經 push）。如果你寧可這一行留到另案處理，
  可以把它從 `dc25ac9` 拿掉。
- **`scripts/validate_run.py:607`：** 一行註解提到 `scripts/demo_statistics.py`，已刪掉這個引用。

## 3. `scripts/validate_run.py` 的三個選項（提案，沒有動）

| | (a) 留在 `scripts/` | (b) 移到 `tooling/`，測試移到 `tests/tooling/` | (c) 一起移出 PR |
| --- | --- | --- | --- |
| PR 行數 | 不變：23 檔、+7847 | 幾乎不變：檔案是改名，相對 base 仍是新增；另有約 10 行文件修改 | **21 檔、+6568**（−1279，已量測）；再加上 `development.md` 的 39 行一節與 `ARCHITECTURE.md` 兩處，約 −1320 |
| 審查者看到的差別 | 1279 行仍在 PR 裡，但仍不受品質 gate 檢查（`tooling/quality.py` 的 `PYTHON_PATHS` 不含 `scripts/`）；測試以 `ModuleType` 載入，9 處呼叫全是 `Any`；Codex 第一則 #2（V1 放過無原因碼的 `None`／字串／bool，P2）仍是 PR 的未解項 | 進入 Ruff／strict Mypy 的範圍（我已用專案設定跑過 Ruff，可以通過；Codex 跑過 Mypy，也可以通過）；測試可以一般 import，mypy 開始檢查那 9 處呼叫；`Run` 可以改用 dataclass；`development.md` 不再需要「scripts 例外」；V1 的 P2 仍在 PR 裡 | PR 只剩統計本體、測試與契約文件，審查焦點最集中；V1 的 P2 移到另一個 PR；依賴的 `breakeven` 留在本 PR，validator PR 可以排在後面 |
| 動到別人的目錄結構嗎 | 不會 | **會**。`tooling/` 的 9 個 commit 全是 Kuan-Lun 的，內容全是開發流程工具（git gate、品質檢查、文件審查、Codex binary）；AGENTS.md 也把它定義為「開發流程的 Python 實作」。驗證回測結果的工具放進去，會改變這個目錄的定位，需要他同意。`tests/tooling/` 同理 | 不會 |
| 其他後果 | 指令不變 | 執行方式改成 `python -m tooling.<名稱>`，文件要同步 | `feat/stats-pinned-fixtures` WIP 依賴 validator，要改 rebase 到新的 validator PR |

**我的建議是 (c)。** 理由有三個：

1. 它不是統計模組的一部分，只借用 `breakeven`。
2. 它帶著一個未解的 P2。
3. (b) 要先取得 `tooling/` 擁有者的同意。

(c) 的後續 PR 可以順便決定 (b) 的位置，或是改成固定 fixture 上的 pytest（pinned-fixtures WIP 已經
在做這件事），讓審查一次只處理一件事。

## 4. 型別邊界

### 4.1 本輪已修（`631dde0`）

| 位置 | 為什麼原本過得了 mypy | 原本會放過什麼 | 現在 |
| --- | --- | --- | --- |
| `plateau.trials_from_metrics` | `rows: Iterable[Mapping[str, Any]]`；`isinstance(raw_params, Mapping)` 只收窄到 `Mapping[Any, Any]` | `{1: 1.0}` 回傳 `int` 參數名稱；混合 `int`／`str` 鍵在 `sorted()` 拋出裸 `TypeError` | 逐鍵檢查，拋 `ValueError: row N parameter name 1 is not a string`；`rows` 改成 `Mapping[str, object]` |
| `breakeven.summarize_breakeven` 的 `start`／`end` | 型別是 `Any` | `start=2024, end=2025` → 被讀成 epoch 奈秒，`years = 3.17e-17`，年化欄位放大約 3×10¹⁶ 倍，**沒有任何錯誤** | 型別改成 `object`，用 `isinstance(date \| np.datetime64 \| str)` 收窄；數字與其他物件拋 `ValueError: start must be a timestamp...`。原本的「None／NaN／NaT／空字串 → missing」行為不變 |
| `breakeven` 的 `capital` | mypy 把 `bool` 視為 `float` | `capital=True` 被當成 1.0 | 拒絕 `bool` |
| `periods.period_closing_equity`（連帶 `period_pnl`、`period_returns`） | `Literal` 只約束字面值，從設定讀進來的 `str` 會通過 | `"weekly"` → 裸 `KeyError` | 拋 `ValueError: frequency must be one of ...` |
| `performance`、`breakeven` 的交易紀錄 | `Mapping[str, Any]` | 執行期本來就逐欄驗證，沒有實際漏洞 | 改成 `Mapping[str, object]`，行為不變 |

**驗證：**

- 新增的 15 個回歸案例，在 `df88dd1` 的原始程式上**全部失敗**，在修正後全部通過。量測方式是
  隔離目錄：舊 src 加新測試，以避免 pytest 的 `pythonpath = ["src"]` 把新 src 插到前面。
- 統計測試、`tests/scripts`、`tests/mcp/test_optimization_failed_trials.py` 合計 **451 passed**。
- 統計本體的 `Any` 從 10 處降到 **0**；PR 合計從 29 處降到 13 處，剩下的全在 validator 與測試。
- 原本的修法在 `pd.Timestamp(value)` 上需要一個 `type: ignore`。我沒有保留它，改成先用
  `isinstance` 明確收窄，這樣就不需要 ignore。

### 4.2 `run_kd_variants` 同類的情況：還留在 PR 裡的

`run_kd_variants()` 隨展示腳本一起離開了。同類問題（已知契約退化成 `Any`）**還有一處**：

- `scripts/validate_run.py`：`load() -> Any`、`validate(pr: Any)`。`bt = pr.backtest_result` 也因此是
  `Any`，第 301、302、343 行的 `bt.equity_curve`、`bt.trades`、`bt.metrics` 拼錯不會報錯，和
  `run_kd_variants` 的 `equity_curv` 是同一種漏洞。
- 另外，`Run` 的四個 `dict[str, Any]` 欄位與 `setting() -> Any` 正是 V1 的成因：在 `Any` 的 metrics
  上只過濾 `int`／`float`，所以放過了其他型別。

**沒有修**，因為 validator 的去留還沒決定（第 3 節）。正確修法是 `load()` 回傳 `object`，再用
`isinstance(..., PipelineResult)` 收窄；pickle 是不可信輸入，不能直接標成合法型別。這件事應該和
V1 一起放在 validator 所屬的 PR 裡修。

### 4.3 還沒修、需要你決定的（會改變「接受哪些輸入」）

| # | 位置 | 為什麼過得了 mypy | 實測會放過什麼 | 疑慮 |
| --- | --- | --- | --- | --- |
| Q1 | `periods.to_utc_index`、`equity_series` 的 `timestamps: npt.ArrayLike` | `ArrayLike` 幾乎接受任何東西 | Unix **秒**的 int 陣列被當成奈秒：30 天的小時 K 變成 `n_days = 1`，Sharpe 變成 None，沒有錯誤 | 拒絕整數 dtype 是政策改變。有沒有呼叫端是刻意傳 int64 奈秒？引擎目前不是 |
| Q2 | `equity_series` 的 `equity_curve: npt.ArrayLike` | 同上 | `bool` 陣列被轉成 0／1 權益 | 拒絕 `bool` dtype，風險低 |
| Q3 | `comparison.align_returns`（所有配對與區間函式、`benchmark` 都經過） | 未參數化的 `pd.Series` 即 `Series[Any]` | `pd.to_numeric(errors="coerce")` 接受數字字串與 `bool`：把 0／1 訊號誤當報酬，會得到 `sufficient=True` | 要不要改成要求數值 dtype 且不是 bool？會改變目前「可轉換就接受」的行為 |
| Q4 | `sharpe._returns`（`returns`、`annualised_trial_sharpes: Iterable[float]`） | mypy 抓得到 `Series[str]`，抓不到 DataFrame 欄位常見的 `Series[Any]` 與 `bool` | `"0.01"` 與 `True` 被轉成 float | 與 Q3 同一個政策，應該一起決定 |
| Q5 | 正整數參數的驗證規則不一致 | 不是 mypy 漏洞 | `comparison`／`sharpe` 用 `isinstance(int)`，`reps=np.int64(5)` 會被拒絕；`plateau` 用 `numbers.Integral`，`radius=np.int64(1)` 可以通過 | 要統一成哪一種？ |

### 4.4 測試與檢查範圍裡剩下的盲點（列出，未修）

- `tests/scripts/test_validate_run.py:35-40`：fixture 回傳 `ModuleType`，9 處 `validator.*` 呼叫都是
  `Any`。這會隨第 3 節的決定一起消失或修正。
- `tests/domain/statistics/test_statistics_plateau.py:47-55`：三個 `**kwargs: Any` wrapper，失去正常
  呼叫的參數檢查。可改成明確的 keyword 參數，屬於純測試修改。
- `tests/scripts/test_validate_run.py:68,70`：`**engine: Any`、`settings: dict[str, Any]`。
- `test_statistics_sharpe.py:138`：`sorted(psrs)  # type: ignore[type-var]` 掩蓋了 `psrs` 可能含 None。
  其餘 15 處 `type: ignore` 都是刻意傳入非法值或第三方無型別，有測試用途。
- `scripts/` 不在 `tooling/quality.py` 的檢查範圍內，只剩 `validate_run.py` 受影響。

## 5. README：放在哪裡、為什麼

**位置：`src/tradingdev/domain/statistics/__init__.py` 的 package docstring**（`a674ea2`），
`ARCHITECTURE.md` 的統計一節加一句指向它。

**內容：**

- 七個模組各自回答的問題。
- 模組間的 import 關係：

  ```text
  performance -> periods, sharpe
  benchmark   -> periods, comparison
  comparison  -> sharpe
  其餘四個不 import 套件內模組
  ```

- `arch` 用在哪裡。
- 閱讀順序：`periods` → `sharpe` → `comparison`，`plateau` 獨立，三個單次摘要模組不分順序。
- 共同慣例：非法輸入拋 `ValueError`；合法但未定義的值回傳 `None`，或回傳說明原因的 `IntervalUnavailable`。

**理由：**

1. 讀者的入口就是這個目錄。打開 `__init__.py` 或執行 `help(tradingdev.domain.statistics)` 就會
   看到，不需要先知道有一份文件存在。
2. 它和程式放在一起，模組改名或依賴改變時，同一個 diff 就會看到它；它也受 Ruff 檢查。
3. AGENTS.md 規定「不得為了承載回覆新增說明 Markdown」，並且要求架構內容放在既有架構文件。
   `ARCHITECTURE.md` 已經說明這個套件和引擎、catalog、MCP 的關係，不需要第二份 docs。
4. 公式與邊界情況已經在各模組的 docstring 裡，入口只負責導覽，不重複這些內容。

**注意可能的衝突：** 主 worktree 有一份使用者尚未提交的 `__init__.py` 修改（加入 `__all__` 與
大量 re-export，並指向一份未追蹤的 `docs/statistics_public_api.md`）。我沒有使用它，也沒有碰它。
如果那份草稿之後要提交，會和 `a674ea2` 在同一個檔案的 docstring 衝突，需要合併。

## 6. 檢查

- `scripts/check-fast.sh`：在 recut worktree 跑了三次（每個 commit 前一次），最後一次在 `a674ea2`：
  Ruff、format、strict Mypy（489 個檔案）、Markdown（15 份文件）**全部通過**，exit 0。
- 相關 pytest：451 passed（見 4.1）。
- 依指示，`check-full.sh` 這一輪**沒有跑**。
- 這一輪也**沒有**安排獨立 code review。AGENTS.md 要求有程式行為變更的階段在提交前做獨立審查，
  `631dde0` 屬於這一類。建議在決定合併進 `feat/stats-py314` 之前補做。
- 遵守的「不要做」：
  - 沒有修單序列 Sharpe 的區塊長度。
  - 沒有改 `statistics_leaderboard_integration.md` 的內容（只換了一個引用位置，見第 2 節）。
  - 沒有碰 `trials_from_metrics` 的最小觀測數門檻。
  - 沒有 force-push，程式分支也沒有 push。

## 7. 本機狀態

- `feat/stats-recut`：`a674ea2`，在 scratchpad worktree，沒有 push、沒有 upstream。
- `feat/stats-py314`：本機 `610e612`，遠端 `df88dd1`，兩者都沒有動。
- 主 worktree：保持本輪開始時的狀態，有 20 項使用者既有的未提交修改，我沒有碰。
- 要把 recut 合進 `feat/stats-py314`：`git merge feat/stats-recut` 會是 fast-forward
  （`df88dd1` → `a674ea2`），不需要改寫歷史。但本機 `feat/stats-py314` 落後 origin，要先
  fast-forward 到 `df88dd1`，而且它目前被主 worktree checkout，並帶著那 20 項未提交修改，
  所以合併最好在另一個 worktree 做。
