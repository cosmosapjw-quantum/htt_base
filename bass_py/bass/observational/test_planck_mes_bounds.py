"""
Test suite: bass/observational/planck_mes_bounds.py  (Week 4 Day 1)
====================================================================

Pastén Option B core — Planck 2018 Commander MES re-derivation.

Test classes (8):
  1. TestCosmologicalConstants        — T₀ and PlanckLowL_Commander values
  2. TestPowerSpectrumConversion      — C_ℓ and ε_ℓ formulas
  3. TestMESBounds                    — σ/Θ, ω/Θ, u̇/Θ from ε_ℓ
  4. TestDocumentedValueReproduction  — match tomographic_MES_framework §2.2
  5. TestReferenceSourceEnum          — provenance tag stability
  6. TestCentralVsUpper               — 2σ widening
  7. TestEdgeCases                    — invalid inputs
  8. TestFormattingHelper             — format_bounds

Target: ~35 tests.

Documented reference values (`tomographic_MES_framework.md §2.2`):
  ε₂ < 4.7 × 10⁻⁶,  ε₃ < 7.7 × 10⁻⁶
  σ/Θ < 9.4 × 10⁻⁶, ω/Θ < 8.2 × 10⁻⁶
  u̇/Θ < 9.4 × 10⁻⁶  (2σ upper limits)
"""
from __future__ import annotations

import math
import pytest

from bass.observational.planck_mes_bounds import (
    # Constants
    T_CMB_K,
    T_CMB_MICROK,
    PLANCK_2018_COMMANDER,
    DOCUMENTED_REFERENCE,
    # Enums
    ReferenceSource,
    # Dataclasses
    PlanckLowL_Commander,
    MESBounds,
    DocumentedReferenceTable,
    # Functions
    compute_C_ell,
    compute_epsilon_ell,
    compute_mes_bounds,
    compute_mes_bounds_2sigma_upper,
    compute_planck_central_bounds,
    format_bounds,
)


# ============================================================================
# Test Class 1 - Cosmological constants
# ============================================================================

class TestCosmologicalConstants:
    """T₀ and PlanckLowL_Commander data sources."""

    def test_T_CMB_fixsen_2009_value(self):
        assert T_CMB_K == pytest.approx(2.7255, abs=1e-10)

    def test_T_CMB_microK_consistency(self):
        assert T_CMB_MICROK == pytest.approx(T_CMB_K * 1e6, rel=1e-14)

    def test_planck_D2_central_matches_arxiv_1807_06205(self):
        assert PLANCK_2018_COMMANDER.D_2_central == pytest.approx(201.5, abs=0.1)

    def test_planck_D2_sigma_matches_arxiv_1807_06205(self):
        assert PLANCK_2018_COMMANDER.D_2_sigma == pytest.approx(96.6, abs=0.1)

    def test_planck_D3_central_matches_arxiv_1807_06205(self):
        assert PLANCK_2018_COMMANDER.D_3_central == pytest.approx(1034.0, abs=1.0)

    def test_planck_D3_sigma_matches_arxiv_1807_06205(self):
        assert PLANCK_2018_COMMANDER.D_3_sigma == pytest.approx(236.0, abs=1.0)

    def test_planck_dataclass_is_frozen(self):
        with pytest.raises(Exception):
            PLANCK_2018_COMMANDER.D_2_central = 999.0


# ============================================================================
# Test Class 2 - Power spectrum conversion
# ============================================================================

class TestPowerSpectrumConversion:
    """C_ℓ = 2π D_ℓ / [ℓ(ℓ+1)] and ε_ℓ formula."""

    def test_C_ell_formula_ell_2(self):
        D_2 = 201.5
        expected = 2 * math.pi * D_2 / (2 * 3)
        assert compute_C_ell(D_2, 2) == pytest.approx(expected, rel=1e-14)

    def test_C_ell_formula_ell_3(self):
        D_3 = 1034.0
        expected = 2 * math.pi * D_3 / (3 * 4)
        assert compute_C_ell(D_3, 3) == pytest.approx(expected, rel=1e-14)

    def test_C_ell_zero_D_gives_zero(self):
        assert compute_C_ell(0.0, 2) == 0.0

    def test_C_ell_rejects_ell_less_than_1(self):
        with pytest.raises(ValueError, match="ell"):
            compute_C_ell(100.0, 0)

    def test_C_ell_rejects_negative_D(self):
        with pytest.raises(ValueError, match="non-negative"):
            compute_C_ell(-1.0, 2)

    def test_epsilon_ell_formula(self):
        # ε_ℓ² = [(2ℓ+1) / (4π)] × C_ℓ / T₀²
        D_2 = 201.5
        C_2 = compute_C_ell(D_2, 2)
        expected_sq = 5.0 / (4 * math.pi) * C_2 / (T_CMB_MICROK ** 2)
        expected = math.sqrt(expected_sq)
        assert compute_epsilon_ell(D_2, 2) == pytest.approx(expected, rel=1e-14)

    def test_epsilon_ell_is_nonnegative(self):
        assert compute_epsilon_ell(0.0, 2) == 0.0
        assert compute_epsilon_ell(100.0, 2) > 0

    def test_epsilon_ell_rejects_invalid_ell(self):
        with pytest.raises(ValueError):
            compute_epsilon_ell(100.0, 0)

    def test_epsilon_ell_rejects_zero_T0(self):
        with pytest.raises(ValueError, match="T0_microK"):
            compute_epsilon_ell(100.0, 2, T0_microK=0.0)


