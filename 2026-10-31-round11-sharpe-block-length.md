# 2026-10-31 第 11 輪：單序列 Sharpe 的區塊長度（最後一個 P2）

**結論：已修正、已審查、check-full 全綠，PR #38 已更新為 41fa0c7，22 檔，+7531 / −3。**
沒有 force，沒有改寫已發布的歷史，也沒有碰主工作樹。

## 1. Codex 第二輪 P3 四項在 b29c967 上的現況（只回報，沒動）

| # | 項目 | 現況 |
|---|---|---|
| 1 | 平原平手判斷遇到極大有限值會拋出 StopIteration（plateau.py `_argmax_score`） | **仍存在，已重現。** 3×3 格點全是 1e308 時，所有分數溢位成 inf，`plateau_summary` 拋出 `StopIteration()`。另外，1-D 四點全是 1e308 時不會拋錯，但會選錯點：最高分是 inf，卻選了分數 1e308 的那一點，`inf − 1e308` 仍然落在容忍範圍內。 |
| 2 | 開發指南錯稱展示腳本不使用 application services | **不適用。** `docs/development.md` 和合併基準 5f8d14d 完全相同（f044ab1 已還原）；第 105–106 行現在講的是 LLM 測試，整份文件沒有 demo 或 application services 的字樣。 |
| 3 | METHODS 對重現既存圖表有互相矛盾的承諾 | **不適用。** METHODS.md 不在 PR 裡。PR 裡只剩 leaderboard 文件的一句：「圖表在現行區塊長度規則之前產生，之後沒有重新產生」，它和現況不矛盾，而且那份文件這輪不能碰。 |
| 4 | 歷史 fee=0 被誤寫為所有成本都併入成交價 | **不適用。** kd_inference.md 和 demo 腳本都已移出；PR diff 裡沒有這類說法（唯一的 `fee=0.6` 是測試資料）。 |

## 2. 重現審查的數字

用審查原文的腳本（PR #38 issue comment 6414977941）：n=1000、100 個樣本（seed 0–99）、reps=300、bootstrap seed=0。

- **b29c967：`0.7062245515464486 49 2.0`，和審查完全一致。**
- 平方報酬：70/100，區塊中位數 45，也一致。

## 3. 評估的規則

四種情境，每種 100 個樣本，bootstrap 設定完全相同，只換區塊長度的選法。數字是覆蓋母體 Sharpe 的次數，名目覆蓋率 95%。

| 規則 | 波動狀態切換（審查案例） | AR(1) φ=0.5 | iid | GARCH(1,1) |
|---|---|---|---|---|
| 原始報酬（修正前） | 49（區塊 2） | 93（12） | 94（2） | 91（2） |
| 平方報酬 | 70（45） | 93（**7**） | 93（2） | 89（27） |
| **max(原始, 平方)（採用）** | **70（45）** | **93（12）** | **94（2）** | **89（27）** |
| jackknife 影響值 | 60（12.5） | 93（12） | 94（2） | 91（2） |
| max(影響值, 平方) | 72（45.5） | 93（12） | 94（2） | 89（27） |

**選 max(原始報酬, 平方報酬) 的理由：**

- **jackknife 影響值**（第 6 輪配對差異的做法）在審查案例只到 60/100。
  - Sharpe 的影響值近似 `z − (SR/2)(z² − 1)`：線性的 `z` 項是白雜訊而且權重大，持續的變異數項被稀釋，Politis–White 估出的區塊就偏短。
  - 理論上它是正確的目標，實測卻比平方報酬差。另外我確認過：Sharpe leave-one-out 的封閉解和泛用 jackknife 結果一致。
- **只用平方報酬**會在 AR(1) 把區塊從 12 縮到 7，丟掉平均數本身的依賴。
- **取兩者較大值**：在每種情境都不比最好的單一規則差，計算是 O(n)，也容易解釋。
- max(影響值, 平方) 是 72，和 70 的差距在 100 個樣本的抽樣誤差（約 ±4.6）之內，卻更複雜。
- reviewer 用另一批樣本（seeds 100–199）複驗，結果一樣：

  | 規則 | 審查案例（原樣本 / 新樣本） | GARCH（新樣本） |
  |---|---|---|
  | 原始報酬 | 49 / 48 | 95 |
  | max(原始, 平方) | 70 / **72** | 93 |
  | jackknife 影響值 | 60 / 66 | 95 |

- **reviewer 提的未來選項（未採用）：** 改用 |x − mean| 當波動代理，審查案例可到 75/80，GARCH 是 93。我沒採用，因為在同一批樣本上比較的規則越多，從中挑最好的就越像在調參。之後如果要再提高覆蓋率，值得另外評估。

## 4. 修正（41fa0c7）

- `sharpe_interval_outcome`，以及 `interval_table_outcome` 的個別區間：區塊長度改成 max(原始報酬的 Politis–White 估計, 平方報酬的估計)。
  - table 是對所有欄位和它們的平方一起取最大值，常數欄位會被略過。
  - 共用的私有函式 `_block_length` 和 `_returns_block_size` 放在 `sharpe.py`。comparison 的 `_block_size` 已移除，配對差異改呼叫 `_block_length`，行為不變：reviewer 比對了 36 個案例，和 b29c967 完全相同。
- 新增可選的 `block_size` 參數：`sharpe_interval_outcome`、`sharpe_confidence_interval`、`interval_table`、`interval_table_outcome`。
  - 驗證規則和 `difference_interval` 一致：只接受內建 int，而且要 ≥ 1。給定的值會原樣回報在結果裡。
  - docstring 寫明什麼時候必須手動指定：依賴在原始報酬和平方報酬都看不出來、依賴的持續時間佔樣本的大半，或樣本足夠做 bootstrap 但不足以可靠地估計區塊長度。
  - 手動指定不會解除 20 期的下限（審查 #1 之後才補上這句）。
