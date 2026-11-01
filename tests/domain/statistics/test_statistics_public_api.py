"""The package's declared entry points match the public API document."""

import re
from pathlib import Path

import tradingdev.domain.statistics as statistics

_DOC = Path(__file__).resolve().parents[3] / "docs" / "statistics_public_api.md"
_INTERNAL = ("to_utc_index", "equity_series", "has_positive_equity")


def test_every_declared_name_resolves() -> None:
    missing = [name for name in statistics.__all__ if not hasattr(statistics, name)]

    assert missing == []
    assert len(statistics.__all__) == len(set(statistics.__all__))


def test_document_names_every_declared_entry_point() -> None:
    documented = set(re.findall(r"`([A-Za-z_][A-Za-z0-9_]*)`", _DOC.read_text()))

    assert sorted(set(statistics.__all__) - documented) == []


def test_shared_helpers_stay_internal() -> None:
    assert not set(_INTERNAL) & set(statistics.__all__)
