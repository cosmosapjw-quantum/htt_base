"""
Test suite: bass/perturbation/cdm_fluid.py  (Week 6-03)
=======================================================

Test classes:
  1. TestCDMFluidState           — container invariants
  2. TestZeroCDMState            — factory
  3. TestCDMParameters           — H validation
  4. TestMakeCDMParameters       — factory with W3 gating
  5. TestCDMContinuityRHS        — δ̇_c = −3Φ̇
  6. TestCDMEulerRHS             — v̇_c = −H v_c (no collision)
  7. TestCDMStepForwardEuler     — combined step
  8. TestAnalyticDecay           — expansion damping matches exp(-Hη)
  9. TestDifferentiationFromBaryon — CDM has no Thomson drag
 10. TestCDMIsCollisionlessIdentity — regression guard
 11. TestRuntimeGatingW3         — all public entries gate
"""
from __future__ import annotations

import math
import numpy as np
import pytest

from bass.perturbation.cdm_fluid import (
    CDMFluidState,
    CDMParameters,
    cdm_continuity_rhs,
    cdm_euler_rhs,
    cdm_is_collisionless,
    cdm_step,
    cdm_v_c_analytic_decay,
    make_cdm_parameters,
    zero_cdm_state,
)
from bass.perturbation.baryon_fluid import SymmetryAxis
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


# ============================================================================
# 1. TestCDMFluidState
# ============================================================================

class TestCDMFluidState:

    def test_construction_basic(self):
        s = CDMFluidState(delta_c=0.02, v_c=5e-5)
        assert s.delta_c == 0.02
        assert s.v_c == 5e-5
        assert s.axis == SymmetryAxis.Z

    def test_frozen(self):
        s = CDMFluidState(delta_c=0.0, v_c=0.0)
        with pytest.raises(Exception):
            s.delta_c = 1.0

    def test_validates_finite_delta(self):
        with pytest.raises(ValueError, match="delta_c must be finite"):
            CDMFluidState(delta_c=float("nan"), v_c=0.0)

    def test_validates_finite_v(self):
        with pytest.raises(ValueError, match="v_c must be finite"):
            CDMFluidState(delta_c=0.0, v_c=float("inf"))

    def test_custom_axis(self):
        s = CDMFluidState(delta_c=0.0, v_c=0.0, axis=SymmetryAxis.X)
        assert s.axis == SymmetryAxis.X


# ============================================================================
# 2. TestZeroCDMState
# ============================================================================

class TestZeroCDMState:

    def test_zero_defaults(self):
        s = zero_cdm_state()
        assert s.delta_c == 0.0
        assert s.v_c == 0.0
        assert s.axis == SymmetryAxis.Z


# ============================================================================
# 3. TestCDMParameters
# ============================================================================

class TestCDMParameters:

    def test_construction_valid(self):
        p = CDMParameters(H=30.0)
        assert p.H == 30.0

    def test_H_zero_allowed(self):
        p = CDMParameters(H=0.0)
        assert p.H == 0.0

    def test_H_negative_rejected(self):
        with pytest.raises(ValueError, match="H must be non-negative"):
            CDMParameters(H=-1.0)

    def test_H_nan_rejected(self):
        with pytest.raises(ValueError, match="H must be non-negative"):
            CDMParameters(H=float("nan"))


# ============================================================================
# 4. TestMakeCDMParameters
# ============================================================================

class TestMakeCDMParameters:

    def test_factory_valid(self):
        p = make_cdm_parameters(30.0, _allowing_decision())
        assert p.H == 30.0

    def test_blocking_decision_rejected(self):
        with pytest.raises(CanonicalBlockError):
            make_cdm_parameters(30.0, _blocking_decision())


# ============================================================================
# 5. TestCDMContinuityRHS
# ============================================================================

class TestCDMContinuityRHS:

    def test_formula_exact(self):
        s = CDMFluidState(delta_c=0.01, v_c=1e-4)
        r = cdm_continuity_rhs(s, 0.002, _allowing_decision())
        assert abs(r - (-3.0 * 0.002)) < 1e-14

    def test_v_c_irrelevant_in_homogeneous_limit(self):
        s1 = CDMFluidState(delta_c=0.0, v_c=0.0)
        s2 = CDMFluidState(delta_c=0.0, v_c=1e-3)
        r1 = cdm_continuity_rhs(s1, 1e-4, _allowing_decision())
        r2 = cdm_continuity_rhs(s2, 1e-4, _allowing_decision())
        assert r1 == r2

    def test_zero_phi_dot_zero_result(self):
        s = zero_cdm_state()
        r = cdm_continuity_rhs(s, 0.0, _allowing_decision())
        assert r == 0.0

    def test_rejects_nonfinite_phi_dot(self):
        s = zero_cdm_state()
        with pytest.raises(ValueError, match="phi_dot must be finite"):
            cdm_continuity_rhs(s, float("nan"), _allowing_decision())


