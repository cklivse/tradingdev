# 第 33 輪（續）：Kuan-Lun 在 #206–#209 的修改、重驗、第 5 包合併

> 同日稍早的〈統計模組簡報草稿〉也標第 33 輪（`2026-11-09-round33-statistics-talk-draft.md`），
> 依指示這份也標第 33 輪，用檔名區分。

## 結論

- **沒有 force push。** `ebac927` 仍是 `stats/4-sharpe` 的祖先，也是第 4、5 包的 merge-base。
  GitHub 上 #206–#209 的 timeline 都沒有 `head_ref_force_pushed` 事件。
  - 用 `+refs/heads/stats/*` 強制 fetch 後，五條分支的 head 和上一輪相同：
    c8154a8、fc62da5、dfb383d、bede2d0、a216dc4。
  - #209 從 `ebac927` 到 `bede2d0` 有 365 個 commit，因為中間有一個 merge main 的 commit（e49b1ef）。
- **任務 1**：Kuan-Lun 自己的 commit 共 34 個。依 `git patch-id` 去掉跨分支重複後是 20 個修改。
  - **沒有發現錯誤。** 可以實測的說法都實際跑過；描述 main 的說法都在 `ad2fb75` 上核對過。
  - 有 4 處修正的正是我們先前寫錯的句子。
  - 有幾處是「刪掉證據、改成較弱的說法」，不算錯，列在「可以在 PR 上討論的地方」。
  - 你提出的「正自相關時 PSR 和 DSR 偏樂觀」本身有條件，見任務 1 第 2 點。
- **任務 2**：四包併入 `ad2fb75` 都沒有衝突；`uv sync --locked`、check-fast 都通過。
  測試數和上一輪相同：36／88／130／146。
- **任務 3**：第 5 包 merge `bede2d0` **沒有任何衝突**。第 5 包相對 `ebac927` 只新增 comparison／benchmark
  的四個檔案，沒動過 sharpe.py 或 `__init__.py`，所以他改的檔案全部原樣採用。
  - 合併後有 **三處語意不一致**：都在我們的 comparison.py 裡，和他新的 sharpe 文字對不上。
    依指示沒有修改，列在「任務 3：要你決定的地方」。
  - 檢查結果見任務 3。
- **任務 4**：四份 body 只改 verified-at 那一行，因為測試數沒變。全文在 `2026-11-09-round33-pr-bodies/`。
  - 我沒有在 GitHub 上編輯 body，原因見任務 4。
  - 另外有三處 body 的敘述已經和分支現況不符，要你決定要不要改。

## 任務 1：逐條判斷

分支欄位的寫法是「1／2／3／4 = 出現在哪幾包」。同一個 patch 在各包的 SHA 不同；用 `git patch-id --stable`
判斷是否相同，第 2、3、4 包的型別 commit 內容略有差別，分開列出。

### A. 型別與測試檔位置（不改執行時行為）

| commit | 包 | 內容 | 判斷 |
| --- | --- | --- | --- |
| 40c52a2／0ca3ec3（1／2） | 1、2 | `periods.py` 回傳型別 `pd.Series` → `pd.Series[float]`；新增 `tests/typing/statistics.py`，用 `assert_type` 檢查 | 只有註記，執行時行為不變 |
| bf06bcc（3） | 3 | 同上，另把 `test_statistics_plateau.py` 的 `_scores`／`_summary`／`_grid` 從 `**kwargs: Any` 改成明確關鍵字參數，兩處 `np.int64` 呼叫加 `# type: ignore[arg-type]`；新增 `tests/typing/plateau_helpers.py`（負向型別檢查） | 測試斷言沒有刪減，只是讓 mypy 能檢查參數名稱 |
| 8045887（4） | 4 | 同 periods，另加 `performance.py` 的 `_sample_std`、`_sharpe` 參數型別 | 只有註記 |
| 959a7bf／714072e／adc3725／246f638 | 1–4 | `tests/typing/*.py` 移到 `tests/domain/statistics/typing_*.py`，內容不變（0 行差異） | 檔名不是 `test_` 開頭，pytest 不收集，所以測試數不變；由 strict mypy 檢查 |

### B. `_scaling.py`、`_validation.py`、`periods.py`（ce3bfcc、bff8c08、c8154a8；1–4 包都有）

**B1. `_scaling` 模組 docstring（ce3bfcc）**

改前：

> Exact power-of-two rescaling for values at extreme magnitudes or spreads. … When both lie inside
> ``[2**-60, 2**60]`` the values are returned unchanged. Otherwise they are multiplied by the power of two that
> brings the spread into ``[0.5, 1)``, or the magnitude when there is no finite, positive spread to use.
>
> Multiplying by a power of two is exact for every value that stays a normal float, and floating-point sums,
> products, quotients and square roots commute with it. A statistic that is invariant to a positive scale
> therefore gives bit-for-bit the same result on rescaled values whenever the unscaled computation did not
> overflow or underflow, and a finite one where it did.

