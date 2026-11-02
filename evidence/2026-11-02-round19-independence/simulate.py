"""Round 19 evidence: what serial dependence does to PSR, and the SE-ratio check.

Run from the code checkout (feat/stats-py314), so the project's functions are
the ones measured:

    cd /workspaces/tradingdev
    uv run python <this file> > <output>

Every figure is drawn from fixed seeds (SEED below), so a rerun on the same
commit and the same NumPy / arch versions reproduces the output exactly.

Sections:
1. PSR false-positive rate and true SD(SR) / formula SE, per scenario.
   PSR is the project's ``probabilistic_sharpe_ratio``, called per sample.
2. ddof=0 versus ddof=1 for the per-period Sharpe inside PSR, and for the
   DSR trial dispersion.
3. SE-ratio diagnostic: stationary-bootstrap SE of the per-period Sharpe over
   the formula SE, block length from ``sharpe._returns_block_size``.
4. The same diagnostic on the KD(14,3,3) BTC/USDT 1h 2024 fixture, daily
   returns, plus the PSR denominator terms.
"""

from __future__ import annotations

import math
import platform
import subprocess
import sys
from pathlib import Path
from statistics import NormalDist

import arch
import numpy as np
import pandas as pd
from arch.bootstrap import StationaryBootstrap

from tradingdev.domain.statistics.periods import period_returns
from tradingdev.domain.statistics.sharpe import (
    _period_sharpe,
    _resample_sharpe,
    _returns_block_size,
    probabilistic_sharpe_ratio,
)

SEED = 20261102
N_OBS = 365
TRUE_SR = 0.05
PSR_REPS = 20_000
DIAG_SERIES = 300
DIAG_RESAMPLES = 1_000
MIN_BLOCKS = 20
KD_SEEDS = range(10)
BURN_IN = 500

FIXTURE = (
    Path.cwd()
    / "tests/domain/statistics/fixtures/kd_btcusdt_1h_2024/equity.parquet"
)


def iid_t5(rng: np.random.Generator, n: int) -> np.ndarray:
    # Student t with 5 degrees of freedom, scaled to unit variance.
    return TRUE_SR + rng.standard_t(5, n) / math.sqrt(5.0 / 3.0)


def ar1(rho: float):
    def draw(rng: np.random.Generator, n: int) -> np.ndarray:
        # Normal innovations scaled so the stationary variance is one.
        shocks = rng.standard_normal(n + BURN_IN) * math.sqrt(1.0 - rho**2)
        noise = np.empty(n + BURN_IN)
        noise[0] = rng.standard_normal()
        for t in range(1, n + BURN_IN):
            noise[t] = rho * noise[t - 1] + shocks[t]
        return TRUE_SR + noise[BURN_IN:]

    return draw


def garch(alpha: float, beta: float):
    omega = 1.0 - alpha - beta  # unconditional variance one

    def draw(rng: np.random.Generator, n: int) -> np.ndarray:
        z = rng.standard_normal(n + BURN_IN)
        eps = np.empty(n + BURN_IN)
        var = 1.0
        for t in range(n + BURN_IN):
            eps[t] = math.sqrt(var) * z[t]
            var = omega + alpha * eps[t] ** 2 + beta * var
        return TRUE_SR + eps[BURN_IN:]

    return draw


SCENARIOS = {
    "iid t(5)": iid_t5,
    "AR(1) 0.2": ar1(0.2),
    "AR(1) 0.4": ar1(0.4),
    "AR(1) -0.2": ar1(-0.2),
    "GARCH(0.10,0.85)": garch(0.10, 0.85),
}


def moments(values: np.ndarray) -> tuple[float, float, float]:
    """Per-period Sharpe (ddof=1), skewness and kurtosis as the project takes them."""
    sharpe = _period_sharpe(values)
    assert sharpe is not None
    dev = values - values.mean()
    var = float(np.mean(dev**2))
    g3 = float(np.mean(dev**3)) / var**1.5
    g4 = float(np.mean(dev**4)) / var**2
    return sharpe, g3, g4


def spread(sharpe: float, g3: float, g4: float) -> float:
    return 1.0 - g3 * sharpe + (g4 - 1.0) / 4.0 * sharpe**2


