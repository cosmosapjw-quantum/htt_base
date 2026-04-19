"""
Test suite: bass/collision/thomson_tensor.py  (Week 4 Day 3)
==============================================================

Axisymmetric photon Thomson collision skeleton with W3 runtime gating.

Test classes (8):
  1. TestPhotonSigma2Coefficient    — Σ^(γ)_2 ≈ 2.044
  2. TestAxisymmetricSTFTensor      — data type + matrix structure
  3. TestSTFTensorArithmetic        — add, scale, axis matching
  4. TestPhotonThomsonCollision     — core formula C = -τ̇(Θ - Π/10)
  5. TestPolarizationSourceSTF      — Π^STF = Θ + E (E₀ h/3 drops)
  6. TestQuasiStaticLimit           — Θ = Σ_2/τ̇ × σ
  7. TestEModeThomsonSource         — Ė = -(2/5) τ̇ c_ξ T
  8. TestRuntimeGating              — every entry point calls require_allow_reduction

Target: ~40 tests.
"""
from __future__ import annotations

import math
import numpy as np
import pytest
from scipy.special import zeta

from bass.collision.thomson_tensor import (
    SIGMA_2_PHOTON_BE,
    THOMSON_POLARIZATION_COEFF,
    E_MODE_THOMSON_COEFF,
    QUASI_STATIC_TAU_H_THRESHOLD,
    SymmetryAxis,
    AxisymmetricSTFTensor,
    ThomsonCollisionResult,
    compute_photon_thomson_collision,
    compute_quasi_static_theta,
    compute_e_mode_thomson_source,
    verify_quasi_static_regime,
    photon_Sigma_2_coefficient,
)
from bass.runtime.canonical_decision import (
    CanonicalDecision,
    CanonicalBlockError,
    make_canonical_decision,
)
from tsc.diagnostics.tangency import compute_D_diagnostic, TangentKind


# ============================================================================
# Fixtures - CanonicalDecision builders
# ============================================================================

def _on_manifold_G(x):
    return np.asarray(x, dtype=float)


def _allowing_decision() -> CanonicalDecision:
    """Build a CanonicalDecision where allow_reduction=True."""
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
    """Build a CanonicalDecision where allow_reduction=False (beta fails)."""
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
# Test Class 1 - Σ^(γ)_2 coefficient
# ============================================================================

class TestPhotonSigma2Coefficient:
    """The shear source coefficient for BE radiation, η=0."""

    def test_matches_closed_form(self):
        # Σ_2 = (8/15) × 24 ζ(5) / (π⁴/15)
        expected = (8.0 / 15.0) * 24.0 * float(zeta(5)) / (math.pi ** 4 / 15.0)
        assert SIGMA_2_PHOTON_BE == pytest.approx(expected, rel=1e-14)

    def test_numeric_value_matches_memory(self):
        # Memory / ch05 reference: ≈ 2.044
        assert SIGMA_2_PHOTON_BE == pytest.approx(2.044, rel=0.01)

    def test_public_accessor_returns_same_value(self):
        assert photon_Sigma_2_coefficient() == SIGMA_2_PHOTON_BE

    def test_matches_8_over_15_times_ratio(self):
        ratio = 24.0 * float(zeta(5)) / (math.pi ** 4 / 15.0)
        assert SIGMA_2_PHOTON_BE == pytest.approx(
            (8.0 / 15.0) * ratio, rel=1e-14,
        )

    def test_thomson_polarization_coeff_is_one_tenth(self):
        assert THOMSON_POLARIZATION_COEFF == pytest.approx(1.0 / 10.0, abs=1e-15)

    def test_e_mode_thomson_coeff_is_two_fifths(self):
        assert E_MODE_THOMSON_COEFF == pytest.approx(2.0 / 5.0, abs=1e-15)


# ============================================================================
# Test Class 2 - AxisymmetricSTFTensor structure
# ============================================================================

