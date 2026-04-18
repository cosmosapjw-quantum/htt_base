"""
Test suite: bass/closure/quadrupole_tca.py  (Week 6-04)
========================================================

Test classes:
  1. TestMatrixAssembly                  — template, Γ_T scaling, det
  2. TestMatrixConditioning              — condition number stable
  3. TestSolveTCAClosureAnalytic         — inverse formula literal
  4. TestSolveTCAClosureMatrixConsistency — matrix solve = analytic
  5. TestSubleadingS_ELimit              — E_2/Θ_2 = −√6/4, Π = (5/2)Θ_2
  6. TestCombinedSourcePi                — Π = Θ_2 − √6 E_2
  7. TestPolterCAMB                      — literal pig/10 + 9 E_2/15
  8. TestSecondOrderCorrection           — CRS factor (1 + c τ̈/τ̇²)
  9. TestTCAClosureConfig                — dataclass invariants
 10. TestSolveConfigurableBackwardCompat — leading order = base formula
 11. TestProductionModeCorrection        — 2nd-order toggle behaviour
 12. TestDiagnostics                     — subleading ratio, Π shortcut
 13. TestRuntimeGatingW3                 — public entries gate
"""
from __future__ import annotations

import math
import numpy as np
import pytest

from bass.closure.quadrupole_tca import (
    TCAClosureConfig,
    build_tca_matrix,
    combined_pi_of_theta_2_only,
    combined_source_pi,
    leading_order_config,
    polter_camb,
    second_order_correction_factor,
    solve_tca_closure,
    solve_tca_closure_configurable,
    subleading_E2_ratio,
    tca_closure_matrix_solve,
    tca_matrix_condition_number,
    tca_matrix_determinant,
)
from bass.runtime.canonical_decision import (
    CanonicalBlockError,
    CanonicalDecision,
    make_canonical_decision,
)
from tsc.diagnostics.tangency import compute_D_diagnostic, TangentKind


# ============================================================================
# Fixtures
# ============================================================================

def _on_manifold_G(x):
    return np.asarray(x, dtype=float)


def _allowing_decision() -> CanonicalDecision:
    tang = compute_D_diagnostic(
        G_field=_on_manifold_G, kind=TangentKind.ONE_FIELD, xi=0, eta=0.0,
    )
    return make_canonical_decision(
        beta_result=(True, {
            "beta": 1.36e-3, "beta_max": 8.62e-3, "slack": 7.26e-3,
            "eta_u_dot": 0.16, "safety_factor": 0.5, "epsilon_1": 0.02,
        }),
        sigma_result=(True, {
            "sigma_sq": 1e-5, "floor": 1e-6, "log_margin_decades": 1.0,
        }),
        tangency_result=tang,
    )


def _blocking_decision() -> CanonicalDecision:
    tang = compute_D_diagnostic(
        G_field=_on_manifold_G, kind=TangentKind.ONE_FIELD, xi=0, eta=0.0,
    )
    return make_canonical_decision(
        beta_result=(False, {
            "beta": 0.5, "beta_max": 8.62e-3, "slack": -0.491,
            "eta_u_dot": 0.16, "safety_factor": 0.5, "epsilon_1": 0.02,
        }),
        sigma_result=(True, {
            "sigma_sq": 1e-5, "floor": 1e-6, "log_margin_decades": 1.0,
        }),
        tangency_result=tang,
    )


SQRT6 = math.sqrt(6.0)


# ============================================================================
# 1. TestMatrixAssembly
# ============================================================================

class TestMatrixAssembly:

    def test_template_structure(self):
        M = build_tca_matrix(1.0)
        # Exact entries
        assert abs(M[0, 0] - 9.0 / 10.0) < 1e-15
        assert abs(M[0, 1] - SQRT6 / 10.0) < 1e-15
        assert abs(M[1, 0] - 3.0 / (5.0 * SQRT6)) < 1e-15
        assert abs(M[1, 1] - 2.0 / 5.0) < 1e-15

    def test_linear_in_gamma(self):
        g1 = 3.5
        g2 = 7.0
        M1 = build_tca_matrix(g1)
        M2 = build_tca_matrix(g2)
        np.testing.assert_allclose(M2, (g2 / g1) * M1, rtol=1e-14)

    def test_zero_gamma_gives_zero_matrix(self):
        M = build_tca_matrix(0.0)
        assert np.all(M == 0.0)

    def test_rejects_negative_gamma(self):
        with pytest.raises(ValueError, match="gamma_T must be non-negative"):
            build_tca_matrix(-0.1)

    def test_rejects_nan_gamma(self):
        with pytest.raises(ValueError, match="gamma_T must be finite"):
            build_tca_matrix(float("nan"))

    def test_determinant_analytic(self):
        # det should equal Γ_T² × 3/10
        for gamma in [0.0, 1.0, 2.5, 100.0]:
            expected = gamma * gamma * (3.0 / 10.0)
            assert abs(tca_matrix_determinant(gamma) - expected) < 1e-14

    def test_determinant_matches_numpy(self):
        # Cross-check against numpy for nontrivial gamma
        for gamma in [1.0, 2.5, 1e3]:
            M = build_tca_matrix(gamma)
            np_det = float(np.linalg.det(M))
            analytic_det = tca_matrix_determinant(gamma)
            assert abs(np_det - analytic_det) < 1e-10 * abs(analytic_det)


