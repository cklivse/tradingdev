# 2026-10-31 第 12 輪：同步上游（837f0c6）

**結論：同步完成，check-full 全綠（7293 passed），PR #38 已更新為 63c44a4，
22 檔，+7561 / −3，GitHub 顯示 MERGEABLE。** 沒有 force，沒有改寫已發布的歷史，
也沒有碰主工作樹。

## 一頁摘要（給睡醒的你）

| 問題 | 答案 |
|---|---|
| 幾個衝突 | **1 個文字衝突**（ARCHITECTURE.md），另有 2 個 git 看不到的**語意衝突**（都只影響文件），以及 1 個被上游改動弄壞的**我們自己的測試** |
| 四個釘值 | **逐位相同**：366 天、Sharpe −7.565103143673017、traded notional 5014735.715506879、cost/\|net\| 0.863481526386825 |
| Sharpe 區塊長度修正 | 新環境仍是 **70/100、區塊中位數 45**；`interval_table_outcome` 的個別區間也一樣 |
| check-full | **exit 0；7293 passed、31 deselected；56 分 24 秒** |
| 非統計目錄的測試 | check-full 裡**全部通過**。同步前我們自己的 `tests/mcp/test_optimization_failed_trials.py` 有 1 個失敗，原因是上游 21c124c 改了 optimization worker 的資料傳遞方式；已照上游的新做法修正（你事先預期過這個測試可能要調） |
| PR #38 | head **63c44a4**，22 檔，**+7561 / −3**，MERGEABLE |
| 需要你決定 | 兩個 buy-and-hold 基準的**成本規則**要不要統一（見第 5 節） |

## 1. 分支與 commit

- 新分支 `feat/stats-sync-upstream` 從 41fa0c7 開出，在獨立的 worktree 裡作業。
- merge upstream/main（837f0c6），合併基準 5f8d14d，帶進上游 280 個 commit。
- 三個 commit：

```text
63c44a4 docs(statistics): relate the statistics package to upstream's benchmark and leaderboard
1135a0d test: pass the frame through a pickle round trip, as the worker now does
f1cdb42 Merge upstream/main (837f0c6) into feat/stats-py314
```

- 推上去的方式：在 detached worktree 裡把 origin/feat/stats-py314 `merge --ff-only`，
  `41fa0c7..63c44a4`，沒有 force。
- 本機的 feat/stats-py314（610e612）和主工作樹都沒動。origin/feat/stats-recut 停在 41fa0c7，
  這輪沒有同步它。

## 2. 每個衝突怎麼解

### 2.1 ARCHITECTURE.md：唯一的文字衝突

- 雙方在責任表的同一個位置各加了一列：
  - 我們：`domain/statistics/`
  - 上游：`domain/benchmark.py`、`app/benchmark_service.py`
- 解法：兩列都保留。我們的放前面，緊接在 `domain/performance/` 之後；上游的接在後面。

### 2.2 pyproject.toml：自動合併，沒有衝突

- 合併後和上游相比，**只多了 `arch>=8.0.0` 這一行**，其餘都以上游為準。

### 2.3 uv.lock：整份以上游為準，再補上 arch

1. `git checkout upstream/main -- uv.lock`，確認和上游完全相同。
2. 用 uv 0.12.18 執行 `UV_NO_CACHE=1 uv lock`。
   - **只新增** arch 8.0.0 和它的依賴：formulaic 1.2.2、interface-meta 2.0.1、patsy 1.0.3、
     statsmodels 0.15.0、wrapt 2.5.2。
   - 既有套件的版本**完全沒變**。
3. `uv lock --check` 通過。

另外有一個附帶變化：uv 拿掉了 3 個平台條件。

- `httpcore2` 底下的 `h11` 和 `truststore`，原本帶 `sys_platform != 'emscripten'`。
- `pexpect` 底下的 `ptyprocess`，原本帶 `!= emscripten and != win32`。

這些條件是多餘的，實際安裝結果不變：

- `httpcore2` 本身只會透過 `httpx2` 安裝，而那條路徑已經帶著同一個條件；`pexpect` 也只會透過 `ipython` 安裝，同樣帶著條件。
- 上游原本的 lock 用同一版 uv 重新 lock，**完全沒有變化**，所以這個化簡是加入 arch 造成的，不是 uv 版本不同。
- reviewer 用 `uv export` 和 `packaging.markers` 在五個平台上實算安裝集合（linux x86_64、linux aarch64、darwin arm64、win amd64、emscripten）：每個平台都只多出 arch 和它的 5 個依賴，沒有少任何套件。

### 2.4 語意衝突一：排行榜文件已經過時

