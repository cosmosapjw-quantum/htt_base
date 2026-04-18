"""
Test suite: bass/transport/multipole_hierarchy.py  (Week 5-A Day 1)
=====================================================================

Test classes (10):
  1. TestMultipoleState             — container invariants
  2. TestZeroStateFactory           — zero_state helper
  3. TestHierarchyParameters        — parameter validation
  4. TestStreamingMatrix            — PSTF coupling coefficients
  5. TestSourceVector               — Σ_2 σ δ_{ℓ,2}
  6. TestEulerStepHierarchy         — single-step formula + validation
  7. TestSteadyStateAnalytic        — analytic linsolve
  8. TestD4Consistency              — reduces to W4D4 at k_eff=0, L_max=2
  9. TestIntegrationConvergence     — Euler loop converges to linsolve
  10. TestRuntimeGating             — all public entries gate

Target: ~55 tests.
"""
from __future__ import annotations

import math
import numpy as np
import pytest

from bass.collision.thomson_tensor import (
    AxisymmetricSTFTensor, SymmetryAxis, SIGMA_2_PHOTON_BE,
)
from bass.transport.ray_transport import (
    TransportSpecies, SIGMA_2_NEUTRINO_FD,
    make_photon_parameters, compute_steady_state,
)
from bass.transport.multipole_hierarchy import (
    MultipoleState,
    HierarchyParameters,
    HierarchyIntegrationResult,
    build_streaming_matrix,
    build_source_vector,
    euler_step_hierarchy,
    compute_steady_state_hierarchy,
    integrate_hierarchy_to_steady_state,
    make_photon_hierarchy_parameters,
    make_neutrino_hierarchy_parameters,
    zero_state,
    cfl_max_dt,
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


def _std_shear() -> AxisymmetricSTFTensor:
    return AxisymmetricSTFTensor(amplitude=1e-6, axis=SymmetryAxis.Z)


# ============================================================================
# Test Class 1 - MultipoleState container
# ============================================================================

class TestMultipoleState:
    def test_construction(self):
        amps = np.array([0.0, 1.0, 2.0, 3.0])
        s = MultipoleState(amplitudes=amps, axis=SymmetryAxis.Z)
        assert s.ell_max == 3
        assert s.n_multipoles == 4

    def test_ell_access(self):
        amps = np.array([10.0, 20.0, 30.0])
        s = MultipoleState(amplitudes=amps)
        assert s.ell(0) == 10.0
        assert s.ell(2) == 30.0

    def test_ell_access_out_of_range_raises(self):
        s = MultipoleState(amplitudes=np.ones(3))
        with pytest.raises(IndexError):
            s.ell(5)

    def test_frozen_dataclass(self):
        s = MultipoleState(amplitudes=np.zeros(3))
        with pytest.raises(Exception):
            s.axis = SymmetryAxis.X

    def test_rejects_non_1d(self):
        with pytest.raises(ValueError, match="1D"):
            MultipoleState(amplitudes=np.zeros((2, 3)))

    def test_rejects_empty(self):
        with pytest.raises(ValueError, match="non-empty"):
            MultipoleState(amplitudes=np.zeros(0))

    def test_as_stf_at_ell_2(self):
        amps = np.array([0.0, 0.0, 5.0, 0.0])
        s = MultipoleState(amplitudes=amps, axis=SymmetryAxis.Z)
        stf = s.as_stf_at(2)
        assert stf.amplitude == 5.0
        assert stf.axis == SymmetryAxis.Z

    def test_as_stf_at_non_two_rejected(self):
        s = MultipoleState(amplitudes=np.ones(4))
        with pytest.raises(ValueError, match="ell=2"):
            s.as_stf_at(3)


# ============================================================================
# Test Class 2 - zero_state factory
# ============================================================================

class TestZeroStateFactory:
    def test_creates_correct_size(self):
        s = zero_state(5)
        assert s.ell_max == 5
        assert s.n_multipoles == 6

    def test_all_amplitudes_zero(self):
        s = zero_state(4)
        assert np.all(s.amplitudes == 0.0)

    def test_default_axis_is_z(self):
        s = zero_state(2)
        assert s.axis == SymmetryAxis.Z

    def test_rejects_negative_ell_max(self):
        with pytest.raises(ValueError, match="ell_max"):
            zero_state(-1)


# ============================================================================
# Test Class 3 - HierarchyParameters validation
# ============================================================================

class TestHierarchyParameters:
    def test_frozen(self):
        p = HierarchyParameters(
            species=TransportSpecies.PHOTON, damping_rate=1.0,
            shear=_std_shear(), shear_coefficient=2.0,
            k_eff=1.0, ell_max=3,
        )
        with pytest.raises(Exception):
            p.k_eff = 99.0

    def test_rejects_negative_damping(self):
        with pytest.raises(ValueError, match="damping"):
            HierarchyParameters(
                species=TransportSpecies.PHOTON, damping_rate=-1.0,
                shear=_std_shear(), shear_coefficient=2.0,
                k_eff=1.0, ell_max=3,
            )

    def test_rejects_negative_shear_coeff(self):
        with pytest.raises(ValueError, match="shear_coefficient"):
            HierarchyParameters(
                species=TransportSpecies.PHOTON, damping_rate=1.0,
                shear=_std_shear(), shear_coefficient=-1.0,
                k_eff=1.0, ell_max=3,
            )

    def test_rejects_negative_k_eff(self):
        with pytest.raises(ValueError, match="k_eff"):
            HierarchyParameters(
                species=TransportSpecies.PHOTON, damping_rate=1.0,
                shear=_std_shear(), shear_coefficient=2.0,
                k_eff=-1.0, ell_max=3,
            )

    def test_photon_factory(self):
        p = make_photon_hierarchy_parameters(
            n_e_sigmaT=1e3, shear=_std_shear(), k_eff=10.0, ell_max=5,
            decision=_allowing_decision(),
        )
        assert p.species == TransportSpecies.PHOTON
        assert p.damping_rate == 1e3
        assert p.shear_coefficient == SIGMA_2_PHOTON_BE
        assert p.ell_max == 5

    def test_neutrino_factory(self):
        p = make_neutrino_hierarchy_parameters(
            hubble_rate=30.0, shear=_std_shear(), k_eff=10.0, ell_max=5,
            decision=_allowing_decision(),
        )
        assert p.species == TransportSpecies.NEUTRINO
        assert p.damping_rate == 30.0
        assert p.shear_coefficient == SIGMA_2_NEUTRINO_FD


# ============================================================================
# Test Class 4 - Streaming matrix
# ============================================================================

class TestStreamingMatrix:
    """PSTF streaming coefficients M[ℓ, ℓ-1] = +kℓ/(2ℓ+1), M[ℓ, ℓ+1] = -k(ℓ+1)/(2ℓ+1)."""

    def test_shape(self):
        M = build_streaming_matrix(1.0, 4)
        assert M.shape == (5, 5)

    def test_diagonal_is_zero(self):
        M = build_streaming_matrix(1.0, 4)
        assert np.allclose(np.diag(M), 0.0)

    def test_coefficient_M_1_0(self):
        # M[1, 0] = k × 1/3
        M = build_streaming_matrix(1.0, 3)
        assert M[1, 0] == pytest.approx(1.0 / 3.0, abs=1e-14)

    def test_coefficient_M_1_2(self):
        # M[1, 2] = -k × 2/3
        M = build_streaming_matrix(1.0, 3)
        assert M[1, 2] == pytest.approx(-2.0 / 3.0, abs=1e-14)

    def test_coefficient_M_2_1(self):
        M = build_streaming_matrix(1.0, 3)
        assert M[2, 1] == pytest.approx(2.0 / 5.0, abs=1e-14)

    def test_coefficient_M_2_3(self):
        M = build_streaming_matrix(1.0, 3)
        assert M[2, 3] == pytest.approx(-3.0 / 5.0, abs=1e-14)

    def test_coefficient_M_3_2(self):
        M = build_streaming_matrix(1.0, 4)
        assert M[3, 2] == pytest.approx(3.0 / 7.0, abs=1e-14)

    def test_k_eff_scales_linearly(self):
        M1 = build_streaming_matrix(1.0, 3)
        M5 = build_streaming_matrix(5.0, 3)
        assert np.allclose(M5, 5.0 * M1)

    def test_k_eff_zero_gives_zero_matrix(self):
        M = build_streaming_matrix(0.0, 4)
        assert np.allclose(M, 0.0)

    def test_boundary_no_column_above_ell_max(self):
        # At ℓ = ell_max, there is no ℓ+1 coupling (absorbed)
        M = build_streaming_matrix(1.0, 3)
        # Row 3 (ell_max = 3): only M[3, 2] should be nonzero
        assert M[3, 2] != 0
        # There's no column ell_max+1 = 4 in a (4,4) matrix

    def test_boundary_no_column_below_zero(self):
        # At ℓ = 0, no ℓ-1 coupling
        M = build_streaming_matrix(1.0, 3)
        # Row 0: only M[0, 1] nonzero
        assert M[0, 0] == 0
        assert M[0, 1] == pytest.approx(-1.0, abs=1e-14)

    def test_rejects_negative_k_eff(self):
        with pytest.raises(ValueError, match="k_eff"):
            build_streaming_matrix(-1.0, 3)

    def test_rejects_negative_ell_max(self):
        with pytest.raises(ValueError, match="ell_max"):
            build_streaming_matrix(1.0, -1)


# ============================================================================
# Test Class 5 - Source vector
# ============================================================================

class TestSourceVector:
    def test_source_at_ell_2_only(self):
        p = HierarchyParameters(
            species=TransportSpecies.PHOTON, damping_rate=1.0,
            shear=AxisymmetricSTFTensor(amplitude=3.0),
            shear_coefficient=2.0, k_eff=1.0, ell_max=4,
        )
        b = build_source_vector(p)
        assert b[2] == pytest.approx(6.0, abs=1e-14)   # 2.0 × 3.0
        for ell in (0, 1, 3, 4):
            assert b[ell] == 0.0

    def test_zero_shear_gives_zero_b(self):
        p = HierarchyParameters(
            species=TransportSpecies.PHOTON, damping_rate=1.0,
            shear=AxisymmetricSTFTensor(amplitude=0.0),
            shear_coefficient=2.0, k_eff=1.0, ell_max=4,
        )
        b = build_source_vector(p)
        assert np.all(b == 0.0)

    def test_no_source_below_ell_2(self):
        p = HierarchyParameters(
            species=TransportSpecies.PHOTON, damping_rate=1.0,
            shear=_std_shear(), shear_coefficient=2.0,
            k_eff=1.0, ell_max=1,
        )
        b = build_source_vector(p)
        assert len(b) == 2
        assert np.all(b == 0.0)

    def test_source_shape_matches_ell_max(self):
        p = HierarchyParameters(
            species=TransportSpecies.PHOTON, damping_rate=1.0,
            shear=_std_shear(), shear_coefficient=2.0,
            k_eff=1.0, ell_max=10,
        )
        b = build_source_vector(p)
        assert b.shape == (11,)


# ============================================================================
# Test Class 6 - Euler step
# ============================================================================

class TestEulerStepHierarchy:
    def test_zero_initial_plus_source_grows_ell_2(self):
        init = zero_state(3, SymmetryAxis.Z)
        params = make_photon_hierarchy_parameters(
            n_e_sigmaT=0.0, shear=_std_shear(), k_eff=0.0, ell_max=3,
            decision=_allowing_decision(),
        )
        new = euler_step_hierarchy(init, params, 0.01, _allowing_decision())
        # Only Θ_2 should grow (source), others stay zero
        assert new.amplitudes[2] > 0
        for ell in (0, 1, 3):
            assert new.amplitudes[ell] == 0.0

    def test_damping_reduces_amplitude_no_source(self):
        init = MultipoleState(
            amplitudes=np.array([0.0, 0.0, 1.0, 0.0]),
            axis=SymmetryAxis.Z,
        )
        # No shear, no streaming; just damping
        params = HierarchyParameters(
            species=TransportSpecies.PHOTON, damping_rate=2.0,
            shear=AxisymmetricSTFTensor(amplitude=0.0),
            shear_coefficient=SIGMA_2_PHOTON_BE,
            k_eff=0.0, ell_max=3,
        )
        new = euler_step_hierarchy(init, params, 0.1, _allowing_decision())
        # new[2] = 1 + 0.1 × (-2 × 1 + 0) = 0.8
        assert new.amplitudes[2] == pytest.approx(0.8, rel=1e-14)

    def test_streaming_transfers_from_ell_2_to_ell_3(self):
        # Start with amplitude only at ℓ=2, no damping, no source
        init = MultipoleState(
            amplitudes=np.array([0.0, 0.0, 1.0, 0.0]),
            axis=SymmetryAxis.Z,
        )
        params = HierarchyParameters(
            species=TransportSpecies.PHOTON, damping_rate=0.0,
            shear=AxisymmetricSTFTensor(amplitude=0.0),
            shear_coefficient=SIGMA_2_PHOTON_BE,
            k_eff=1.0, ell_max=3,
        )
        new = euler_step_hierarchy(init, params, 0.01, _allowing_decision())
        # dΘ_3/dt = k × ℓ/(2ℓ+1) × Θ_{ℓ-1} at ℓ=3 → = 1 × (3/7) × 1 = 3/7
        # new[3] = 0 + 0.01 × 3/7 ≈ 4.286e-3
        assert new.amplitudes[3] == pytest.approx(0.01 * 3.0 / 7.0, rel=1e-14)
        # dΘ_1/dt = k × -(ℓ+1)/(2ℓ+1) × Θ_{ℓ+1} at ℓ=1 → = -2/3 × 1 = -2/3
        # new[1] = 0 + 0.01 × (-2/3) ≈ -6.67e-3
        assert new.amplitudes[1] == pytest.approx(-0.01 * 2.0 / 3.0, rel=1e-14)

    def test_axis_preserved(self):
        init = zero_state(3, SymmetryAxis.Y)
        params = HierarchyParameters(
            species=TransportSpecies.PHOTON, damping_rate=1.0,
            shear=AxisymmetricSTFTensor(amplitude=1e-6, axis=SymmetryAxis.Y),
            shear_coefficient=SIGMA_2_PHOTON_BE,
            k_eff=0.0, ell_max=3,
        )
        new = euler_step_hierarchy(init, params, 0.001, _allowing_decision())
        assert new.axis == SymmetryAxis.Y

    def test_rejects_mismatched_ell_max(self):
        init = zero_state(3)
        params = make_photon_hierarchy_parameters(
            1e3, _std_shear(), 0.0, ell_max=5,
            decision=_allowing_decision(),
        )
        with pytest.raises(ValueError, match="ell_max"):
            euler_step_hierarchy(init, params, 0.01, _allowing_decision())

    def test_rejects_mismatched_axis(self):
        init = zero_state(3, axis=SymmetryAxis.X)
        params = HierarchyParameters(
            species=TransportSpecies.PHOTON, damping_rate=1.0,
            shear=AxisymmetricSTFTensor(amplitude=1e-6, axis=SymmetryAxis.Z),
            shear_coefficient=SIGMA_2_PHOTON_BE,
            k_eff=0.0, ell_max=3,
        )
        with pytest.raises(ValueError, match="axis"):
            euler_step_hierarchy(init, params, 0.01, _allowing_decision())

    def test_rejects_negative_dt(self):
        init = zero_state(3)
        params = make_photon_hierarchy_parameters(
            1e3, _std_shear(), 0.0, 3, _allowing_decision(),
        )
        with pytest.raises(ValueError, match="dt"):
            euler_step_hierarchy(init, params, -0.1, _allowing_decision())


# ============================================================================
# Test Class 7 - Steady state analytic
# ============================================================================

class TestSteadyStateAnalytic:
    def test_k_eff_zero_L_max_2_reproduces_D4(self):
        """No streaming, single source: Θ_2 = Σ_2 σ / Γ, others zero."""
        shear = _std_shear()
        tau_dot = 1e3
        params = make_photon_hierarchy_parameters(
            n_e_sigmaT=tau_dot, shear=shear, k_eff=0.0, ell_max=2,
            decision=_allowing_decision(),
        )
        ss = compute_steady_state_hierarchy(params, _allowing_decision())
        expected_l2 = SIGMA_2_PHOTON_BE * shear.amplitude / tau_dot
        assert ss.amplitudes[2] == pytest.approx(expected_l2, rel=1e-14)
        assert ss.amplitudes[0] == pytest.approx(0.0, abs=1e-14)
        assert ss.amplitudes[1] == pytest.approx(0.0, abs=1e-14)

    def test_higher_L_no_streaming_zero_above_ell_2(self):
        params = make_photon_hierarchy_parameters(
            n_e_sigmaT=1e3, shear=_std_shear(), k_eff=0.0, ell_max=6,
            decision=_allowing_decision(),
        )
        ss = compute_steady_state_hierarchy(params, _allowing_decision())
        # Only Θ_2 nonzero; streaming is off
        for ell in (0, 1, 3, 4, 5, 6):
            assert ss.amplitudes[ell] == pytest.approx(0.0, abs=1e-14)
        assert ss.amplitudes[2] > 0

    def test_streaming_produces_nonzero_higher_ell(self):
        params = make_photon_hierarchy_parameters(
            n_e_sigmaT=1e3, shear=_std_shear(), k_eff=100.0, ell_max=5,
            decision=_allowing_decision(),
        )
        ss = compute_steady_state_hierarchy(params, _allowing_decision())
        # Streaming leaks ℓ=2 to ℓ=3, 4, 5
        for ell in (3, 4, 5):
            assert abs(ss.amplitudes[ell]) > 0

    def test_steady_state_cascade_monotonic_decay(self):
        """|Θ_ℓ| monotonically decreases for ℓ ≥ 2 in the cascade."""
        params = make_photon_hierarchy_parameters(
            n_e_sigmaT=1e3, shear=_std_shear(), k_eff=50.0, ell_max=6,
            decision=_allowing_decision(),
        )
        ss = compute_steady_state_hierarchy(params, _allowing_decision())
        # ℓ=2 is driven, then cascade decays
        amps = np.abs(ss.amplitudes[2:])
        for i in range(1, len(amps)):
            assert amps[i] < amps[i - 1], (
                f"non-monotonic at ℓ={2+i}: {amps}"
            )

    def test_zero_damping_and_zero_k_rejected(self):
        params = HierarchyParameters(
            species=TransportSpecies.PHOTON, damping_rate=0.0,
            shear=_std_shear(), shear_coefficient=SIGMA_2_PHOTON_BE,
            k_eff=0.0, ell_max=3,
        )
        with pytest.raises(ValueError, match="trivial"):
            compute_steady_state_hierarchy(params, _allowing_decision())

    def test_preserves_axis(self):
        shear_x = AxisymmetricSTFTensor(amplitude=1e-6, axis=SymmetryAxis.X)
        params = make_photon_hierarchy_parameters(
            n_e_sigmaT=1e3, shear=shear_x, k_eff=10.0, ell_max=3,
            decision=_allowing_decision(),
        )
        ss = compute_steady_state_hierarchy(params, _allowing_decision())
        assert ss.axis == SymmetryAxis.X


# ============================================================================
# Test Class 8 - W4D4 consistency
# ============================================================================

class TestD4Consistency:
    """With k_eff=0 and L_max=2, reduce to W4D4 single-ℓ system."""

    def test_steady_state_matches_D4_photon(self):
        shear = _std_shear()
        tau_dot = 1e3
        # Hierarchy with k_eff=0, L_max=2
        p_hier = make_photon_hierarchy_parameters(
            n_e_sigmaT=tau_dot, shear=shear, k_eff=0.0, ell_max=2,
            decision=_allowing_decision(),
        )
        ss_hier = compute_steady_state_hierarchy(p_hier, _allowing_decision())
        # D4 single-ℓ
        p_d4 = make_photon_parameters(tau_dot, shear, _allowing_decision())
        ss_d4 = compute_steady_state(p_d4, _allowing_decision())
        assert ss_hier.amplitudes[2] == pytest.approx(
            ss_d4.amplitude, rel=1e-14,
        )

    def test_steady_state_matches_D4_neutrino(self):
        from bass.transport.ray_transport import make_neutrino_parameters
        shear = _std_shear()
        H = 30.0
        p_hier = make_neutrino_hierarchy_parameters(
            hubble_rate=H, shear=shear, k_eff=0.0, ell_max=2,
            decision=_allowing_decision(),
        )
        ss_hier = compute_steady_state_hierarchy(p_hier, _allowing_decision())
        p_d4 = make_neutrino_parameters(H, shear, _allowing_decision())
        ss_d4 = compute_steady_state(p_d4, _allowing_decision())
        assert ss_hier.amplitudes[2] == pytest.approx(
            ss_d4.amplitude, rel=1e-14,
        )

    def test_N_F_ratio_at_k_zero_matches_D4(self):
        """N_2/F_2 at k_eff=0 reproduces D4's 35.71."""
        shear = _std_shear()
        p_g = make_photon_hierarchy_parameters(
            n_e_sigmaT=1e3, shear=shear, k_eff=0.0, ell_max=2,
            decision=_allowing_decision(),
        )
        p_n = make_neutrino_hierarchy_parameters(
            hubble_rate=30.0, shear=shear, k_eff=0.0, ell_max=2,
            decision=_allowing_decision(),
        )
        ss_g = compute_steady_state_hierarchy(p_g, _allowing_decision())
        ss_n = compute_steady_state_hierarchy(p_n, _allowing_decision())
        ratio = ss_n.amplitudes[2] / ss_g.amplitudes[2]
        expected = (SIGMA_2_NEUTRINO_FD / SIGMA_2_PHOTON_BE) * (1e3 / 30.0)
        assert ratio == pytest.approx(expected, rel=1e-14)


# ============================================================================
# Test Class 9 - Integration convergence
# ============================================================================

class TestIntegrationConvergence:
    def test_converges_from_zero(self):
        params = make_photon_hierarchy_parameters(
            n_e_sigmaT=1e3, shear=_std_shear(), k_eff=100.0, ell_max=5,
            decision=_allowing_decision(),
        )
        init = zero_state(5)
        dt = 0.5 * cfl_max_dt(params)
        result = integrate_hierarchy_to_steady_state(
            init, params, dt, _allowing_decision(),
            max_steps=20000, tolerance=1e-10,
        )
        assert result.converged
        # Final state close to linsolve target
        max_rel_err = np.max(np.abs(
            result.final_state.amplitudes - result.steady_state_target.amplitudes
        ) / (np.abs(result.steady_state_target.amplitudes) + 1e-30))
        assert max_rel_err < 1e-5

    def test_returns_HierarchyIntegrationResult(self):
        params = make_photon_hierarchy_parameters(
            n_e_sigmaT=1e3, shear=_std_shear(), k_eff=10.0, ell_max=3,
            decision=_allowing_decision(),
        )
        init = zero_state(3)
        result = integrate_hierarchy_to_steady_state(
            init, params, 1e-4, _allowing_decision(),
        )
        assert isinstance(result, HierarchyIntegrationResult)

    def test_max_steps_enforced(self):
        params = make_photon_hierarchy_parameters(
            n_e_sigmaT=1e3, shear=_std_shear(), k_eff=10.0, ell_max=3,
            decision=_allowing_decision(),
        )
        init = zero_state(3)
        # Tight tolerance + few steps → won't converge
        result = integrate_hierarchy_to_steady_state(
            init, params, 1e-5, _allowing_decision(),
            max_steps=5, tolerance=1e-14,
        )
        assert result.converged is False
        assert result.steps_taken == 5

    def test_rejects_bad_tolerance(self):
        params = make_photon_hierarchy_parameters(
            n_e_sigmaT=1e3, shear=_std_shear(), k_eff=10.0, ell_max=3,
            decision=_allowing_decision(),
        )
        init = zero_state(3)
        with pytest.raises(ValueError, match="tolerance"):
            integrate_hierarchy_to_steady_state(
                init, params, 1e-4, _allowing_decision(),
                tolerance=-1e-6,
            )

    def test_rejects_mismatched_ell_max(self):
        params = make_photon_hierarchy_parameters(
            n_e_sigmaT=1e3, shear=_std_shear(), k_eff=10.0, ell_max=5,
            decision=_allowing_decision(),
        )
        init = zero_state(3)   # different ell_max
        with pytest.raises(ValueError, match="ell_max"):
            integrate_hierarchy_to_steady_state(
                init, params, 1e-4, _allowing_decision(),
            )


# ============================================================================
# Test Class 10 - Runtime gating
# ============================================================================

class TestRuntimeGating:
    def test_euler_step_blocked(self):
        init = zero_state(3)
        params = make_photon_hierarchy_parameters(
            n_e_sigmaT=1e3, shear=_std_shear(), k_eff=10.0, ell_max=3,
            decision=_allowing_decision(),
        )
        with pytest.raises(CanonicalBlockError, match="euler_step_hierarchy"):
            euler_step_hierarchy(init, params, 1e-4, _blocking_decision())

    def test_steady_state_blocked(self):
        params = make_photon_hierarchy_parameters(
            n_e_sigmaT=1e3, shear=_std_shear(), k_eff=10.0, ell_max=3,
            decision=_allowing_decision(),
        )
        with pytest.raises(CanonicalBlockError, match="compute_steady_state_hierarchy"):
            compute_steady_state_hierarchy(params, _blocking_decision())

    def test_integrate_blocked(self):
        init = zero_state(3)
        params = make_photon_hierarchy_parameters(
            n_e_sigmaT=1e3, shear=_std_shear(), k_eff=10.0, ell_max=3,
            decision=_allowing_decision(),
        )
        with pytest.raises(CanonicalBlockError, match="integrate_hierarchy_to_steady_state"):
            integrate_hierarchy_to_steady_state(
                init, params, 1e-4, _blocking_decision(),
            )

    def test_photon_hierarchy_factory_blocked(self):
        with pytest.raises(CanonicalBlockError):
            make_photon_hierarchy_parameters(
                n_e_sigmaT=1e3, shear=_std_shear(), k_eff=10.0, ell_max=3,
                decision=_blocking_decision(),
            )

    def test_neutrino_hierarchy_factory_blocked(self):
        with pytest.raises(CanonicalBlockError):
            make_neutrino_hierarchy_parameters(
                hubble_rate=30.0, shear=_std_shear(), k_eff=10.0, ell_max=3,
                decision=_blocking_decision(),
            )

    def test_blocked_error_carries_decision(self):
        params = make_photon_hierarchy_parameters(
            n_e_sigmaT=1e3, shear=_std_shear(), k_eff=10.0, ell_max=3,
            decision=_allowing_decision(),
        )
        try:
            compute_steady_state_hierarchy(params, _blocking_decision())
        except CanonicalBlockError as e:
            assert e.decision.allow_reduction is False


# ============================================================================
# Test Class 11 - CFL diagnostic
# ============================================================================

class TestCFLDiagnostic:
    def test_cfl_returns_finite_for_positive_damping(self):
        params = make_photon_hierarchy_parameters(
            n_e_sigmaT=1e3, shear=_std_shear(), k_eff=100.0, ell_max=3,
            decision=_allowing_decision(),
        )
        dt_max = cfl_max_dt(params)
        assert dt_max > 0
        assert math.isfinite(dt_max)
        # Γ + k_eff = 1100, so dt_max = 2/1100 ≈ 1.82e-3
        assert dt_max == pytest.approx(2.0 / 1100.0, rel=1e-14)

    def test_cfl_returns_infinity_for_zero_rates(self):
        params = HierarchyParameters(
            species=TransportSpecies.PHOTON, damping_rate=0.0,
            shear=_std_shear(), shear_coefficient=SIGMA_2_PHOTON_BE,
            k_eff=0.0, ell_max=3,
        )
        assert cfl_max_dt(params) == float("inf")
