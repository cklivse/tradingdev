# 第 25 輪：PR body 拿掉可合併性主張、第 1 包在 c246355 上重驗、記憶體數字、被殺點之後的容器失敗清單

日期：2026-11-08。沒有開 PR、沒有在 #189／#190 留言、沒有建映像、沒有跑完整 check-full、沒有用 strace、沒有動五個 stats 分支的程式、沒有關任何 VS Code session。

## 結論

- **任務 1 完成**：五份 PR body 都改了（`2026-11-07-round22-pr-bodies/`）。
- **任務 2 完成**：第 1 包合進 `main` c246355，`scripts/check-fast.sh` 通過，`tests/domain/statistics` 36 passed。
- **任務 3：memmon.txt 沒有涵蓋三次被殺的任何一刻**。它的第一筆是 17:20:54，最後一筆是 17:40:25；三次被殺是 16:15、16:51、17:05。檔案裡也沒有 `free` 的值。所以 memmon.txt 的取樣不夠，不能用它判斷被殺當下的記憶體。
- **任務 4 完成**：第 4712–7588 個測試在乾淨 741fd84 上跑完，沒有被殺。117 個失敗或 error，全部是需要 strategy-runtime 容器的測試。

## 任務 1：PR body

五份共同的改動：

- 拿掉「Merged with `main` … without conflicts」這一行（第 4、5 包是「… (`pyproject.toml` auto-merged)」）。第 4、5 包保留 `uv sync --locked` 在合併後的樹上成功，因為那是實際跑過的結果。
- 驗證段改成：「Checks were run locally on this branch merged into `main`, verified at `main` <SHA>:」。第 1 包是 c246355，第 2–5 包仍是 741fd84（這輪只重驗第 1 包）。
- 拿掉 SIGTERM 那段。它不屬於任務 1 列的兩件事，而且寫著 741fd84。
- 容器那段（上游 aa2d3f4、`docs/development.md`）不變。
- 第 5 包「All five parts merged together onto `main` 741fd84」改成「into the same `main`」，SHA 由上一行的 verified at 提供。

第 1 包的額外說明改成只剩三件事：建立 `src/tradingdev/domain/statistics/`、該目錄在 `main` 上不存在、`main` 上沒有東西 import 它，也沒有動任何既有檔案（五個新增檔案）。

**拿掉的內容**：原本那段還有「所以除了自己的 36 個測試，完整套件不可能受影響」，以及三個掃整個 source tree 的測試檔在 741fd84 上有無此 PR 結果一致（44 個測試、同樣 5 個失敗）。後者是在某個 SHA 量到的結果，這輪沒有在 c246355 重量，所以一起拿掉。要放回的話，要寫成 verified at 741fd84。

