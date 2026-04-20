from __future__ import annotations

import numpy as np

from bass.hierarchy import (
    BoostOrder,
    SeedAssignmentFrame,
    build_constraint_projection_stub,
    build_flrw_regular_seed_stub,
    promote_tilted_seed_stub,
)


def test_regular_seed_stub_keeps_flrw_regular_contract() -> None:
    seed = build_flrw_regular_seed_stub(amplitude=3.0)
    assert seed.delta_gamma == 3.0
    assert seed.descriptor.flrw_limit_required is True
    assert seed.descriptor.assignment_frame is SeedAssignmentFrame.NORMAL


def test_tilted_seed_stub_records_frame_rule_and_preserves_zero_tilt_limit() -> None:
    seed = build_flrw_regular_seed_stub(amplitude=2.0)
    tilted = promote_tilted_seed_stub(
        seed,
        electron_velocity=np.zeros(3),
        boost_order=BoostOrder.LINEAR,
    )
    assert tilted.amplitude == seed.amplitude
    assert tilted.delta_gamma == seed.delta_gamma
    assert tilted.descriptor.assignment_frame is SeedAssignmentFrame.ELECTRON_IF_TILTED
    assert tilted.descriptor.boost_order is BoostOrder.LINEAR


def test_constraint_projection_stub_stays_explicitly_pending() -> None:
    seed = build_flrw_regular_seed_stub(amplitude=1.0)
    projection = build_constraint_projection_stub(seed)
    assert projection.projection_ready is False
    assert projection.constraint_projection_required is True
