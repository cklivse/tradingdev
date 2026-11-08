# 第 29 輪：上游環境檢查器的輸出、環境段落改寫、五包在 1ea5276 上重驗

日期：2026-11-08。沒有改五個包的程式、沒有把 #207–#209 改成 ready、沒有開第 5 包、沒有在 #205–#209 留言、沒有建映像、沒有跑完整 check-full。PR 上的 body 沒有動，只更新了本分支的檔案。

## 結論

- **任務 1**：`tooling.environment full` 失敗（exit 1），原因是缺 strategy-runtime 映像。`docs`、`format`、`fast`、`tooling` 四個 profile 都通過（沒有輸出、exit 0）。輸出照抄在下面。
- **任務 2 完成**：五份 body 的環境段落改成以這個輸出為主，225 的清單降成最後一句的參考。說明 741fd84 和驗證基準不同的那句已刪掉。
- **任務 3 完成**：五包在 `main` 1ea5276 上全部通過，五份 body 的 verified at 改成 1ea5276。

## 任務 1：`tooling.environment` 的輸出（一字不改）

在 `main` 1ea5276 的乾淨 worktree，`uv sync --locked --all-extras` 之後，從 repo 根目錄執行。stdout 和 stderr 分開記錄：

```text
$ .venv/bin/python -m tooling.environment --help
[stdout]
usage: python -m tooling.environment [-h] {docs,format,fast,tooling,full}

Check only the prerequisites needed by a development operation.

positional arguments:
  {docs,format,fast,tooling,full}

options:
  -h, --help            show this help message and exit
[stderr]
[exit 0]

$ .venv/bin/python -m tooling.environment docs
[stdout]
[stderr]
[exit 0]

$ .venv/bin/python -m tooling.environment format
[stdout]
[stderr]
[exit 0]

$ .venv/bin/python -m tooling.environment fast
[stdout]
[stderr]
[exit 0]

$ .venv/bin/python -m tooling.environment tooling
[stdout]
[stderr]
[exit 0]

$ .venv/bin/python -m tooling.environment full
[stdout]
[stderr]
Environment check failed: Strategy runtime is unavailable: Strategy runtime image 'tradingdev-strategy-runtime:0.1.0' is unavailable; build the Dockerfile strategy-runtime target first. Prepare the local Docker Engine and Dockerfile strategy-runtime image; TRADINGDEV_STRATEGY_IMAGE selects a custom image. See docs/development.md (container build and verification).
[exit 1]

```

- profile 只有這五個（`argparse` 的 `choices=("docs", "format", "fast", "tooling", "full")`）。
- `scripts/check-docs.sh` 用 `docs`，`scripts/check-tooling.sh` 用 `tooling`，`scripts/check-full.sh` 用 `full`。
- 看過 `tooling/environment.py`：`full` 以外的 profile 只檢查 Python 套件，`tooling` 和 `full` 另外檢查 `git`、`uv` 指令；只有 `full` 檢查策略映像。這些檢查都不改檔案，跑完 worktree 沒有變動。
- 只有 `full` 失敗，所以你的假設成立：它檢查的是 Docker 映像，不是簡報工具鏈。

**commit 歸屬和你說的不同**：dadf8d3（`fix(presentations): integrate main environment checks`）是 merge commit，父節點是 894d8b9 和 c246355。它對第一個父節點的 diff 裡有 `check-full.sh` 那一行，但那是從 c246355 帶進來的。在 `main` 上最早加入這一行的是 51af970（`fix: validate development prerequisites before running checks`），`git log 741fd84..1ea5276 -- scripts/check-full.sh` 只列出 51af970。新的 body 不引用任何 commit，所以不受影響。

## 任務 2：新的環境段落

結構：

1. `scripts/check-full.sh` 第一步是 repo 自己的前置檢查 `python -m tooling.environment full`；在這個環境它失敗（exit 1），所以 pytest 不會啟動。接著貼 stderr 原文。
2. 同一個檢查器的 `fast` profile 通過，所以上面列的是 check-fast 和該包自己的測試。有映像的審閱者跑 check-full 會是第一個完整結果。
3. 最後一句是參考：在舊的 `main`（741fd84，前置檢查加入之前），225／7588 個測試因同樣缺映像而失敗，當時沒有任何 statistics 程式碼。附上釘住的清單連結（eeec723）。

刪掉的：上游 aa2d3f4 和 `docs/development.md` 的引用（工具輸出本身寫了 `See docs/development.md`），以及解釋驗證基準和 741fd84 不同的那句。

第 3 包的「Commits」段落仍然引用 aa2d3f4，那是說明 b1dac02 跟著上游改名，和環境段落無關，沒有動。

