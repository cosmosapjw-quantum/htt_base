from __future__ import annotations

import pytest

from bass.likelihood.htt_decomposition import build_htt_decomposition


@pytest.mark.skip(reason="pending FB-7.3 implementation — skeleton only")
def test_fb73_htt_decomposition_skeleton_contract() -> None:
    assert callable(build_htt_decomposition)
