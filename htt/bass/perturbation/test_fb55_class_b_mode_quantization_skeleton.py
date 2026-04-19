from __future__ import annotations

import pytest

from bass.perturbation.class_b_mode_quantization import (
    quantise_class_b_mode,
)


@pytest.mark.skip(reason="pending FB-5.5 implementation — skeleton only")
def test_fb55_class_b_mode_quantization_skeleton_contract() -> None:
    assert callable(quantise_class_b_mode)
