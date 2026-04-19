from __future__ import annotations

import pytest

from bass.spectrum.lowell_los import build_lowell_line_of_sight_propagator


@pytest.mark.skip(reason="pending FB-7.1 implementation — skeleton only")
def test_fb71_lowell_los_skeleton_contract() -> None:
    assert callable(build_lowell_line_of_sight_propagator)
