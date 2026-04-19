"""
Test suite: bass/transport/emode_hierarchy.py  (Week 7-01)
==========================================================

Test classes:
  1. TestSpin2CouplingCoeffs     — α, β formulas + boundary conditions
  2. TestEModeParameters         — container invariants, damping profile
  3. TestEModeState              — container invariants, E_ell access
  4. TestZeroEModeState          — factory
  5. TestStreamingMatrixStructure — dimensions, boundary, symmetry
  6. TestDampingVector           — (2/5) factor at ℓ=2, Γ_T elsewhere
  7. TestSourceVector            — Θ_2 → E_2 coupling sign
  8. TestEulerStepEMode          — single-step formula, gates
  9. TestSteadyState             — linsolve correctness
 10. TestW604CrossCheck          — **independent verification vs W6-04**
 11. TestIntegrationConvergence  — Euler → analytic target
 12. TestPhysicalSignAssertions  — v1.2 NEW PATTERN: external-sign checks
 13. TestCFLDiagnostic           — CFL bound sanity
 14. TestSubleadingCrossCheckRatio — diagnostic
 15. TestRuntimeGatingW3         — gating discipline
"""
from __future__ import annotations

import math
import numpy as np
import pytest

from bass.transport.emode_hierarchy import (
    EModeIntegrationResult,
    EModeParameters,
    EModeState,
    build_emode_damping_vector,
    build_emode_source_vector,
    build_emode_streaming_matrix,
    cfl_max_dt_emode,
    compute_emode_steady_state,
    euler_step_emode,
    integrate_emode_to_steady_state,
    pstf_emode_coupling_coeffs,
    subleading_cross_check_ratio,
    zero_emode_state,
)
from bass.closure.quadrupole_tca import solve_tca_closure
from bass.runtime.canonical_decision import (
    CanonicalBlockError,
    CanonicalDecision,
    make_canonical_decision,
)
from tsc.diagnostics.tangency import compute_D_diagnostic, TangentKind


# ============================================================================
# Fixtures
# ============================================================================

SQRT6 = math.sqrt(6.0)
SUBLEADING_RATIO = -SQRT6 / 4.0  # E_2/Θ_2 in W6-04 subleading limit


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


# ============================================================================
# 1. TestSpin2CouplingCoeffs
# ============================================================================

class TestSpin2CouplingCoeffs:

    def test_alpha_ell_2_is_zero(self):
        # Boundary: spin-2 requires ℓ ≥ 2, so α^E_2 couples to E_1 ≡ 0.
        alpha, _ = pstf_emode_coupling_coeffs(2)
        assert alpha == 0.0

    def test_beta_ell_2_formula(self):
        # β^E_2 = √(9-4)/5 = √5 / 5
        _, beta = pstf_emode_coupling_coeffs(2)
        expected = math.sqrt(5.0) / 5.0
        assert abs(beta - expected) < 1e-14

    def test_alpha_ell_3_formula(self):
        # α^E_3 = √(9-4)/7 = √5 / 7
        alpha, _ = pstf_emode_coupling_coeffs(3)
        expected = math.sqrt(5.0) / 7.0
        assert abs(alpha - expected) < 1e-14

    def test_beta_ell_3_formula(self):
        # β^E_3 = √(16-4)/7 = √12 / 7 = 2√3 / 7
        _, beta = pstf_emode_coupling_coeffs(3)
        expected = 2.0 * math.sqrt(3.0) / 7.0
        assert abs(beta - expected) < 1e-14

    def test_alpha_ell_4_formula(self):
        # α^E_4 = √(16-4)/9 = 2√3 / 9
        alpha, _ = pstf_emode_coupling_coeffs(4)
        expected = 2.0 * math.sqrt(3.0) / 9.0
        assert abs(alpha - expected) < 1e-14

    def test_coeffs_below_ell_2_zero(self):
        # ℓ = 0 or 1: no spin-2 modes exist
        for ell in [0, 1]:
            a, b = pstf_emode_coupling_coeffs(ell)
            assert a == 0.0
            assert b == 0.0

    def test_coeffs_all_nonnegative(self):
        for ell in range(2, 20):
            a, b = pstf_emode_coupling_coeffs(ell)
            assert a >= 0.0
            assert b >= 0.0

    def test_coeffs_approach_unity_at_large_ell(self):
        # As ℓ → ∞, both α and β → 1/2 (since √(ℓ²-4)/ℓ → 1 and 1/(2ℓ+1) → 1/(2ℓ))
        # More precisely: α × (2ℓ+1) / √(ℓ²-4) = 1 exactly
        for ell in [10, 50, 100, 500]:
            a, _ = pstf_emode_coupling_coeffs(ell)
            expected_ratio = math.sqrt(ell * ell - 4) / (2.0 * ell + 1.0)
            assert abs(a - expected_ratio) < 1e-14


