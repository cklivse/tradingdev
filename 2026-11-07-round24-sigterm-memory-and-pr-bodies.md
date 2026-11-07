# 第 24 輪：SIGTERM 調查、PR body 改版、issue 編號

日期：2026-11-07。沒有開 PR、沒有留言、沒有建 Docker 映像或 builder、沒有動五個 stats 分支的程式。

第 22、23 輪沒有另外寫報告，因為兩輪要的 check-full 都被 SIGTERM 中斷。兩輪的結果併在本檔最後一節。

## 結論

- **任務 3（PR body）完成**：session-notes f4b9b9b，`2026-11-07-round22-pr-bodies/`。
- **任務 4（issue 編號）完成**：Issue B 是 #189，Issue A 是 #190。寫進 `ISSUES.md`，兩份草稿開頭也註明了（194a69e、64b1b53）。
- **任務 2（61–62%）完成**：被殺時跑的是第 4705／7588 個測試（62.01%），也就是 `tests/e2e/test_cleanup_workflow_evidence.py::test_cleanup_seed_and_evidence_use_real_mcp_and_preserve_history`。它是需要 strategy-runtime 容器的測試。
- **任務 1（記憶體）**：沒有證據顯示是 cgroup 記憶體限制造成的。被殺的原因仍然未知；這次加了 strace 跑到被殺點，沒有重現。

## 記憶體實際數值

調查開始時讀到的值（17:1x UTC，當時沒有在跑測試）：

```text
memory.max      max
memory.high     max
memory.peak     6547718144
memory.current  5081853952
memory.events   low 0 high 0 max 0 oom 0 oom_kill 0 oom_group_kill 0
memory.swap.max max
memory.swap.current 0
pids.max        9522
pids.peak       385
pids.current    326
/proc/self/cgroup  0::/init（cgroup2fs）
free -b         Mem total 8328077312，Swap 0
```

- `memory.max` 和 `memory.high` 都是 `max`，cgroup 本身沒有記憶體上限。實際的上限是實體記憶體 8328077312。
- 開機約在 14:35 UTC，三次被殺分別在 16:15、16:51、17:05 UTC，都在這段期間內。這段期間 `memory.peak` 是 6547718144（實體記憶體的 78.6%），所有事件計數都是 0。
- 沒有在跑測試時，平常就佔用約 5.2 GB，最大的是兩組 VS Code server（RSS 約 550 MB 和 517 MB 的 node 程序，各自還有 Python 延伸套件）。
- `dmesg`：`dmesg: read kernel buffer failed: Operation not permitted`
- `journalctl -k`：`No journal files were found.` / `-- No entries --`

## strace 的範圍（更正前提）

- 第一次 strace run 時說的「0 行」，是 pytest 還沒開始執行時讀的值。停掉時（9%）已經有 582 行，其中 18 筆 `kill(-N, SIGTERM)`。所以 strace 記錄得到程序樹內、包含對 process group 送的 signal。
- strace 會拖慢測試：prefix run 裡 `tests/adapters/test_dashboard_render.py` 的 6 個測試因 Streamlit `AppTest script run timed out after 15(s)` 失敗，但這 6 個在兩次沒有 strace 的 check-full 裡都通過。

## Prefix run：從第 1 個測試跑到被殺點

- 在乾淨的 741fd84 上，依 collection 順序跑前 222 個檔案，也就是第 1–4711 個測試，最後一個檔案是 `tests/e2e/test_cleanup_workflow_evidence.py`。
- 同時開著 strace（`kill, tkill, tgkill, rt_sigqueueinfo, pidfd_send_signal`）和每 5 秒一次的記憶體紀錄。
- 17:22:29–17:37:38 UTC，**沒有被殺**：92 failed、4597 passed、22 errors，903.11 s。
- strace 記到 115 筆 SIGTERM，目標全是測試自己啟動的子程序或子 process group。沒有任何 signal 指向 pytest（pid 369482）或它的 process group。
- 記憶體（183 筆取樣）：
  - `memory.current` 最高 6551289856，在 17:37:24，就是最後那個真實 MCP 的 e2e 測試執行時。
  - pytest RSS 最高 1376596 kB（17:30:14）。
  - 每一筆 `memory.events` 都是全 0。
  - 跑完後 `memory.peak` 是 6606610432。