改後：

> Power-of-two rescaling for values at extreme magnitudes or spreads. … Values remain unchanged when the spread
> is at least ``2**-60`` and the largest magnitude is at most ``2**60``. Empty and all-zero arrays also remain
> unchanged. Otherwise a power of two brings the spread into ``[0.5, 1)``, or the magnitude when there is no
> finite, positive spread to use.
>
> Power-of-two scaling is exact for values that remain representable as normal floats. It reduces overflow and
> underflow in deviation-based calculations, but does not guarantee bit-for-bit equivalence or a finite
> statistic. Extreme magnitude ranges can make smaller observations subnormal or underflow to zero, losing
> information even for a mathematically scale-invariant statistic.

**判斷：正確，而且修正了我們的錯誤。**

- 新的條件和程式 `if spread >= _LOWER and peak <= _UPPER: return 0` 逐字對應。舊文的「both inside
  `[2**-60, 2**60]`」不精確。
- 舊文保證「溢位時會得到有限結果」，這說過頭了。
- 實測：`rescaled([1e-300, 1e300, 0.0])` 的指數是 997，`1e-300` 縮放後變成 `0.0`，資訊遺失，正是他新加的那句。

`scale_exponent` 的 docstring 同步改寫（`such that values * 2**-e is safe to use` → `used to moderate magnitude
or spread`，並加上可能遺失小值的提醒）。正確。

**B2. `positive_int` docstring（ce3bfcc）**

改前：

> ``bool`` is an ``int`` subclass and NumPy integers are not ``int``, so both are rejected. This is the rule the
> annotations already state: mypy rejects ``True`` and ``np.int64(5)`` for an ``int`` parameter as well.

改後：

> ``bool`` is an ``int`` subclass and NumPy integers are not ``int``, so both are rejected at runtime. Static
> typing permits ``bool`` where ``int`` is expected, so the boolean restriction requires this explicit check.

**判斷：正確，修正了我們的錯誤。**

- 實測：對 `def f(x: int)` 用 strict mypy 檢查，`f(True)` 不報錯，`f(np.int64(5))` 報 `arg-type`。
- 舊文說 mypy 拒絕 `True` 是錯的。

**B3. `_validation` 模組 docstring（c8154a8）**

改前：

> Every check here narrows such input to the declared type or raises ``ValueError`` naming the argument; none
> converts a value of the wrong kind, because a silent conversion is how a wrong input becomes a plausible but
> wrong answer.

改後：

> Unsupported kinds are rejected with ``ValueError`` instead of deliberately coercing booleans or text into
> numbers. NumPy array construction and float64 conversion failures propagate and need not name the argument;
> for example, an unrepresentable integer can raise ``OverflowError``. Accepted numeric kinds do not guarantee
> finite float64 values, so callers must also check shape and finiteness.

**判斷：正確。** 舊文「或 raise ValueError」說過頭了。

- 實測：`real_array([2**1100], "x")` 拋出 `OverflowError: int too large to convert to float`。
- 實測：`real_array([inf], "x")` 被接受。

**B4. `periods` 模組 docstring 與兩個函式（bff8c08）**

模組，改前：

> Period P&L therefore always sums to ``equity_curve[-1] - equity_curve[0]``.

模組，改後：

> In exact arithmetic, period P&L sums to ``equity_curve[-1] - equity_curve[0]``. Floating-point rounding or
> overflow can break this identity, including producing nonfinite period changes from finite equity values.

`to_utc_index`：

- 「Numbers are rejected」改成「Numeric arrays and numeric elements retained in object arrays are rejected」。
- 新增一段：

  > Non-DatetimeIndex inputs pass through ``np.asarray`` before validation. Mixed sequences can therefore lose
  > their original element types: for example, ``[2024, "2025-01-01"]`` becomes strings and parses as dates.
  > Numeric rejection does not cover values already coerced to date strings; callers must normalize mixed
  > numeric/text inputs before calling.

- Raises 的「If ``timestamps`` is not one-dimensional」改成「If the converted input is not one-dimensional」。

`period_returns`，改前：

> Compounding the returns reproduces ``equity_curve[-1] / equity_curve[0]``.

`period_returns`，改後：

> In exact arithmetic, compounding the returns reproduces ``equity_curve[-1] / equity_curve[0]``.
> Floating-point rounding, underflow or overflow can break this identity. In particular, a sufficiently small
> positive closing/opening ratio can round to a return of -1, losing the remaining capital when compounded;
> finite inputs do not ensure finite return values.

**判斷：三處都正確。** 實測：

- `to_utc_index([2024, "2025-01-01"])` 得到 `2024-01-01`、`2025-01-01`。數字 2024 沒有被拒絕，正如他寫的。
- `period_returns([1.0, 1e-17, 1e-17], …)` 得到 `[0.0, -1.0, 0.0]`。
- `period_pnl([1.7e308, -1.7e308, 1.7e308], …)` 得到 `[0.0, -inf, inf]`。

