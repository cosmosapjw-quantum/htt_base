"""
Test suite: bass/perturbation/baryon_fluid.py  (Week 6-01)
==========================================================

Test classes (7):
  1. TestBaryonFluidState              — container invariants
  2. TestZeroBaryonState               — factory helper
  3. TestBaryonParameters              — parameter validation + R_b formula
  4. TestMakeBaryonParameters          — factory derivation
  5. TestContinuityRHS                 — homogeneous limit δ̇_b = -3Φ̇
  6. TestEulerRHS                      — Thomson drag + expansion + sign
  7. TestBaryonStepForwardEuler        — combined step, free regime
  8. TestTightCouplingLimit            — τ̇→∞ ⇒ v_b → 3Θ_1
  9. TestMomentumConservationSign      — drag sign matches photon side
 10. TestRuntimeGatingW3               — all public entries gate

Target: ~40 tests.
"""
from __future__ import annotations

import math
import numpy as np
import pytest

from bass.perturbation.baryon_fluid import (
    BaryonFluidState,
    BaryonParameters,
    SymmetryAxis,
    baryon_continuity_rhs,
    baryon_euler_rhs,
    baryon_step,
    make_baryon_parameters,
    tight_coupling_residual,
    tight_coupling_v_b_steady_state,
    zero_baryon_state,
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


def _std_params(
    R_b: float = 0.6,
    tau_dot: float = 1e3,
    H: float = 30.0,
) -> BaryonParameters:
    return BaryonParameters(R_b=R_b, tau_dot=tau_dot, H=H)


# ============================================================================
# 1. TestBaryonFluidState
# ============================================================================

class TestBaryonFluidState:

    def test_construction_basic(self):
        s = BaryonFluidState(delta_b=0.01, v_b=1e-4)
        assert s.delta_b == 0.01
        assert s.v_b == 1e-4
        assert s.axis == SymmetryAxis.Z

    def test_construction_custom_axis(self):
        s = BaryonFluidState(delta_b=0.0, v_b=0.0, axis=SymmetryAxis.X)
        assert s.axis == SymmetryAxis.X

    def test_frozen_dataclass(self):
        s = BaryonFluidState(delta_b=0.0, v_b=0.0)
        with pytest.raises(Exception):
            s.delta_b = 1.0  # frozen

    def test_validates_finite_delta(self):
        with pytest.raises(ValueError, match="delta_b must be finite"):
            BaryonFluidState(delta_b=float("nan"), v_b=0.0)

    def test_validates_finite_v(self):
        with pytest.raises(ValueError, match="v_b must be finite"):
            BaryonFluidState(delta_b=0.0, v_b=float("inf"))

    def test_negative_delta_allowed(self):
        # Density contrast can be negative (underdensity)
        s = BaryonFluidState(delta_b=-0.001, v_b=0.0)
        assert s.delta_b == -0.001


# ============================================================================
# 2. TestZeroBaryonState
# ============================================================================

class TestZeroBaryonState:

    def test_zero_defaults(self):
        s = zero_baryon_state()
        assert s.delta_b == 0.0
        assert s.v_b == 0.0
        assert s.axis == SymmetryAxis.Z

    def test_zero_custom_axis(self):
        s = zero_baryon_state(axis=SymmetryAxis.Y)
        assert s.axis == SymmetryAxis.Y


# ============================================================================
# 3. TestBaryonParameters
# ============================================================================

class TestBaryonParameters:

    def test_construction_valid(self):
        p = BaryonParameters(R_b=0.6, tau_dot=1e3, H=30.0)
        assert p.R_b == 0.6
        assert p.tau_dot == 1e3
        assert p.H == 30.0
        assert p.sound_speed_sq == 0.0
        assert p.k_comoving == 0.0

    def test_R_b_must_be_positive(self):
        with pytest.raises(ValueError, match="R_b must be positive"):
            BaryonParameters(R_b=0.0, tau_dot=1e3, H=30.0)
        with pytest.raises(ValueError, match="R_b must be positive"):
            BaryonParameters(R_b=-0.1, tau_dot=1e3, H=30.0)

    def test_tau_dot_nonnegative(self):
        # Zero is allowed (free-streaming limit)
        p = BaryonParameters(R_b=0.6, tau_dot=0.0, H=30.0)
        assert p.tau_dot == 0.0
        with pytest.raises(ValueError, match="tau_dot must be non-negative"):
            BaryonParameters(R_b=0.6, tau_dot=-1.0, H=30.0)

    def test_H_nonnegative(self):
        # Zero H allowed (static universe limit for testing)
        p = BaryonParameters(R_b=0.6, tau_dot=1e3, H=0.0)
        assert p.H == 0.0
        with pytest.raises(ValueError, match="H must be non-negative"):
            BaryonParameters(R_b=0.6, tau_dot=1e3, H=-1.0)

    def test_nan_rejected(self):
        with pytest.raises(ValueError):
            BaryonParameters(R_b=float("nan"), tau_dot=1e3, H=30.0)

    def test_sound_speed_and_k_validation(self):
        p = BaryonParameters(
            R_b=0.6,
            tau_dot=1e3,
            H=30.0,
            sound_speed_sq=1.0e-9,
            k_comoving=0.05,
        )
        assert p.sound_speed_sq == 1.0e-9
        assert p.k_comoving == 0.05
        with pytest.raises(ValueError, match="sound_speed_sq"):
            BaryonParameters(R_b=0.6, tau_dot=1e3, H=30.0, sound_speed_sq=-1.0)
        with pytest.raises(ValueError, match="k_comoving"):
            BaryonParameters(R_b=0.6, tau_dot=1e3, H=30.0, k_comoving=-0.1)


# ============================================================================
# 4. TestMakeBaryonParameters
# ============================================================================

class TestMakeBaryonParameters:

    def test_R_b_formula(self):
        # R_b = 3 ρ_b / (4 ρ_γ). At ρ_b/ρ_γ = 4/3, R_b = 1.
        p = make_baryon_parameters(
            rho_b=4.0, rho_gamma=3.0,
            n_e_sigma_T=1e3, scale_factor=1e-3,
            H_conformal=30.0,
            decision=_allowing_decision(),
        )
        assert abs(p.R_b - 1.0) < 1e-14

    def test_tau_dot_formula(self):
        # τ̇ = a × (n_e σ_T)
        p = make_baryon_parameters(
            rho_b=1.0, rho_gamma=1.0,
            n_e_sigma_T=1e3, scale_factor=1e-3,
            H_conformal=30.0,
            decision=_allowing_decision(),
        )
        assert abs(p.tau_dot - 1.0) < 1e-14  # 1e-3 × 1e3

    def test_H_pass_through(self):
        p = make_baryon_parameters(
            rho_b=1.0, rho_gamma=1.0,
            n_e_sigma_T=1e3, scale_factor=1e-3,
            H_conformal=42.0,
            decision=_allowing_decision(),
        )
        assert p.H == 42.0

    def test_rejects_zero_rho_gamma(self):
        with pytest.raises(ValueError, match="rho_gamma must be positive"):
            make_baryon_parameters(
                rho_b=1.0, rho_gamma=0.0,
                n_e_sigma_T=1e3, scale_factor=1e-3,
                H_conformal=30.0,
                decision=_allowing_decision(),
            )

    def test_rejects_zero_rho_b(self):
        with pytest.raises(ValueError, match="rho_b must be positive"):
            make_baryon_parameters(
                rho_b=0.0, rho_gamma=1.0,
                n_e_sigma_T=1e3, scale_factor=1e-3,
                H_conformal=30.0,
                decision=_allowing_decision(),
            )

    def test_rejects_zero_scale_factor(self):
        with pytest.raises(ValueError, match="scale_factor must be positive"):
            make_baryon_parameters(
                rho_b=1.0, rho_gamma=1.0,
                n_e_sigma_T=1e3, scale_factor=0.0,
                H_conformal=30.0,
                decision=_allowing_decision(),
            )

    def test_blocking_decision_prevents_construction(self):
        with pytest.raises(CanonicalBlockError):
            make_baryon_parameters(
                rho_b=1.0, rho_gamma=1.0,
                n_e_sigma_T=1e3, scale_factor=1e-3,
                H_conformal=30.0,
                decision=_blocking_decision(),
            )


# ============================================================================
# 5. TestContinuityRHS
# ============================================================================

class TestContinuityRHS:

    def test_formula_exact(self):
        # δ̇_b = -3 Φ̇
        s = BaryonFluidState(delta_b=0.01, v_b=1e-4)
        phi_dot = 0.001
        result = baryon_continuity_rhs(s, phi_dot, _allowing_decision())
        assert abs(result - (-3.0 * 0.001)) < 1e-14

    def test_zero_phi_dot_gives_zero(self):
        s = BaryonFluidState(delta_b=0.01, v_b=1e-4)
        result = baryon_continuity_rhs(s, 0.0, _allowing_decision())
        assert result == 0.0

    def test_v_b_does_not_appear_in_homogeneous_limit(self):
        # δ̇_b formula should be independent of v_b in the homogeneous limit
        s1 = BaryonFluidState(delta_b=0.0, v_b=0.0)
        s2 = BaryonFluidState(delta_b=0.0, v_b=1e-3)
        r1 = baryon_continuity_rhs(s1, 1e-4, _allowing_decision())
        r2 = baryon_continuity_rhs(s2, 1e-4, _allowing_decision())
        assert r1 == r2

    def test_sign_reverses_with_phi_dot(self):
        s = BaryonFluidState(delta_b=0.0, v_b=0.0)
        r_pos = baryon_continuity_rhs(s, +1.0, _allowing_decision())
        r_neg = baryon_continuity_rhs(s, -1.0, _allowing_decision())
        assert r_pos == -r_neg

    def test_rejects_nonfinite_phi_dot(self):
        s = zero_baryon_state()
        with pytest.raises(ValueError, match="phi_dot must be finite"):
            baryon_continuity_rhs(
                s, float("nan"), _allowing_decision(),
            )


# ============================================================================
# 6. TestEulerRHS
# ============================================================================

class TestEulerRHS:

    def test_pure_expansion_no_Thomson(self):
        # At τ̇ = 0: v̇_b = -H v_b (pure expansion drag)
        s = BaryonFluidState(delta_b=0.0, v_b=1e-3)
        p = _std_params(tau_dot=0.0, H=30.0)
        result = baryon_euler_rhs(s, 0.0, p, _allowing_decision())
        expected = -30.0 * 1e-3
        assert abs(result - expected) < 1e-14

    def test_thomson_drag_zero_at_tight_coupling_state(self):
        # If v_b = 3 Θ_1 exactly, drag term vanishes: v̇_b = -H v_b
        theta_1 = 1e-4
        v_b = 3.0 * theta_1
        s = BaryonFluidState(delta_b=0.0, v_b=v_b)
        p = _std_params(tau_dot=1e10, H=30.0)  # huge τ̇
        result = baryon_euler_rhs(s, theta_1, p, _allowing_decision())
        expected = -p.H * v_b  # only expansion term survives
        assert abs(result - expected) < 1e-10

    def test_thomson_drag_sign_pushes_v_b_toward_3_theta(self):
        # If v_b < 3 Θ_1, drag should be positive (accelerate v_b up)
        theta_1 = 1e-3
        s = BaryonFluidState(delta_b=0.0, v_b=0.0)
        p = _std_params(tau_dot=1e3, H=0.0)  # H=0 isolates drag
        result = baryon_euler_rhs(s, theta_1, p, _allowing_decision())
        assert result > 0.0

    def test_thomson_drag_sign_pushes_v_b_down_if_above(self):
        # If v_b > 3 Θ_1, drag should be negative
        theta_1 = 1e-4
        s = BaryonFluidState(delta_b=0.0, v_b=1e-2)  # v_b > 3 Θ_1
        p = _std_params(tau_dot=1e3, H=0.0)
        result = baryon_euler_rhs(s, theta_1, p, _allowing_decision())
        assert result < 0.0

    def test_R_b_scales_drag_inversely(self):
        # Larger R_b ⇒ smaller drag amplitude
        theta_1 = 1e-3
        s = BaryonFluidState(delta_b=0.0, v_b=0.0)
        p_small_R = _std_params(R_b=0.1, tau_dot=1e3, H=0.0)
        p_large_R = _std_params(R_b=10.0, tau_dot=1e3, H=0.0)
        drag_small = baryon_euler_rhs(
            s, theta_1, p_small_R, _allowing_decision(),
        )
        drag_large = baryon_euler_rhs(
            s, theta_1, p_large_R, _allowing_decision(),
        )
        assert abs(drag_small) > abs(drag_large)
        # Ratio should be R_large / R_small = 100
        assert abs(drag_small / drag_large - 100.0) < 1e-10

    def test_rejects_nonfinite_theta_1(self):
        s = zero_baryon_state()
        p = _std_params()
        with pytest.raises(ValueError, match="theta_1_photon must be finite"):
            baryon_euler_rhs(
                s, float("nan"), p, _allowing_decision(),
            )

    def test_scalar_pressure_gradient_matches_mb95_velocity_convention(self):
        s = BaryonFluidState(delta_b=2.0e-4, v_b=0.0)
        p = BaryonParameters(
            R_b=0.6,
            tau_dot=0.0,
            H=0.0,
            sound_speed_sq=1.5e-9,
            k_comoving=0.05,
        )
        result = baryon_euler_rhs(s, 0.0, p, _allowing_decision())
        assert result == pytest.approx(p.sound_speed_sq * p.k_comoving * s.delta_b)


# ============================================================================
# 7. TestBaryonStepForwardEuler
# ============================================================================

class TestBaryonStepForwardEuler:

    def test_free_streaming_expansion_damps_v_b(self):
        # τ̇ = 0 ⇒ v_b decays as exp(-H η); single step drops it
        s = BaryonFluidState(delta_b=0.0, v_b=1.0)
        p = _std_params(tau_dot=0.0, H=1.0)
        dt = 0.01
        s_next = baryon_step(
            s, theta_1_photon=0.0, phi_dot=0.0,
            params=p, dt=dt, decision=_allowing_decision(),
        )
        # v_b_next = v_b - dt × H × v_b = v_b × (1 - dt H)
        expected_v = 1.0 * (1.0 - dt * 1.0)
        assert abs(s_next.v_b - expected_v) < 1e-14

    def test_phi_dot_drives_delta_b(self):
        s = zero_baryon_state()
        p = _std_params(tau_dot=0.0, H=0.0)
        dt = 0.01
        s_next = baryon_step(
            s, theta_1_photon=0.0, phi_dot=1e-3,
            params=p, dt=dt, decision=_allowing_decision(),
        )
        # δ_b_next = 0 + dt × (-3 × 1e-3)
        assert abs(s_next.delta_b - (-3e-5)) < 1e-18

    def test_axis_preserved(self):
        s = BaryonFluidState(delta_b=0.0, v_b=0.0, axis=SymmetryAxis.X)
        p = _std_params()
        s_next = baryon_step(
            s, theta_1_photon=1e-4, phi_dot=1e-4,
            params=p, dt=0.01, decision=_allowing_decision(),
        )
        assert s_next.axis == SymmetryAxis.X

    def test_rejects_nonpositive_dt(self):
        s = zero_baryon_state()
        p = _std_params()
        with pytest.raises(ValueError, match="dt must be positive"):
            baryon_step(
                s, theta_1_photon=0.0, phi_dot=0.0,
                params=p, dt=0.0,
                decision=_allowing_decision(),
            )
        with pytest.raises(ValueError, match="dt must be positive"):
            baryon_step(
                s, theta_1_photon=0.0, phi_dot=0.0,
                params=p, dt=-0.01,
                decision=_allowing_decision(),
            )


# ============================================================================
# 8. TestTightCouplingLimit
# ============================================================================

class TestTightCouplingLimit:

    def test_steady_state_approaches_3_theta_as_tau_grows(self):
        theta_1 = 1e-3
        H = 30.0
        # Increasing τ̇ / R_b should bring v_b → 3 Θ_1
        for tau_dot in [1e4, 1e6, 1e9]:
            p = BaryonParameters(R_b=0.6, tau_dot=tau_dot, H=H)
            v_b_ss = tight_coupling_v_b_steady_state(
                theta_1, p, _allowing_decision(),
            )
            target = 3.0 * theta_1
            # Relative error should shrink as τ̇ grows
            rel_err = abs(v_b_ss - target) / abs(target)
            expected_rel = p.H / (p.tau_dot / p.R_b)
            # Close to expected scaling
            assert rel_err < 2.0 * expected_rel + 1e-14

    def test_steady_state_at_infinity_exactly_3_theta(self):
        theta_1 = 1e-4
        # τ̇ huge: v_b → 3 Θ_1 to high precision
        p = BaryonParameters(R_b=0.6, tau_dot=1e15, H=30.0)
        v_b_ss = tight_coupling_v_b_steady_state(
            theta_1, p, _allowing_decision(),
        )
        assert abs(v_b_ss / (3.0 * theta_1) - 1.0) < 1e-13

    def test_zero_tau_dot_gives_zero_v_b(self):
        # No collision ⇒ only expansion drag; steady state is v_b = 0
        p = BaryonParameters(R_b=0.6, tau_dot=0.0, H=30.0)
        v_b_ss = tight_coupling_v_b_steady_state(
            1e-3, p, _allowing_decision(),
        )
        assert v_b_ss == 0.0

    def test_residual_zero_at_lock(self):
        theta_1 = 1e-4
        s = BaryonFluidState(delta_b=0.0, v_b=3.0 * theta_1)
        r = tight_coupling_residual(s, theta_1)
        assert abs(r) < 1e-14

    def test_residual_order_unity_when_decoupled(self):
        theta_1 = 1e-4
        s = BaryonFluidState(delta_b=0.0, v_b=0.0)
        r = tight_coupling_residual(s, theta_1)
        # (3 × 1e-4 - 0) / (3 × 1e-4) = 1
        assert abs(r - 1.0) < 1e-14

    def test_integration_locks_over_time(self):
        # Start decoupled, integrate, verify residual shrinks
        theta_1 = 1e-4
        s = BaryonFluidState(delta_b=0.0, v_b=0.0)
        p = _std_params(tau_dot=1e6, H=30.0)
        dt = 1e-7  # small dt for stability
        decision = _allowing_decision()
        r0 = abs(tight_coupling_residual(s, theta_1))
        for _ in range(1000):
            s = baryon_step(
                s, theta_1_photon=theta_1, phi_dot=0.0,
                params=p, dt=dt, decision=decision,
            )
        r_final = abs(tight_coupling_residual(s, theta_1))
        # Residual should shrink; after 1000 steps with stiff damping,
        # must be much smaller than initial
        assert r_final < 0.5 * r0


# ============================================================================
# 9. TestMomentumConservationSign
# ============================================================================

class TestMomentumConservationSign:
    """Verify the Thomson drag sign is consistent with momentum conservation.

    The baryon Euler drag is −(τ̇/R_b)(3 Θ_1 − v_b). The analogous photon
    dipole equation (W6-02 scope) will have equal-and-opposite +τ̇(v_b/3 −
    Θ_1). This test fixture only covers the baryon side, documenting the
    sign that W6-02 must match."""

    def test_drag_zero_at_momentum_equipartition(self):
        # When v_b = 3 Θ_1 (momentum equipartition in v_b=3Θ_1 convention),
        # no Thomson drag on either species.
        theta_1 = 1e-3
        s = BaryonFluidState(delta_b=0.0, v_b=3.0 * theta_1)
        p = _std_params(tau_dot=1e10, H=0.0)  # isolate drag; no expansion
        dot_v = baryon_euler_rhs(s, theta_1, p, _allowing_decision())
        assert abs(dot_v) < 1e-10  # only numerical roundoff

    def test_drag_drives_toward_lock_not_away(self):
        # If v_b starts below 3 Θ_1, drag must PUSH it UP (positive v̇_b).
        theta_1 = 1e-3
        s_below = BaryonFluidState(delta_b=0.0, v_b=0.0)
        s_above = BaryonFluidState(delta_b=0.0, v_b=1e-2)
        p = _std_params(tau_dot=1e3, H=0.0)
        dot_below = baryon_euler_rhs(
            s_below, theta_1, p, _allowing_decision(),
        )
        dot_above = baryon_euler_rhs(
            s_above, theta_1, p, _allowing_decision(),
        )
        assert dot_below > 0.0
        assert dot_above < 0.0


# ============================================================================
# 10. TestRuntimeGatingW3
# ============================================================================

class TestRuntimeGatingW3:
    """Verify every public entry gate via W3 CanonicalDecision."""

    def test_make_baryon_parameters_gates(self):
        with pytest.raises(CanonicalBlockError):
            make_baryon_parameters(
                rho_b=1.0, rho_gamma=1.0,
                n_e_sigma_T=1e3, scale_factor=1e-3,
                H_conformal=30.0,
                decision=_blocking_decision(),
            )

    def test_baryon_continuity_rhs_gates(self):
        s = zero_baryon_state()
        with pytest.raises(CanonicalBlockError):
            baryon_continuity_rhs(s, 0.0, _blocking_decision())

    def test_baryon_euler_rhs_gates(self):
        s = zero_baryon_state()
        p = _std_params()
        with pytest.raises(CanonicalBlockError):
            baryon_euler_rhs(s, 0.0, p, _blocking_decision())

    def test_baryon_step_gates(self):
        s = zero_baryon_state()
        p = _std_params()
        with pytest.raises(CanonicalBlockError):
            baryon_step(
                s, theta_1_photon=0.0, phi_dot=0.0,
                params=p, dt=0.01,
                decision=_blocking_decision(),
            )

    def test_tight_coupling_steady_state_gates(self):
        p = _std_params()
        with pytest.raises(CanonicalBlockError):
            tight_coupling_v_b_steady_state(
                0.0, p, _blocking_decision(),
            )

    def test_residual_is_pure_diagnostic_no_gate(self):
        # tight_coupling_residual has no decision parameter by design
        # (pure diagnostic). This test is a regression guard against
        # someone adding a gate and breaking the contract.
        import inspect
        from bass.perturbation.baryon_fluid import (
            tight_coupling_residual,
        )
        sig = inspect.signature(tight_coupling_residual)
        assert "decision" not in sig.parameters
