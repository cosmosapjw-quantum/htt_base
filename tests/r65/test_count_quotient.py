"""Semantic checks of the conditional experiment, not implementation snapshots."""
import numpy as np
import pytest
from numpy.testing import assert_allclose
from scipy import linalg

from htt.htt.infer.r65_count_quotient import (
    RingLikelihood, angular_features, finite_bin_response, fit_joint,
    flux_path_transform, gaussian_five_views, nested_lr, shared_maps,
)


def experiment(quadrupole=False):
    phi = np.tile(np.linspace(0, 2*np.pi, 16, endpoint=False), 5)
    z = np.repeat(np.linspace(-.7, .8, 5), 16)
    v = np.column_stack([np.sqrt(1-z*z)*np.cos(phi),
                         np.sqrt(1-z*z)*np.sin(phi), z])
    keep = ~((phi > .5) & (phi < 1.5) & (z < .1))
    v = v[keep]
    groups = np.repeat(np.arange(5), 16)[keep]
    counts = np.arange(len(v)) % 7+15
    exposure = .7+.1*(np.arange(len(v)) % 4)
    return RingLikelihood(counts, angular_features(v, quadrupole), groups, exposure), v


def test_conditional_quotient_is_invariant_under_arbitrary_ring_exposure():
    e, _ = experiment(True)
    theta = np.array([.013, -.02, .001, -.003, .002, -.004])
    factors = np.exp(np.linspace(-7, 6, e.n_groups))
    other = RingLikelihood(e.counts, e.features, e.groups, e.exposure*factors[e.groups])
    for a, b in zip(e.evaluate(theta)[:3], other.evaluate(theta)[:3]):
        assert_allclose(a, b, atol=2e-10)


def test_profiled_poisson_and_conditioned_multinomial_same_likelihood_ratio():
    e, _ = experiment()
    theta = np.array([.03, -.02])
    def poisson_profile(t):
        weights = e.exposure*np.exp(e.features@t)
        sums = np.bincount(e.groups, weights=weights)
        rate = e.totals[e.groups]*weights/sums[e.groups]
        return np.sum(e.counts*np.log(rate)-rate)
    assert_allclose(e.evaluate(theta)[0], poisson_profile(theta)-poisson_profile(np.zeros(2)),
                    rtol=0, atol=2e-10)


def test_score_hessian_finite_difference_and_fisher_schur():
    e, _ = experiment(True)
    theta = np.linspace(-.02, .03, 6)
    ll, score, fisher, mu = e.evaluate(theta)
    eps = 1e-5
    grad = np.array([(e.evaluate(theta+eps*np.eye(6)[j])[0]-
                      e.evaluate(theta-eps*np.eye(6)[j])[0])/(2*eps) for j in range(6)])
    h = np.column_stack([(e.evaluate(theta+eps*np.eye(6)[j])[1]-
                          e.evaluate(theta-eps*np.eye(6)[j])[1])/(2*eps) for j in range(6)])
    assert_allclose(grad, score, rtol=2e-7, atol=2e-7)
    assert_allclose(-h, fisher, rtol=1e-7, atol=2e-7)
    group_design = np.eye(e.n_groups)[e.groups]
    full = np.column_stack([e.features, group_design])
    j = full.T@(mu[:, None]*full)
    schur = j[:6, :6]-j[:6, 6:]@np.linalg.solve(j[6:, 6:], j[6:, :6])
    assert_allclose(fisher, schur, rtol=1e-11, atol=1e-10)


def test_ring_constant_direction_is_unidentified_not_zero_variance():
    e, v = experiment()
    bad = RingLikelihood(e.counts, np.column_stack([e.features, v[:, 2]]), e.groups)
    eig = np.linalg.eigvalsh(bad.evaluate(np.zeros(3))[2])
    assert abs(eig[0]) < 1e-11*eig[-1]
    with pytest.raises(ValueError, match="not identifiable"):
        fit_joint([bad])


def test_linear_density_dz_is_not_an_all_order_null():
    phi = np.linspace(0, 2*np.pi, 8, endpoint=False)
    def p(z, dz):
        rate = 1+.04*np.sqrt(1-z*z)*np.cos(phi)+dz*z
        return rate/rate.sum()
    assert not np.allclose(p(.5, .1), p(.5, -.1), atol=1e-7)
    assert_allclose(p(0, .1), p(0, -.1))


