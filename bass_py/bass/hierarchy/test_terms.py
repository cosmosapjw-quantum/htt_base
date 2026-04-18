"""Tests H-13 .. H-17 for ``bass.hierarchy.terms``.

Covers the PSTF multipole RHS term functions specified in
``docs/lowell_bianchi/02_multipole_hierarchy_spec.md §11.3``:

- H-13: T1 at Θ = 1, Π_2 = unit → (4/3) × unit.
- H-14: T7 with σ = 0 is zero (LB-2b; stub raises).
- H-15: T9 at ℓ = 1 is zero (no monopole-from-dipole-shear).
- H-16: T9 at ℓ = 2 with σ = Σ_+ axisymmetric, Π_0 = 1 → −4 σ.
- H-17: FLRW sum (σ = ω = A = 0) reduces to T1 + T3 + T2 (background).

Additional coverage:
- LB-2a stub functions T4, T5, T6, T7 raise ``NotImplementedError``.
- Numerical smoke at ℓ > 2 for T8 and T9.
- ``zero_nabla_operator`` shape handling.
"""
from __future__ import annotations

import numpy as np
import pytest

from bass.background.tetrad_state import axisymmetric_sigma_tensor
from bass.hierarchy import (
    PSTFTensor,
    T1_expansion,
    T2_gradient,
    T3_divergence,
    T4_accel_divergence,
    T5_accel_gradient,
    T6_vorticity,
    T7_shear_up,
    T8_shear_same,
    T9_shear_down,
    pstf_to_tensor,
    sym_trace_free,
    verify_pstf_invariants,
    zero_nabla_operator,
)


# ════════════════════════════════════════════════════════════════════
#   H-13 — T1 at Θ = 1
# ════════════════════════════════════════════════════════════════════

def test_h13_T1_unit_quadrupole() -> None:
    """H-13: T1 with Θ = 1 and a rank-2 PSTF unit input scales by 4/3."""
    unit = axisymmetric_sigma_tensor(1.0, 0.0)  # already PSTF rank 2
    out = T1_expansion(ell=2, Pi_ell_full=unit, Theta=1.0)
    assert np.allclose(out, (4.0 / 3.0) * unit, rtol=0, atol=1e-14)


def test_h13_T1_zero_at_zero_theta() -> None:
    unit = axisymmetric_sigma_tensor(1.0, 0.0)
    out = T1_expansion(ell=2, Pi_ell_full=unit, Theta=0.0)
    assert np.max(np.abs(out)) < 1e-15


def test_h13_T1_scales_linearly_in_theta() -> None:
    rng = np.random.default_rng(77)
    T = sym_trace_free(rng.normal(size=(3, 3, 3)))
    for theta in (-1.5, 0.3, 100.0):
        out = T1_expansion(ell=3, Pi_ell_full=T, Theta=theta)
        assert np.allclose(out, (4.0 / 3.0) * theta * T, rtol=0, atol=1e-12)


def test_h13_T1_shape_mismatch_raises() -> None:
    with pytest.raises(ValueError):
        T1_expansion(ell=3, Pi_ell_full=np.zeros((3, 3)), Theta=1.0)


# ════════════════════════════════════════════════════════════════════
#   H-14 — T7 stub (LB-2a defers; LB-2b implements)
# ════════════════════════════════════════════════════════════════════

def test_h14_T7_raises_not_implemented_for_lb2a() -> None:
    """H-14 (adapted): LB-2a defers T7 to LB-2b; calling must raise."""
    with pytest.raises(NotImplementedError):
        T7_shear_up(4)


# ════════════════════════════════════════════════════════════════════
#   H-15 — T9 at ℓ = 1 is zero (no Π_{-1})
# ════════════════════════════════════════════════════════════════════

def test_h15_T9_at_ell_1_is_zero() -> None:
    """H-15: T9 requires ℓ ≥ 2; at ℓ = 1 it is exactly zero."""
    sigma = axisymmetric_sigma_tensor(1.0, 0.0)
    # For ℓ=1 there is no Π_{ℓ−2} tensor; pass a rank-0 placeholder that
    # the function must still reject as "ℓ too low".
    dummy = np.array(1.0)
    out = T9_shear_down(ell=1, Pi_ell_minus_2_full=dummy, sigma_tensor=sigma)
    assert out.shape == (3,)
    assert np.max(np.abs(out)) < 1e-15


def test_h15_T9_at_ell_0_is_zero() -> None:
    sigma = axisymmetric_sigma_tensor(1.0, 0.0)
    dummy = np.array(0.0)
    out = T9_shear_down(ell=0, Pi_ell_minus_2_full=dummy, sigma_tensor=sigma)
    assert np.max(np.abs(out)) < 1e-15


# ════════════════════════════════════════════════════════════════════
#   H-16 — T9 at ℓ = 2 with Σ_+ axisymmetric, monopole Π_0 = 1
# ════════════════════════════════════════════════════════════════════

