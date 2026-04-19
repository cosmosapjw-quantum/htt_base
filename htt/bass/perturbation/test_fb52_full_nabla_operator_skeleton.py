from __future__ import annotations

import pytest

from bass.perturbation.full_nabla_operator import (
    make_full_mode_nabla_tilde_operator,
)


@pytest.mark.skip(reason="pending FB-5.2 implementation — skeleton only")
def test_fb52_full_mode_nabla_tilde_operator_skeleton_contract() -> None:
    assert callable(make_full_mode_nabla_tilde_operator)
