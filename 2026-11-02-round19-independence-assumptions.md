# 第 19 輪：PSR／DSR／IC t 值的獨立性假設，SE 比值診斷列為提案

日期：2026-11-02。只改文件與 docstring，程式行為未變。

## 結果摘要

- `feat/stats-py314`：8994a61 → **005854f**，已 fast-forward push（三個 commit）。
- `feat/stats-public-api`：0cf2c90 → **45dfe10**（merge，無衝突），已 push。
- session-notes：證據 37ed9f4（`evidence/2026-11-02-round19-independence/`）與本報告。
- 重跑的模擬和背景數字大致吻合。唯一接近邊界的是 AR(1) 0.4 診斷的 p90：重跑得 1.55，背景是 1.62；換 6 個種子得 1.54–1.59，差距約 2.8 個標準差，仍在 3σ 內，因此沒有停下。
- Mertens (2002) 用「as cited in [BL12]」的形式引用。查證時發現 BL12 原文說這個式子在平穩遍歷報酬下也成立，文件有交代這點，並用模擬說明本專案為何仍把它當成 iid 變異數。

## 步驟 0：前置檢查

- fetch origin 與 upstream；`feat/stats-py314` 本機＝origin＝8994a61，工作樹乾淨。
- upstream/main＝a77babf；`feat/stats-public-api`＝0cf2c90，已包含 py314（d9e28bc 曾 merge），所以步驟 6 適用。

## 步驟 1：重跑模擬（證據不進 PR）

設定：seed 20261102；程式 8994a61；Python 3.14.2、NumPy 2.5.4、arch 8.0.0、pandas 3.0.6。
每筆序列 365 個報酬，邊際變異數 1，平均 0.05（每期真實 SR 0.05）。t(5) 為 iid；AR(1) 與 GARCH(1,1) 用常態創新，burn-in 500 期。
PSR 直接逐筆呼叫專案的 `probabilistic_sharpe_ratio`。腳本另用公式 SE 重算 PSR 對照，最大差 2.2e-16。區塊長度用 `sharpe._returns_block_size`。

### PSR 假陽性率與比值（每情境 20,000 筆，benchmark＝0.05，名目 5%）

| 情境 | 背景 P(PSR>0.95) | 重跑 | 95% MC 誤差 | 背景比值 | 重跑比值 |
| --- | --- | --- | --- | --- | --- |
| iid t(5) | 5.2% | 5.49% | ±0.32% | 1.00 | 1.009 |
| AR(1) 0.2 | 9.3% | 9.03% | ±0.40% | 1.23 | 1.231 |
| AR(1) 0.4 | — | 13.94% | ±0.48% | 1.53 | 1.517 |
| AR(1) −0.2 | — | 2.31% | ±0.21% | 0.82 | 0.822 |
| GARCH(0.10,0.85) | 5.3% | 5.41% | ±0.31% | 1.01 | 1.004 |

- ddof：PSR 改用 ddof=0 的 SR，差平均 0.00038、最大 0.00085（背景 0.0004／0.0009）。
- DSR 門檻用 ddof=0 會乘上 √(2/3)＝0.8165，在 N=3 時低 18.4%（背景 18%）。

### SE 比值診斷（每情境 300 組 × 1000 次重抽）

| 情境 | 真實比值（重跑） | 背景 p10/中位數/p90 | 重跑 p10/中位數/p90 | 背景 n/L<20 | 重跑 n/L<20 |
| --- | --- | --- | --- | --- | --- |
| iid t(5) | 1.01 | 0.95/1.00/1.04 | 0.94/1.00/1.05 | 0% | 0% |
| AR(1) 0.2 | 1.23 | 1.06/1.14/1.27 | 1.06/1.15/1.26 | 1% | 0% |
| AR(1) 0.4 | 1.52 | 1.23/1.39/1.62 | 1.24/1.38/1.55 | 1% | 0% |
| AR(1) −0.2 | 0.82 | 0.75/0.85/0.94 | 0.75/0.85/0.93 | 0% | 0% |
| GARCH | 1.00 | 0.81/0.98/1.09 | 0.83/0.98/1.08 | 19% | 18% |

- 中位數抓到的「與 1 的距離」：AR 0.2 為 64%，AR 0.4 為 74%，AR −0.2 為 84%。也就是少抓 36%、26%、16%，和背景的 25–40% 一致。
- AR(1) 0.4 的 p90 換種子 1–6 的結果：1.585、1.593、1.540、1.572、1.541、1.563（單次 bootstrap SE 約 0.02）。背景的 1.62 偏高約 2.8σ，算邊界但仍在抽樣誤差內；也可能是背景的創新分布不同（例如 t 分布）。結論不受影響。
- n/L<20 在 AR 0.2／0.4 的 1% 對 0%：300 組裡差 3 組，屬抽樣誤差。

### KD fixture（日報酬）

