from __future__ import annotations

import pytest

from bass.perturbation.regular_adiabatic_ic import (
    make_camb_regular_adiabatic_seed,
)


@pytest.mark.skip(reason="pending FB-5.3 implementation — skeleton only")
def test_fb53_regular_adiabatic_seed_skeleton_contract() -> None:
    assert callable(make_camb_regular_adiabatic_seed)
