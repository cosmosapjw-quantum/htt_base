"""Independent scalar likelihood oracles for the global amplitude repair."""
import math
from types import SimpleNamespace

import numpy as np
import pytest

from common.covariance_amplitude import maximize_covariance_amplitude


def test_negative_boundary_score_can_hide_global_interior_maximum():
    # Exact stationary roots of the two-mode score numerator.
    expected = (1699 + math.sqrt(2821801)) / 400
    answer = maximize_covariance_amplitude([0, 20], [100, 1])
    assert answer["amplitude"] == pytest.approx(expected, rel=2e-6)
    assert answer["loglike_gain"] == pytest.approx(4.4485319395, abs=1e-9)
    assert answer["objective_gap"] <= 1e-8
    assert answer["amplitude"] > 0


def test_legacy_consumer_uses_global_objective():
    from obsstat.cf4_growth_covariance import amplitude_mle
    prep = SimpleNamespace(eigvec=np.eye(2), inv_sig=np.ones(2), eigval=np.array([100., 1.]))
    a, variance = amplitude_mle(np.array([0., math.sqrt(20.)]), prep)
    assert a == pytest.approx((1699 + math.sqrt(2821801))/400, rel=2e-6)
    assert variance > 0


def test_one_mode_oracles_and_cap():
    assert maximize_covariance_amplitude([4], [2])["amplitude"] == pytest.approx(1.5)
    assert maximize_covariance_amplitude([.5], [2])["amplitude"] == 0
    a = maximize_covariance_amplitude([10], [1], a_cap=2)
    assert a["amplitude"] == 2 and a["at_cap"]
    assert maximize_covariance_amplitude([5], [0])["identified"] is False


def test_multiple_peaks_agree_with_dense_reference_lower_bound():
    rng = np.random.default_rng(98422)
    for _ in range(6):
        lam = 10. ** rng.uniform(-3, 3, 7)
        p2 = rng.chisquare(1, 7) * rng.uniform(1, 12)
        a = maximize_covariance_amplitude(p2, lam, loglike_tol=1e-7)
        grid = np.r_[0., np.geomspace(1e-9, a["search_upper"], 10001)]
        t = grid[:, None] * lam
        values = .5 * np.sum(p2 * t / (1+t) - np.log1p(t), axis=1)
        assert a["loglike_gain"] >= values.max() - 1e-8
        assert a["objective_gap"] <= 1e-7


def test_legacy_scale_400_modes_resolves_without_monotone_score_assumption():
    # Independent reviewer reproduced a resource failure of the separable
    # bound alone on this valid existing-consumer-sized problem.
    rng = np.random.default_rng(600400)
    lam = np.geomspace(1e-2, 1e2, 400)
    p2 = (1.0 + lam) * rng.chisquare(1, 400)
    answer = maximize_covariance_amplitude(p2, lam)
    grid = np.r_[0.0, np.geomspace(1e-7, answer["search_upper"], 10001)]
    t = grid[:, None] * lam
    ref = .5 * np.sum(p2 * t / (1.0 + t) - np.log1p(t), axis=1)
    assert answer["loglike_gain"] >= ref.max() - 1e-8
    assert answer["objective_gap"] <= 1e-8
    assert answer["intervals"] < 5000


@pytest.mark.parametrize("p2,lam", [([-1],[1]),([1],[-1]),([np.inf],[1]),([] ,[]),([1,2],[1])])
def test_invalid_input_rejected(p2, lam):
    with pytest.raises(ValueError):
        maximize_covariance_amplitude(p2, lam)


def test_unresolved_search_raises_instead_of_passing():
    with pytest.raises(RuntimeError, match="max_intervals"):
        maximize_covariance_amplitude([0,20], [100,1], loglike_tol=1e-14, max_intervals=1)
