# 2026-10-31 第 9 輪：獨立審查、check-full（未合併、未 push）

**結論：審查已收完，check-full 沒有全綠，依指示停下。PR #38 沒有更新**，
origin/feat/stats-py314 仍是 `df88dd1`，沒有 merge，也沒有 force。

## 1. session-notes：6e16e12 的 rebase

- 6e16e12（validate_run evidence）cherry-pick 到 origin/session-notes（4a50aaa）上，
  新 SHA 是 **2db16d4**，已 push。內容與 f044ab1 從 PR 移除的兩個檔案逐位元組相同（`cmp`）。
- **SHA 對應要記住：** f044ab1 的 commit 訊息引用的是 `6e16e12`。f044ab1 已在
  origin/feat/stats-recut 上，不改寫歷史，所以那個 SHA 從此只能對應到
  **2db16d4**。路徑 `evidence/2026-10-27-validate-run/` 不變。

## 2. 獨立審查

Reviewer 是另一個沒參與實作、只能唯讀的 agent。受查的 checkout 每次都凍結在
受查版本。第一輪範圍是 df88dd1..ed9de31，六個 commit 一起審；之後每次修正都補查新的差異。

### 第一輪（df88dd1..ed9de31）：8 項

| # | 嚴重度 | 內容 | 處理 |
|---|---|---|---|
| 1 | P2 | Python list 裡混著的 `True`／`np.bool_` 被 NumPy 升成 1.0；Sharpe 系列先 `list()` 再檢查，連 object Series 也放行，`sharpe_ratio([True,0.5,0.1])` 回傳 18.8 | 採納，7f3f29b |
| 2 | P3 | `summarize_breakeven(capital=np.True_)` 被當成 1.0；`"100"`、Decimal、complex 漏出 TypeError | 採納，7f3f29b |
| 3 | P3 | 文件寫 ValueError 的邊界漏出 TypeError／AttributeError（timedelta、bytes、`np.str_`、不可雜湊的 frequency、非 Series 的 returns）；`seed` 完全沒驗證 | 採納，a3b0f22 |
| 4 | P3 | 公開的 `has_positive_equity` 仍是 `np.asarray(dtype=float64)` | 採納，7f3f29b |
| 5 | P3 | 計數錯誤訊息沒寫實際型別（`np.int64(5)` 只說 "must be a positive integer"） | 採納，a3b0f22 |
| 6 | P3 | 套件 docstring 兩處與程式不符（不是每個函式都回傳 frozen object；`_validation` 不是每個模組都用），漏了 `summarize_performance` 預設 365 | 採納，65e10bc |
| 7 | P3 | `docs/statistics_leaderboard_integration.md` 的 plateau.py 行號過時 | **不採納**：本輪禁止修改該文件，留待下次改文件時一起處理 |
| 8 | P3 | 631dde0 是不相容變更卻沒標 `!`／BREAKING CHANGE；也可以拆開 | **無法修**：631dde0 已在 origin，改訊息就是改寫歷史。在此揭露：631dde0 讓 breakeven 的數字日期、`capital=True`、非字串參數名改為拋 ValueError |

**沒有推翻任何型別漏洞的處理方向。** Reviewer 的判斷：

- 數字時間戳一律拒絕、不提供 unit 參數：方向正確。
- 布林或字串的 equity／returns 一律拒絕：方向正確，只是實作不完整（即 #1）。
- 計數只接受內建 int：可以接受，屬於可用性取捨。
- 另外提醒：整數 dtype 的 0/1 訊號仍會被當成報酬接受。這一點已寫進套件 docstring。

### 第一次複查（ed9de31..65e10bc）：2 項 P3，都採納

- **list 走逐元素檢查後慢了約 13 倍**：保存的 run 產物是 `list[float]`。修正在 103cf64：
  - 先讓 NumPy 轉型，只對數值結果比對元素型別。
  - `summarize_performance` 只驗證一次。
- **NaT/None 時間戳被說成「not strictly increasing」**：修正在 912e63e，改成直接指出是缺值。

### 第二次複查（65e10bc..912e63e）：3 項 P3，都採納

- 103cf64 的快速路徑漏掉兩種輸入：2-D list 給 `has_positive_equity`，以及 list 中的 0-d 布林 ndarray。
  修正在 3ae82d0：快速路徑改成白名單，只有「平的、全是 Python／NumPy 整數或浮點」才走快速路徑。