def formula_se(values: np.ndarray) -> float:
    sharpe, g3, g4 = moments(values)
    return math.sqrt(spread(sharpe, g3, g4) / (values.size - 1))


def bootstrap_se(values: np.ndarray, block: int, seed: int) -> float:
    boot = StationaryBootstrap(block, values, seed=np.random.default_rng(seed))
    draws = boot.apply(_resample_sharpe, DIAG_RESAMPLES)[:, 0]
    draws = draws[np.isfinite(draws)]
    return float(draws.std(ddof=1))


def section_psr(seeds: dict[str, tuple[np.random.SeedSequence, ...]]) -> dict[str, float]:
    print("## 1. PSR under H0 (true per-period SR = benchmark = 0.05)")
    print(f"n = {N_OBS}, samples per scenario = {PSR_REPS}")
    print()
    print("| scenario | P(PSR>0.95) | 95% MC band | SD(SR) | mean formula SE | ratio |")
    print("| --- | --- | --- | --- | --- | --- |")
    normal = NormalDist()
    true_ratio: dict[str, float] = {}
    ddof_diffs: list[np.ndarray] = []
    max_reimpl_gap = 0.0
    for name, draw in SCENARIOS.items():
        rng = np.random.default_rng(seeds[name][0])
        psr = np.empty(PSR_REPS)
        sr = np.empty(PSR_REPS)
        se = np.empty(PSR_REPS)
        diff = np.empty(PSR_REPS)
        for i in range(PSR_REPS):
            x = draw(rng, N_OBS)
            value = probabilistic_sharpe_ratio(x, benchmark_sr=TRUE_SR)
            assert value is not None
            psr[i] = value
            s1, g3, g4 = moments(x)
            sr[i] = s1
            se[i] = math.sqrt(spread(s1, g3, g4) / (N_OBS - 1))
            # Re-derive PSR from the same SE to confirm the SE is the one PSR uses.
            mine = normal.cdf((s1 - TRUE_SR) / se[i])
            max_reimpl_gap = max(max_reimpl_gap, abs(mine - value))
            # Same PSR with the population (ddof=0) Sharpe.
            s0 = s1 * math.sqrt((N_OBS - 1) / N_OBS)
            psr0 = normal.cdf(
                (s0 - TRUE_SR) * math.sqrt(N_OBS - 1) / math.sqrt(spread(s0, g3, g4))
            )
            diff[i] = abs(psr0 - value)
        rate = float(np.mean(psr > 0.95))
        band = 1.96 * math.sqrt(rate * (1 - rate) / PSR_REPS)
        sd = float(sr.std(ddof=1))
        ratio = sd / float(se.mean())
        true_ratio[name] = ratio
        ddof_diffs.append(diff)
        print(
            f"| {name} | {rate:.2%} | ±{band:.2%} | {sd:.4f} | {se.mean():.4f} "
            f"| {ratio:.3f} |"
        )
    print()
    print(f"Max |PSR from formula SE - probabilistic_sharpe_ratio| = {max_reimpl_gap:.2e}")
    print()
    print("## 2. ddof")
    all_diff = np.concatenate(ddof_diffs)
    print(
        f"|PSR(ddof=0 SR) - PSR(ddof=1 SR)| over all {all_diff.size} samples: "
        f"mean {all_diff.mean():.5f}, max {all_diff.max():.5f}"
    )
    iid = ddof_diffs[0]
    print(f"iid t(5) only: mean {iid.mean():.5f}, max {iid.max():.5f}")
    trials = np.array([0.4, 1.1, -0.3])
    factor = trials.std(ddof=0) / trials.std(ddof=1)
    print(
        f"DSR hurdle, N=3: std(ddof=0)/std(ddof=1) = {factor:.4f} "
        f"(sqrt(2/3) = {math.sqrt(2 / 3):.4f}, {1 - factor:.1%} lower)"
    )
    print()
    return true_ratio


