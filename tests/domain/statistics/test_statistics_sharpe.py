"""Tests for the Sharpe ratio, its bootstrap interval, and PSR."""

import math
from statistics import NormalDist

import numpy as np
import numpy.typing as npt
import pytest
from arch.bootstrap import IIDBootstrap

from tradingdev.domain.statistics.sharpe import (
    MIN_BOOTSTRAP_OBSERVATIONS,
    probabilistic_sharpe_ratio,
    sharpe_confidence_interval,
    sharpe_ratio,
)

_DAILY = 365.0


def _ar1(n: int, phi: float, seed: int) -> npt.NDArray[np.float64]:
    rng = np.random.default_rng(seed)
    shocks = rng.normal(0.0, 0.01, n)
    values = np.empty(n)
    values[0] = shocks[0]
    for t in range(1, n):
        values[t] = phi * values[t - 1] + shocks[t]
    return values + 0.0005


def _annual_sharpe(values: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    return np.array([np.mean(values) / np.std(values, ddof=1) * math.sqrt(_DAILY)])


class TestSharpeRatio:
    def test_known_value(self) -> None:
        returns = [0.01, -0.01, 0.02, 0.0]
        expected = np.mean(returns) / np.std(returns, ddof=1) * math.sqrt(_DAILY)

        assert sharpe_ratio(returns, periods_per_year=_DAILY) == pytest.approx(expected)

    def test_accepts_numpy_arrays(self) -> None:
        returns = np.array([0.01, -0.01, 0.02, 0.0])

        assert sharpe_ratio(returns, periods_per_year=252.0) == pytest.approx(
            sharpe_ratio(list(returns), periods_per_year=252.0)
        )


class TestProbabilisticSharpeRatio:
    def test_benchmark_equal_to_estimate_gives_one_half(self) -> None:
        returns = np.random.default_rng(1).normal(0.001, 0.01, 500)
        per_period = float(np.mean(returns) / np.std(returns, ddof=1))

        psr = probabilistic_sharpe_ratio(returns, benchmark_sr=per_period)
        assert psr == pytest.approx(0.5)

    def test_matches_normal_closed_form_on_iid_normal_returns(self) -> None:
        returns = np.random.default_rng(2).normal(0.0005, 0.01, 2_000)
        sr = float(np.mean(returns) / np.std(returns, ddof=1))
        expected = NormalDist().cdf(
            sr * math.sqrt(len(returns) - 1) / math.sqrt(1.0 + sr**2 / 2.0)
        )

        psr = probabilistic_sharpe_ratio(returns)
        assert psr == pytest.approx(expected, abs=0.02)

    def test_strong_edges_are_near_certain(self) -> None:
        rng = np.random.default_rng(3)
        winning = rng.normal(0.002, 0.01, 1_000)

        assert probabilistic_sharpe_ratio(winning) == pytest.approx(1.0, abs=1e-3)
        assert probabilistic_sharpe_ratio(-winning) == pytest.approx(0.0, abs=1e-3)

    def test_is_calibrated_under_a_zero_true_sharpe(self) -> None:
        rng = np.random.default_rng(4)
        psrs = [
            probabilistic_sharpe_ratio(rng.normal(0.0, 0.01, 250)) for _ in range(800)
        ]
        values = np.array([p for p in psrs if p is not None])

        assert values.size == 800
        assert np.mean(values > 0.95) == pytest.approx(0.05, abs=0.025)
        assert np.mean(values) == pytest.approx(0.5, abs=0.05)

    def test_decreases_with_benchmark(self) -> None:
        returns = np.random.default_rng(5).normal(0.001, 0.01, 500)
        psrs = [
            probabilistic_sharpe_ratio(returns, benchmark_sr=b)
            for b in (-0.05, 0.0, 0.05, 0.1)
        ]

        assert all(p is not None for p in psrs)
        assert psrs == sorted(psrs, reverse=True)  # type: ignore[type-var]

    def test_negative_skew_lowers_probability(self) -> None:
        noise = np.random.default_rng(6).exponential(0.01, 1_000)
        noise -= noise.mean()
        right_skewed = 0.001 + noise
        left_skewed = 0.001 - noise

        right = probabilistic_sharpe_ratio(right_skewed)
        left = probabilistic_sharpe_ratio(left_skewed)
        assert right is not None
        assert left is not None
        assert left < right


class TestConfidenceInterval:
    def test_autocorrelated_returns_widen_the_interval(self) -> None:
        returns = _ar1(1_000, 0.6, seed=7)
        interval = sharpe_confidence_interval(returns, periods_per_year=_DAILY, seed=11)
        assert interval is not None

        iid = IIDBootstrap(returns, seed=np.random.default_rng(11))
        draws = iid.apply(_annual_sharpe, 1_000)[:, 0]
        iid_lower, iid_upper = np.quantile(draws, [0.025, 0.975])

        assert interval.block_size > 1
        assert interval.upper - interval.lower > 1.5 * (iid_upper - iid_lower)
        assert interval.lower < interval.sharpe < interval.upper

    def test_interval_fields(self) -> None:
        returns = np.random.default_rng(8).normal(0.001, 0.01, 400)
        interval = sharpe_confidence_interval(
            returns, periods_per_year=_DAILY, confidence=0.9, reps=200, seed=1
        )

        assert interval is not None
        assert interval.sharpe == pytest.approx(
            sharpe_ratio(returns, periods_per_year=_DAILY)
        )
        assert interval.confidence == pytest.approx(0.9)
        assert interval.reps == 200
        assert interval.valid_reps == 200
        assert interval.block_size >= 1
        assert interval.lower < interval.upper

    def test_seed_makes_the_interval_reproducible(self) -> None:
        returns = _ar1(300, 0.3, seed=9)
        first = sharpe_confidence_interval(returns, periods_per_year=_DAILY, seed=5)
        second = sharpe_confidence_interval(returns, periods_per_year=_DAILY, seed=5)

        assert first == second


class TestDegenerateReturns:
    @pytest.mark.parametrize("returns", [[], [0.01]], ids=["empty", "single"])
    def test_too_few_returns(self, returns: list[float]) -> None:
        assert sharpe_ratio(returns, periods_per_year=_DAILY) is None
        assert probabilistic_sharpe_ratio(returns) is None
        assert sharpe_confidence_interval(returns, periods_per_year=_DAILY) is None

    def test_too_few_returns_to_bootstrap(self) -> None:
        returns = np.random.default_rng(10).normal(
            0.001, 0.01, MIN_BOOTSTRAP_OBSERVATIONS - 1
        )

        assert sharpe_ratio(returns, periods_per_year=_DAILY) is not None
        assert probabilistic_sharpe_ratio(returns) is not None
        assert sharpe_confidence_interval(returns, periods_per_year=_DAILY) is None

    @pytest.mark.parametrize("value", [0.0, 0.1, -0.003], ids=["zero", "pos", "neg"])
    def test_constant_returns(self, value: float) -> None:
        returns = [value] * 100

        assert sharpe_ratio(returns, periods_per_year=_DAILY) is None
        assert probabilistic_sharpe_ratio(returns) is None
        assert sharpe_confidence_interval(returns, periods_per_year=_DAILY) is None


class TestValidation:
    @pytest.mark.parametrize("periods_per_year", [0.0, -1.0, math.inf, math.nan])
    def test_rejects_invalid_periods_per_year(self, periods_per_year: float) -> None:
        with pytest.raises(ValueError, match="periods_per_year"):
            sharpe_ratio([0.01, 0.02], periods_per_year=periods_per_year)

    def test_rejects_non_finite_returns(self) -> None:
        with pytest.raises(ValueError, match="finite"):
            probabilistic_sharpe_ratio([0.01, math.nan, 0.02])

    def test_rejects_non_finite_benchmark(self) -> None:
        with pytest.raises(ValueError, match="benchmark_sr"):
            probabilistic_sharpe_ratio([0.01, 0.02], benchmark_sr=math.inf)

    @pytest.mark.parametrize(
        ("kwargs", "match"),
        [
            ({"confidence": 0.0}, "confidence"),
            ({"confidence": 1.0}, "confidence"),
            ({"reps": 0}, "reps"),
            ({"reps": True}, "reps"),
        ],
    )
    def test_rejects_invalid_bootstrap_settings(
        self, kwargs: dict[str, object], match: str
    ) -> None:
        with pytest.raises(ValueError, match=match):
            sharpe_confidence_interval(
                [0.01, 0.02],
                periods_per_year=_DAILY,
                **kwargs,  # type: ignore[arg-type]
            )
