"""Falsifiers for the physical core; no statistical experiment."""

import numpy as np
from numpy.polynomial.legendre import legval

from radiation_core import (Moments, coercivity_diagnostic,
                            linear_temperature_quadrupole, moments,
                            response_direct, response_from_moments,
                            sphere_rule, stress_readout, stf2,
                            temperature_brightness)


def test_exact_boost_null_and_landau_invariance():
    b = 0.21
    v = np.array([0.6 * b, 0.0, 0.8 * b])
    gamma = 1 / np.sqrt(1 - b * b)
    transform = np.eye(4)
    transform[0, 0] = gamma
    transform[0, 1:] = transform[1:, 0] = gamma * v
    transform[1:, 1:] += (gamma - 1) * np.outer(v, v) / (b * b)
    for a in (0.0, 0.02):
        rest = np.diag([1.0, 1 / 3 - a / 15, 1 / 3 - a / 15,
                        1 / 3 + 2 * a / 15])
        t = transform @ rest @ transform.T
        fake = Moments(float(t[0, 0]), 299792458.0 * t[0, 1:],
                       stf2(t[1:, 1:]), np.zeros((3,) * 4), t)
        read = stress_readout(fake)
        assert abs(read["A_gamma"] - np.sqrt(6) * abs(a) / 15) < 3e-14
        if a == 0:
            assert read["D_norm"] < 3e-14


def test_positive_moment_cone_and_quadratic_temperature_error():
    n, weights = sphere_rule()
    q = stf2(np.array([[0.11, 0.03, 0], [0.03, -0.03, 0], [0, 0, -0.08]]))
    theta = n @ np.array([0.12, -0.03, 0.08]) + np.einsum(
        "ni,ij,nj->n", n, q, n)
    m = moments(n, weights, temperature_brightness(theta), rho0=2.0)
    assert np.linalg.eigvalsh(m.stress[1:, 1:]).min() > 0
    assert np.linalg.norm(stress_readout(m)["P"]
                          - linear_temperature_quadrupole(q)) > 1e-3
    try:
        moments(n, weights, -np.ones(len(n)), rho0=2.0)
    except ValueError:
        pass
    else:
        raise AssertionError("negative brightness entered physical cone")


def test_rank_four_matching_preserves_full_response_with_higher_moment():
    n, weights = sphere_rule(36, 24)
    mu = n[:, 2]
    w1 = legval(mu, [1, 0, 0.3, 0, 0.2, 0, 0.15])
    w2 = legval(mu, [1, 0, 0.3, 0, 0.2, 0, 0.25])
    w_l2 = legval(mu, [1, 0, 0.3])
    m1 = moments(n, weights, w1, 1.0)
    m2 = moments(n, weights, w2, 1.0)
    assert np.linalg.norm(m1.pi - m2.pi) < 1e-14
    assert np.linalg.norm(m1.h4 - m2.h4) < 1e-14
    r1, r2 = response_from_moments(m1), response_from_moments(m2)
    assert np.linalg.norm(r1 - r2, ord=2) < 1e-13
    assert np.linalg.norm(r1 - response_direct(n, weights, w1, 1), ord=2) < 1e-13
    assert np.linalg.norm(r1 - response_from_moments(
        moments(n, weights, w_l2, 1)), ord=2) > 1e-3
    assert np.linalg.eigvalsh(r1).min() > 0


def test_failed_entropy_sufficiency_triggers_actual_spectrum():
    n, weights = sphere_rule(64, 24)
    raw = np.exp(20 * n[:, 2] ** 2)
    brightness = raw / (weights @ raw)
    m = moments(n, weights, brightness, 1.0)
    d = coercivity_diagnostic(weights, brightness,
                             response_from_moments(m), m.rho)
    assert not d["sufficient_certificate_pass"]
    assert d["actual_positive"]
    assert d["actual_lambda_min_over_rho"] > 0