class TestAxisymmetricSTFTensor:
    """Single-DOF STF tensor, matrix form, invariants."""

    def test_z_axis_matrix_structure(self):
        t = AxisymmetricSTFTensor(amplitude=1.0, axis=SymmetryAxis.Z)
        M = t.to_matrix()
        # Expected diag: (-0.5, -0.5, +1.0)
        assert M[0, 0] == pytest.approx(-0.5, rel=1e-14)
        assert M[1, 1] == pytest.approx(-0.5, rel=1e-14)
        assert M[2, 2] == pytest.approx(+1.0, rel=1e-14)

    def test_x_axis_matrix_structure(self):
        t = AxisymmetricSTFTensor(amplitude=2.0, axis=SymmetryAxis.X)
        M = t.to_matrix()
        # Expected diag: (+2.0, -1.0, -1.0)
        assert M[0, 0] == pytest.approx(+2.0, rel=1e-14)
        assert M[1, 1] == pytest.approx(-1.0, rel=1e-14)
        assert M[2, 2] == pytest.approx(-1.0, rel=1e-14)

    def test_is_trace_free(self):
        for axis in (SymmetryAxis.X, SymmetryAxis.Y, SymmetryAxis.Z):
            for amp in (0.0, 1.0, -2.5, 1e-6):
                t = AxisymmetricSTFTensor(amplitude=amp, axis=axis)
                assert t.trace() == pytest.approx(0.0, abs=1e-14)

    def test_off_diagonal_is_zero(self):
        t = AxisymmetricSTFTensor(amplitude=3.5, axis=SymmetryAxis.Z)
        M = t.to_matrix()
        for i in range(3):
            for j in range(3):
                if i != j:
                    assert M[i, j] == pytest.approx(0.0, abs=1e-14)

    def test_zero_amplitude_gives_zero_tensor(self):
        t = AxisymmetricSTFTensor(amplitude=0.0, axis=SymmetryAxis.Z)
        assert np.allclose(t.to_matrix(), 0.0)

    def test_dataclass_is_frozen(self):
        t = AxisymmetricSTFTensor(amplitude=1.0, axis=SymmetryAxis.Z)
        with pytest.raises(Exception):
            t.amplitude = 2.0


# ============================================================================
# Test Class 3 - STF tensor arithmetic
# ============================================================================

class TestSTFTensorArithmetic:
    """Scale / add operations preserve axis and STF property."""

    def test_scale_preserves_axis(self):
        t = AxisymmetricSTFTensor(amplitude=1.0, axis=SymmetryAxis.Z)
        t2 = t.scale(3.5)
        assert t2.amplitude == pytest.approx(3.5, rel=1e-14)
        assert t2.axis == SymmetryAxis.Z

    def test_scale_by_zero_gives_zero_amplitude(self):
        t = AxisymmetricSTFTensor(amplitude=7.2, axis=SymmetryAxis.X)
        assert t.scale(0.0).amplitude == 0.0

    def test_add_same_axis(self):
        a = AxisymmetricSTFTensor(amplitude=2.0, axis=SymmetryAxis.Z)
        b = AxisymmetricSTFTensor(amplitude=3.0, axis=SymmetryAxis.Z)
        c = a.add(b)
        assert c.amplitude == pytest.approx(5.0, rel=1e-14)
        assert c.axis == SymmetryAxis.Z

    def test_add_different_axes_rejected(self):
        a = AxisymmetricSTFTensor(amplitude=1.0, axis=SymmetryAxis.Z)
        b = AxisymmetricSTFTensor(amplitude=1.0, axis=SymmetryAxis.X)
        with pytest.raises(ValueError, match="different axes"):
            a.add(b)

    def test_sum_remains_STF(self):
        a = AxisymmetricSTFTensor(amplitude=1.5, axis=SymmetryAxis.Y)
        b = AxisymmetricSTFTensor(amplitude=-0.7, axis=SymmetryAxis.Y)
        c = a.add(b)
        assert c.trace() == pytest.approx(0.0, abs=1e-14)


# ============================================================================
# Test Class 4 - Photon Thomson collision core formula
# ============================================================================