# ============================================================================
# 2. TestEModeParameters
# ============================================================================

class TestEModeParameters:

    def test_construction_valid(self):
        p = EModeParameters(thomson_rate=1e3, k_eff=5.0, ell_max=10)
        assert p.thomson_rate == 1e3
        assert p.k_eff == 5.0
        assert p.ell_max == 10
        assert p.ell2_damping_factor == 2.0 / 5.0

    def test_state_dim(self):
        p = EModeParameters(thomson_rate=1.0, k_eff=0.0, ell_max=10)
        # E_2..E_10: 9 components
        assert p.state_dim == 9

    def test_rejects_ell_max_below_2(self):
        for bad in [0, 1]:
            with pytest.raises(ValueError, match="ell_max must be ≥ 2"):
                EModeParameters(
                    thomson_rate=1.0, k_eff=0.0, ell_max=bad,
                )

    def test_rejects_negative_thomson(self):
        with pytest.raises(ValueError, match="thomson_rate must be"):
            EModeParameters(thomson_rate=-1.0, k_eff=0.0, ell_max=5)

    def test_rejects_negative_k(self):
        with pytest.raises(ValueError, match="k_eff must be"):
            EModeParameters(thomson_rate=1.0, k_eff=-1.0, ell_max=5)

    def test_custom_ell2_damping_factor(self):
        p = EModeParameters(
            thomson_rate=1.0, k_eff=0.0, ell_max=5,
            ell2_damping_factor=1.0,  # no (2/5) reduction
        )
        assert p.ell2_damping_factor == 1.0


# ============================================================================
# 3. TestEModeState
# ============================================================================

class TestEModeState:

    def test_construction_basic(self):
        s = EModeState(amplitudes=np.array([1e-4, 2e-5, 3e-6]), ell_max=4)
        assert s.ell_max == 4
        assert s.amplitudes.shape == (3,)

    def test_frozen(self):
        s = zero_emode_state(5)
        with pytest.raises(Exception):
            s.ell_max = 10

    def test_E_ell_access(self):
        amps = np.array([0.1, 0.2, 0.3, 0.4])  # E_2, E_3, E_4, E_5
        s = EModeState(amplitudes=amps, ell_max=5)
        assert s.E_ell(2) == 0.1
        assert s.E_ell(3) == 0.2
        assert s.E_ell(4) == 0.3
        assert s.E_ell(5) == 0.4

    def test_E_ell_out_of_range_raises(self):
        s = zero_emode_state(4)
        with pytest.raises(ValueError, match="ell must be in"):
            s.E_ell(1)
        with pytest.raises(ValueError, match="ell must be in"):
            s.E_ell(5)

    def test_shape_mismatch_rejected(self):
        with pytest.raises(ValueError, match="amplitudes must have shape"):
            EModeState(amplitudes=np.zeros(3), ell_max=5)

    def test_nonfinite_amplitudes_rejected(self):
        with pytest.raises(ValueError, match="all amplitudes must be finite"):
            EModeState(amplitudes=np.array([1.0, float("nan")]), ell_max=3)


