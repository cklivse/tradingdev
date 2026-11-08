## 實測結果（`main` 1ea5276）

在 `main` 1ea5276 上重現了。從本 issue 依據的 741fd84 到 1ea5276，`src/` 沒有改動。

### 重現方式

- 資料：60 天合成小時 K 線，前 30 天訓練、後 30 天測試。
- 策略：內建 `kd_crossover`，在程序內執行。
- 用 worker 自己的 `optimization._run_single_combo` 跑兩次網格，各選訓練期 Sharpe 最高的一組在測試期重跑：
  - `narrow`：`k_period` ∈ {9, 14}，共 2 組
  - `wide`：`k_period` 8 個值 × `d_period` 3 個值，共 24 組
- 用 worker 自己的 `_performance_artifacts` 產生 bundle，存進真實的 workspace storage。
- 最後交給 `RankingService.rank_run_scopes("run.sharpe_ratio", [("narrow", None), ("wide", None)])`，scope 是預設的 `test`。

結果：搜尋 24 組的 `wide` 排第 1（測試期 Sharpe −8.222），搜尋 2 組的 `narrow` 排第 2（−16.207）。

### 排名結果裡沒有的

每個候選只帶 `rank`、`tied`、`value`、`run_id`、`scope`、`strategy_id`、`revision_id`、`parameters`、`metadata`、`conditions`、`metric_source`。沒有搜尋了幾組，也沒有各組的指標。

這兩樣都在同一個 run 的 bundle 裡：

| run | `trial/{i}/train` scope | `selected_train_scope` | 試驗 Sharpe 的標準差 σ_SR（`ddof=1`） |
| --- | ---: | --- | ---: |
| `narrow` | 2 | `trial/0/train` | 0.4566 |
| `wide` | 24 | `trial/17/train` | 4.3291 |

每個 `trial/{i}/train` scope 都存了 `sharpe_ratio`。

### 把門檻算出來

DSR 的門檻是：

```text
SR*_0 = σ_SR × E[max_N]
E[max_N] = (1 − γ) Φ⁻¹(1 − 1/N) + γ Φ⁻¹(1 − 1/(N e))
```

γ 是 Euler–Mascheroni 常數（0.5772156649…），σ_SR 是試驗年化 Sharpe 的樣本標準差。

| 搜尋組數 N | σ_SR | E[max_N] | DSR 門檻 SR*_0（年化） |
| ---: | ---: | ---: | ---: |
| 2 | 0.4566 | 0.520 | 0.237 |
| 24 | 4.3291 | 1.980 | 8.571 |

兩個門檻差 36.1 倍。排第 1 的 `wide` 要越過的門檻是 `narrow` 的 36 倍，而排名結果裡這兩個數字都沒有。

驗算方式：上表用公式直接算，並另外用 statistics 拆分第 4 包（#209）的 `deflated_sharpe_ratio`，對同一組試驗 Sharpe 取 `hurdle_annualised`。兩者到小數第六位一致（0.237309、8.570670）。

公式假設 N 個試驗互相獨立。網格試驗彼此相關，所以這兩個門檻的誤差方向未知（`deflated_sharpe_ratio` docstring 的 Limitation 一段）。但兩個 run 用同樣的公式，兩者的比較仍然有意義。

### 離散度本身就是要讀的資訊

門檻高低主要由 σ_SR 決定，不只由 N 決定：N 從 2 到 24，E[max_N] 只變成 3.8 倍；σ_SR 從 0.4566 到 4.3291，是 9.5 倍。

`wide` 選中的那組（`trial/17/train`）訓練期 Sharpe 是 0.0804，比它的門檻 8.571 低得多。這個比較只有讀得到 σ_SR 才做得出來。所以需要帶上的不只是組數，試驗指標的離散度本身也有診斷價值。

這裡的 K 線是隨機漫步（常態步長），本來就沒有可交易的規律，所以這個例子示範的是機制，不是某個真實策略的結論。σ_SR 大也不單獨證明勝出那組是運氣：參數確實影響結果時，σ_SR 一樣會大。它的作用是把門檻放在對的高度。

### 這次沒有驗到的

24 組全部成功，沒有指標為 `None` 的試驗。所以本 issue 裡「`n_trials` 要包含失敗的組」那一點，這次沒有驗到。

### 重現腳本和輸出

- 腳本：[`repro_189.py`](https://github.com/cklivse/tradingdev/blob/7b66c0c839a2cf8b6c33da888811344b3c57f271/evidence/2026-11-08-round31-issue-repro/repro_189.py)
- 輸出：[`repro_189.out`](https://github.com/cklivse/tradingdev/blob/7b66c0c839a2cf8b6c33da888811344b3c57f271/evidence/2026-11-08-round31-issue-repro/repro_189.out)

在 repo 根目錄、`uv sync --locked --all-extras` 之後執行 `PYTHONPATH=. .venv/bin/python repro_189.py`。不需要 strategy-runtime 映像。腳本沿用 `tests/app/test_run_ranking.py` 的 `_manifest()`，所以輸出裡 `conditions` 的 `timeframe` 和期間是 fixture 的值，和本 issue 無關。
