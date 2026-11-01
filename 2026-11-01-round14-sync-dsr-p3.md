# 2026-11-01 第 14 輪：收進 a24594c 同步、deflated Sharpe 限制段、兩個 P3

## 結果

| 項目 | 結果 |
| --- | --- |
| push | `feat/stats-py314` 1d1fff6 → **c5fff7a**，fast-forward，沒有 force；push 前再確認過 origin 仍是 1d1fff6 |
| PR #38 | head c5fff7a，23 檔，+8151 / −3，MERGEABLE |
| check-full | **exit 0；7476 passed、32 deselected；57 分 01 秒**（head c5fff7a） |
| 四個釘值 | **逐位相同**（1d1fff6、c67a074、0ceb3f7 三個版本） |
| 語意衝突 | **3 個**（見第 3 節），其中 1 個是本 session 新補的 |

## 1. 開始前的狀態與意外發現

- origin/feat/stats-py314 = 1d1fff6 ✓；feat/stats-sync-upstream-2 = 733b521，含 a24594c ✓。
- 意外：本機分支 `round14/merge-sync`（0ceb3f7）已經有另一個 session（02:19–03:01 UTC）做完的四個 commit。它沒有 push，也沒有報告，worktree 目錄已經不在，看不到它跑過的 check-full。
- 你選擇「審查後沿用」。我在新分支 `round14/merge-sync-2` 依序重建這四個 commit，只改了任務 1 的文件 commit（補 8 行，見 3.3）。`round14/merge-sync` 原樣保留。
- 主工作樹的本機 `feat/stats-py314` 停在舊的 610e612，裡面還有未提交的修改，我沒有動。

## 2. commit 切分

| commit | 內容 |
| --- | --- |
| c67a074 | Merge feat/stats-sync-upstream-2（upstream a24594c）。tree 和重新機械合併 1d1fff6＋733b521 的結果相同（51dfdbd），沒有手改 |
| 79d76b4 | 任務 1：排行榜整合文件對齊合併後的樹 |
| 3e2600a | 任務 2：deflated Sharpe 誤差方向未知 |
| c5fff7a | 任務 3：plateau／Sharpe 極端量級 |

## 3. 釘值與語意衝突

### 3.1 四個釘值

測試和 fixture 從 `feat/stats-pinned-fixtures`（49de1b7）用 `git archive` 取出，放在 scratchpad 執行，沒有 commit。三個版本的結果都是：

```text
days 366
sharpe -7.565103143673017
traded_notional 5014735.715506879
cost_share 0.863481526386825
```

P3 修正改到了 `sharpe.py`，所以修正後的 0ceb3f7 也算了一次。這組輸入沒有觸發縮放，因此結果不變。

### 3.2 語意衝突（3 個）

1. **文件開頭「不在本分支的樹裡」那句話過時了。** 已改成「本分支已合併 a24594c，所有描述都對照本樹的程式碼」。
2. **兩處描述不精確。**
   - 規則的 `method_name` 會用 `g` 格式把門檻四捨五入，`parameters` 保留精確值。
   - `build_entry_id` 識別規則用的是名稱加精確參數，所以「一個規則＝一個 method_name」不成立：兩個接近的門檻可能同名。

   前一個 session 已經修正這兩處，我逐項對照程式碼確認過。我也重新核對了文件裡所有關於 method_family 和門檻規則的描述，對照的有 `resolve_method`、`LeaderboardEntry.family`、`ThresholdRule` 的 `name`／`parameters`／`signal`、MCP `evaluate_signal` 的 model-or-threshold 輸入、skipped rows 的欄位，以及 `docs/ml_research.md` 的章節名稱。都和程式碼一致。
3. **（本 session 新補）上游的 `family` 篩選會縮小 Bonferroni 的 N。** `rank_entries` 把篩選後可排名的候選數傳給 `required_t_stat`，所以只排名一個家族時，修正只涵蓋該家族，不涵蓋在這個資料集上試過的所有候選。上游自己也建議「pass `family` to rank one kind」。我在「Two Selection Corrections」補了這點，並說明表格裡的「Metric family」和 `method_family` 無關。

### 3.3 掃過但不算衝突的部分