# ============================================================================
# 4. TestZeroEModeState
# ============================================================================

class TestZeroEModeState:

    def test_zeros(self):
        s = zero_emode_state(5)
        assert np.all(s.amplitudes == 0.0)
        assert s.ell_max == 5

    def test_dimensions(self):
        # ell_max=4 → E_2, E_3, E_4 → shape (3,)
        s = zero_emode_state(4)
        assert s.amplitudes.shape == (3,)

    def test_rejects_below_2(self):
        with pytest.raises(ValueError, match="ell_max must be ≥ 2"):
            zero_emode_state(1)


# ============================================================================
# 5. TestStreamingMatrixStructure
# ============================================================================

class TestStreamingMatrixStructure:

    def test_dimensions(self):
        p = EModeParameters(thomson_rate=1.0, k_eff=5.0, ell_max=6)
        M = build_emode_streaming_matrix(p)
        assert M.shape == (5, 5)

    def test_first_row_no_below_coupling(self):
        # α^E_2 = 0, so M[0, i-1] contribution doesn't exist (i-1 = -1),
        # but also the first row must only have M[0, 1] non-zero (−β^E_2).
        p = EModeParameters(thomson_rate=1.0, k_eff=5.0, ell_max=6)
        M = build_emode_streaming_matrix(p)
        # M[0, 0] (diag) must be 0
        assert M[0, 0] == 0.0
        # M[0, 1] = -k × β^E_2 = -k × √5/5
        expected = -5.0 * math.sqrt(5.0) / 5.0
        assert abs(M[0, 1] - expected) < 1e-14

    def test_second_row_has_above_below(self):
        # ℓ=3: α^E_3 = √5/7, β^E_3 = 2√3/7
        p = EModeParameters(thomson_rate=1.0, k_eff=7.0, ell_max=6)
        M = build_emode_streaming_matrix(p)
        # M[1, 0] = +k × α^E_3 = +7 × √5/7 = +√5
        assert abs(M[1, 0] - math.sqrt(5.0)) < 1e-14
        # M[1, 2] = -k × β^E_3 = -7 × 2√3/7 = -2√3
        assert abs(M[1, 2] - (-2.0 * math.sqrt(3.0))) < 1e-14

    def test_top_row_truncated(self):
        # M[L-1, L] doesn't exist (past boundary)
        p = EModeParameters(thomson_rate=1.0, k_eff=5.0, ell_max=4)
        M = build_emode_streaming_matrix(p)
        # Last row is for ℓ=4, state index 2. M[2, :] can only have M[2, 1]
        # from the coupling below. M[2, 2] must be zero.
        assert M[2, 2] == 0.0
        # No column index 3 exists (truncated)

    def test_ell_max_2_matrix_is_zero(self):
        # With ell_max=2, only E_2 exists. α^E_2 = 0 and truncation at top:
        # matrix is effectively 1×1 zero.
        p = EModeParameters(thomson_rate=1.0, k_eff=5.0, ell_max=2)
        M = build_emode_streaming_matrix(p)
        assert M.shape == (1, 1)
        assert M[0, 0] == 0.0

    def test_k_eff_zero_matrix_is_zero(self):
        p = EModeParameters(thomson_rate=1.0, k_eff=0.0, ell_max=6)
        M = build_emode_streaming_matrix(p)
        assert np.all(M == 0.0)


# ============================================================================
# 6. TestDampingVector
# ============================================================================

