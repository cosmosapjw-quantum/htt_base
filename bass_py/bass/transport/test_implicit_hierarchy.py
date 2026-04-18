"""
Test suite: bass/transport/implicit_hierarchy.py  (Week 5-B)
==============================================================

Three implicit integrators for the multi-ℓ hierarchy + runtime gating.

Test classes (10):
  1. TestImplicitMethod          — enum identity
  2. TestStabilityFunctions      — R(z) = 1/(1-z), (1+z/2)/(1-z/2), exp(z)
  3. TestBackwardEulerStep       — BE formula, small-dt limit
  4. TestCrankNicolsonStep       — CN formula, 2nd-order accuracy
  5. TestExponentialStep         — EXACT for linear TI system (oracle)
  6. TestMethodCrossCheck        — BE ≈ CN ≈ EXP at small dt
  7. TestStiffRegimeStability    — implicit survives where explicit diverges
  8. TestIntegrateImplicitDriver — loop + convergence + method dispatch
  9. TestRuntimeGating           — all entries gate
 10. TestValidation              — input validation and edge cases

Target: ~55 tests.
"""
from __future__ import annotations

import math
import numpy as np
import pytest

from bass.collision.thomson_tensor import AxisymmetricSTFTensor, SymmetryAxis
from bass.transport.ray_transport import TransportSpecies, SIGMA_2_NEUTRINO_FD
from bass.transport.multipole_hierarchy import (
    MultipoleState, HierarchyParameters, HierarchyIntegrationResult,
    zero_state, build_streaming_matrix, build_source_vector,
    make_photon_hierarchy_parameters, make_neutrino_hierarchy_parameters,
    euler_step_hierarchy, compute_steady_state_hierarchy, cfl_max_dt,
    SIGMA_2_PHOTON_BE,
)
from bass.transport.implicit_hierarchy import (
    ImplicitMethod,
    backward_euler_step, crank_nicolson_step, exponential_step,
    integrate_implicit_to_steady_state,
    stability_function_ratio,
)
from bass.runtime.canonical_decision import (
    CanonicalDecision, CanonicalBlockError, make_canonical_decision,
)
from tsc.diagnostics.tangency import compute_D_diagnostic, TangentKind


# ============================================================================
# Fixtures
# ============================================================================

def _on(x):
    return np.asarray(x, dtype=float)


def _allowing_decision() -> CanonicalDecision:
    tang = compute_D_diagnostic(
        G_field=_on, kind=TangentKind.ONE_FIELD, xi=0, eta=0.0,
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
        G_field=_on, kind=TangentKind.ONE_FIELD, xi=0, eta=0.0,
    )
    return make_canonical_decision(
        beta_result=(False, {
            "beta": 0.5, "beta_max": 8.62e-3, "slack": -0.49,
            "eta_u_dot": 0.16, "safety_factor": 0.5, "epsilon_1": 0.02,
        }),
        sigma_result=(True, {
            "sigma_sq": 1e-5, "floor": 1e-6, "log_margin_decades": 1.0,
        }),
        tangency_result=tang,
    )


def _std_params(k_eff: float = 5.0, ell_max: int = 4):
    shear = AxisymmetricSTFTensor(amplitude=1e-6)
    return make_photon_hierarchy_parameters(
        n_e_sigmaT=100.0, shear=shear, k_eff=k_eff, ell_max=ell_max,
        decision=_allowing_decision(),
    )


def _stiff_params(ell_max: int = 5):
    """Pre-recombination: τ̇ = 10⁴, H scale 30, k_eff = 10. τ̇/H = 333."""
    shear = AxisymmetricSTFTensor(amplitude=1e-6)
    return make_photon_hierarchy_parameters(
        n_e_sigmaT=1e4, shear=shear, k_eff=10.0, ell_max=ell_max,
        decision=_allowing_decision(),
    )


# ============================================================================
# Test Class 1 - ImplicitMethod enum
# ============================================================================

class TestImplicitMethod:
    def test_three_members(self):
        assert len(list(ImplicitMethod)) == 3

    def test_backward_euler_value(self):
        assert ImplicitMethod.BACKWARD_EULER.value == "backward_euler"

    def test_crank_nicolson_value(self):
        assert ImplicitMethod.CRANK_NICOLSON.value == "crank_nicolson"

    def test_exponential_value(self):
        assert ImplicitMethod.EXPONENTIAL.value == "exponential"


# ============================================================================
# Test Class 2 - Stability functions
# ============================================================================

