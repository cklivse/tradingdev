"""Record per test whether any StrategyService public method returned runtime_unavailable."""
import functools, json, os, re
import pytest
MARK = re.compile(r"runtime_unavailable|tradingdev-strategy-runtime|Strategy runtime image")
_hits = set()
def _seen(v, d=0):
    if d > 5: return False
    if isinstance(v, str): return bool(MARK.search(v))
    if isinstance(v, dict): return any(_seen(x, d + 1) for x in v.values())
    if isinstance(v, (list, tuple)): return any(_seen(x, d + 1) for x in v[:50])
    if hasattr(v, "model_dump"):
        try: return _seen(v.model_dump(), d + 1)
        except Exception: return False
    return False
def pytest_configure(config):
    from tradingdev.app import strategy_service as m
    cls = m.StrategyService
    for name in [n for n in vars(cls) if not n.startswith("_") and callable(getattr(cls, n))]:
        orig = getattr(cls, name)
        @functools.wraps(orig)
        def w(*a, __o=orig, **k):
            try:
                r = __o(*a, **k)
            except Exception as e:
                if MARK.search(str(e)): _hits.add(os.environ.get("PYTEST_CURRENT_TEST", "").split(" ")[0])
                raise
            if _seen(r): _hits.add(os.environ.get("PYTEST_CURRENT_TEST", "").split(" ")[0])
            return r
        setattr(cls, name, w)
@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    rep = yield
    if rep.failed:
        hit = item.nodeid in _hits or bool(MARK.search(str(rep.longrepr)))
        with open(os.environ["DIAG_OUT"], "a") as f:
            f.write(json.dumps({"node": item.nodeid, "when": rep.when, "cause": "runtime_unavailable" if hit else "OTHER"}) + "\n")
    return rep
