from __future__ import annotations

import pytest

from bass.perturbation.k_type_regression import run_k_type_regression_matrix


@pytest.mark.skip(reason="pending FB-5.7 implementation — skeleton only")
def test_fb57_k_type_regression_skeleton_contract() -> None:
    assert callable(run_k_type_regression_matrix)