### C. `breakeven.py` 與 ARCHITECTURE（第 2 包）

**C1. 模組 docstring（6976d1c）**

改前（三處）：

> * A trade wins when its ``net_pnl`` is above zero and loses when it is below zero, as in
>   :mod:`tradingdev.domain.statistics.performance`.
> * … With this denominator the win-rate edge is positive exactly when the trades' total ``net_pnl`` is positive.
> * Undefined figures (no wins, no losses, no notional, no capital basis) are ``None`` rather than infinities or
>   zeros.

改後：

> * A trade wins when its ``net_pnl`` is above zero and loses when it is below zero.
> * … When both wins and losses are present, this denominator makes a positive win-rate edge equivalent to
>   positive total ``net_pnl`` in exact arithmetic. Without either group the edge is ``None``. Floating-point
>   rounding or overflow can break the equivalence.
> * Structurally undefined figures (no wins, no losses, no notional, no capital basis) are ``None`` rather than
>   invented zeros. Finite inputs do not ensure finite aggregates or ratios: intermediate sums can overflow, and
>   subsequent arithmetic can produce infinities or NaN. Formulas and reconciliation statements describe exact
>   arithmetic and are subject to these limitations.

**判斷：正確，修正了我們的錯誤。**

- 舊文「exactly when」在只有獲利交易時不成立：此時總 `net_pnl` 為正，但 `win_rate_edge` 是 `None`。
- 推導：edge > 0 ⇔ w/(w+l) > L̄/(W̄+L̄) ⇔ w·W̄ > l·L̄ ⇔ 總盈 > 總虧，前提是兩組都有。
- 刪掉「as in performance」是因為第 2 包不含 performance。說法本身沒錯，只是少了交叉參照。

**C2. ARCHITECTURE「績效計算」表新增 `domain/statistics/breakeven.py` 一列（40c07b4，fc62da5 再把「見函式 docstring」
改成「見模組與函式 docstring」）**

> `summarize_breakeven` 從呼叫端提供的交易、評估起訖及可選本金計算損益兩平勝率與周轉成本；欄位、未平倉處理及不可用
> 條件見模組與函式 docstring。獨立計算，不讀取 runs，尚未接入績效發布或 MCP 查詢

**判斷：正確**，和函式簽名與模組行為一致。

### D. `plateau.py` 與 ARCHITECTURE（第 3 包）

**D1. Integration contract 的一條（dfb383d）**

改前：

> * Upstream currently persists only ``trial/{index}/train``, so the resulting plateau is in-sample. Label it as
>   in-sample; it is not out-of-sample evidence.

改後：

> * Successfully published optimization results retain per-trial scopes as ``trial/{index}/train``, including
>   completed evaluations with an undefined objective. They also contain the selected candidate's out-of-sample
>   test scope, not a test scope for every grid point. A plateau built from the per-trial training scopes is
>   in-sample and must be labelled as such. Execution errors, timeouts, or failure to select a valid objective
>   can stop the job before trial scopes are published. Those failed searches cannot be reconstructed from
>   persisted training scopes alone; this module still requires the caller's complete grid rows.

**判斷：正確，修正了我們的錯誤。** 在 `ad2fb75` 的 `mcp/workers/optimization.py` 核對：

- `_performance_artifacts` 對 `evaluations` 每一筆都建立 `trial/{index}/train`，另外建立一個 `test` scope，
  `default_scope="test"`。所以舊文「只保存 train」是錯的。
- `candidates` 由 `all_results` 全部建立，`metric_value` 可為 `None`，由 `best_result` 略過。
- trial timeout、批次錯誤、`best_result` 的 `ValueError`（沒有有效目標值）、樣本外測試錯誤，都在發布前呼叫
  `_fail` 後 return。

**D2. ARCHITECTURE 新增 `domain/statistics/plateau.py` 一列（d64b54c，258f9f9 同樣改成「模組與函式 docstring」）**

**判斷：正確。**

### E. `sharpe.py`（第 4 包，你要求特別細看的部分）

**E1. 001c09f「make Sharpe guidance self-contained」**

模組 Frequency 段，改前：

> Frequency: compute these statistics on daily returns. Annualising intraday returns with
> ``sqrt(periods_per_year)`` assumes independent periods, but intraday strategy returns are autocorrelated, so an
> hourly Sharpe is systematically biased against the daily one; a KD strategy measured -8.70 annualised from
> hourly returns versus -7.57 from daily returns. ``periods_per_year`` is therefore normally 365 for crypto or 252
> for exchange-traded markets.

模組 Frequency 段，改後：

> Frequency: use daily returns for daily-return analysis and choose ``periods_per_year`` for the caller's
> annualisation basis. Square-root annualisation does not remove frequency dependence: serial correlation and
> compounding can change the ratio, and the direction depends on the return process. Report the frequency and
> compare ratios at matching frequencies and annualisation bases.

PSR 的獨立性段，改前：