# ============================================================================
# 6. TestCDMEulerRHS
# ============================================================================

class TestCDMEulerRHS:

    def test_pure_expansion_damping(self):
        # v̇_c = −H v_c
        s = CDMFluidState(delta_c=0.0, v_c=1e-3)
        p = CDMParameters(H=30.0)
        r = cdm_euler_rhs(s, p, _allowing_decision())
        assert abs(r - (-30.0 * 1e-3)) < 1e-14

    def test_zero_v_c_zero_rhs(self):
        s = zero_cdm_state()
        p = CDMParameters(H=30.0)
        r = cdm_euler_rhs(s, p, _allowing_decision())
        assert r == 0.0

    def test_zero_H_zero_rhs(self):
        # Static universe: no expansion damping
        s = CDMFluidState(delta_c=0.0, v_c=1e-3)
        p = CDMParameters(H=0.0)
        r = cdm_euler_rhs(s, p, _allowing_decision())
        assert r == 0.0

    def test_delta_c_irrelevant_in_euler(self):
        # δ_c does not appear in v̇_c
        s1 = CDMFluidState(delta_c=0.0, v_c=1e-3)
        s2 = CDMFluidState(delta_c=0.1, v_c=1e-3)
        p = CDMParameters(H=30.0)
        r1 = cdm_euler_rhs(s1, p, _allowing_decision())
        r2 = cdm_euler_rhs(s2, p, _allowing_decision())
        assert r1 == r2


# ============================================================================
# 7. TestCDMStepForwardEuler
# ============================================================================

class TestCDMStepForwardEuler:

    def test_step_advances_state(self):
        s = CDMFluidState(delta_c=0.0, v_c=1.0)
        p = CDMParameters(H=1.0)
        dt = 0.01
        s_next = cdm_step(
            s, phi_dot=0.0, params=p, dt=dt,
            decision=_allowing_decision(),
        )
        # v_c_next = v_c × (1 − dt H)
        assert abs(s_next.v_c - (1.0 - dt * 1.0)) < 1e-14
        # δ_c unchanged since phi_dot = 0
        assert s_next.delta_c == 0.0

    def test_phi_dot_drives_delta(self):
        s = zero_cdm_state()
        p = CDMParameters(H=0.0)
        dt = 0.01
        s_next = cdm_step(
            s, phi_dot=1e-3, params=p, dt=dt,
            decision=_allowing_decision(),
        )
        assert abs(s_next.delta_c - (-3e-5)) < 1e-18

    def test_axis_preserved(self):
        s = CDMFluidState(delta_c=0.0, v_c=0.0, axis=SymmetryAxis.X)
        p = CDMParameters(H=1.0)
        s_next = cdm_step(
            s, phi_dot=1e-4, params=p, dt=0.01,
            decision=_allowing_decision(),
        )
        assert s_next.axis == SymmetryAxis.X

    def test_rejects_nonpositive_dt(self):
        s = zero_cdm_state()
        p = CDMParameters(H=1.0)
        with pytest.raises(ValueError, match="dt must be positive"):
            cdm_step(
                s, phi_dot=0.0, params=p, dt=0.0,
                decision=_allowing_decision(),
            )
        with pytest.raises(ValueError, match="dt must be positive"):
            cdm_step(
                s, phi_dot=0.0, params=p, dt=-0.01,
                decision=_allowing_decision(),
            )


# ============================================================================
# 8. TestAnalyticDecay
# ============================================================================

