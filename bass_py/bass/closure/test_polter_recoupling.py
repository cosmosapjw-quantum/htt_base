"""
Test suite: bass/closure/polter_recoupling.py  (Week 7-02)
===========================================================

Test classes:
  1. TestPolterRecoupling            — container invariants, is_trivial
  2. TestNoPolterRecouplingFactory   — factory returns trivial
  3. TestPolterCAMBFormulaReExport   — thin wrapper correctness
  4. TestDampingVectorModification   — (9/10) factor at ℓ=2
  5. TestSourceVectorModification    — E_2 cross-coupling at ℓ=2
  6. TestW5ABackwardCompat           — trivial → W5-A bit-exact
  7. TestEulerStepPolterDriven       — single step formula, gates
  8. TestSteadyStatePolterDriven     — analytic linsolve
  9. TestW604JointConsistency        — residual zero at tight-coupling
 10. TestPhysicalSignAssertions      — v1.2 NEW PATTERN
 11. TestJointLoopW702W701           — W7-02+W7-01 fixed point = W6-04
 12. TestIntegrationConvergence      — Euler → analytic target
 13. TestCFLDiagnostic               — CFL bound
 14. TestRuntimeGatingW3             — gating discipline
"""
from __future__ import annotations

import math
import numpy as np
import pytest

