"""Independent small-matrix falsifiers for R58's Gaussian carrier contract."""
from pathlib import Path
import importlib.util
import math

import numpy as np
import pytest
from scipy import stats


# Works in a complete repo and in the small review patch without modifying a
# production import path or copying the parent repository.
ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "r58_mixed_tensor_likelihood", ROOT / "htt/htt/htt/infer/r58_mixed_tensor_likelihood.py")
mt = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mt)


def experiment():
    rng = np.random.default_rng(20261117)
    x = rng.normal(size=(9, 4))
    a = rng.normal(size=(9, 9))
    c = a @ a.T + 0.8 * np.eye(9)
    y = rng.normal(size=9)
    return y, c, x


def test_direct_gls_and_absolute_likelihood():
    y, c, x = experiment()
    f = mt.fit_linear(y, c, x, [100, .01, 2, .1])
    invc = np.linalg.inv(c)
    j = x.T @ invc @ x
    expected_cov = np.linalg.inv(j)
    expected_mean = expected_cov @ x.T @ invc @ y
    np.testing.assert_allclose(f["estimate"], expected_mean, rtol=2e-11, atol=2e-12)
    np.testing.assert_allclose(f["covariance"], expected_cov, rtol=2e-11, atol=2e-12)
    np.testing.assert_allclose(f["precision"], j, rtol=2e-12, atol=2e-12)
    assert f["rank"] == 4 and f["dof"] == 5
    np.testing.assert_allclose(f["residual_chi2"], (y - x @ expected_mean) @ invc @ (y - x @ expected_mean), rtol=2e-11)
    for theta in (expected_mean, np.zeros(4), np.array([1., -2., 3., 4.])):
        direct = stats.multivariate_normal.logpdf(y, mean=x @ theta, cov=c)
        assert mt.gaussian_log_likelihood(f, theta) == pytest.approx(direct, rel=3e-12, abs=3e-12)
        minimal = {key: value for key, value in f.items() if not key.startswith("_")}
        assert mt.gaussian_log_likelihood(minimal, theta) == pytest.approx(direct, rel=3e-12, abs=3e-12)
    assert f["q0"] == pytest.approx(y @ invc @ y)
    assert f["logdet_cov"] == pytest.approx(np.linalg.slogdet(c)[1])


def test_mixed_units_and_change_of_parameter_chart():
    y, c, x = experiment()
    reference = mt.fit_linear(y, c, x)
    scales = np.array([1e9, 1e-8, 5e3, 2e-4])
    # theta = diag(scales) phi; covariance transforms as a tensor, not a scalar.
    f = mt.fit_linear(y, c, x * scales, 1 / scales)
    np.testing.assert_allclose(scales * f["estimate"], reference["estimate"], rtol=3e-12, atol=3e-12)
    np.testing.assert_allclose(scales[:, None] * f["covariance"] * scales[None, :], reference["covariance"], rtol=3e-12, atol=3e-12)
    rng = np.random.default_rng(6)
    rotation = np.linalg.qr(rng.normal(size=(4, 4)))[0]
    rotated = mt.fit_linear(y, c, x @ rotation)
    contrast = np.array([.2, -.5, 1., .7])
    a = mt.linear_interval(reference, contrast)
    b = mt.linear_interval(rotated, rotation.T @ contrast)
    assert a["lower"] == pytest.approx(b["lower"], rel=1e-12)
    assert a["upper"] == pytest.approx(b["upper"], rel=1e-12)


def test_full_cross_covariance_changes_mixed_contrasts():
    # Exact two-row independent oracle: Var((y1 +/- y2)/2)=(1 +/- rho)/2.
    rho = .8
    c = np.array([[1., rho], [rho, 1.]])
    x = np.array([[1., 1.], [1., -1.]])
    f = mt.fit_linear([2., -1.], c, x)
    ablated = mt.fit_linear([2., -1.], np.eye(2), x)
    np.testing.assert_allclose(f["covariance"], np.diag([.9, .1]), atol=1e-14)
    np.testing.assert_allclose(ablated["covariance"], .5 * np.eye(2), atol=1e-14)
    # Dropping cross covariance can inflate one direction and shrink another;
    # it is not uniformly conservative, despite matching diagonal variances.
    assert mt.linear_interval(f, [1, 0])["sd"] > mt.linear_interval(ablated, [1, 0])["sd"]
    assert mt.linear_interval(f, [0, 1])["sd"] < mt.linear_interval(ablated, [0, 1])["sd"]


