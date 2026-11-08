# 第 26 輪：五份 PR body 定稿（225 個容器測試、全部驗到 c246355）

日期：2026-11-08。沒有開 PR、沒有在 #189／#190 留言、沒有建映像、沒有跑完整 check-full、沒有動五個 stats 分支的程式。

## 結論

- **任務 1 完成**：五份 body 的容器段落改成帶 225 這個數字和清單連結的版本。第 1 包沒有放回 44 個測試的對照。
- **任務 2 完成**：第 2–5 包在 `main` c246355 上全部通過，四份 body 的 verified at 改成 c246355。五份現在都寫 c246355。
- **任務 3 沒有跑**：看過程式碼和 strace 紀錄後，這個實驗不管結果如何都不能判斷假設成立與否。理由在下面，要不要換別的實驗由你決定。
- 五份 body 全文在本檔最後，可直接複製。

## 任務 2：第 2–5 包在 c246355 上

每包各自合進 c246355（`main` 現在仍是 c246355）：

| 包 | 分支 head | 合併 | `uv sync --locked` | check-fast | 自己的測試 |
| --- | --- | --- | --- | --- | --- |
| 2 | 5ea494d | 無衝突，7 個新增檔案 | 成功 | 通過 | 88 passed |
| 3 | b1dac02 | 無衝突，8 個新增檔案 | 成功 | 通過 | 130 passed（含 `tests/mcp/test_optimization_failed_trials.py`） |
| 4 | ebac927 | 無衝突，`pyproject.toml` 自動合併；9 個新增、`pyproject.toml` 和 `uv.lock` 修改 | 成功 | 通過 | 146 passed |
| 5 | a216dc4 | 無衝突，`pyproject.toml` 自動合併；13 個新增、`pyproject.toml` 和 `uv.lock` 修改 | 成功 | 通過 | 303 passed |

測試數和 741fd84 上相同。跑完後每個 worktree 都沒有未追蹤或修改的檔案。

第 5 包 body 另外寫了兩項，所以也在 c246355 上重做：

- 五包一起合進 c246355（2、3、5 依序合併，1 和 4 經由 5 包含）：無衝突。check-fast 通過；`tests/domain/statistics` 加第 3 包的 MCP 測試，449 passed。
- KD 四個釘值：把 feat/stats-py314 的 KD fixture 和測試（9c1abc8 加入的 7 個檔案，取自 005854f）複製到這棵暫存樹，4 個測試通過。測試本身用的是 `pytest.approx(rel=1e-9)`，不能直接證明逐位相同，所以我另外算出四個值，用 `==` 和釘值比：

```text
days        366                  366                  EQUAL
sharpe      -7.565103143673017   -7.565103143673017   EQUAL
notional    5014735.715506879    5014735.715506879    EQUAL
cost_share  0.863481526386825    0.863481526386825    EQUAL
```

## 任務 1：容器段落

新段落包含：

- 上游 aa2d3f4 和 `docs/development.md` 的引用（保留）。
- 225／7588，其中 219 個回報 `runtime_unavailable`，6 個是容器沒有啟動、沒有錯誤碼。
- 清單的路徑和連結：`evidence/2026-11-08-round26/container-failures-741fd84.md`（session-notes 分支，cklivse/tradingdev 是 public）。
- 最後一句照指示。

**自己加的一句，要確認**：c246355 上 `scripts/check-full.sh` 第一步改成 `python -m tooling.environment full`（上游 51af970、b46e001，在 741fd84 之後）。缺映像時它會停下來，不跑品質檢查也不跑 pytest（`docs/development.md` 第 40–44 行）。我在 c246355 上跑了這個前置檢查（只解析映像，不啟動容器）：

```text
Environment check failed: Strategy runtime is unavailable: Strategy runtime image 'tradingdev-strategy-runtime:0.1.0' is unavailable; build the Dockerfile strategy-runtime target first. Prepare the local Docker Engine and Dockerfile strategy-runtime image; TRADINGDEV_STRATEGY_IMAGE selects a custom image. See docs/development.md (container build and verification).
rc=1
```

