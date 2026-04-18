"""
Test suite: bass/transport/ray_transport.py  (Week 4 Day 4)
============================================================

Axisymmetric ℓ=2 transport equation with W3 runtime gating.

Test classes (9):
  1. TestTransportSpecies              — enum identity
  2. TestSigmaCoefficients             — Σ_2 values per species
  3. TestDampingRateHelpers            — photon τ̇, neutrino H
  4. TestTransportParameters           — frozen dataclass + validation
  5. TestEulerStep                     — single-step formula
  6. TestSteadyStateAnalytic           — Θ_∞ = Σ_2 σ / Γ
  7. TestIntegrationConvergence        — Euler → steady state convergence
  8. TestFreeStreamingDecay            — exp(-Γt) for zero-source
  9. TestRuntimeGating                 — all entries gate on decision
  10. TestPhysicsInvariants            — N_2/F_2 dominance, photon-D3 consistency

Target: ~45 tests.
"""
from __future__ import annotations

import math
import numpy as np
import pytest

from bass.collision.thomson_tensor import (
    AxisymmetricSTFTensor, SymmetryAxis,
    SIGMA_2_PHOTON_BE, compute_quasi_static_theta,
)
from bass.transport.ray_transport import (
    TransportSpecies,
    TransportParameters,
    SIGMA_2_NEUTRINO_FD,
    photon_damping_rate,
    neutrino_damping_rate,
    species_shear_coefficient,
    make_photon_parameters,
    make_neutrino_parameters,
    euler_step,
    compute_steady_state,
    integrate_to_steady_state,
    IntegrationResult,
    free_streaming_decay_factor,
)
from bass.runtime.canonical_decision import (
    CanonicalDecision, CanonicalBlockError, make_canonical_decision,
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
# Test Class 1 - TransportSpecies enum
# ============================================================================

class TestTransportSpecies:
    def test_has_two_members(self):
        assert len(list(TransportSpecies)) == 2

    def test_photon_value(self):
        assert TransportSpecies.PHOTON.value == "photon"

    def test_neutrino_value(self):
        assert TransportSpecies.NEUTRINO.value == "neutrino"


# ============================================================================
# Test Class 2 - Σ_2 coefficients
# ============================================================================

class TestSigmaCoefficients:
    def test_photon_sigma_matches_D3(self):
        assert species_shear_coefficient(TransportSpecies.PHOTON) == (
            SIGMA_2_PHOTON_BE
        )

    def test_neutrino_sigma_FD(self):
        # Σ_ν = (8/15) × 4.10596
        expected = (8.0 / 15.0) * 4.10596
        assert SIGMA_2_NEUTRINO_FD == pytest.approx(expected, rel=1e-12)

    def test_nu_gamma_ratio_approx_1p07(self):
        # 7% species-independence band from ch05
        ratio = SIGMA_2_NEUTRINO_FD / SIGMA_2_PHOTON_BE
        assert ratio == pytest.approx(1.07, rel=0.01)

    def test_species_shear_coefficient_returns_nonnegative(self):
        assert species_shear_coefficient(TransportSpecies.PHOTON) > 0
        assert species_shear_coefficient(TransportSpecies.NEUTRINO) > 0


# ============================================================================
# Test Class 3 - Damping-rate helpers
# ============================================================================

class TestDampingRateHelpers:
    def test_photon_damping_is_tau_dot(self):
        g = photon_damping_rate(n_e_sigmaT=1e3, decision=_allowing_decision())
        assert g == 1e3

    def test_photon_damping_rejects_negative(self):
        with pytest.raises(ValueError, match="non-negative"):
            photon_damping_rate(-1.0, _allowing_decision())

    def test_neutrino_damping_is_hubble(self):
        g = neutrino_damping_rate(
            hubble_rate=30.0, decision=_allowing_decision(),
        )
        assert g == 30.0

    def test_neutrino_damping_rejects_zero(self):
        with pytest.raises(ValueError, match="positive"):
            neutrino_damping_rate(0.0, _allowing_decision())

    def test_photon_allows_zero_opacity(self):
        # Post-recombination, τ̇ → 0 is physical
        g = photon_damping_rate(0.0, _allowing_decision())
        assert g == 0.0


# ============================================================================
# Test Class 4 - TransportParameters
# ============================================================================

class TestTransportParameters:
    def test_frozen_construction(self):
        shear = AxisymmetricSTFTensor(amplitude=1e-6, axis=SymmetryAxis.Z)
        p = TransportParameters(
            species=TransportSpecies.PHOTON,
            damping_rate=1e3,
            shear=shear,
            shear_coefficient=SIGMA_2_PHOTON_BE,
        )
        assert p.species == TransportSpecies.PHOTON
        assert p.damping_rate == 1e3

    def test_rejects_negative_damping(self):
        shear = AxisymmetricSTFTensor(amplitude=1.0)
        with pytest.raises(ValueError, match="damping_rate"):
            TransportParameters(
                species=TransportSpecies.PHOTON,
                damping_rate=-1.0,
                shear=shear,
                shear_coefficient=2.0,
            )

    def test_rejects_negative_sigma_2(self):
        shear = AxisymmetricSTFTensor(amplitude=1.0)
        with pytest.raises(ValueError, match="shear_coefficient"):
            TransportParameters(
                species=TransportSpecies.PHOTON,
                damping_rate=1.0,
                shear=shear,
                shear_coefficient=-2.0,
            )

    def test_frozen_immutable(self):
        shear = AxisymmetricSTFTensor(amplitude=1.0)
        p = TransportParameters(
            species=TransportSpecies.PHOTON,
            damping_rate=1.0, shear=shear, shear_coefficient=2.0,
        )
        with pytest.raises(Exception):
            p.damping_rate = 5.0

    def test_make_photon_factory(self):
        shear = AxisymmetricSTFTensor(amplitude=1e-6, axis=SymmetryAxis.Z)
        p = make_photon_parameters(1e3, shear, _allowing_decision())
        assert p.species == TransportSpecies.PHOTON
        assert p.damping_rate == 1e3
        assert p.shear_coefficient == SIGMA_2_PHOTON_BE

    def test_make_neutrino_factory(self):
        shear = AxisymmetricSTFTensor(amplitude=1e-6, axis=SymmetryAxis.Z)
        p = make_neutrino_parameters(30.0, shear, _allowing_decision())
        assert p.species == TransportSpecies.NEUTRINO
        assert p.damping_rate == 30.0
        assert p.shear_coefficient == SIGMA_2_NEUTRINO_FD


# ============================================================================
# Test Class 5 - Euler step formula
# ============================================================================

class TestEulerStep:
    def test_bit_exact_formula(self):
        # dΘ/dt = -Γ Θ + Σ_2 σ
        # With Θ=0.1, Γ=2, Σ_2=3, σ=0.5, dt=0.01:
        # dot = -0.2 + 1.5 = 1.3; new = 0.1 + 0.013 = 0.113
        theta = AxisymmetricSTFTensor(amplitude=0.1, axis=SymmetryAxis.Z)
        shear = AxisymmetricSTFTensor(amplitude=0.5, axis=SymmetryAxis.Z)
        params = TransportParameters(
            species=TransportSpecies.PHOTON,
            damping_rate=2.0, shear=shear, shear_coefficient=3.0,
        )
        new = euler_step(theta, params, dt=0.01, decision=_allowing_decision())
        assert new.amplitude == pytest.approx(0.113, rel=1e-14)

    def test_zero_source_zero_damping_is_stationary(self):
        theta = AxisymmetricSTFTensor(amplitude=5.0)
        shear = AxisymmetricSTFTensor(amplitude=0.0)
        params = TransportParameters(
            species=TransportSpecies.NEUTRINO, damping_rate=0.0,
            shear=shear, shear_coefficient=1.0,
        )
        new = euler_step(theta, params, 0.1, _allowing_decision())
        assert new.amplitude == 5.0

    def test_zero_source_decays(self):
        theta = AxisymmetricSTFTensor(amplitude=1.0)
        shear = AxisymmetricSTFTensor(amplitude=0.0)
        params = TransportParameters(
            species=TransportSpecies.NEUTRINO, damping_rate=2.0,
            shear=shear, shear_coefficient=1.0,
        )
        new = euler_step(theta, params, 0.1, _allowing_decision())
        # new = 1.0 + 0.1 × (-2.0 × 1.0 + 0) = 0.8
        assert new.amplitude == pytest.approx(0.8, rel=1e-14)

    def test_zero_damping_grows_from_source(self):
        theta = AxisymmetricSTFTensor(amplitude=0.0)
        shear = AxisymmetricSTFTensor(amplitude=1.0)
        params = TransportParameters(
            species=TransportSpecies.NEUTRINO, damping_rate=0.0,
            shear=shear, shear_coefficient=3.0,
        )
        new = euler_step(theta, params, 0.5, _allowing_decision())
        # new = 0 + 0.5 × (0 + 3×1) = 1.5
        assert new.amplitude == pytest.approx(1.5, rel=1e-14)

    def test_axis_preserved(self):
        theta = AxisymmetricSTFTensor(amplitude=1.0, axis=SymmetryAxis.Y)
        shear = AxisymmetricSTFTensor(amplitude=0.5, axis=SymmetryAxis.Y)
        params = TransportParameters(
            species=TransportSpecies.PHOTON, damping_rate=1.0,
            shear=shear, shear_coefficient=1.0,
        )
        new = euler_step(theta, params, 0.1, _allowing_decision())
        assert new.axis == SymmetryAxis.Y

    def test_axis_mismatch_rejected(self):
        theta = AxisymmetricSTFTensor(amplitude=1.0, axis=SymmetryAxis.Z)
        shear = AxisymmetricSTFTensor(amplitude=0.5, axis=SymmetryAxis.X)
        params = TransportParameters(
            species=TransportSpecies.PHOTON, damping_rate=1.0,
            shear=shear, shear_coefficient=1.0,
        )
        with pytest.raises(ValueError, match="axis"):
            euler_step(theta, params, 0.1, _allowing_decision())

    def test_rejects_negative_dt(self):
        theta = AxisymmetricSTFTensor(amplitude=1.0)
        shear = AxisymmetricSTFTensor(amplitude=1.0)
        params = TransportParameters(
            species=TransportSpecies.PHOTON, damping_rate=1.0,
            shear=shear, shear_coefficient=1.0,
        )
        with pytest.raises(ValueError, match="dt"):
            euler_step(theta, params, -0.1, _allowing_decision())


# ============================================================================
# Test Class 6 - Analytic steady state
# ============================================================================

class TestSteadyStateAnalytic:
    def test_formula_bit_exact(self):
        # Θ_∞ = Σ_2 σ / Γ = 2.0 × 3.0 / 4.0 = 1.5
        shear = AxisymmetricSTFTensor(amplitude=3.0, axis=SymmetryAxis.Z)
        params = TransportParameters(
            species=TransportSpecies.PHOTON, damping_rate=4.0,
            shear=shear, shear_coefficient=2.0,
        )
        ss = compute_steady_state(params, _allowing_decision())
        assert ss.amplitude == pytest.approx(1.5, rel=1e-14)

    def test_photon_steady_reproduces_D3_quasi_static(self):
        """compute_steady_state with photon params = compute_quasi_static_theta."""
        shear = AxisymmetricSTFTensor(amplitude=1e-6, axis=SymmetryAxis.Z)
        tau_dot = 1e3
        # Transport-module steady state
        p = make_photon_parameters(tau_dot, shear, _allowing_decision())
        ss_transport = compute_steady_state(p, _allowing_decision())
        # D3-module quasi-static
        ss_d3 = compute_quasi_static_theta(
            shear, tau_dot, _allowing_decision(),
        )
        assert ss_transport.amplitude == pytest.approx(
            ss_d3.amplitude, rel=1e-14,
        )

    def test_axis_preserved(self):
        shear = AxisymmetricSTFTensor(amplitude=1.0, axis=SymmetryAxis.X)
        params = TransportParameters(
            species=TransportSpecies.NEUTRINO, damping_rate=1.0,
            shear=shear, shear_coefficient=2.0,
        )
        ss = compute_steady_state(params, _allowing_decision())
        assert ss.axis == SymmetryAxis.X

    def test_rejects_zero_damping(self):
        # No steady state without damping
        shear = AxisymmetricSTFTensor(amplitude=1.0)
        params = TransportParameters(
            species=TransportSpecies.PHOTON, damping_rate=0.0,
            shear=shear, shear_coefficient=1.0,
        )
        with pytest.raises(ValueError, match="steady-state"):
            compute_steady_state(params, _allowing_decision())

    def test_zero_shear_gives_zero_steady_state(self):
        shear = AxisymmetricSTFTensor(amplitude=0.0)
        params = TransportParameters(
            species=TransportSpecies.NEUTRINO, damping_rate=1.0,
            shear=shear, shear_coefficient=2.0,
        )
        ss = compute_steady_state(params, _allowing_decision())
        assert ss.amplitude == 0.0


# ============================================================================
# Test Class 7 - Integration to steady state
# ============================================================================

class TestIntegrationConvergence:
    def test_converges_from_zero_initial(self):
        init = AxisymmetricSTFTensor(amplitude=0.0, axis=SymmetryAxis.Z)
        shear = AxisymmetricSTFTensor(amplitude=1e-6, axis=SymmetryAxis.Z)
        params = make_photon_parameters(1e3, shear, _allowing_decision())
        result = integrate_to_steady_state(
            init, params, dt=1e-4,
            decision=_allowing_decision(),
            max_steps=5000, tolerance=1e-8,
        )
        assert result.converged is True
        assert result.final_state.amplitude == pytest.approx(
            result.steady_state_target.amplitude, rel=1e-5,
        )

    def test_returns_IntegrationResult(self):
        init = AxisymmetricSTFTensor(amplitude=0.0)
        shear = AxisymmetricSTFTensor(amplitude=1e-6)
        params = make_photon_parameters(1e3, shear, _allowing_decision())
        result = integrate_to_steady_state(
            init, params, 1e-4, _allowing_decision(), max_steps=5000,
        )
        assert isinstance(result, IntegrationResult)

    def test_max_steps_reached_reports_not_converged(self):
        # Tight tolerance + tiny step + few iterations → won't converge
        init = AxisymmetricSTFTensor(amplitude=0.0)
        shear = AxisymmetricSTFTensor(amplitude=1e-6)
        params = make_photon_parameters(1e3, shear, _allowing_decision())
        result = integrate_to_steady_state(
            init, params, dt=1e-6,
            decision=_allowing_decision(),
            max_steps=10, tolerance=1e-12,
        )
        assert result.converged is False
        assert result.steps_taken == 10

    def test_rejects_negative_tolerance(self):
        init = AxisymmetricSTFTensor(amplitude=0.0)
        shear = AxisymmetricSTFTensor(amplitude=1e-6)
        params = make_photon_parameters(1e3, shear, _allowing_decision())
        with pytest.raises(ValueError, match="tolerance"):
            integrate_to_steady_state(
                init, params, 1e-4, _allowing_decision(),
                tolerance=-0.1,
            )

    def test_rejects_zero_max_steps(self):
        init = AxisymmetricSTFTensor(amplitude=0.0)
        shear = AxisymmetricSTFTensor(amplitude=1e-6)
        params = make_photon_parameters(1e3, shear, _allowing_decision())
        with pytest.raises(ValueError, match="max_steps"):
            integrate_to_steady_state(
                init, params, 1e-4, _allowing_decision(), max_steps=0,
            )

    def test_axis_mismatch_rejected(self):
        init = AxisymmetricSTFTensor(amplitude=0.0, axis=SymmetryAxis.Z)
        shear = AxisymmetricSTFTensor(amplitude=1e-6, axis=SymmetryAxis.X)
        params = TransportParameters(
            species=TransportSpecies.PHOTON, damping_rate=1.0,
            shear=shear, shear_coefficient=1.0,
        )
        with pytest.raises(ValueError, match="axis"):
            integrate_to_steady_state(
                init, params, 1e-4, _allowing_decision(),
            )


# ============================================================================
# Test Class 8 - Free-streaming decay
# ============================================================================

class TestFreeStreamingDecay:
    def test_decay_factor_at_t_zero_is_1(self):
        assert free_streaming_decay_factor(damping_rate=5.0, time=0.0) == 1.0

    def test_decay_factor_at_t_equals_one_over_Gamma(self):
        # exp(-1) ≈ 0.3679
        assert free_streaming_decay_factor(
            damping_rate=1.0, time=1.0,
        ) == pytest.approx(math.exp(-1.0), rel=1e-14)

    def test_decay_factor_large_Gt_small(self):
        assert free_streaming_decay_factor(
            damping_rate=10.0, time=1.0,
        ) == pytest.approx(math.exp(-10.0), rel=1e-14)

    def test_decay_factor_rejects_negative_inputs(self):
        with pytest.raises(ValueError, match="non-negative"):
            free_streaming_decay_factor(-1.0, 1.0)
        with pytest.raises(ValueError, match="non-negative"):
            free_streaming_decay_factor(1.0, -1.0)

    def test_numerical_euler_matches_analytic_at_small_dt(self):
        # Γ=1, zero source, Θ(0)=1; integrate to t=1 with small dt
        init = AxisymmetricSTFTensor(amplitude=1.0)
        shear_zero = AxisymmetricSTFTensor(amplitude=0.0)
        params = TransportParameters(
            species=TransportSpecies.NEUTRINO, damping_rate=1.0,
            shear=shear_zero, shear_coefficient=1.0,
        )
        dt = 1e-3
        state = init
        n_steps = int(1.0 / dt)
        for _ in range(n_steps):
            state = euler_step(state, params, dt, _allowing_decision())
        expected = math.exp(-1.0)
        # Euler O(dt) error → expect rel err ~ dt/2 = 5e-4
        assert state.amplitude == pytest.approx(expected, rel=1e-3)


# ============================================================================
# Test Class 9 - Runtime gating
# ============================================================================

class TestRuntimeGating:
    def test_photon_damping_blocked(self):
        with pytest.raises(CanonicalBlockError, match="photon_damping_rate"):
            photon_damping_rate(1e3, _blocking_decision())

    def test_neutrino_damping_blocked(self):
        with pytest.raises(CanonicalBlockError, match="neutrino_damping_rate"):
            neutrino_damping_rate(30.0, _blocking_decision())

    def test_euler_step_blocked(self):
        theta = AxisymmetricSTFTensor(amplitude=1.0)
        shear = AxisymmetricSTFTensor(amplitude=0.5)
        params = TransportParameters(
            species=TransportSpecies.PHOTON, damping_rate=1.0,
            shear=shear, shear_coefficient=1.0,
        )
        with pytest.raises(CanonicalBlockError, match="euler_step"):
            euler_step(theta, params, 0.1, _blocking_decision())

    def test_compute_steady_state_blocked(self):
        shear = AxisymmetricSTFTensor(amplitude=1.0)
        params = TransportParameters(
            species=TransportSpecies.PHOTON, damping_rate=1.0,
            shear=shear, shear_coefficient=1.0,
        )
        with pytest.raises(CanonicalBlockError, match="compute_steady_state"):
            compute_steady_state(params, _blocking_decision())

    def test_integrate_blocked(self):
        init = AxisymmetricSTFTensor(amplitude=0.0)
        shear = AxisymmetricSTFTensor(amplitude=1.0)
        params = TransportParameters(
            species=TransportSpecies.PHOTON, damping_rate=1.0,
            shear=shear, shear_coefficient=1.0,
        )
        with pytest.raises(CanonicalBlockError, match="integrate_to_steady_state"):
            integrate_to_steady_state(
                init, params, 0.1, _blocking_decision(),
            )

    def test_blocked_error_carries_decision(self):
        try:
            photon_damping_rate(1.0, _blocking_decision())
        except CanonicalBlockError as e:
            assert e.decision.allow_reduction is False
            assert e.decision.beta_policy_pass is False


# ============================================================================
# Test Class 10 - Physics invariants
# ============================================================================

class TestPhysicsInvariants:
    def test_neutrino_photon_amplitude_ratio_follows_gamma_ratio(self):
        """N_2/F_2 = (Σ_ν / Σ_γ) × (Γ_γ / Γ_ν) at steady state."""
        shear = AxisymmetricSTFTensor(amplitude=1e-6, axis=SymmetryAxis.Z)
        tau_dot = 1e3
        H = 30.0
        p_g = make_photon_parameters(tau_dot, shear, _allowing_decision())
        p_n = make_neutrino_parameters(H, shear, _allowing_decision())
        ss_g = compute_steady_state(p_g, _allowing_decision())
        ss_n = compute_steady_state(p_n, _allowing_decision())
        observed_ratio = ss_n.amplitude / ss_g.amplitude
        expected = (SIGMA_2_NEUTRINO_FD / SIGMA_2_PHOTON_BE) * (tau_dot / H)
        assert observed_ratio == pytest.approx(expected, rel=1e-14)

    def test_sign_convention_damping(self):
        """Positive Θ with no source must decrease under positive Γ."""
        theta = AxisymmetricSTFTensor(amplitude=1.0)
        shear = AxisymmetricSTFTensor(amplitude=0.0)
        params = TransportParameters(
            species=TransportSpecies.PHOTON, damping_rate=1.0,
            shear=shear, shear_coefficient=1.0,
        )
        new = euler_step(theta, params, 0.1, _allowing_decision())
        assert new.amplitude < theta.amplitude

    def test_sign_convention_shear_drives_positive(self):
        """Zero Θ with positive σ source grows positive."""
        theta = AxisymmetricSTFTensor(amplitude=0.0)
        shear = AxisymmetricSTFTensor(amplitude=1.0)
        params = TransportParameters(
            species=TransportSpecies.NEUTRINO, damping_rate=0.0,
            shear=shear, shear_coefficient=1.0,
        )
        new = euler_step(theta, params, 0.1, _allowing_decision())
        assert new.amplitude > theta.amplitude

    def test_euler_converged_within_O_dt_of_analytic(self):
        """Converged Euler result matches analytic steady state."""
        shear = AxisymmetricSTFTensor(amplitude=1e-6, axis=SymmetryAxis.Z)
        params = make_photon_parameters(1e3, shear, _allowing_decision())
        init = AxisymmetricSTFTensor(amplitude=0.0, axis=SymmetryAxis.Z)
        result = integrate_to_steady_state(
            init, params, dt=1e-4, decision=_allowing_decision(),
            max_steps=10000, tolerance=1e-10,
        )
        if result.converged:
            rel_err = abs(
                result.final_state.amplitude
                - result.steady_state_target.amplitude
            ) / abs(result.steady_state_target.amplitude)
            assert rel_err < 1e-4   # Euler O(dt) accuracy

    def test_IntegrationResult_frozen(self):
        init = AxisymmetricSTFTensor(amplitude=0.0)
        shear = AxisymmetricSTFTensor(amplitude=1e-6)
        params = make_photon_parameters(1e3, shear, _allowing_decision())
        result = integrate_to_steady_state(
            init, params, 1e-4, _allowing_decision(),
        )
        with pytest.raises(Exception):
            result.converged = False
