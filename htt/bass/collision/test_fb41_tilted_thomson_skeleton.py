from __future__ import annotations

import pytest

from bass.collision.tilted_thomson_layer_b import (
    evaluate_tilted_thomson_pstf_collision,
)


@pytest.mark.skip(reason="pending FB-4.1 implementation — skeleton only")
def test_tilted_thomson_layer_b_skeleton_contract() -> None:
    assert callable(evaluate_tilted_thomson_pstf_collision)