def section_diagnostic(
    seeds: dict[str, tuple[np.random.SeedSequence, ...]], true_ratio: dict[str, float]
) -> None:
    print("## 3. SE-ratio diagnostic (bootstrap SE / formula SE)")
    print(
        f"n = {N_OBS}, series per scenario = {DIAG_SERIES}, "
        f"resamples = {DIAG_RESAMPLES}, block = _returns_block_size"
    )
    print()
    print("| scenario | true ratio | p10 | median | p90 | share n/L<20 | median L |")
    print("| --- | --- | --- | --- | --- | --- | --- |")
    for name, draw in SCENARIOS.items():
        child = seeds[name][1]
        rng = np.random.default_rng(child)
        boot_seeds = child.generate_state(DIAG_SERIES)
        ratios = np.empty(DIAG_SERIES)
        blocks = np.empty(DIAG_SERIES, dtype=int)
        for i in range(DIAG_SERIES):
            x = draw(rng, N_OBS)
            block = _returns_block_size(x[:, np.newaxis])
            blocks[i] = block
            ratios[i] = bootstrap_se(x, block, int(boot_seeds[i])) / formula_se(x)
        p10, p50, p90 = np.quantile(ratios, [0.1, 0.5, 0.9])
        short = float(np.mean(N_OBS / blocks < MIN_BLOCKS))
        print(
            f"| {name} | {true_ratio[name]:.2f} | {p10:.2f} | {p50:.2f} | {p90:.2f} "
            f"| {short:.0%} | {int(np.median(blocks))} |"
        )
        # How much of the excess over one the median recovers.
        if abs(true_ratio[name] - 1) > 0.05:
            print(
                f"|  ↳ median captures {(p50 - 1) / (true_ratio[name] - 1):.0%} "
                "of (true - 1) | | | | | | |"
            )
    print()


def section_kd() -> None:
    print("## 4. KD(14,3,3) BTC/USDT 1h 2024 fixture, daily returns")
    bars = pd.read_parquet(FIXTURE)
    returns = period_returns(
        bars["equity"].to_numpy(dtype=np.float64),
        pd.DatetimeIndex(bars["timestamp"]),
        "daily",
    ).to_numpy(dtype=np.float64)
    n = returns.size
    sharpe, g3, g4 = moments(returns)
    skew_term = -g3 * sharpe
    kurt_term = (g4 - 1.0) / 4.0 * sharpe**2
    total = spread(sharpe, g3, g4)
    block = _returns_block_size(returns[:, np.newaxis])
    print(f"n = {n}, L = {block}, n/L = {n / block:.0f}")
    print(f"per-period SR = {sharpe:.4f}, g3 = {g3:.3f}, g4 = {g4:.3f}")
    print(
        f"PSR denominator 1 - g3*SR + (g4-1)/4*SR^2 = 1 + ({skew_term:.3f}) "
        f"+ {kurt_term:.3f} = {total:.3f}"
    )
    print(
        f"  kurtosis term / leading 1 = {kurt_term:.0%}; "
        f"|skew term| / leading 1 = {abs(skew_term):.0%}; "
        f"higher-moment terms shift the denominator by {total - 1:+.0%}"
    )
    normal_spread = 1.0 + sharpe**2 / 2.0
    print(f"  (normal returns would give 1 + SR^2/2 = {normal_spread:.3f})")
    ratios = [
        bootstrap_se(returns, block, seed) / formula_se(returns) for seed in KD_SEEDS
    ]
    print(
        f"SE ratio over bootstrap seeds {list(KD_SEEDS)}: "
        + ", ".join(f"{r:.3f}" for r in ratios)
        + f"; range {min(ratios):.3f}-{max(ratios):.3f}"
    )
    print()


def main() -> None:
    commit = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    print("# Round 19 independence-assumption simulation")
    print()
    print(
        f"seed {SEED}; code {commit}; Python {platform.python_version()}; "
        f"NumPy {np.__version__}; arch {arch.__version__}; pandas {pd.__version__}"
    )
    print(
        "Scenarios: unit marginal variance plus mean 0.05; t(5) iid; AR(1) and "
        f"GARCH(1,1) with normal innovations, {BURN_IN} burn-in periods."
    )
    print()
    root = np.random.SeedSequence(SEED)
    # Each scenario gets one stream for section 1 and one for section 3.
    seeds = {
        name: tuple(seq.spawn(2))
        for name, seq in zip(SCENARIOS, root.spawn(len(SCENARIOS)), strict=True)
    }
    true_ratio = section_psr(seeds)
    section_diagnostic(seeds, true_ratio)
    section_kd()
    sys.stdout.flush()


if __name__ == "__main__":
    main()