- `docs/performance_artifacts.md` 新增的「Metric Interpretation」是上游 4c18457 的文件重組，大部分是搬移，沒有行為變更。
- buy-and-hold 的成本規則這次沒有新變化，上一輪的待決事項照舊。
- 「訓練／評估配對」仍在上游 `feat/ml-training-dataset-binding`。upstream/main 仍是 a24594c，文件裡「不在 main」的說法依然正確。

## 4. 任務 2：Limitation 段落

改前（1d1fff6）：

```text
Limitation: the formula assumes ``N`` independent trials. Grid-search
trials are strongly correlated (a lookback of 20 and of 21 is almost
the same strategy), so the effective number of trials is far smaller
than the actual ``N``. Using the actual ``N`` over-corrects and leans
towards rejecting a real edge. This version deliberately takes that
conservative side, preferring a missed edge to a false positive.
Estimating the effective ``N`` requires clustering the trials by the
correlation of their returns and is out of scope.
```

改後（c5fff7a）：

```text
Limitation: the formula assumes ``N`` independent trials. Grid-search
trials are strongly correlated (a lookback of 20 and of 21 is almost
the same strategy), and the correlation has two opposite effects on
the hurdle. The effective number of trials is smaller than the actual
``N``, so using the actual ``N`` raises the ``Z^-1`` multiplier, which
pushes towards over-correction. But correlated trials also have Sharpe
ratios that cluster together, so the measured ``std(SR_n)`` is small,
which lowers the hurdle. Which effect dominates has not been measured,
so the net direction of the error is unknown: the result may under- or
over-correct for the selection. Using the actual ``N`` is a deliberate
design choice meant to lean conservative, preferring a missed edge to
a false positive; it is not a demonstrated property of the result.
Estimating the effective ``N`` requires clustering the trials by the
correlation of their returns and is out of scope.
```

套件 docstring（`__init__.py`）和整合文件也改成同樣的說法。全樹沒有剩下把 over-correct 當成事實陳述的句子。docstring 沿用公式裡的 `Z^-1` 記號，也就是你說的 Phi^-1。

## 5. 任務 3：兩個 P3

- 修法：新增私有模組 `_scaling`。當數值的量級或離散度超出 [2^-60, 2^60] 時，乘上一個精確的 2 的冪次。範圍內的一般輸入原樣傳回，結果逐位不變。
- plateau：
  - 鄰域平均和標準差都會先縮放，所以 1e308 不再算出 inf − inf，也就不再 StopIteration。
  - 一維情形不再因為無限大的分數挑錯點。
  - metric 的跨度超出 float 範圍時，明確丟出 ValueError。
  - spikiness 超出 float 範圍時回傳 None，docstring 已註明。
- sharpe：
  - 1e-170 不再 ZeroDivisionError，1e200 不再回傳錯誤的 0.0。
  - PSR 的四階動差在約 1e77 會溢位，現在也先縮放。
  - 估 block length 前逐欄縮放。
  - trial Sharpe 離散到門檻不是有限值時，丟出 ValueError。
- 回歸測試：新增 28 個。套到修正前的原始碼，24 個失敗，包括 1e308 StopIteration、一維挑錯點、1e-170、1e200；另外 4 個守的是原本就正確的行為。修正後統計測試 656 個全部通過。

## 6. 檢查與審查

- check-full 用 fork → `setsid()` → 把 SIGINT/SIGQUIT 重設為 SIG_DFL → exec 的方式跑。pytest 行程的 SigIgn 是 0x1001000，SIGINT 不在忽略清單內；rootdir 是 scratchpad worktree。
  - 第一次直接在行程裡 `setsid()` 得到 EPERM（行程已經是群組領導者），check-full 沒有跑起來，所以改成先 fork。
- P3 的程式碼由我審查（我沒有參與它的實作）。前一個 session 提到的獨立審查，我無法查證內容。
- 這個 repository 沒有設定 `core.hooksPath`，commit hook 沒有執行；文件 commit 前我手動跑了 check-fast，結果綠燈。

## 7. 仍待決定

- 範圍措辭要等 Kuan-Lun 確認。
- 兩個 buy-and-hold 基準的成本規則是否統一。
- `round14/merge-sync`（原分支）和 `round14/merge-sync-2` 要不要刪掉。