- 空 timestamps 被說成「not numbers」：修正在 b29c967（amend 前是 ebc4495），改成回傳空的 UTC index。

### 第三次複查（912e63e..ebc4495）

無 finding。可選建議是在 `to_utc_index` 的 docstring 補一句空輸入的行為，已補，amend 成 b29c967（只改文件）。

### 回歸測試（每一組都放到修正前的版本上跑過）

| 修正 | 修正前的版本 | 新測試在修正前失敗 |
|---|---|---|
| 7f3f29b | ed9de31 | 12 個（1 個只是訊息改變） |
| a3b0f22 | 7f3f29b | 42 個 |
| 912e63e | 103cf64 | 3 個 |
| 3ae82d0 | 912e63e | 7 個；真正抓到 bug 的是 0-d 布林 ndarray 和巢狀 list，其餘只是訊息改變 |
| b29c967 | 3ae82d0 | 2 個 |

- 有一個 `confidence="0.9"` 的測試在修正前就通過，因為 `_tail` 原本就有檢查。我撤回了那段多餘的修改，也拿掉了那個測試。
- 效能：1M 筆 `list[float]`，修正前（ed9de31）、65e10bc、b29c967 依序是：

  | 函式 | ed9de31 | 65e10bc | b29c967 |
  |---|---|---|---|
  | `summarize_performance` | 0.62 s | 8.14 s | 0.18 s |
  | `sharpe_ratio` | 0.04 s | 1.53 s | 0.07 s |
  | `equity_series` | 0.09 s | 1.34 s | 0.11 s |

## 3. 分支狀態

`feat/stats-recut` 本機 HEAD 是 **b29c967**，在 df88dd1 之上共 11 個 commit：

```text
b29c967 fix(statistics): give empty timestamps an empty index
3ae82d0 fix(statistics): take the fast numeric path only for flat, plain numbers
912e63e fix(statistics): name missing timestamps instead of calling them unordered
103cf64 perf(statistics): look for hidden booleans by type, validate once per summary
65e10bc docs(statistics): correct the package guide where review found it wrong
a3b0f22 fix(statistics)!: raise ValueError at every documented input boundary
7f3f29b fix(statistics)!: reject booleans hidden in lists and object arrays
ed9de31 docs(statistics): make the package docstring a standalone guide      <- origin/feat/stats-recut
7d59d82 fix(statistics)!: reject inputs that were silently converted
f044ab1 chore: move validate_run.py out of the statistics PR
a674ea2 docs(statistics): add a module map to the package docstring
631dde0 fix(statistics): validate inputs where their declared types are unchecked
dc25ac9 chore: move the statistics demo material out of the PR
```

- 本輪新增的 5 個 commit **只在本機**，branch ref 在主 repo 的 `.git` 裡。這輪沒有授權推 recut，所以沒推。
- df88dd1 → b29c967 是乾淨的 fast-forward。
- PR 規模（都以合併基準 5f8d14d 起算）：

  | 版本 | 檔案 | 行數 |
  |---|---|---|
  | df88dd1（目前 PR #38 head） | 33 | +9286 / −7 |
  | f044ab1（validate_run 移出後） | 20 | +6522 / −3 |
  | ed9de31 | 22 | +6953 / −3 |
  | b29c967（合併後會是這個） | 22 | +7299 / −3 |

  從 20 檔變 22 檔，是因為 7d59d82 新增了 `_validation.py` 和它的測試檔。上一輪「為什麼比預估多」的疑問就是這個原因。

## 4. check-full

所有 check-fast（Ruff、格式、strict mypy、Markdown）在每個 commit 都是綠的。完整的 check-full 跑了兩次，**兩次都沒有全綠**。

### 第 1 次（07:57–08:32 UTC）：被 SIGTERM 終止

- 記錄到的結果：
  - exit 143（SIGTERM）
  - 跑了 35 分 29 秒，進度 79%
  - 當時剛開始跑 `tests/integration/test_mcp_protocol.py`，log 只有 `Terminated`
  - rootdir 是 recut worktree；collected 4847，selected 4833
