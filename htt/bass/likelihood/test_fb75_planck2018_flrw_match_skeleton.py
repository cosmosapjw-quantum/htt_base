from __future__ import annotations

import pytest

from bass.likelihood.planck2018_flrw_match import (
    validate_planck2018_flrw_limit_match,
)


@pytest.mark.skip(reason="pending FB-7.5 implementation — skeleton only")
def test_fb75_planck2018_flrw_match_skeleton_contract() -> None:
    assert callable(validate_planck2018_flrw_limit_match)
