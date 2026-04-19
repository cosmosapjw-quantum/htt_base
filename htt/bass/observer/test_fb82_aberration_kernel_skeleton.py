from __future__ import annotations

import pytest

from bass.observer.aberration import aberration_kernel


@pytest.mark.skip(reason="pending FB-8.2 implementation — skeleton only")
def test_fb82_aberration_kernel_skeleton_contract() -> None:
    assert callable(aberration_kernel)
    doc = aberration_kernel.__doc__ or ""
    assert "astro-ph/0112457" in doc
    assert "1303.5087" in doc
