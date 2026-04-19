from __future__ import annotations

import pytest

from bass.spectrum.off_diagonal_covariance import (
    assemble_bianchi_spectrum_covariance,
)


@pytest.mark.skip(reason="pending FB-7.2 implementation — skeleton only")
def test_fb72_off_diagonal_covariance_skeleton_contract() -> None:
    assert callable(assemble_bianchi_spectrum_covariance)
