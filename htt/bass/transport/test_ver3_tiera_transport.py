from __future__ import annotations

import numpy as np
import pytest

from bass.background import build_geometry, get_family_spec
from bass.transport import (
    ScreenBasisState,
    TierAState,
    collision_source_tierA,
    ray_rhs,
    screen_basis_rhs,
)


def _state() -> TierAState:
    return TierAState(
        eta=0.0,
        ray_direction=np.array([0.0, 0.0, 1.0]),
        screen_basis=ScreenBasisState(
            u=np.array([1.0, 0.0, 0.0]),
            v=np.array([0.0, 1.0, 0.0]),
        ),
        phase=0.0,
        I_dir=np.array([1.0, 2.0, 3.0]),
        P_dir=np.array([0.0, 0.0, 0.0]),
        energy=2.0,
    )


def test_ray_rhs_matches_isotropic_redshift_in_zero_shear_background() -> None:
    rhs = ray_rhs(
        0.0,
        _state(),
        {"H": 1.5, "sigma_ab": np.zeros((3, 3))},
    )
    np.testing.assert_allclose(rhs.direction_dot, 0.0)
    assert rhs.energy_dot == pytest.approx(-3.0)


def test_screen_basis_rhs_preserves_transversality_contract() -> None:
    state = _state()
    geometry = build_geometry(get_family_spec("I"))
    rhs_ray = ray_rhs(
        0.0,
        state,
        {"H": 1.0, "sigma_ab": np.diag([0.1, -0.1, 0.0]), "geometry": geometry},
    )
    rhs_screen = screen_basis_rhs(
        0.0,
        state,
        {"H": 1.0, "sigma_ab": np.diag([0.1, -0.1, 0.0]), "geometry": geometry},
    )
    assert abs(float(np.dot(state.ray_direction, rhs_screen.basis_dot_u) + np.dot(rhs_ray.direction_dot, state.screen_basis.u))) < 1.0e-10
    assert abs(float(np.dot(state.ray_direction, rhs_screen.basis_dot_v) + np.dot(rhs_ray.direction_dot, state.screen_basis.v))) < 1.0e-10
    assert np.isfinite(rhs_screen.phase_dot)


def test_collision_source_tiera_uses_directional_thomson_contract() -> None:
    source = collision_source_tierA(
        0.0,
        _state(),
        {"H": 1.0, "sigma_ab": np.zeros((3, 3))},
        {"Gamma_T": 5.0, "I0": 2.0, "I2": 0.0, "E2_pol": 0.0},
    )
    np.testing.assert_allclose(source.dI_dir, 5.0 * np.array([1.0, 0.0, -1.0]))
    np.testing.assert_allclose(source.dP_dir, 0.0)
    assert source.effective_opacity == pytest.approx(5.0)
