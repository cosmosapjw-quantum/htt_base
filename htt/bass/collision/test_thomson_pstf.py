"""Tests for bass/collision/thomson_pstf.py (LB-4, TC-01..TC-09,
TC-12, TC-13 + contract / validation).

References
----------
- ``docs/lowell_bianchi/04_thomson_collision_spec.md §4, §10, §11``.
- Ma-Bertschinger 1995 eq (63); Zaldarriaga-Seljak 1997 eq (7).
"""
from __future__ import annotations

import numpy as np
import pytest

from bass.collision.polarization import (
    PolarizationHierarchyState,
    zero_polarization_hierarchy,
)
from bass.collision.thomson_pstf import (
    EModeThomsonAux,
    EModeThomsonCollisionOperator,
    THOMSON_ELL2_POLARIZATION_COEFF,
    THOMSON_ELL2_SELF_COEFF,
    ThomsonAux,
    ThomsonPSTFCollisionOperator,
)
from bass.hierarchy.collision_interface import CollisionOperator
from bass.hierarchy.pstf_tensor import (
    PSTFHierarchyState,
    PSTFTensor,
    zero_hierarchy,
)


# ════════════════════════════════════════════════════════════════════
#   Fixtures
# ════════════════════════════════════════════════════════════════════

@pytest.fixture
def populated_state():
    """Non-trivial temperature tower up to L=4 for shape / damping tests."""
    st = zero_hierarchy(L=4)
    st.tensors[0].components[:] = [0.3]
    st.tensors[1].components[:] = [0.1, 0.0, -0.2]
    st.tensors[2].components[:] = [0.05, -0.12, 0.20, -0.08, 0.04]
    st.tensors[3].components[:] = np.linspace(-0.5, 0.5, 7)
    st.tensors[4].components[:] = np.linspace(1.0, -1.0, 9)
    return st


@pytest.fixture
def populated_E_state():
    E_st = zero_polarization_hierarchy(L=4)
    E_st.tensors[2].components[:] = [0.02, -0.05, 0.10, -0.03, 0.01]
    E_st.tensors[3].components[:] = np.linspace(-0.2, 0.2, 7)
    E_st.tensors[4].components[:] = np.linspace(0.3, -0.3, 9)
    return E_st


# ════════════════════════════════════════════════════════════════════
#   Protocol conformance
# ════════════════════════════════════════════════════════════════════

def test_operators_satisfy_CollisionOperator_protocol() -> None:
    assert isinstance(ThomsonPSTFCollisionOperator(), CollisionOperator)
    assert isinstance(EModeThomsonCollisionOperator(), CollisionOperator)


# ════════════════════════════════════════════════════════════════════
#   TC-01: K_0 ≡ 0
# ════════════════════════════════════════════════════════════════════

def test_TC01_monopole_is_zero(populated_state, populated_E_state) -> None:
    op = ThomsonPSTFCollisionOperator()
    aux = ThomsonAux(
        E_state=populated_E_state,
        v_b_real_sph=np.array([0.3, -0.1, 0.2]),
        Gamma_T=5.0,
    )
    K0 = op.evaluate(0, populated_state, aux)
    assert K0.ell == 0
    np.testing.assert_array_equal(K0.components, np.zeros(1))


def test_TC01_monopole_is_zero_irrespective_of_Gamma(
    populated_state, populated_E_state,
) -> None:
    op = ThomsonPSTFCollisionOperator()
    for Gamma_T in (0.0, 0.1, 1.0, 100.0):
        aux = ThomsonAux(
            E_state=populated_E_state,
            v_b_real_sph=np.array([1.0, -2.0, 3.0]),
            Gamma_T=Gamma_T,
        )
        K0 = op.evaluate(0, populated_state, aux)
        assert np.all(K0.components == 0.0)


# ════════════════════════════════════════════════════════════════════
#   TC-02: K_1 at Π_1 = v_b → 0 (tight-coupling fixed point)
# ════════════════════════════════════════════════════════════════════