class TestPhotonThomsonCollision:
    """C^(γ)_ab = -τ̇ (Θ_ab - Π^STF_ab / 10)."""

    def test_formula_reproduces_smoke_example(self):
        # Smoke: Θ=1e-5, E=2e-6, τ̇=1e3
        # Π_STF = 1e-5 + 2e-6 = 1.2e-5
        # C = -1e3 × (1e-5 - 1.2e-6) = -8.8e-3
        theta = AxisymmetricSTFTensor(amplitude=1e-5, axis=SymmetryAxis.Z)
        E = AxisymmetricSTFTensor(amplitude=2e-6, axis=SymmetryAxis.Z)
        result = compute_photon_thomson_collision(
            theta_gamma=theta, E_gamma=E, n_e_sigmaT=1e3,
            decision=_allowing_decision(),
        )
        assert result.collision.amplitude == pytest.approx(-8.8e-3, rel=1e-14)

    def test_returns_ThomsonCollisionResult(self):
        result = compute_photon_thomson_collision(
            theta_gamma=AxisymmetricSTFTensor(1e-5),
            E_gamma=AxisymmetricSTFTensor(0.0),
            n_e_sigmaT=1.0,
            decision=_allowing_decision(),
        )
        assert isinstance(result, ThomsonCollisionResult)

    def test_zero_opacity_gives_zero_collision(self):
        result = compute_photon_thomson_collision(
            theta_gamma=AxisymmetricSTFTensor(1.0),
            E_gamma=AxisymmetricSTFTensor(0.5),
            n_e_sigmaT=0.0,
            decision=_allowing_decision(),
        )
        assert result.collision.amplitude == 0.0

    def test_equal_theta_and_E_not_self_cancel(self):
        # With Θ=1, E=1, Π_STF=2, C = -τ̇(1 - 0.2) = -0.8 τ̇
        result = compute_photon_thomson_collision(
            theta_gamma=AxisymmetricSTFTensor(1.0),
            E_gamma=AxisymmetricSTFTensor(1.0),
            n_e_sigmaT=1.0,
            decision=_allowing_decision(),
        )
        assert result.collision.amplitude == pytest.approx(-0.8, rel=1e-14)

    def test_collision_vanishes_when_theta_equals_pi_over_10(self):
        """If Θ = Π/10 (fine-tuned), the collision vanishes."""
        # Set E = 9Θ so Π = 10Θ, then C = -τ̇(Θ - 10Θ/10) = 0
        theta = AxisymmetricSTFTensor(amplitude=0.1, axis=SymmetryAxis.Z)
        E = AxisymmetricSTFTensor(amplitude=0.9, axis=SymmetryAxis.Z)
        result = compute_photon_thomson_collision(
            theta_gamma=theta, E_gamma=E, n_e_sigmaT=1e3,
            decision=_allowing_decision(),
        )
        assert result.collision.amplitude == pytest.approx(0.0, abs=1e-14)

    def test_opacity_scales_collision_linearly(self):
        r1 = compute_photon_thomson_collision(
            theta_gamma=AxisymmetricSTFTensor(1e-5),
            E_gamma=AxisymmetricSTFTensor(2e-6),
            n_e_sigmaT=1e2, decision=_allowing_decision(),
        )
        r2 = compute_photon_thomson_collision(
            theta_gamma=AxisymmetricSTFTensor(1e-5),
            E_gamma=AxisymmetricSTFTensor(2e-6),
            n_e_sigmaT=1e3, decision=_allowing_decision(),
        )
        assert r2.collision.amplitude == pytest.approx(
            10.0 * r1.collision.amplitude, rel=1e-14,
        )

    def test_rejects_negative_opacity(self):
        with pytest.raises(ValueError, match="non-negative"):
            compute_photon_thomson_collision(
                theta_gamma=AxisymmetricSTFTensor(1.0),
                E_gamma=AxisymmetricSTFTensor(0.0),
                n_e_sigmaT=-1.0,
                decision=_allowing_decision(),
            )

    def test_rejects_mismatched_axes(self):
        with pytest.raises(ValueError, match="axis"):
            compute_photon_thomson_collision(
                theta_gamma=AxisymmetricSTFTensor(1.0, SymmetryAxis.Z),
                E_gamma=AxisymmetricSTFTensor(1.0, SymmetryAxis.X),
                n_e_sigmaT=1.0,
                decision=_allowing_decision(),
            )


# ============================================================================
# Test Class 5 - STF polarization source Π
# ============================================================================

class TestPolarizationSourceSTF:
    """Π^STF_ab = Θ_ab + E_ab (h_ab trace drops in rank-2 equation)."""

    def test_pi_amplitude_is_theta_plus_E(self):
        result = compute_photon_thomson_collision(
            theta_gamma=AxisymmetricSTFTensor(3e-5),
            E_gamma=AxisymmetricSTFTensor(7e-6),
            n_e_sigmaT=1.0,
            decision=_allowing_decision(),
        )
        assert result.polarization_source_stf.amplitude == pytest.approx(
            3.7e-5, rel=1e-14,
        )

    def test_pi_is_STF(self):
        result = compute_photon_thomson_collision(
            theta_gamma=AxisymmetricSTFTensor(1e-3),
            E_gamma=AxisymmetricSTFTensor(2e-4),
            n_e_sigmaT=1.0,
            decision=_allowing_decision(),
        )
        assert result.polarization_source_stf.trace() == pytest.approx(
            0.0, abs=1e-14,
        )

    def test_pi_axis_matches_inputs(self):
        result = compute_photon_thomson_collision(
            theta_gamma=AxisymmetricSTFTensor(1.0, SymmetryAxis.Y),
            E_gamma=AxisymmetricSTFTensor(0.5, SymmetryAxis.Y),
            n_e_sigmaT=1.0,
            decision=_allowing_decision(),
        )
        assert result.polarization_source_stf.axis == SymmetryAxis.Y

    def test_pi_with_negative_E_reduces(self):
        # E can cancel Θ partially
        result = compute_photon_thomson_collision(
            theta_gamma=AxisymmetricSTFTensor(1.0),
            E_gamma=AxisymmetricSTFTensor(-0.5),
            n_e_sigmaT=1.0,
            decision=_allowing_decision(),
        )
        assert result.polarization_source_stf.amplitude == pytest.approx(
            0.5, rel=1e-14,
        )


