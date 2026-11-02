# 第 18 輪待決事項：分析與建議

日期：2026-11-02
接續：`2026-11-02-round18-ranking-core-and-citations.md`

這一份只做分析，沒有改程式、沒有 push 程式分支、沒有在 GitHub 留言或開 PR，也沒有刪除任何分支。

## 結論

| # | 事項 | 建議 |
| --- | --- | --- |
| 1 | 給 AIunusual 的回覆 (a) | **現在貼** |
| 2 | README PR | **先不開，等 Kuan-Lun 回答第 3 題** |
| 3 | #136 的 (b) | **現在貼** |
| 4 | `0cf2c90` 的 docstring 修改 | **保留**；另外 PR #38 也有同樣兩句舊說法，建議同步修正（要你授權） |
| 5 | PSR 改用母體標準差 | **不改**，維持文件記錄 |
| 6 | `origin/wip/stash-610e612` | **可以刪**，內容都已經在其他分支 |

## 現況核對（2026-11-02）

- 上游 main 仍是 `a77babf`，第 18 輪之後沒有新 commit。
- PR #38：head `8994a61`（和 origin 一致）。最後一則留言仍是 AIunusual 的（2026-11-01 20:24 UTC），之後沒有新留言或 review。Kuan-Lun 還沒回答 AIunusual 的第 2 到第 4 題。
- PR #136：head 仍是 `d22e380`，狀態 OPEN，沒有留言也沒有 review。
- #62：仍只有 cklivse 的兩則留言。
- 上游另有兩個 OPEN 的 PR：#137、#138。標題看起來和統計無關，這次沒有細看。

## 1. (a) 現在貼到 #38

理由：

- (a) 分成兩部分：對介面的 7 點意見，以及對 4 個問題的看法。第一部分是回應 AIunusual 的設計，不需要等 Kuan-Lun。第二部分明寫 "for Kuan-Lun's decision"，只給統計端的立場，沒有替他決定。
- AIunusual 正在做共用排名核心，#139 已經先為較寬的 `compare_runs` 調高 MCP 預算。介面一旦定型（例如 `values: {metric: float | null}`、dense rank），之後再改的成本更高。第 1、2、5 點都會改到回傳格式。
- 貼出後，Kuan-Lun 回答時可以一次看到雙方的意見。
- (a) 引用的 commit（`8994a61`、`a77babf`）都還是最新的，內文不用改。

風險：Kuan-Lun 可能覺得問題是問他的，被別人先回答。(a) 的開頭已經寫明 "The four questions are Kuan-Lun's"，這個風險不大。

## 2. README PR 先不開

理由：

- 第 3 題問的是 Kuan-Lun 想怎麼處理 README，決定權在他。(a) 已經提供兩個選項（獨立 PR 或留在 #38），他只要回一句就好。
- 在他回答前就在上游開 PR，等於替他選了一個選項，還會在上游多一個 PR 要他處理。
- 等待的成本很低：分支 `docs/readme-final-evaluation-data`（`a68f1e4`）已經 push，PR 標題和內文在第 18 輪報告的 (c)，回答後一分鐘內就能開。這段 README 只是使用建議，不會擋住其他工作。

如果 Kuan-Lun 選擇留在 #38，這條分支就可以刪掉。

## 3. (b) 現在貼到 #136

理由：

- AIunusual 打算先合併 #136，再做排名核心。兩點（`training_dataset_status` 明確區分 no_fit 和 unknown、記錄 `signal_source`）都會改到 #136 新增的資料格式。合併後再改要動已經寫出去的紀錄，合併前改最便宜。
- #136 head 仍是 `d22e380`，(b) 是在這個 head 上核對的，內文不用改。
- 第 1 點是 Kuan-Lun 在 #38 自己提出的要求，也寫在 #62 的驗收標準裡，不是新主張。
- #136 目前沒有任何留言或 review，現在貼不會打斷正在進行的討論。

## 4. `0cf2c90` 保留；PR #38 也要改

`0cf2c90` 只在 `feat/stats-public-api` 上，改了 `__init__.py` docstring 的兩處：

1. 描述整合文件的那句，從「plateau 和配對比較怎麼讀排行榜」改成「訊號與回測的排名、排行榜、本套件三者如何分工；本套件在排名後分析、不決定名次」。
2. "only out-of-sample returns … are comparable" 改成「統計比較需要樣本外報酬；在調過參數的樣本內報酬上它量的是擬合；排名沒有這個要求」。

我的判斷是兩處都該改：

- 舊的第 2 句可以讀成「只有樣本外結果才能比較」。Kuan-Lun 在 #38 確認的範圍是排名不需要樣本外證據，整合文件和 README 段落也都這樣寫。舊句和這個範圍矛盾。
- 新句沒有放寬統計的要求：做統計比較仍然要樣本外報酬，只是把「排名」和「統計比較」分開。
- 只改 docstring，不改行為，也不改 `__all__`。