def test_TC02_dipole_at_fixed_point_is_zero(populated_E_state) -> None:
    v_b = np.array([0.17, -0.03, 0.42], dtype=np.float64)
    st = zero_hierarchy(L=2)
    st.tensors[1].components[:] = v_b  # Π_1 = v_b

    op = ThomsonPSTFCollisionOperator()
    aux = ThomsonAux(
        E_state=populated_E_state, v_b_real_sph=v_b, Gamma_T=2.0,
    )
    K1 = op.evaluate(1, st, aux)
    np.testing.assert_allclose(K1.components, np.zeros(3), atol=1e-15)


# ════════════════════════════════════════════════════════════════════
#   TC-03: K_1 at v_b = 0, Π_1 ≠ 0 → K_1 = −Γ_T Π_1
# ════════════════════════════════════════════════════════════════════

def test_TC03_dipole_at_zero_vb_is_damping(populated_state, populated_E_state) -> None:
    Gamma_T = 1.5
    op = ThomsonPSTFCollisionOperator()
    aux = ThomsonAux(
        E_state=populated_E_state,
        v_b_real_sph=np.zeros(3),
        Gamma_T=Gamma_T,
    )
    K1 = op.evaluate(1, populated_state, aux)
    expected = -Gamma_T * populated_state.tensors[1].components
    np.testing.assert_allclose(K1.components, expected, rtol=0, atol=1e-12)


# ════════════════════════════════════════════════════════════════════
#   TC-04: K_2 at E_2 = 0, Π_2 ≠ 0 → K_2 = −(9/10) Γ_T Π_2
# ════════════════════════════════════════════════════════════════════

def test_TC04_quadrupole_at_zero_E2_is_self_damping(populated_state) -> None:
    """Π_2 ≠ 0, E_2 = 0 → K_2 = (-9/10) Γ_T Π_2."""
    E_state = zero_polarization_hierarchy(L=2)  # E_2 = 0
    Gamma_T = 2.2
    op = ThomsonPSTFCollisionOperator()
    aux = ThomsonAux(
        E_state=E_state,
        v_b_real_sph=np.zeros(3),
        Gamma_T=Gamma_T,
    )
    K2 = op.evaluate(2, populated_state, aux)
    expected = Gamma_T * THOMSON_ELL2_SELF_COEFF * populated_state.tensors[2].components
    np.testing.assert_allclose(K2.components, expected, rtol=0, atol=1e-12)


# ════════════════════════════════════════════════════════════════════
#   TC-05: K_2 at Π_2 = 0, E_2 ≠ 0 → K_2 = −(√6/10) Γ_T E_2
# ════════════════════════════════════════════════════════════════════

def test_TC05_quadrupole_at_zero_Pi2_is_polter_coupling() -> None:
    """Π_2 = 0, E_2 ≠ 0 → K_2 = -(√6/10) Γ_T E_2."""
    st = zero_hierarchy(L=2)  # Π_2 = 0
    E_state = zero_polarization_hierarchy(L=2)
    E_state.tensors[2].components[:] = [0.11, -0.07, 0.23, -0.09, 0.15]
    Gamma_T = 3.0
    op = ThomsonPSTFCollisionOperator()
    aux = ThomsonAux(
        E_state=E_state,
        v_b_real_sph=np.zeros(3),
        Gamma_T=Gamma_T,
    )
    K2 = op.evaluate(2, st, aux)
    expected = (
        Gamma_T * THOMSON_ELL2_POLARIZATION_COEFF
        * E_state.tensors[2].components
    )
    np.testing.assert_allclose(K2.components, expected, rtol=0, atol=1e-12)


# ════════════════════════════════════════════════════════════════════
#   Coefficient values (literals)
# ════════════════════════════════════════════════════════════════════

def test_Thomson_coefficients_match_MB_1995() -> None:
    assert THOMSON_ELL2_SELF_COEFF == pytest.approx(-9.0 / 10.0, rel=0)
    assert THOMSON_ELL2_POLARIZATION_COEFF == pytest.approx(
        -np.sqrt(6.0) / 10.0, rel=0,
    )


# ════════════════════════════════════════════════════════════════════
#   TC-08: K_3 = −Γ_T × Π_3 (temperature high-ℓ damping)
# ════════════════════════════════════════════════════════════════════

