"""
tests/test_realizability.py
============================

Week 2 Day 5 test suite for Paper I realizability (Prop 14/15).

Covers:
  §1 — AdmissibilityVerdict enum
  §2 — Layer 1: check_field_admissible (Θ > 0, BE η ≤ 0)
  §3 — Layer 2: check_gram_positive_definite (Gram PD)
  §4 — Layer 3: check_moment_admissible (T_0 > 0, |T_ℓ/T_0| bound)
  §5 — assess_realizability unified audit
  §6 — Known-limit recovery (FLRW, small shear, large-dipole break)
  §7 — BE admissibility: positive η rejected for ξ = +1
  §8 — Verdict aggregation (multiple violations)
  §9 — Boost preservation (Paper I Thm 3 consequence)

Run
---
    pytest test_realizability.py -v
"""
from __future__ import annotations

import math
import numpy as np
import pytest

from tsc.admissibility.realizability import (
    AdmissibilityVerdict,
    FieldAdmissibilityResult, check_field_admissible,
    GramPositiveDefiniteResult, check_gram_positive_definite,
    MomentAdmissibilityResult, check_moment_admissible,
    RealizabilityAudit, assess_realizability,
    verify_flrw_limit_admissible,
    verify_small_shear_admissible,
    verify_large_dipole_breaks_positivity,
)
from tsc.charts.forward_F_to_T import (
    AxisymmetricField,
    isotropic_theta, dipole_theta, quadrupole_theta,
)
from tsc.diagnostics.tangency import TangentKind


# ═══════════════════════════════════════════════════════════════
# §1 — Verdict enum
# ═══════════════════════════════════════════════════════════════

class TestAdmissibilityVerdict:
    def test_enum_values_exist(self):
        assert AdmissibilityVerdict.ADMISSIBLE.value == "admissible"
        assert AdmissibilityVerdict.FIELD_VIOLATION.value == "field_violation"
        assert AdmissibilityVerdict.GRAM_DEGENERATE.value == "gram_degenerate"
        assert AdmissibilityVerdict.MOMENT_OUT_OF_DOMAIN.value == "moment_out_of_domain"
        assert AdmissibilityVerdict.MULTIPLE_VIOLATIONS.value == "multiple_violations"


# ═══════════════════════════════════════════════════════════════
# §2 — Layer 1: Field admissibility
# ═══════════════════════════════════════════════════════════════

class TestFieldAdmissibility:
    def test_isotropic_admissible(self):
        r = check_field_admissible(isotropic_theta(1.0), xi=0)
        assert r.theta_positive
        assert r.is_admissible
        assert math.isclose(r.theta_min, 1.0)
        assert math.isclose(r.theta_max, 1.0)

    def test_small_dipole_admissible(self):
        """Θ = 1 + 0.05 P_1(μ), range [0.95, 1.05]."""
        r = check_field_admissible(dipole_theta(1.0, 0.05), xi=0)
        assert r.is_admissible
        assert math.isclose(r.theta_min, 0.95, abs_tol=1e-3)
        assert math.isclose(r.theta_max, 1.05, abs_tol=1e-3)

    def test_large_dipole_fails_positivity(self):
        """Θ = 1 + 1.2 P_1(μ), dips to -0.2 at μ = -1."""
        r = check_field_admissible(dipole_theta(1.0, 1.2), xi=0)
        assert not r.theta_positive
        assert not r.is_admissible
        assert r.theta_min < 0

    def test_negative_theta_fails(self):
        """Uniform Θ = -1 < 0."""
        Theta = AxisymmetricField(coeffs=np.array([-1.0]))
        r = check_field_admissible(Theta, xi=0)
        assert not r.theta_positive
        assert not r.is_admissible

    def test_BE_eta_positive_fails_admissibility(self):
        """For ξ = +1, η(μ) = 0.5 > 0 must fail."""
        eta = AxisymmetricField(coeffs=np.array([0.5]))
        r = check_field_admissible(isotropic_theta(1.0), xi=+1, eta=eta)
        assert not r.be_admissible
        assert not r.is_admissible

    def test_BE_eta_negative_is_admissible(self):
        """For ξ = +1, η = -0.3 ≤ 0 is admissible."""
        eta = AxisymmetricField(coeffs=np.array([-0.3]))
        r = check_field_admissible(isotropic_theta(1.0), xi=+1, eta=eta)
        assert r.is_admissible

    def test_FD_positive_eta_is_admissible(self):
        """For ξ = -1 (FD), positive η is physical (degenerate FD)."""
        eta = AxisymmetricField(coeffs=np.array([0.5]))
        r = check_field_admissible(isotropic_theta(1.0), xi=-1, eta=eta)
        assert r.is_admissible

    def test_eta_none_is_admissible(self):
        """eta = None means one-field; trivially admissible."""
        r = check_field_admissible(isotropic_theta(1.0), xi=+1, eta=None)
        assert r.is_admissible


