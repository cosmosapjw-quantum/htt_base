"""PR-153 published-table JWST host-distance result tests."""
from __future__ import annotations

import csv
import math
from pathlib import Path

import pytest

from obsstat.jwst_distance_consistency import (
    JWSTDistanceError,
    build_distance_result,
    paired_consistency,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TABLE = REPO_ROOT / "dl_pipeline/data/jwst_host_distance_comparisons.csv"
AGGREGATES = REPO_ROOT / "dl_pipeline/data/jwst_published_aggregate_comparisons.csv"


def _rows() -> list[dict]:
    with TABLE.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(line for line in handle if not line.startswith("#")))


def _aggregate_rows() -> list[dict]:
    with AGGREGATES.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(line for line in handle if not line.startswith("#")))


def test_source_checked_tables_have_registered_unique_host_counts() -> None:
    result = build_distance_result(_rows(), _aggregate_rows())
    cchp = result["cchp_trgb_minus_jagb_consistency"]
    shoes = result["shoes_jwst_minus_hst_consistency"]
    assert cchp["n_unique_hosts"] == 7
    assert shoes["n_unique_hosts"] == 13
    assert cchp["method_a"] == "JAGB"
    assert shoes["method_a"] == "JWST"


def test_reproduces_published_scale_of_cchp_method_agreement() -> None:
    cchp = build_distance_result(
        _rows(), _aggregate_rows())["cchp_trgb_minus_jagb_consistency"]
    primary = cchp["primary_host_level"]
    # Published unweighted result is -0.008 +/- 0.018 mag (rounding and its
    # precise error convention); our transparent unique-host replay agrees.
    assert primary["mean_delta_mag"] == pytest.approx(-0.008142857143, abs=1e-12)
    assert primary["standard_error_mag"] == pytest.approx(
        0.018169084904268273, abs=1e-15)
    assert primary["two_sided_p_for_zero_mean"] > 0.4
    assert abs(primary["mean_fractional_distance_offset"]) < 0.01
    assert primary["covariance_status"] == "shared_anchor_covariance_unavailable"
    assert not primary["total_uncertainty"]


def test_shoes_host_table_is_consistent_with_zero_but_rejects_registered_shift() -> None:
    shoes = build_distance_result(
        _rows(), _aggregate_rows())["shoes_jwst_minus_hst_consistency"]
    primary = shoes["primary_host_level"]
    shift = shoes["registered_shift_comparison"]
    assert primary["mean_delta_mag"] == pytest.approx(-0.033846153846, abs=1e-10)
    assert primary["standard_error_mag"] == pytest.approx(
        0.026518944886058767, abs=1e-15)
    assert primary["two_sided_p_for_zero_mean"] > 0.1
    assert shift["comparison_shift_mag"] == pytest.approx(
        5.0 * math.log10(73.0 / 67.5))
    assert shift["one_sided_p_mean_at_least_comparison"] < 1e-5
    assert shift["n_host_deltas_below_comparison"] == 12


def test_expanded_published_aggregates_are_replayed_not_pooled() -> None:
    expanded = build_distance_result(
        _rows(), _aggregate_rows())["expanded_source_reported_aggregates"]
    assert expanded["n_registered_aggregates"] == 2
    assert not expanded["cross_sample_combination_performed"]
    by_name = {row["dataset"]: row for row in expanded["rows"]}
    li2024 = by_name["li2024_jwst_trgb_hst_cepheid"]
    li2025 = by_name["li2025_complete_trgb_hst_cepheid"]
    assert li2024["paired_object_count"] == 8
    assert li2024["parent_count_unit"] == "SN"
    assert li2024["paired_count_unit"] == "host"
    assert li2024["published_mean_delta_mag"] == pytest.approx(0.007)
    assert li2025["parent_sn_calibrator_count"] == 35
    assert li2025["paired_object_count"] == 20
    assert li2025["parent_count_unit"] == "SN"
    assert li2025["paired_count_unit"] == "object"
    assert li2025["published_mean_delta_mag"] == pytest.approx(-0.003)
    assert li2025["normal_reference_two_sided_p_for_zero"] > 0.8
    tiny_p = li2025["registered_shift_comparison"][
        "one_sided_p_mean_at_least_comparison"]
    assert tiny_p == pytest.approx(8.422603573854381e-17, rel=1e-12)
    assert 0.0 < tiny_p <= 1.0
    assert all(row["analysis_level"].endswith("not_host_level_reanalysis")
               for row in expanded["rows"])


def test_duplicate_hosts_fail_closed() -> None:
    rows = _rows()
    selected = [row for row in rows if row["dataset"] == "cchp_trgb_jagb"]
    with pytest.raises(JWSTDistanceError, match="duplicate host"):
        paired_consistency(selected + [dict(selected[0])],
                           dataset="cchp_trgb_jagb")


def test_aggregate_count_units_fail_closed() -> None:
    rows = _aggregate_rows()
    rows[0]["paired_count_unit"] = "SN"
    with pytest.raises(JWSTDistanceError, match="count/unit/source contract"):
        build_distance_result(_rows(), rows)