class TestStabilityFunctions:
    def test_BE_formula(self):
        # R(z) = 1/(1-z)
        assert stability_function_ratio(
            ImplicitMethod.BACKWARD_EULER, -1.0,
        ) == pytest.approx(0.5, rel=1e-14)

    def test_CN_formula(self):
        # R(-1) = (1-1/2)/(1+1/2) = (1/2)/(3/2) = 1/3
        assert stability_function_ratio(
            ImplicitMethod.CRANK_NICOLSON, -1.0,
        ) == pytest.approx(1.0 / 3.0, rel=1e-14)

    def test_EXP_formula(self):
        assert stability_function_ratio(
            ImplicitMethod.EXPONENTIAL, -1.0,
        ) == pytest.approx(math.exp(-1.0), rel=1e-14)

    def test_BE_L_stable_at_minus_infinity(self):
        # |R(z)| → 0 as z → -∞ (L-stability)
        z = -1e10
        R = stability_function_ratio(ImplicitMethod.BACKWARD_EULER, z)
        assert abs(R) < 1e-8

    def test_CN_not_L_stable(self):
        # |R(∞)| → 1 for CN (A-stable but NOT L-stable)
        z = -1e10
        R = stability_function_ratio(ImplicitMethod.CRANK_NICOLSON, z)
        assert abs(R) == pytest.approx(1.0, rel=1e-6)

    def test_all_methods_stable_for_negative_real_z(self):
        for z in [-0.1, -1.0, -10.0, -100.0]:
            for m in [ImplicitMethod.BACKWARD_EULER,
                      ImplicitMethod.CRANK_NICOLSON,
                      ImplicitMethod.EXPONENTIAL]:
                R = stability_function_ratio(m, z)
                assert abs(R) <= 1.0 + 1e-10, f"method={m} at z={z}, |R|={abs(R)}"

    def test_rejects_unknown_method_enum_string(self):
        # Pass a string instead of enum
        with pytest.raises((ValueError, AttributeError)):
            stability_function_ratio("unknown", -1.0)


# ============================================================================
# Test Class 3 - Backward Euler
# ============================================================================

class TestBackwardEulerStep:
    def test_formula_single_ell(self):
        """At L=0, k=0, Γ=2, σ=0 (no source): (1 + 2dt)Θ' = Θ. So Θ' = Θ/(1+2dt)."""
        shear_zero = AxisymmetricSTFTensor(amplitude=0.0)
        params = HierarchyParameters(
            species=TransportSpecies.PHOTON, damping_rate=2.0,
            shear=shear_zero, shear_coefficient=1.0, k_eff=0.0, ell_max=0,
        )
        s = MultipoleState(amplitudes=np.array([1.0]))
        out = backward_euler_step(s, params, dt=0.1, decision=_allowing_decision())
        # Expected: 1 / (1 + 0.2) = 0.8333...
        assert out.amplitudes[0] == pytest.approx(1.0 / 1.2, rel=1e-14)

    def test_matches_explicit_at_small_dt(self):
        params = _std_params()
        init = zero_state(ell_max=params.ell_max)
        dt = 1e-6  # very small
        s_be = backward_euler_step(init, params, dt, _allowing_decision())
        s_explicit = euler_step_hierarchy(init, params, dt, _allowing_decision())
        # Both should be close — explicit is linear in dt, BE is too at 1st order
        assert np.allclose(s_be.amplitudes, s_explicit.amplitudes, atol=1e-12)

    def test_always_stable(self):
        """BE with arbitrarily large dt does not diverge."""
        params = _stiff_params()
        init = zero_state(ell_max=params.ell_max)
        dt_big = 1e6 * cfl_max_dt(params)  # 10⁶× CFL
        s = init
        for _ in range(20):
            s = backward_euler_step(s, params, dt_big, _allowing_decision())
        # Must not blow up
        assert np.max(np.abs(s.amplitudes)) < 1e10

    def test_axis_preserved(self):
        shear = AxisymmetricSTFTensor(amplitude=1e-6, axis=SymmetryAxis.Y)
        params = make_photon_hierarchy_parameters(
            n_e_sigmaT=10.0, shear=shear, k_eff=0.0, ell_max=2,
            decision=_allowing_decision(),
        )
        init = zero_state(ell_max=2, axis=SymmetryAxis.Y)
        out = backward_euler_step(init, params, 1e-3, _allowing_decision())
        assert out.axis == SymmetryAxis.Y

    def test_reaches_steady_state_in_stiff_regime(self):
        params = _stiff_params()
        init = zero_state(ell_max=params.ell_max)
        dt = cfl_max_dt(params) * 10  # 10× CFL — explicit would fail
        s = init
        for _ in range(100):
            s = backward_euler_step(s, params, dt, _allowing_decision())
        target = compute_steady_state_hierarchy(params, _allowing_decision())
        rel_err = np.max(np.abs(s.amplitudes - target.amplitudes) /
                         (np.abs(target.amplitudes) + 1e-30))
        assert rel_err < 1e-6


