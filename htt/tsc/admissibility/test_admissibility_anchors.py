"""Regression anchors for ``tsc.admissibility`` (Tier-D).

Pins the rational-arithmetic three-bound hierarchy outputs, the realizability
verdicts, and the domain flags — all BASS-independent, pure algebra.

Cross-package consistency: every bound function in
``tsc.admissibility.three_bound_hierarchy`` must match the corresponding
``tsc_legacy.htt_core_bounds`` function bit-exact at canonical S1/S2a/S2c
ε₁ values.
A drift on either side fires here.

Scope note: TSC's ``Sigma2_max`` uses the *uncorrected* ``B_sigma`` exactly
(Corollary 3.1) while HTT's ``Sig2_max_MES`` uses the VT-07-corrected
``B_sigma_corrected`` (Corollary 3.1 + frame-bias correction). These are
different observables by design; the two ceilings must NOT be identified.
"""
from __future__ import annotations

import pytest

from tsc.admissibility.domain import (
    DomainFlag,
    check_be_eta_nonpositive,
    check_theta_positive,
    check_weight_simplex,
)
from tsc.admissibility.realizability import (
    verify_flrw_limit_admissible,
    verify_large_dipole_breaks_positivity,
    verify_small_shear_admissible,
)
from tsc.admissibility.three_bound_hierarchy import (
    A2_max,
    B_accel as tsc_B_accel,
    B_omega as tsc_B_omega,
    B_sigma as tsc_B_sigma,
    BIANCHI_TYPES,
    HierarchyViolationError,
    Sigma2_max,
    ThreeBoundReport,
    W2_max,
    compute_three_bound_hierarchy,
    evaluate_all_bianchi_types,
)

from tsc_legacy.htt_core_bounds import (
    B_accel as htt_B_accel,
    B_omega as htt_B_omega,
    B_sigma as htt_B_sigma,
)


# ─── Canonical scenarios ──────────────────────────────────────────────
_S1_EPS1  = 1.233e-3
_S2A_EPS1 = 1.476e-3
_S2C_EPS1 = 3.296e-3
_EPS2 = 3.559629e-6
_EPS3 = 6.065291e-6


# ═══════════════════════════════════════════════════════════════════════
# Part 1 — tsc.admissibility.three_bound_hierarchy: cross-consistency
# ═══════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("eps1", [_S1_EPS1, _S2A_EPS1, _S2C_EPS1])
def test_tsc_htt_B_sigma_bit_identical(eps1):
    """TSC rational-arithmetic B_σ must match HTT float B_σ bit-exact."""
    assert tsc_B_sigma(eps1, _EPS2, _EPS3) == htt_B_sigma(eps1, _EPS2, _EPS3)


@pytest.mark.parametrize("eps1", [_S1_EPS1, _S2A_EPS1, _S2C_EPS1])
def test_tsc_htt_B_omega_bit_identical(eps1):
    """TSC B_ω = HTT B_ω bit-exact."""
    assert tsc_B_omega(eps1, _EPS2, _EPS3) == htt_B_omega(eps1, _EPS2, _EPS3)


@pytest.mark.parametrize("eps1", [_S1_EPS1, _S2A_EPS1, _S2C_EPS1])
def test_tsc_htt_B_accel_bit_identical(eps1):
    """TSC B_u̇ = HTT B_u̇ bit-exact."""
    assert tsc_B_accel(eps1, _EPS2, _EPS3) == htt_B_accel(eps1, _EPS2, _EPS3)


# ═══════════════════════════════════════════════════════════════════════
# Part 2 — MES ceilings (uncorrected) pinned
# ═══════════════════════════════════════════════════════════════════════
def test_Sigma2_max_pinned_at_S1():
    """Σ²_max = (3/2)·B_σ² (Corollary 3.1, uncorrected)."""
    assert Sigma2_max(_S1_EPS1, _EPS2, _EPS3) == pytest.approx(
        6.416662673421047e-06, abs=1e-18
    )


def test_W2_max_pinned_at_S1():
    """W²_max = (3/2)·B_ω² (Corollary 3.2)."""
    assert W2_max(_S1_EPS1, _EPS2, _EPS3) == pytest.approx(
        1.3074195969658773e-06, abs=1e-18
    )


def test_A2_max_pinned_at_S1():
    """A²_max = (3/2)·B_u̇² (Corollary 3.3)."""
    assert A2_max(_S1_EPS1, _EPS2, _EPS3) == pytest.approx(
        1.2962602713874913e-06, abs=1e-18
    )


def test_Sigma2_max_uncorrected_differs_from_htt_corrected():
    """TSC Σ²_max (Corollary 3.1) and HTT Sig2_max_MES (VT-07 corrected) differ.

    Protects the design invariant that the two are *different observables*;
    if a refactor ever aliases them, this test fires. Expected relative
    gap at S1: `~2*2.69*eps1 ≈ 6.6e-3` (leading-order frame-bias term).
    """
    from tsc_legacy.htt_core_bounds import Sig2_max_MES as htt_sig2_max

    tsc_val = Sigma2_max(_S1_EPS1, _EPS2, _EPS3)
    htt_val = htt_sig2_max(_S1_EPS1)
    # Ceiling rises under the VT-07 correction factor (1 + 2.69 ε₁)².
    assert htt_val > tsc_val
    rel_gap = (htt_val - tsc_val) / tsc_val
    # At S1 ε₁=1.233e-3: expected leading-order 2*2.69*eps1 ≈ 6.63e-3
    assert rel_gap == pytest.approx(6.63e-3, abs=5e-4)


