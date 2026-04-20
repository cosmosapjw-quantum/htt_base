from __future__ import annotations

import numpy as np
import pytest

from bass.transport import (
    PhotonGeodesicState,
    ScreenBasisState,
    hard_redshift_check,
    photon_geodesic_rhs_stub,
    redshift_log_derivative,
)


def test_screen_basis_requires_orthonormality() -> None:
    with pytest.raises(ValueError, match="orthonormal"):
        ScreenBasisState(u=np.array([1.0, 0.0, 0.0]), v=np.array([1.0, 0.0, 0.0]))


def test_geodesic_state_requires_transverse_screen_basis() -> None:
    basis = ScreenBasisState(u=np.array([0.0, 1.0, 0.0]), v=np.array([0.0, 0.0, 1.0]))
    state = PhotonGeodesicState(
        energy=2.0,
        direction=np.array([1.0, 0.0, 0.0]),
        screen_basis=basis,
    )
    assert np.allclose(state.direction, np.array([1.0, 0.0, 0.0]))


def test_redshift_formula_matches_hard_check_definition() -> None:
    sigma = np.diag([0.2, -0.1, -0.1])
    direction = np.array([1.0, 0.0, 0.0])
    assert redshift_log_derivative(1.5, sigma, direction) == pytest.approx(-1.7)
    assert hard_redshift_check(1.5, sigma, direction) == pytest.approx(-0.2)


def test_rhs_stub_keeps_frame_metadata_and_zero_direction_transport() -> None:
    basis = ScreenBasisState(u=np.array([0.0, 1.0, 0.0]), v=np.array([0.0, 0.0, 1.0]))
    state = PhotonGeodesicState(
        energy=1.0,
        direction=np.array([1.0, 0.0, 0.0]),
        screen_basis=basis,
    )
    rhs = photon_geodesic_rhs_stub(
        state=state,
        H=2.0,
        sigma_ab=np.zeros((3, 3)),
    )
    assert rhs.log_energy_derivative == pytest.approx(-2.0)
    assert np.array_equal(rhs.direction_derivative, np.zeros(3))
    assert rhs.frame_metadata.transport_frame == "n_frame"