def test_rank_deficiency_keeps_unbounded_directions_and_mixed_identified_target():
    x = np.array([[1., 1., 0.], [2., 2., 0.], [-1., -1., 0.]])
    f = mt.fit_linear([1., 3., -2.], np.eye(3), x, [1000, .001, 2])
    assert f["rank"] == 1 and f["null_basis"].shape == (3, 2)
    np.testing.assert_allclose(x @ f["null_basis"], 0, atol=1e-12)
    identified = mt.linear_interval(f, [1, 1, 0])
    assert identified["identified"]
    assert identified["estimate"] == pytest.approx(1.5)
    assert identified["sd"] == pytest.approx(1 / math.sqrt(6))
    for contrast in ([1, -1, 0], [0, 0, 1]):
        interval = mt.linear_interval(f, contrast)
        assert not interval["identified"]
        assert interval["lower"] == -math.inf and interval["upper"] == math.inf
        assert interval["estimate"] is None
    # Moving far along an exactly unidentified direction does not change L.
    a = mt.gaussian_log_likelihood(f, [0., 2., 0.])
    b = mt.gaussian_log_likelihood(f, [4., -2., 99.])
    assert a == pytest.approx(b, abs=1e-11)


def test_wide_design_has_full_null_basis():
    f = mt.fit_linear([1., 2.], np.eye(2), [[1, 0, 1, 0], [0, 1, 0, 1]])
    assert f["rank"] == 2 and f["null_basis"].shape == (4, 2)
    assert f["adequacy_p"] is None
    assert mt.linear_interval(f, [1, 0, 1, 0])["identified"]
    assert not mt.linear_interval(f, [1, 0, 0, 0])["identified"]


def test_unit_scale_cannot_hide_nonzero_null_projection():
    f = mt.fit_linear([1.], [[1.]], [[1., 1.]], [1e9, 1e-9])
    assert not mt.linear_interval(f, [1., 0.])["identified"]
    assert not mt.linear_interval(f, [0., 1.])["identified"]
    assert mt.linear_interval(f, [1., 1.])["identified"]


def test_roundoff_null_entry_does_not_erase_identified_component():
    # theta1=y1-y2 is exactly estimable, while theta2-theta3 is not.
    # A floating SVD has a spurious ~7e-17 entry in its null vector's first
    # component; testing that entry against itself falsely yields infinity.
    x = np.array([[1., 1., 1.], [0., 1., 1.]])
    f = mt.fit_linear([0., 0.], np.eye(2), x)
    interval = mt.linear_interval(f, [1., 0., 0.], simultaneous=False)
    assert interval["identified"]
    assert interval["sd"] == pytest.approx(math.sqrt(2))
    assert not mt.linear_interval(f, [0., 1., -1.])["identified"]
    # A genuine unit change transforms design and target covector together.
    unit = np.array([1e9, 1e-8, 1e3])
    changed = mt.fit_linear([0., 0.], np.eye(2), x * unit, 1 / unit)
    shifted = mt.linear_interval(changed, np.array([1., 0., 0.]) * unit, simultaneous=False)
    assert shifted["identified"]
    assert shifted["sd"] == pytest.approx(math.sqrt(2))


def test_rank_deficient_rotations_preserve_identified_mixed_target():
    x = np.array([[1., 1., 1.], [0., 1., 1.]])
    rng = np.random.default_rng(31415)
    for _ in range(12):
        rotation = np.linalg.qr(rng.normal(size=(3, 3)))[0]
        rotated = mt.fit_linear([1., -1.], np.eye(2), x @ rotation)
        identified = mt.linear_interval(rotated, rotation.T @ [1., 0., 0.])
        assert identified["identified"]
        assert identified["estimate"] == pytest.approx(2.)
        assert identified["sd"] == pytest.approx(math.sqrt(2))
        assert not mt.linear_interval(rotated, rotation.T @ [0., 1., -1.])["identified"]


def test_disagreeing_numerical_ranks_fail_closed_before_calibrated_tests():
    # The caller's scale drops a nonzero mode; column equilibration retains it.
    with pytest.raises(ValueError, match="numerically unresolved rank disagreement"):
        mt.fit_linear([0., 0.], np.eye(2), np.diag([1., 1e-14]))


def test_likelihood_is_stable_far_along_a_singular_null_direction():
    rng = np.random.default_rng(777)
    x = rng.normal(size=(8, 2)) @ rng.normal(size=(2, 3))
    y = rng.normal(size=8)
    f = mt.fit_linear(y, np.eye(8), x)
    for size in (1e8, 1e10):
        theta = f["estimate"] + size * f["null_basis"][:, 0]
        direct = stats.multivariate_normal.logpdf(y, mean=x @ theta, cov=np.eye(8))
        # Solving for xw changes memory layout and BLAS summation order even
        # for C=I. The allowable residual error is linear in ||theta||, not
        # the catastrophic quadratic cancellation of theta.T J theta.
        rounding_budget = 16 * np.finfo(float).eps * np.linalg.norm(x, np.inf) * np.linalg.norm(theta, np.inf) * (np.linalg.norm(y - x @ theta, 1) + 1)
        assert mt.gaussian_log_likelihood(f, theta) == pytest.approx(direct, rel=0, abs=rounding_budget)
        assert mt.gaussian_log_likelihood(f, theta) <= -4 * math.log(2 * math.pi)
    minimal = {k: v for k, v in f.items() if k not in ("likelihood_factor", "likelihood_offset")}
    with pytest.raises(ValueError, match="singular carrier requires"):
        mt.gaussian_log_likelihood(minimal, theta)


