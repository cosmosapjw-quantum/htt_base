"""Tests for bass/collision/polarization.py (LB-4, TC-06/TC-07, plus
basic container contract).

References
----------
- ``docs/lowell_bianchi/04_thomson_collision_spec.md §5``, §10.
- Ma-Bertschinger 1995 eq (64); Zaldarriaga-Seljak 1997 eq (17).
"""
from __future__ import annotations

import numpy as np
import pytest

from bass.collision.polarization import (
    E_MODE_ELL2_SELF_COEFF,
    E_MODE_ELL2_TEMPERATURE_COEFF,
    E_mode_collision_source,
    PolarizationHierarchyState,
    zero_polarization_hierarchy,
)
from bass.hierarchy.pstf_tensor import (
    PSTFHierarchyState,
    PSTFTensor,
    zero_hierarchy,
    zero_pstf,
)


# ════════════════════════════════════════════════════════════════════
#   Container contract
# ════════════════════════════════════════════════════════════════════

def test_polarization_state_requires_psfhierarchy() -> None:
    with pytest.raises(TypeError):
        PolarizationHierarchyState(E=object())  # type: ignore[arg-type]


def test_polarization_state_rejects_L_below_2() -> None:
    for L in (0, 1):
        with pytest.raises(ValueError):
            PolarizationHierarchyState(E=zero_hierarchy(L))


def test_zero_polarization_factory() -> None:
    E_st = zero_polarization_hierarchy(L=4)
    assert E_st.L == 4
    assert len(E_st.tensors) == 5
    for ell, t in enumerate(E_st.tensors):
        assert t.ell == ell
        assert np.all(t.components == 0.0)


def test_zero_polarization_factory_rejects_L_below_2() -> None:
    for L in (-1, 0, 1):
        with pytest.raises(ValueError):
            zero_polarization_hierarchy(L=L)


def test_polarization_state_copy_isolates_components() -> None:
    E_st = zero_polarization_hierarchy(L=3)
    E_st.tensors[2].components[:] = [1, 2, 3, 4, 5]
    dup = E_st.copy()
    dup.tensors[2].components[:] = 0.0
    assert np.all(E_st.tensors[2].components == np.array([1, 2, 3, 4, 5]))


# ════════════════════════════════════════════════════════════════════
#   Thomson coefficients
# ════════════════════════════════════════════════════════════════════

def test_E_mode_coefficients_match_MB_1995() -> None:
    """Coefficients are the exact Ma-Bertschinger eq (64) values."""
    assert E_MODE_ELL2_SELF_COEFF == pytest.approx(-2.0 / 5.0, rel=0)
    assert E_MODE_ELL2_TEMPERATURE_COEFF == pytest.approx(
        -3.0 / (5.0 * np.sqrt(6.0)), rel=0,
    )


# ════════════════════════════════════════════════════════════════════
#   TC-06: K^E_2 at Π_2 = 0, E_2 ≠ 0: K^E_2 = -(2/5) Γ_T E_2
# ════════════════════════════════════════════════════════════════════

def test_TC06_E_collision_at_zero_Pi2() -> None:
    E_state = zero_polarization_hierarchy(L=4)
    E_state.tensors[2].components[:] = [0.1, -0.2, 0.3, -0.4, 0.5]
    Gamma_T = 2.7
    Pi_2_packed = np.zeros(5)

    K_E_2 = E_mode_collision_source(
        ell=2,
        E_state=E_state,
        Pi_2_packed=Pi_2_packed,
        Gamma_T=Gamma_T,
    )
    expected = Gamma_T * E_MODE_ELL2_SELF_COEFF * E_state.tensors[2].components
    np.testing.assert_allclose(K_E_2.components, expected, rtol=0, atol=1e-12)
    assert K_E_2.ell == 2


# ════════════════════════════════════════════════════════════════════
#   TC-07: K^E_2 at Π_2 ≠ 0, E_2 = 0: K^E_2 = -(3/(5√6)) Γ_T Π_2
# ════════════════════════════════════════════════════════════════════

def test_TC07_E_collision_at_zero_E2() -> None:
    E_state = zero_polarization_hierarchy(L=4)
    # E_2 is all zeros
    Gamma_T = 1.3
    Pi_2_packed = np.array([0.1, -0.2, 0.3, -0.4, 0.5], dtype=np.float64)

    K_E_2 = E_mode_collision_source(
        ell=2,
        E_state=E_state,
        Pi_2_packed=Pi_2_packed,
        Gamma_T=Gamma_T,
    )
    expected = Gamma_T * E_MODE_ELL2_TEMPERATURE_COEFF * Pi_2_packed
    np.testing.assert_allclose(K_E_2.components, expected, rtol=0, atol=1e-12)


# ════════════════════════════════════════════════════════════════════
#   TC-06 + TC-07 combined
# ════════════════════════════════════════════════════════════════════

def test_E_collision_superposition_with_Pi2_and_E2() -> None:
    E_state = zero_polarization_hierarchy(L=3)
    E_state.tensors[2].components[:] = [0.05, -0.11, 0.22, -0.13, 0.07]
    Gamma_T = 3.14
    Pi_2_packed = np.array([0.09, -0.01, 0.15, -0.07, 0.02], dtype=np.float64)

    K_E_2 = E_mode_collision_source(
        ell=2, E_state=E_state,
        Pi_2_packed=Pi_2_packed, Gamma_T=Gamma_T,
    )
    expected = Gamma_T * (
        E_MODE_ELL2_SELF_COEFF * E_state.tensors[2].components
        + E_MODE_ELL2_TEMPERATURE_COEFF * Pi_2_packed
    )
    np.testing.assert_allclose(K_E_2.components, expected, rtol=0, atol=1e-13)