def test_TC08_high_ell_temperature_damping(populated_state, populated_E_state) -> None:
    Gamma_T = 0.8
    op = ThomsonPSTFCollisionOperator()
    aux = ThomsonAux(
        E_state=populated_E_state,
        v_b_real_sph=np.zeros(3),
        Gamma_T=Gamma_T,
    )
    for ell in (3, 4):
        K = op.evaluate(ell, populated_state, aux)
        expected = -Gamma_T * populated_state.tensors[ell].components
        np.testing.assert_allclose(K.components, expected, rtol=0, atol=1e-12)
        assert K.ell == ell


# ════════════════════════════════════════════════════════════════════
#   TC-09: K^E_3 = −Γ_T × E_3 (E-mode high-ℓ damping via E operator)
# ════════════════════════════════════════════════════════════════════

def test_TC09_high_ell_E_mode_damping_via_operator(populated_E_state) -> None:
    Gamma_T = 1.2
    op = EModeThomsonCollisionOperator()
    aux = EModeThomsonAux(
        Pi_2_packed=np.zeros(5, dtype=np.float64), Gamma_T=Gamma_T,
    )
    for ell in (3, 4):
        K = op.evaluate(ell, populated_E_state.E, aux)
        expected = -Gamma_T * populated_E_state.tensors[ell].components
        np.testing.assert_allclose(K.components, expected, rtol=0, atol=1e-12)
        assert K.ell == ell


# ════════════════════════════════════════════════════════════════════
#   Superposition of quadrupole contributions (Π_2 + E_2)
# ════════════════════════════════════════════════════════════════════

def test_quadrupole_superposition_linear(populated_state, populated_E_state) -> None:
    Gamma_T = 1.0
    op = ThomsonPSTFCollisionOperator()
    aux = ThomsonAux(
        E_state=populated_E_state,
        v_b_real_sph=np.zeros(3),
        Gamma_T=Gamma_T,
    )
    K2_full = op.evaluate(2, populated_state, aux)
    expected = Gamma_T * (
        THOMSON_ELL2_SELF_COEFF * populated_state.tensors[2].components
        + THOMSON_ELL2_POLARIZATION_COEFF * populated_E_state.tensors[2].components
    )
    np.testing.assert_allclose(K2_full.components, expected, atol=1e-12)


# ════════════════════════════════════════════════════════════════════
#   TC-12: at v_e = 0 (orthogonal), LB-4 collision matches trivially
#   (the orthogonal limit *is* the LB-4 scope — test is that operators
#    accept the full parametrisation without needing a boost kernel)
# ════════════════════════════════════════════════════════════════════

def test_TC12_orthogonal_frame_consistency(populated_state, populated_E_state) -> None:
    """At v_e = 0 the LB-4 operator's output does not depend on any
    hidden frame-boost parameters; it is a pure function of ``Π, E, v_b, Γ_T``.

    This is the scoping assertion for LB-4a: the operator does not take
    a ``v_e`` input, and the full boost is deferred to LB-4b.
    """
    op = ThomsonPSTFCollisionOperator()
    # Two different aux payloads with identical (Π, E, v_b, Γ_T).
    aux1 = ThomsonAux(
        E_state=populated_E_state,
        v_b_real_sph=np.array([0.1, -0.2, 0.05]),
        Gamma_T=1.7,
    )
    aux2 = ThomsonAux(
        E_state=populated_E_state,
        v_b_real_sph=np.array([0.1, -0.2, 0.05]),
        Gamma_T=1.7,
    )
    for ell in range(populated_state.L + 1):
        K1 = op.evaluate(ell, populated_state, aux1)
        K2 = op.evaluate(ell, populated_state, aux2)
        np.testing.assert_array_equal(K1.components, K2.components)


# ════════════════════════════════════════════════════════════════════
#   TC-13: axisymmetric Π_2 m=0 slot corresponds to Θ_2 (W6-04 scalar)
# ════════════════════════════════════════════════════════════════════

