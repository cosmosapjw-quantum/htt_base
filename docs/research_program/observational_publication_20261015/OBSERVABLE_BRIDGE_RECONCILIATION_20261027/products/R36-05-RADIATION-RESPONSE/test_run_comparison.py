"""Preproduction falsifiers for the frozen conditional consumer."""

import numpy as np

from radiation_core import STF_BASIS, moments, sphere_rule
from run_comparison import (C_THETA, analyze_moments, boost, chart,
                            check_polynomial, feature_matrix, moment_operator,
                            polynomial_adapter, tensor_moment_vector, truth_sky)


def test_lorentz_temperature_tensors_and_polynomial_adapter():
    n, weights = sphere_rule(36, 73)
    t, analytic = truth_sky(n, .02, .3)
    actual = moments(n, weights, t ** 4, 1).stress
    assert np.max(abs(actual - analytic)) < 2e-12
    tbar, _, d, q = chart(n, weights, t)
    assert np.isfinite(np.r_[tbar, d, q]).all()
    features = feature_matrix(n)
    coefficients, monomials = polynomial_adapter(
        t, tbar, features, moment_operator(n, weights))
    assert len(monomials) == 495
    assert check_polynomial(t, tbar, features, moment_operator(n, weights),
                            coefficients, monomials) < 2e-12
    read = analyze_moments(tensor_moment_vector(analytic)[None, :])
    assert read["valid"][0]
    assert abs(read["A"][0] - np.sqrt(6) * .02 / 15) < 2e-12


def test_physical_guard_rejects_large_flux_and_zero_density():
    bad = np.zeros((2, 9))
    bad[0, 0] = 1
    bad[0, 1] = 2
    result = analyze_moments(bad)
    assert not result["valid"].any()
    assert np.isnan(result["A"][1])


def test_rotation_transports_noise_covariance_and_tensor_targets():
    angle = .37
    rotation = np.array([[np.cos(angle), -np.sin(angle), 0],
                         [np.sin(angle), np.cos(angle), 0], [0, 0, 1]])
    transform = np.zeros((8, 8))
    transform[:3, :3] = rotation
    for a, ea in enumerate(STF_BASIS):
        for b, eb in enumerate(STF_BASIS):
            transform[3 + a, 3 + b] = np.sum(ea * (rotation @ eb @ rotation.T))
    assert np.linalg.norm(transform @ transform.T - np.eye(8)) < 1e-13
    rotated_covariance = transform @ C_THETA @ transform.T
    assert np.linalg.eigvalsh(rotated_covariance).min() > 0
    eta = np.array([1., -2., .5, .7, -1., .2, 1.3, -.6]) * 1e-5
    eta_r = transform @ eta
    q = np.einsum("a,aij->ij", eta[3:], STF_BASIS)
    q_r = np.einsum("a,aij->ij", eta_r[3:], STF_BASIS)
    assert np.linalg.norm(q_r - rotation @ q @ rotation.T) < 1e-18
    assert np.linalg.norm(eta_r[:3] - rotation @ eta[:3]) < 1e-18
    n, weights = sphere_rule(36, 73)
    t, _ = truth_sky(n, .02, .3)
    t_rot, _ = truth_sky(n @ rotation, .02, .3)
    perturb = feature_matrix(n) @ eta
    perturb_rot = feature_matrix(n) @ eta_r
    tbar = weights @ t
    tbar_rot = weights @ t_rot
    assert abs(tbar - tbar_rot) < 1e-14
    m = moments(n, weights, (t + tbar * perturb) ** 4, 1)
    m_rot = moments(n, weights, (t_rot + tbar_rot * perturb_rot) ** 4, 1)
    rot4 = np.eye(4)
    rot4[1:, 1:] = rotation
    assert np.max(abs(m_rot.stress - rot4 @ m.stress @ rot4.T)) < 2e-12
    r0 = analyze_moments(tensor_moment_vector(m.stress)[None, :])
    r1 = analyze_moments(tensor_moment_vector(m_rot.stress)[None, :])
    d0 = np.einsum("a,aij->ij", r0["D"][0], STF_BASIS)
    d1 = np.einsum("a,aij->ij", r1["D"][0], STF_BASIS)
    assert np.linalg.norm(d1 - rotation @ d0 @ rotation.T) < 2e-12
    assert abs(r0["A"][0] - r1["A"][0]) < 2e-12