# ============================================================================
# Test Class 3 - MES kinematic bounds
# ============================================================================

class TestMESBounds:
    """σ/Θ = 2ε₂, ω/Θ = √3 ε₂, u̇/Θ = max(3ε₁^res, 2ε₂, ε₃)."""

    def test_returns_MESBounds_instance(self):
        result = compute_mes_bounds(D_2=201.5, D_3=1034.0)
        assert isinstance(result, MESBounds)

    def test_sigma_bound_is_2_epsilon_2(self):
        result = compute_mes_bounds(D_2=201.5, D_3=1034.0)
        assert result.sigma_over_Theta == pytest.approx(
            2.0 * result.epsilon_2, rel=1e-14
        )

    def test_omega_bound_is_sqrt3_epsilon_2(self):
        result = compute_mes_bounds(D_2=201.5, D_3=1034.0)
        assert result.omega_over_Theta == pytest.approx(
            math.sqrt(3.0) * result.epsilon_2, rel=1e-14
        )

    def test_omega_sigma_ratio_is_sqrt3_over_2(self):
        result = compute_mes_bounds(D_2=201.5, D_3=1034.0)
        assert (
            result.omega_over_Theta / result.sigma_over_Theta
        ) == pytest.approx(math.sqrt(3.0) / 2.0, rel=1e-14)

    def test_udot_bound_is_2eps2_when_eps3_smaller(self):
        # Planck regime: 2 ε₂ ≈ 9.4e-6 > ε₃ ≈ 7.7e-6
        result = compute_mes_bounds_2sigma_upper()
        assert result.udot_over_Theta == pytest.approx(
            2.0 * result.epsilon_2, rel=1e-14
        )

    def test_udot_bound_picks_eps3_when_dominant(self):
        # Synthetic: give ε₃ amplitude that dominates 2ε₂
        # Choose D_3 such that ε₃ >> 2 ε₂
        result = compute_mes_bounds(D_2=1.0, D_3=1e8)
        # ε₃ will dominate
        assert result.udot_over_Theta == pytest.approx(
            result.epsilon_3, rel=1e-14
        )

    def test_udot_bound_picks_3eps1res_when_dominant(self):
        # With eps1_res = 1e-3, 3×eps1_res = 3e-3, way above CMB ε₂,₃
        result = compute_mes_bounds(
            D_2=201.5, D_3=1034.0, epsilon_1_residual=1e-3,
        )
        assert result.udot_over_Theta == pytest.approx(3e-3, rel=1e-14)

    def test_MESBounds_is_frozen(self):
        result = compute_mes_bounds(D_2=201.5, D_3=1034.0)
        with pytest.raises(Exception):
            result.epsilon_2 = 0.0

    def test_bounds_positive_for_positive_D(self):
        result = compute_mes_bounds(D_2=201.5, D_3=1034.0)
        assert result.epsilon_2 > 0
        assert result.epsilon_3 > 0
        assert result.sigma_over_Theta > 0
        assert result.omega_over_Theta > 0
        assert result.udot_over_Theta > 0


# ============================================================================
# Test Class 4 - Reproduction of documented values
# ============================================================================

class TestDocumentedValueReproduction:
    """2σ upper-limit bounds match tomographic_MES_framework §2.2 values."""

    # Documented values have 2 sig fig; allow 3% rel err band
    TOLERANCE = 0.03

    def test_epsilon_2_reproduces(self):
        upper = compute_mes_bounds_2sigma_upper()
        rel_err = abs(upper.epsilon_2 - DOCUMENTED_REFERENCE.epsilon_2_2sigma)
        rel_err /= DOCUMENTED_REFERENCE.epsilon_2_2sigma
        assert rel_err < self.TOLERANCE, (
            f"ε₂ observed={upper.epsilon_2:.3e}, "
            f"expected={DOCUMENTED_REFERENCE.epsilon_2_2sigma:.3e}, "
            f"rel_err={rel_err:.2%}"
        )

    def test_epsilon_3_reproduces(self):
        upper = compute_mes_bounds_2sigma_upper()
        rel_err = abs(upper.epsilon_3 - DOCUMENTED_REFERENCE.epsilon_3_2sigma)
        rel_err /= DOCUMENTED_REFERENCE.epsilon_3_2sigma
        assert rel_err < self.TOLERANCE

    def test_sigma_over_Theta_reproduces(self):
        upper = compute_mes_bounds_2sigma_upper()
        rel_err = abs(
            upper.sigma_over_Theta - DOCUMENTED_REFERENCE.sigma_over_Theta_2sigma
        ) / DOCUMENTED_REFERENCE.sigma_over_Theta_2sigma
        assert rel_err < self.TOLERANCE

    def test_omega_over_Theta_reproduces(self):
        upper = compute_mes_bounds_2sigma_upper()
        rel_err = abs(
            upper.omega_over_Theta - DOCUMENTED_REFERENCE.omega_over_Theta_2sigma
        ) / DOCUMENTED_REFERENCE.omega_over_Theta_2sigma
        assert rel_err < self.TOLERANCE

    def test_udot_over_Theta_reproduces(self):
        upper = compute_mes_bounds_2sigma_upper()
        rel_err = abs(
            upper.udot_over_Theta - DOCUMENTED_REFERENCE.udot_over_Theta_2sigma
        ) / DOCUMENTED_REFERENCE.udot_over_Theta_2sigma
        assert rel_err < self.TOLERANCE

    def test_improvement_over_cobe_is_order_of_magnitude(self):
        """SAG97 COBE bound ε ~ 10⁻⁴; Planck ε₂ ~ 5×10⁻⁶. ~20× improvement."""
        upper = compute_mes_bounds_2sigma_upper()
        improvement = DOCUMENTED_REFERENCE.cobe_epsilon_floor / upper.epsilon_2
        assert improvement > 10, (
            f"Planck improvement over COBE = {improvement:.1f}× "
            f"(expected > 10×)"
        )


