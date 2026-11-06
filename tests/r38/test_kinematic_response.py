"""Unit tests for frame-aware kinematic and shear response.

Phase C of HTT-R38 Observational Convergence.
Tests frame decomposition, relativistic composition, superluminal bounds,
basis normalization, and carrier separation.
"""
from __future__ import annotations

import math
import numpy as np
import pytest

from common.kinematic_response import (
    KinematicFrameState,
    KinematicResponseModel,
    STF_BASIS,
    compose_velocities,
    KinematicsError,
    BetaTruncationError,
)

def test_stf_basis_orthonormality():
    # Verify Frobenius orthonormality: Tr(E_a E_b) = delta_ab
    gram = np.einsum("aij,bij->ab", STF_BASIS, STF_BASIS)
    assert np.allclose(gram, np.eye(5), atol=1e-14)
    # Verify each basis matrix is symmetric and traceless
    for a in range(5):
        E_a = STF_BASIS[a]
        assert np.allclose(E_a, E_a.T, atol=1e-14)
        assert math.isclose(float(np.trace(E_a)), 0.0, abs_tol=1e-14)


def test_velocity_composition():
    # Collinear velocities: 0.1c and 0.05c
    v1 = np.array([0.1, 0.0, 0.0])
    v2 = np.array([0.05, 0.0, 0.0])
    v_rel = compose_velocities(v1, v2)
    # Expected: (0.1 - 0.05) / (1 - 0.1*0.05) = 0.05 / 0.995 = 0.05025125...
    expected = (0.1 - 0.05) / (1.0 - 0.005)
    assert math.isclose(v_rel[0], expected, rel_tol=1e-10)

    # Superluminal rejection
    v_lum = np.array([1.0, 0.0, 0.0])
    with pytest.raises(BetaTruncationError, match="strictly subluminal"):
        compose_velocities(v_lum, v2)


def test_velocity_composition_non_collinear_exact():
    # Both velocities are measured in the same inertial frame. The result is
    # the velocity of A as measured in B's standard-boost axes.
    v_a = np.array([0.3, 0.0, 0.0])
    v_b = np.array([0.0, 0.4, 0.0])
    expected = np.array([0.3 * math.sqrt(1.0 - 0.4**2), -0.4, 0.0])
    actual = compose_velocities(v_a, v_b)
    assert np.allclose(actual, expected, rtol=1e-13, atol=1e-14)
    assert float(np.linalg.norm(actual)) < 1.0

    # Limiting cases: B at rest, and A at rest in the common frame.
    assert np.allclose(compose_velocities(v_a, np.zeros(3)), v_a)
    assert np.allclose(compose_velocities(np.zeros(3), v_b), -v_b)


def test_velocity_composition_small_beta_limit_is_stable():
    # The gamma-1 cancellation must not erase the transverse correction.
    v_a = np.array([0.0, 0.3, 0.0])
    v_b = np.array([1.0e-8, 0.0, 0.0])
    actual = compose_velocities(v_a, v_b)
    assert np.allclose(actual, [-1.0e-8, 0.3, 0.0], rtol=0.0, atol=1.0e-15)

def test_velocity_composition_rejects_nonfinite_inputs():
    with pytest.raises(KinematicsError, match="finite"):
        compose_velocities(np.array([np.nan, 0.0, 0.0]), np.zeros(3))

def test_kinematic_response_model():
    # Initialize with observer boost 0.00123 (approx CMB dipole speed ~ 369 km/s)
    bro = [0.00123, 0.0, 0.0]
    brm = [0.00020, 0.0, 0.0]
    dint = [0.00005, 0.0, 0.0]
    model = KinematicResponseModel.from_parameters(
        beta_RO=bro, beta_RM=brm, d_int=dint
    )
    
    # Matter-observer velocity: 0.00123 - 0.00020 = 0.00103
    assert np.allclose(model.state.beta_MO, [0.00103, 0.0, 0.0])
    
    # Direction along +x
    n_x = np.array([[1.0, 0.0, 0.0]])
    # CMB dipole along +x: beta_RO + d_int = 0.00123 + 0.00005 = 0.00128
    dip_x = model.cmb_temperature_dipole(n_x)
    assert math.isclose(dip_x[0], 0.00128, rel_tol=1e-12)

    # Direction along +y (orthogonal) -> 0.0
    n_y = np.array([[0.0, 1.0, 0.0]])
    dip_y = model.cmb_temperature_dipole(n_y)
    assert math.isclose(dip_y[0], 0.0, abs_tol=1e-14)

    # Second-order kinetic quadrupole along +x:
    # Q_kin = 0.5 * ( (n.beta)^2 - 1/3 beta^2 ) = 0.5 * (2/3 * beta^2) = (1/3) * beta^2
    qkin_x = model.cmb_kinetic_quadrupole(n_x)
    expected_qkin_x = (1.0 / 3.0) * (0.00123 ** 2)
    assert math.isclose(qkin_x[0], expected_qkin_x, rel_tol=1e-12)

    # Matter count dipole: [2 + 0.75*(1 + 1)] * beta_MO = 3.5 * 0.00103 = 0.003605
    count_dip = model.matter_count_dipole(n_x, spectral_index=0.75, flux_slope=1.0)
    assert math.isclose(count_dip[0], 3.5 * 0.00103, rel_tol=1e-12)


def test_carrier_separation():
    # E1/B1 polar/axial carrier vs E2/STF shear
    model = KinematicResponseModel.from_parameters(
        beta_RO=[0.001, 0.0, 0.0],
        stf_shear=[1e-5, -2e-5, 0.0, 0.0, 0.0],
        e1_polar=[1e-6, 0.0, 0.0],
        b1_axial=[0.0, 1e-6, 0.0],
    )
    assert model.state.stf_shear_amplitudes.shape == (5,)
    assert model.state.e1_polar_vector.shape == (3,)
    assert model.state.b1_axial_vector.shape == (3,)
    # Verify that E1 and STF are maintained as distinct tensors
    assert not np.array_equal(model.state.e1_polar_vector, model.state.stf_shear_amplitudes[:3])



def test_directional_hubble_acceleration_requires_cH_normalization():
    model = KinematicResponseModel.from_parameters(beta_RO=[0.0, 0.0, 0.0])
    n = np.array([[1.0, 0.0, 0.0], [-1.0, 0.0, 0.0]])
    physical_acceleration = np.array([6.0, 0.0, 0.0])

    with pytest.raises(KinematicsError, match="explicit H0 and speed_of_light"):
        model.directional_hubble_variation(n, acceleration_vector=physical_acceleration)

    physical = model.directional_hubble_variation(
        n, acceleration_vector=physical_acceleration, H0=2.0, speed_of_light=3.0
    )
    normalized = model.directional_hubble_variation(
        n, acceleration_over_cH=np.array([1.0, 0.0, 0.0])
    )
    np.testing.assert_allclose(physical, [-1.0, 1.0])
    np.testing.assert_allclose(normalized, physical)