- 最後一分鐘的取樣（被殺點附近）：

```text
17:37:09 current=6073806848 pytest_max_rss_kb=1324352
17:37:14 current=6162452480 pytest_max_rss_kb=1324328
17:37:19 current=6499803136 pytest_max_rss_kb=1324280
17:37:24 current=6551289856 pytest_max_rss_kb=1324280
17:37:29 current=6255665152 pytest_max_rss_kb=1319672
17:37:34 current=5894160384 pytest_max_rss_kb=1307896
```

**解讀（只寫看得到的）**：在被殺點，`memory.current` 衝到 6551289856，和之前三次被殺期間的高水位 6547718144 幾乎相同。但這次衝到 6.55 GB（之後的 peak 是 6.61 GB）沒有被殺，而且 cgroup 沒有任何記憶體事件。所以單純的記憶體門檻解釋不了，記憶體也還不能完全排除。另一個差別是 strace 讓整體變慢，這可能改變了時間點。發送者目前未知。

只跑被殺點附近的 289 個測試（`tests/domain/validation` 加三個 e2e 檔）時，53 秒跑完沒有被殺，`memory.current` 最高 6167977984。

## 容器測試失敗清單（第 1–4711 個測試，乾淨 741fd84）

114 個失敗或 error：108 個是 `runtime_unavailable`，6 個是 strace 造成的 dashboard timeout。

判斷方法：先檢查失敗訊息和 traceback 各層的區域變數。還沒判斷出原因的 50 個，不開 strace 重跑，用 plugin 包住 `StrategyService` 的所有 public method，看回傳值或 exception 裡有沒有 `runtime_unavailable`。結果 50 個全部是。

| 檔案 | 失敗 | 原因 |
| --- | --- | --- |
| `tests/app/test_comparison_plans.py` | 4 | runtime_unavailable |
| `tests/app/test_comparison_preflight.py` | 9 | runtime_unavailable |
| `tests/app/test_execution_plan_service.py` | 2 | runtime_unavailable |
| `tests/app/test_generated_strategy_job.py` | 6 | runtime_unavailable |
| `tests/app/test_preflight_service.py` | 15 | runtime_unavailable |
| `tests/app/test_research_preparation.py` | 11 | runtime_unavailable |
| `tests/app/test_strategy_experiments.py` | 22（error，fixture 階段） | runtime_unavailable |
| `tests/app/test_strategy_service.py` | 9 | runtime_unavailable |
| `tests/domain/strategies/test_loader_contract.py` | 11 | runtime_unavailable |
| `tests/domain/strategies/test_strategy_execution.py` | 9 | runtime_unavailable |
| `tests/domain/strategies/test_template_execution.py` | 9 | runtime_unavailable |
| `tests/e2e/test_cleanup_workflow_evidence.py` | 1 | runtime_unavailable |
| `tests/adapters/test_dashboard_render.py` | 6 | strace 造成的 timeout，沒有 strace 時通過 |

第 4712–7588 個測試（被殺點之後）沒有完整清單。目前已確認的有：

- `tests/mcp/test_strategy_contracts.py` 5 個 `runtime_unavailable`。
- 第 23 輪看到 `tests/integration/` 有多個檔案以相同原因失敗，包括 `test_mcp_cleanup`、`test_mcp_optimization`、`test_mcp_protocol`、`test_mcp_research_intake`、`test_parameter_experiments`、`test_preflight_temporary_files` 和 `test_preflight_workers`。這些是在 35a2409 + 第 1 包上看到的，還沒逐一分類。

和第 23 輪清單的差別：`test_mcp_*` 等整合測試都在被殺點之後，所以不在這份清單裡。被殺點之前的容器測試，主要在 `tests/app` 和 `tests/domain/strategies`。