# ============================================================================
# 2. TestMatrixConditioning
# ============================================================================

class TestMatrixConditioning:

    def test_condition_number_reasonable(self):
        # Should be a small number (well-conditioned)
        kappa = tca_matrix_condition_number()
        assert 1.0 < kappa < 10.0

    def test_condition_number_gamma_independent(self):
        # Template is gamma-independent, so cond is a pure number
        kappa = tca_matrix_condition_number()
        # Check that multiplying by Γ_T doesn't change conditioning
        for gamma in [0.1, 1.0, 1e6]:
            M = build_tca_matrix(gamma)
            kappa_scaled = float(np.linalg.cond(M))
            assert abs(kappa_scaled - kappa) < 1e-10


# ============================================================================
# 3. TestSolveTCAClosureAnalytic
# ============================================================================

class TestSolveTCAClosureAnalytic:

    def test_formula_S_T_only(self):
        # With S_E = 0 (physical convention, Γ_T M X = +S):
        #   Θ_2 = +(4/3) S_T / Γ_T
        #   E_2 = −(√6/3) S_T / Γ_T
        # S_T > 0 gives Θ_2 > 0 (shear drives positive anisotropic stress),
        # matching CAMB's π_γ ≈ (32/45) κ̇⁻¹ σ sign convention.
        S_T = 1e-3
        gamma = 1e3
        theta, E = solve_tca_closure(
            S_T, 0.0, gamma, _allowing_decision(),
        )
        assert abs(theta - (+4.0 / 3.0 * S_T / gamma)) < 1e-14
        assert abs(E - (-SQRT6 / 3.0 * S_T / gamma)) < 1e-14
        # Physical sign check: shear source creates positive quadrupole
        assert theta > 0
        assert E < 0

    def test_formula_S_E_only(self):
        # With S_T = 0 (physical convention, Γ_T M X = +S):
        #   Θ_2 = −(√6/3) S_E / Γ_T
        #   E_2 = +3 S_E / Γ_T
        S_E = 1e-3
        gamma = 1e3
        theta, E = solve_tca_closure(
            0.0, S_E, gamma, _allowing_decision(),
        )
        assert abs(theta - (-SQRT6 / 3.0 * S_E / gamma)) < 1e-14
        assert abs(E - (+3.0 * S_E / gamma)) < 1e-14
        # Physical sign check: positive S_E drives E_2 positive
        assert E > 0
        assert theta < 0

    def test_linearity_in_sources(self):
        # Θ_2, E_2 are linear in (S_T, S_E). Verify superposition.
        gamma = 1.0e3
        theta1, E1 = solve_tca_closure(
            1e-3, 2e-3, gamma, _allowing_decision(),
        )
        theta2, E2 = solve_tca_closure(
            3e-3, 4e-3, gamma, _allowing_decision(),
        )
        theta_sum, E_sum = solve_tca_closure(
            1e-3 + 3e-3, 2e-3 + 4e-3, gamma, _allowing_decision(),
        )
        assert abs(theta_sum - (theta1 + theta2)) < 1e-14
        assert abs(E_sum - (E1 + E2)) < 1e-14

    def test_scales_inversely_with_gamma(self):
        # Double Γ_T → Θ_2, E_2 halve.
        theta_1, E_1 = solve_tca_closure(
            1e-3, 2e-3, 1.0e3, _allowing_decision(),
        )
        theta_2, E_2 = solve_tca_closure(
            1e-3, 2e-3, 2.0e3, _allowing_decision(),
        )
        assert abs(theta_2 - 0.5 * theta_1) < 1e-14
        assert abs(E_2 - 0.5 * E_1) < 1e-14

    def test_rejects_zero_gamma(self):
        with pytest.raises(ValueError, match="strictly positive"):
            solve_tca_closure(
                1e-3, 2e-3, 0.0, _allowing_decision(),
            )

    def test_rejects_nonfinite_sources(self):
        with pytest.raises(ValueError, match="S_T must be finite"):
            solve_tca_closure(
                float("nan"), 0.0, 1e3, _allowing_decision(),
            )
        with pytest.raises(ValueError, match="S_E must be finite"):
            solve_tca_closure(
                0.0, float("inf"), 1e3, _allowing_decision(),
            )


