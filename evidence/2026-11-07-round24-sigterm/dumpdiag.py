"""Record, per failed test, whether any frame local or the error text shows runtime_unavailable."""
import json, os, re
import pytest
MARK = re.compile(r"runtime_unavailable|tradingdev-strategy-runtime|Strategy runtime image")
def _seen(value, depth=0):
    if depth > 4: return False
    if isinstance(value, str): return bool(MARK.search(value))
    if isinstance(value, dict): return any(_seen(v, depth + 1) for v in value.values())
    if isinstance(value, (list, tuple)): return any(_seen(v, depth + 1) for v in value[:50])
    return False
@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    rep = yield
    if rep.failed:
        hit = bool(MARK.search(str(rep.longrepr)))
        tb = call.excinfo.tb if call.excinfo else None
        while tb and not hit:
            hit = any(_seen(v) for v in tb.tb_frame.f_locals.values()); tb = tb.tb_next
        with open(os.environ["DIAG_OUT"], "a") as f:
            f.write(json.dumps({"node": item.nodeid, "when": rep.when,
                                "cause": "runtime_unavailable" if hit else "OTHER"}) + "\n")
    return rep