所以 225 只能在 741fd84 上量，在現在的 `main` 上，完整檢查不會啟動 pytest。body 的驗證基準是 c246355，容器數字卻是 741fd84，沒有這句的話讀者會問為什麼兩個 SHA 不同。所以我在段落裡加了「since upstream 51af970 (2026-11-08), `scripts/check-full.sh` also checks for the image first and does not start pytest without it」（引用固定的 commit，不寫「current `main`」，避免過期），並明寫 225 是在「a clean `main` 741fd84」上量的。不要的話刪掉那半句即可。

**清單怎麼來的**：225 是兩段合起來的，都在乾淨的 741fd84 上，依 collection 順序：

- 第 1–4711 個（第 24 輪，開 strace）：108 個。另有 6 個 dashboard 測試只因 strace 拖慢而 timeout，沒有 strace 時通過，沒有列入。
- 第 4712–7588 個（第 25 輪，沒有 strace）：117 個。

清單檔開頭有說明分兩段跑的原因（被殺點 4705）和 strace 的影響。每個測試標了證據類別：

| 類別 | 個數 | 證據 |
| --- | ---: | --- |
| A | 103 | 失敗訊息或 traceback 區域變數裡有 `runtime_unavailable` 或映像不存在的訊息 |
| B | 108 | 訊息被截斷；包住 `StrategyService` public method 的 plugin 在回傳值或 exception 看到 `runtime_unavailable` |
| C | 8 | service 在子程序裡跑；`pytest -l` 抓到的子程序輸出有 `runtime_unavailable` |
| D | 6 | 沒有錯誤碼；測試在等 Docker 容器 unit 啟動，沒有啟動。本機 Docker daemon 沒有任何映像 |

body 寫的「219 report `runtime_unavailable`」是 A+B+C。

## 任務 3：沒有跑，理由

假設是：被殺的測試清理 MCP 程序時對 process group 送 SIGTERM，而 setsid wrapper 讓 pytest 落在那個 group 裡。我查了三件事，結論是拿掉 setsid 改變不了結果，而且縮小範圍跑本來就不會被殺：

1. **MCP 函式庫不會打到 pytest 的 group**。專案用的 mcp 2.3.0，`stdio_client` 啟動 server 時一律 `start_new_session=True`（`mcp/client/stdio.py` 第 348 行）。清理時 `pgid = process.pid`，也就是 server 自己的 group（`mcp/os/posix/utilities.py` 第 27–32 行）。pytest 不在那個 group，不管 pytest 有沒有 setsid。
2. **產品和測試程式碼的 `killpg` 也都只打自己開的新 session**。741fd84 上所有 `killpg`（`worker_supervisor.py`、`tooling/process_guard.py`）的對象都是用 `start_new_session=True` 開的子程序，而且多數先檢查 `getpgid(pid) == pid`。沒有任何地方用 `getpgid(child)` 去打一個可能和 pytest 共用的 group。
3. **strace 實際看到的 `kill(-N)` 都不是 pytest 的 group**。第 24 輪的 strace 紀錄 221 行，打向 pytest（pid 369482）或 `-369482` 的筆數是 0；所有 `kill(-N)` 的 N 都是測試自己開的子程序 group。

另外，即使有程式碼打到「和 pytest 共用的 group」，拿掉 setsid 也救不了 pytest：沒有 setsid 時，沒有另開 session 的子程序仍和 pytest 在同一個 group（只是那個 group 改成啟動它的 shell 的），一樣會被打到。setsid 只決定那個 group 的 leader 是誰，不決定 pytest 在不在裡面。

最關鍵的是判讀問題：第 24 輪只跑被殺點附近的 289 個測試時，53 秒跑完，**沒有被殺**；開 strace 從第 1 個跑到第 4711 個，也沒有被殺；第 25 輪從 4712 跑到結尾也沒有被殺。到目前為止只有完整的 check-full 會被殺。所以縮小範圍、不用 setsid 跑到 4705 附近，如果沒被殺，也不能說明是 setsid 的關係，因為有 setsid 時縮小範圍本來就不會被殺。如果被殺，就推翻了「縮小範圍不會被殺」，但也不能說明和 setsid 有關。兩種結果都判斷不了這個假設。

要能判斷，先要找到一個用 setsid 會穩定被殺的縮小範圍，再拿掉 setsid 比對。目前唯一確定會被殺的是完整套件，而 c246355 上缺映像時完整檢查已經不會啟動 pytest。這屬於新的實驗設計，沒有做，由你決定。

記憶體那條線照指示關掉，這輪沒有再量。

## 證據

