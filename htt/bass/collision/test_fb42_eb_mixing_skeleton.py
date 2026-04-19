from __future__ import annotations

import pytest

from bass.collision.tilted_eb_mixing import (
    evaluate_tilted_polarization_eb_collision,
)


@pytest.mark.skip(reason="pending FB-4.2 implementation — skeleton only")
def test_tilted_polarization_eb_collision_skeleton_contract() -> None:
    assert callable(evaluate_tilted_polarization_eb_collision)
