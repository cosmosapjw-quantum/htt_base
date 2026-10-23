"""Focused frozen-law and artifact controls; no catalogue replay."""
import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import norm

import analyze

HERE = Path(__file__).resolve().parent


def result():
    return json.loads((HERE/"RESULT.json").read_text())


def test_cached_join_design_and_no_observed_response():
    X, n, s, groups, meta = analyze.read_design()
    assert X.shape == (274, 12) and n.shape == (274, 3)
    assert len(groups) == len(s) == 274
    assert meta["PGC9031_Vcmb_km_s"] == 317
    assert np.max(np.abs(np.linalg.norm(n, axis=1)-1)) < 1e-12
    assert "DMbest_mag" not in meta["nuisance_columns"]
    assert abs(np.sqrt(np.mean(X*X, axis=0)).min()-1) < 1e-12


def test_exact_scalar_law_antipodal_and_cubic_order():
    k = 5/math.log(10)
    a = .1
    assert abs(-k*(math.log1p(-a)+math.log1p(a))-.021824027012250224) < 1e-12
    for name, x in analyze.fixed_directions():
        assert abs(np.linalg.norm(x)-1) < 1e-12
        for a in (.001, .002, .3):
            assert np.min(1-a*x) >= .7-1e-14
        p3 = (5*x**3-3*x)/2
        np.testing.assert_allclose(x**3, (2/5)*p3+(3/5)*x, atol=1e-15)


def test_all_fixed_power_remainder_and_midpoint():
    r = result()
    assert r["controls"]["factorizations_cholesky"] == 4
    assert r["controls"]["unique_fixed_templates"] == 48
    assert len(r["scenarios"]) == 4
    for scenario in r["scenarios"]:
        assert len(scenario["rows"]) == 48
        assert set(scenario["nuisance_ranks"].values()) == {12}
        for row in scenario["rows"]:
            d = row["d0"]
            assert abs(row["overlap_rho_star"]-d/2) < 1e-14
            witness = row["shared_midpoint_witness"]
            midpoint = np.asarray(witness["projected_whitened_midpoint"])
            assert midpoint.shape == (274,)
            assert abs(np.linalg.norm(midpoint)-d/2) < 1e-12
            assert abs(witness["null_remainder_norm"]-d/2) < 1e-12
            assert abs(witness["alternative_remainder_norm"]-d/2) < 1e-12
            assert abs(row["tau80"]-d/(norm.ppf(.8)-norm.ppf(.05))) < 1e-12
            for case in row["noise"]:
                tau = case["tau"]
                assert abs(case["oracle_power"]-norm.cdf(norm.ppf(.05)+d/tau)) < 1e-14
                for curve in case["remainder_power"]:
                    assert abs(curve["maximin_power"]-norm.cdf(norm.ppf(.05)+max(0, d-2*curve["rho"])/tau)) < 1e-14
                    assert .05-1e-14 <= curve["maximin_power"] <= case["oracle_power"]+1e-14
    assert r["physical_remainder_status"].startswith("UNRESTRICTED")
    assert r["original_acceptance_promoted"] is False


def test_cubic_small_amplitude_bound_and_independent_reference():
    r = result()
    controls = r["controls"]
    assert controls["max_linear_scaled_projection"] < 1e-10
    assert controls["max_quadratic_scaled_projection"] < 1e-10
    assert controls["max_small_amplitude_bound_ratio"] < 1
    for scenario in r["scenarios"]:
        for row in scenario["rows"]:
            assert np.isclose(row["d0_squared"], row["eigen_reference_d0_squared"], rtol=1e-9, atol=1e-10)
            if row["amplitude"] == .01:
                small = row["small_amplitude_controls"]
                assert len(small) == 2
                for case in small:
                    assert case["cubic_error"] <= case["rigorous_remainder_bound"]
                assert abs(small[1]["d0_over_a_cubed"]/small[0]["d0_over_a_cubed"]-1) < .01