def test_h16_T9_ell_2_shear_injection() -> None:
    """H-16: T9 at ℓ = 2 with monopole = 1 and σ = diag(−2,1,1)/√6 → −4 σ.

    Formula: T9_{ab} = −(ℓ+2) STF(σ_{ab} Π) = −4 σ_{ab} × 1 (σ already STF).

    Reference: lowell §6 (ℓ=2 worked example); Pontzen-Challinor 2007 eq C4.
    """
    sigma = axisymmetric_sigma_tensor(1.0, 0.0)
    monopole = np.array(1.0)
    T9 = T9_shear_down(ell=2, Pi_ell_minus_2_full=monopole, sigma_tensor=sigma)
    expected = -4.0 * sigma
    assert np.allclose(T9, expected, rtol=0, atol=1e-14), (
        f"T9(ℓ=2) mismatch: got\n{T9}\nexpected\n{expected}"
    )


def test_h16_T9_ell_2_generic_monopole_scales() -> None:
    """Generic monopole scales the shear linearly."""
    sigma = axisymmetric_sigma_tensor(0.5, -0.3)
    for pi0 in (1.0, 2.7, -4.2):
        T9 = T9_shear_down(
            ell=2, Pi_ell_minus_2_full=np.array(pi0), sigma_tensor=sigma
        )
        expected = -4.0 * pi0 * sigma
        assert np.allclose(T9, expected, rtol=0, atol=1e-14)


# ════════════════════════════════════════════════════════════════════
#   H-17 — FLRW sum reduces to T1 + T2 + T3 (σ = ω = A = 0)
# ════════════════════════════════════════════════════════════════════

def test_h17_flrw_sum_is_T1_only_at_background() -> None:
    """H-17: σ = ω = A = 0 and homogeneous background ⇒ T2, T3 = 0.

    Only T1 contributes; T4/T5/T6 drop by ω = A = 0, T7/T8/T9 drop by
    σ = 0. The net RHS is therefore ``(4/3) Θ Π_ℓ`` at every ℓ.
    """
    rng = np.random.default_rng(1234)
    theta = 0.123
    for ell in [0, 1, 2, 3]:
        # Build a PSTF Π_ℓ:
        if ell == 0:
            Pi_full = np.array(rng.normal())
        else:
            Pi_full = sym_trace_free(rng.normal(size=(3,) * ell))
        # Build Π_{ℓ-1} and Π_{ℓ+1} for T2, T3:
        if ell > 0:
            if ell == 1:
                Pi_minus_full = np.array(rng.normal())
            else:
                Pi_minus_full = sym_trace_free(rng.normal(size=(3,) * (ell - 1)))
        Pi_plus_full = sym_trace_free(rng.normal(size=(3,) * (ell + 1)))

        # σ = 0, so T8 and T9 vanish (T7/T4/T5/T6 stubbed off).
        T1 = T1_expansion(ell, Pi_full, theta)
        T2 = (
            T2_gradient(ell, Pi_minus_full, zero_nabla_operator)
            if ell > 0
            else np.array(0.0)
        )
        T3 = T3_divergence(ell, Pi_plus_full, zero_nabla_operator)
        sigma = np.zeros((3, 3))
        T8 = T8_shear_same(ell, Pi_full, sigma)
        # At ell=0 T8 returns scalar 0; at ell≥1 it returns rank-ell tensor.
        if ell < 2:
            Pi_mm = np.array(0.0)
        else:
            Pi_mm = sym_trace_free(rng.normal(size=(3,) * (ell - 2)))
        T9 = T9_shear_down(ell, Pi_mm, sigma)
        # Verify T2, T3 = 0 at background
        assert np.max(np.abs(T2)) < 1e-15, f"T2 non-zero at ell={ell}"
        assert np.max(np.abs(T3)) < 1e-15, f"T3 non-zero at ell={ell}"
        # Verify T8, T9 = 0 at σ=0
        assert np.max(np.abs(T8)) < 1e-15, f"T8 non-zero at σ=0, ell={ell}"
        assert np.max(np.abs(T9)) < 1e-15, f"T9 non-zero at σ=0, ell={ell}"
        # T1 should equal (4/3) θ Π
        if ell == 0:
            assert abs(float(T1) - (4.0 / 3.0) * theta * float(Pi_full)) < 1e-14
        else:
            assert np.allclose(
                T1, (4.0 / 3.0) * theta * Pi_full, rtol=0, atol=1e-12
            )


# ════════════════════════════════════════════════════════════════════
#   Deferred-stub guardrails (T4, T5, T6 raise NotImplementedError)
# ════════════════════════════════════════════════════════════════════

def test_T4_raises_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        T4_accel_divergence(2)


def test_T5_raises_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        T5_accel_gradient(2)


def test_T6_raises_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        T6_vorticity(2)


# ════════════════════════════════════════════════════════════════════
#   T2, T3 at background: explicit zero and shape check
# ════════════════════════════════════════════════════════════════════