# ═══════════════════════════════════════════════════════════════
# §3 — Layer 2: Gram PD
# ═══════════════════════════════════════════════════════════════

class TestGramPositiveDefinite:
    def test_one_field_MB_PD(self):
        """ONE_FIELD (span{x}) has 1×1 Gram = [24] (MB); trivially PD."""
        r = check_gram_positive_definite(TangentKind.ONE_FIELD, xi=0)
        assert r.is_positive_definite
        assert r.eigenvalues.shape == (1,)
        assert math.isclose(r.min_eigenvalue, 24.0, rel_tol=1e-6)
        assert math.isclose(r.condition_number, 1.0)

    def test_two_field_MB_PD(self):
        """TWO_FIELD for MB: both eigvals positive, κ ~ 54."""
        r = check_gram_positive_definite(TangentKind.TWO_FIELD, xi=0)
        assert r.is_positive_definite
        assert r.eigenvalues.shape == (2,)
        assert r.min_eigenvalue > 0.1
        assert r.condition_number < 100

    def test_two_field_BE_PD(self):
        r = check_gram_positive_definite(TangentKind.TWO_FIELD, xi=+1)
        assert r.is_positive_definite

    def test_two_field_FD_PD(self):
        r = check_gram_positive_definite(TangentKind.TWO_FIELD, xi=-1)
        assert r.is_positive_definite

    def test_eigenvalues_sorted_ascending(self):
        r = check_gram_positive_definite(TangentKind.TWO_FIELD, xi=0)
        assert r.eigenvalues[0] <= r.eigenvalues[1]


# ═══════════════════════════════════════════════════════════════
# §4 — Layer 3: Moment admissibility
# ═══════════════════════════════════════════════════════════════

class TestMomentAdmissibility:
    def test_T0_negative_fails(self):
        T = np.array([-1.0, 0.0, 0.0])
        r = check_moment_admissible(T)
        assert not r.T_0_positive
        assert not r.is_admissible

    def test_isotropic_multipoles_admissible(self):
        T = np.array([6.0, 0.0, 0.0])
        r = check_moment_admissible(T)
        assert r.is_admissible
        assert r.max_abs_ratio == 0.0

    def test_moderate_ratios_admissible(self):
        T = np.array([6.0, 0.2, 0.1])
        r = check_moment_admissible(T)
        assert r.is_admissible
        assert math.isclose(r.max_abs_ratio, 0.2 / 6.0, rel_tol=1e-10)

    def test_large_T_1_ratio_fails(self):
        T = np.array([6.0, 8.0, 0.0])  # |T_1/T_0| = 1.33 > 1
        r = check_moment_admissible(T)
        assert not r.within_heuristic_bound
        assert not r.is_admissible

    def test_custom_heuristic_bound(self):
        T = np.array([6.0, 4.0, 0.0])  # ratio = 2/3
        r_tight = check_moment_admissible(T, heuristic_bound=0.5)
        r_loose = check_moment_admissible(T, heuristic_bound=1.0)
        assert not r_tight.is_admissible
        assert r_loose.is_admissible

    def test_only_T_0_returned(self):
        """Single-element T array (L_out=0)."""
        T = np.array([6.0])
        r = check_moment_admissible(T)
        assert r.is_admissible  # no ratios to check
        assert r.max_abs_ratio == 0.0


# ═══════════════════════════════════════════════════════════════
# §5 — Unified audit
# ═══════════════════════════════════════════════════════════════