> Positively autocorrelated returns have a larger true standard error, so the probability is too optimistic (in
> a simulation with AR(1) coefficient 0.2, ``PSR > 0.95`` occurred 9% of the time instead of the nominal 5%);
> negatively autocorrelated returns make it too conservative. See "Independence Assumptions" in
> docs/statistics_bootstrap_methods.md.

PSR 的獨立性段，改後：

> Serial correlation can invalidate the reported probability; this function does not estimate an effective
> sample size or adjust for serial correlation.

DSR 的 `n_trials`：刪掉「With plateau analysis, `trials_from_metrics` returns the dropped count for this purpose;
pass ``n_trials = len(result.trials) + result.dropped_count``」，改成「Track all attempted trials before
filtering out undefined Sharpes and pass that total as ``n_trials``.」

DSR 繼承 PSR 假設，改前：

> positively autocorrelated returns make it too optimistic, separately from any error in the trial correction.

DSR 繼承 PSR 假設，改後：

> serial correlation can invalidate its probability, separately from any error in the trial correction.

DSR 的「Within one series」，改前：

> treats the ICs of non-overlapping windows as independent, and this function treats the returns as independent
> through its PSR. So the DSR needs both kinds of independence and Bonferroni only the second. See "Independence
> Assumptions" in docs/statistics_bootstrap_methods.md.

DSR 的「Within one series」，改後：

> approximates effective sample size as ``bars // window`` to account for overlap, without estimating remaining
> serial dependence. This function uses the independent-return variance through its PSR. Bonferroni's
> robustness to dependence between tests does not repair miscalibrated individual IC tests.

同一個 commit 在 ARCHITECTURE 新增 `domain/statistics/` 一列，並在「績效計算與對話摘要」加一段（零無風險利率、金額型
`max_drawdown`、交易統計計入所有紀錄、未接入績效發佈或 MCP）。

**判斷：正確；但刪掉了幾項我們有證據的內容。**

- 新的 Frequency 段正確：自相關的正負決定小時 Sharpe 比日 Sharpe 高或低。
- 「`bars // window`」在 `ad2fb75` 的 `ml/evaluation/metrics.py` 核對過：`n_effective = max(1, n_bars // window)`，
  docstring 寫「Use effective sample size ``bars // window``」。舊文說「把不重疊視窗的 IC 當成獨立」不夠精確。
- 刪掉 plateau 和 `docs/statistics_bootstrap_methods.md` 的參照是必要的：第 4 包沒有這兩者，留著會變成斷掉的參照。
- 刪掉的有 KD 的 -8.70／-7.57 量測值，以及 AR(1) 0.2 的 9%／5% 模擬。原文的方向說法有條件，見 E3。
- 刪掉了「`len(result.trials) + result.dropped_count`」這個具體算法。第 3 包合併後可以考慮在 plateau 那邊補回。

**E2. be80ac5「state single-series bootstrap interval limits」**

`IntervalUnavailable` 類別 docstring，改前：

> Why a bootstrap interval is missing, with what could still be computed. …
> * ``"insufficient_observations"``: fewer than ``min_observations`` returns (after alignment, for comparisons),
>   so the block length cannot be estimated. …
> * ``"undefined_statistic"``: the statistic of the returns themselves is undefined, such as the Sharpe ratio of
>   constant returns.
> * ``"no_valid_resample"``: no resample defines the statistic.
>
> estimate: The statistic of the returns, or ``None`` when it is undefined; … For a paired comparison it is the
> difference. observations: Number of returns, after alignment for comparisons.

`IntervalUnavailable` 類別 docstring，改後：

> Why a Sharpe interval is missing, with what could still be computed. …
> * ``"insufficient_observations"``: fewer than ``min_observations`` returns, so the sample is too short for the
>   bootstrap. …
> * ``"undefined_statistic"``: the Sharpe ratio of the returns is undefined, such as for constant returns.
> * ``"no_valid_resample"``: no resample has a defined Sharpe ratio.
>
> estimate: The annualised Sharpe ratio, or ``None`` when it is undefined; … observations: Number of returns in
> the input series.

`sharpe_interval_outcome` 的覆蓋率段，改前：

> The rule improves coverage but does not guarantee it. In the review simulation (two volatility regimes …
> 1000 periods, 100 samples, 300 resamples), nominal 95% intervals covered the true Sharpe ratio in 70 samples,
> against 49 with blocks fitted to the returns alone; … The jackknife influence values used for paired
> differences covered 60 … independent returns (94 of 100) … AR(1) … (93); … GARCH(1,1) … 89 against 91 …

`sharpe_interval_outcome` 的覆蓋率段，改後：

> Automatic block selection does not guarantee nominal coverage. When regimes persist for much of the sample,
> too few transitions may be observed to estimate the sampling variability reliably, regardless of block length.

**判斷：**

- **單看第 4 包是正確的。** 第 4 包裡只有 Sharpe 使用 `IntervalUnavailable`。舊文說「block length cannot be
  estimated」也不精確：真正的原因是 API 設了 20 期門檻。
