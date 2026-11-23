"""Tests for R100 Part C (fixed-offset exposure GLMs, empty-cell retention, boosted reselection)."""
from __future__ import annotations

import json
import math
import numpy as np
import pytest

from scripts.r100 import radio_exposure_selection as r100_rad


def test_exposure_offset_scaling_invariance_and_empty_cells():
    """Uniform exposure rescaling e -> c*e shifts only beta_0 by -ln(c) and retains empty cells cleanly."""
    rng = np.random.default_rng(1004)
    n_pix = 120
    X = np.column_stack((np.ones(n_pix), rng.normal(size=(n_pix, 3))))
    X[:, 1:] /= np.maximum(np.linalg.norm(X[:, 1:], axis=1, keepdims=True), 1.0)
    exp_sr = rng.uniform(0.05, 1.0, size=n_pix)
    true_b = np.array([4.0, 0.2, -0.15, 0.1])
    mu = exp_sr * np.exp(X @ true_b)
    y = rng.poisson(mu).astype(float)
    y[0] = 0.0  # force an explicit observed empty cell

    for model in ("poisson", "nb1_pearson", "nb1_mle", "nb2_coxlss"):
        f1 = r100_rad.fit_offset_count_glm(y, X, np.log(exp_sr), model=model)
        c = 7.5
        f2 = r100_rad.fit_offset_count_glm(y, X, np.log(c * exp_sr), model=model)
        assert abs((f2["beta"][0] - f1["beta"][0]) + math.log(c)) < 1e-8
        assert np.allclose(f2["beta"][1:], f1["beta"][1:], rtol=0, atol=1e-8)

    with pytest.raises(ValueError, match="all be finite"):
        r100_rad.fit_offset_count_glm(y[:5], X[:5], np.array([0.0, -np.inf, 0.0, 0.0, 0.0]), "poisson")


def test_count_pmf_score_finite_difference_parity():
    """Analytic d(logp)/d(eta) and d(logp)/d(disp) match centered finite differences for NB1 & NB2."""
    rng = np.random.default_rng(1005)
    y = rng.integers(0, 25, size=40).astype(float)
    eta = rng.uniform(1.0, 4.0, size=40)
    eps = 1e-6
    for fam, disp in (("poisson", 0.0), ("nb1", 0.37), ("nb2", 0.18)):
        lp, de, dd = r100_rad.count_logpmf_and_grad_eta(y, eta, fam, disp)
        fd_eta = (
            r100_rad.count_logpmf_and_grad_eta(y, eta + eps, fam, disp)[0]
            - r100_rad.count_logpmf_and_grad_eta(y, eta - eps, fam, disp)[0]
        ) / (2.0 * eps)
        assert np.allclose(de, fd_eta, rtol=1e-7, atol=1e-8)
        if fam != "poisson":
            fd_disp = (
                r100_rad.count_logpmf_and_grad_eta(y, eta, fam, disp + eps)[0]
                - r100_rad.count_logpmf_and_grad_eta(y, eta, fam, disp - eps)[0]
            ) / (2.0 * eps)
            assert np.allclose(dd, fd_disp, rtol=1e-6, atol=1e-7)


def test_boosted_reselection_small_beta_ellis_baldwin_limit():
    """Nonlinear finite-boost reselection recovers [2 + x(1+alpha)]*beta to O(beta^3) as beta -> 0."""
    cuts = np.log(np.array([15.0, 20.0, 30.0, 50.0]))
    x = 1.15
    counts = -x * (cuts - cuts[1])
    beta_tiny = 1e-4 * np.array([0.5, -0.7, 0.3])
    out = r100_rad.boosted_reselection_dipole(beta_tiny, cuts, counts, 1, "dirac_0p75", 0.75)
    assert out["nonlinear_plus_curvature_rel_diff"] < 1e-7
    assert np.allclose(out["boosted_nonlinear_dipole_vec"], (2.0 + x * 1.75) * beta_tiny, rtol=1e-7, atol=1e-12)


def test_r100_radio_result_artifact_contracts():
    """Verify RADIO_EXPOSURE_SELECTION_RESULTS.json preserves physical_Pi=None and active support."""
    path = r100_rad.OUT_DIR / "RADIO_EXPOSURE_SELECTION_RESULTS.json"
    if not path.exists():
        pytest.skip("RADIO_EXPOSURE_SELECTION_RESULTS.json not generated yet")
    d = json.loads(path.read_text())
    assert d["physical_Pi"] is None
    assert d["C1_lotss_dr3_coverage_audit"]["mosaic_count"] == 1580
    assert d["C2_offset_count_models"]["LoTSS_DR3_outer_all1771"]["active_cells"] == 1771
    assert d["C2_offset_count_models"]["LoTSS_DR3_legacy966"]["active_cells"] == 966
    assert d["C2_five_survey_common_beta_vs_residuals"]["calibrated_p"] is None
    assert d["C2_five_survey_with_lotss_outer_b15_sensitivity"]["calibrated_p"] is None
    assert d["C2_five_survey_common_beta_vs_residuals"]["surveys"][-1] == "LoTSS_DR3_legacy966"
    assert d["C2_five_survey_with_lotss_outer_b15_sensitivity"]["surveys"][-1] == "LoTSS_DR3_outer_b15"
