"""Pin the KD figures of demo_output/kd_inference.md on the versioned fixture.

The figures are deterministic, so they are pinned at rel 1e-9 to the values
the demo computed from the source pickle, and their displayed forms are
checked against the committed report.
"""

import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from tests.domain.statistics.kd_fixture import KDFixture, load_kd_fixture

from tradingdev.domain.statistics.breakeven import summarize_breakeven
from tradingdev.domain.statistics.periods import period_returns
from tradingdev.domain.statistics.sharpe import sharpe_ratio

_REPORT = Path(__file__).resolve().parents[3] / "demo_output" / "kd_inference.md"
_REL = 1e-9
_DAYS = 366
_SHARPE = -7.565103143673017
_TRADED_NOTIONAL = 5014735.715506879
_COST_SHARE = 0.863481526386825


@pytest.fixture(scope="module")
def kd() -> KDFixture:
    return load_kd_fixture()


def _daily_returns(kd: KDFixture) -> pd.Series:
    return period_returns(kd.equity, kd.timestamps, "daily")


def _traded_notional(kd: KDFixture) -> float:
    return summarize_breakeven(
        kd.trades,
        start=kd.timestamps[0],
        end=kd.timestamps[-1],
        capital=kd.run["init_cash"],
    ).traded_notional


def _cost_share(kd: KDFixture) -> float:
    cost = _traded_notional(kd) * (kd.run["fees"] + kd.run["slippage"])
    return cost / abs(float(kd.equity[-1] - kd.equity[0]))


def _report_value(label: str) -> str:
    match = re.search(
        rf"^\| {re.escape(label)} \| (.+?) \|$",
        _REPORT.read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    assert match is not None, f"{label!r} row missing from {_REPORT.name}"
    return match.group(1)


class TestResample:
    def test_hourly_equity_resamples_to_366_utc_days(self, kd: KDFixture) -> None:
        returns = _daily_returns(kd)

        assert len(kd.equity) == 8761
        assert len(returns) == _DAYS
        assert returns.index[0] == pd.Timestamp("2024-01-01", tz="UTC")
        assert returns.index[-1] == pd.Timestamp("2024-12-31", tz="UTC")


class TestPinnedFigures:
    def test_annualised_daily_sharpe(self, kd: KDFixture) -> None:
        returns = _daily_returns(kd).to_numpy()

        sharpe = sharpe_ratio(returns, periods_per_year=365.0)

        assert sharpe == pytest.approx(_SHARPE, rel=_REL)

    def test_traded_notional(self, kd: KDFixture) -> None:
        engine_volume = float(
            np.sum([t["size_quote"] + t["exit_notional"] for t in kd.trades])
        )

        assert _traded_notional(kd) == pytest.approx(_TRADED_NOTIONAL, rel=_REL)
        assert engine_volume == pytest.approx(_TRADED_NOTIONAL, rel=_REL)

    def test_cost_share_of_net_pnl(self, kd: KDFixture) -> None:
        assert _cost_share(kd) == pytest.approx(_COST_SHARE, rel=_REL)


class TestCommittedReport:
    def test_report_cites_the_fixture_source(self, kd: KDFixture) -> None:
        assert _report_value("Real days (UTC days with data)") == str(_DAYS)
        assert f"`{kd.run['source']['sha256']}`" in _REPORT.read_text(encoding="utf-8")

    def test_report_shows_the_pinned_figures(self, kd: KDFixture) -> None:
        sharpe = sharpe_ratio(_daily_returns(kd).to_numpy(), periods_per_year=365.0)
        assert sharpe is not None

        assert _report_value("Annualised Sharpe (daily)") == f"{sharpe:.2f}"
        assert (
            _report_value("Traded notional (entry + exit)")
            == f"{_traded_notional(kd):,.0f}"
        )
        assert _report_value("Cost / abs(net P&L)") == f"{_cost_share(kd):.1%}"
