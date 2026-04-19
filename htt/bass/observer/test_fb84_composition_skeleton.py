from __future__ import annotations

import pytest

from bass.observer.composition import compose_tilts


@pytest.mark.skip(reason="pending FB-8.4 implementation — skeleton only")
def test_fb84_composition_skeleton_contract() -> None:
    assert callable(compose_tilts)
    doc = compose_tilts.__doc__ or ""
    assert "Diagnostic-only" in doc
    assert "must never be routed into the production path" in doc