# ============================================================================
# 4. TestSolveTCAClosureMatrixConsistency
# ============================================================================

class TestSolveTCAClosureMatrixConsistency:
    """Analytic inverse must match numerical linsolve."""

    def test_agreement_across_source_range(self):
        test_cases = [
            (1e-3, 2e-3, 1e3),
            (5e-2, -3e-2, 1e2),
            (-1e-4, 7e-4, 1e5),
            (1e-10, 1e-10, 1.0),
        ]
        for S_T, S_E, gamma in test_cases:
            t_a, E_a = solve_tca_closure(
                S_T, S_E, gamma, _allowing_decision(),
            )
            t_m, E_m = tca_closure_matrix_solve(
                S_T, S_E, gamma, _allowing_decision(),
            )
            rel_err_theta = abs(t_a - t_m) / max(abs(t_a), 1e-30)
            rel_err_E = abs(E_a - E_m) / max(abs(E_a), 1e-30)
            assert rel_err_theta < 1e-12
            assert rel_err_E < 1e-12


# ============================================================================
# 5. TestSubleadingS_ELimit
# ============================================================================

class TestSubleadingS_ELimit:

    def test_ratio_sqrt6_over_4(self):
        # When S_E = 0, E_2/Θ_2 = −√6/4.
        S_T = 1e-3
        gamma = 1.0e3
        theta, E = solve_tca_closure(
            S_T, 0.0, gamma, _allowing_decision(),
        )
        assert abs(E / theta - (-SQRT6 / 4.0)) < 1e-14

    def test_pi_equals_5_over_2_theta(self):
        # With E_2 = −√6/4 Θ_2, Π = Θ_2 − √6 E_2 = (5/2) Θ_2.
        S_T = 1e-3
        gamma = 1.0e3
        theta, E = solve_tca_closure(
            S_T, 0.0, gamma, _allowing_decision(),
        )
        pi = combined_source_pi(theta, E)
        assert abs(pi - 2.5 * theta) < 1e-14

    def test_pi_shortcut_matches_full_formula(self):
        theta = 1.5e-4
        shortcut = combined_pi_of_theta_2_only(theta)
        full = combined_source_pi(theta, -SQRT6 / 4.0 * theta)
        assert abs(shortcut - full) < 1e-18


# ============================================================================
# 6. TestCombinedSourcePi
# ============================================================================

class TestCombinedSourcePi:

    def test_formula(self):
        theta = 2e-4
        E = 1e-4
        pi = combined_source_pi(theta, E)
        assert abs(pi - (theta - SQRT6 * E)) < 1e-18

    def test_zero_for_both_zero(self):
        assert combined_source_pi(0.0, 0.0) == 0.0

    def test_linear_in_inputs(self):
        p1 = combined_source_pi(1e-3, 2e-3)
        p2 = combined_source_pi(2e-3, 4e-3)
        assert abs(p2 - 2.0 * p1) < 1e-18

    def test_rejects_nonfinite(self):
        with pytest.raises(ValueError, match="theta_2 and E_2 must be finite"):
            combined_source_pi(float("nan"), 0.0)


# ============================================================================
# 7. TestPolterCAMB
# ============================================================================

class TestPolterCAMB:

    def test_formula(self):
        pig = 3e-4
        E = 5e-5
        p = polter_camb(pig, E)
        expected = pig / 10.0 + 9.0 * E / 15.0
        assert abs(p - expected) < 1e-18

    def test_zero_for_both_zero(self):
        assert polter_camb(0.0, 0.0) == 0.0

    def test_linearity(self):
        p1 = polter_camb(1e-3, 2e-3)
        p2 = polter_camb(2e-3, 4e-3)
        assert abs(p2 - 2.0 * p1) < 1e-18

    def test_differs_from_pstf_pi(self):
        # polter and Π are NOT the same (different normalizations).
        # This is a guard against accidentally conflating them.
        theta_2 = 1e-3
        E_2 = -SQRT6 / 4.0 * theta_2
        pi = combined_source_pi(theta_2, E_2)
        p = polter_camb(theta_2, E_2)  # treat pig = Θ_2 nominally
        assert abs(pi - p) > 1e-6 * abs(pi)  # verify they are different

    def test_rejects_nonfinite(self):
        with pytest.raises(ValueError, match="pig and E_2 must be finite"):
            polter_camb(float("nan"), 0.0)