- `evidence/2026-11-08-round26/container-failures-741fd84.md`：225 個測試的完整清單（逐檔、逐測試、證據類別）。由 `evidence/2026-11-07-round24-sigterm/diag-prefix.jsonl`、`diag-other.jsonl` 和 `evidence/2026-11-08-round25/tail.xml`、`diag-other2.jsonl` 產生。

## 五份 PR body 全文

檔案在 `2026-11-07-round22-pr-bodies/`。第一行 `Title:` 是 PR 標題，不是 body 的一部分。第 2–5 包的 `#<P1>`、`#<P4>`，以及第 1 包的 `<AGREEMENT_URL>`，開 PR 時要換成實際值。

### pr1-foundation.md

````markdown
Title: feat(statistics): add input validation, scaling and period returns

## Why this is split into five PRs

At the 2026-10-27 meeting the review feedback on #38 was that the PR was too large to review. #38 is a single PR against `main` that currently adds 32 files, +9404/−3 (GitHub's count today). This series splits out its code and tests into five PRs, one commit per module group. Each PR's base matches what its code actually imports:

| PR | Branch | Modules | Imports from the statistics package |
| --- | --- | --- | --- |
| 1 (this PR) | `stats/1-foundation` | `_validation`, `_scaling`, `periods` | nothing |
| 2 | `stats/2-breakeven` | `breakeven` | `_validation` (1) |
| 3 | `stats/3-plateau` | `plateau` | `_validation`, `_scaling` (1) |
| 4 | `stats/4-sharpe` | `sharpe`, `performance`; adds `arch` | `_validation`, `_scaling`, `periods` (1) |
| 5 | `stats/5-comparison` | `comparison`, `benchmark` | `sharpe` (4), `periods` (1) |

Merge order: this PR first, then 2, 3 and 4 in any order, then 5 after 4. Until a prerequisite merges, a PR's diff against `main` also shows the prerequisite's commits. The split was agreed on #38 (<AGREEMENT_URL>).

Code and tests are copied file by file from `feat/stats-py314` without rewriting. After the split, two changes were made only on the split branches: PR 3 picks up an upstream rename, and PR 5 rewords one docstring. Both PRs explain them. What #38 has beyond this series is documentation (the full package guide in `__init__.py`, the methods documents, and the ARCHITECTURE/README sections). A KD fixture test PR follows once 2, 3 and 5 are in.

## This PR

- Shared input validation, exact power-of-two rescaling for extreme magnitudes, and UTC daily/monthly P&L and returns from an equity curve.
- `__init__.py` carries a one-line docstring; the full package guide comes later from #38.
- Depends on: nothing (based on `main`).

This PR creates `src/tradingdev/domain/statistics/`, a directory that does not exist on `main`. Nothing on `main` imports it, and the PR changes no existing file: its diff is five added files (four under `src/tradingdev/domain/statistics/`, one test file).

## Verification

This repository has no CI, so nothing on GitHub runs these checks. Checks were run locally on this branch merged into `main`, verified at `main` c246355:

- `scripts/check-fast.sh`: passes.
- This part's tests (`tests/domain/statistics`): 36 passed.

