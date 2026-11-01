"""The committed demo_output/kd_inference.md shows the fixture's pinned figures.

Moved from tests/domain/statistics/test_statistics_kd_fixture.py, which pins
the figures themselves; the demo report lives only on this branch.
"""

import re
from pathlib import Path

import pytest
from tests.domain.statistics.kd_fixture import KDFixture, load_kd_fixture

from tradingdev.domain.statistics.breakeven import summarize_breakeven
from tradingdev.domain.statistics.periods import period_returns
from tradingdev.domain.statistics.sharpe import sharpe_ratio

_REPORT = Path(__file__).resolve().parents[2] / "demo_output" / "kd_inference.md"
_DAYS = 366


@pytest.fixture(scope="module")
def kd() -> KDFixture:
    return load_kd_fixture()


def _traded_notional(kd: KDFixture) -> float:
    return summarize_breakeven(
        kd.trades,
        start=kd.timestamps[0],
        end=kd.timestamps[-1],
        capital=kd.run["init_cash"],
    ).traded_notional


def _cost_share(kd: KDFixture) -> float:
    rate = float(kd.run["fees"]) + float(kd.run["slippage"])
    return _traded_notional(kd) * rate / abs(float(kd.equity[-1] - kd.equity[0]))


def _report_value(label: str) -> str:
    match = re.search(
        rf"^\| {re.escape(label)} \| (.+?) \|$",
        _REPORT.read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    assert match is not None, f"{label!r} row missing from {_REPORT.name}"
    return match.group(1)


class TestCommittedReport:
    def test_report_cites_the_fixture_source(self, kd: KDFixture) -> None:
        assert _report_value("Real days (UTC days with data)") == str(_DAYS)
        assert f"`{kd.run['source']['sha256']}`" in _REPORT.read_text(encoding="utf-8")

    def test_report_shows_the_pinned_figures(self, kd: KDFixture) -> None:
        returns = period_returns(kd.equity, kd.timestamps, "daily").to_numpy()
        sharpe = sharpe_ratio(returns, periods_per_year=365.0)
        assert sharpe is not None

        assert _report_value("Annualised Sharpe (daily)") == f"{sharpe:.2f}"
        assert (
            _report_value("Traded notional (entry + exit)")
            == f"{_traded_notional(kd):,.0f}"
        )
        assert _report_value("Cost / abs(net P&L)") == f"{_cost_share(kd):.1%}"
