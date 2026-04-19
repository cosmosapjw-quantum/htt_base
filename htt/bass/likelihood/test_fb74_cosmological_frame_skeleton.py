from __future__ import annotations

import pytest

from bass.likelihood.cosmological_frame import CosmologicalFrameLikelihood


@pytest.mark.skip(reason="pending FB-7.4 implementation — skeleton only")
def test_fb74_cosmological_frame_skeleton_contract() -> None:
    assert hasattr(CosmologicalFrameLikelihood, "log_prob")
    doc = CosmologicalFrameLikelihood.__doc__ or ""
    assert "cosmological-frame only" in doc
    assert "observer_frame_adapter" in doc