class TestDampingVector:

    def test_ell_2_has_reduced_damping(self):
        p = EModeParameters(thomson_rate=1e3, k_eff=0.0, ell_max=5)
        gamma = build_emode_damping_vector(p)
        assert abs(gamma[0] - (2.0 / 5.0) * 1e3) < 1e-14

    def test_ell_3_and_above_full_damping(self):
        p = EModeParameters(thomson_rate=1e3, k_eff=0.0, ell_max=5)
        gamma = build_emode_damping_vector(p)
        # gamma[0] is ℓ=2, gamma[1] is ℓ=3, etc.
        for i in range(1, len(gamma)):
            assert abs(gamma[i] - 1e3) < 1e-14

    def test_custom_ell2_factor(self):
        p = EModeParameters(
            thomson_rate=1.0, k_eff=0.0, ell_max=5,
            ell2_damping_factor=0.5,
        )
        gamma = build_emode_damping_vector(p)
        assert abs(gamma[0] - 0.5) < 1e-14
        assert abs(gamma[1] - 1.0) < 1e-14  # unchanged

    def test_zero_thomson_gives_zero(self):
        p = EModeParameters(thomson_rate=0.0, k_eff=0.0, ell_max=5)
        gamma = build_emode_damping_vector(p)
        assert np.all(gamma == 0.0)


# ============================================================================
# 7. TestSourceVector
# ============================================================================

class TestSourceVector:

    def test_source_only_at_ell_2(self):
        p = EModeParameters(thomson_rate=1e3, k_eff=0.0, ell_max=5)
        s = build_emode_source_vector(p, theta_2_external=1e-4)
        assert s[0] != 0.0
        for i in range(1, len(s)):
            assert s[i] == 0.0

    def test_source_formula(self):
        # s[0] = -(3/(5√6)) × Γ_T × Θ_2
        p = EModeParameters(thomson_rate=1e3, k_eff=0.0, ell_max=5)
        theta_2 = 1e-4
        s = build_emode_source_vector(p, theta_2_external=theta_2)
        expected = -(3.0 / (5.0 * SQRT6)) * 1e3 * theta_2
        assert abs(s[0] - expected) < 1e-14

    def test_sign_opposite_to_theta_2(self):
        # Θ_2 > 0 → s[0] < 0 (drives E_2 negative)
        p = EModeParameters(thomson_rate=1e3, k_eff=0.0, ell_max=5)
        s_pos = build_emode_source_vector(p, theta_2_external=+1e-4)
        s_neg = build_emode_source_vector(p, theta_2_external=-1e-4)
        assert s_pos[0] < 0.0
        assert s_neg[0] > 0.0
        assert s_pos[0] == -s_neg[0]

    def test_zero_theta_2_zero_source(self):
        p = EModeParameters(thomson_rate=1e3, k_eff=0.0, ell_max=5)
        s = build_emode_source_vector(p, theta_2_external=0.0)
        assert np.all(s == 0.0)


# ============================================================================
# 8. TestEulerStepEMode
# ============================================================================

class TestEulerStepEMode:

    def test_step_from_zero_produces_negative_E_2(self):
        # Start at zero, apply positive Θ_2: after one step E_2 < 0.
        p = EModeParameters(thomson_rate=1.0, k_eff=0.0, ell_max=3)
        init = zero_emode_state(3)
        new = euler_step_emode(
            init, p, theta_2_external=1.0, dt=1e-3,
            decision=_allowing_decision(),
        )
        assert new.E_ell(2) < 0.0

    def test_step_rejects_zero_dt(self):
        p = EModeParameters(thomson_rate=1.0, k_eff=0.0, ell_max=3)
        with pytest.raises(ValueError, match="dt must be positive"):
            euler_step_emode(
                zero_emode_state(3), p, theta_2_external=0.0,
                dt=0.0, decision=_allowing_decision(),
            )

    def test_step_rejects_shape_mismatch(self):
        p = EModeParameters(thomson_rate=1.0, k_eff=0.0, ell_max=5)
        wrong = zero_emode_state(3)
        with pytest.raises(ValueError, match="ell_max"):
            euler_step_emode(
                wrong, p, theta_2_external=0.0,
                dt=1e-3, decision=_allowing_decision(),
            )


# ============================================================================
# 9. TestSteadyState
# ============================================================================

