"""Tests for scripts/validate_run.py on the versioned KD fixture."""

import importlib.util
import pickle
import subprocess
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest
from tests.domain.statistics.kd_fixture import KDFixture, load_kd_fixture

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "validate_run.py"


@pytest.fixture(scope="module")
def validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("validate_run", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def kd() -> KDFixture:
    return load_kd_fixture()


def _pipeline(kd: KDFixture, **metric_overrides: Any) -> SimpleNamespace:
    """A pipeline result shaped like the engine's, built from the fixture."""
    metrics = dict(kd.run["engine_metrics"]) | metric_overrides
    return SimpleNamespace(
        mode="simple",
        backtest_result=SimpleNamespace(
            metrics=metrics,
            equity_curve=kd.equity,
            trades=kd.trades,
            timestamps=kd.timestamps,
            init_cash=kd.run["init_cash"],
            mode=kd.run["mode"],
        ),
        config_snapshot={
            "backtest": {
                "fees": kd.run["fees"],
                "slippage": kd.run["slippage"],
                "init_cash": kd.run["init_cash"],
            }
        },
    )


def _status(validator: ModuleType, prefix: str) -> str:
    matches = [s for s, name, _ in validator.results if name.startswith(prefix)]
    assert len(matches) == 1, f"expected one {prefix} check, got {matches}"
    return str(matches[0])


class TestEngineOutput:
    def test_every_check_passes(self, validator: ModuleType, kd: KDFixture) -> None:
        exit_code = validator.validate(_pipeline(kd))

        assert exit_code == 0
        assert len(validator.results) == 24
        failing = [(s, n, d) for s, n, d in validator.results if s != "PASS"]
        assert failing == []

    def test_main_reads_a_pickled_result(
        self, validator: ModuleType, kd: KDFixture, tmp_path: Path
    ) -> None:
        path = tmp_path / "pipeline_result.pkl"
        path.write_bytes(pickle.dumps(_pipeline(kd)))

        assert validator.main(str(path)) == 0
        assert len(validator.results) == 24

    def test_repeated_runs_do_not_accumulate_checks(
        self, validator: ModuleType, kd: KDFixture
    ) -> None:
        validator.validate(_pipeline(kd))
        validator.validate(_pipeline(kd))

        assert len(validator.results) == 24


class TestMaxDrawdownSign:
    @pytest.mark.parametrize("magnitude", [0.0, 0.25, 1.5])
    def test_nonnegative_magnitude_passes_v3(
        self, validator: ModuleType, kd: KDFixture, magnitude: float
    ) -> None:
        validator.validate(_pipeline(kd, max_drawdown=magnitude))

        assert _status(validator, "V3") == "PASS"

    def test_engine_value_passes_v3(self, validator: ModuleType, kd: KDFixture) -> None:
        assert kd.run["engine_metrics"]["max_drawdown"] > 0

        validator.validate(_pipeline(kd))

        assert _status(validator, "V3") == "PASS"

    def test_negative_value_of_the_old_convention_fails_v3(
        self, validator: ModuleType, kd: KDFixture
    ) -> None:
        negative = -kd.run["engine_metrics"]["max_drawdown"]

        assert validator.validate(_pipeline(kd, max_drawdown=negative)) == 1
        assert _status(validator, "V3") == "FAIL"


class TestCostBreakdown:
    def test_cost_share_counts_each_leg_once(
        self,
        validator: ModuleType,
        kd: KDFixture,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        validator.validate(_pipeline(kd))

        out = capsys.readouterr().out
        assert "成本占比 86%" in out
        assert "173%" not in out

    def test_cost_ignores_the_total_volume_metric(
        self,
        validator: ModuleType,
        kd: KDFixture,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        doubled = 2 * kd.run["engine_metrics"]["total_volume"]

        validator.validate(_pipeline(kd, total_volume=doubled))

        assert "成本占比 86%" in capsys.readouterr().out


def test_cli_requires_an_explicit_path() -> None:
    completed = subprocess.run(
        [sys.executable, str(_SCRIPT)],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )

    assert completed.returncode == 2
    assert "validate_run.py path/to/pipeline_result.pkl" in completed.stdout