- 上游已經實作了 `docs/statistics_leaderboard_integration.md` 列為「還缺」的前提：
  - `LeaderboardEntry.parameters`
  - `metrics: Mapping[str, float | None]`，而且把 NaN、Inf 存成 None
  - `allow_parameter_axes` 和 `parameter_axes`
- 因此那份文件的部分內容（例如「has no parameter field」「`Mapping[str, float]`」）和大量行號都已經失真。
- 依指示**沒有修改那份文件**。改的是 `statistics/__init__.py` 和 ARCHITECTURE 裡指向它的說明：改成「這是對較早主線的整合分析，『尚缺』清單已經過時，待改寫」（63c44a4）。

### 2.5 語意衝突二：兩個 buy-and-hold 基準

上游新增的 `domain/benchmark.py` 是產品的正式基準，和我們的 `statistics/benchmark.py` 對同一個概念有不同的規定：

| | 上游 `domain/benchmark.py`（產品） | 我們 `statistics/benchmark.py`（研究） |
|---|---|---|
| 標的 | 依資產類別固定：Binance USDT 交易對一律用 BTC/USDT，美股用 ^GSPC | 呼叫端傳入的價格，預期是策略本身交易的標的 |
| 成本 | 以該次 run 的手續費與滑價買進一次後持有到期末 | 不計任何成本，docstring 原本還寫「不要去『修正』它」 |
| 超額報酬 | 報告裡是總報酬差（策略 − 基準） | `excess_return_annualised` 是年化的平均差 |

- 處理方式：**行為不變**。在 `statistics/benchmark.py` 的 docstring、套件 README、ARCHITECTURE 三處寫明：
  - 哪一個是產品的正式基準。
  - beta 只有在同一標的時才能解讀為淨曝險。
  - 兩種超額報酬的定義不同。
  - **成本規則要不要統一，列為待決。**
- reviewer 已對照 837f0c6 的原始碼逐項核實這些陳述：`asset_class_for` 的判斷規則、`buy_and_hold()` 只在進場付一次成本、報表 `_benchmark_row` 計算的是總報酬差。

### 2.6 被上游改動弄壞的測試

- 失敗的是 `tests/mcp/test_optimization_failed_trials.py::test_parallel_transport_also_returns_the_zero_trade_combo`，錯誤是 `AttributeError: 'str' object has no attribute 'copy'`。
- 原因：上游 21c124c（fix: preserve optimization frames across workers）把 `_evaluate_combo` 的參數從 JSON 字串改成 `pd.DataFrame`，由 joblib 以 pickle 傳給 worker。
- 修正（1135a0d）：測試改傳 `pickle.loads(pickle.dumps(frame))`，模擬 worker 實際收到資料的方式。
  - 第一版只是直接傳 `frame`，reviewer 指出這樣測試名稱裡的「transport」就沒有被測到，於是改成經過一次 pickle 序列化。
  - 3 個測試都通過。

## 3. 環境

- 為了不動主工作樹（舊分支加上 20 項未提交修改）的環境，新的 `.venv` 建在 sync worktree 裡，沒有刪除主工作樹的 `.venv`。
  - 新環境放在 `/tmp` 那顆磁碟（38G 可用）。`/workspaces` 剩 9.5G，沒有使用到。
- 先 `uv cache clean`，然後 `UV_NO_CACHE=1 uv sync --locked --all-extras`。
  - 加上 `--all-extras`，是因為這是專案的標準做法（rebuild-env.sh、開發指南），而唯一的 extra 是 dashboard（streamlit、plotly），check-full 裡有用到它的測試。
  - 上游的依賴裡沒有 autogluon 或 torch；最大的是 xgboost 帶進來的 nvidia-nccl（約 300 MB）。
- 建置花了 13 秒，`.venv` 2.0G，**沒有出現 No space left on device**。
- 版本：pandas 3.0.6、numpy 2.5.4、arch 8.0.0，**和同步前完全相同**。

## 4. 數值驗證

### 4.1 四個釘值

- 釘值測試不在 PR 分支裡。我從 `feat/stats-pinned-fixtures`（49de1b7）用 `git archive` 取出測試和 fixture，暫時複製進 worktree 執行，跑完就刪除，沒有 commit。
- 同步前（41fa0c7、舊環境）和同步後（f1cdb42、新環境）各算一次，**逐位相同**：

```text
days 366
sharpe -7.565103143673017
traded_notional 5014735.715506879
cost_share 0.863481526386825
```

- 釘值測試 4 passed。另外 2 個 `TestCommittedReport` 要讀 `demo_output/kd_inference.md`，那份已經隨展示材料移出 PR，所以同步前就會失敗，和這四個數字無關，這次排除不跑。

