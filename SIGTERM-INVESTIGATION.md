# check-full 被 SIGTERM 中斷：已知事實與未解問題

整理日期：2026-11-08。本檔只收已記錄的事實和還沒有答案的問題，不寫結論、不列下一步。來源是本分支各輪報告和 `evidence/` 下的檔案，每一項都標了出處。

原始 log 和暫存 worktree 放在 `/tmp` 的 scratchpad，codespace 在 2026-11-08 09:43:36 UTC 重開後已經不在。所以下面只有當時寫進報告或證據檔的內容。

## 1. 被中斷的執行

| 日期（UTC） | 執行 | 進度與當時的測試 | exit | 出處 |
| --- | --- | --- | --- | --- |
| 2026-10-31 07:57–08:32 | check-full，recut worktree，collected 4847、selected 4833 | 79%，35 分 29 秒；剛開始跑 `tests/integration/test_mcp_protocol.py`；log 只有 `Terminated` | 143 | `2026-10-31-round9-review-and-check-full.md` §4 |
| 2026-11-01 15:15 開始 | check-full，`988cf54` | 76%，`tests/e2e/test_workflow_verifier.py`；之前沒有任何失敗 | 241 | `2026-11-01-round16-active-return-rename.md` |
| 2026-11-07 | check-full，35a2409 + 第 1 包 | 79% | 241 | `2026-11-07-round24-sigterm-memory-and-pr-bodies.md`「第 22、23 輪的結果」 |
| 2026-11-07 | check-full，乾淨 `main` 741fd84；以及 741fd84 + 第 1 包 | 兩次都在約 61% | 未記錄 | 同上，「乾淨 main 和第 1 包的對照」 |

第 24 輪記錄的被殺點：第 4705／7588 個測試（62.01%），`tests/e2e/test_cleanup_workflow_evidence.py::test_cleanup_seed_and_evidence_use_real_mcp_and_preserve_history`。這是 741fd84 的 collection 順序（`evidence/2026-11-07-round24-sigterm/collect-base741.txt`）。這個測試啟動真實的 MCP 程序，需要 strategy-runtime 容器。

第 24 輪記錄 2026-11-07 有三次被殺，時間是 16:15、16:51、17:05 UTC；開機約在 14:35 UTC。**哪個時間對應上表哪一次執行，報告沒有記錄。** 4705 是不是三次共同的被殺點，報告也沒有分開寫。

exit code 的意思：

- 143 是 shell 的 128 + 15。
- 241 是 `tools/default_signals_exec.py` 回報的值：它對子程序的狀態做 `sys.exit(os.waitstatus_to_exitcode(status))`，被 signal 15 殺掉時是 `sys.exit(-15)`，也就是 256 − 15。
- 兩者都表示 pytest 收到 signal 15。

## 2. 跑完沒有被中斷的執行

### 完整套件

| 日期 | 執行 | 結果 | 出處 |
| --- | --- | --- | --- |
| 2026-10-31 08:50–09:47 | check-full，`setsid --wait`，同一 worktree | 跑完，12 個失敗（之後確認是執行方式造成的 SIGINT 被忽略） | round 9 §4 |
| 2026-10-31 11:12–12:02 | check-full，b29c967 | 4833 passed，exit 0 | `2026-10-31-round10-clean-check-full-and-push.md` |
| 2026-11-01 | check-full，c5fff7a，fork + setsid + SIG_DFL wrapper | 7476 passed，exit 0 | `2026-11-01-round14-sync-dsr-p3.md` |
| 2026-11-01 | check-full，8b4336e，同一 wrapper | 7480 passed，exit 0，56 分 06 秒 | `2026-11-01-round15b-stash-split.md` |
| 2026-11-01 | check-full，`988cf54`（被中斷的那個 commit 重跑），同一 wrapper | 7480 passed，exit 0，58 分 48 秒 | round 16 |

2026-11-01 之後，報告裡沒有任何一次完整套件跑完。上游 aa2d3f4（2026-11-06，`feat!: isolate generated strategies across product entrypoints`）之後，執行生成策略的測試需要預建的 `tradingdev-strategy-runtime` 映像，這個環境沒有。

