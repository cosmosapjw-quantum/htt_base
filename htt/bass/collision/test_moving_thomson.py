"""Unit tests for covariant moving electron-frame Thomson collision (N2)."""
from __future__ import annotations

import numpy as np
from numpy.testing import assert_allclose
import pytest

from bass.collision.coherency import ThomsonCoherencyPropagator
from bass.collision.moving_thomson import (
    MovingFrameThomsonOperator,
    boost_photon_and_screen,
    covariant_thomson_four_force,
    radiation_stress_tensor_4d,
)
from bass.transport.general_bianchi_transfer import _spherical_screen_basis, gl_sphere_grid
from common.relativistic_velocity_closure import compose_and_close_velocities


def test_zero_velocity_reduces_to_coherency_propagator() -> None:
    op = MovingFrameThomsonOperator([0.0, 0.0, 0.0], n_theta_rest=8)
    _, _, d, w = gl_sphere_grid(8)
    n_flat = d.reshape(-1, 3)
    u, v = _spherical_screen_basis(n_flat)
    ref = ThomsonCoherencyPropagator(n_flat, w.ravel(), u, v)

    rng = np.random.default_rng(10203)
    sky = np.abs(rng.normal(size=(len(n_flat), 4))) + 1.0
    sky[:, 1:] *= 0.1
    assert_allclose(op.collision_bolometric(sky, clock="rest_time"), ref.collision(sky), atol=1e-14)
    assert_allclose(op.collision_bolometric(sky, clock="conserved_anchor"), ref.collision(sky), atol=1e-14)


def test_boosted_blackbody_equilibrium_and_relativistic_4force() -> None:
    beta = np.array([0.28, -0.31, 0.19])  # |beta| ~ 0.459
    op = MovingFrameThomsonOperator(beta, n_theta_rest=10)

    # Exact blackbody in electron rest frame is exact fixed point of moving collision
    eq = op.bolometric_equilibrium_sky(I0_rest=1.7)
    coll_eq = op.collision_bolometric(eq, clock="rest_time")
    assert_allclose(coll_eq, 0.0, atol=1e-13)
    f_eq = op.four_force(eq, clock="rest_time")
    assert float(np.linalg.norm(f_eq["F_angular_4d"])) < 1e-12
    assert float(np.linalg.norm(f_eq["F_covariant_4d"])) < 1e-12

    # Arbitrary polarized anisotropic radiation field: exact 4-force conservation u_b . F == 0
    rng = np.random.default_rng(10204)
    n = op.directions_normal
    sky = np.zeros_like(eq)
    sky[:, 0] = 2.0 + 0.4 * n[:, 0] - 0.3 * (n[:, 1] ** 2 - n[:, 2] ** 2) + 0.1 * n[:, 2] ** 3
    sky[:, 1] = 0.05 * (n[:, 0] * n[:, 1])
    sky[:, 2] = -0.04 * (n[:, 0] * n[:, 2])
    sky[:, 3] = 0.03 * n[:, 1]

    f_res = op.four_force(sky, clock="rest_time")
    assert f_res["orthogonality_ub_dot_F_ang"] < 1e-13
    assert f_res["orthogonality_ub_dot_F_cov"] < 1e-13
    assert f_res["rel_diff"] < 1e-12

    # Conserved-anchor clock scales by 1/Gamma
    f_anch = op.four_force(sky, clock="conserved_anchor")
    assert_allclose(f_anch["F_angular_4d"], f_res["F_angular_4d"] / op.gamma, rtol=1e-13, atol=1e-14)
    assert f_anch["rel_diff"] < 1e-12


def test_finite_lorentz_composition_and_wigner_screen_rotation() -> None:
    beta1 = np.array([0.35, 0.12, -0.08])
    beta2 = np.array([-0.15, 0.28, 0.14])
    closure = compose_and_close_velocities(-beta2, beta1)
    # Wait: check compose_and_close_velocities(beta_RM, beta_MO) ordering:
    # We compose L = Lambda(-beta2) @ Lambda(-beta1). From wigner_rotation:
    # B(b1) @ B(b2) = B(b12) @ R4, where L1 = lorentz_boost(b1).
    # Here we boost by (-beta1) then (-beta2), so L = B(-beta2) @ B(-beta1) = B(b_comp) @ R_4:
    from common.relativistic_velocity_closure import compose_velocities_sr, wigner_rotation
    from common.relativistic_kinematics import lorentz_boost

    b_comp = compose_velocities_sr(-beta2, -beta1)
    R_w, _, _ = wigner_rotation(-beta2, -beta1, beta_composed=b_comp)
    assert_allclose(lorentz_boost(-beta2) @ lorentz_boost(-beta1), lorentz_boost(b_comp) @ np.block([[np.ones((1, 1)), np.zeros((1, 3))], [np.zeros((3, 1)), R_w]]), atol=1e-13)

    _, _, d, _ = gl_sphere_grid(8)
    n0 = d.reshape(-1, 3)
    u0, v0 = _spherical_screen_basis(n0)
    # Two-step boost: n0 -> (step 1: beta1) -> n1 -> (step 2: beta2) -> n2
    g1 = boost_photon_and_screen(n0, beta1, basis_u=u0, basis_v=v0)
    g2 = boost_photon_and_screen(g1.directions_rest, beta2, basis_u=g1.basis_u_rest, basis_v=g1.basis_v_rest)
    # Single composed boost Lambda(b_comp) @ diag(1, R_w) == Lambda(-(-b_comp)):
    # Since g_comp boosts by (-b_comp) after rotating input triad by R_w:
    g_single = boost_photon_and_screen(n0 @ R_w.T, -b_comp, basis_u=u0 @ R_w.T, basis_v=v0 @ R_w.T)

    assert_allclose(g2.directions_rest, g_single.directions_rest, atol=1e-12)
    assert_allclose(g1.doppler_D * g2.doppler_D, g_single.doppler_D, rtol=1e-12)
    assert_allclose(g2.basis_u_rest, g_single.basis_u_rest, atol=1e-12)
    assert_allclose(g2.basis_v_rest, g_single.basis_v_rest, atol=1e-12)


def test_scatter_in_redistribution_not_uniform_ray_scaling() -> None:
    beta = np.array([0.0, 0.0, 0.25])
    op = MovingFrameThomsonOperator(beta, n_theta_rest=8)
    _, emission = op.linearized_perturbation_and_emission(np.zeros((len(op.directions_normal), 4)), clock="conserved_anchor")
    # Unpolarized isotropic input I_0 = 0.25 MUST produce nonzero kinetic dipole and quadrupole Q_0 != 0
    # Wait: if one mistakenly scaled static G'(I0) - I0 = 0 by (1 - beta.n), emission would be IDENTICALLY ZERO!
    # Our covariant redistribution gives O(|beta|) dipole + O(beta^2) Q polarization!
    I_rms = float(np.sqrt(np.mean(emission[:, 0] ** 2)))
    Q_rms = float(np.sqrt(np.mean(emission[:, 1] ** 2)))
    assert I_rms > 0.1 * np.linalg.norm(beta)
    assert Q_rms > 1e-4
