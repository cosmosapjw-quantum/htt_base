"""Narrow falsifiers for the R37-02 saved-law consumer."""
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("kinematic_image", HERE / "kinematic_image.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def test_gaia_common_carrier_and_lost_slope():
    raw = json.loads(M.GAIA.read_text())
    old = json.loads(M.GAIA_PRE.read_text())
    out = M.gaia_product(raw, old)
    c = out["constrained_bin_depth"]
    assert abs(c["full_deviance_difference"] - c["common_carrier_deviance_difference"]) < 1e-9
    assert abs(c["single_g_score_deviance_difference"]) < 1e-10
    assert out["free_bin_slope"]["T24_to18_information_rank_with_free_bin_nuisance"] == 0
    assert c["joint_coverage"]["joint_GLS_and_tensorized"]["trials"] == 100000


def test_optical_cross_covariance_and_shared_budget():
    src = json.loads(M.OPT.read_text())
    p6 = json.loads(M.P6.read_text())
    optmod = M.load_optical_module()
    out = M.optical_product(src, p6, optmod)
    c = np.array(out["full_summary_covariance_10x10"])
    cr = np.array(out["residual_covariance_7x7"])
    cc = c.copy(); cc[:3, 3:] = 0; cc[3:, :3] = 0
    assert np.linalg.norm(cr-optmod.residual_covariance(cc, np.array(p6["tensor"]))) > 0
    assert "direct_dipole" not in out["shared_budget"]
    assert out["minimum_compatibility"]["compatible"]
    assert out["S_zero"]["branch"] == "S_ZERO_DIRECT_MEMBERSHIP"
    assert out["S_small_nonzero"]["branch"] == "INVERTIBLE_S"


def test_pm_null_and_exact_fixed_q_radius():
    pm = json.loads(M.PM.read_text())
    out = M.pm_product(pm)
    assert all(x["response_rank"] == 5 and x["null_dimension"] == 5 for x in out["history_images"])
    assert out["nuisance"]["free_E2_nuisance_rank"] == 0
    ch = M.chirality(M.load_optical_module())
    assert abs(ch["rho_sign"] - 1/np.sqrt(3)) < 1e-12
    assert abs(ch["rho_sign"] - ch["attaining_delta_norm"]) < 1e-12


def test_endpoint_difference_and_full_null_fibre():
    # Dimensionless normalized-time endpoint witness from the R37 review.
    bo = np.zeros(5); bs = np.array([-1e-4, 0, 0, 0, 0]); s = np.zeros(5)
    tref = 1.; c = 1.; distance = 2.
    q = (bo-bs)/tref
    k = 2*c*tref/distance
    u = M.history_response(k) @ np.r_[q, s]
    np.testing.assert_allclose(u, [1e-4, 0, 0, 0, 0], atol=0)
    for k in (0, .1, 1, 2, 10):
        dq = np.array([1, -2, 3, -4, 5.])
        np.testing.assert_allclose(M.history_response(k) @ np.r_[dq, k*dq], np.zeros(5), atol=1e-14)


def test_physical_remainder_support_and_unit_equivariance():
    pm = json.loads(M.PM.read_text())
    result = M.pm_product(pm)
    f = np.asarray(pm["gram"]["primary_spin_glide6"]["profile"]["information"])
    center = np.asarray(result["quotient_image"]["center_a_hat_uasyr"])
    threshold = result["quotient_image"]["chi2_5_95_threshold"]
    v = np.array([.2, -.1, .3, .4, -.5]); radius = 1.
    at_zero = M.quotient_support(center, f, 0, v, threshold)
    at_one = M.quotient_support(center, f, radius, v, threshold)
    assert at_one[1] > at_zero[1] and at_one[0] < at_zero[0]
    # Ellipsoid extremizer plus aligned Frobenius-ball extremizer attains support.
    fi_v = np.linalg.solve(f, v)
    z = center + np.sqrt(threshold / (v @ fi_v)) * fi_v + radius*v/np.linalg.norm(v)
    np.testing.assert_allclose(v @ z, at_one[1], rtol=1e-13)
    unit = .001  # microarcsec/year to milliarcsec/year
    scaled = M.quotient_support(unit*center, f/unit**2, unit*radius, v, threshold)
    np.testing.assert_allclose(scaled, unit*np.asarray(at_one), rtol=1e-13)
    widths = np.asarray(result["quotient_image"]["eigenmode_halfwidths_uasyr"])
    np.testing.assert_allclose(widths[1]-widths[0], .5)


def test_optical_exact_zero_tiny_nonzero_and_domain_rejection():
    src = json.loads(M.OPT.read_text()); p6 = json.loads(M.P6.read_text())
    mod = M.load_optical_module()
    s = np.asarray(p6["tensor"])
    summary = np.asarray(src["synthetic_source_design"]["full_signed_summary"])
    d, o = summary[:3], summary[3:]
    zero = M.safe_joint_test(mod, o, 0*s, d, .01, e_d=0)
    small = M.safe_joint_test(mod, o, 1e-8*s, d, .01, e_d=0)
    tiny = M.safe_joint_test(mod, o, 1e-200*s, d, .01, e_d=0)
    assert zero["branch"] == "S_ZERO_DIRECT_MEMBERSHIP" and zero["inverse_d"] is None
    assert small["branch"] == tiny["branch"] == "INVERTIBLE_S"
    assert np.isfinite(tiny["inverse_d"]).all()
    import pytest
    with pytest.raises(ValueError, match="nonrepresentable"):
        M.safe_joint_test(mod, o, 1e-320*s, d, .01, e_d=0)