### 分段執行（都在乾淨 741fd84 上，依 collection 順序）

| 日期 | 範圍 | 條件 | 結果 | 出處 |
| --- | --- | --- | --- | --- |
| 2026-11-07 | 第 1 個到 9% | 開 strace | 依指示停掉，沒有被殺 | round 24「strace 的範圍」 |
| 2026-11-07 17:22:29–17:37:38 | 第 1–4711 個（前 222 個檔案，含被殺點） | 開 strace，`memmon.py` 每 5 秒 | 跑完沒有被殺：92 failed、4597 passed、22 errors，903.11 s | round 24「Prefix run」 |
| 2026-11-07 | 被殺點附近 289 個（`tests/domain/validation` 加三個 e2e 檔） | 沒有記錄是否開 strace 或用 wrapper | 53 秒跑完，沒有被殺 | round 24 |
| 2026-11-08 10:04:16–10:28:41 | 第 4712–7588 個 | 沒有 strace，用 `default_signals_exec.py`，`memmon.py` | 跑完沒有被殺：84 failed、2760 passed、33 errors，1463.25 s | `2026-11-08-round25-pr-bodies-memory-tail-failures.md` |

## 3. 記憶體

cgroup 設定（第 24 輪，2026-11-07 17:1x UTC，沒有在跑測試時讀）：

```text
memory.max      max
memory.high     max
memory.peak     6547718144
memory.current  5081853952
memory.events   low 0 high 0 max 0 oom 0 oom_kill 0 oom_group_kill 0
memory.swap.max max
memory.swap.current 0
/proc/self/cgroup  0::/init（cgroup2fs）
free -b         Mem total 8328077312，Swap 0
```

- `memory.max` 和 `memory.high` 都是 `max`，所以 `memory.events` 的 `high`、`max` 計數不會增加，不管用了多少記憶體。它們是 0 不能當成反證。
- `memory.peak` 6547718144 是讀取時這個 cgroup 自建立以來 `memory.current` 的最高值（kernel 6.8，不能重設）。2026-11-07 的三次被殺都在讀取之前。所以三次被殺時，這個 cgroup 的 `memory.current` 都不超過 6547718144。這比實體記憶體 8328077312 少 1780359168 bytes（peak 是 78.62%）。
- 這個上界排除的是：這個 cgroup 的記憶體在被殺時達到實體記憶體。它量不到 cgroup 以外的記憶體使用。
- `evidence/2026-11-07-round24-sigterm/memmon.txt` 涵蓋 17:20:54–17:40:25，三次被殺都不在範圍內，也沒有 `free` 欄位。
- prefix run 在被殺點（17:37:24，最後那個真實 MCP 的 e2e 測試）的 `memory.current` 是 6551289856，沒有被殺；之後 `memory.peak` 是 6606610432。
- 2026-11-08 第 4712–7588 個那次，`memory.current` 最高 5021102080。
- 2026-10-31 的記錄（round 9、10）：第 2 次執行最低可用 1144 MB，第 3 次最低可用 2253 MB，`memory.events` 的 `oom`、`oom_kill` 都是 0；第 1 次（被殺的那次）沒有記憶體紀錄。

## 4. 誰送的 signal

### strace

prefix run（第 1–4711 個）用 strace 記錄 `kill, tkill, tgkill, rt_sigqueueinfo, pidfd_send_signal`。SIGTERM 和 SIGKILL 的紀錄在 `evidence/2026-11-07-round24-sigterm/strace-prefix-term-kill.txt`：

- 共 221 筆，全部是 `kill`。
- 115 筆 SIGTERM：104 筆是 `kill(-N, SIGTERM)`（對 process group），11 筆是對單一 PID。
- 106 筆 SIGKILL。
- pytest 的 PID 是 369482。它是其中 23 筆的發送者。沒有任何一筆的對象是 369482 或 -369482。
- 所有對象都是測試自己啟動的子程序或子程序的 process group。
- 第一次 strace run 停在 9% 時有 582 行，其中 18 筆 `kill(-N, SIGTERM)`。這次證明 strace 記錄得到程序樹內的 signal，包括對 process group 送的。
- 這次 run 沒有被殺，所以沒有記錄到被殺那一刻的 signal。
- strace 會拖慢測試：`tests/adapters/test_dashboard_render.py` 的 6 個測試因 Streamlit `AppTest script run timed out after 15(s)` 失敗，沒有 strace 時通過。