# ============================================================================
# Test Class 6 - Quasi-static limit
# ============================================================================

class TestQuasiStaticLimit:
    """Pre-recombination: Θ^(γ)_ab ≃ (Σ^(γ)_2 / τ̇) σ_ab."""

    def test_formula_bit_exact(self):
        sigma = AxisymmetricSTFTensor(amplitude=1e-6, axis=SymmetryAxis.Z)
        theta_qs = compute_quasi_static_theta(
            shear=sigma, n_e_sigmaT=1e3, decision=_allowing_decision(),
        )
        expected = SIGMA_2_PHOTON_BE * 1e-6 / 1e3
        assert theta_qs.amplitude == pytest.approx(expected, rel=1e-14)

    def test_preserves_axis(self):
        sigma = AxisymmetricSTFTensor(amplitude=1.0, axis=SymmetryAxis.X)
        theta_qs = compute_quasi_static_theta(
            shear=sigma, n_e_sigmaT=10.0, decision=_allowing_decision(),
        )
        assert theta_qs.axis == SymmetryAxis.X

    def test_zero_shear_gives_zero_theta(self):
        sigma = AxisymmetricSTFTensor(amplitude=0.0)
        theta_qs = compute_quasi_static_theta(
            shear=sigma, n_e_sigmaT=1.0, decision=_allowing_decision(),
        )
        assert theta_qs.amplitude == 0.0

    def test_rejects_zero_opacity(self):
        sigma = AxisymmetricSTFTensor(amplitude=1.0)
        with pytest.raises(ValueError, match="positive"):
            compute_quasi_static_theta(
                shear=sigma, n_e_sigmaT=0.0, decision=_allowing_decision(),
            )

    def test_Sigma_2_override(self):
        # Override with a custom Σ_2 (e.g., for FD species at η=0)
        sigma = AxisymmetricSTFTensor(amplitude=1.0)
        # FD: I_4/I_3 ≈ 4.106, Σ_2 ≈ 2.190
        Sigma_2_FD = (8.0 / 15.0) * 4.106
        theta_qs = compute_quasi_static_theta(
            shear=sigma, n_e_sigmaT=1.0, decision=_allowing_decision(),
            Sigma_2=Sigma_2_FD,
        )
        assert theta_qs.amplitude == pytest.approx(Sigma_2_FD, rel=1e-14)


# ============================================================================
# Test Class 7 - E-mode Thomson source
# ============================================================================

class TestEModeThomsonSource:
    """Paper VI P2: Ė_ab = -(2/5) τ̇ c_ξ T_ab."""

    def test_formula_bit_exact(self):
        T = AxisymmetricSTFTensor(amplitude=1e-5, axis=SymmetryAxis.Z)
        E_dot = compute_e_mode_thomson_source(
            T_gamma=T, n_e_sigmaT=1e3,
            decision=_allowing_decision(), c_xi=1.0,
        )
        # -(2/5) × 1e3 × 1 × 1e-5 = -4e-3
        assert E_dot.amplitude == pytest.approx(-4e-3, rel=1e-14)

    def test_c_xi_scales_linearly(self):
        T = AxisymmetricSTFTensor(amplitude=1.0)
        E1 = compute_e_mode_thomson_source(
            T_gamma=T, n_e_sigmaT=1.0, decision=_allowing_decision(), c_xi=1.0,
        )
        E2 = compute_e_mode_thomson_source(
            T_gamma=T, n_e_sigmaT=1.0, decision=_allowing_decision(), c_xi=2.5,
        )
        assert E2.amplitude == pytest.approx(2.5 * E1.amplitude, rel=1e-14)

    def test_sign_is_negative_for_positive_T(self):
        T = AxisymmetricSTFTensor(amplitude=1.0)
        E_dot = compute_e_mode_thomson_source(
            T_gamma=T, n_e_sigmaT=1.0, decision=_allowing_decision(),
        )
        assert E_dot.amplitude < 0

    def test_zero_T_gives_zero_Edot(self):
        T = AxisymmetricSTFTensor(amplitude=0.0)
        E_dot = compute_e_mode_thomson_source(
            T_gamma=T, n_e_sigmaT=1.0, decision=_allowing_decision(),
        )
        assert E_dot.amplitude == 0.0

    def test_preserves_axis(self):
        T = AxisymmetricSTFTensor(amplitude=1.0, axis=SymmetryAxis.Y)
        E_dot = compute_e_mode_thomson_source(
            T_gamma=T, n_e_sigmaT=1.0, decision=_allowing_decision(),
        )
        assert E_dot.axis == SymmetryAxis.Y


