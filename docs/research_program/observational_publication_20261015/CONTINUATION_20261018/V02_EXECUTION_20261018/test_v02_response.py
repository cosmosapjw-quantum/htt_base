"""Narrow falsifiers of the declared finite-sector counterfactual."""
import numpy as np
import pytest

from v02_response import (beam_layout, defined_source, design, finite_modes,
                          fit_operator, nuisance_projected_response,
                          pullback_points, sphere_rule)


def test_exact_inverse_direction_and_doppler_product():
    n, _ = sphere_rule(10)
    b = np.array([.11, -.07, .04])
    source, d = pullback_points(n, b)
    back, inverse_d = pullback_points(source, -b)
    np.testing.assert_allclose(back, n, atol=8*np.finfo(float).eps, rtol=0)
    np.testing.assert_allclose(d*inverse_d, 1., atol=8*np.finfo(float).eps, rtol=0)


def test_constant_perturbation_has_positive_boost_dipole():
    n, w = sphere_rule(24)
    y = design(n, 8)
    a = np.zeros((36, 1)); a[0] = np.sqrt(4*np.pi)
    b = .001
    boosted = finite_modes(a, [0., 0., b], n, w, y)
    # Outward +z gets hotter; real Y_10=sqrt(3/4pi)*z.
    np.testing.assert_allclose(boosted[1, 0]/b, np.sqrt(4*np.pi/3), rtol=2e-6)
    # D=1+b*z+b²*(z²-1/2)+O(b³) gives this known quadrupole coefficient.
    np.testing.assert_allclose(boosted[4, 0]/b**2, np.sqrt(16*np.pi/45), rtol=3e-6)


def test_actual_projector_equals_nuisance_quotient_and_kills_nuisance():
    n, _ = sphere_rule(12); y = design(n, 5)
    mask = n[:, 2] > -.3
    op = fit_operator(y, mask)
    rng = np.random.default_rng(92)
    g = rng.normal(size=(mask.sum(), 3))
    fwl, residual = nuisance_projected_response(y, mask, g)
    # Forward-error allowance includes the deliberately difficult cap-mask condition.
    tolerance = 128*np.finfo(float).eps*np.linalg.cond(y[mask])*np.linalg.norm(g, 2)
    np.testing.assert_allclose(fwl, op[4:]@g, atol=tolerance, rtol=0)
    np.testing.assert_allclose(y[mask, :4].T@residual, 0., atol=1e-12, rtol=0)
    np.testing.assert_allclose(op[4:]@y[mask, :4], 0., atol=2e-11, rtol=0)


def test_beam_once_and_mode_leakage_are_not_commuted():
    n, w = sphere_rule(28); y = design(n, 12)
    beam = np.exp(-.03*np.arange(13)*(np.arange(13)+1))
    beam[:2] = 0  # actual delivered table also zeros these entries
    retained = np.zeros((32, 1)); retained[-1] = 1.
    source = defined_source(retained, beam)
    b = np.array([.002, -.003, .001])
    correct = beam_layout(beam, 12)[:, None]*finite_modes(source, b, n, w, y)
    delivered = source*beam_layout(beam, 5)[:, None]
    wrong = finite_modes(delivered, b, n, w, y)
    assert np.linalg.norm(correct[36:]) > 1e-4
    assert np.linalg.norm(correct-wrong) > 1e-4
    zero = beam_layout(beam, 12)[:, None]*finite_modes(source, [0, 0, 0], n, w, y)
    np.testing.assert_allclose(zero[4:36], retained, atol=1e-13, rtol=0)
    assert np.linalg.norm(zero[36:]) < 1e-13


@pytest.mark.parametrize("b", [[1, 0, 0], [np.nan, 0, 0], [0, 0]])
def test_invalid_boost_fails_closed(b):
    n, _ = sphere_rule(3)
    with pytest.raises(ValueError): pullback_points(n, b)


def test_missing_beam_sector_is_not_zero_filled():
    with pytest.raises(ValueError): defined_source(np.ones((32, 1)), np.zeros(6))
