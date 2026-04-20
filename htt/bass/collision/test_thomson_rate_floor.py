from __future__ import annotations

import numpy as np
import pytest

from bass.collision.polarization import zero_polarization_hierarchy
from bass.collision.thomson_pstf import EModeThomsonAux, ThomsonAux


def test_thomson_aux_clips_tiny_negative_rate_to_zero() -> None:
    aux = ThomsonAux(
        E_state=zero_polarization_hierarchy(2),
        v_b_real_sph=np.zeros(3),
        Gamma_T=-5.0e-8,
    )
    assert aux.Gamma_T == 0.0


def test_emode_aux_still_rejects_large_negative_rate() -> None:
    with pytest.raises(ValueError, match="non-negative finite"):
        EModeThomsonAux(
            Pi_2_packed=np.zeros(5),
            Gamma_T=-1.0e-4,
        )