- n=366、L=3、n/L=122（和背景相同）。
- 每期 SR −0.396、g3 −1.584、g4 8.702。PSR 分母＝1 + (−0.627) + 0.302 = 0.675：峰態項占開頭 1 的 30%，動差項合計把分母壓低 33%。
- 比值（bootstrap 種子 0–9）：1.050、0.999、1.009、1.036、1.034、1.024、1.030、1.044、1.035、1.027，範圍 0.999–1.050。背景寫 1.03–1.05，應該是用的種子比較少；文件寫成 1.00–1.05。

## 步驟 2–4：PR 內的改動

| Commit | 檔案 | 內容 |
| --- | --- | --- |
| 5f450d1 | docs/statistics_bootstrap_methods.md | 新增 [LO02] 參考文獻。PSR 一節新增「Assumption: independent returns」：iid 變異數、方向、BL12 的平穩遍歷說法與本專案的解讀，並附模擬表。ddof 段補上 0.0004／0.0009。DSR 一節補 ddof=0 會低 18%，以及 PSR 的假設原樣傳到 DSR。改寫 "Not stacked with Bonferroni"：兩個維度。新增「Independence Assumptions」一節：2×2 表、波動叢聚與 KD 動差占比、Bonferroni 只和單一檢定一樣可靠。 |
| 78d3824 | src/tradingdev/domain/statistics/sharpe.py | 只改 docstring。`probabilistic_sharpe_ratio` 加 Assumption 段。`deflated_sharpe_ratio` 的 Limitation 補上 PSR 的報酬 iid 假設會原樣傳到 DSR；「Two selection corrections」的依賴性段落改成跨試驗與序列內兩個維度。 |
| 005854f | docs/statistics_leaderboard_integration.md | Two Selection Corrections 表加「Independence assumed」欄，並連到方法文件。Open Items 7：PSR/DSR 依賴性檢查提案（只報不調、欄位、n/L≥20 才報且原因中性、20 未校準、偏向 1 與 0.95–1.05 的解讀、KD 數值、Lo (2002) 延後、預定測試）。 |

sharpe.py 確認：用 AST 比對 8994a61 與修改後的版本，把模組、類別、函式的 docstring 換成 pass 後兩者相同（`AST identical apart from docstrings: True`）。diff 為 +25/−7 行，全部落在兩個 docstring 內。

## 引用查證

- 來源：BL12 預印本（davidhbailey.com/dhbpapers/sharpe-frontier.pdf）抽出的全文。
- BL12 第 1 節："we rely on Mertens (2002), who 'originally' assumed IID non-Normal returns"。第 2.4 節的式 (8) 就是這個變異數。參考文獻欄位："Mertens, E. (2002) 'Variance of the IID estimator in Lo (2002)'. Working paper, University of Basel."
- 我沒有取得 Mertens 的工作論文本身，所以文件寫成「Mertens (2002, as cited in [BL12], ...)」，沒有列入參考文獻清單。這和方法文件既有的「as cited in [LW08]」寫法一致。
- 需要注意：BL12 第 1、2.4 節引用 Opdyke (2007) 與 Christie (2005)，主張這個式子在「平穩且遍歷」的報酬下也成立，不只 iid。但 BL12 的摘要與結論又要求「取樣頻率高到不違反 IID 假設」。文件照實寫出 BL12 的說法，也寫出本專案的模擬：照現行算法（只用樣本偏態、峰態，沒有自相關項），在 AR(1) 下 SE 會被低估。所以本專案把它當成 iid 變異數。Opdyke 只標為 as cited，沒有查證原文。
- Lo (2002)：BL12 參考文獻為 "Financial Analysts Journal (July), pp. 36-52"，和題目給的 58(4), 36–52 一致，已加為 [LO02]。

## 步驟 5：檢查

- `scripts/check-docs.sh`：通過（22 份文件）。
- `scripts/check-fast.sh`：通過（commit 78d3824 前跑一次，005854f 再跑一次）。
- `uv run pytest tests/domain/statistics`：660 passed。
- 沒有跑 check-full，理由：只改文件與 docstring，AST 不變。依 AGENTS.md，文件變更跑文件檢查即可，註解或格式變更跑快速檢查即可。
- 沒有安排獨立模型審查，理由：依 AGENTS.md，文件與一般程式註解變更不強制審查。
- push：`8994a61..005854f`，fast-forward。

## 步驟 6：feat/stats-public-api

- 已 merge 過 py314，所以在獨立 worktree 用 merge（不 rebase）接上 005854f，無衝突，產生 45dfe10。
- 在該 worktree 跑 check-docs（23 份文件）與 check-fast，都通過；push `0cf2c90..45dfe10`。
- 未改：`docs/statistics_public_api.md` 的注意事項只寫「DSR 假設試驗獨立」，沒有提到報酬 iid（PSR 與 DSR 都受影響）。這句話沒有錯，但已不完整。這輪範圍只有 merge，所以沒有補；建議下一輪加一條。

## 步驟 7

證據 commit 37ed9f4（simulate.py、output.md、ar04_p90_seed_check.py/.out、README.md）；本報告另一個 commit。

## 給 Kuan-Lun 的短訊（#38）

依第 8 步，這段併入 (a) 的最後一段，見下方「第 8 步」。