class TestAnalyticDecay:

    def test_analytic_formula_pure(self):
        p = CDMParameters(H=1.0)
        v0 = 2.0
        d_eta = 1.0
        result = cdm_v_c_analytic_decay(v0, p, d_eta)
        expected = v0 * math.exp(-p.H * d_eta)
        assert abs(result - expected) < 1e-14

    def test_zero_H_no_decay(self):
        p = CDMParameters(H=0.0)
        v0 = 1.0
        result = cdm_v_c_analytic_decay(v0, p, 10.0)
        assert result == v0

    def test_forward_euler_converges_to_analytic(self):
        # Integrate many small steps and compare to analytic decay.
        v0 = 1.0
        total_eta = 2.0
        n_steps = 1000
        dt = total_eta / n_steps
        p = CDMParameters(H=1.0)

        s = CDMFluidState(delta_c=0.0, v_c=v0)
        for _ in range(n_steps):
            s = cdm_step(
                s, phi_dot=0.0, params=p, dt=dt,
                decision=_allowing_decision(),
            )
        analytic = cdm_v_c_analytic_decay(v0, p, total_eta)
        # Euler rel error ~ n(H dt)²/2 = 1000 × (0.002)² / 2 = 2e-3.
        # Use 5e-3 tolerance as safety margin for the O(dt) behavior.
        assert abs(s.v_c - analytic) / abs(analytic) < 5e-3

    def test_zero_initial_zero_result(self):
        p = CDMParameters(H=1.0)
        result = cdm_v_c_analytic_decay(0.0, p, 1.0)
        assert result == 0.0


# ============================================================================
# 9. TestDifferentiationFromBaryon
# ============================================================================

class TestDifferentiationFromBaryon:
    """Verify that CDM has no Thomson-like drag coupling.

    Physically, CDM is collisionless so its velocity cannot be
    "dragged" by photons or any other species at first order. These
    tests serve as regression guards against accidentally introducing
    such a coupling."""

    def test_no_parameter_for_coupling(self):
        # CDMParameters should NOT expose a tau_dot, R_b, or v_photon
        import inspect
        from bass.perturbation.cdm_fluid import CDMParameters as P
        fields = list(P.__dataclass_fields__.keys())
        assert "tau_dot" not in fields
        assert "R_b" not in fields
        assert "v_photon" not in fields
        # Only H should be present
        assert fields == ["H"]

    def test_euler_does_not_accept_external_velocity(self):
        # cdm_euler_rhs signature must not have any "external velocity"
        # parameter (unlike baryon_euler_rhs which takes theta_1_photon).
        import inspect
        sig = inspect.signature(cdm_euler_rhs)
        params = list(sig.parameters.keys())
        # Expect: state, params, decision
        assert params == ["state", "params", "decision"]

    def test_v_c_independent_of_hypothetical_theta_1(self):
        # Regression check: changing any external "photon dipole" context
        # must NOT affect cdm_euler_rhs. We test this by computing v̇_c
        # with the same state/params twice — no other parameter exists
        # to vary.
        s = CDMFluidState(delta_c=0.0, v_c=1e-3)
        p = CDMParameters(H=30.0)
        r1 = cdm_euler_rhs(s, p, _allowing_decision())
        r2 = cdm_euler_rhs(s, p, _allowing_decision())
        assert r1 == r2


# ============================================================================
# 10. TestCDMIsCollisionlessIdentity
# ============================================================================

class TestCDMIsCollisionlessIdentity:

    def test_identity_returns_true(self):
        s = zero_cdm_state()
        assert cdm_is_collisionless(s) is True

    def test_identity_regardless_of_state(self):
        s = CDMFluidState(delta_c=1.0, v_c=1.0)
        assert cdm_is_collisionless(s) is True


# ============================================================================
# 11. TestRuntimeGatingW3
# ============================================================================

class TestRuntimeGatingW3:

    def test_make_cdm_parameters_gates(self):
        with pytest.raises(CanonicalBlockError):
            make_cdm_parameters(30.0, _blocking_decision())

    def test_cdm_continuity_rhs_gates(self):
        s = zero_cdm_state()
        with pytest.raises(CanonicalBlockError):
            cdm_continuity_rhs(s, 0.0, _blocking_decision())

    def test_cdm_euler_rhs_gates(self):
        s = zero_cdm_state()
        p = CDMParameters(H=1.0)
        with pytest.raises(CanonicalBlockError):
            cdm_euler_rhs(s, p, _blocking_decision())

    def test_cdm_step_gates(self):
        s = zero_cdm_state()
        p = CDMParameters(H=1.0)
        with pytest.raises(CanonicalBlockError):
            cdm_step(
                s, phi_dot=0.0, params=p, dt=0.01,
                decision=_blocking_decision(),
            )

    def test_diagnostics_have_no_gate(self):
        import inspect
        for fn in [cdm_v_c_analytic_decay, cdm_is_collisionless]:
            sig = inspect.signature(fn)
            assert "decision" not in sig.parameters, (
                f"{fn.__name__} should not have a decision parameter"
            )