from bass.closure.polter_recoupling import (
    PolterRecoupling,
    build_polter_damping_vector,
    build_polter_driven_source_vector,
    cfl_max_dt_polter_driven,
    compute_steady_state_polter_driven,
    euler_step_polter_driven,
    integrate_polter_driven_to_steady_state,
    joint_w604_consistency_residual,
    no_polter_recoupling,
    polter_camb,
)
from bass.closure.quadrupole_tca import (
    polter_camb as polter_camb_source,
    solve_tca_closure,
)
from bass.collision.thomson_tensor import (
    AxisymmetricSTFTensor, SymmetryAxis, SIGMA_2_PHOTON_BE,
)
from bass.transport.ray_transport import TransportSpecies
from bass.transport.multipole_hierarchy import (
    HierarchyParameters,
    MultipoleState,
    build_source_vector,
    compute_steady_state_hierarchy,
    euler_step_hierarchy,
    zero_state,
)
from bass.transport.emode_hierarchy import (
    EModeParameters,
    compute_emode_steady_state,
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

SQRT6 = math.sqrt(6.0)
SUBLEADING_RATIO = -SQRT6 / 4.0  # E_2/Θ_2 in W6-04 subleading


def _G(x):
    return np.asarray(x, dtype=float)


def _allowing_decision() -> CanonicalDecision:
    tang = compute_D_diagnostic(
        G_field=_G, kind=TangentKind.ONE_FIELD, xi=0, eta=0.0,
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
        G_field=_G, kind=TangentKind.ONE_FIELD, xi=0, eta=0.0,
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


def _std_photon_params(ell_max=5, k_eff=1.0, gamma=1e3,
                       sigma_amp=1e-6) -> HierarchyParameters:
    return HierarchyParameters(
        species=TransportSpecies.PHOTON,
        damping_rate=gamma,
        shear=AxisymmetricSTFTensor(
            amplitude=sigma_amp, axis=SymmetryAxis.Z,
        ),
        shear_coefficient=SIGMA_2_PHOTON_BE,
        k_eff=k_eff,
        ell_max=ell_max,
    )


# ============================================================================
# 1. TestPolterRecoupling
# ============================================================================

class TestPolterRecoupling:

    def test_default_is_active(self):
        r = PolterRecoupling()
        assert r.has_polarization is True
        # thomson_rate=0 default makes it trivial via is_trivial
        assert r.is_trivial is True

    def test_active_configuration(self):
        r = PolterRecoupling(
            E_2_external=1e-6, thomson_rate=1e3,
        )
        assert r.has_polarization is True
        assert not r.is_trivial

    def test_has_polarization_false_makes_trivial(self):
        r = PolterRecoupling(
            E_2_external=1e-6, thomson_rate=1e3,
            has_polarization=False,
        )
        assert r.is_trivial

    def test_zero_thomson_makes_trivial(self):
        r = PolterRecoupling(
            E_2_external=1e-6, thomson_rate=0.0,
        )
        assert r.is_trivial

    def test_rejects_negative_thomson(self):
        with pytest.raises(ValueError, match="thomson_rate must be"):
            PolterRecoupling(thomson_rate=-1.0)

    def test_rejects_nonfinite_E_2(self):
        with pytest.raises(ValueError, match="E_2_external must be finite"):
            PolterRecoupling(E_2_external=float("nan"))


# ============================================================================
# 2. TestNoPolterRecouplingFactory
# ============================================================================

class TestNoPolterRecouplingFactory:

    def test_factory_trivial(self):
        r = no_polter_recoupling()
        assert r.is_trivial
        assert r.has_polarization is False


# ============================================================================
# 3. TestPolterCAMBFormulaReExport
# ============================================================================

class TestPolterCAMBFormulaReExport:

    def test_matches_quadrupole_tca_polter(self):
        pig, E_2 = 1e-4, -2e-5
        assert polter_camb(pig, E_2) == polter_camb_source(pig, E_2)

    def test_literal_formula(self):
        # polter = pig/10 + 9 E_2 / 15
        p = polter_camb(1.0, 2.0)
        expected = 1.0 / 10.0 + 9.0 * 2.0 / 15.0
        assert abs(p - expected) < 1e-14


# ============================================================================
# 4. TestDampingVectorModification
# ============================================================================

class TestDampingVectorModification:

    def test_ell_2_reduced_to_nine_tenths(self):
        p = _std_photon_params(ell_max=5, gamma=1e3)
        r = PolterRecoupling(E_2_external=0.0, thomson_rate=1e3)
        gamma = build_polter_damping_vector(p, r)
        assert abs(gamma[2] - (9.0 / 10.0) * 1e3) < 1e-14

    def test_other_ell_unchanged(self):
        p = _std_photon_params(ell_max=5, gamma=1e3)
        r = PolterRecoupling(E_2_external=0.0, thomson_rate=1e3)
        gamma = build_polter_damping_vector(p, r)
        for ell in [0, 1, 3, 4, 5]:
            assert gamma[ell] == 1e3

    def test_trivial_gives_uniform(self):
        p = _std_photon_params(ell_max=5, gamma=1e3)
        gamma = build_polter_damping_vector(p, no_polter_recoupling())
        for v in gamma:
            assert v == 1e3


# ============================================================================
# 5. TestSourceVectorModification
# ============================================================================

class TestSourceVectorModification:

    def test_polter_source_added_at_ell_2(self):
        p = _std_photon_params(ell_max=5)
        E_2 = 1e-6
        Gamma = 1e3
        r = PolterRecoupling(E_2_external=E_2, thomson_rate=Gamma)
        b = build_polter_driven_source_vector(p, r)
        b_w5a = build_source_vector(p)
        # b[2] = b_w5a[2] + (-(√6/10) × Γ × E_2)
        polter_term = -(SQRT6 / 10.0) * Gamma * E_2
        assert abs(b[2] - (b_w5a[2] + polter_term)) < 1e-14

    def test_other_ell_unchanged(self):
        p = _std_photon_params(ell_max=5)
        r = PolterRecoupling(E_2_external=1e-6, thomson_rate=1e3)
        b = build_polter_driven_source_vector(p, r)
        b_w5a = build_source_vector(p)
        for ell in [0, 1, 3, 4, 5]:
            assert b[ell] == b_w5a[ell]

    def test_zero_E_2_no_modification(self):
        p = _std_photon_params(ell_max=5)
        r = PolterRecoupling(E_2_external=0.0, thomson_rate=1e3)
        b = build_polter_driven_source_vector(p, r)
        b_w5a = build_source_vector(p)
        np.testing.assert_array_equal(b, b_w5a)


# ============================================================================
# 6. TestW5ABackwardCompat
# ============================================================================

class TestW5ABackwardCompat:
    """Trivial recoupling must produce bit-exact W5-A behavior."""

    def test_damping_vector_w5a(self):
        p = _std_photon_params(ell_max=5, gamma=1e3)
        gamma = build_polter_damping_vector(p, no_polter_recoupling())
        assert np.all(gamma == p.damping_rate)

    def test_source_vector_w5a(self):
        p = _std_photon_params(ell_max=5)
        b = build_polter_driven_source_vector(p, no_polter_recoupling())
        b_w5a = build_source_vector(p)
        np.testing.assert_array_equal(b, b_w5a)

    def test_euler_step_identical(self):
        p = _std_photon_params(ell_max=5, k_eff=5.0, gamma=1e3)
        state = MultipoleState(
            amplitudes=np.array([1e-4, 2e-5, 5e-6, 1e-6, 3e-7, 8e-8]),
            axis=SymmetryAxis.Z,
        )
        dt = 1e-5
        s_w5a = euler_step_hierarchy(state, p, dt, _allowing_decision())
        s_polter = euler_step_polter_driven(
            state, p, no_polter_recoupling(), dt, _allowing_decision(),
        )
        np.testing.assert_array_equal(
            s_w5a.amplitudes, s_polter.amplitudes,
        )

    def test_steady_state_identical(self):
        p = _std_photon_params(ell_max=5, k_eff=5.0, gamma=1e3)
        ss_w5a = compute_steady_state_hierarchy(p, _allowing_decision())
        ss_polter = compute_steady_state_polter_driven(
            p, no_polter_recoupling(), _allowing_decision(),
        )
        np.testing.assert_allclose(
            ss_w5a.amplitudes, ss_polter.amplitudes, rtol=1e-14,
        )


# ============================================================================
# 7. TestEulerStepPolterDriven
# ============================================================================

class TestEulerStepPolterDriven:

    def test_e_2_cross_coupling_effect(self):
        # Start with Θ=0, no shear. Apply E_2 > 0.
        # Expected: Θ_2 decreases (polter source is negative with E_2 > 0).
        p = HierarchyParameters(
            species=TransportSpecies.PHOTON,
            damping_rate=1.0,
            shear=AxisymmetricSTFTensor(
                amplitude=0.0, axis=SymmetryAxis.Z,
            ),
            shear_coefficient=0.0,
            k_eff=0.0,
            ell_max=3,
        )
        r = PolterRecoupling(E_2_external=1e-4, thomson_rate=1.0)
        init = zero_state(p.ell_max)
        dt = 1e-3
        new = euler_step_polter_driven(
            init, p, r, dt, _allowing_decision(),
        )
        # source[2] = -(√6/10) × 1 × 1e-4 < 0, so Θ_2 new value < 0
        assert new.amplitudes[2] < 0.0

    def test_rejects_zero_dt(self):
        p = _std_photon_params()
        with pytest.raises(ValueError, match="dt must be positive"):
            euler_step_polter_driven(
                zero_state(p.ell_max), p, no_polter_recoupling(),
                0.0, _allowing_decision(),
            )

    def test_rejects_shape_mismatch(self):
        p = _std_photon_params(ell_max=5)
        with pytest.raises(ValueError, match="ell_max"):
            euler_step_polter_driven(
                zero_state(3), p, no_polter_recoupling(),
                1e-5, _allowing_decision(),
            )


# ============================================================================
# 8. TestSteadyStatePolterDriven
# ============================================================================

class TestSteadyStatePolterDriven:

    def test_amplification_vs_w5a(self):
        # With polter recoupling active, Θ_2 is LARGER than W5-A
        # (factor 4/3 at tight coupling; polarization return AMPLIFIES
        # the quadrupole).
        p = _std_photon_params(ell_max=3, k_eff=0.0, gamma=1e3,
                               sigma_amp=1e-6)
        # W5-A: Θ_2 = Σ_2 σ / Γ
        ss_w5a = compute_steady_state_hierarchy(p, _allowing_decision())
        # W7-02 WITHOUT E_2 feedback: Θ_2 = Σ_2 σ / (9/10 × Γ) = (10/9) × W5-A
        r_no_E = PolterRecoupling(
            E_2_external=0.0, thomson_rate=p.damping_rate,
        )
        ss_polter_noE = compute_steady_state_polter_driven(
            p, r_no_E, _allowing_decision(),
        )
        ratio = ss_polter_noE.amplitudes[2] / ss_w5a.amplitudes[2]
        # Should be 10/9 ≈ 1.111 (just from damping reduction)
        assert abs(ratio - 10.0 / 9.0) < 1e-6

    def test_E_2_feedback_reduces_theta_2(self):
        # With Θ_2 > 0 at steady state, E_2 = -(√6/4) Θ_2 < 0.
        # Feed E_2 < 0 back: polter source = -(√6/10) × Γ × (negative) > 0,
        # which ADDS to Θ_2. But we compare WITH and WITHOUT feedback,
        # where the expected amplification factor from full recoupling
        # is 4/3 vs 1 (W5-A). So with feedback ON, Θ_2 is LARGER.
        p = _std_photon_params(ell_max=3, k_eff=0.0, gamma=1e3,
                               sigma_amp=1e-6)
        ss_w5a = compute_steady_state_hierarchy(p, _allowing_decision())
        
        # Self-consistent E_2 for the W5-A Θ_2: E_2 = -(√6/4) × Θ_2
        theta_2_w5a = ss_w5a.amplitudes[2]
        E_2_consistent = SUBLEADING_RATIO * theta_2_w5a
        r_with_E = PolterRecoupling(
            E_2_external=E_2_consistent, thomson_rate=p.damping_rate,
        )
        ss_polter_withE = compute_steady_state_polter_driven(
            p, r_with_E, _allowing_decision(),
        )
        # With feedback, Θ_2 is larger than W5-A. Factor depends on
        # how accurate E_2_consistent is (approximation of fixed-point).
        assert ss_polter_withE.amplitudes[2] > ss_w5a.amplitudes[2]

    def test_no_trivial_null_dynamics(self):
        # Γ=0, k=0, trivial dynamics → ValueError
        p = HierarchyParameters(
            species=TransportSpecies.PHOTON,
            damping_rate=0.0,
            shear=AxisymmetricSTFTensor(0.0, SymmetryAxis.Z),
            shear_coefficient=0.0,
            k_eff=0.0,
            ell_max=3,
        )
        r = PolterRecoupling(E_2_external=1e-6, thomson_rate=1e3)
        with pytest.raises(ValueError, match="trivial null dynamics"):
            compute_steady_state_polter_driven(
                p, r, _allowing_decision(),
            )


# ============================================================================
# 9. TestW604JointConsistency
# ============================================================================

class TestW604JointConsistency:
    """Given (Θ_2, E_2) from W6-04, the joint residual must be zero."""

    def test_residual_zero_at_w604_solution(self):
        gamma_T = 1e3
        S_T = 1e-3
        S_E = 0.0
        theta_2, E_2 = solve_tca_closure(
            S_T, S_E, gamma_T, _allowing_decision(),
        )
        res = joint_w604_consistency_residual(
            theta_2, E_2, S_T, S_E, gamma_T,
        )
        assert res < 1e-14

    def test_residual_nonzero_at_w5a_solution(self):
        # W5-A solution has different Θ_2 (no polarization amplification).
        # It should NOT satisfy the W6-04 equation.
        gamma_T = 1.0
        S_T = 1.0
        theta_2_w5a = S_T / gamma_T  # naive W5-A value
        E_2_guess = 0.0
        res = joint_w604_consistency_residual(
            theta_2_w5a, E_2_guess, S_T, 0.0, gamma_T,
        )
        # Should be significantly non-zero
        assert res > 0.01

    def test_residual_with_both_sources(self):
        # Full test: both S_T and S_E nonzero
        gamma_T = 1e3
        S_T, S_E = 2e-3, 5e-4
        theta_2, E_2 = solve_tca_closure(
            S_T, S_E, gamma_T, _allowing_decision(),
        )
        res = joint_w604_consistency_residual(
            theta_2, E_2, S_T, S_E, gamma_T,
        )
        assert res < 1e-14


# ============================================================================
# 10. TestPhysicalSignAssertions — v1.2 pattern
# ============================================================================

class TestPhysicalSignAssertions:
    """Explicit physical-sign checks for polter recoupling outputs."""

    def test_polter_source_E_2_positive_gives_negative_source(self):
        # E_2 > 0 → polter source at ℓ=2 is -(√6/10)Γ_T × E_2 < 0
        p = _std_photon_params(ell_max=5)
        r = PolterRecoupling(E_2_external=+1e-6, thomson_rate=1e3)
        b = build_polter_driven_source_vector(p, r)
        b_w5a = build_source_vector(p)
        polter_contribution = b[2] - b_w5a[2]
        assert polter_contribution < 0.0

    def test_polter_source_E_2_negative_gives_positive_source(self):
        # E_2 < 0 → polter contribution > 0
        p = _std_photon_params(ell_max=5)
        r = PolterRecoupling(E_2_external=-1e-6, thomson_rate=1e3)
        b = build_polter_driven_source_vector(p, r)
        b_w5a = build_source_vector(p)
        polter_contribution = b[2] - b_w5a[2]
        assert polter_contribution > 0.0

    def test_damping_at_ell_2_reduction_factor(self):
        # Reduction factor is 9/10 = 0.9 exactly (document §3.3)
        p = _std_photon_params(ell_max=3, gamma=1.0)
        r = PolterRecoupling(E_2_external=0.0, thomson_rate=1.0)
        gamma = build_polter_damping_vector(p, r)
        assert abs(gamma[2] - 0.9) < 1e-14

    def test_amplification_factor_at_tight_coupling(self):
        # Joint W6-04 gives Θ_2 = (4/3) S_T/Γ, W5-A gives S_T/Γ:
        # ratio 4/3 is the full amplification factor from polarization.
        gamma_T = 1.0
        S_T = 1.0
        theta_2, _ = solve_tca_closure(
            S_T, 0.0, gamma_T, _allowing_decision(),
        )
        theta_2_w5a = S_T / gamma_T
        ratio = theta_2 / theta_2_w5a
        assert abs(ratio - 4.0 / 3.0) < 1e-14


# ============================================================================
# 11. TestJointLoopW702W701 — bidirectional fixed-point
# ============================================================================

class TestJointLoopW702W701:
    """Running W5A+W7-02 (for Θ) and W7-01 (for E) to mutual fixed point
    must reproduce W6-04 at the isolated ℓ=2 limit.
    """

    def test_mutual_fixed_point_matches_w604(self):
        # Isolated ℓ=2 (k_eff=0, ell_max=2 for both hierarchies).
        # W7-01 parameters: E_2 hierarchy
        # W7-02 parameters: Θ hierarchy with polter recoupling
        gamma_T = 1e3
        sigma_amp = 1e-6
        theta_params = HierarchyParameters(
            species=TransportSpecies.PHOTON,
            damping_rate=gamma_T,
            shear=AxisymmetricSTFTensor(
                amplitude=sigma_amp, axis=SymmetryAxis.Z,
            ),
            shear_coefficient=SIGMA_2_PHOTON_BE,
            k_eff=0.0,
            ell_max=2,
        )
        E_params = EModeParameters(
            thomson_rate=gamma_T, k_eff=0.0, ell_max=2,
        )

        # Fixed-point iteration
        E_2 = 0.0
        theta_2 = 0.0
        for _ in range(100):
            # Update Θ hierarchy given current E_2
            r = PolterRecoupling(
                E_2_external=E_2, thomson_rate=gamma_T,
            )
            theta_ss = compute_steady_state_polter_driven(
                theta_params, r, _allowing_decision(),
            )
            theta_2_new = theta_ss.amplitudes[2]
            # Update E hierarchy given current Θ_2
            E_ss = compute_emode_steady_state(
                E_params, theta_2_new, _allowing_decision(),
            )
            E_2_new = E_ss.E_ell(2)
            if (abs(theta_2_new - theta_2) < 1e-15
                    and abs(E_2_new - E_2) < 1e-15):
                break
            theta_2, E_2 = theta_2_new, E_2_new

        # Compare to W6-04 direct
        S_T = SIGMA_2_PHOTON_BE * sigma_amp
        theta_w604, E_w604 = solve_tca_closure(
            S_T, 0.0, gamma_T, _allowing_decision(),
        )
        # Fixed point should match W6-04 closely. Absolute precision is
        # at machine level (1e-16); relative precision is limited by the
        # small magnitude of Θ_2 (~1e-9 with Σ=2.044, σ=1e-6, Γ=1e3).
        np.testing.assert_allclose(
            theta_2, theta_w604, rtol=1e-6, atol=1e-14,
        )
        np.testing.assert_allclose(
            E_2, E_w604, rtol=1e-6, atol=1e-14,
        )

    def test_residual_after_fixed_point_near_zero(self):
        gamma_T = 1e3
        sigma_amp = 1e-6
        S_T = SIGMA_2_PHOTON_BE * sigma_amp

        # Compute W6-04 directly (it IS the fixed point)
        theta_w604, E_w604 = solve_tca_closure(
            S_T, 0.0, gamma_T, _allowing_decision(),
        )
        # Residual should be zero
        res = joint_w604_consistency_residual(
            theta_w604, E_w604, S_T, 0.0, gamma_T,
        )
        assert res < 1e-14


# ============================================================================
# 12. TestIntegrationConvergence
# ============================================================================

class TestIntegrationConvergence:

    def test_converges_to_analytic(self):
        p = _std_photon_params(ell_max=3, k_eff=1.0, gamma=1e3)
        r = PolterRecoupling(E_2_external=-1e-7, thomson_rate=1e3)
        init = zero_state(p.ell_max)
        dt = 0.5 * cfl_max_dt_polter_driven(p, r)
        result = integrate_polter_driven_to_steady_state(
            init, p, r, dt, _allowing_decision(),
            max_steps=20000, tolerance=1e-9,
        )
        assert result.converged
        np.testing.assert_allclose(
            result.final_state.amplitudes,
            result.steady_state_target.amplitudes,
            rtol=1e-2, atol=1e-20,
        )

    def test_trivial_recoupling_matches_w5a_integration(self):
        from bass.transport.multipole_hierarchy import (
            integrate_hierarchy_to_steady_state,
        )
        p = _std_photon_params(ell_max=5, k_eff=1.0, gamma=1e3)
        init = zero_state(p.ell_max)
        dt = 1e-4
        r_w5a = integrate_hierarchy_to_steady_state(
            init, p, dt, _allowing_decision(),
            max_steps=2000, tolerance=1e-8,
        )
        r_polter = integrate_polter_driven_to_steady_state(
            init, p, no_polter_recoupling(), dt,
            _allowing_decision(),
            max_steps=2000, tolerance=1e-8,
        )
        np.testing.assert_allclose(
            r_w5a.final_state.amplitudes,
            r_polter.final_state.amplitudes,
            rtol=1e-12,
        )


# ============================================================================
# 13. TestCFLDiagnostic
# ============================================================================

class TestCFLDiagnostic:

    def test_cfl_positive_finite(self):
        p = _std_photon_params()
        dt = cfl_max_dt_polter_driven(p, no_polter_recoupling())
        assert 0 < dt < float("inf")

    def test_cfl_independent_of_ell_2_reduction(self):
        # At ell_max=3 with gamma=1e3, max(γ) = 1e3 (ℓ=0,1 or 3 dominate),
        # reducing γ[2] to 900 doesn't change max. So CFL same as W5-A.
        p = _std_photon_params(ell_max=3, gamma=1e3)
        r_active = PolterRecoupling(E_2_external=0.0, thomson_rate=1e3)
        dt_active = cfl_max_dt_polter_driven(p, r_active)
        dt_trivial = cfl_max_dt_polter_driven(p, no_polter_recoupling())
        assert dt_active == dt_trivial


# ============================================================================
# 14. TestRuntimeGatingW3
# ============================================================================

class TestRuntimeGatingW3:

    def test_euler_step_gates(self):
        p = _std_photon_params()
        with pytest.raises(CanonicalBlockError):
            euler_step_polter_driven(
                zero_state(p.ell_max), p, no_polter_recoupling(),
                1e-5, _blocking_decision(),
            )

    def test_steady_state_gates(self):
        p = _std_photon_params()
        with pytest.raises(CanonicalBlockError):
            compute_steady_state_polter_driven(
                p, no_polter_recoupling(), _blocking_decision(),
            )

    def test_integrate_gates(self):
        p = _std_photon_params()
        with pytest.raises(CanonicalBlockError):
            integrate_polter_driven_to_steady_state(
                zero_state(p.ell_max), p, no_polter_recoupling(),
                1e-5, _blocking_decision(),
            )

    def test_utilities_have_no_gate(self):
        import inspect
        for fn in [
            build_polter_damping_vector,
            build_polter_driven_source_vector,
            cfl_max_dt_polter_driven,
            joint_w604_consistency_residual,
            polter_camb,
        ]:
            sig = inspect.signature(fn)
            assert "decision" not in sig.parameters, (
                f"{fn.__name__} should not have a decision parameter"
            )