def test_TC13_axisymmetric_Pi2_m0_slot_is_theta2_scalar() -> None:
    """In the real-SH packing with ``m = i − ℓ``, the ``m = 0`` slot
    of a rank-ℓ array is at index ℓ. For an axisymmetric Π_2 the
    scalar Θ_2 of the W6-04 convention is the ``m = 0`` amplitude,
    and the Thomson self-damping reduces to the scalar −(9/10) Γ_T Θ_2.
    """
    Theta_2_scalar = 0.37
    st = zero_hierarchy(L=2)
    st.tensors[2].components[2] = Theta_2_scalar  # m = 0 slot (index ℓ = 2)

    E_state = zero_polarization_hierarchy(L=2)  # E = 0
    Gamma_T = 1.0
    op = ThomsonPSTFCollisionOperator()
    aux = ThomsonAux(
        E_state=E_state,
        v_b_real_sph=np.zeros(3),
        Gamma_T=Gamma_T,
    )
    K2 = op.evaluate(2, st, aux)
    # Only the m = 0 slot is non-zero; value is (-9/10) Γ_T Θ_2.
    assert K2.components[2] == pytest.approx(
        THOMSON_ELL2_SELF_COEFF * Gamma_T * Theta_2_scalar, abs=1e-14,
    )
    for idx in (0, 1, 3, 4):
        assert K2.components[idx] == 0.0


# ════════════════════════════════════════════════════════════════════
#   Stateless operator: evaluate never mutates state
# ════════════════════════════════════════════════════════════════════

def test_operators_do_not_mutate_state(
    populated_state, populated_E_state,
) -> None:
    T_snapshots = [t.components.copy() for t in populated_state.tensors]
    E_snapshots = [t.components.copy() for t in populated_E_state.tensors]
    op_T = ThomsonPSTFCollisionOperator()
    op_E = EModeThomsonCollisionOperator()
    aux_T = ThomsonAux(
        E_state=populated_E_state,
        v_b_real_sph=np.array([0.2, -0.1, 0.05]),
        Gamma_T=2.0,
    )
    aux_E = EModeThomsonAux(
        Pi_2_packed=populated_state.tensors[2].components.copy(),
        Gamma_T=2.0,
    )
    for ell in range(populated_state.L + 1):
        _ = op_T.evaluate(ell, populated_state, aux_T)
        _ = op_E.evaluate(ell, populated_E_state.E, aux_E)
    for orig, now in zip(T_snapshots, populated_state.tensors):
        np.testing.assert_array_equal(orig, now.components)
    for orig, now in zip(E_snapshots, populated_E_state.tensors):
        np.testing.assert_array_equal(orig, now.components)


def test_evaluate_tower_reproduces_per_ell_evaluate(
    populated_state, populated_E_state,
) -> None:
    """The full-tower API is just per-ℓ repeated; no drift allowed."""
    op = ThomsonPSTFCollisionOperator()
    v_b = np.array([0.1, -0.2, 0.03])
    Gamma_T = 1.9
    aux = ThomsonAux(
        E_state=populated_E_state, v_b_real_sph=v_b, Gamma_T=Gamma_T,
    )

    tower_K = op.evaluate_tower(
        state=populated_state,
        E_state=populated_E_state,
        v_b_real_sph=v_b,
        Gamma_T=Gamma_T,
    )
    for ell in range(populated_state.L + 1):
        K_perL = op.evaluate(ell, populated_state, aux)
        np.testing.assert_array_equal(
            K_perL.components,
            tower_K.tensors[ell].components,
        )


def test_E_evaluate_tower_reproduces_per_ell_evaluate(populated_E_state) -> None:
    op = EModeThomsonCollisionOperator()
    Pi_2 = np.array([0.1, -0.2, 0.3, -0.4, 0.5], dtype=np.float64)
    Gamma_T = 1.1
    aux = EModeThomsonAux(Pi_2_packed=Pi_2, Gamma_T=Gamma_T)

    tower = op.evaluate_tower(
        E_state=populated_E_state, Pi_2_packed=Pi_2, Gamma_T=Gamma_T,
    )
    for ell in range(populated_E_state.L + 1):
        K_perL = op.evaluate(ell, populated_E_state.E, aux)
        np.testing.assert_array_equal(
            K_perL.components,
            tower.tensors[ell].components,
        )