# ============================================================================
# Test Class 8 - Runtime gating
# ============================================================================

class TestRuntimeGating:
    """Every public entry calls require_allow_reduction(...)."""

    def test_thomson_collision_raises_when_blocked(self):
        with pytest.raises(CanonicalBlockError, match="thomson_collision"):
            compute_photon_thomson_collision(
                theta_gamma=AxisymmetricSTFTensor(1.0),
                E_gamma=AxisymmetricSTFTensor(0.5),
                n_e_sigmaT=1.0,
                decision=_blocking_decision(),
            )

    def test_quasi_static_raises_when_blocked(self):
        with pytest.raises(CanonicalBlockError, match="quasi_static"):
            compute_quasi_static_theta(
                shear=AxisymmetricSTFTensor(1.0),
                n_e_sigmaT=1.0,
                decision=_blocking_decision(),
            )

    def test_e_mode_source_raises_when_blocked(self):
        with pytest.raises(CanonicalBlockError, match="e_mode_thomson"):
            compute_e_mode_thomson_source(
                T_gamma=AxisymmetricSTFTensor(1.0),
                n_e_sigmaT=1.0,
                decision=_blocking_decision(),
            )

    def test_blocked_error_carries_decision(self):
        try:
            compute_photon_thomson_collision(
                theta_gamma=AxisymmetricSTFTensor(1.0),
                E_gamma=AxisymmetricSTFTensor(0.0),
                n_e_sigmaT=1.0,
                decision=_blocking_decision(),
            )
        except CanonicalBlockError as e:
            assert e.decision.allow_reduction is False
            assert e.decision.beta_policy_pass is False

    def test_allowed_decision_does_not_raise(self):
        # Simple smoke: no exception from a standard evaluation
        result = compute_photon_thomson_collision(
            theta_gamma=AxisymmetricSTFTensor(1.0),
            E_gamma=AxisymmetricSTFTensor(0.5),
            n_e_sigmaT=1.0,
            decision=_allowing_decision(),
        )
        assert result is not None


# ============================================================================
# Test Class 9 - Quasi-static regime diagnostic
# ============================================================================

class TestQuasiStaticRegimeDiagnostic:
    """verify_quasi_static_regime + in_quasi_static_regime flag."""

    def test_high_opacity_is_quasi_static(self):
        assert verify_quasi_static_regime(n_e_sigmaT=1e3, hubble_rate=30.0) is True

    def test_low_opacity_is_free_streaming(self):
        # τ̇/H = 0.1, below threshold
        assert verify_quasi_static_regime(n_e_sigmaT=1.0, hubble_rate=10.0) is False

    def test_custom_threshold(self):
        # With threshold=100, τ̇/H=50 is NOT quasi-static
        assert verify_quasi_static_regime(
            n_e_sigmaT=500.0, hubble_rate=10.0, threshold=100.0,
        ) is False

    def test_rejects_zero_hubble(self):
        with pytest.raises(ValueError, match="hubble_rate"):
            verify_quasi_static_regime(n_e_sigmaT=1.0, hubble_rate=0.0)

    def test_collision_result_flag_when_quasi_static(self):
        result = compute_photon_thomson_collision(
            theta_gamma=AxisymmetricSTFTensor(1e-5),
            E_gamma=AxisymmetricSTFTensor(1e-6),
            n_e_sigmaT=1e4, decision=_allowing_decision(),
            hubble_rate=30.0,
        )
        assert result.in_quasi_static_regime is True
        assert result.tau_dot_over_H > QUASI_STATIC_TAU_H_THRESHOLD

    def test_collision_result_flag_when_free_streaming(self):
        result = compute_photon_thomson_collision(
            theta_gamma=AxisymmetricSTFTensor(1e-5),
            E_gamma=AxisymmetricSTFTensor(1e-6),
            n_e_sigmaT=0.1, decision=_allowing_decision(),
            hubble_rate=30.0,
        )
        assert result.in_quasi_static_regime is False