# ============================================================================
# 8. TestSecondOrderCorrection
# ============================================================================

class TestSecondOrderCorrection:

    def test_zero_tau_ddot_gives_unity(self):
        f = second_order_correction_factor(1e3, 0.0)
        assert f == 1.0

    def test_formula_literal(self):
        tau_dot = 1e3
        tau_ddot = 1e5
        f = second_order_correction_factor(tau_dot, tau_ddot)
        expected = 1.0 + (11.0 / 6.0) * tau_ddot / (tau_dot * tau_dot)
        assert abs(f - expected) < 1e-14

    def test_positive_tau_ddot_increases_factor(self):
        # τ̈ > 0 ⇒ factor > 1 (increasing opacity strengthens correction)
        f = second_order_correction_factor(1e3, 1e5)
        assert f > 1.0

    def test_negative_tau_ddot_decreases_factor(self):
        # τ̈ < 0 ⇒ factor < 1
        f = second_order_correction_factor(1e3, -1e5)
        assert f < 1.0

    def test_custom_coefficient(self):
        # Override CRS default to test parameterization.
        f_default = second_order_correction_factor(1e3, 1e4)
        f_custom = second_order_correction_factor(
            1e3, 1e4, coefficient=2.0,
        )
        assert f_custom != f_default

    def test_rejects_zero_tau_dot(self):
        with pytest.raises(ValueError, match="strictly positive"):
            second_order_correction_factor(0.0, 1e4)

    def test_rejects_nonfinite(self):
        with pytest.raises(ValueError):
            second_order_correction_factor(float("nan"), 1e4)
        with pytest.raises(ValueError):
            second_order_correction_factor(1e3, float("inf"))


# ============================================================================
# 9. TestTCAClosureConfig
# ============================================================================

class TestTCAClosureConfig:

    def test_default_is_production(self):
        c = TCAClosureConfig()
        assert c.use_second_order is True

    def test_leading_order_config(self):
        c = leading_order_config()
        assert c.use_second_order is False
        assert c.tau_ddot == 0.0

    def test_frozen(self):
        c = TCAClosureConfig()
        with pytest.raises(Exception):
            c.use_second_order = False

    def test_rejects_nonfinite_tau_ddot_when_second_order(self):
        with pytest.raises(ValueError, match="tau_ddot must be finite"):
            TCAClosureConfig(
                use_second_order=True, tau_ddot=float("nan"),
            )

    def test_allows_nonfinite_tau_ddot_when_leading(self):
        # When 2nd order disabled, tau_ddot is unused, but we still
        # require it be finite per construction contract. This test
        # checks current behaviour — validator path.
        c = TCAClosureConfig(
            use_second_order=False, tau_ddot=0.0,
        )
        assert c.use_second_order is False


# ============================================================================
# 10. TestSolveConfigurableBackwardCompat
# ============================================================================

class TestSolveConfigurableBackwardCompat:
    """Leading-order configurable must match the base formula bit-exact."""

    def test_leading_order_matches_base(self):
        S_T, S_E, gamma = 1e-3, 2e-3, 1.0e3
        t_base, E_base = solve_tca_closure(
            S_T, S_E, gamma, _allowing_decision(),
        )
        t_cfg, E_cfg = solve_tca_closure_configurable(
            S_T, S_E, gamma, leading_order_config(), _allowing_decision(),
        )
        assert t_base == t_cfg
        assert E_base == E_cfg


# ============================================================================
# 11. TestProductionModeCorrection
# ============================================================================