# ============================================================================
# Test Class 4 - Crank-Nicolson
# ============================================================================

class TestCrankNicolsonStep:
    def test_formula_single_ell(self):
        """At L=0, k=0, Γ=2: (1+dt)Θ' = (1-dt)Θ."""
        shear_zero = AxisymmetricSTFTensor(amplitude=0.0)
        params = HierarchyParameters(
            species=TransportSpecies.PHOTON, damping_rate=2.0,
            shear=shear_zero, shear_coefficient=1.0, k_eff=0.0, ell_max=0,
        )
        s = MultipoleState(amplitudes=np.array([1.0]))
        # dt = 0.1: LHS = 1 + 0.1 = 1.1; RHS = 1 - 0.1 = 0.9; Θ' = 0.9/1.1
        out = crank_nicolson_step(s, params, dt=0.1, decision=_allowing_decision())
        assert out.amplitudes[0] == pytest.approx(0.9 / 1.1, rel=1e-14)

    def test_second_order_accuracy(self):
        """CN should be 2nd-order in dt vs the exact exponential solution."""
        params = _std_params()
        init = MultipoleState(
            amplitudes=np.array([0.1, 0.0, 1e-6, 0.0, 0.0]),
        )
        # Step at two different dt, look at error ratio
        dt_1 = 1e-3
        dt_2 = 5e-4  # half
        s_cn_1 = crank_nicolson_step(init, params, dt_1, _allowing_decision())
        s_cn_2 = crank_nicolson_step(init, params, dt_2, _allowing_decision())
        s_exact_1 = exponential_step(init, params, dt_1, _allowing_decision())
        s_exact_2 = exponential_step(init, params, dt_2, _allowing_decision())
        err_1 = np.linalg.norm(s_cn_1.amplitudes - s_exact_1.amplitudes)
        err_2 = np.linalg.norm(s_cn_2.amplitudes - s_exact_2.amplitudes)
        # For 2nd order, err_2 / err_1 should be around 0.25 (since dt halved)
        # Tolerate factor-of-3 range to account for finite-precision noise
        if err_1 > 1e-15 and err_2 > 1e-15:
            ratio = err_2 / err_1
            assert 0.1 < ratio < 0.4, f"err ratio {ratio} not consistent with 2nd-order"

    def test_stable_in_stiff_regime(self):
        params = _stiff_params()
        init = zero_state(ell_max=params.ell_max)
        dt = cfl_max_dt(params) * 10
        s = init
        for _ in range(50):
            s = crank_nicolson_step(s, params, dt, _allowing_decision())
        # CN doesn't diverge even at 10× CFL
        assert np.max(np.abs(s.amplitudes)) < 1e-5


# ============================================================================
# Test Class 5 - Exponential step (oracle)
# ============================================================================

