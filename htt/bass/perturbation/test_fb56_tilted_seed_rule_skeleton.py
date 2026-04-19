from __future__ import annotations

import pytest

from bass.perturbation.tilted_seed_rule import apply_tilted_boost_seed_rule


@pytest.mark.skip(reason="pending FB-5.6 implementation — skeleton only")
def test_fb56_tilted_seed_rule_skeleton_contract() -> None:
    assert callable(apply_tilted_boost_seed_rule)
