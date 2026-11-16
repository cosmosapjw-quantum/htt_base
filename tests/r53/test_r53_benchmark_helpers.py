"""R53 helper regressions: finite-MC flat posterior, power-only LR, analytic inflation."""
import importlib.util
import math
from pathlib import Path

import numpy as np
import pytest
from scipy.stats import chi2


def _mod():
    p = Path(__file__).resolve().parents[2] / "scripts/r53/run_r53_benchmark.py"
    spec = importlib.util.spec_from_file_location("r53b", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_power_only_lr_matches_noncentral_chi2_and_is_sign_blind():
    m = _mod()
    F = np.diag([4.0, 2.0, 1.0])
    s = np.array([0.5, -0.3, 0.2]); sh = np.array([0.4, -0.1, 0.3])
    T = sh @ F @ sh
    lr = m.power_only_loglr(T, s @ F @ s, 3)
    assert lr == m.power_only_loglr(T, (-s) @ F @ (-s), 3)
    assert m.power_only_loglr(T, 0.0, 3) == 0.0
    assert math.isfinite(lr)


def test_flat_finite_mc_posterior_is_multivariate_t():
    m = _mod()
    F = np.array([[2.0, 0.3], [0.3, 1.0]]); t = np.array([0.5, -0.2]); car = {"F": F, "t": t, "Q0": 7.0}
    sh, scale, nu = m.flat_prior_finite_mc_posterior(car, F, 30)
    np.testing.assert_allclose(sh, np.linalg.solve(F, t))
    Qmin = 7.0 - t @ sh
    np.testing.assert_allclose(scale, (29 + Qmin) / 28 * np.linalg.inv(F))
    # density check: log posterior differences equal SH law differences
    def sh_law(s):
        q = 7.0 - 2 * s @ t + s @ F @ s
        return -15 * math.log1p(q / 29)
    def mvt(s):
        d = s - sh
        return -(nu + 2) / 2 * math.log1p(d @ np.linalg.solve(scale, d) / nu)
    a, b = np.array([0.1, 0.2]), np.array([-0.4, 0.3])
    assert sh_law(a) - sh_law(b) == pytest.approx(mvt(a) - mvt(b), rel=1e-12)


def test_analytic_inflation_limits():
    m = _mod()
    assert m.analytic_sd_inflation(10**8, 45, 5) == pytest.approx(1.0, abs=1e-5)
    assert m.analytic_sd_inflation(200, 45, 5) == pytest.approx(math.sqrt(199 / 153 * 198 / 159))