- **合併第 5 包後會變成錯的。** comparison 用同一個類別裝「任意統計量的差」，見任務 3 的 C1、C2。
- 刪掉覆蓋率模擬數字：新句子本身正確，但少了量測證據。
- 你要求確認的「區塊長度取原始報酬和平方報酬兩個估計的最大值」**保留了**，在 `sharpe_interval_outcome` 的 Block size 段：
  「the larger of two Politis and White (2004) automatic estimates … one for the returns and one for the squared
  returns」。程式 `_returns_block_size` 也沒變。

**E3. e88f23f「qualify PSR probability direction」**

改前：

> Negative skew and fat tails widen the Sharpe estimator's standard error and lower the probability.

改後：

> For a positive ``SR``, more negative skew and greater kurtosis increase the standard error, holding the other
> terms fixed. A larger standard error moves the probability towards 0.5: down when ``SR > SR*`` and up when
> ``SR < SR*``. The skew term reverses direction for negative ``SR``.

**判斷：正確，修正了我們的錯誤。**

- 公式是 z = (SR − SR*)·√(n−1)/√(1 − g3·SR + (g4−1)/4·SR²)。
- 分母變大會讓 |z| 變小，Φ(z) 往 0.5 移動。舊文「lower the probability」只在 SR > SR* 時成立。
- 峰態項的係數是 SR²/4，恆非負；偏態項的係數是 −SR，隨 SR 的符號反向。他寫「只有偏態項反向」也正確。

**關於你的第 2 點（「正自相關時 PSR 和 DSR 偏樂觀」）：這個說法本身有條件。**

- 正自相關時，iid 公式低估了 Sharpe 估計量的真實標準誤，所以 |z| 被高估，PSR 被推離 0.5。
  這和 e88f23f 用的是同一個機制，只是方向相反。
- 結果是：SR > SR* 時 PSR 偏高（偏樂觀），SR < SR* 時 PSR 偏低。
- DSR 也一樣：被選出的策略若低於門檻（DSR < 0.5），正自相關會讓 DSR 更低，是偏保守而不是偏樂觀。
- 我們舊文的 AR(1) 模擬（9% 對 5%）量的是「PSR > 0.95」的頻率，這是 SR > SR* 那一側，所以和這個結論一致。
- Kuan-Lun 現在的「can invalidate」正確，但比可證明的內容弱。

如果要在 PR 上提，建議的精確說法：

> Positive serial correlation makes the iid standard error too small, which pushes the probability away from
> 0.5: too high when ``SR > SR*``, too low when ``SR < SR*``.

**E4. 815a4a7「qualify bootstrap inference assumptions」**

`sharpe_interval_outcome` 開頭，改前：

> Strategy returns are autocorrelated, and an iid bootstrap that shuffles single periods destroys that dependence
> and understates the sampling variability. The stationary bootstrap … keeping the short-range dependence while
> producing a stationary resample.

`sharpe_interval_outcome` 開頭，改後：

> Strategy returns can exhibit serial dependence. An iid bootstrap that shuffles single periods removes that
> dependence and may misstate the sampling variability. The stationary bootstrap … preserving local order within
> each block. This does not make inference valid for an arbitrary non-stationary return process.

Block size 段：

- 「blocks fitted to the returns alone then cut」改成「can cut」。
- 刪掉「Nearly independent returns with stable volatility still get a block length near one. The estimate needs a
  reasonable sample, so fewer than … give no interval.」
- 換成：

  > Finite-sample block estimates can vary even for independent returns. This API requires at least
  > ``MIN_BOOTSTRAP_OBSERVATIONS`` returns … Meeting that threshold does not establish that the sample is adequate
  > for reliable inference.

block_size 參數段，改前：

> A block length that is too short narrows the interval; one that is too long costs only precision.

block_size 參數段，改後：

> Blocks that are too short can omit dependence; excessive block lengths can leave too few block restarts and
> produce unreliable or nearly degenerate intervals. Either choice can impair coverage.

PSR 段，改前：

> The standard error in the denominator is the variance of the Sharpe estimator for iid returns

PSR 段，改後：

> The standard error uses an asymptotic variance expression for iid returns

另外兩處程式註解措辭（`exact rescaling` → `rescaling`；`_period_sharpe` 的註解）只改文字。

**判斷：正確，修正了我們的錯誤。**

- 舊文「太長只損失精度」說過頭了：區塊太長時重抽的起點太少，區間會不可靠甚至退化。
- 舊文把標準誤和變異數混為一談；公式也是漸近式。
- 「最大值規則」仍在（見 E2）。

**E5. f12202b「state annualised hurdle overflow limit」**（你說不知道指什麼）

`DeflatedSharpe.hurdle_annualised` 屬性，改前：

> The hurdle ``SR*_0`` annualised, the expected maximum Sharpe of ``n_trials`` skill-less trials.

