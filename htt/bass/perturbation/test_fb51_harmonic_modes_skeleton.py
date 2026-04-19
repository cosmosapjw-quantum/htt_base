from __future__ import annotations

import pytest

from bass.perturbation.harmonic_modes import make_harmonic_mode_rhs_context


@pytest.mark.skip(reason="pending FB-5.1 implementation — skeleton only")
def test_fb51_harmonic_mode_rhs_context_skeleton_contract() -> None:
    assert callable(make_harmonic_mode_rhs_context)