### 4.2 Sharpe 區塊長度

- 審查原腳本：`0.7062245515464486 70 45.0`。
- `interval_table_outcome` 的個別區間：70/100，區塊中位數 45.0。
- 都和同步前相同。

### 4.3 你特別點名要盯的地方

- `periods.py` 的 resample 和時區轉換、`sharpe.py` 的 `optimal_block_length(...)["stationary"]`、`comparison.py` 的 `align_returns`、`benchmark.py` 的 `buy_and_hold_returns`：
  - 依賴的 pandas、numpy、arch 版本都沒變。
  - 統計測試 631 個全部通過。
  - 四個釘值也逐位相同，表示 resample 和時區的行為沒變。
- optimization worker：見 2.6，已調整。worker 仍然只保存 `trial/{index}/train`，reviewer 核對過 `optimization.py:217`。
- reviewer 另外跑了上游會和我們互動的測試，952 個全部通過：benchmark、performance、ML leaderboard、optimization manifest 等。

## 5. 獨立審查（同一位唯讀 reviewer）

- **第一輪（41fa0c7..599d94a）**：
  - 機械性的合併沒有問題：PR 原本的差異逐行保留，lock 的五平台安裝集合也核實過。
  - 提了兩個 P2 語意衝突（2.4、2.5）和一個 P3 測試命名問題（2.6）。三項都採納。
- **複查（f1cdb42..63c44a4）**：沒有剩下的問題，新增的文字也逐項對照上游原始碼核實過。
- **待你決定：** 兩個基準的成本規則要不要統一。
  - 現況是：研究用的對照不計成本，產品的正式基準計入進場成本。
  - 文件已經寫明兩者不同，行為沒有改。

## 6. check-full

- 做法和第 10、11 輪相同：
  - 包裝程式先 `setsid`，再把 SIGINT 和 SIGQUIT 設回預設，然後 exec。
  - 不加外掛，unset `PYTEST_ADDOPTS`。
  - 另開 keepalive，每分鐘記錄記憶體。
- **預檢：** 不用包裝時 SIGINT 是 `1`；用包裝後，程序本身和子程序都是 `default_int_handler`。
- **執行中實測：** pytest PID 355159（pgid 和 sid 相同），用的是 sync 的 `.venv`，`SigIgn=0x1001000`，SIGINT 沒有被忽略。
- **結果：** exit 0；**7293 passed**、31 deselected、74 warnings；56 分 24 秒（16:34–17:32 UTC）。
  - rootdir 是 sync worktree，collected 7324。上游新增了大量測試，比上一輪的 4879 多出許多。
  - HEAD 前後都是 63c44a4，工作樹乾淨。
- **非統計目錄的測試：全部通過，沒有任何失敗。**
- **記憶體：** 58 筆紀錄，最低可用 2098 MB（第 36 分），`memory.peak` 6054 MB，`oom` 計數是 0。

## 7. 其他確認

- 上游的 leaderboard parameter surface **已經在 main 裡**：`metrics: Mapping[str, float | None]`、`allow_parameter_axes`、`parameter_axes` 都在。
- **PR #131（method_family）還沒合併**，仍是 OPEN。
- 上游的 check-fast 新增了 MCP 上下文預算報告，所有項目都在預算內（例如 model_tools 69751 / 70000）。

## 8. 收尾狀態

- 合併用的 `merge` 和審查用的 `rev` worktree 已移除。
- 保留的 worktree：
  - `sync`：feat/stats-sync-upstream，63c44a4，乾淨，裡面有新的 `.venv`
  - `recut`：feat/stats-recut，41fa0c7
  - `notes`、`lb`
  - 它們都在 `/tmp` 底下，Codespace 關閉後會消失，但所有 commit 都已經 push 或存在主 repo 的 `.git` 裡。`feat/stats-sync-upstream` 只在本機，不過它的內容已經和 origin/feat/stats-py314 完全相同。
- 沒有殘留的 pytest、check-full 或 keepalive 程序。

## 9. 待決／下一步

1. 兩個基準的成本規則要不要統一（本輪新增，需要你決定）。
2. plateau 的 StopIteration（P3）、Sharpe 在極端數值下的問題（P3）：依指示留到同步確認乾淨之後。同步現在已經確認乾淨了。
3. `docs/statistics_leaderboard_integration.md` 整份重寫：已確認上游實作了哪些前提（見 2.4），等對方回答範圍問題。
4. 主工作樹的本機 feat/stats-py314（610e612）落後 origin 很多，加上 20 項未提交修改，要怎麼處理由你決定。