def test_zero_design_and_zero_contrast():
    f = mt.fit_linear([2., 3.], np.eye(2), np.zeros((2, 3)))
    assert f["rank"] == 0 and f["wald_p"] == 1
    assert f["null_chi2"] == 13 and f["residual_chi2"] == 13
    assert f["null_basis"].shape == (3, 3)
    assert not mt.linear_interval(f, [0, 1, 0])["identified"]
    zero = mt.linear_interval(f, [0, 0, 0])
    assert zero["identified"] and zero["lower"] == zero["upper"] == 0


def test_common_cylinder_versus_pointwise_radius():
    f = mt.fit_linear([0., 0., 0.], np.eye(3), np.eye(3))
    simultaneous = mt.linear_interval(f, [1, 0, 0])
    pointwise = mt.linear_interval(f, [1, 0, 0], simultaneous=False)
    assert simultaneous["upper"] == pytest.approx(math.sqrt(stats.chi2.ppf(.95, 3)))
    assert pointwise["upper"] == pytest.approx(stats.norm.ppf(.975))


def test_union_interval_is_union_not_intersection_or_independent_product():
    f1 = mt.fit_linear([2.], [[1.]], [[1.]])
    f2 = mt.fit_linear([-3.], [[4.]], [[1.]])
    u = mt.robust_interval([f1, f2], [1])
    assert u["lower"] == pytest.approx(-3 - 2 * stats.norm.ppf(.975))
    assert u["upper"] == pytest.approx(2 + stats.norm.ppf(.975))
    assert mt.robust_null_p([f1, f2], same_hypothesis=True) == max(f1["null_p"], f2["null_p"])
    unident = mt.fit_linear([1.], [[1.]], [[0.]])
    ub = mt.robust_interval([f1, unident], [1])
    assert not ub["identified_in_all_models"] and math.isinf(ub["upper"])
    with pytest.raises(ValueError, match="explicitly affirmed"):
        mt.robust_null_p([f1, f2], same_hypothesis=False)


@pytest.mark.parametrize("c", [np.array([[1., .2], [.1, 1.]]), np.ones((2, 2)), np.diag([1., -1.]), np.zeros((2, 2)), np.array([[1., np.nan], [np.nan, 1.]])])
def test_bad_covariance_fails(c):
    with pytest.raises(ValueError):
        mt.fit_linear([0, 0], c, np.eye(2))


@pytest.mark.parametrize("scale", [[1, 0], [1, -2], [1, np.inf], [1], [[1], [1]]])
def test_bad_scales_fail(scale):
    with pytest.raises(ValueError):
        mt.fit_linear([0, 0], np.eye(2), np.eye(2), scale)


def test_invalid_inputs_and_probability_contracts():
    with pytest.raises(ValueError):
        mt.fit_linear([np.nan], [[1]], [[1]])
    with pytest.raises(ValueError):
        mt.fit_linear([1, 2], [[1]], [[1], [2]])
    with pytest.raises(ValueError):
        mt.fit_linear([1], [[1]], [[np.inf]])
    f = mt.fit_linear([1], [[1]], [[1]])
    for level in (0, 1, np.nan):
        with pytest.raises(ValueError):
            mt.linear_interval(f, [1], level)
    with pytest.raises(ValueError):
        mt.linear_interval(f, [1, 2])
    with pytest.raises(ValueError):
        mt.gaussian_log_likelihood(f, [1, 2])
    with pytest.raises(ValueError):
        mt.robust_interval([], [1])
    with pytest.raises(ValueError):
        mt.robust_null_p([], same_hypothesis=True)
    with pytest.raises(ValueError):
        mt.robust_null_p([{"null_p": np.nan}], same_hypothesis=True)


def test_scalar_norm_loses_signed_target_likelihood():
    # Equal scalar amplitudes do not encode the orientation of a vector/tensor.
    f = mt.fit_linear([2., 0.], [[1., .3], [.3, 1.]], np.eye(2))
    a, b = np.array([2., 0.]), np.array([0., 2.])
    assert np.linalg.norm(a) == np.linalg.norm(b)
    assert mt.gaussian_log_likelihood(f, a) > mt.gaussian_log_likelihood(f, b)
