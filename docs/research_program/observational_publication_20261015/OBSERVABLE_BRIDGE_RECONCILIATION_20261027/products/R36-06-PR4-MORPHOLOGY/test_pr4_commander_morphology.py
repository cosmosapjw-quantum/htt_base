"""Small falsifiers for the frozen Commander source/operator boundary."""

import importlib.util
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from astropy.io import fits


SOURCE = Path(__file__).with_name("pr4_commander_morphology.py")
SPEC = importlib.util.spec_from_file_location("pr4_commander_morphology_test", SOURCE)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def table(kind):
    names = ("Q_POLARIZATION", "U_POLARIZATION") if kind == "observed" else ("I_STOKES", "Q_STOKES", "U_STOKES")
    unit = "K_CMB" if kind == "observed" else "uK_CMB"
    hdu = fits.BinTableHDU.from_columns([fits.Column(name=x, format="E", unit=unit, array=[0.0]) for x in names])
    for key, value in {"NSIDE": 2048, "ORDERING": "NESTED", "COORDSYS": "GALACTIC",
                       "POLCCONV": "COSMO", "PIXTYPE": "HEALPIX"}.items():
        hdu.header[key] = value
    if kind == "mc":
        hdu.header["METHOD"] = "Commander"
        hdu.header["AST-COMP"] = "CMB"
    return hdu


@pytest.mark.parametrize("kind,names", [("observed", ("Q_POLARIZATION", "U_POLARIZATION")),
                                        ("mc", ("Q_STOKES", "U_STOKES"))])
def test_header_accepts_exact_polarization_role(kind, names):
    hdu = table(kind)
    MODULE.check_header(hdu, kind, names)
    hdu.header["POLCCONV"] = "IAU"
    with pytest.raises(ValueError, match="geometry/frame"):
        MODULE.check_header(hdu, kind, names)


def test_header_rejects_units_and_component_role():
    hdu = table("mc")
    hdu.header["TUNIT2"] = "K_CMB"
    with pytest.raises(ValueError, match="unit"):
        MODULE.check_header(hdu, "mc", ("Q_STOKES", "U_STOKES"))
    hdu = table("mc")
    hdu.header["AST-COMP"] = "NOISE"
    with pytest.raises(ValueError, match="component role"):
        MODULE.check_header(hdu, "mc", ("Q_STOKES", "U_STOKES"))


def test_excluded_nan_is_zero_but_retained_nan_rejects(monkeypatch):
    monkeypatch.setattr(MODULE, "NPIX", 4)
    mask = np.array([True, False, True, False])
    index = np.arange(4)
    hdu = SimpleNamespace(data={"Q": np.array([1.0, np.nan, 2.0, np.nan]),
                                "U": np.array([3.0, np.nan, 4.0, np.nan])})
    q, u = MODULE.masked_qu_from_nested(hdu, ("Q", "U"), 1.0, mask, index)
    np.testing.assert_array_equal(q, [1, 0, 2, 0])
    np.testing.assert_array_equal(u, [3, 0, 4, 0])
    hdu.data["Q"][0] = np.nan
    with pytest.raises(ValueError, match="nonfinite"):
        MODULE.masked_qu_from_nested(hdu, ("Q", "U"), 1.0, mask, index)


def test_exact_interval_endpoints_and_missing_id():
    lo, hi = MODULE.exact_interval(0, 100)
    assert lo == 0 and 0 < hi < 0.05
    lo, hi = MODULE.exact_interval(100, 100)
    assert hi == 1 and 0.95 < lo < 1
    lo, hi = MODULE.exact_interval(50, 100)
    assert (hi - lo) / 2 <= 0.105
    with pytest.raises(ValueError, match="outside frozen set"):
        MODULE.map_identity("mc", 200)


def test_valid_J_survives_descriptive_axis_abstention():
    donor = MODULE.donor_module()
    alm = {(l, m): 0j for l in (2, 3, 4) for m in range(-l, l + 1)}
    alm[2, 0] = 1
    alm[3, 1], alm[3, -1] = 1, -1
    alm[4, 1], alm[4, -1] = 1j, 1j
    result = donor.features(alm)
    assert result["axis_status"] == "ABSTAIN"
    assert result["alignment23_squared"] is None
    assert math.isfinite(result["J234"]) and abs(result["J234"]) > 0
    zero_ell = dict(alm)
    zero_ell.update({(4, m): 0j for m in range(-4, 5)})
    with pytest.raises(ValueError, match="zero multipole"):
        donor.features(zero_ell)


def test_mc100_aggregate_json_integrity():
    aggregate_path = SOURCE.with_name("COMMANDER_MC100_AGGREGATE.json")
    assert aggregate_path.is_file(), "COMMANDER_MC100_AGGREGATE.json must exist"
    import json
    data = json.loads(aggregate_path.read_text())
    assert data["schema"] == "htt.r36_pr4_commander_mc100_aggregate/1"
    assert data["task_id"] == "R36-06-PR4-MORPHOLOGY"
    assert data["status"] == "COMPLETED_SUCCESS"
    assert data["claim_tier"] == "C0_DIAGNOSTIC_ONLY"
    assert data["sample_size"] == 100
    assert len(data["mc_values"]["mc_ids"]) == 100

    p_vals = data["p_values"]
    assert p_vals["count_J234_gte_obs"] == 43
    assert p_vals["p_J234_gte_obs"] == (43 + 1) / 101
    assert abs(p_vals["p_J234_gte_obs"] - 0.43564356) < 1e-6

    assert p_vals["count_abs_J234_gte_obs"] == 74
    assert p_vals["p_abs_J234_gte_obs"] == (74 + 1) / 101
    assert abs(p_vals["p_abs_J234_gte_obs"] - 0.74257425) < 1e-6

    assert p_vals["count_alignment23_squared_gte_obs"] == 22
    assert p_vals["p_alignment23_squared_gte_obs"] == (22 + 1) / 101
    assert abs(p_vals["p_alignment23_squared_gte_obs"] - 0.22772277) < 1e-6


def test_result_json_mc100_consistency():
    result_path = SOURCE.with_name("RESULT.json")
    import json
    res = json.loads(result_path.read_text())
    assert res["status"] == "COMPLETED_SUCCESS"
    assert res["claim_tier"] == "C0_DIAGNOSTIC_ONLY"
    assert "mc100_statistics" in res
    mc_stats = res["mc100_statistics"]
    assert mc_stats["sample_size"] == 100
    assert mc_stats["ranks"]["count_J234_gte_obs"] == 43
    assert mc_stats["ranks"]["count_abs_J234_gte_obs"] == 74
    assert mc_stats["ranks"]["count_alignment23_squared_gte_obs"] == 22
    assert mc_stats["p_values"]["p_J234_gte_obs"] == (43 + 1) / 101


def test_histogram_artifacts_exist():
    pdf_path = SOURCE.with_name("null_distribution_histograms.pdf")
    png_path = SOURCE.with_name("null_distribution_histograms.png")
    assert pdf_path.is_file() and pdf_path.stat().st_size > 1000
    assert png_path.is_file() and png_path.stat().st_size > 1000