- 文件：
  - `sharpe_interval_outcome` 的 docstring 寫了選法、理由、各情境的實測覆蓋率，以及殘餘偏差。
  - `interval_table_outcome` 的 docstring 引用同一條規則。
  - 兩個結果 dataclass 的 `block_size` 欄位說明已更新。
  - 套件 README（`statistics/__init__.py`）的「已知限制」改寫成：「**Bootstrap intervals can still be too narrow**…nominal 95% Sharpe intervals covered the true value in 70 of 100 samples (49 when blocks followed the returns alone)…」
- **修正後實測覆蓋率**（審查原腳本，100 個樣本）：

  | 入口 | 修正前 | 修正後 |
  |---|---|---|
  | `sharpe_interval_outcome` | 49/100（區塊 2.0） | **70/100**（區塊 45.0） |
  | `interval_table_outcome` 個別區間（同一批樣本） | 49/100（區塊 2.0） | **70/100**（區塊 45.0） |

  仍然遠低於名目的 95%。狀態大約每一百期才切換一次，一個樣本裡只有少數幾段，這不是區塊長度能修好的。文件照實寫了這一點。

### 回歸測試

- 新增 32 個測試，其中 30 個在 b29c967 上失敗：
  - 審查的覆蓋率模擬（100 個樣本，耗時 2 秒）
  - 波動狀態切換讓區塊變長的測試，sharpe 和 interval table 各一個
  - `block_size` 指定後實際生效並原樣回報
  - `block_size` 的 20 個拒絕案例和 4 個接受案例
- 覆蓋率測試的門檻是 ≥ 65，實測 70，修正前 49。資料和 bootstrap 的 seed 都固定，結果是決定性的；門檻只用來吸收函式庫版本的差異，測的是「有改善」，不是「達到 95%」。
- 守護測試：iid 的區塊仍然很短（≤ 3），AR(1) 的區塊不短於原始報酬的估計值。這兩個在修正前後都通過，是預期的。

## 5. 獨立審查（同一位唯讀 reviewer，受查版本 8cc0a8b）

- **沒有 P1/P2，也沒有推翻選定的做法。**
- reviewer 用自己的腳本重算了所有覆蓋率數字，結果一致，也核實了 commit 訊息的每一項陳述。
- **#1 P3（採納）**：docstring 暗示樣本太短時手動指定 `block_size` 就能得到區間，但不足 20 期一律沒有區間。已修正措辭，amend 成 41fa0c7（只改文件）。
- **#2 P3（本 commit 之前就存在，不在這輪處理）**：
  - 報酬約 1e-170 時，`std` 下溢成 0，拋出 `ZeroDivisionError`。
  - 報酬約 1e200 時，`std` 溢位，`sharpe_ratio` 回傳 0.0、區間是 [0, 0]。
  - b29c967 的行為相同，新增的平方欄位只多一個 RuntimeWarning。和 plateau 的 StopIteration 一樣屬於極端數值，列為待決事項。

## 6. check-full

- 做法和第 10 輪相同。
  - 預檢：不用包裝時 SIGINT 是 `1`；用包裝後，程序本身和子程序都是 `default_int_handler`。
  - 沒有外掛，沒有設 `PYTEST_ADDOPTS`；另開 keepalive，每分鐘記錄記憶體。
- 執行中實測：pytest PID 226303（pgid 和 sid 相同），`SigIgn=0x1001000`，SIGINT 沒有被忽略。
  - 監控裡只有第 0 分和第 1 分的值不同，都在 pytest 接手之前：第 0 分是包裝程式還沒重設信號，第 1 分是 check-full.sh 的 bash 在跑 check-fast。
- 結果：**exit 0；4865 passed、14 deselected、74 warnings；47 分 48 秒**（12:31–13:20 UTC）。
  - rootdir 是 recut worktree，collected 4879，比上一輪多 32 項，正好是本輪新增的測試數。
  - HEAD 前後都是 41fa0c7，工作樹乾淨。
- 記憶體：最低可用 2322 MB，`oom` 計數是 0。

## 7. push

- origin/feat/stats-recut：`b29c967..41fa0c7`。
- origin/feat/stats-py314：在另開的 detached worktree 裡 `merge --ff-only`，`b29c967..41fa0c7`。
- **PR #38：OPEN，head 41fa0c7，22 檔，+7531 / −3。**
- 本機 feat/stats-py314（610e612）沒動，它被主工作樹 checkout 著，而且有使用者未提交的修改。

## 8. 收尾狀態

- 合併用的 `merge` 和審查用的 `base` worktree 都乾淨，已移除。
- 保留的 worktree：`recut`（41fa0c7，乾淨）、`notes`、`lb`。
- 沒有殘留的 pytest、check-full 或 keepalive 程序。

## 9. 待決事項

1. plateau 的 StopIteration（Codex P3，本輪第 1 節）：已重現，還沒修。
2. Sharpe 在極端數值下會回傳 0.0 或拋 ZeroDivisionError（本輪審查 #2，之前就存在）。
3. 如果要再提高覆蓋率：可以評估 |x − mean| 當波動代理，但要用新的樣本評估，避免調參。
4. 延續的事項：
   - `docs/statistics_leaderboard_integration.md` 要整份重寫，在等對方回答範圍問題。
   - 同一個 horizon 能不能混用兩個 dataset 版本。
   - upstream 同步（main 已經到 af9688f）。
   - 本機的 feat/stats-py314 落後 origin。
