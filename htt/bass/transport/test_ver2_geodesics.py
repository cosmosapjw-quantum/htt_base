from __future__ import annotations

import numpy as np
import pytest

from bass.background import build_bianchi_algebra, build_geometry
from bass.transport import (
    PhotonGeodesicState,
    ScreenBasisState,
    hard_redshift_check,
    photon_geodesic_rhs,
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


def test_rhs_preserves_direction_and_screen_constraints() -> None:
    basis = ScreenBasisState(u=np.array([0.0, 1.0, 0.0]), v=np.array([0.0, 0.0, 1.0]))
    state = PhotonGeodesicState(
        energy=1.0,
        direction=np.array([1.0, 0.0, 0.0]),
        screen_basis=basis,
    )
    rhs = photon_geodesic_rhs(
        state=state,
        H=2.0,
        sigma_ab=np.diag([0.2, -0.1, -0.1]),
    )
    assert rhs.log_energy_derivative == pytest.approx(-2.2)
    assert abs(float(np.dot(state.direction, rhs.direction_derivative))) < 1.0e-12
    assert (
        abs(float(np.dot(state.direction, rhs.screen_u_derivative) + np.dot(rhs.direction_derivative, state.screen_basis.u)))
        < 1.0e-12
    )
    assert (
        abs(float(np.dot(state.direction, rhs.screen_v_derivative) + np.dot(rhs.direction_derivative, state.screen_basis.v)))
        < 1.0e-12
    )
    assert rhs.frame_metadata.transport_frame == "n_frame"


def test_geometry_drives_nontrivial_direction_transport() -> None:
    algebra = build_bianchi_algebra("VII_0")
    geometry = build_geometry(algebra)
    direction = np.array([1.0, 1.0, 1.0]) / np.sqrt(3.0)
    basis = ScreenBasisState(
        u=np.array([1.0, -1.0, 0.0]) / np.sqrt(2.0),
        v=np.array([1.0, 1.0, -2.0]) / np.sqrt(6.0),
    )
    state = PhotonGeodesicState(
        energy=1.0,
        direction=direction,
        screen_basis=basis,
    )
    rhs = photon_geodesic_rhs(
        state=state,
        H=0.0,
        sigma_ab=np.zeros((3, 3)),
        geometry=geometry,
    )
    assert np.linalg.norm(rhs.direction_derivative) > 0.0
    assert abs(float(np.dot(direction, rhs.direction_derivative))) < 1.0e-12