- 我之後單獨跑這個檔案（相同 worktree、相同 `PYTHONPATH`）：7 passed，10 分 57 秒。
- 送信號的來源沒有證據。可以排除的：
  - repo 自己的看門狗：見第 5 節
  - 核心 OOM：那會是 SIGKILL／137，而且 cgroup 的 `memory.events` 是 `oom 0`、`oom_kill 0`
- 不能排除的：優雅型的記憶體監控，例如 Codespaces 的監控。這類監控就是送 SIGTERM。
- 當時沒有每分鐘的記憶體紀錄。

### 第 2 次（08:50–09:47 UTC）：跑完，12 個失敗

執行方式：

- 用 `setsid --wait` 放進獨立的 session 和程序群組；pytest PID 86027，pgid 和 sid 都是 86027。
- keepalive 每分鐘記錄一次記憶體。
- 加了一個 scratchpad 裡的 faulthandler 外掛，透過 `PYTEST_ADDOPTS="-p sigterm_trace"` 載入，用來在收到 SIGTERM 時印出堆疊。
- 開跑前我依指示嘗試關掉 VS Code 的 mypy 和 ruff 語言伺服器，但它們在 15 秒內就被 VS Code 重啟了。要讓它們保持關閉，得改使用者或工作區的 VS Code 設定，所以沒有繼續。
- 最大的編輯器程序其實是 Pylance，約 850 MB，不在指示範圍內，沒有動它。

結果：

- **exit 1；12 failed、4821 passed、14 deselected；55 分 29 秒**
- 沒有收到任何信號，faulthandler 沒有輸出
- 跑過第 1 次被終止的位置：`test_mcp_protocol.py` 7 個都通過
- HEAD 前後都是 b29c967，工作樹乾淨

失敗的 12 個全部在 `tests/tooling/`：

```text
tests/tooling/test_check_pr.py::test_snapshot_timeout_stops_children_and_removes_snapshot[full]
tests/tooling/test_check_pr.py::test_snapshot_timeout_stops_children_and_removes_snapshot[docs]
tests/tooling/test_process_guard.py::test_timeout_stops_independent_child_and_allows_leader_teardown[False]
tests/tooling/test_process_guard.py::test_timeout_stops_independent_child_and_allows_leader_teardown[True]
tests/tooling/test_temporary_paths.py::test_tmp_path_is_removed_after_success_failure_timeout_and_interrupt[passed]
tests/tooling/test_temporary_paths.py::test_tmp_path_is_removed_after_success_failure_timeout_and_interrupt[assertion]
tests/tooling/test_temporary_paths.py::test_tmp_path_is_removed_after_success_failure_timeout_and_interrupt[timeout]
tests/tooling/test_temporary_paths.py::test_tmp_path_is_removed_after_success_failure_timeout_and_interrupt[interrupt]
tests/tooling/test_temporary_paths.py::test_tmp_path_cleanup_failure_is_a_test_error
tests/tooling/test_temporary_paths.py::test_plot_cache_cleanup_failure_is_reported
tests/tooling/test_temporary_paths.py::test_tmp_path_cleanup_restores_nested_cwd_in_either_fixture_order[monkeypatch, tmp_path]
tests/tooling/test_temporary_paths.py::test_tmp_path_cleanup_restores_nested_cwd_in_either_fixture_order[tmp_path, monkeypatch]
```

錯誤只有兩種：

1. **`ImportError: Error importing plugin "sigterm_trace": No module named 'sigterm_trace'`**
   - 出現在 temporary_paths，以及 check_pr 的一部分。
   - 這些測試會在子程序裡再開一個 pytest。子程序繼承了我設的 `PYTEST_ADDOPTS`，但測試替它組的環境裡沒有我加的 `PYTHONPATH`，所以載不到外掛。
2. **`FileNotFoundError: …/teardown.completed`**
   - 出現在 process_guard 和 check_pr 的逾時測試。
   - 測試預期子程序在逾時後收到 SIGINT，觸發 `KeyboardInterrupt`，再寫出這個檔案。
   - 我驗證過：非互動 bash 用 `&` 背景啟動的程序，SIGINT 會被設成忽略（`signal.getsignal(SIGINT)` 是 `1`），而且會遺傳給所有子孫程序；前景啟動則是 `default_int_handler`。
   - 第 2 次的腳本是用 `setsid --wait … &` 啟動的。第 1 次是前景啟動，但在跑到 `tests/tooling` 之前就被終止了。