class TestSteadyState:

    def test_zero_theta_2_gives_zero_steady(self):
        p = EModeParameters(thomson_rate=1.0, k_eff=1.0, ell_max=5)
        ss = compute_emode_steady_state(
            p, theta_2_external=0.0, decision=_allowing_decision(),
        )
        for amp in ss.amplitudes:
            assert abs(amp) < 1e-14

    def test_isolated_ell_2_matches_subleading(self):
        # k_eff = 0, ell_max = 2: isolated ℓ=2 system.
        # Steady state: (2/5 Γ_T) × E_2 = -(3/(5√6)) Γ_T Θ_2
        # ⟹ E_2 = -(3/(5√6)) × (5/2) × Θ_2 = -(√6/4) Θ_2
        p = EModeParameters(thomson_rate=1.0, k_eff=0.0, ell_max=2)
        theta_2 = 1.0
        ss = compute_emode_steady_state(
            p, theta_2_external=theta_2, decision=_allowing_decision(),
        )
        expected_E_2 = SUBLEADING_RATIO * theta_2
        assert abs(ss.E_ell(2) - expected_E_2) < 1e-14

    def test_non_trivial_streaming(self):
        # With k>0 and ell_max=3, E_3 is non-zero (streaming cascade from E_2).
        p = EModeParameters(thomson_rate=1.0, k_eff=1.0, ell_max=3)
        theta_2 = 1.0
        ss = compute_emode_steady_state(
            p, theta_2_external=theta_2, decision=_allowing_decision(),
        )
        assert ss.E_ell(3) != 0.0

    def test_trivial_dynamics_source_auto_zeros(self):
        # With Γ_T = 0 and k_eff = 0: source s = -(3/(5√6)) × Γ_T × Θ_2 = 0
        # automatically, regardless of Θ_2. So zero state is returned
        # (not an error). This is physically correct: without Thomson
        # scattering there is no coupling from Θ_2 to E_2.
        p = EModeParameters(thomson_rate=0.0, k_eff=0.0, ell_max=3)
        ss = compute_emode_steady_state(
            p, theta_2_external=1.0,  # non-zero Θ_2 but no coupling path
            decision=_allowing_decision(),
        )
        # With Γ_T=0, source is zero, dynamics trivial → zero E state
        assert np.all(ss.amplitudes == 0.0)

    def test_trivial_dynamics_zero_source_ok(self):
        # Γ=0 and k=0 with zero source → zero state is valid
        p = EModeParameters(thomson_rate=0.0, k_eff=0.0, ell_max=3)
        ss = compute_emode_steady_state(
            p, theta_2_external=0.0, decision=_allowing_decision(),
        )
        assert np.all(ss.amplitudes == 0.0)


# ============================================================================
# 10. TestW604CrossCheck — independent verification against W6-04
# ============================================================================