`DeflatedSharpe.hurdle_annualised` 屬性，改後：

> … This can overflow to infinity even when the validated per-period hurdle is finite; this output is not
> separately validated.

`deflated_sharpe_ratio` 的 Raises，改前：

> or the trial Sharpes are so dispersed that the hurdle is not a finite number.

`deflated_sharpe_ratio` 的 Raises，改後：

> the dispersion calculation overflows, or the per-period hurdle is nonfinite.

**指的是什麼：**

- 程式只檢查「每期門檻」`hurdle = std_annualised / scale * expected_max` 是否有限，有限才往下算。
- 回傳的 `hurdle_annualised = hurdle * scale` 沒有再檢查。
- 試驗 Sharpe 的離散度接近浮點上限時，每期門檻還有限，乘回 √365 就溢位成 `inf`。
- Raises 的改寫則是如實列出程式裡兩個拋出 `_DISPERSED_TRIALS` 的位置：標準差計算溢位，以及每期門檻不是有限值。

**判斷：正確。** 在 `stats/4-sharpe` 實測：

- 呼叫：`deflated_sharpe_ratio(r, [0.0, 1.7e308], periods_per_year=365, n_trials=1000)`
- 回傳：`DeflatedSharpe(dsr=0.0, psr_vs_zero=0.9449…, hurdle_annualised=inf, n_trials=1000,
  trial_sharpe_std_annualised=1.2020815280171307e+308)`

只有在年化試驗 Sharpe 達到 1e307 量級才會發生，實務上不會遇到。他選擇只寫在文件、不改程式。

**E6. bede2d0「distinguish selection correction populations」**

改前：

> … Bonferroni asks whether any of ``N`` IC tests would reject at family-wise ``alpha``. They are not
> interchangeable, and never both apply to the same number: each already accounts for the whole selection, so
> stacking them corrects one selection twice. When reports show both side by side, label each figure with the
> correction it carries. They also differ in what they assume about independence, …

改後：

> … Bonferroni asks whether any of ``N`` IC tests would reject at family-wise ``alpha``. Their candidate
> populations also differ: this function requires all attempted trials in ``n_trials``, while ``rank_entries``
> in the ML leaderboard passes only ``ranked_total`` to its Bonferroni caveat. That count includes rankable
> candidates before ``top_k`` truncation, but excludes skipped entries and any candidates filtered out before
> ranking. The caveat alone does not establish coverage of the complete research search history.
>
> The corrections are not interchangeable. When reporting them side by side, label the metric, correction and
> candidate population; do not apply a second correction to the same selection without defining the statistical
> procedure. They also differ in what they assume about independence, …

**判斷：正確，沒有把淨方向寫成確定的。**

- 「Bonferroni rests on the union bound, which holds whatever the dependence between the ``N`` tests, so correlated
  candidates only make it conservative; this function's hurdle is the expected maximum of ``N`` independent
  trials」這段**原封保留**。
- Limitation 段完全沒動，仍是：「Which effect dominates has not been measured, so the net direction of the error
  is unknown: the result may under- or over-correct for the selection.」
- 新加的母體說法在 `ad2fb75` 核對過：
  - `rank_entries` 只在 `result.ranked_total > 1` 時把 `ranked_total` 傳給 `_selection_caveat`。
  - `ranked_total` 的定義（`domain/ranking.py`）是「had a usable value before ``top_k``」。
  - `skipped` 另列，不計入；呼叫端先過濾掉的候選本來就不會進來。
- 舊文說「each already accounts for the whole selection」**是錯的**：`ranked_total` 不一定涵蓋完整搜尋歷史。他把它刪了。
- 措辭變弱的地方：舊文「never both apply to the same number」，新文「do not apply a second correction to the same
  selection without defining the statistical procedure」。這留了空間，不是錯誤。
  我在簡報草稿第 20 頁寫的「不套在同一個數字上」比他現在的說法強，簡報恢復時要對齊。

### F. 介紹簡報與 ARCHITECTURE 總覽（471cedc、bb13cc2、db2bdda；第 4 包）

最終結果（三個 commit 疊起來）：

- 04 章首頁的引言從「目前主線已有完整回測績效與排行榜；PR #38 的統計擴充仍是未合併項目。」
  改成「回測績效與排行榜使用已保存的結果；統計 API 提供獨立計算，尚未接入結果查詢。」並刪掉 PR #38 狀態的來源註解。
- 「主線績效與 PR #38 擴充」頁改名為「績效管線與獨立統計 API」，表格內容如下：

  | 範圍 | 已提供的內容與限制 |
  | --- | --- |
  | 績效管線 | 一般 run performance、年化報酬、Sharpe、日／月損益及 run leaderboard |
  | 獨立統計 API | `domain/statistics` 例如提供期間分析、原始資料績效摘要及 Sharpe 推論 |
  | 整合邊界 | 統計 API 尚未接入績效發布或 MCP 結果查詢，並非排行榜新增欄位 |

  另加頁尾「模組責任與統計慣例見 ARCHITECTURE.md 的績效計算與對話摘要。」並刪掉原本三條來源註解。
  bb13cc2 曾加上「候選配對比較、參數平台等擴充不屬於此處已提供的統計 API。」，db2bdda 又刪掉，同時加上「例如」。