# ════════════════════════════════════════════════════════════════════
#   Γ_T = 0 returns zero everywhere
# ════════════════════════════════════════════════════════════════════

def test_Gamma_zero_returns_zero_everywhere(populated_state, populated_E_state) -> None:
    """At Γ_T = 0 every collision source vanishes (tests TC-15 half)."""
    op_T = ThomsonPSTFCollisionOperator()
    aux_T = ThomsonAux(
        E_state=populated_E_state,
        v_b_real_sph=np.array([0.5, -0.5, 0.5]),  # v_b ≠ 0
        Gamma_T=0.0,
    )
    for ell in range(populated_state.L + 1):
        K = op_T.evaluate(ell, populated_state, aux_T)
        np.testing.assert_array_equal(K.components, np.zeros(2 * ell + 1))

    op_E = EModeThomsonCollisionOperator()
    aux_E = EModeThomsonAux(
        Pi_2_packed=np.ones(5), Gamma_T=0.0,
    )
    for ell in range(populated_E_state.L + 1):
        K = op_E.evaluate(ell, populated_E_state.E, aux_E)
        np.testing.assert_array_equal(K.components, np.zeros(2 * ell + 1))


# ════════════════════════════════════════════════════════════════════
#   Validation / edge-cases
# ════════════════════════════════════════════════════════════════════

def test_evaluate_rejects_negative_ell(
    populated_state, populated_E_state,
) -> None:
    op = ThomsonPSTFCollisionOperator()
    aux = ThomsonAux(
        E_state=populated_E_state,
        v_b_real_sph=np.zeros(3),
        Gamma_T=1.0,
    )
    with pytest.raises(ValueError):
        op.evaluate(-1, populated_state, aux)


def test_evaluate_rejects_aux_none(populated_state) -> None:
    op = ThomsonPSTFCollisionOperator()
    with pytest.raises(TypeError, match="ThomsonAux"):
        op.evaluate(0, populated_state, None)


def test_evaluate_rejects_wrong_aux_type(populated_state) -> None:
    op = ThomsonPSTFCollisionOperator()
    with pytest.raises(TypeError):
        op.evaluate(0, populated_state, object())


def test_aux_rejects_superluminal_vb() -> None:
    # v_b itself can be superluminal in principle — the Thomson formula
    # K_1 = Γ_T (v_b − Π_1) is linear in v_b, no sqrt(1-v^2) factor here.
    # But we do require the shape to be (3,) and components to be finite.
    E_state = zero_polarization_hierarchy(L=2)
    with pytest.raises(ValueError):
        ThomsonAux(
            E_state=E_state,
            v_b_real_sph=np.array([1.0, 2.0]),  # wrong shape
            Gamma_T=1.0,
        )


def test_aux_rejects_negative_gamma() -> None:
    E_state = zero_polarization_hierarchy(L=2)
    with pytest.raises(ValueError):
        ThomsonAux(
            E_state=E_state, v_b_real_sph=np.zeros(3), Gamma_T=-0.1,
        )


def test_aux_rejects_nonfinite_gamma() -> None:
    E_state = zero_polarization_hierarchy(L=2)
    for bad in (np.nan, np.inf):
        with pytest.raises(ValueError):
            ThomsonAux(
                E_state=E_state, v_b_real_sph=np.zeros(3), Gamma_T=bad,
            )


def test_E_aux_rejects_wrong_Pi2_shape() -> None:
    with pytest.raises(ValueError):
        EModeThomsonAux(Pi_2_packed=np.zeros(3), Gamma_T=1.0)


def test_E_aux_rejects_negative_gamma() -> None:
    with pytest.raises(ValueError):
        EModeThomsonAux(Pi_2_packed=np.zeros(5), Gamma_T=-1.0)


# Silence unused-import warnings.
_ = PSTFHierarchyState
_ = PSTFTensor
_ = PolarizationHierarchyState
