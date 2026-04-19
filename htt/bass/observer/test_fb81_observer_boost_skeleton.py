from __future__ import annotations

from dataclasses import is_dataclass

import pytest

from bass.observer import ObserverBoost
from bass.species.tilted import assert_tilt_admissible


@pytest.mark.skip(reason="pending FB-8.1 implementation — skeleton only")
def test_fb81_observer_boost_skeleton_contract() -> None:
    assert is_dataclass(ObserverBoost)
    assert hasattr(ObserverBoost, "velocity")
    assert callable(assert_tilt_admissible)
    doc = ObserverBoost.__doc__ or ""
    assert "must not subclass" in doc
