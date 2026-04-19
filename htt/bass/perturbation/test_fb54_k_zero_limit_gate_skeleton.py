from __future__ import annotations

import pytest

from bass.perturbation.k_zero_limit_gate import (
    assert_k_zero_limit_matches_background,
)


@pytest.mark.skip(reason="pending FB-5.4 implementation — skeleton only")
def test_fb54_k_zero_limit_gate_skeleton_contract() -> None:
    assert callable(assert_k_zero_limit_matches_background)