**這兩種錯誤都和第 2 次的執行方式有直接關聯，但依指示我不判定它們與本輪無關，也沒有第三次重跑。**

- 本輪的 diff（5f8d14d..b29c967）沒有動到 `tooling/`、`tests/tooling/`、`scripts/`。
- 這兩次加起來，**還沒有任何一次 check-full 的 `tests/tooling/` 是在乾淨的環境下跑的**。

### 記憶體（第 2 次，每分鐘 57 筆）

- 機器：Codespace `automatic-carnival-…`，2 vCPU（AMD EPYC 7763），總記憶體 7942 MB，無 swap。cgroup 的 `memory.max` 是 `max`，沒有設上限。
- 開跑前：已用 4476 MB，可用 3465 MB。
- 最低可用 **1144 MB**（09:13:47，第 23 分）。cgroup `memory.current` 最高 5218 MB，`memory.peak` 5369 MB。
- pytest session 的 RSS 最高 **1626 MB**（第 6 分），之後多半在 1.2–1.4 GB。
- `memory.pressure` 的 full avg10 最高 **14.53**（第 12 分），代表那一刻有程序在等記憶體；第 41 分也有 3.99。
- `memory.events` 前後都是 `oom 0`、`oom_kill 0`。
- 第 34–37 分（第 1 次被終止的時間點）：可用 1440–1631 MB，pressure 0–0.7。和其他時段比，沒有特別異常。
- 其他常駐的程序：Pylance 約 850 MB，VS Code server 約 540 MB，Claude Code 約 370 MB。
- **結論：** 記憶體偏緊而且確實有壓力，但這次沒有觸發終止。第 1 次的 SIGTERM 是不是記憶體監控送的，**這些數據不能證明，也不能排除**。

## 5. 看門狗查到什麼

- `scripts/process_guard.py` 已經搬到 **`tooling/process_guard.py`**。
  - 它只終止**自己**用 `start_new_session=True` 啟動的子程序。逾時的順序是 SIGINT，等 5 秒，送 SIGTERM，等 3 秒，送 SIGKILL。
  - 逾時門檻由呼叫端傳入，例如 PR gate 的 snapshot 預設 900 秒、文件審查 180 秒。
  - 它只在 leader 是自己的程序群組時才 `killpg`。
- 使用它的是 `tooling/` 的 check_pr、gate、cleanup_pr、review_docs、pr_context，以及 `tests/tooling`。
- `scripts/check-full.sh` 是直接 `exec pytest`，**完全不經過它**。
- `pyproject.toml` 和 conftest 沒有 pytest-timeout、alarm 或 SIGTERM 設定。
- **結論：repo 裡沒有會對 check-full 的 pytest 送 SIGTERM 的看門狗。**

## 6. 收尾狀態

- 工作樹：
  - 主工作樹沒碰。
  - recut worktree 乾淨（b29c967）。
  - 審查用的 `stats` worktree 是 detached 在 ebc4495。
  - `lb` 是 detached 在 12293d5，是 10/31 實測用的。
  - `notes` 是本報告用的。
- 背景程序：沒有殘留的 pytest、check-full 或 keepalive。第一次那個 keepalive 留下的 `sleep` 已經清掉，清理順序也修正了。
- 沒有合併，沒有 push 程式分支，PR #38 沒有更新。

## 7. 待決事項（都需要使用者決定）

1. **怎麼重跑 check-full。** 建議：
   - 前景啟動，不要用 `&`。可以用 `setsid --wait` 在前景跑，或用 `setsid --fork` 讓它直接當 session leader。
   - 不設 `PYTEST_ADDOPTS`、不加外掛。
   - 保留每分鐘的記憶體監控。
   - 如果需要知道是誰送了 SIGTERM，可以考慮用 eBPF 或 auditd（需要權限）；faulthandler 只能告訴我們當下在跑哪個測試。
2. **通過之後：** fast-forward feat/stats-py314（df88dd1 → b29c967）並 push。也要決定 origin/feat/stats-recut 要不要同步到 b29c967。
3. 延續的事項：`docs/statistics_leaderboard_integration.md` 的過時行號（審查 #7）；同 horizon 單一 dataset 版本的作業問題（10/31 實測報告）；upstream 同步（f7a217c）。