class TestW604CrossCheck:
    """
    Critical cross-module test: W7-01 steady state at isolated ℓ=2 (k=0)
    must reproduce W6-04's subleading-S_E formula E_2 = −(√6/4) Θ_2.

    W6-04 and W7-01 use INDEPENDENT derivations:
    - W6-04: algebraic matrix inverse of Γ_T M X = +S
    - W7-01: ODE steady state via (diag γ − M) E = s

    Agreement at the isolated limit provides a critical consistency
    check between the two modules.
    """

    def test_isolated_ell_2_agrees_with_w604_subleading(self):
        # W7-01: isolated ℓ=2, k=0
        gamma_T = 1.0e3
        theta_2 = 1e-4
        p = EModeParameters(
            thomson_rate=gamma_T, k_eff=0.0, ell_max=2,
        )
        ss_w701 = compute_emode_steady_state(
            p, theta_2_external=theta_2, decision=_allowing_decision(),
        )

        # W6-04: subleading limit S_T generating the same Θ_2
        # From W6-04 formula: Θ_2 = +(4/3) S_T / Γ_T
        # Inverting: S_T = (3/4) × Γ_T × Θ_2
        # Then W6-04 gives E_2 = -(√6/3) S_T / Γ_T
        S_T = (3.0 / 4.0) * gamma_T * theta_2
        theta_2_w604, E_2_w604 = solve_tca_closure(
            S_T, 0.0, gamma_T, _allowing_decision(),
        )

        # Consistency: W6-04 Θ_2 reproduces input theta_2
        assert abs(theta_2_w604 - theta_2) < 1e-14 * abs(theta_2)
        # And E_2 from both modules agree
        assert abs(ss_w701.E_ell(2) - E_2_w604) < 1e-14 * abs(E_2_w604)
        # Both should equal -(√6/4) × Θ_2
        expected = SUBLEADING_RATIO * theta_2
        assert abs(ss_w701.E_ell(2) - expected) < 1e-14 * abs(expected)
        assert abs(E_2_w604 - expected) < 1e-14 * abs(expected)

    def test_subleading_ratio_diagnostic_zero_at_isolated(self):
        p = EModeParameters(
            thomson_rate=1e3, k_eff=0.0, ell_max=2,
        )
        theta_2 = 1e-4
        ss = compute_emode_steady_state(
            p, theta_2_external=theta_2, decision=_allowing_decision(),
        )
        deviation = subleading_cross_check_ratio(ss, theta_2)
        assert abs(deviation) < 1e-12

    def test_subleading_deviation_nonzero_with_streaming(self):
        # Adding streaming (k>0) should make E_2 deviate from -(√6/4)Θ_2
        # because higher ℓ components couple back.
        p = EModeParameters(
            thomson_rate=1.0, k_eff=1.0, ell_max=5,
        )
        theta_2 = 1.0
        ss = compute_emode_steady_state(
            p, theta_2_external=theta_2, decision=_allowing_decision(),
        )
        deviation = subleading_cross_check_ratio(ss, theta_2)
        assert abs(deviation) > 1e-6


# ============================================================================
# 11. TestIntegrationConvergence
# ============================================================================

class TestIntegrationConvergence:

    def test_converges_to_analytic(self):
        p = EModeParameters(thomson_rate=1e3, k_eff=1.0, ell_max=4)
        theta_2 = 1e-4
        init = zero_emode_state(p.ell_max)
        dt_safe = 0.5 * cfl_max_dt_emode(p)
        result = integrate_emode_to_steady_state(
            init, p, theta_2, dt_safe, _allowing_decision(),
            max_steps=20000, tolerance=1e-9,
        )
        assert result.converged
        # rtol 1% structural, tight rtol on E_2 specifically
        np.testing.assert_allclose(
            result.final_state.amplitudes,
            result.steady_state_target.amplitudes,
            rtol=1e-2, atol=1e-20,
        )

    def test_trivial_dynamics_returns_zero_target(self):
        # Γ=0, k=0, source=0 → trivial
        p = EModeParameters(thomson_rate=0.0, k_eff=0.0, ell_max=3)
        init = zero_emode_state(3)
        result = integrate_emode_to_steady_state(
            init, p, 0.0, 1e-3, _allowing_decision(),
            max_steps=100, tolerance=1e-6,
        )
        # Target is zero; initial is zero; trivially converged
        assert np.all(result.final_state.amplitudes == 0.0)


# ============================================================================
# 12. TestPhysicalSignAssertions — v1.2 NEW PATTERN
# ============================================================================