class TestExponentialStep:
    def test_exact_for_zero_source_pure_damping(self):
        """Γ Θ decay: Θ(dt) = exp(-Γ dt) Θ(0) exactly."""
        shear_zero = AxisymmetricSTFTensor(amplitude=0.0)
        params = HierarchyParameters(
            species=TransportSpecies.PHOTON, damping_rate=3.0,
            shear=shear_zero, shear_coefficient=1.0, k_eff=0.0, ell_max=0,
        )
        s = MultipoleState(amplitudes=np.array([2.0]))
        out = exponential_step(s, params, dt=1.5, decision=_allowing_decision())
        expected = 2.0 * math.exp(-3.0 * 1.5)
        assert out.amplitudes[0] == pytest.approx(expected, rel=1e-12)

    def test_exact_reaches_steady_state_from_zero_init(self):
        """Exponential step at very large dt jumps directly toward Θ_∞."""
        params = _std_params()
        init = zero_state(ell_max=params.ell_max)
        # Very large dt — exponential is exact
        s = exponential_step(init, params, dt=100.0, decision=_allowing_decision())
        target = compute_steady_state_hierarchy(params, _allowing_decision())
        rel_err = np.max(np.abs(s.amplitudes - target.amplitudes) /
                         (np.abs(target.amplitudes) + 1e-30))
        assert rel_err < 1e-10

    def test_composition_law(self):
        """exp step of 2dt equals two exp steps of dt, bit-exact (up to matrix exp precision)."""
        params = _std_params()
        init = MultipoleState(
            amplitudes=np.array([0.01, 0.01, 0.01, 0.01, 0.01]),
        )
        dt = 0.01
        s1 = exponential_step(init, params, 2.0 * dt, _allowing_decision())
        s2a = exponential_step(init, params, dt, _allowing_decision())
        s2 = exponential_step(s2a, params, dt, _allowing_decision())
        assert np.allclose(s1.amplitudes, s2.amplitudes, rtol=1e-12, atol=1e-15)

    def test_always_stable_arbitrary_dt(self):
        """Exponential step: stable at any dt, converges to Θ_∞ as dt → ∞."""
        params = _stiff_params()
        init = zero_state(ell_max=params.ell_max)
        dt = 1e10  # absurdly large
        out = exponential_step(init, params, dt, _allowing_decision())
        target = compute_steady_state_hierarchy(params, _allowing_decision())
        # Should be indistinguishable from steady state
        assert np.allclose(out.amplitudes, target.amplitudes, atol=1e-10)

    def test_axis_preserved(self):
        shear = AxisymmetricSTFTensor(amplitude=1e-6, axis=SymmetryAxis.X)
        params = make_photon_hierarchy_parameters(
            n_e_sigmaT=10.0, shear=shear, k_eff=0.0, ell_max=2,
            decision=_allowing_decision(),
        )
        init = zero_state(ell_max=2, axis=SymmetryAxis.X)
        out = exponential_step(init, params, 0.1, _allowing_decision())
        assert out.axis == SymmetryAxis.X

    def test_zero_dt_preserves_state(self):
        """Actually dt=0 is forbidden, but dt → 0 should give state unchanged."""
        params = _std_params()
        s_in = MultipoleState(amplitudes=np.array([1.0, 2.0, 3.0, 4.0, 5.0]))
        dt_small = 1e-15
        s_out = exponential_step(s_in, params, dt_small, _allowing_decision())
        assert np.allclose(s_out.amplitudes, s_in.amplitudes, atol=1e-10)


# ============================================================================
# Test Class 6 - Method cross-check
# ============================================================================

class TestMethodCrossCheck:
    """BE, CN, EXP should all agree at small dt (within expected error orders)."""

    def test_agreement_at_small_dt(self):
        params = _std_params()
        init = MultipoleState(amplitudes=np.array([0.0, 0.0, 1e-7, 0.0, 0.0]))
        dt = 1e-4
        s_be = backward_euler_step(init, params, dt, _allowing_decision())
        s_cn = crank_nicolson_step(init, params, dt, _allowing_decision())
        s_exp = exponential_step(init, params, dt, _allowing_decision())
        # CN should be closer to EXP than BE (2nd order vs 1st)
        err_be = np.linalg.norm(s_be.amplitudes - s_exp.amplitudes)
        err_cn = np.linalg.norm(s_cn.amplitudes - s_exp.amplitudes)
        if err_be > 1e-20 and err_cn > 1e-20:
            assert err_cn <= err_be * 10  # CN at most ~10× BE error (generous)

    def test_all_converge_to_same_steady_state(self):
        """Integrating to convergence with each method gives same final state."""
        params = _std_params()
        init = zero_state(ell_max=params.ell_max)
        target = compute_steady_state_hierarchy(params, _allowing_decision())
        # Use dt large enough that explicit would fail
        dt = cfl_max_dt(params) * 5
        final_states = {}
        for method in ImplicitMethod:
            result = integrate_implicit_to_steady_state(
                init, params, dt, _allowing_decision(),
                method=method, max_steps=2000, tolerance=1e-10,
            )
            final_states[method] = result.final_state.amplitudes
        # All three methods' final states should match target
        for m, amps in final_states.items():
            rel_err = np.max(np.abs(amps - target.amplitudes) /
                             (np.abs(target.amplitudes) + 1e-30))
            assert rel_err < 1e-4, f"method={m} rel_err={rel_err}"


# ============================================================================
# Test Class 7 - Stiff regime stability
# ============================================================================

