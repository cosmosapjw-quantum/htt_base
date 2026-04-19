"""Tests for bass/hierarchy/ic.py (LB-5 I-04..I-06).

Pins the IC constructors against spec §6. Post-LB-5 CAMB-regular-
adiabatic seeding will extend this file with its own IC-XX block.
"""
from __future__ import annotations

import numpy as np
import pytest

from bass.hierarchy.ic import make_initial_state, zero_IC
from bass.hierarchy.pack_unpack import (
    combined_total_size,
    slice_a,
    slice_photon_E,
    slice_photon_T,
    slice_sigma_pm,
    slice_neutrino_reduced,
    unpack_combined_state,
)


# ════════════════════════════════════════════════════════════════════
# I-04 zero_IC gives all zeros except the scale factor
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("L_max", [4, 6, 8])
def test_I04_zero_IC_populates_only_scale_factor(L_max: int) -> None:
    """``zero_IC(a_initial=a0)`` sets ``Y[0] = a0`` and all other slots
    to exact zero.

    Reference: spec §6 table.
    """
    a0 = 1e-4
    y0 = zero_IC(L_max=L_max, a_initial=a0)
    assert y0.shape == (combined_total_size(L_max),)

    assert y0[slice_a(L_max)][0] == a0
    assert np.all(y0[slice_sigma_pm(L_max)] == 0.0)
    assert np.all(y0[slice_photon_T(L_max)] == 0.0)
    assert np.all(y0[slice_photon_E(L_max)] == 0.0)
    assert np.all(y0[slice_neutrino_reduced(L_max)] == 0.0)


# ════════════════════════════════════════════════════════════════════
# I-05 Σ_+ initial value is preserved
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize(
    "Sp_init,Sm_init", [(1e-4, 0.0), (5e-6, -2e-7), (0.0, 3e-5)],
)
def test_I05_zero_IC_sigma_plus_preserved(
    Sp_init: float, Sm_init: float,
) -> None:
    """Non-zero ``Σ_+ / Σ_−`` initial values round-trip through the
    packed state.

    Reference: spec §6 (non-zero shear triggers the T9 shear-injection
    term which then drives Π_2 via collision).
    """
    y0 = zero_IC(
        L_max=6,
        a_initial=1e-4,
        Sigma_plus_initial=Sp_init,
        Sigma_minus_initial=Sm_init,
    )
    state = unpack_combined_state(y0, L_max=6)
    assert state.Sigma_plus == pytest.approx(Sp_init, abs=1e-15)
    assert state.Sigma_minus == pytest.approx(Sm_init, abs=1e-15)


# ════════════════════════════════════════════════════════════════════
# I-06 IC validators
# ════════════════════════════════════════════════════════════════════

def test_I06_zero_IC_rejects_negative_a() -> None:
    """Negative or zero ``a_initial`` is a ``ValueError``."""
    with pytest.raises(ValueError, match="a_initial"):
        zero_IC(L_max=6, a_initial=-1e-4)
    with pytest.raises(ValueError, match="a_initial"):
        zero_IC(L_max=6, a_initial=0.0)


def test_I06_zero_IC_rejects_nonfinite_sigma() -> None:
    """NaN / Inf in Σ_± is a ``ValueError``."""
    with pytest.raises(ValueError, match="Sigma_plus_initial"):
        zero_IC(L_max=6, a_initial=1e-4, Sigma_plus_initial=np.nan)
    with pytest.raises(ValueError, match="Sigma_minus_initial"):
        zero_IC(L_max=6, a_initial=1e-4, Sigma_minus_initial=np.inf)


def test_I06_zero_IC_rejects_low_L_max() -> None:
    """``L_max < 2`` breaks the E-mode tower (needs ℓ≥2 storage)."""
    with pytest.raises(ValueError, match="L_max"):
        zero_IC(L_max=1, a_initial=1e-4)


# ════════════════════════════════════════════════════════════════════
#   make_initial_state — axisymmetric seeds for Π_2 / E_2 (m = 0)
# ════════════════════════════════════════════════════════════════════

def test_make_initial_state_seeds_Pi2_and_E2() -> None:
    """Non-None ``seed_Pi_2_m0`` / ``seed_E_2_m0`` populates exactly
    the m=0 slot (index 2 of the length-5 packed array).
    """
    theta_2 = 7.7e-6
    E_2 = -1.9e-6
    y0 = make_initial_state(
        L_max=6,
        a_initial=1e-4,
        seed_Pi_2_m0=theta_2,
        seed_E_2_m0=E_2,
    )
    state = unpack_combined_state(y0, L_max=6)
    assert state.photon_T.tensors[2].components[2] == theta_2
    assert state.photon_E.E.tensors[2].components[2] == E_2
    # Off-slot components (m ≠ 0) must be zero.
    for idx in (0, 1, 3, 4):
        assert state.photon_T.tensors[2].components[idx] == 0.0
        assert state.photon_E.E.tensors[2].components[idx] == 0.0
    # Higher multipoles untouched.
    for ell in (3, 4, 5, 6):
        np.testing.assert_array_equal(
            state.photon_T.tensors[ell].components, 0.0,
        )
