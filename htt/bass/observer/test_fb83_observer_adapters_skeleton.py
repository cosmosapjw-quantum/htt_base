from __future__ import annotations

import pytest

from bass.observer.adapters import apply_observer_boost, observed_alm_mixing


@pytest.mark.skip(reason="pending FB-8.3 implementation — skeleton only")
def test_fb83_observer_adapters_skeleton_contract() -> None:
    assert callable(apply_observer_boost)
    assert callable(observed_alm_mixing)
    assert "boost.rapidity == 0" in (apply_observer_boost.__doc__ or "")