class TestAssessRealizability:
    def test_isotropic_admissible(self):
        audit = assess_realizability(
            isotropic_theta(1.0), xi=0, kind=TangentKind.ONE_FIELD,
        )
        assert audit.verdict == AdmissibilityVerdict.ADMISSIBLE
        assert audit.is_admissible

    def test_small_dipole_admissible(self):
        audit = assess_realizability(
            dipole_theta(1.0, 0.05), xi=0, kind=TangentKind.ONE_FIELD,
        )
        assert audit.verdict == AdmissibilityVerdict.ADMISSIBLE

    def test_large_dipole_field_violation(self):
        audit = assess_realizability(
            dipole_theta(1.0, 1.2), xi=0, kind=TangentKind.ONE_FIELD,
        )
        assert audit.verdict == AdmissibilityVerdict.FIELD_VIOLATION
        assert not audit.is_admissible

    def test_negative_theta_field_violation(self):
        Theta = AxisymmetricField(coeffs=np.array([-1.0]))
        audit = assess_realizability(Theta, xi=0, kind=TangentKind.ONE_FIELD)
        # Depending on whether moment layer also reports (skipped when field fails)
        assert not audit.is_admissible
        assert audit.verdict in [AdmissibilityVerdict.FIELD_VIOLATION,
                                 AdmissibilityVerdict.MULTIPLE_VIOLATIONS]

    def test_BE_positive_eta_violation(self):
        eta = AxisymmetricField(coeffs=np.array([0.3]))
        audit = assess_realizability(
            isotropic_theta(1.0), xi=+1, eta=eta,
            kind=TangentKind.TWO_FIELD,
        )
        assert not audit.is_admissible

    def test_all_three_layers_returned(self):
        audit = assess_realizability(
            isotropic_theta(1.0), xi=0, kind=TangentKind.TWO_FIELD,
        )
        assert audit.field_result is not None
        assert audit.gram_result is not None
        assert audit.moment_result is not None

    def test_xi_preserved(self):
        audit = assess_realizability(
            isotropic_theta(1.0), xi=-1, kind=TangentKind.TWO_FIELD,
        )
        assert audit.xi == -1


# ═══════════════════════════════════════════════════════════════
# §6 — Known-limit recovery
# ═══════════════════════════════════════════════════════════════

class TestKnownLimits:
    def test_FLRW_admissible_MB(self):
        assert verify_flrw_limit_admissible(xi=0)

    def test_FLRW_admissible_BE(self):
        assert verify_flrw_limit_admissible(xi=+1)

    def test_FLRW_admissible_FD(self):
        assert verify_flrw_limit_admissible(xi=-1)

    def test_small_shear_admissible_MB(self):
        assert verify_small_shear_admissible(xi=0, Theta_1=0.05)

    def test_small_shear_admissible_BE(self):
        assert verify_small_shear_admissible(xi=+1, Theta_1=0.05)

    def test_small_shear_admissible_FD(self):
        assert verify_small_shear_admissible(xi=-1, Theta_1=0.05)

    def test_large_dipole_fails(self):
        assert verify_large_dipole_breaks_positivity()


# ═══════════════════════════════════════════════════════════════
# §7 — Boost preservation (Paper I Thm 3 natural consequence)
# ═══════════════════════════════════════════════════════════════

class TestBoostPreservation:
    """Admissibility should be preserved under small boosts (Thm 3)."""

    def test_isotropic_after_small_boost_still_admissible(self):
        """Boost of Θ = 1 by v = 0.01 produces Θ' ≈ 1 + 0.01 μ, still > 0."""
        from tsc.charts.boost_perturbative import boost_theta_axisymmetric
        Theta_boosted = boost_theta_axisymmetric(isotropic_theta(1.0), v=0.01)
        r = check_field_admissible(Theta_boosted, xi=0)
        assert r.is_admissible

    def test_isotropic_after_moderate_boost_still_admissible(self):
        """Even at v=0.1, isotropic Θ remains positive after boost."""
        from tsc.charts.boost_perturbative import boost_theta_axisymmetric
        Theta_boosted = boost_theta_axisymmetric(isotropic_theta(1.0), v=0.1)
        r = check_field_admissible(Theta_boosted, xi=0)
        # Θ'_min = 1/γ(1+v) at μ=1, Θ'_max = 1/γ(1-v) at μ=-1; both > 0 for |v| < 1
        assert r.is_admissible


# ═══════════════════════════════════════════════════════════════
# §8 — Result container properties
# ═══════════════════════════════════════════════════════════════

class TestResultContainers:
    def test_field_result_is_frozen(self):
        r = check_field_admissible(isotropic_theta(1.0), xi=0)
        with pytest.raises(Exception):
            r.theta_positive = False  # frozen

    def test_gram_result_is_frozen(self):
        r = check_gram_positive_definite(TangentKind.ONE_FIELD, xi=0)
        with pytest.raises(Exception):
            r.is_positive_definite = False

    def test_moment_result_is_frozen(self):
        r = check_moment_admissible(np.array([1.0, 0.1]))
        with pytest.raises(Exception):
            r.T_0 = 0.0

    def test_audit_is_frozen(self):
        audit = assess_realizability(
            isotropic_theta(1.0), xi=0, kind=TangentKind.ONE_FIELD,
        )
        with pytest.raises(Exception):
            audit.verdict = AdmissibilityVerdict.FIELD_VIOLATION