class TestProductionModeCorrection:

    def test_zero_tau_ddot_leading_order_match(self):
        # 2nd order on but τ̈ = 0 → factor = 1 → same as leading order
        S_T, S_E, gamma = 1e-3, 2e-3, 1.0e3
        config_prod = TCAClosureConfig(
            use_second_order=True, tau_ddot=0.0,
        )
        t_lead, E_lead = solve_tca_closure_configurable(
            S_T, S_E, gamma, leading_order_config(), _allowing_decision(),
        )
        t_prod, E_prod = solve_tca_closure_configurable(
            S_T, S_E, gamma, config_prod, _allowing_decision(),
        )
        assert t_prod == t_lead
        assert E_prod == E_lead

    def test_positive_tau_ddot_enhances_source(self):
        S_T, S_E, gamma = 1e-3, 0.0, 1.0e3
        config_prod = TCAClosureConfig(
            use_second_order=True, tau_ddot=1e5,
        )
        t_lead, E_lead = solve_tca_closure_configurable(
            S_T, S_E, gamma, leading_order_config(), _allowing_decision(),
        )
        t_prod, E_prod = solve_tca_closure_configurable(
            S_T, S_E, gamma, config_prod, _allowing_decision(),
        )
        # τ̈ > 0 ⇒ factor > 1. Θ_2 is positive (from leading with S_T>0),
        # and scales proportionally. |Θ_2| should grow.
        assert abs(t_prod) > abs(t_lead)
        # Ratio should match the 2nd-order factor
        factor = 1.0 + (11.0 / 6.0) * 1e5 / (1e3 * 1e3)
        assert abs(t_prod / t_lead - factor) < 1e-12

    def test_E2_Theta2_ratio_preserved_in_subleading(self):
        # With S_E = 0 and 2nd-order on, ratio E_2/Θ_2 = −√6/4 preserved
        S_T, gamma = 1e-3, 1.0e3
        config_prod = TCAClosureConfig(
            use_second_order=True, tau_ddot=5e4,
        )
        theta, E = solve_tca_closure_configurable(
            S_T, 0.0, gamma, config_prod, _allowing_decision(),
        )
        ratio = E / theta
        assert abs(ratio - (-SQRT6 / 4.0)) < 1e-12


# ============================================================================
# 12. TestDiagnostics
# ============================================================================

class TestDiagnostics:

    def test_subleading_ratio_zero_in_S_E_zero_case(self):
        # Θ_2 = −4/3 × S_T / Γ_T, E_2 = +√6/3 × S_T / Γ_T
        # ratio = (√6/3) / (−4/3) = −√6/4  →  deviation = 0
        S_T = 1e-3
        theta, E = solve_tca_closure(
            S_T, 0.0, 1.0e3, _allowing_decision(),
        )
        dev = subleading_E2_ratio(theta, E)
        assert abs(dev) < 1e-14

    def test_subleading_ratio_nonzero_for_nontrivial_S_E(self):
        # With both S_T and S_E non-zero, deviation should be non-zero
        theta, E = solve_tca_closure(
            1e-3, 5e-4, 1.0e3, _allowing_decision(),
        )
        dev = subleading_E2_ratio(theta, E)
        assert abs(dev) > 1e-6

    def test_nan_when_theta_2_zero(self):
        dev = subleading_E2_ratio(0.0, 1e-3)
        assert math.isnan(dev)

    def test_combined_pi_shortcut_matches_full(self):
        theta = 1.5e-4
        short = combined_pi_of_theta_2_only(theta)
        full = combined_source_pi(theta, -SQRT6 / 4.0 * theta)
        assert abs(short - full) < 1e-18


# ============================================================================
# 13. TestRuntimeGatingW3
# ============================================================================

class TestRuntimeGatingW3:

    def test_solve_tca_closure_gates(self):
        with pytest.raises(CanonicalBlockError):
            solve_tca_closure(
                1e-3, 2e-3, 1e3, _blocking_decision(),
            )

    def test_matrix_solve_gates(self):
        with pytest.raises(CanonicalBlockError):
            tca_closure_matrix_solve(
                1e-3, 2e-3, 1e3, _blocking_decision(),
            )

    def test_configurable_gates(self):
        with pytest.raises(CanonicalBlockError):
            solve_tca_closure_configurable(
                1e-3, 2e-3, 1e3,
                leading_order_config(), _blocking_decision(),
            )

    def test_utilities_have_no_gate(self):
        # Pure utilities should not require a decision parameter.
        import inspect
        for fn in [
            build_tca_matrix,
            tca_matrix_determinant,
            tca_matrix_condition_number,
            combined_source_pi,
            combined_pi_of_theta_2_only,
            polter_camb,
            second_order_correction_factor,
            subleading_E2_ratio,
        ]:
            sig = inspect.signature(fn)
            assert "decision" not in sig.parameters, (
                f"{fn.__name__} should not have a decision parameter"
            )