### 程式碼

- mcp 2.3.0 的 `stdio_client` 啟動 server 時用 `start_new_session=True`（`mcp/client/stdio.py` 第 348 行）。清理時 `pgid = process.pid`，也就是 server 自己的 group（`mcp/os/posix/utilities.py` 第 27–32 行）。
- 741fd84 上 repo 裡所有 `os.killpg` 的對象（`src/tradingdev/adapters/execution/worker_supervisor.py`、`tooling/process_guard.py`）都是用 `start_new_session=True` 啟動的子程序，多數先檢查 `getpgid(pid) == pid`。
- `scripts/check-full.sh` 直接 `exec pytest`，不經過 `tooling/process_guard.py`。`pyproject.toml` 和 conftest 沒有 pytest-timeout、alarm 或 SIGTERM 設定（round 9 §5）。
- 2026-11-01 被殺時，兩個審查子代理沒有 kill 指令（round 16）。

### 系統紀錄

- `dmesg`：`dmesg: read kernel buffer failed: Operation not permitted`
- `journalctl -k`：`No journal files were found.` / `-- No entries --`

## 5. 啟動方式

- 2026-10-31 第 1 次（exit 143）：報告沒有記錄啟動方式。第 2 次才寫明改用 `setsid --wait`。
- 2026-11-01 被中斷的那次：報告寫重跑「用同一個 fork + setsid + SIG_DFL wrapper」。
- 2026-11-07 的被中斷執行：報告沒有逐次記錄啟動方式。其中 79% 那次的 exit 241，和 `default_signals_exec.py` 回報 signal 15 的值相同。
- wrapper 的作法：fork，子程序 `os.setsid()`、把 SIGINT 和 SIGQUIT 設回 SIG_DFL，再 exec（`tools/default_signals_exec.py`）。pytest 因此是自己 session 和 process group 的 leader。

## 6. 51af970 之後

上游 51af970（2026-11-08，`fix: validate development prerequisites before running checks`）在 `scripts/check-full.sh` 開頭加了 `python -m tooling.environment full`。`docs/development.md`（c246355）寫：完整測試共用產品的 `DockerRuntime.resolve()`，確認 Docker 端點、daemon 資源能力、策略映像及有效資源設定；失敗時不啟動品質檢查或 pytest，也不自動下載或建置映像。

2026-11-08 在 c246355 上執行這個前置檢查：

```text
Environment check failed: Strategy runtime is unavailable: Strategy runtime image 'tradingdev-strategy-runtime:0.1.0' is unavailable; build the Dockerfile strategy-runtime target first. Prepare the local Docker Engine and Dockerfile strategy-runtime image; TRADINGDEV_STRATEGY_IMAGE selects a custom image. See docs/development.md (container build and verification).
rc=1
```

這個環境 Docker daemon 在跑（29.8.0-1），`docker images` 是空的。所以在 c246355 和之後的 `main` 上，這個環境的 `scripts/check-full.sh` 不會啟動 pytest。

## 7. 未解

- 誰送了 SIGTERM。
- 2026-11-07 的三個時間點各對應哪一次執行，以及每一次各停在第幾個測試。
- 2026-10-31 第 1 次的啟動方式。
- 為什麼 2026-11-01 和之前的完整套件有幾次跑完、有幾次被殺；被殺的那次重跑同一個 commit 就跑完了。
- 為什麼分段執行（包括經過被殺點的 prefix run）都沒有被殺。prefix run 開了 strace，執行時間和其他執行不同。
- 被殺時 cgroup 以外的記憶體狀況。
- 2026-11-07 被殺時 `free` 的值，以及被殺當下 `memory.current` 的取樣值。
