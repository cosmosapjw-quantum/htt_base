"""Small independent numerical references for the optical STF image."""
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("optical_shear_analysis", HERE / "analyze.py")
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


def test_full_sky_fourth_moment_and_stf_reconstruction():
    # Product quadrature integrates this degree-four polynomial exactly.
    x, w = np.polynomial.legendre.leggauss(6)
    phi = 2*np.pi*np.arange(16)/16
    b = np.array([.17, -.31, .09, -.23, .19])
    B = np.einsum("a,aij->ij", b, analysis.STF)
    acc = 0.
    for xx, ww in zip(x, w):
        for pp in phi:
            n = np.array([math.sqrt(1-xx*xx)*math.cos(pp), math.sqrt(1-xx*xx)*math.sin(pp), xx])
            acc += ww/2/len(phi)*float(n@B@n)**2
    assert abs(acc - 2*np.sum(b*b)/15) < 1e-14
    assert abs(np.trace(B)) < 1e-14


def test_full_covariance_and_independent_ellipsoid_optimization():
    d = json.loads((HERE / "RESULT.json").read_text())
    x = d["scenarios"]["a_0.055_b_0.290"]["models"]["C_union"]
    names = x["coefficient_names_raw_units"]
    C = np.asarray(x["coefficient_covariance_full_raw_units"])
    indices = x["stf_column_indices"]
    # Independent selector and Jacobian applied to all 15 correlated coefficients.
    J = np.zeros((5, len(names)))
    J[np.arange(5), indices] = -math.log(10)/5
    np.testing.assert_allclose(J @ C @ J.T, x["sigma_eff_over_H_covariance"], atol=1e-14, rtol=0)
    assert np.max(np.abs(C[np.ix_(indices, [0, 4, 7])])) > 1e-5
    b = np.asarray(x["sigma_eff_over_H_coordinates"])
    Q = np.asarray(x["sigma_eff_over_H_covariance"])
    c = x["reference_region"]["radius_sq_chi2_p"]
    L = np.linalg.cholesky(Q)
    # SLSQP in whitened coordinates provides a separate optimization reference.
    starts = [np.eye(5)[j]*np.sqrt(c) for j in range(5)]
    starts += [-v for v in starts]
    candidates = []
    for init in starts:
        opt = minimize(lambda u: -np.linalg.norm(b+L@u)**2, init,
                       jac=lambda u: -2*L.T@(b+L@u),
                       constraints=[{"type": "ineq", "fun": lambda u: c-u@u,
                                     "jac": lambda u: -2*u}],
                       method="SLSQP", options={"ftol": 1e-12, "maxiter": 500})
        if opt.success:
            candidates.append(np.linalg.norm(b+L@opt.x))
    assert candidates
    assert abs(max(candidates)-x["reference_region"]["norm_sigma_eff_over_H_interval"][1]) < 1e-7
    assert float(b@np.linalg.solve(Q,b)) < c


def test_remainder_nesting_and_physical_hold():
    d = json.loads((HERE / "RESULT.json").read_text())
    assert len(d["scenarios"]) == 4
    for s in d["scenarios"].values():
        assert s["models"]["A_calibration_flow"]["stf_status"] == "UNDEFINED_NO_STF_COORDINATES_IN_MODEL_A"
        for name in ("B_optical_STF", "C_union"):
            x = s["models"][name]
            widths = [row["width"] for row in x["remainder_sensitivity"]]
            assert all(a < b for a, b in zip(widths, widths[1:]))
            assert all(row["conditional_sigma2_lower"] == 0 for row in x["remainder_sensitivity"])
            assert x["physical_H_strata"]["H_minus_nonpositive"] == "UNBOUNDED_UPPER_IN_T2_QUOTIENT"
            assert x["physical_H_strata"]["registered_G_congruence_map"] == "HOLD"
            assert x["reference_region"]["zero_inside"]
