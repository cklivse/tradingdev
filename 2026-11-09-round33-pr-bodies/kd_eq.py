"""Recompute the four KD figures and compare them to the pins with ==."""
import sys
sys.path.insert(0, ".")
from tests.domain.statistics.kd_fixture import load_kd_fixture
from tradingdev.domain.statistics.breakeven import summarize_breakeven
from tradingdev.domain.statistics.periods import period_returns
from tradingdev.domain.statistics.sharpe import sharpe_ratio

kd = load_kd_fixture()
r = period_returns(kd.equity, kd.timestamps, "daily")
notional = summarize_breakeven(kd.trades, start=kd.timestamps[0], end=kd.timestamps[-1], capital=kd.run["init_cash"]).traded_notional
rate = float(kd.run["fees"]) + float(kd.run["slippage"])
got = {
    "days": len(r),
    "sharpe": sharpe_ratio(r.to_numpy(), periods_per_year=365.0),
    "notional": notional,
    "cost_share": notional * rate / abs(float(kd.equity[-1] - kd.equity[0])),
}
pins = {"days": 366, "sharpe": -7.565103143673017, "notional": 5014735.715506879, "cost_share": 0.863481526386825}
ok = True
for k in pins:
    eq = got[k] == pins[k]
    ok &= eq
    print(f"{k:<11} {pins[k]!r:<21} {got[k]!r:<21} {'EQUAL' if eq else 'DIFF'}")
sys.exit(0 if ok else 1)