## 乾淨 main 和第 1 包的對照

- 掃描整個 `src` 或 package 的三個檔案（`tests/integration/test_import_migration.py`、`tests/mcp/test_strategy_contracts.py`、`tests/mcp/test_strategy_save_failures.py`）：741fd84 和 741fd84 + 第 1 包（d6bbdcc）的 44 個測試結果逐一相同，都是 39 passed、5 failed，5 個都是 `runtime_unavailable`。
- 第 1 包自己的測試在 741fd84 上：36 passed。
- 第 1 包的 diff 只有 5 個新增檔案（`git diff --name-status 741fd84 d6bbdcc`，全部是 `A`）。
- 第 1 包完整套件的通過數：沒有。兩次 check-full 都在約 61% 被 SIGTERM 中斷。

## PR body 的改動（f4b9b9b）

- 驗證基準都改成 `main` 741fd84。
- 每一份都加了英文的具名排除說明，內容照指示：aa2d3f4、`tradingdev-strategy-runtime`、`docs/development.md`，乾淨 main 上相同，有映像的審閱者會是第一個完整結果。
- **自行加的一段**：目前兩次完整套件（乾淨 main 和第 1 包）都在約 61% 被外部 SIGTERM 中斷，所以本機還沒有任何完整結果，這件事在另外調查。沒寫的話，讀者會以為完整套件跑完了、只有容器測試失敗。不要的話刪掉那一段即可。
- 第 1 包另外寫了新目錄、沒有任何東西 import 它、沒有改動既有檔案，以及上面那三個掃描用測試的對照結果。
- 各包在 741fd84 上的測試數：
  - 第 1 包：36
  - 第 2 包：88
  - 第 3 包：130（含 MCP 測試，那個測試在程序內執行內建 KD 策略，不需要容器）
  - 第 4 包：146
  - 第 5 包：303
  - 五包合在一起：449，KD 四個釘值逐位相同
- 每一包 merge 後 check-fast 都通過。

## Issue 編號

- Issue B 是 #189、Issue A 是 #190，都是 2026-11-07 由 cklivse 開立。
- 貼上的正文和草稿只差開頭「依據 upstream main」那一行，其餘逐字相同。

## 第 22、23 輪的結果（補記）

- stats/3-plateau：merge 35a2409 的 commit 是 **bfb62ae**，上游改名的修正是 b1dac02，已 push（8a7a82a..b1dac02，fast-forward）。
- stats/5-comparison：docstring 改成描述規則，a216dc4，已 push（000c15e..a216dc4）。
- PR #38 的大小在 GitHub 上是 32 檔、+9404/−3。「23 檔、+8151」和歷史上的任何一點都對不上，PR body 用 32 檔、+9404。
- 第 22 輪的兩次 check-full（35a2409 + 第 1 包、35a2409 + 第 1–5 包）：第一次在 79% 以 EXIT 241 中斷，第二次依指示停掉。

## 證據

`evidence/2026-11-07-round24-sigterm/`：

- 記憶體取樣：`memmon.txt`
- collection 順序：`collect-base741.txt`
- 分類結果：`diag-prefix.jsonl`、`diag-other.jsonl`
- 用到的 plugin 和監控腳本：`dumpdiag.py`、`wrapsvc.py`、`memmon.py`
- prefix run 的 SIGTERM/SIGKILL strace 紀錄：`strace-prefix-term-kill.txt`

## 還開著的

- 被殺原因未知。下一步可以試：
  - 不用 strace，只開記憶體監控，再跑一次到被殺點，確認沒有 strace 時是否穩定重現。
  - 不用 `setsid` wrapper 跑，看是不是和 session leader 有關。
- 被殺點之後（第 4712–7588 個測試）的容器失敗清單還沒做完。
- scratchpad 裡還保留 `base741` 和 `p1on741` 兩個 worktree，之後要繼續查可以直接用。