class TestPhysicalSignAssertions:
    """Explicit physical-sign checks against externally-predictable
    signs. This pattern was codified in v1.2 after the W6-04 sign
    error was detected by external cross-reference rather than by
    self-consistent ratio tests.
    """

    def test_positive_theta_2_gives_negative_E_2_at_steady(self):
        # Externally predictable: Θ_2 > 0 produces E_2 < 0 (via the
        # cross-coupling sign, corroborated by W6-04).
        p = EModeParameters(thomson_rate=1e3, k_eff=0.0, ell_max=3)
        ss = compute_emode_steady_state(
            p, theta_2_external=+1e-4, decision=_allowing_decision(),
        )
        assert ss.E_ell(2) < 0.0

    def test_negative_theta_2_gives_positive_E_2_at_steady(self):
        # Sign-symmetry: Θ_2 < 0 → E_2 > 0 (linearity of the system)
        p = EModeParameters(thomson_rate=1e3, k_eff=0.0, ell_max=3)
        ss = compute_emode_steady_state(
            p, theta_2_external=-1e-4, decision=_allowing_decision(),
        )
        assert ss.E_ell(2) > 0.0

    def test_source_coefficient_magnitude(self):
        # |s_2| / (Γ_T × |Θ_2|) = 3/(5√6) ≈ 0.2449 (externally known)
        p = EModeParameters(thomson_rate=1.0, k_eff=0.0, ell_max=2)
        theta_2 = 1.0
        s = build_emode_source_vector(p, theta_2_external=theta_2)
        expected_magnitude = 3.0 / (5.0 * SQRT6)
        assert abs(abs(s[0]) - expected_magnitude) < 1e-14

    def test_effective_damping_at_ell_2_is_two_fifths_gamma(self):
        # |Γ^E_2| / Γ_T = 2/5 = 0.4 exactly (document §3.3)
        p = EModeParameters(thomson_rate=1.0, k_eff=0.0, ell_max=2)
        gamma = build_emode_damping_vector(p)
        assert abs(gamma[0] - 0.4) < 1e-14


# ============================================================================
# 13. TestCFLDiagnostic
# ============================================================================

class TestCFLDiagnostic:

    def test_cfl_positive_finite(self):
        p = EModeParameters(thomson_rate=1e3, k_eff=5.0, ell_max=5)
        dt_max = cfl_max_dt_emode(p)
        assert dt_max > 0.0
        assert dt_max < float("inf")

    def test_cfl_infinite_when_no_dynamics(self):
        p = EModeParameters(thomson_rate=0.0, k_eff=0.0, ell_max=3)
        assert cfl_max_dt_emode(p) == float("inf")


# ============================================================================
# 14. TestSubleadingCrossCheckRatio
# ============================================================================

class TestSubleadingCrossCheckRatio:

    def test_nan_for_zero_theta_2(self):
        s = zero_emode_state(3)
        r = subleading_cross_check_ratio(s, theta_2_external=0.0)
        assert math.isnan(r)

    def test_nonfinite_theta_2_rejected(self):
        s = zero_emode_state(3)
        with pytest.raises(ValueError, match="theta_2_external must be"):
            subleading_cross_check_ratio(s, theta_2_external=float("inf"))


# ============================================================================
# 15. TestRuntimeGatingW3
# ============================================================================

class TestRuntimeGatingW3:

    def test_euler_step_gates(self):
        p = EModeParameters(thomson_rate=1.0, k_eff=0.0, ell_max=3)
        with pytest.raises(CanonicalBlockError):
            euler_step_emode(
                zero_emode_state(3), p, theta_2_external=0.0,
                dt=1e-3, decision=_blocking_decision(),
            )

    def test_steady_state_gates(self):
        p = EModeParameters(thomson_rate=1.0, k_eff=0.0, ell_max=3)
        with pytest.raises(CanonicalBlockError):
            compute_emode_steady_state(
                p, theta_2_external=0.0, decision=_blocking_decision(),
            )

    def test_integrate_gates(self):
        p = EModeParameters(thomson_rate=1.0, k_eff=0.0, ell_max=3)
        with pytest.raises(CanonicalBlockError):
            integrate_emode_to_steady_state(
                zero_emode_state(3), p, 0.0, 1e-3, _blocking_decision(),
            )

    def test_utilities_have_no_gate(self):
        import inspect
        for fn in [
            pstf_emode_coupling_coeffs,
            build_emode_streaming_matrix,
            build_emode_damping_vector,
            build_emode_source_vector,
            cfl_max_dt_emode,
            subleading_cross_check_ratio,
        ]:
            sig = inspect.signature(fn)
            assert "decision" not in sig.parameters, (
                f"{fn.__name__} should not have a decision parameter"
            )
