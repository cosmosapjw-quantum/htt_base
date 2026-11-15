"""CORE-03 GRAM-1 regression: the MIO certificate's shear amplitude must use the STF5 Gram (Frobenius) norm.

The 5-vector chart is (Sxx, Syy, Sxy, Sxz, Syz) with Szz = -Sxx - Syy, so ||S||_F^2 = v^T G_STF5 v with
G_STF5 = [[2,1,0,0,0],[1,2,0,0,0],[0,0,2,0,0],[0,0,0,2,0],[0,0,0,0,2]].  The component-Euclidean norm is wrong.
Synthetic stub inputs only; no MCMC and no data are used.
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT / "htt" / "src", ROOT / "htt", ROOT):
    sys.path.insert(0, str(p))

from htt.htt.infer.tensor_five_variable_inference import TensorFiveVariableEngine  # noqa: E402

G_STF5 = np.array([[2, 1, 0, 0, 0], [1, 2, 0, 0, 0], [0, 0, 2, 0, 0], [0, 0, 0, 2, 0], [0, 0, 0, 0, 2]], float)


def _certificate(shear5):
    mean = np.zeros(17)
    mean[0:5] = shear5
    engine = TensorFiveVariableEngine.__new__(TensorFiveVariableEngine)
    engine.n_data = 100
    state = SimpleNamespace(
        support_profiles_F={"BETA_MO": SimpleNamespace(occupancy_ratios=np.array([0.1]))},
        exceedance_surfaces_Pi={"BETA_MO_MIO_NULL": SimpleNamespace(observed_exceedance=0.5, undefined_mass=0.0)},
        depth_path_GF=SimpleNamespace(cross_shell_covariance=np.eye(2)),
    )
    mcmc = SimpleNamespace(mean=mean, r_hat=np.ones(17))
    loocv = {"summary_status": "LOOCV_ADEQUACY_VERIFIED", "folds": {"a": {"out_of_sample_chi2_per_dof": 1.0}}}
    comp = {"hypotheses": [{"hypothesis_id": "H_loc", "chi2": 10.0, "Delta_BIC": -1.0},
                           {"hypothesis_id": "H_0", "chi2": 12.0, "Delta_BIC": 0.0}]}
    return engine.generate_mio_certificate(state, mcmc, loocv, comp)


def _find(d, key):
    if isinstance(d, dict):
        if key in d:
            return d[key]
        for v in d.values():
            r = _find(v, key)
            if r is not None:
                return r
    return None


def test_sigma_amplitude_uses_stf5_gram_norm():
    v = np.array([0.6e-4, 0.6e-4, 0.0, 0.0, 0.0])
    expected = float(np.sqrt(v @ G_STF5 @ v))          # 1.4697e-4 (Euclidean would be 8.485e-5)
    cert = _certificate(v)
    got = _find(cert, "sigma_frobenius_upper_bound")
    assert got is not None, "sigma_frobenius_upper_bound missing from certificate payload"
    assert abs(got - expected) < 1e-12 * max(1.0, expected) + 1e-18, (got, expected)


def test_shear_budget_flag_uses_gram_norm():
    # Euclidean norm 8.5e-5 < 1e-4 would wrongly report 'bounded'; the Gram norm 1.47e-4 exceeds the 1e-4 budget.
    cert = _certificate(np.array([0.6e-4, 0.6e-4, 0.0, 0.0, 0.0]))
    assert _find(cert, "cosmic_shear_bounded_by_physical_budget") is False


def test_off_diagonal_shear_components_weighted_by_two():
    v = np.array([0.0, 0.0, 0.5e-4, 0.5e-4, 0.5e-4])     # Gram norm^2 = 2*3*(0.5e-4)^2
    cert = _certificate(v)
    got = _find(cert, "sigma_frobenius_upper_bound")
    assert abs(got - np.sqrt(6.0) * 0.5e-4) < 1e-16
