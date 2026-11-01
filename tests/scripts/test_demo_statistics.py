"""Tests for how scripts/demo_statistics.py chooses and cites its KD input."""

import hashlib
import importlib.util
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from types import ModuleType

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "demo_statistics.py"


@pytest.fixture(scope="module")
def demo() -> ModuleType:
    spec = importlib.util.spec_from_file_location("demo_statistics", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pickle(path: Path, payload: bytes = b"kd backtest") -> str:
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


class TestPinnedDefault:
    def test_reads_the_pinned_file_when_its_hash_matches(
        self, demo: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pinned = tmp_path / "pinned.pkl"
        digest = _pickle(pinned)
        monkeypatch.setattr(demo, "KD_SOURCE", pinned)
        monkeypatch.setattr(demo, "KD_SOURCE_SHA256", digest)

        assert demo.resolve_kd_source(None) == (pinned, digest)

    def test_newer_files_beside_it_are_never_picked(
        self, demo: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pinned = tmp_path / "pinned.pkl"
        digest = _pickle(pinned)
        _pickle(tmp_path / "newer.pkl", b"another backtest")
        monkeypatch.setattr(demo, "KD_SOURCE", pinned)
        monkeypatch.setattr(demo, "KD_SOURCE_SHA256", digest)

        assert demo.resolve_kd_source(None)[0] == pinned

    def test_missing_pinned_file_stops(
        self, demo: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(demo, "KD_SOURCE", tmp_path / "absent.pkl")

        with pytest.raises(SystemExit, match="is missing"):
            demo.resolve_kd_source(None)

    def test_changed_pinned_file_stops(
        self, demo: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pinned = tmp_path / "pinned.pkl"
        _pickle(pinned, b"rewritten")
        monkeypatch.setattr(demo, "KD_SOURCE", pinned)
        monkeypatch.setattr(demo, "KD_SOURCE_SHA256", "0" * 64)

        with pytest.raises(SystemExit, match="expected"):
            demo.resolve_kd_source(None)

    def test_pinned_constant_matches_the_committed_report(
        self, demo: ModuleType
    ) -> None:
        report = _SCRIPT.parents[1] / "demo_output" / "kd_inference.md"

        assert f"`{demo.KD_SOURCE_SHA256}`" in report.read_text(encoding="utf-8")


class TestExplicitInput:
    def test_explicit_file_is_used_with_its_own_hash(
        self, demo: ModuleType, tmp_path: Path
    ) -> None:
        other = tmp_path / "other.pkl"
        digest = _pickle(other, b"explicit backtest")

        assert demo.resolve_kd_source(other) == (other.resolve(), digest)

    def test_relative_path_is_resolved(
        self, demo: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _pickle(tmp_path / "other.pkl")
        monkeypatch.chdir(tmp_path)

        source, _ = demo.resolve_kd_source(Path("other.pkl"))

        assert source == (tmp_path / "other.pkl").resolve()

    def test_missing_explicit_file_stops(
        self, demo: ModuleType, tmp_path: Path
    ) -> None:
        with pytest.raises(SystemExit, match="does not exist"):
            demo.resolve_kd_source(tmp_path / "absent.pkl")


class TestDisplayedPath:
    def test_repository_path_is_shown_relative(self, demo: ModuleType) -> None:
        assert demo.display_path(demo.KD_SOURCE) == (
            "workspace/data/processed/cache/cd03bf19459b48af.pkl"
        )

    def test_outside_path_shows_only_the_file_name(
        self, demo: ModuleType, tmp_path: Path
    ) -> None:
        assert demo.display_path(tmp_path / "private" / "run.pkl") == "run.pkl"