**新發現**：PR #38（`feat/stats-py314` @ `8994a61`）的 `src/tradingdev/domain/statistics/__init__.py` 還是舊的兩句（第 9–11 行和第 55–57 行）。#38 自己的整合文件已經寫「排名不需要樣本外」，所以 #38 現在前後矛盾。public-api 分支是從 #38 往下接的，等 #38 合併時，矛盾的句子會先進 main。

建議：把 `0cf2c90` 裡 `__init__.py` 的兩處修改，用一個只改文件的 commit 套到 `feat/stats-py314`，跑 check-docs 和 check-fast 後 push。之後 public-api 再 merge #38 時，這兩處內容相同，不會衝突。`docs/statistics_public_api.md` 那部分只存在 public-api 分支，不用動。這一步會在 #38 加 commit，需要你授權才做。

## 5. PSR 的 Sharpe 不改用母體標準差

差異：作者附錄程式用母體標準差（`ddof=0`），我們的 `sharpe._period_sharpe` 用 `ddof=1`。兩個 Sharpe 差 `sqrt(n/(n-1))` 倍。

我實際算了 PSR 的差（同樣的報酬序列，只換 Sharpe 的標準差，偏度和峰度都用母體動差）：

| n | ddof=1（現行） | ddof=0（作者） | 差 |
| --- | --- | --- | --- |
| 30 | 0.4439 | 0.4430 | -0.0010 |
| 90 | 0.9677 | 0.9684 | +0.0007 |
| 365 | 0.4661 | 0.4660 | -0.0000 |
| 365 | 0.4066 | 0.4065 | -0.0001 |
| 1000 | 0.6714 | 0.6715 | +0.0001 |

（常態亂數，seed 0，日波動 2%。）

不改的理由：

- 差距在小數第三位以下，n 越大越小。PSR 本身是漸近常態近似，近似誤差本身就是 O(1/n)，比這個差距大。
- `_period_sharpe` 也被 `sharpe_ratio`、bootstrap 信賴區間和 DSR 使用。只在 PSR 改，PSR 用的 Sharpe 就會和同一套件回報的 Sharpe 不一樣；全部都改，又會讓本套件其他地方統一的 `ddof=1` 慣例出現例外（`__init__.py`、`performance.py`、`plateau.py`、`benchmark.py` 都是 `ddof=1`）。
- 兩種估計量都是一致估計量，文獻上兩種寫法都有。

目前 `docs/statistics_bootstrap_methods.md` 已經寫明這個差異，建議維持現狀。之後如果要和作者的數字逐位對照，再在測試裡換算 `sqrt(n/(n-1))` 即可。

## 6. `origin/wip/stash-610e612` 可以刪

這條分支（`53d7ed2`）是第 15b 輪拆分 stash 前留下的遠端備份。我逐檔比對了 stash 的內容（含 untracked 的 3 個檔案，共 21 個檔案）：

| 內容 | 現在在哪裡 |
| --- | --- |
| KD fixture（`equity.parquet`、`trades.parquet`、`run.json`、`extract.py`）、`kd_fixture.py` | 逐位元相同，在 py314、public-api、demo-evidence 三條分支上 |
| fixture `README.md`、`test_statistics_kd_fixture.py` | py314 上是拿掉了「對照 demo 報告」的版本；對照報告的測試搬到 demo-evidence 的 `tests/scripts/test_demo_kd_report.py`（`TestCommittedReport`） |
| `demo_output/*`、`scripts/demo_statistics.py`、`scripts/validate_run.py`、`test_demo_statistics.py`、`test_validate_run.py` | 逐位元相同，在 `feat/stats-demo-evidence` |
| `docs/statistics_public_api.md`、`test_statistics_public_api.py`、`__all__` | 在 `feat/stats-public-api`（之後各輪又修改過） |
| ARCHITECTURE.md 和整合文件連到公開 API 文件的連結 | 在 `feat/stats-public-api` |
| `performance.py` 的 `periods_per_year` 有限值檢查及其測試 | 當時刻意不搬，已經由 `723aec3` 的 `sharpe._annualisation` 取代：`_finite()` 擋掉 NaN 和 inf，再檢查 `> 0` |

沒有找到只存在於這個備份的內容。刪掉後，本機在 `git gc` 前仍保有這些物件；只是刪掉遠端的 ref，日後要找回比較麻煩。

建議刪除：`git push origin --delete wip/stash-610e612`。刪除後無法從 GitHub 還原，所以要等你同意才做。

## 你同意後我會做的事

1. 依你的決定貼 (a)、(b)，或由你自己貼（文字在第 18 輪報告）。
2. 在 `feat/stats-py314` 加上第 4 項的 docstring commit，跑 check-docs 和 check-fast 後 push。
3. 刪除 `origin/wip/stash-610e612`。
4. 等 Kuan-Lun 回答第 3 題後，再處理 README PR。
