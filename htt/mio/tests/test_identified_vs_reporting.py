"""Tests for the active identified/reporting split registry."""
from __future__ import annotations

import pytest

from mio.reporting.identified_vs_reporting import (
    IdentifiedVsReportingSplitter,
    QuantityType,
    classify_quantity,
    enforce_identified_only,
    split_posterior_report,
)


def _report() -> dict[str, dict]:
    return {
        "beta": {"median": 0.0012},
        "x": {"median": 0.15},
        "F": {"median": 0.45},
        "delta_H": {"median": 2.3},
    }


def test_classify_quantity_exposes_canonical_types():
    assert classify_quantity("beta").quantity_type == QuantityType.IDENTIFIED
    assert classify_quantity("F").quantity_type == QuantityType.REPORTING


def test_split_posterior_report_partitions_identified_and_reporting():
    split = split_posterior_report(_report())
    assert set(split["identified"]) == {"beta"}
    assert set(split["reporting"]) == {"x", "F", "delta_H"}
    assert split["reporting"]["F"]["_classification"] == "reporting"


def test_enforce_identified_only_strips_reporting_quantities():
    out = enforce_identified_only(_report())
    assert out == {"beta": {"median": 0.0012, "_classification": "identified", "_warning": ""}}


def test_splitter_audits_access_patterns():
    splitter = IdentifiedVsReportingSplitter()
    report = _report()
    splitter.get_identified("beta", report)
    splitter.get_reporting("F", report)
    audit = splitter.audit()
    assert audit["identified_accessed"] == ["beta"]
    assert audit["reporting_accessed"] == ["F"]
    assert audit["leakage"] == []


def test_splitter_rejects_reporting_quantity_in_identified_path():
    splitter = IdentifiedVsReportingSplitter()
    with pytest.raises(ValueError, match="not identified"):
        splitter.get_identified("F", _report())
