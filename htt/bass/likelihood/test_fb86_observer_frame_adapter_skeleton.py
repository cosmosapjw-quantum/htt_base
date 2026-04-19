from __future__ import annotations

import pytest

from bass.likelihood.observer_frame_adapter import ObserverFrameLikelihood


@pytest.mark.skip(reason="pending FB-8.6 implementation — skeleton only")
def test_fb86_observer_frame_adapter_skeleton_contract() -> None:
    assert hasattr(ObserverFrameLikelihood, "log_prob")
    assert hasattr(ObserverFrameLikelihood, "marginalise_boost")
    assert hasattr(ObserverFrameLikelihood, "profile_boost")
    doc = ObserverFrameLikelihood.__doc__ or ""
    assert "wraps an FB-7 cosmological-frame likelihood" in doc