- 參考資料的「PR #38」改成「統計研究背景：PR #38」。
- db2bdda 把 ARCHITECTURE 的 `domain/statistics/` 一列改成「由呼叫端提供觀察值或試驗資料的獨立統計計算與推論；入口見
  「績效計算與對話摘要」」。

**判斷：和模組實際行為一致。**

- 「獨立計算、未接入結果查詢、不是排行榜欄位」：五條分支的 app／mcp／adapters 都沒有匯入 `domain.statistics`。
- 第 4 包含 periods、performance、sharpe，正好是「期間分析、原始資料績效摘要及 Sharpe 推論」。
  加了「例如」之後，第 2、3、5 包合併進來也不會失真。db2bdda 刪掉 bb13cc2 那句也是對的，否則第 3 包合併後會變成錯的。
- 「試驗資料」涵蓋 plateau 的輸入。
- 頁尾指向的段落確實在 #209 分支 ARCHITECTURE 的「績效計算與對話摘要」一節裡（001c09f 新增）。
- 唯一的取捨：頁面原本的 `來源：` 註解被刪掉了，這兩頁現在沒有可追溯的來源。這是格式取捨，不是內容錯誤。

### 有沒有錯的或講得比證據強的

**沒有。** 20 個修改裡沒有發現錯誤，也沒有比證據更強的說法。方向剛好相反：

- **他修正了我們的 6 處錯誤或過強說法**：
  1. mypy 不會拒絕 `bool`（B2）
  2. 縮放保證有限結果（B1）
  3. 勝率優勢「exactly when」（C1）
  4. 最佳化「只保存 train」（D1）
  5. PSR「lower the probability」（E3）
  6. 區塊太長「只損失精度」（E4）
- **可以在 PR 上討論的地方**（他刪掉了證據，或說法比可證明的弱）：
  1. PSR／DSR 自相關的方向：建議補上 E3 那句有條件的說法。
  2. AR(1) 9%／5%、覆蓋率 70／49 等模擬數字和 KD -8.70／-7.57：要不要找地方保留。這些原本出自
     `docs/statistics_bootstrap_methods.md`，只在 #38 上。
  3. `n_trials = len(result.trials) + result.dropped_count`：第 3 包合併後要不要補回。
  4. 「不同時套用兩種修正」：他的版本允許「定義好程序」後疊加。

## 任務 2：在 ad2fb75 上重驗四條分支

每包都在 `ad2fb75` 的 detached worktree 上 merge 分支 head，跑 `uv sync --locked --all-extras` 和
`scripts/check-fast.sh`，再跑自己的測試：

| 包 | head | 合併 | `uv sync --locked` | check-fast | 測試 |
| --- | --- | --- | --- | --- | --- |
| 1 | c8154a8 | 無衝突 | 成功 | 通過 | `tests/domain/statistics`：36 passed |
| 2 | fc62da5 | 無衝突（ARCHITECTURE.md 自動合併） | 成功 | 通過 | 88 passed |
| 3 | dfb383d | 無衝突（ARCHITECTURE.md 自動合併） | 成功 | 通過 | `tests/domain/statistics` 127 passed；加 `tests/mcp/test_optimization_failed_trials.py` 共 130 passed |
| 4 | bede2d0 | 無衝突（ARCHITECTURE.md 自動合併） | 成功 | 通過 | 146 passed |

- 測試數和上一輪相同。
- 959a7bf 等搬移的是 `typing_*.py`。pytest 只收集 `test_*.py`，所以不受影響；這些檔案改由 check-fast 的 strict mypy 檢查。
- 每個 worktree 跑完都沒有修改或未追蹤的檔案。

## 任務 3：第 5 包

在本機 `stats/5-comparison`（a216dc4）上 `git merge origin/stats/4-sharpe`（bede2d0）：**自動合併，沒有衝突。**
merge commit 是 `7b522c2`。

逐檔核對合併後的 blob：

| 檔案 | 來源 |
| --- | --- |
| `_scaling.py`、`_validation.py`、`performance.py`、`periods.py`、`sharpe.py`、`typing_periods.py` | 和 bede2d0 相同（他的版本） |
| `comparison.py`、`benchmark.py`、兩個測試 | 和 a216dc4 相同（我們的版本） |
| `__init__.py`、其餘測試 | 兩邊相同 |

合併結果相對 bede2d0 只多了我們的四個檔案（+2176 行）。

你預期的 sharpe docstring 和 `__init__.py` 衝突沒有出現。第 5 包從 `ebac927` 之後只新增 comparison／benchmark，
沒有改過這兩個檔案；`__init__.py` 兩邊都還是一行 docstring，完整總覽只在 #38 上。