# ============================================================================
# Test Class 5 - Reference source enum
# ============================================================================

class TestReferenceSourceEnum:
    """Provenance tag stability."""

    def test_has_three_members(self):
        assert len(list(ReferenceSource)) == 3

    def test_cobe_member_references_SAG97(self):
        val = ReferenceSource.COBE_SAG97.value
        assert "1997" in val
        assert "Stoeger" in val

    def test_planck_this_work_tag(self):
        val = ReferenceSource.PLANCK_2018_THIS_WORK.value
        assert "Planck" in val
        assert "this work" in val

    def test_maluf_neves_tag(self):
        val = ReferenceSource.MALUF_NEVES_2021.value
        assert "Maluf" in val


# ============================================================================
# Test Class 6 - Central vs 2σ upper relationship
# ============================================================================

class TestCentralVsUpper:
    """2σ upper > central, and relationship is correct."""

    def test_upper_exceeds_central(self):
        central = compute_planck_central_bounds()
        upper = compute_mes_bounds_2sigma_upper()
        assert upper.epsilon_2 > central.epsilon_2
        assert upper.epsilon_3 > central.epsilon_3
        assert upper.sigma_over_Theta > central.sigma_over_Theta

    def test_confidence_level_tag(self):
        central = compute_planck_central_bounds()
        upper = compute_mes_bounds_2sigma_upper()
        assert central.confidence_level == "central"
        assert upper.confidence_level == "2sigma_upper"

    def test_upper_uses_D_plus_2_sigma(self):
        upper = compute_mes_bounds_2sigma_upper()
        # Reconstruct what the function should have used
        D_2_upper = (
            PLANCK_2018_COMMANDER.D_2_central
            + 2 * PLANCK_2018_COMMANDER.D_2_sigma
        )
        expected_eps_2 = compute_epsilon_ell(D_2_upper, 2)
        assert upper.epsilon_2 == pytest.approx(expected_eps_2, rel=1e-14)


# ============================================================================
# Test Class 7 - Edge cases and input validation
# ============================================================================

class TestEdgeCases:
    """Invalid inputs raise ValueError with informative messages."""

    def test_compute_mes_bounds_rejects_negative_D_2(self):
        with pytest.raises(ValueError):
            compute_mes_bounds(D_2=-1.0, D_3=1034.0)

    def test_compute_mes_bounds_rejects_negative_D_3(self):
        with pytest.raises(ValueError):
            compute_mes_bounds(D_2=201.5, D_3=-1.0)

    def test_zero_D_gives_zero_epsilon(self):
        bounds = compute_mes_bounds(D_2=0.0, D_3=0.0)
        assert bounds.epsilon_2 == 0.0
        assert bounds.epsilon_3 == 0.0
        assert bounds.sigma_over_Theta == 0.0

    def test_compute_mes_bounds_rejects_negative_T0(self):
        with pytest.raises(ValueError):
            compute_mes_bounds(D_2=201.5, D_3=1034.0, T0_microK=-1.0)


# ============================================================================
# Test Class 8 - Formatting helper
# ============================================================================

class TestFormattingHelper:
    """format_bounds output shape."""

    def test_format_contains_all_bounds(self):
        upper = compute_mes_bounds_2sigma_upper()
        text = format_bounds(upper)
        assert "ε₂" in text
        assert "ε₃" in text
        assert "σ/Θ" in text
        assert "ω/Θ" in text
        assert "u̇/Θ" in text

    def test_format_contains_source_and_confidence(self):
        upper = compute_mes_bounds_2sigma_upper()
        text = format_bounds(upper)
        assert "2sigma_upper" in text
        assert "PLANCK" in text.upper()