## 任務 3：五包在 1ea5276 上

`main` 是 1ea5276（`Merge pull request #203 from Kuan-Lun/feat/mermaid-presentation-diagrams`），比 c246355 多 23 個 commit。分支 head：1 = 69ecbda、2 = 5ea494d、3 = b1dac02、4 = ebac927、5 = a216dc4（都和 PR 上的相同）。

| 包 | 合併 | 改動 | `uv sync --locked` | check-fast | 自己的測試 |
| --- | --- | --- | --- | --- | --- |
| 1 | 無衝突 | 5 個新增 | 成功 | 通過 | 36 passed |
| 2 | 無衝突 | 7 個新增 | 成功 | 通過 | 88 passed |
| 3 | 無衝突 | 8 個新增 | 成功 | 通過 | 130 passed（含 `tests/mcp/test_optimization_failed_trials.py`） |
| 4 | 無衝突 | 9 個新增、2 個修改（`pyproject.toml`、`uv.lock`） | 成功 | 通過 | 146 passed |
| 5 | 無衝突 | 13 個新增、2 個修改 | 成功 | 通過 | 303 passed |
| 五包一起 | 依序合併 2、3、5，無衝突（1、4 經由 5 包含） | 18 個新增、2 個修改 | 成功 | 通過 | 449 passed（statistics 加第 3 包的 MCP 測試） |

每個 worktree 跑完都沒有未追蹤或修改的檔案。

KD 四個釘值：把 9c1abc8 的 KD fixture 和測試（取自 005854f）複製到五包合併的暫存樹，4 passed。另外用 `==` 比對：

```text
days        366                  366                  EQUAL
sharpe      -7.565103143673017   -7.565103143673017   EQUAL
notional    5014735.715506879    5014735.715506879    EQUAL
cost_share  0.863481526386825    0.863481526386825    EQUAL
```

## 五份 PR body 全文

檔案在 `2026-11-07-round22-pr-bodies/`。第一行 `Title:` 是 PR 標題，不是 body 的一部分。第 1 包已經刪掉 agreement 那句；第 2–4 包是 #206；第 5 包是 #209 和 #206（第 5 包的 PR 還沒開）。

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

Merge order: this PR first, then 2, 3 and 4 in any order, then 5 after 4. Until a prerequisite merges, a PR's diff against `main` also shows the prerequisite's commits.

Code and tests are copied file by file from `feat/stats-py314` without rewriting. After the split, two changes were made only on the split branches: PR 3 picks up an upstream rename, and PR 5 rewords one docstring. Both PRs explain them. What #38 has beyond this series is documentation (the full package guide in `__init__.py`, the methods documents, and the ARCHITECTURE/README sections). A KD fixture test PR follows once 2, 3 and 5 are in.

## This PR

- Shared input validation, exact power-of-two rescaling for extreme magnitudes, and UTC daily/monthly P&L and returns from an equity curve.
- `__init__.py` carries a one-line docstring; the full package guide comes later from #38.
- Depends on: nothing (based on `main`).

This PR creates `src/tradingdev/domain/statistics/`, a directory that does not exist on `main`. Nothing on `main` imports it, and the PR changes no existing file: its diff is five added files (four under `src/tradingdev/domain/statistics/`, one test file).

## Verification

This repository has no CI, so nothing on GitHub runs these checks. Checks were run locally on this branch merged into `main`, verified at `main` 1ea5276:

- `scripts/check-fast.sh`: passes.
- This part's tests (`tests/domain/statistics`): 36 passed.

Why there is no full-suite result: `scripts/check-full.sh` starts with the repository's own prerequisite check, `python -m tooling.environment full`. In this environment that check fails (exit 1), so pytest never starts:

```text
Environment check failed: Strategy runtime is unavailable: Strategy runtime image 'tradingdev-strategy-runtime:0.1.0' is unavailable; build the Dockerfile strategy-runtime target first. Prepare the local Docker Engine and Dockerfile strategy-runtime image; TRADINGDEV_STRATEGY_IMAGE selects a custom image. See docs/development.md (container build and verification).
```

The `fast` profile of the same checker passes, so the checks listed above are `scripts/check-fast.sh` and this part's own tests. If a reviewer's environment has the strategy-runtime image, their `scripts/check-full.sh` run will be the first complete result.