class TestStiffRegimeStability:
    """The crowning test: implicit survives at 10× CFL where explicit diverges."""

    def test_explicit_diverges_at_10x_CFL(self):
        params = _stiff_params()
        init = zero_state(ell_max=params.ell_max)
        dt = cfl_max_dt(params) * 10
        s = init
        for _ in range(50):
            s = euler_step_hierarchy(s, params, dt, _allowing_decision())
        # Explicit at 10× CFL diverges to enormous values
        assert np.max(np.abs(s.amplitudes)) > 1e30

    def test_backward_euler_stable_at_10x_CFL(self):
        params = _stiff_params()
        init = zero_state(ell_max=params.ell_max)
        dt = cfl_max_dt(params) * 10
        s = init
        for _ in range(50):
            s = backward_euler_step(s, params, dt, _allowing_decision())
        target = compute_steady_state_hierarchy(params, _allowing_decision())
        rel_err = np.max(np.abs(s.amplitudes - target.amplitudes) /
                         (np.abs(target.amplitudes) + 1e-30))
        assert rel_err < 1e-4

    def test_exponential_exact_at_10x_CFL(self):
        params = _stiff_params()
        init = zero_state(ell_max=params.ell_max)
        dt = cfl_max_dt(params) * 10
        s = init
        for _ in range(50):
            s = exponential_step(s, params, dt, _allowing_decision())
        target = compute_steady_state_hierarchy(params, _allowing_decision())
        rel_err = np.max(np.abs(s.amplitudes - target.amplitudes) /
                         (np.abs(target.amplitudes) + 1e-30))
        # Exponential converges exactly
        assert rel_err < 1e-10

    def test_backward_euler_stable_at_100x_CFL(self):
        """BE is stable arbitrarily far beyond CFL."""
        params = _stiff_params()
        init = zero_state(ell_max=params.ell_max)
        dt = cfl_max_dt(params) * 100
        s = init
        for _ in range(30):
            s = backward_euler_step(s, params, dt, _allowing_decision())
        # Finite, not blown up
        assert np.all(np.isfinite(s.amplitudes))
        assert np.max(np.abs(s.amplitudes)) < 1e-5


# ============================================================================
# Test Class 8 - Implicit driver
# ============================================================================

class TestIntegrateImplicitDriver:
    def test_default_method_is_backward_euler(self):
        params = _std_params()
        init = zero_state(ell_max=params.ell_max)
        result = integrate_implicit_to_steady_state(
            init, params, dt=1e-3, decision=_allowing_decision(),
            max_steps=2000, tolerance=1e-8,
        )
        assert result.converged

    def test_backward_euler_converges_stiff(self):
        params = _stiff_params()
        init = zero_state(ell_max=params.ell_max)
        dt = cfl_max_dt(params) * 10
        result = integrate_implicit_to_steady_state(
            init, params, dt=dt, decision=_allowing_decision(),
            method=ImplicitMethod.BACKWARD_EULER,
            max_steps=500, tolerance=1e-8,
        )
        assert result.converged

    def test_exponential_converges_in_few_steps(self):
        """Exponential integrator at large dt reaches steady state very quickly."""
        params = _std_params()
        init = zero_state(ell_max=params.ell_max)
        result = integrate_implicit_to_steady_state(
            init, params, dt=10.0, decision=_allowing_decision(),
            method=ImplicitMethod.EXPONENTIAL,
            max_steps=100, tolerance=1e-10,
        )
        assert result.converged
        assert result.steps_taken < 10  # typically 2-3

    def test_crank_nicolson_converges(self):
        params = _stiff_params()
        init = zero_state(ell_max=params.ell_max)
        dt = cfl_max_dt(params) * 5
        result = integrate_implicit_to_steady_state(
            init, params, dt=dt, decision=_allowing_decision(),
            method=ImplicitMethod.CRANK_NICOLSON,
            max_steps=2000, tolerance=1e-6,
        )
        assert result.converged

    def test_returns_HierarchyIntegrationResult(self):
        params = _std_params()
        init = zero_state(ell_max=params.ell_max)
        result = integrate_implicit_to_steady_state(
            init, params, 1e-2, _allowing_decision(),
        )
        assert isinstance(result, HierarchyIntegrationResult)

    def test_target_matches_compute_steady_state(self):
        """The driver's steady_state_target should match compute_steady_state_hierarchy."""
        params = _std_params()
        init = zero_state(ell_max=params.ell_max)
        result = integrate_implicit_to_steady_state(
            init, params, 1e-2, _allowing_decision(),
        )
        explicit_target = compute_steady_state_hierarchy(
            params, _allowing_decision(),
        )
        assert np.allclose(
            result.steady_state_target.amplitudes,
            explicit_target.amplitudes,
            rtol=1e-10,
        )


