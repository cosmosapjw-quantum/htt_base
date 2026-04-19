from __future__ import annotations

import pytest

from bass.collision.tilted_doppler_second_order import (
    evaluate_tilted_second_order_doppler_correction,
)


@pytest.mark.skip(reason="pending FB-4.3 implementation — skeleton only")
def test_tilted_second_order_doppler_correction_skeleton_contract() -> None:
    assert callable(evaluate_tilted_second_order_doppler_correction)
