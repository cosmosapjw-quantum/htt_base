from __future__ import annotations

import numpy as np

from bass.background import build_bianchi_algebra, build_geometry
from bass.hierarchy import (
    BoostOrder,
    SeedAssignmentFrame,
    build_constraint_projection,
    build_flrw_regular_seed,
    promote_tilted_seed,
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
