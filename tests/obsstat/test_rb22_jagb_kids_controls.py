import csv
import importlib.util
import io
import zipfile
from pathlib import Path

import numpy as np
import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "run_rb22_jagb_kids_controls.py"
spec = importlib.util.spec_from_file_location("rb22_controls", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)


def test_parse_and_summarize_two_bin_nz():
    starts, values = module.parse_nz_table("# binstart, density\n0 1\n1 3\n")
    summary = module.summarize_nz(starts, values)
    assert summary["normalized_bin_mass_sum"] == pytest.approx(1.0)
    assert summary["mean_z"] == pytest.approx(1.25)
    assert summary["quantiles"]["0.5"] == pytest.approx(4.0 / 3.0)


def test_nz_parser_rejects_negative_nonuniform_and_nonfinite():
    with pytest.raises(ValueError, match="negative"):
        module.parse_nz_table("0 1\n1 -1\n")
    with pytest.raises(ValueError, match="uniform"):
        module.parse_nz_table("0 1\n1 2\n2.1 3\n")
    with pytest.raises(ValueError, match="non-finite"):
        module.parse_nz_table("0 1\n1 nan\n")


def test_tied_radii_are_deterministically_assigned_and_stats_are_descriptive():
    profile = module._quartile_profile([0, 1, 1, 1, 2, 3, 4, 5], [2, 3, 5, 7, 11, 13, 17, 19])
    assert len(profile["bins"]) == 4
    assert sum(b["n"] for b in profile["bins"]) == 8
    assert profile["spearman_rho"] == pytest.approx(0.9759000729485332)
    assert "p_value" not in profile


def test_spearman_constant_input_is_unavailable():
    assert module.spearman_rho([1, 1], [2, 3]) is None


def test_nz_pairwise_overlap_is_normalized_and_symmetric():
    assert module.overlap_coefficient([2, 8], [8, 2]) == pytest.approx(0.4)
    assert module.overlap_coefficient([2, 8], [8, 2]) == module.overlap_coefficient([8, 2], [2, 8])
    assert module.overlap_coefficient([2, 8], [2, 8]) == pytest.approx(1.0)
    with pytest.raises(ValueError, match="same grid"):
        module.overlap_coefficient([1], [1, 2])


def test_cchp_keeps_both_filter_groups_and_counts_unique_host_rows(tmp_path):
    path = tmp_path / "cchp.zip"
    with zipfile.ZipFile(path, "w") as archive:
        for i in range(10):
            archive.writestr(f"release/h{i}.csv", ",RA,DEC,RGC,F115W,F356W\n0,10,20,1,21,20\n")
        archive.writestr("release/n4258.csv", ",RA,DEC,RGC,F115W,F356W,F444W\n0,10,20,1,21,20,19\n")
    result = module.analyze_cchp(path)
    assert result["summary"]["host_csv_count"] == 11
    assert result["summary"]["host_filter_profile_count"] == 12
    assert result["summary"]["row_count"] == 11
    assert "n4258" in result["summary"]["filter_groups"]["F115W-F356W"]
    assert "n4258" in result["summary"]["filter_groups"]["F115W-F444W"]