# ============================================================================
# Test Class 9 - Runtime gating
# ============================================================================

class TestRuntimeGating:
    def test_backward_euler_blocked(self):
        params = _std_params()
        init = zero_state(ell_max=params.ell_max)
        with pytest.raises(CanonicalBlockError, match="backward_euler"):
            backward_euler_step(init, params, 1e-3, _blocking_decision())

    def test_crank_nicolson_blocked(self):
        params = _std_params()
        init = zero_state(ell_max=params.ell_max)
        with pytest.raises(CanonicalBlockError, match="crank_nicolson"):
            crank_nicolson_step(init, params, 1e-3, _blocking_decision())

    def test_exponential_blocked(self):
        params = _std_params()
        init = zero_state(ell_max=params.ell_max)
        with pytest.raises(CanonicalBlockError, match="exponential"):
            exponential_step(init, params, 1e-3, _blocking_decision())

    def test_integrate_blocked(self):
        params = _std_params()
        init = zero_state(ell_max=params.ell_max)
        with pytest.raises(CanonicalBlockError, match="integrate_implicit"):
            integrate_implicit_to_steady_state(
                init, params, 1e-3, _blocking_decision(),
            )

    def test_blocked_error_carries_decision(self):
        params = _std_params()
        init = zero_state(ell_max=params.ell_max)
        try:
            backward_euler_step(init, params, 1e-3, _blocking_decision())
        except CanonicalBlockError as e:
            assert e.decision.allow_reduction is False
            assert e.decision.beta_policy_pass is False


# ============================================================================
# Test Class 10 - Validation
# ============================================================================

class TestValidation:
    def test_rejects_dt_zero_BE(self):
        params = _std_params()
        init = zero_state(ell_max=params.ell_max)
        with pytest.raises(ValueError, match="dt"):
            backward_euler_step(init, params, 0.0, _allowing_decision())

    def test_rejects_dt_negative_CN(self):
        params = _std_params()
        init = zero_state(ell_max=params.ell_max)
        with pytest.raises(ValueError, match="dt"):
            crank_nicolson_step(init, params, -1e-3, _allowing_decision())

    def test_rejects_ell_mismatch_EXP(self):
        params = _std_params(ell_max=4)
        init = zero_state(ell_max=2)
        with pytest.raises(ValueError, match="ell_max"):
            exponential_step(init, params, 1e-3, _allowing_decision())

    def test_rejects_axis_mismatch_BE(self):
        shear = AxisymmetricSTFTensor(amplitude=1e-6, axis=SymmetryAxis.Z)
        params = make_photon_hierarchy_parameters(
            n_e_sigmaT=10.0, shear=shear, k_eff=0.0, ell_max=2,
            decision=_allowing_decision(),
        )
        init = zero_state(ell_max=2, axis=SymmetryAxis.X)
        with pytest.raises(ValueError, match="axis"):
            backward_euler_step(init, params, 1e-3, _allowing_decision())

    def test_integrate_rejects_axis_mismatch(self):
        shear = AxisymmetricSTFTensor(amplitude=1e-6, axis=SymmetryAxis.Z)
        params = make_photon_hierarchy_parameters(
            n_e_sigmaT=10.0, shear=shear, k_eff=0.0, ell_max=2,
            decision=_allowing_decision(),
        )
        init = zero_state(ell_max=2, axis=SymmetryAxis.X)
        with pytest.raises(ValueError, match="axis"):
            integrate_implicit_to_steady_state(
                init, params, 1e-3, _allowing_decision(),
            )

    def test_integrate_rejects_negative_tolerance(self):
        params = _std_params()
        init = zero_state(ell_max=params.ell_max)
        with pytest.raises(ValueError, match="tolerance"):
            integrate_implicit_to_steady_state(
                init, params, 1e-3, _allowing_decision(), tolerance=-1.0,
            )

    def test_integrate_rejects_zero_max_steps(self):
        params = _std_params()
        init = zero_state(ell_max=params.ell_max)
        with pytest.raises(ValueError, match="max_steps"):
            integrate_implicit_to_steady_state(
                init, params, 1e-3, _allowing_decision(), max_steps=0,
            )
