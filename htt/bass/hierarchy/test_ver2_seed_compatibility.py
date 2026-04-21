from __future__ import annotations

import numpy as np

from bass.background import build_bianchi_algebra, build_geometry
from bass.hierarchy import (
    BoostOrder,
    PackedRegularSeedInjection,
    SeedAssignmentFrame,
    build_constraint_projection,
    build_flrw_regular_seed,
    project_packed_regular_seed,
    promote_tilted_seed,
)
from bass.perturbation.regular_adiabatic_ic import (
    make_camb_regular_adiabatic_seed,
    seed_observables,
)


def test_regular_seed_keeps_flrw_regular_contract() -> None:
    seed = build_flrw_regular_seed(amplitude=3.0)
    assert seed.delta_gamma == 3.0
    assert seed.descriptor.flrw_limit_required is True
    assert seed.descriptor.assignment_frame is SeedAssignmentFrame.NORMAL


def test_tilted_seed_records_frame_rule_and_preserves_zero_tilt_limit() -> None:
    seed = build_flrw_regular_seed(amplitude=2.0)
    tilted = promote_tilted_seed(
        seed,
        electron_velocity=np.zeros(3),
        boost_order=BoostOrder.LINEAR,
    )
    assert tilted.amplitude == seed.amplitude
    assert tilted.delta_gamma == seed.delta_gamma
    assert tilted.descriptor.assignment_frame is SeedAssignmentFrame.ELECTRON_IF_TILTED
    assert tilted.descriptor.boost_order is BoostOrder.LINEAR


def test_constraint_projection_is_finite_in_symbolic_mode() -> None:
    seed = promote_tilted_seed(
        build_flrw_regular_seed(amplitude=1.0),
        electron_velocity=np.array([0.3, 0.0, 0.0]),
    )
    projection = build_constraint_projection(seed)
    assert projection.projection_ready is True
    assert projection.projection_mode == "boost_consistency_first_pass"
    assert np.linalg.norm(projection.momentum_residual_after) < np.linalg.norm(
        projection.momentum_residual_before
    )


def test_constraint_projection_can_project_onto_background_codazzi_surface() -> None:
    algebra = build_bianchi_algebra("V")
    geometry = build_geometry(algebra)
    seed = promote_tilted_seed(
        build_flrw_regular_seed(amplitude=1.0),
        electron_velocity=np.array([0.2, 0.0, 0.0]),
    )
    projection = build_constraint_projection(
        seed,
        geometry=geometry,
        sigma_ab=np.zeros((3, 3)),
    )
    assert projection.projection_ready is True
    assert projection.projection_mode == "background_codazzi_project"
    assert projection.projected_sigma_ab is not None
    assert np.linalg.norm(projection.momentum_residual_after) < 1.0e-10


def test_constraint_projection_accepts_explicit_runtime_target_q() -> None:
    algebra = build_bianchi_algebra("V")
    geometry = build_geometry(algebra)
    seed = promote_tilted_seed(
        build_flrw_regular_seed(amplitude=1.0),
        electron_velocity=np.array([0.2, 0.0, 0.0]),
    )
    target_q = np.array([2.0e-3, 0.0, 0.0], dtype=np.float64)
    projection = build_constraint_projection(
        seed,
        geometry=geometry,
        sigma_ab=np.zeros((3, 3)),
        target_q=target_q,
    )
    assert projection.projection_ready is True
    assert projection.projection_mode == "background_codazzi_project"
    assert projection.projected_sigma_ab is not None
    assert np.linalg.norm(projection.momentum_residual_after) < 1.0e-10


def test_project_packed_regular_seed_preserves_zero_tilt_limit() -> None:
    injected = project_packed_regular_seed(
        make_camb_regular_adiabatic_seed(
            k_comoving=1.0e-3,
            eta_initial=0.2,
            a_initial=3.0e-7,
            L_max=6,
        ),
        electron_velocity=np.zeros(3),
    )
    assert isinstance(injected, PackedRegularSeedInjection)
    assert injected.velocity_scale == 1.0
    assert injected.projection.projection_ready is True
    before = seed_observables(
        make_camb_regular_adiabatic_seed(
            k_comoving=1.0e-3,
            eta_initial=0.2,
            a_initial=3.0e-7,
            L_max=6,
        ),
        L_max=6,
    )
    after = seed_observables(injected.seed_state, L_max=6)
    assert after["theta_gamma"] == before["theta_gamma"]
    assert after["theta_nu"] == before["theta_nu"]
    assert after["theta_b"] == before["theta_b"]
    assert after["theta_c"] == before["theta_c"]


def test_project_packed_regular_seed_rescales_velocity_block_under_tilt() -> None:
    seed_state = make_camb_regular_adiabatic_seed(
        k_comoving=1.0e-3,
        eta_initial=0.2,
        a_initial=3.0e-7,
        L_max=6,
    )
    injected = project_packed_regular_seed(
        seed_state,
        electron_velocity=np.array([0.3, 0.0, 0.0]),
    )
    before = seed_observables(seed_state, L_max=6)
    after = seed_observables(injected.seed_state, L_max=6)
    assert injected.velocity_scale < 1.0
    assert after["theta_gamma"] == before["theta_gamma"] * injected.velocity_scale
    assert after["theta_nu"] == before["theta_nu"] * injected.velocity_scale
    assert after["theta_b"] == before["theta_b"] * injected.velocity_scale
    assert after["theta_c"] == before["theta_c"] * injected.velocity_scale