def test_T2_ell_0_returns_scalar_zero() -> None:
    out = T2_gradient(0, np.array(1.0), zero_nabla_operator)
    assert out.ndim == 0 and float(out) == 0.0


def test_T2_ell_2_homogeneous_background_is_zero() -> None:
    rng = np.random.default_rng(321)
    Pi1 = rng.normal(size=3)
    out = T2_gradient(2, Pi1, zero_nabla_operator)
    assert out.shape == (3, 3)
    assert np.max(np.abs(out)) < 1e-15


def test_T3_ell_3_homogeneous_background_is_zero() -> None:
    rng = np.random.default_rng(987)
    Pi4 = sym_trace_free(rng.normal(size=(3, 3, 3, 3)))
    out = T3_divergence(3, Pi4, zero_nabla_operator)
    assert out.shape == (3, 3, 3)
    assert np.max(np.abs(out)) < 1e-15


def test_T3_ell_0_from_homogeneous_dipole_is_zero() -> None:
    Pi1 = np.ones(3)
    out = T3_divergence(0, Pi1, zero_nabla_operator)
    # ell=0 divergence: rank-0 output
    assert float(out) == 0.0


# ════════════════════════════════════════════════════════════════════
#   T8 extra coverage: ℓ > 2, ℓ = 1
# ════════════════════════════════════════════════════════════════════

def test_T8_ell_1_is_sigma_Pi() -> None:
    """At ℓ = 1 T8 gives T8_a = 5 σ_{ab} Π^b / (2·1+3) = (5/5) σ_{ab} Π^b."""
    sigma = axisymmetric_sigma_tensor(1.0, 0.0)
    Pi1 = np.array([1.0, 2.0, -3.0])
    out = T8_shear_same(ell=1, Pi_ell_full=Pi1, sigma_tensor=sigma)
    prefactor = 5.0 * 1.0 / (2.0 * 1.0 + 3.0)  # = 1
    # raw: np.tensordot(Pi1, sigma, axes=([-1],[1])) -> Σ_k Pi1[k] σ[j, k]
    expected_raw = sigma @ Pi1  # σ symmetric so same as σ^T @ Pi1
    expected = prefactor * sym_trace_free(expected_raw)
    assert np.allclose(out, expected, rtol=0, atol=1e-14)


def test_T8_output_is_pstf_at_ell_3() -> None:
    """T8 output is automatically PSTF after sym_trace_free."""
    sigma = axisymmetric_sigma_tensor(0.7, 0.2)
    rng = np.random.default_rng(42)
    Pi3 = sym_trace_free(rng.normal(size=(3, 3, 3)))
    out = T8_shear_same(ell=3, Pi_ell_full=Pi3, sigma_tensor=sigma)
    ok, msg = verify_pstf_invariants(out, tol=1e-12)
    assert ok, msg


def test_T8_wrong_sigma_shape_raises() -> None:
    with pytest.raises(ValueError):
        T8_shear_same(ell=2, Pi_ell_full=np.zeros((3, 3)), sigma_tensor=np.zeros((2, 2)))


def test_T9_wrong_sigma_shape_raises() -> None:
    with pytest.raises(ValueError):
        T9_shear_down(ell=2, Pi_ell_minus_2_full=np.array(1.0), sigma_tensor=np.zeros((4, 4)))


def test_T9_ell_3_output_is_pstf() -> None:
    """T9 at ℓ=3 injects monopole × σ ⊗ Π_1; output is PSTF rank 3."""
    sigma = axisymmetric_sigma_tensor(0.4, 0.1)
    rng = np.random.default_rng(1984)
    Pi1 = rng.normal(size=3)
    out = T9_shear_down(ell=3, Pi_ell_minus_2_full=Pi1, sigma_tensor=sigma)
    ok, msg = verify_pstf_invariants(out, tol=1e-12)
    assert ok, msg


# ════════════════════════════════════════════════════════════════════
#   zero_nabla_operator shape contract
# ════════════════════════════════════════════════════════════════════

def test_zero_nabla_operator_gradient_raises_rank() -> None:
    out = zero_nabla_operator(np.zeros((3, 3)), kind="gradient")
    assert out.shape == (3, 3, 3)
    assert np.all(out == 0.0)


def test_zero_nabla_operator_divergence_lowers_rank() -> None:
    out = zero_nabla_operator(np.zeros((3, 3, 3)), kind="divergence")
    assert out.shape == (3, 3)
    out0 = zero_nabla_operator(np.zeros(3), kind="divergence")
    assert out0.ndim == 0


def test_zero_nabla_operator_invalid_kind() -> None:
    with pytest.raises(ValueError):
        zero_nabla_operator(np.zeros(3), kind="curl")


def test_zero_nabla_operator_divergence_rank0_raises() -> None:
    with pytest.raises(ValueError):
        zero_nabla_operator(np.array(1.0), kind="divergence")
