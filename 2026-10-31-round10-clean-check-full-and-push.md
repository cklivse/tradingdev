# 2026-10-31 第 10 輪：乾淨重跑 check-full、合併、push

**結論：check-full 全綠（4833 passed）。feat/stats-py314 已 fast-forward 到
b29c967 並 push，PR #38 更新。** 沒有 force，沒有改寫歷史，也沒有碰主工作樹。

## 1. 存檔

- origin/feat/stats-recut：`ed9de31..b29c967`，fast-forward push。第 9 輪的 7 個修正 commit 現在也在 origin 上了。

## 2. 最嚴重審查項目的證據（第一輪 #1）

在 b29c967 上，從 recut worktree import（`tradingdev.__file__` 指向 `scratchpad/recut/src`）：

```text
>>> sharpe_ratio([True, 0.5, 0.1], periods_per_year=252)
  File ".../statistics/_validation.py", line 102, in real_array
    raise ValueError(f"{label} must be numbers, got {element!r}")
ValueError: returns must be numbers, got True
```

修正前（ed9de31）這個呼叫會回傳 18.8。修正在 7f3f29b，3ae82d0 又把快速路徑改成白名單。

## 3. check-full

### 怎麼讓子程序拿到預設的 SIGINT

非互動 bash 用 `cmd &` 啟動時，會把 SIGINT 和 SIGQUIT 設成 SIG_IGN，而且會遺傳下去。我選了一個 Python 包裝（`default_signals_exec.py`，放在 scratchpad，沒有 commit）：

1. `os.setsid()`
2. 把 SIGINT 和 SIGQUIT 設回 `SIG_DFL`
3. `os.execvp` 執行 `scripts/check-full.sh`，而它最後又會 `exec pytest`

選它而不選 tmux 的理由：

- 它直接處理問題本身。
- PID 從頭到尾不變，記錄到的就是 pytest。
- 不依賴 tmux，也不會多帶一層終端環境進測試。

**預檢**（和正式執行相同的背景啟動路徑）：

| 啟動方式 | 程序本身的 SIGINT | 子程序的 SIGINT |
|---|---|---|
| 不用包裝 | `1`（忽略） | `1` |
| 用包裝 | `default_int_handler` | `default_int_handler` |

**執行中實測：**

- pytest 的 PID 是 162548，pgid 和 sid 也都是 162548。
- 它的 `SigIgn=0x1001000`，只代表 SIGPIPE 和 SIGXFSZ 被忽略，這兩個是 Python 自己設的；SIGINT 的 bit（0x2）沒有設定。
- 每分鐘的監控都記錄同一個值，從頭到尾沒變。
- 一個測試開的 multiprocessing 輔助程序是 `0x1005002`。它的父程序 pytest 沒有忽略 SIGINT，所以這是 multiprocessing 自己主動設的，不是從我這裡繼承的。

### 執行條件

- 沒有外掛，`PYTEST_ADDOPTS` 明確 unset。
- `PYTHONPATH` 只有 recut 的 `src`。
- keepalive 另開，每分鐘記錄記憶體。
- 執行期間沒有修改任何檔案。

### 結果

- **exit 0；4833 passed、14 deselected（live_llm）、74 warnings；49 分 35 秒**（11:12–12:02 UTC）。
- rootdir 是 recut worktree，collected 4847，selected 4833。
- HEAD 前後都是 b29c967，工作樹乾淨。
- `tests/tooling/` 全部通過，`tests/integration/test_mcp_protocol.py` 也全部通過。
- 所以第 9 輪那 12 個 tooling 失敗，確實出在那次的執行方式。

### 記憶體（51 筆）

- 開跑前：已用 3525 MB，可用 4416 MB。這比第 2 次開跑前多了約 950 MB 可用。
- 最低可用 **2253 MB**（第 42 分）。pytest session 最高 1431 MB。
- 記憶體壓力（full avg10）最高 2.53（第 10 分）。
- 第 34–37 分（第 1 次被 SIGTERM 的時間點）：可用 2363–3073 MB，壓力 0–0.6。
- cgroup 的 `memory.events` 前後都是 `oom 0`、`oom_kill 0`，`memory.peak` 是 5896 MB。

### 第 1 次 SIGTERM 的原因：**仍未確定**

- 三次執行裡只有第 1 次被終止，而且那次沒有記憶體紀錄。
- 第 2 次和第 3 次都跑超過 35 分鐘：最低可用 1144 MB 和 2253 MB，都沒有被終止。
- 「35 分鐘」沒有再出現，所以不支持「固定時間就終止」的看門狗。
- repo 裡沒有這種看門狗，見第 9 輪報告。
- 記憶體監控的嫌疑無法證明，也無法排除。

## 4. 合併與 push

- 合併在另開的 detached worktree 裡做，起點是 origin/feat/stats-py314（df88dd1）：
  `git merge --ff-only feat/stats-recut`，結果是 `Updating df88dd1..b29c967 / Fast-forward`。
- 用 `git push origin HEAD:refs/heads/feat/stats-py314` 推上去，結果是 `df88dd1..b29c967`，沒有 force。
- 本機的 feat/stats-py314 ref 沒動。它被主工作樹 checkout 著，而且主工作樹有使用者未提交的修改。它目前是 610e612，落後 origin。
- **PR #38（Kuan-Lun/tradingdev）**：OPEN，**head b29c967，22 檔，+7299 / −3**。GitHub 的數字和本機以 5f8d14d 為基準算的一致。

| 版本 | 檔案 | 行數 |
|---|---|---|
| df88dd1（10/26 起的 PR head） | 33 | +9286 / −7 |
| f044ab1（validate_run 移出後） | 20 | +6522 / −3 |
| b29c967（現在） | 22 | +7299 / −3 |

## 5. 收尾狀態

- worktree：
  - 合併用的 `merge` 和審查用的 `stats` 都乾淨，已移除。
  - `recut` 是 feat/stats-recut 的 b29c967，乾淨。
  - `lb` 是 10/31 實測腳本用的。
  - `notes` 是本報告用的。
- 主工作樹沒碰，仍是 20 項未提交。
- 沒有殘留的 pytest、check-full 或 keepalive 程序。

## 6. 待決／延續事項

1. 第 1 次 SIGTERM 的原因未定。之後如果再遇到，每分鐘的記憶體監控腳本可以直接沿用。
2. `docs/statistics_leaderboard_integration.md` 裡 plateau.py 的行號過時（審查 #7），等下次修改文件時一起處理。
3. 631dde0 漏標 BREAKING CHANGE，已在第 9 輪報告揭露。
4. 同 horizon 單一 dataset 版本的作業問題（10/31 實測報告），由使用者回覆排行榜負責人。
5. upstream 同步（f7a217c，落後 246 個 commit）是下一輪的事。
6. 本機 feat/stats-py314（610e612）落後 origin。主工作樹那 20 項未提交修改的處理由使用者決定。