第 3 包「Commits」段落的 bfb62ae（merge of `main` 35a2409）和第 1 包開頭「+9404/−3 (GitHub's count today)」沒改：前者描述固定的 commit，後者不是可合併性主張。後者仍會隨 #38 改變。

## 任務 2：第 1 包在 c246355 上

- `main` 現在是 c246355（`Merge pull request #204 from Kuan-Lun/fix/check-environment`），比 741fd84 多 48 個 commit。
- 69ecbda 合進 c246355：無衝突，diff 只有五個新增檔案，全在 `src/tradingdev/domain/statistics/` 和 `tests/domain/statistics/`。
- c246355 上沒有 `src/tradingdev/domain/statistics/`。整棵樹搜尋 `domain.statistics`，只有簡報 `docs/talks/tradingdev-introduction/`（slides.md、index.html）以文字提到「PR #38，尚未合併」，沒有 import。
- `scripts/check-fast.sh`：exit 0。
- `tests/domain/statistics`：36 passed。

## 任務 3：記憶體

### memmon.txt 與三次被殺的時間

| 項目 | 值 |
| --- | --- |
| memmon.txt 第一筆 | 17:20:54 |
| memmon.txt 最後一筆 | 17:40:25 |
| 取樣間隔 | 5 秒 |
| 三次被殺 | 16:15、16:51、17:05 UTC |
| 有 `free` 欄位的列數 | 0 |

三次被殺都在 memmon 開始之前。**取樣不夠，memmon.txt 沒有被殺那一刻的 `memory.current` 和 `free`。** 檔案裡的值（最高 6551289856）是之後沒被殺的 prefix run 的值，不能拿來代表被殺當下。

唯一涵蓋那段時間的數字是第 24 輪 17:1x 讀到的 `memory.peak` = 6547718144。這是 cgroup 建立以來 `memory.current` 的最高值（kernel 6.8 不能重設 peak），所以三次被殺時的 `memory.current` 都不超過 6547718144。它和實體記憶體 8328077312 差 1780359168 bytes（peak 是 8328077312 的 78.62%）。這是上界，不是被殺當下的取樣值；`free` 在那段時間沒有任何紀錄。

### 現在空閒時（2026-11-08 09:58 UTC）

Codespace 在 2026-11-08 09:43:36 重開過，所以昨天的程序都不在了。

```text
memory.current  3973656576
memory.peak     4157419520
memory.max      max
memory.high     max
memory.stat     anon 1610256384  file 2198654976  kernel 170266624  slab 142164296
free -b         total 8328077312  used 2899419136  free 220995584  buff/cache 5605015552  available 5428658176
```

現在只有一組 VS Code server（commit c4453f8e）。各程序 RSS：

| PID | RSS (kB) | 程序 |
| --- | ---: | --- |
| 633 | 592160 | extensionHost |
| 1630 | 495764 | Pylance language server |
| 583 | 161260 | server-main |
| 666 | 155524 | agentHost |
| 799 | 109772 | copilot-runtime |
| 660 | 101976 | fileWatcher |
| 639 | 79668 | ptyHost |
| 1061 | 72060 | markdown language server |
| 1241、4665 | 9380、9368 | 終端機 bash |
| 1090 | 6412 | python-envs `pet server` |
| 567 | 1884 | code-server 啟動 shell |

VS Code 程序樹 RSS 加總 1795252 kB（RSS 加總會重複計算共享頁面）。所有程序 RSS 加總 2299800 kB。其他較大的：`claude` 325088 kB、`dockerd` 92084 kB、`containerd` 49232 kB。

**關於「關掉一個編輯器 session」**：現在只有一個 VS Code server，沒有第二個可以關。昨天被殺時有兩組（第 24 輪記到的是兩個約 550 MB 和 517 MB 的 node 程序，各自還有 Python 延伸套件），但當時沒有記錄每組的完整 RSS，所以昨天第二組占多少，現在無法得知。

## 任務 4：第 4712–7588 個測試（乾淨 741fd84）

- 用第 24 輪的 `collect-base741.txt` 第 4712–7588 行（2877 個測試、105 個檔案，第一個是 `tests/e2e/test_codex_app_server.py`）。以檔案路徑依 collection 順序跑；`--collect-only` 得到 2877 個，和清單相符。沒有 strace；用 `default_signals_exec.py` 啟動；同時跑 `memmon.py`。
- 10:04:16–10:28:41 UTC，**沒有被殺**：84 failed、2760 passed、7 deselected、33 errors，1463.25 s。
- 這段期間 `memory.current` 最高 5021102080。這段不經過第 4705 個測試，所以和被殺的問題無關。
- 本機 Docker daemon 在跑（29.8.0-1），`docker images` 是空的。

117 個失敗或 error 的原因，依證據分四類：

- **A（45）**：失敗訊息直接含 `runtime_unavailable` 或 `Strategy runtime image 'tradingdev-strategy-runtime:0.1.0' is unavailable`。
- **B（58）**：訊息被 pytest 截斷。只重跑這 72 個並掛 `wrapsvc.py`，58 個在 `StrategyService` 的回傳裡看到 `runtime_unavailable`。用 `-vv` 看到的 diagnostics 是 `'code': 'runtime_unavailable', 'phase': 'contract'`。
- **C（8）**：`test_service_survives_runtime_failure[validate-*]`，在子程序裡跑 service，plugin 看不到。加 `-l` 重跑，子程序輸出裡有 `runtime_unavailable`／`Strategy runtime image`。
- **D（6）**：失敗訊息裡沒有直接出現 `runtime_unavailable`。這 6 個都在等 Docker 容器啟動 generated unit，失敗點都是 unit 沒啟動：
  - `test_codex_verifier.py::test_verifier_terminates_hanging_generated_code_and_removes_artifacts`：`Verifier never started the generated unit`（測試檢查 64 字元的 `container_id`）。
  - `test_generated_worker_cleanup.py::test_supervisor_removes_container_with_detached_generated_descendant[cancel_other_session, abrupt]`：`Generated unit did not reach the cleanup probe`；`[timeout]`：`preflight_failed`（預期 `preflight_timeout`），worker `returncode: 1`。
  - `test_strategy_check_workers.py::test_real_mcp_survives_exit_and_accepts_repaired_revision[validate_strategy, dry_run_strategy]`：沒有收到 `strategy_execution_failed`。

  D 類是根據「測試需要啟動容器 unit」加上「本機沒有映像」推斷的，訊息本身沒有寫出原因。

| 檔案 | 失敗 | 類別 |
| --- | ---: | --- |
| `tests/e2e/test_codex_verifier.py` | 3 | A2、D1 |
| `tests/e2e/test_llm_execution_plans.py` | 1 | B1 |
| `tests/e2e/test_workflow_verifier.py` | 33 | B33（全是 setup error） |
| `tests/integration/test_generated_protocol.py` | 16 | A16 |
| `tests/integration/test_generated_runtime.py` | 3 | A3 |
| `tests/integration/test_generated_worker_cleanup.py` | 3 | D3 |
| `tests/integration/test_mcp_cleanup.py` | 3 | B3 |
| `tests/integration/test_mcp_optimization.py` | 2 | B2 |
| `tests/integration/test_mcp_protocol.py` | 6 | A6 |
| `tests/integration/test_mcp_research_intake.py` | 1 | B1 |
| `tests/integration/test_parameter_experiments.py` | 2 | A2 |
| `tests/integration/test_preflight_temporary_files.py` | 8 | B8 |
| `tests/integration/test_preflight_workers.py` | 8 | B8 |
| `tests/integration/test_strategy_check_workers.py` | 14 | A4、C8、D2 |
| `tests/integration/test_strategy_isolation.py` | 9 | A9 |
| `tests/mcp/test_strategy_contracts.py` | 5 | A3、B2 |
| **合計** | **117** | A45、B58、C8、D6 |

和第 24 輪的第 1–4711 個測試合併（同一個 741fd84）：全部 7588 個測試中，容器相關的失敗是 108 + 117 = 225 個（其中 6 個是 D 類推斷）。另外第 24 輪有 6 個 dashboard timeout，是 strace 造成的，沒有 strace 時通過。

## 證據

`evidence/2026-11-08-round25/`：

- `tail-ids.txt`、`tail-files.txt`：第 4712–7588 個測試和它們的檔案
- `tail.xml`：該次的 junit XML
- `tail-summary.txt`：FAILED／ERROR 清單和結果行
- `memmon-tail.txt`：該次的記憶體取樣
- `diag-other2.jsonl`：72 個截斷訊息的 `wrapsvc.py` 判斷結果
- `other14.txt`：用 `-l` 重跑的 14 個