### 任務 3 檢查

| 範圍 | 合併 | 改動（相對 ad2fb75） | `uv sync --locked` | check-fast | 測試 |
| --- | --- | --- | --- | --- | --- |
| 第 5 包（7b522c2）併入 ad2fb75 | 無衝突 | 18 個檔案，+4786／−19 | 成功 | 通過 | `tests/domain/statistics`：303 passed |
| 五包一起：依序 merge 1、2、3、7b522c2（4 經由 5） | 無衝突 | 24 個檔案，+7168／−19 | 成功 | 通過 | `tests/domain/statistics` + `tests/mcp/test_optimization_failed_trials.py`：449 passed |

- 測試數和上一輪相同。
- 這次第 1 包要明確 merge：Kuan-Lun 在各包分別套用相同的 patch，產生不同的 SHA，所以第 1 包的 head 不再是第 4 包的祖先。
  兩邊內容相同，合併沒有衝突。
- KD 四個釘值：把 9c1abc8 的 7 個 KD fixture／測試檔（取自 005854f）複製到五包合併的暫存樹，結果 4 passed。
  另外用 `==` 和釘值比對：

```text
days        366                   366                   EQUAL
sharpe      -7.565103143673017    -7.565103143673017    EQUAL
notional    5014735.715506879     5014735.715506879     EQUAL
cost_share  0.863481526386825     0.863481526386825     EQUAL
```

- 比對腳本存在 `2026-11-09-round33-pr-bodies/kd_eq.py`（上一輪的腳本沒有存下來，這次照 fixture 測試的計算重建）。
- `7b522c2` 已推到 `origin/stats/5-comparison`（a216dc4 → 7b522c2，fast-forward）。
- 第 5 包的 body 依指示等之後再更新；PR 還沒開。

### 任務 3：要你決定的地方（沒有修改）

合併沒有文字衝突，但 Kuan-Lun 對 sharpe.py 的修改，讓我們 comparison.py 的三處說法變得不一致：

- **C1. `IntervalUnavailable` 現在只描述 Sharpe**，但 comparison 用它裝別的東西：
  - be80ac5 把類別改寫成：「Why a Sharpe interval is missing」、`estimate: The annualised Sharpe ratio`、
    `observations: Number of returns in the input series`。
  - comparison 的 `_unavailable` 用它回傳配對差與任意統計量：`estimate` 是差值或任意統計量，
    `observations=aligned.overlap`，`min_observations=aligned.min_overlap`。
  - comparison 的 docstring 也寫「Its ``estimate`` is the difference」。
  - 舊版類別 docstring 原本有「after alignment, for comparisons」「For a paired comparison it is the difference」。
  - 可能的做法：
    - (a) 在 #209 上請 Kuan-Lun 讓類別保持通用措辭
    - (b) 在第 5 包加一個 commit 擴充類別 docstring（但這會改到他剛改過的 docstring）
    - (c) 讓 comparison 用自己的類別
- **C2. `interval_table_outcome` 的參照失效**：docstring 寫「This is the rule of `sharpe_interval_outcome`, whose
  docstring gives its measured coverage: better than blocks fitted to the returns alone when volatility clusters,
  still below the nominal level.」但 be80ac5 已經刪掉那些量測數字，這句現在描述的內容不存在了。
- **C3. comparison 還留著被他修正的說法**：`difference_interval_outcome` 寫「A block size that is too long costs
  only some precision.」815a4a7 在 sharpe 把同一句改成「excessive block lengths can … produce unreliable or nearly
  degenerate intervals」。他的審閱標準會直接套到這裡。

benchmark.py 沒有發現類似問題。

## 任務 4：PR body

- 四份 body 只改 `verified at `main` c246355:` → `verified at `main` ad2fb75:`。測試數和任務 2 的結果相同，不用改。
- 全文在 `2026-11-09-round33-pr-bodies/pr206.md`～`pr209.md`，`*.orig.md` 是目前 GitHub 上的原文。
- **我沒有在 GitHub 上直接編輯 body**：
  - 第 29 輪起都是你自己更新 body。
  - 這一輪只授權 push，沒有授權寫入 PR。
  - 要我用 `gh pr edit` 代改的話，說一聲就好。
- **這三處敘述已經和分支現況不符，我沒有改**（你只要求改 verified-at 和測試數）：
  1. #207、#209 第一行和 #208 的 commit 清單寫「copied unchanged from `feat/stats-py314`」。分支現在多了 Kuan-Lun 的審閱 commit。
  2. #206 寫「After the split, two changes were made only on the split branches」。現在不只兩處。
  3. #208 寫「Unlike the other parts, this branch has three commits」。現在是 11 個。

## 沒做的事

- 沒有改或 revert 任何 Kuan-Lun 的 commit。
- 沒有 force push。
- 沒有開 PR、沒有留言、沒有編輯 PR body。
- 沒有跑 check-full。
- 沒有碰任何簡報。