For reference only: on an older `main` (741fd84, before this prerequisite check existed), 225 of the 7588 tests failed for the same missing image, with no statistics code present ([list](https://github.com/cklivse/tradingdev/blob/eeec7235e956db8ab1d8cf68af898b4a5480460c/evidence/2026-11-08-round26/container-failures-741fd84.md)).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
````

### pr2-breakeven.md

````markdown
Title: feat(statistics): add break-even and cost analysis

Part 2 of the statistics split; #206 explains the split. Code and tests are copied unchanged from `feat/stats-py314`.

- Break-even win rate and turnover cost, computed only from trade records.

Depends on #206. Until #206 merges, this diff also shows #206's commit.

## Verification

This repository has no CI, so nothing on GitHub runs these checks. Checks were run locally on this branch merged into `main`, verified at `main` 1ea5276:

- `scripts/check-fast.sh`: passes.
- Statistics tests on this branch (`tests/domain/statistics`, Part 1 + Part 2): 88 passed.

Why there is no full-suite result: `scripts/check-full.sh` starts with the repository's own prerequisite check, `python -m tooling.environment full`. In this environment that check fails (exit 1), so pytest never starts:

```text
Environment check failed: Strategy runtime is unavailable: Strategy runtime image 'tradingdev-strategy-runtime:0.1.0' is unavailable; build the Dockerfile strategy-runtime target first. Prepare the local Docker Engine and Dockerfile strategy-runtime image; TRADINGDEV_STRATEGY_IMAGE selects a custom image. See docs/development.md (container build and verification).
```

The `fast` profile of the same checker passes, so the checks listed above are `scripts/check-fast.sh` and this part's own tests. If a reviewer's environment has the strategy-runtime image, their `scripts/check-full.sh` run will be the first complete result.

For reference only: on an older `main` (741fd84, before this prerequisite check existed), 225 of the 7588 tests failed for the same missing image, with no statistics code present ([list](https://github.com/cklivse/tradingdev/blob/eeec7235e956db8ab1d8cf68af898b4a5480460c/evidence/2026-11-08-round26/container-failures-741fd84.md)).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
````

### pr3-plateau.md

````markdown
Title: feat(statistics): add parameter plateau analysis

Part 3 of the statistics split; #206 explains the split.

- Parameter plateau analysis over grid-search trials (is the best parameter set on a broad plateau or an isolated spike), with an MCP test showing that failed trials stay recorded.

Depends on #206. Until #206 merges, this diff also shows #206's commit.

## Commits

Unlike the other parts, this branch has three commits:

1. 8a7a82a — the plateau module and tests, copied unchanged from `feat/stats-py314`.
2. bfb62ae — a merge of `main` 35a2409. Nothing conflicted, but after the merge the MCP test no longer collected.
3. b1dac02 — follows upstream aa2d3f4 (`feat!: isolate generated strategies across product entrypoints`), which moved `tradingdev.domain.strategies.loader.StrategyLoader` to `tradingdev.adapters.execution.strategy_factory.StrategyFactory` with the same `resolve_execution` interface. Only the import and two call sites in `tests/mcp/test_optimization_failed_trials.py` change. This follows an upstream rename and is not a defect in the statistics code.

The merge was used instead of a rebase so the already-pushed branch is not rewritten.

## Verification

This repository has no CI, so nothing on GitHub runs these checks. Checks were run locally on this branch merged into `main`, verified at `main` 1ea5276:

- `scripts/check-fast.sh`: passes.
- Statistics tests plus `tests/mcp/test_optimization_failed_trials.py` (Part 1 + Part 3): 130 passed. The MCP test runs the bundled KD strategy in process and does not need the container image.

Why there is no full-suite result: `scripts/check-full.sh` starts with the repository's own prerequisite check, `python -m tooling.environment full`. In this environment that check fails (exit 1), so pytest never starts:

```text
Environment check failed: Strategy runtime is unavailable: Strategy runtime image 'tradingdev-strategy-runtime:0.1.0' is unavailable; build the Dockerfile strategy-runtime target first. Prepare the local Docker Engine and Dockerfile strategy-runtime image; TRADINGDEV_STRATEGY_IMAGE selects a custom image. See docs/development.md (container build and verification).
```

The `fast` profile of the same checker passes, so the checks listed above are `scripts/check-fast.sh` and this part's own tests. If a reviewer's environment has the strategy-runtime image, their `scripts/check-full.sh` run will be the first complete result.

For reference only: on an older `main` (741fd84, before this prerequisite check existed), 225 of the 7588 tests failed for the same missing image, with no statistics code present ([list](https://github.com/cklivse/tradingdev/blob/eeec7235e956db8ab1d8cf68af898b4a5480460c/evidence/2026-11-08-round26/container-failures-741fd84.md)).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
````

### pr4-sharpe.md

````markdown
Title: feat(statistics): add Sharpe inference and performance summary

Part 4 of the statistics split; #206 explains the split. Code and tests are copied unchanged from `feat/stats-py314`.

- Sharpe ratio with a bootstrap interval, probabilistic and deflated Sharpe, and a performance summary computed from raw run outputs; adds the `arch` dependency (`pyproject.toml`, `uv.lock`).
- The literature behind each step is in `docs/statistics_bootstrap_methods.md` on #38.

Depends on #206. Until #206 merges, this diff also shows #206's commit.

## Verification

This repository has no CI, so nothing on GitHub runs these checks. Checks were run locally on this branch merged into `main`, verified at `main` 1ea5276:

- `uv sync --locked` succeeds on the merged tree.
- `scripts/check-fast.sh`: passes.
- Statistics tests on this branch (Part 1 + Part 4): 146 passed.

Why there is no full-suite result: `scripts/check-full.sh` starts with the repository's own prerequisite check, `python -m tooling.environment full`. In this environment that check fails (exit 1), so pytest never starts:

```text
Environment check failed: Strategy runtime is unavailable: Strategy runtime image 'tradingdev-strategy-runtime:0.1.0' is unavailable; build the Dockerfile strategy-runtime target first. Prepare the local Docker Engine and Dockerfile strategy-runtime image; TRADINGDEV_STRATEGY_IMAGE selects a custom image. See docs/development.md (container build and verification).
```

The `fast` profile of the same checker passes, so the checks listed above are `scripts/check-fast.sh` and this part's own tests. If a reviewer's environment has the strategy-runtime image, their `scripts/check-full.sh` run will be the first complete result.

For reference only: on an older `main` (741fd84, before this prerequisite check existed), 225 of the 7588 tests failed for the same missing image, with no statistics code present ([list](https://github.com/cklivse/tradingdev/blob/eeec7235e956db8ab1d8cf68af898b4a5480460c/evidence/2026-11-08-round26/container-failures-741fd84.md)).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
````

### pr5-comparison.md

````markdown
Title: feat(statistics): add paired comparison and benchmark comparison

Part 5 of the statistics split; #206 explains the split.

- Paired bootstrap comparison of strategies on the same data, and buy-and-hold benchmark returns with a strategy's regression on them.

Depends on #209 (and on #206 through it). Until those merge, this diff also shows their commits.

## Commits

1. 000c15e — the comparison and benchmark modules and tests, copied unchanged from `feat/stats-py314`.
2. a216dc4 — docstring only. The `benchmark` module docstring had listed the product benchmark's instruments (BTC/USDT, S&P 500), but that list belongs to `tradingdev.domain.benchmark`'s `BENCHMARKS` table, and upstream 947a372 has since added Taiwan equities. It now describes the rule: the upstream table decides the instruments, and BTC/USDT is kept only as an example. No code change.

## Verification

This repository has no CI, so nothing on GitHub runs these checks. Checks were run locally on this branch merged into `main`, verified at `main` 1ea5276:

- `uv sync --locked` succeeds on the merged tree.
- `scripts/check-fast.sh`: passes.
- Statistics tests on this branch (Parts 1, 4 and 5): 303 passed.
- All five parts merged together into the same `main`: statistics tests plus the Part 3 MCP test, 449 passed; `scripts/check-fast.sh` passes.
- The four pinned KD figures from #38's fixture (366 UTC days, annualised daily Sharpe, traded notional, cost share of net P&L), recomputed on that combined tree, are bitwise equal to the pinned values.

Why there is no full-suite result: `scripts/check-full.sh` starts with the repository's own prerequisite check, `python -m tooling.environment full`. In this environment that check fails (exit 1), so pytest never starts:

```text
Environment check failed: Strategy runtime is unavailable: Strategy runtime image 'tradingdev-strategy-runtime:0.1.0' is unavailable; build the Dockerfile strategy-runtime target first. Prepare the local Docker Engine and Dockerfile strategy-runtime image; TRADINGDEV_STRATEGY_IMAGE selects a custom image. See docs/development.md (container build and verification).
```

The `fast` profile of the same checker passes, so the checks listed above are `scripts/check-fast.sh` and this part's own tests. If a reviewer's environment has the strategy-runtime image, their `scripts/check-full.sh` run will be the first complete result.

For reference only: on an older `main` (741fd84, before this prerequisite check existed), 225 of the 7588 tests failed for the same missing image, with no statistics code present ([list](https://github.com/cklivse/tradingdev/blob/eeec7235e956db8ab1d8cf68af898b4a5480460c/evidence/2026-11-08-round26/container-failures-741fd84.md)).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
````
