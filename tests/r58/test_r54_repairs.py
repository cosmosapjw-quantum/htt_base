"""Regression witnesses for the R54 theorem-domain and stable-kernel repairs."""
from pathlib import Path
import importlib.util
import sys
import types

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[2]
INFER = ROOT / "htt/htt/htt/infer"
PACKAGE = "r54_repair_review_package"
package = types.ModuleType(PACKAGE)
package.__path__ = [str(INFER)]
sys.modules[PACKAGE] = package


def load(name):
    full_name = PACKAGE + "." + name
    spec = importlib.util.spec_from_file_location(full_name, INFER / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[full_name] = module
    spec.loader.exec_module(module)
    return module


tensor = load("r54_tensor_five_view")
ident = load("r54_identifiability")


def test_rho_zero_small_and_overflow_limits():
    tau = np.array([0., 1e-20, 1e-10, .2, 10., 1100., 10000.])
    rho = ident.rho_ratio(tau)
    assert np.isfinite(rho).all()
    assert rho[0] == 0
    assert rho[1] == pytest.approx(np.sqrt(6) * tau[1] / 10, rel=1e-14, abs=0.)
    assert np.all(np.diff(rho) >= 0)
    assert rho[-1] == pytest.approx(np.sqrt(6), rel=1e-15)
    x = np.exp(.7 * tau[2:5])
    np.testing.assert_allclose(rho[2:5], np.sqrt(6) * (x - 1) / (x + 6), rtol=1e-6)


@pytest.mark.parametrize("tau", [-1., np.nan, np.inf, -np.inf, [0., np.nan]])
def test_rho_invalid_optical_depth_fails_closed(tau):
    with pytest.raises(ValueError):
        ident.rho_ratio(tau)


@pytest.mark.parametrize("n,p,k", [(2, 3, 3), (3, 3, 1), (3, 3, 0), (3, 3, 4),
                                       (True, 1, 1), (4., 3, 1), (4, 3., 1), (4, 3, 1.)])
def test_wishart_domain_and_integer_counts(n, p, k):
    with pytest.raises(ValueError):
        ident.wishart_gls_factors(n, p, k)
    # A centered covariance from N simulations has n=N-1 Wishart degrees.
    n_sims = n + 1 if not isinstance(n, bool) else True
    with pytest.raises(ValueError):
        tensor.finite_mc_sd_inflation(n_sims, p, k)


@pytest.mark.parametrize("n,p,k", [(3, 3, 3), (4, 3, 1), (299, 45, 5),
                                       (np.int64(5), np.int64(3), np.int64(2))])
def test_finite_covariance_factors_use_same_valid_wishart_domain(n, p, k):
    factors = ident.wishart_gls_factors(n, p, k)
    sd = tensor.finite_mc_sd_inflation(n + 1, p, k)
    assert sd**2 == pytest.approx(factors["variance_ratio"])
    if p == k:
        assert factors["cov_factor"] == factors["plugin_factor"] == sd == 1.


def test_unidentified_marginal_contracts_under_correlated_proper_prior():
    # Likelihood observes iota only. A correlated proper prior can nevertheless
    # shrink nu's MARGINAL; nu|iota retains its prior conditional law.
    r = .9
    prior = np.array([[1., r], [r, 1.]])
    variances = []
    for n in (0., 1., 10., 10000.):
        posterior = np.linalg.inv(np.linalg.inv(prior) + np.diag([n, 0.]))
        expected = 1 - r**2 + r**2 / (n + 1)
        assert posterior[1, 1] == pytest.approx(expected)
        assert posterior[1, 0] / posterior[0, 0] == pytest.approx(r)
        conditional_var = posterior[1, 1] - posterior[1, 0]**2 / posterior[0, 0]
        assert conditional_var == pytest.approx(1 - r**2)
        variances.append(posterior[1, 1])
    assert np.all(np.diff(variances) < 0)
    assert variances[-1] > 1 - r**2