Why the full suite is not reported as green: since upstream aa2d3f4 (2026-11-06, `feat!: isolate generated strategies across product entrypoints`), the integration tests that execute generated strategies need a prebuilt `tradingdev-strategy-runtime` image. `docs/development.md` states that the tests do not download the image and that a missing daemon, required capability or prebuilt image makes them fail; since upstream 51af970 (2026-11-08), `scripts/check-full.sh` also checks for the image first and does not start pytest without it. On a clean `main` 741fd84, with no statistics code, 225 of the 7588 tests fail for this reason: 219 report `runtime_unavailable`, and the other 6 fail because their container never starts. The full list, with the evidence for each test and how the suite was run, is in [`evidence/2026-11-08-round26/container-failures-741fd84.md`](https://github.com/cklivse/tradingdev/blob/session-notes/evidence/2026-11-08-round26/container-failures-741fd84.md) on the `session-notes` branch. This environment does not have that image, so the full-suite evidence attached here is limited to that list. If a reviewer's environment has the image, their run will be the first complete result.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
````

### pr2-breakeven.md

````markdown
Title: feat(statistics): add break-even and cost analysis

Part 2 of the statistics split; #<P1> explains the split. Code and tests are copied unchanged from `feat/stats-py314`.

- Break-even win rate and turnover cost, computed only from trade records.

Depends on #<P1>. Until #<P1> merges, this diff also shows #<P1>'s commit.

## Verification

This repository has no CI, so nothing on GitHub runs these checks. Checks were run locally on this branch merged into `main`, verified at `main` c246355:

- `scripts/check-fast.sh`: passes.
- Statistics tests on this branch (`tests/domain/statistics`, Part 1 + Part 2): 88 passed.

Why the full suite is not reported as green: since upstream aa2d3f4 (2026-11-06, `feat!: isolate generated strategies across product entrypoints`), the integration tests that execute generated strategies need a prebuilt `tradingdev-strategy-runtime` image. `docs/development.md` states that the tests do not download the image and that a missing daemon, required capability or prebuilt image makes them fail; since upstream 51af970 (2026-11-08), `scripts/check-full.sh` also checks for the image first and does not start pytest without it. On a clean `main` 741fd84, with no statistics code, 225 of the 7588 tests fail for this reason: 219 report `runtime_unavailable`, and the other 6 fail because their container never starts. The full list, with the evidence for each test and how the suite was run, is in [`evidence/2026-11-08-round26/container-failures-741fd84.md`](https://github.com/cklivse/tradingdev/blob/session-notes/evidence/2026-11-08-round26/container-failures-741fd84.md) on the `session-notes` branch. This environment does not have that image, so the full-suite evidence attached here is limited to that list. If a reviewer's environment has the image, their run will be the first complete result.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
````

### pr3-plateau.md

````markdown
Title: feat(statistics): add parameter plateau analysis

Part 3 of the statistics split; #<P1> explains the split.

- Parameter plateau analysis over grid-search trials (is the best parameter set on a broad plateau or an isolated spike), with an MCP test showing that failed trials stay recorded.

Depends on #<P1>. Until #<P1> merges, this diff also shows #<P1>'s commit.

## Commits

Unlike the other parts, this branch has three commits:

1. 8a7a82a — the plateau module and tests, copied unchanged from `feat/stats-py314`.
2. bfb62ae — a merge of `main` 35a2409. Nothing conflicted, but after the merge the MCP test no longer collected.
3. b1dac02 — follows upstream aa2d3f4 (`feat!: isolate generated strategies across product entrypoints`), which moved `tradingdev.domain.strategies.loader.StrategyLoader` to `tradingdev.adapters.execution.strategy_factory.StrategyFactory` with the same `resolve_execution` interface. Only the import and two call sites in `tests/mcp/test_optimization_failed_trials.py` change. This follows an upstream rename and is not a defect in the statistics code.

The merge was used instead of a rebase so the already-pushed branch is not rewritten.

## Verification

This repository has no CI, so nothing on GitHub runs these checks. Checks were run locally on this branch merged into `main`, verified at `main` c246355:

- `scripts/check-fast.sh`: passes.
- Statistics tests plus `tests/mcp/test_optimization_failed_trials.py` (Part 1 + Part 3): 130 passed. The MCP test runs the bundled KD strategy in process and does not need the container image.

Why the full suite is not reported as green: since upstream aa2d3f4 (2026-11-06, `feat!: isolate generated strategies across product entrypoints`), the integration tests that execute generated strategies need a prebuilt `tradingdev-strategy-runtime` image. `docs/development.md` states that the tests do not download the image and that a missing daemon, required capability or prebuilt image makes them fail; since upstream 51af970 (2026-11-08), `scripts/check-full.sh` also checks for the image first and does not start pytest without it. On a clean `main` 741fd84, with no statistics code, 225 of the 7588 tests fail for this reason: 219 report `runtime_unavailable`, and the other 6 fail because their container never starts. The full list, with the evidence for each test and how the suite was run, is in [`evidence/2026-11-08-round26/container-failures-741fd84.md`](https://github.com/cklivse/tradingdev/blob/session-notes/evidence/2026-11-08-round26/container-failures-741fd84.md) on the `session-notes` branch. This environment does not have that image, so the full-suite evidence attached here is limited to that list. If a reviewer's environment has the image, their run will be the first complete result.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
````

### pr4-sharpe.md

````markdown
Title: feat(statistics): add Sharpe inference and performance summary

Part 4 of the statistics split; #<P1> explains the split. Code and tests are copied unchanged from `feat/stats-py314`.

- Sharpe ratio with a bootstrap interval, probabilistic and deflated Sharpe, and a performance summary computed from raw run outputs; adds the `arch` dependency (`pyproject.toml`, `uv.lock`).
- The literature behind each step is in `docs/statistics_bootstrap_methods.md` on #38.

Depends on #<P1>. Until #<P1> merges, this diff also shows #<P1>'s commit.

## Verification

This repository has no CI, so nothing on GitHub runs these checks. Checks were run locally on this branch merged into `main`, verified at `main` c246355:

- `uv sync --locked` succeeds on the merged tree.
- `scripts/check-fast.sh`: passes.
- Statistics tests on this branch (Part 1 + Part 4): 146 passed.

Why the full suite is not reported as green: since upstream aa2d3f4 (2026-11-06, `feat!: isolate generated strategies across product entrypoints`), the integration tests that execute generated strategies need a prebuilt `tradingdev-strategy-runtime` image. `docs/development.md` states that the tests do not download the image and that a missing daemon, required capability or prebuilt image makes them fail; since upstream 51af970 (2026-11-08), `scripts/check-full.sh` also checks for the image first and does not start pytest without it. On a clean `main` 741fd84, with no statistics code, 225 of the 7588 tests fail for this reason: 219 report `runtime_unavailable`, and the other 6 fail because their container never starts. The full list, with the evidence for each test and how the suite was run, is in [`evidence/2026-11-08-round26/container-failures-741fd84.md`](https://github.com/cklivse/tradingdev/blob/session-notes/evidence/2026-11-08-round26/container-failures-741fd84.md) on the `session-notes` branch. This environment does not have that image, so the full-suite evidence attached here is limited to that list. If a reviewer's environment has the image, their run will be the first complete result.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
````

### pr5-comparison.md

````markdown
Title: feat(statistics): add paired comparison and benchmark comparison

Part 5 of the statistics split; #<P1> explains the split.

- Paired bootstrap comparison of strategies on the same data, and buy-and-hold benchmark returns with a strategy's regression on them.

Depends on #<P4> (and on #<P1> through it). Until those merge, this diff also shows their commits.

## Commits

1. 000c15e — the comparison and benchmark modules and tests, copied unchanged from `feat/stats-py314`.
2. a216dc4 — docstring only. The `benchmark` module docstring had listed the product benchmark's instruments (BTC/USDT, S&P 500), but that list belongs to `tradingdev.domain.benchmark`'s `BENCHMARKS` table, and upstream 947a372 has since added Taiwan equities. It now describes the rule: the upstream table decides the instruments, and BTC/USDT is kept only as an example. No code change.

## Verification

This repository has no CI, so nothing on GitHub runs these checks. Checks were run locally on this branch merged into `main`, verified at `main` c246355:

- `uv sync --locked` succeeds on the merged tree.
- `scripts/check-fast.sh`: passes.
- Statistics tests on this branch (Parts 1, 4 and 5): 303 passed.
- All five parts merged together into the same `main`: statistics tests plus the Part 3 MCP test, 449 passed; `scripts/check-fast.sh` passes.
- The four pinned KD figures from #38's fixture (366 UTC days, annualised daily Sharpe, traded notional, cost share of net P&L), recomputed on that combined tree, are bitwise equal to the pinned values.

Why the full suite is not reported as green: since upstream aa2d3f4 (2026-11-06, `feat!: isolate generated strategies across product entrypoints`), the integration tests that execute generated strategies need a prebuilt `tradingdev-strategy-runtime` image. `docs/development.md` states that the tests do not download the image and that a missing daemon, required capability or prebuilt image makes them fail; since upstream 51af970 (2026-11-08), `scripts/check-full.sh` also checks for the image first and does not start pytest without it. On a clean `main` 741fd84, with no statistics code, 225 of the 7588 tests fail for this reason: 219 report `runtime_unavailable`, and the other 6 fail because their container never starts. The full list, with the evidence for each test and how the suite was run, is in [`evidence/2026-11-08-round26/container-failures-741fd84.md`](https://github.com/cklivse/tradingdev/blob/session-notes/evidence/2026-11-08-round26/container-failures-741fd84.md) on the `session-notes` branch. This environment does not have that image, so the full-suite evidence attached here is limited to that list. If a reviewer's environment has the image, their run will be the first complete result.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
````