# ═══════════════════════════════════════════════════════════════════════
# Part 3 — compute_three_bound_hierarchy report pinned
# ═══════════════════════════════════════════════════════════════════════
def test_three_bound_report_at_S1_pinned():
    """Full ThreeBoundReport output is pinned at S1."""
    rpt = compute_three_bound_hierarchy(_S1_EPS1, _EPS2, _EPS3, strict=False)
    assert rpt.type_name == "generic"
    assert rpt.eps1 == _S1_EPS1
    assert rpt.B_sigma_val == pytest.approx(2.0682782974285716e-3, abs=1e-18)
    assert rpt.B_omega_val == pytest.approx(9.336021982857143e-4,  abs=1e-18)
    assert rpt.B_accel_val == pytest.approx(9.296093342142857e-4,  abs=1e-18)
    assert rpt.Sigma2_max_val == pytest.approx(6.416662673421047e-6, abs=1e-18)
    assert rpt.ratio_omega_over_sigma == pytest.approx(0.45139099484166806, abs=1e-14)
    assert rpt.ratio_accel_over_omega == pytest.approx(0.9957231633786207,  abs=1e-14)
    assert rpt.hierarchy_strict is True


def test_HierarchyViolationError_is_ValueError_subclass():
    """The strict-mode exception is a ValueError subclass (clean catching)."""
    assert issubclass(HierarchyViolationError, ValueError)


def test_evaluate_all_bianchi_types_covers_all_9_types():
    """Evaluator returns all 9 Bianchi types at once."""
    out = evaluate_all_bianchi_types(_S1_EPS1, _EPS2, _EPS3, strict=False)
    assert len(out) == 9
    assert set(out.keys()) == set(BIANCHI_TYPES)
    # At fixed (eps1,eps2,eps3) the numerical bounds are type-invariant —
    # only the type_name label changes.
    first = next(iter(out.values()))
    for rpt in out.values():
        assert rpt.B_sigma_val == first.B_sigma_val
        assert rpt.B_omega_val == first.B_omega_val


def test_BIANCHI_TYPES_tuple_frozen():
    """9 Bianchi types, canonical order."""
    assert BIANCHI_TYPES == (
        "I", "II", "V", "VI0", "VII0", "VIII", "IX", "VIIh", "III",
    )
    assert len(BIANCHI_TYPES) == 9


# ═══════════════════════════════════════════════════════════════════════
# Part 4 — realizability verdicts
# ═══════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("xi", [-1, 0, 1])
def test_flrw_limit_admissible_all_xi(xi):
    """FLRW limit (Σ²=W²=0) must be admissible at every ξ ∈ {-1, 0, +1}."""
    assert verify_flrw_limit_admissible(xi=xi) is True


def test_flrw_limit_rejects_invalid_xi():
    """verify_flrw_limit_admissible enforces ξ ∈ {-1, 0, +1}."""
    with pytest.raises(ValueError, match="ξ"):
        verify_flrw_limit_admissible(xi=2)


@pytest.mark.parametrize("xi", [-1, 0, 1])
@pytest.mark.parametrize("Theta_1", [0.01, 0.05, 0.1])
def test_small_shear_admissible(xi, Theta_1):
    """Small-shear limit stays admissible across the valid parameter grid."""
    assert verify_small_shear_admissible(xi=xi, Theta_1=Theta_1) is True


def test_large_dipole_breaks_positivity():
    """A sufficiently large dipole must break positivity (True = correctly detected)."""
    assert verify_large_dipole_breaks_positivity() is True


# ═══════════════════════════════════════════════════════════════════════
# Part 5 — domain flags (layer-2 gate)
# ═══════════════════════════════════════════════════════════════════════
def test_theta_positive_accepts_all_positive():
    flag = check_theta_positive([0.1, 0.2, 0.5])
    assert flag.ok is True
    assert flag.reason is None


def test_theta_positive_rejects_negative():
    flag = check_theta_positive([-0.1, 0.2])
    assert flag.ok is False
    assert flag.reason == "theta_nonpositive"
    assert flag.value == -0.1


def test_be_eta_nonpositive_accepts_zero_and_negative():
    flag = check_be_eta_nonpositive([-1.0, 0.0, -0.5])
    assert flag.ok is True


def test_be_eta_nonpositive_rejects_positive():
    flag = check_be_eta_nonpositive([0.1, -0.2])
    assert flag.ok is False


def test_weight_simplex_accepts_normalized():
    flag = check_weight_simplex([0.2, 0.3, 0.5])
    assert flag.ok is True


def test_weight_simplex_rejects_unnormalized():
    flag = check_weight_simplex([0.5, 0.5, 0.5])  # sum=1.5
    assert flag.ok is False


def test_domain_flag_is_dataclass():
    """DomainFlag has the three-tuple (ok, value, reason) contract."""
    import dataclasses
    flag = DomainFlag(ok=True, value=0.1, reason=None)
    assert dataclasses.is_dataclass(flag)
    fields = {f.name for f in dataclasses.fields(flag)}
    assert fields == {"ok", "value", "reason"}