# ════════════════════════════════════════════════════════════════════
#   ℓ = 0, 1 return zero
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("ell", [0, 1])
def test_E_collision_zero_at_low_ell(ell: int) -> None:
    E_state = zero_polarization_hierarchy(L=4)
    # Populate all tensors to ensure the returned zero is from physics,
    # not a zero-state coincidence.
    for ell_loc, t in enumerate(E_state.tensors):
        t.components[:] = 0.1 * (ell_loc + 1)
    K = E_mode_collision_source(
        ell=ell, E_state=E_state, Pi_2_packed=None, Gamma_T=5.0,
    )
    assert K.ell == ell
    assert np.all(K.components == 0.0)


# ════════════════════════════════════════════════════════════════════
#   TC-09: K^E_3 = -Γ_T × E_3
# ════════════════════════════════════════════════════════════════════

def test_TC09_high_ell_damping() -> None:
    E_state = zero_polarization_hierarchy(L=5)
    E_state.tensors[3].components[:] = np.linspace(-0.5, 0.5, 7)
    E_state.tensors[4].components[:] = np.linspace(1.0, -1.0, 9)
    Gamma_T = 0.77

    K_E_3 = E_mode_collision_source(
        ell=3, E_state=E_state, Pi_2_packed=None, Gamma_T=Gamma_T,
    )
    np.testing.assert_allclose(
        K_E_3.components,
        -Gamma_T * E_state.tensors[3].components,
        rtol=0, atol=1e-12,
    )
    K_E_4 = E_mode_collision_source(
        ell=4, E_state=E_state, Pi_2_packed=None, Gamma_T=Gamma_T,
    )
    np.testing.assert_allclose(
        K_E_4.components,
        -Gamma_T * E_state.tensors[4].components,
        rtol=0, atol=1e-12,
    )


# ════════════════════════════════════════════════════════════════════
#   Validation / edge-cases
# ════════════════════════════════════════════════════════════════════

def test_E_collision_rejects_negative_ell() -> None:
    E_state = zero_polarization_hierarchy(L=3)
    with pytest.raises(ValueError):
        E_mode_collision_source(
            ell=-1, E_state=E_state, Pi_2_packed=None, Gamma_T=1.0,
        )


def test_E_collision_rejects_negative_gamma() -> None:
    E_state = zero_polarization_hierarchy(L=3)
    with pytest.raises(ValueError):
        E_mode_collision_source(
            ell=3, E_state=E_state, Pi_2_packed=None, Gamma_T=-1.0,
        )


def test_E_collision_rejects_nonfinite_gamma() -> None:
    E_state = zero_polarization_hierarchy(L=3)
    for bad in (np.nan, np.inf):
        with pytest.raises(ValueError):
            E_mode_collision_source(
                ell=3, E_state=E_state, Pi_2_packed=None, Gamma_T=bad,
            )


def test_E_collision_rejects_ell_above_tower() -> None:
    E_state = zero_polarization_hierarchy(L=3)
    with pytest.raises(ValueError):
        E_mode_collision_source(
            ell=4, E_state=E_state, Pi_2_packed=None, Gamma_T=1.0,
        )


def test_E_collision_requires_Pi2_at_ell2() -> None:
    E_state = zero_polarization_hierarchy(L=3)
    with pytest.raises(ValueError, match="Pi_2_packed"):
        E_mode_collision_source(
            ell=2, E_state=E_state, Pi_2_packed=None, Gamma_T=1.0,
        )


def test_E_collision_rejects_wrong_Pi2_shape() -> None:
    E_state = zero_polarization_hierarchy(L=3)
    for shape in ((3,), (7,), (5, 5)):
        with pytest.raises(ValueError):
            E_mode_collision_source(
                ell=2, E_state=E_state,
                Pi_2_packed=np.zeros(shape), Gamma_T=1.0,
            )


def test_E_collision_gamma_zero_returns_zero() -> None:
    E_state = zero_polarization_hierarchy(L=3)
    E_state.tensors[2].components[:] = [1, 2, 3, 4, 5]
    E_state.tensors[3].components[:] = np.arange(7) + 1.0
    Pi_2_packed = np.array([10, 20, 30, 40, 50], dtype=np.float64)

    for ell in (2, 3):
        K = E_mode_collision_source(
            ell=ell, E_state=E_state,
            Pi_2_packed=Pi_2_packed if ell == 2 else None,
            Gamma_T=0.0,
        )
        assert np.all(K.components == 0.0)


def test_E_collision_does_not_mutate_state() -> None:
    E_state = zero_polarization_hierarchy(L=3)
    E_state.tensors[2].components[:] = [0.1, 0.2, 0.3, 0.4, 0.5]
    E_state.tensors[3].components[:] = np.ones(7)
    snapshots = [t.components.copy() for t in E_state.tensors]

    _ = E_mode_collision_source(
        ell=2, E_state=E_state,
        Pi_2_packed=np.ones(5), Gamma_T=1.0,
    )
    _ = E_mode_collision_source(
        ell=3, E_state=E_state, Pi_2_packed=None, Gamma_T=1.0,
    )
    for orig, now in zip(snapshots, E_state.tensors):
        np.testing.assert_array_equal(orig, now.components)


# Silence unused-import warning on ``PSTFTensor`` / ``zero_pstf`` / ``PSTFHierarchyState``.
_ = PSTFTensor
_ = zero_pstf
_ = PSTFHierarchyState