def test_fit_concavity_and_nested_morphology_ordering():
    e, _ = experiment(True)
    full = fit_joint([e])
    restricted = RingLikelihood(e.counts, e.features[:, :2], e.groups, e.exposure)
    dip = fit_joint([restricted])
    lr = nested_lr(full['log_likelihood_relative_zero'], dip['log_likelihood_relative_zero'], 4)
    assert lr['statistic'] >= 0
    assert np.linalg.norm(full['score_at_maximum']) < 1e-5
    rng = np.random.default_rng(132)
    for offset in rng.normal(0, .02, size=(5, 6)):
        assert e.evaluate(full['estimate']+offset)[0] < full['log_likelihood_relative_zero']


def test_conditional_simulation_preserves_every_ring_total_and_integrality():
    e, _ = experiment()
    simulated = e.simulate([.02, -.01], np.random.default_rng(132))
    assert_allclose(simulated.totals, e.totals)
    assert np.all(simulated.counts == np.floor(simulated.counts))


def test_joint_maps_keep_same_quadrupole_nuisance_under_restriction():
    e, _ = experiment(True)
    maps, offsets = shared_maps(3, 6, responses=[3, 4, 5])
    assert maps[0].shape == (6, 14)
    theta = np.arange(14)/100
    for b, m in enumerate(maps):
        assert_allclose((m@theta)[:2], (3+b)*theta[:2])
        assert_allclose((m@theta)[2:], theta[2+4*b:6+4*b])
    fixedmaps, fixedoffsets = shared_maps(3, 6, [3, 4, 5], fixed_dipole=[.001, -.002])
    assert fixedmaps[0].shape == (6, 12)
    assert_allclose(fixedoffsets[2][:2], [.005, -.01])


def test_finite_flux_bin_reduces_to_power_law_response():
    x, alpha = 1.04310206471, .75
    bounds = np.array([.02, .04, .08])
    cumulative = bounds**(-x)
    counts = cumulative-np.r_[cumulative[1:], 0.]
    boundary = np.r_[x*cumulative, 0.]
    assert_allclose(finite_bin_response(counts, boundary, alpha), 2+(1+alpha)*x)
    with pytest.raises(ValueError):
        finite_bin_response([0], [1, 0], alpha)


def test_signed_flux_path_retains_full_likelihood_and_cross_covariance():
    rng = np.random.default_rng(42)
    a = rng.normal(size=(6, 6))
    c = a@a.T+np.eye(6)
    y, predicted = rng.normal(size=(2, 6))
    t = flux_path_transform(3)
    pathcov = t@c@t.T
    assert_allclose(np.linalg.det(t), 1)
    assert_allclose(np.linalg.solve(t, t@y), y)
    q = (y-predicted)@np.linalg.solve(c, y-predicted)
    qp = (t@(y-predicted))@np.linalg.solve(pathcov, t@(y-predicted))
    assert_allclose(q, qp)
    assert np.max(np.abs(pathcov-np.diag(np.diag(pathcov)))) > .1
    views = gaussian_five_views(y, c, predicted)
    assert_allclose(views['Pi']['wald'], q)
    assert views['independent_factors'] is False


def test_gaussian_support_rotates_with_state_and_covariance():
    e, _ = experiment()
    fit = fit_joint([e])
    c, y = fit['covariance'], fit['estimate']
    a = .62
    rot = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    one = gaussian_five_views(y, c)
    two = gaussian_five_views(rot@y, rot@c@rot.T)
    assert_allclose(one['Q']['gauge'], two['Q']['gauge'])


@pytest.mark.parametrize('bad', [-1, .5, float('nan')])
def test_bad_counts_rejected(bad):
    e, _ = experiment()
    counts = e.counts.copy()
    counts[0] = bad
    with pytest.raises(ValueError):
        RingLikelihood(counts, e.features, e.groups)


def test_invalid_exposure_and_maps_rejected():
    e, _ = experiment()
    with pytest.raises(ValueError):
        RingLikelihood(e.counts, e.features, e.groups, np.zeros_like(e.counts))
    with pytest.raises(ValueError):
        fit_joint([e], maps=[np.zeros((2, 1))])
    with pytest.raises(ValueError):
        nested_lr(0, 10, 2)
