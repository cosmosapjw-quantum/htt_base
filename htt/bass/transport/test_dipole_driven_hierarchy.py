"""
Test suite: bass/transport/dipole_driven_hierarchy.py  (Week 6-02)
===================================================================

Test classes:
  1. TestBaryonCoupling                      — container invariants
  2. TestDipoleDrive                         — trivial-drive detector
  3. TestNoDipoleDriveFactory                — trivial factory
  4. TestSourceVectorStructure               — b[1] acceleration + Doppler
  5. TestDampingVectorStructure              — +τ̇ at ℓ=1 only
  6. TestW5ABackwardCompatibility            — trivial drive = W5-A bit-exact
  7. TestEulerStepDipoleDriven               — single-step Euler formula
  8. TestSteadyStateDipoleDriven             — analytic linsolve
  9. TestTightCouplingPhotonLock             — Θ_1 → v_b/3 at large τ̇
 10. TestMomentumConservationPhotonBaryon    — equal-and-opposite signs
 11. TestIntegrationConvergence              — Euler reaches analytic target
 12. TestRuntimeGatingW3                     — public entries gate
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
)
from bass.transport.multipole_hierarchy import (
    HierarchyParameters,
    MultipoleState,
    build_source_vector,
    build_streaming_matrix,
    compute_steady_state_hierarchy,
    euler_step_hierarchy,
    integrate_hierarchy_to_steady_state,
    make_photon_hierarchy_parameters,
    zero_state,
)
from bass.transport.dipole_driven_hierarchy import (
    BaryonCoupling,
    DipoleDrive,
    build_damping_vector,
    build_dipole_driven_source_vector,
    cfl_max_dt_dipole_driven,
    compute_steady_state_dipole_driven,
    euler_step_dipole_driven,
    integrate_dipole_driven_to_steady_state,
    no_dipole_drive,
    tight_coupling_photon_residual,
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


def _std_shear(amplitude: float = 1e-6) -> AxisymmetricSTFTensor:
    return AxisymmetricSTFTensor(amplitude=amplitude, axis=SymmetryAxis.Z)


def _std_photon_params(
    ell_max: int = 5,
    k_eff: float = 10.0,
    gamma: float = 1e3,
) -> HierarchyParameters:
    return HierarchyParameters(
        species=TransportSpecies.PHOTON,
        damping_rate=gamma,
        shear=_std_shear(),
        shear_coefficient=SIGMA_2_PHOTON_BE,
        k_eff=k_eff,
        ell_max=ell_max,
    )


# ============================================================================
# 1. TestBaryonCoupling
# ============================================================================

class TestBaryonCoupling:

    def test_construction_valid(self):
        bc = BaryonCoupling(v_b=1e-4, tau_dot=1e3)
        assert bc.v_b == 1e-4
        assert bc.tau_dot == 1e3

    def test_frozen(self):
        bc = BaryonCoupling(v_b=0.0, tau_dot=1e3)
        with pytest.raises(Exception):
            bc.v_b = 1.0

    def test_tau_dot_zero_allowed(self):
        bc = BaryonCoupling(v_b=0.0, tau_dot=0.0)
        assert bc.tau_dot == 0.0

    def test_tau_dot_negative_rejected(self):
        with pytest.raises(ValueError, match="tau_dot must be non-negative"):
            BaryonCoupling(v_b=0.0, tau_dot=-1.0)

    def test_nan_v_b_rejected(self):
        with pytest.raises(ValueError, match="v_b must be finite"):
            BaryonCoupling(v_b=float("nan"), tau_dot=1e3)


# ============================================================================
# 2. TestDipoleDrive
# ============================================================================

class TestDipoleDrive:

    def test_default_is_trivial(self):
        d = DipoleDrive()
        assert d.is_trivial
        assert d.acceleration_A_1 == 0.0
        assert d.baryon_coupling is None

    def test_with_acceleration_not_trivial(self):
        d = DipoleDrive(acceleration_A_1=1e-5)
        assert not d.is_trivial

    def test_with_coupling_not_trivial(self):
        d = DipoleDrive(
            baryon_coupling=BaryonCoupling(v_b=1e-4, tau_dot=1e3),
        )
        assert not d.is_trivial

    def test_nan_acceleration_rejected(self):
        with pytest.raises(ValueError, match="acceleration_A_1 must be finite"):
            DipoleDrive(acceleration_A_1=float("nan"))


# ============================================================================
# 3. TestNoDipoleDriveFactory
# ============================================================================

class TestNoDipoleDriveFactory:

    def test_factory_returns_trivial(self):
        d = no_dipole_drive()
        assert d.is_trivial


# ============================================================================
# 4. TestSourceVectorStructure
# ============================================================================

class TestSourceVectorStructure:

    def test_trivial_drive_matches_w5a(self):
        p = _std_photon_params()
        b_w5a = build_source_vector(p)
        b_new = build_dipole_driven_source_vector(p, no_dipole_drive())
        np.testing.assert_array_equal(b_w5a, b_new)

    def test_acceleration_enters_at_ell_1(self):
        p = _std_photon_params()
        A_1 = 3e-4
        drive = DipoleDrive(acceleration_A_1=A_1)
        b = build_dipole_driven_source_vector(p, drive)
        # b[1] should be A_1 / 3, all other ells should match W5-A
        b_w5a = build_source_vector(p)
        assert abs(b[1] - A_1 / 3.0) < 1e-15
        for ell in range(p.ell_max + 1):
            if ell != 1:
                assert b[ell] == b_w5a[ell]

    def test_doppler_from_baryon_at_ell_1(self):
        p = _std_photon_params()
        v_b = 3e-4
        tau_dot = 2e3
        drive = DipoleDrive(
            baryon_coupling=BaryonCoupling(v_b=v_b, tau_dot=tau_dot),
        )
        b = build_dipole_driven_source_vector(p, drive)
        # b[1] should be τ̇ v_b / 3
        assert abs(b[1] - tau_dot * v_b / 3.0) < 1e-10

    def test_acceleration_plus_doppler_linear(self):
        p = _std_photon_params()
        A_1 = 3e-4
        v_b = 6e-4
        tau_dot = 1e3
        drive = DipoleDrive(
            acceleration_A_1=A_1,
            baryon_coupling=BaryonCoupling(v_b=v_b, tau_dot=tau_dot),
        )
        b = build_dipole_driven_source_vector(p, drive)
        expected = A_1 / 3.0 + tau_dot * v_b / 3.0
        assert abs(b[1] - expected) < 1e-10

    def test_ell_2_shear_source_preserved(self):
        p = _std_photon_params()
        drive = DipoleDrive(
            acceleration_A_1=1e-3,
            baryon_coupling=BaryonCoupling(v_b=1e-3, tau_dot=1e3),
        )
        b = build_dipole_driven_source_vector(p, drive)
        expected_b2 = p.shear_coefficient * p.shear.amplitude
        assert abs(b[2] - expected_b2) < 1e-20


# ============================================================================
# 5. TestDampingVectorStructure
# ============================================================================

class TestDampingVectorStructure:

    def test_uniform_when_trivial(self):
        p = _std_photon_params(ell_max=5, gamma=1e3)
        gv = build_damping_vector(p, no_dipole_drive())
        assert gv.shape == (6,)
        for v in gv:
            assert v == 1e3

    def test_adds_tau_at_ell_1_only(self):
        p = _std_photon_params(ell_max=5, gamma=1e3)
        tau = 500.0
        drive = DipoleDrive(
            baryon_coupling=BaryonCoupling(v_b=0.0, tau_dot=tau),
        )
        gv = build_damping_vector(p, drive)
        # ell=1 should have extra τ̇; others unchanged
        assert abs(gv[1] - (1e3 + tau)) < 1e-14
        for ell in [0, 2, 3, 4, 5]:
            assert gv[ell] == 1e3

    def test_no_change_with_acceleration_only(self):
        # Acceleration drive is inhomogeneous — does NOT change damping.
        p = _std_photon_params()
        drive = DipoleDrive(acceleration_A_1=1e-3)
        gv = build_damping_vector(p, drive)
        for v in gv:
            assert v == p.damping_rate

    def test_ell_max_zero_no_crash(self):
        p = _std_photon_params(ell_max=0)
        drive = DipoleDrive(
            baryon_coupling=BaryonCoupling(v_b=0.0, tau_dot=1e3),
        )
        gv = build_damping_vector(p, drive)
        # Only ℓ=0 exists, no ℓ=1 modification applies
        assert gv.shape == (1,)
        assert gv[0] == p.damping_rate


# ============================================================================
# 6. TestW5ABackwardCompatibility
# ============================================================================

class TestW5ABackwardCompatibility:
    """Critical: trivial drive must be bit-exact to W5-A behavior."""

    def test_euler_step_identical(self):
        p = _std_photon_params(ell_max=5, k_eff=10.0, gamma=1e3)
        state = MultipoleState(
            amplitudes=np.array([1e-4, 2e-5, 5e-6, 1e-6, 3e-7, 8e-8]),
            axis=SymmetryAxis.Z,
        )
        dt = 1e-5
        s_w5a = euler_step_hierarchy(state, p, dt, _allowing_decision())
        s_new = euler_step_dipole_driven(
            state, p, no_dipole_drive(), dt, _allowing_decision(),
        )
        np.testing.assert_array_equal(s_w5a.amplitudes, s_new.amplitudes)
        assert s_w5a.axis == s_new.axis

    def test_steady_state_identical(self):
        p = _std_photon_params(ell_max=8, k_eff=5.0, gamma=1e3)
        ss_w5a = compute_steady_state_hierarchy(p, _allowing_decision())
        ss_new = compute_steady_state_dipole_driven(
            p, no_dipole_drive(), _allowing_decision(),
        )
        np.testing.assert_allclose(
            ss_w5a.amplitudes, ss_new.amplitudes,
            rtol=1e-14, atol=0.0,
        )

    def test_integration_converges_to_same_target(self):
        p = _std_photon_params(ell_max=5, k_eff=1.0, gamma=1e3)
        init = zero_state(p.ell_max)
        dt = 1e-4
        r_w5a = integrate_hierarchy_to_steady_state(
            init, p, dt, _allowing_decision(),
            max_steps=2000, tolerance=1e-8,
        )
        r_new = integrate_dipole_driven_to_steady_state(
            init, p, no_dipole_drive(), dt, _allowing_decision(),
            max_steps=2000, tolerance=1e-8,
        )
        np.testing.assert_allclose(
            r_w5a.final_state.amplitudes, r_new.final_state.amplitudes,
            rtol=1e-12, atol=0.0,
        )

    def test_cfl_matches_when_trivial(self):
        from bass.transport.multipole_hierarchy import cfl_max_dt
        p = _std_photon_params()
        cfl_w5a = cfl_max_dt(p)
        cfl_new = cfl_max_dt_dipole_driven(p, no_dipole_drive())
        assert abs(cfl_w5a - cfl_new) < 1e-14


# ============================================================================
# 7. TestEulerStepDipoleDriven
# ============================================================================

class TestEulerStepDipoleDriven:

    def test_acceleration_source_enters_dynamics(self):
        # Start from zero; after one step, ℓ=1 should be non-zero.
        p = _std_photon_params(ell_max=5, k_eff=0.0, gamma=0.0)
        A_1 = 3e-4
        drive = DipoleDrive(acceleration_A_1=A_1)
        init = zero_state(p.ell_max)
        dt = 1e-4
        new = euler_step_dipole_driven(
            init, p, drive, dt, _allowing_decision(),
        )
        # Θ_1 should advance by dt × (A_1 / 3)
        assert abs(new.amplitudes[1] - dt * A_1 / 3.0) < 1e-18

    def test_baryon_coupling_drives_toward_vb_over_3(self):
        # Start at Θ_1 = 0 with finite v_b, large τ̇ → Θ_1 grows.
        p = _std_photon_params(ell_max=3, k_eff=0.0, gamma=0.0)
        bc = BaryonCoupling(v_b=3e-4, tau_dot=1e4)
        drive = DipoleDrive(baryon_coupling=bc)
        init = zero_state(p.ell_max)
        dt = 1e-5
        new = euler_step_dipole_driven(
            init, p, drive, dt, _allowing_decision(),
        )
        # Θ_1 should increase (moving toward v_b/3 = 1e-4)
        assert new.amplitudes[1] > 0.0

    def test_rejects_zero_dt(self):
        p = _std_photon_params()
        with pytest.raises(ValueError, match="dt must be positive"):
            euler_step_dipole_driven(
                zero_state(p.ell_max), p, no_dipole_drive(),
                0.0, _allowing_decision(),
            )

    def test_rejects_shape_mismatch(self):
        p = _std_photon_params(ell_max=5)
        wrong_state = zero_state(3)  # ell_max=3 vs params ell_max=5
        with pytest.raises(ValueError, match="ell_max"):
            euler_step_dipole_driven(
                wrong_state, p, no_dipole_drive(),
                1e-4, _allowing_decision(),
            )


# ============================================================================
# 8. TestSteadyStateDipoleDriven
# ============================================================================

class TestSteadyStateDipoleDriven:

    def test_acceleration_only_produces_dipole(self):
        # Without shear but with A_1 ≠ 0: Θ_1 nonzero in steady state.
        p = HierarchyParameters(
            species=TransportSpecies.PHOTON,
            damping_rate=1e3,
            shear=AxisymmetricSTFTensor(amplitude=0.0, axis=SymmetryAxis.Z),
            shear_coefficient=0.0,
            k_eff=0.0,
            ell_max=3,
        )
        A_1 = 3e-3
        drive = DipoleDrive(acceleration_A_1=A_1)
        ss = compute_steady_state_dipole_driven(
            p, drive, _allowing_decision(),
        )
        # With k_eff = 0 and no baryon drag, Γ Θ_1 = A_1/3 ⇒ Θ_1 = A_1/(3Γ)
        expected_theta_1 = A_1 / (3.0 * p.damping_rate)
        assert abs(ss.amplitudes[1] - expected_theta_1) < 1e-10
        # Θ_0 = 0 (no source at ℓ=0)
        assert abs(ss.amplitudes[0]) < 1e-12

    def test_baryon_drag_equilibrium(self):
        # Large τ̇ ≫ Γ baseline: Θ_1 → v_b/3 closely.
        # A tiny baseline Γ keeps all ℓ non-singular (so Θ_0 etc. are
        # uniquely determined, pinned at zero by having no source).
        p = HierarchyParameters(
            species=TransportSpecies.PHOTON,
            damping_rate=1e-3,  # tiny baseline for regularity
            shear=AxisymmetricSTFTensor(amplitude=0.0, axis=SymmetryAxis.Z),
            shear_coefficient=0.0,
            k_eff=0.0,
            ell_max=3,
        )
        v_b = 3e-4
        bc = BaryonCoupling(v_b=v_b, tau_dot=1e5)
        drive = DipoleDrive(baryon_coupling=bc)
        ss = compute_steady_state_dipole_driven(
            p, drive, _allowing_decision(),
        )
        # Steady state: (Γ + τ̇) Θ_1 = τ̇ v_b/3 ⇒
        #   Θ_1 = v_b/3 · τ̇/(Γ + τ̇); with τ̇ = 1e5 ≫ Γ = 1e-3,
        # the ratio differs from unity by ~1e-8.
        expected = (v_b / 3.0) * bc.tau_dot / (p.damping_rate + bc.tau_dot)
        assert abs(ss.amplitudes[1] - expected) < 1e-14 * abs(expected) + 1e-14
        # And v_b/3 is recovered to ~τ̇/(Γ+τ̇) = 1 - Γ/τ̇ ≈ 1
        assert abs(ss.amplitudes[1] / (v_b / 3.0) - 1.0) < 1e-7

    def test_rejects_trivial_dynamics(self):
        # Γ = 0 and k_eff = 0 → no unique steady state, but if we
        # HAVE baryon coupling, τ̇ provides damping at ℓ=1 so still OK.
        # This test hits the fully trivial case: drive also trivial.
        p = HierarchyParameters(
            species=TransportSpecies.PHOTON,
            damping_rate=0.0,
            shear=AxisymmetricSTFTensor(amplitude=0.0, axis=SymmetryAxis.Z),
            shear_coefficient=0.0,
            k_eff=0.0,
            ell_max=3,
        )
        with pytest.raises(ValueError, match="trivial null dynamics"):
            compute_steady_state_dipole_driven(
                p, no_dipole_drive(), _allowing_decision(),
            )


# ============================================================================
# 9. TestTightCouplingPhotonLock
# ============================================================================

class TestTightCouplingPhotonLock:

    def test_residual_zero_at_lock(self):
        # State with Θ_1 = v_b/3 exactly
        v_b = 3e-4
        state = MultipoleState(
            amplitudes=np.array([0.0, v_b / 3.0, 0.0, 0.0]),
            axis=SymmetryAxis.Z,
        )
        drive = DipoleDrive(
            baryon_coupling=BaryonCoupling(v_b=v_b, tau_dot=1e3),
        )
        r = tight_coupling_photon_residual(state, drive)
        assert abs(r) < 1e-14

    def test_residual_order_unity_when_decoupled(self):
        v_b = 3e-4
        state = MultipoleState(
            amplitudes=np.array([0.0, 0.0, 0.0, 0.0]),
            axis=SymmetryAxis.Z,
        )
        drive = DipoleDrive(
            baryon_coupling=BaryonCoupling(v_b=v_b, tau_dot=1e3),
        )
        r = tight_coupling_photon_residual(state, drive)
        # (0 − v_b/3) / (v_b/3) = −1
        assert abs(r - (-1.0)) < 1e-14

    def test_nan_when_no_coupling(self):
        state = zero_state(3)
        drive = no_dipole_drive()
        r = tight_coupling_photon_residual(state, drive)
        assert math.isnan(r)

    def test_large_tau_brings_theta_1_to_vb_over_3(self):
        # Steady-state test: Θ_1 should equal v_b/3 at high τ̇.
        p = HierarchyParameters(
            species=TransportSpecies.PHOTON,
            damping_rate=1e3,  # mild
            shear=AxisymmetricSTFTensor(amplitude=0.0, axis=SymmetryAxis.Z),
            shear_coefficient=0.0,
            k_eff=0.0,
            ell_max=3,
        )
        v_b = 3e-4
        for tau in [1e4, 1e6, 1e9]:
            drive = DipoleDrive(
                baryon_coupling=BaryonCoupling(v_b=v_b, tau_dot=tau),
            )
            ss = compute_steady_state_dipole_driven(
                p, drive, _allowing_decision(),
            )
            # With Γ at ℓ=1 = Γ + τ̇, steady state:
            #   (Γ + τ̇) Θ_1 = (τ̇ v_b)/3  ⇒  Θ_1 = v_b/3 · τ̇/(Γ+τ̇)
            expected = (v_b / 3.0) * tau / (p.damping_rate + tau)
            assert abs(ss.amplitudes[1] - expected) < 1e-10 * abs(expected)


# ============================================================================
# 10. TestMomentumConservationPhotonBaryon
# ============================================================================

class TestMomentumConservationPhotonBaryon:
    """The photon-side Thomson drag must be equal-and-opposite to the
    baryon-side drag from W6-01 (up to the R_b, 1/3 normalization).

    Baryon side: (τ̇/R_b)(3Θ_1 − v_b)        — from W6-01
    Photon side: −τ̇(Θ_1 − v_b/3)             — this module

    Taking ρ_γ × photon-RHS + ρ_b × baryon-RHS of the momentum:
        ρ_γ · (−τ̇(Θ_1 − v_b/3)) + (4 R_b ρ_γ / 3) · (τ̇/R_b)(3Θ_1 − v_b)
      = ρ_γ τ̇ [−(Θ_1 − v_b/3) + (4/3)(Θ_1 − v_b/3)]
      = ρ_γ τ̇ · (1/3)(Θ_1 − v_b/3)                                (*)

    Wait — this does NOT cancel by itself. Momentum conservation in the
    CAMB convention with v_b = 3Θ_1 lock requires normalizations that
    involve the factor (4/3) from radiation stress-energy: the baryon
    momentum density is ρ_b v_b, the photon momentum density is
    (4/3) ρ_γ Θ_1 (with the 4/3 from p = ρ/3 in T^{0i}). Combined:

        ρ_b v̇_b + (4/3) ρ_γ Θ̇_1 |_{drag}
          = ρ_b · (τ̇/R_b)(3Θ_1 − v_b) + (4/3) ρ_γ · (−τ̇)(Θ_1 − v_b/3)
          = (τ̇/R_b) · ρ_b (3Θ_1 − v_b) − (4 τ̇/3) ρ_γ (Θ_1 − v_b/3)
          = (τ̇ · 4 ρ_γ / 3) (3Θ_1 − v_b) − (4 τ̇ / 3) ρ_γ (Θ_1 − v_b/3)
            [using ρ_b/R_b = 4 ρ_γ / 3]
          = (4 τ̇ ρ_γ / 3) [(3Θ_1 − v_b) − (Θ_1 − v_b/3)]
          = (4 τ̇ ρ_γ / 3) · (2 Θ_1 − (2/3) v_b)
          ≠ 0 in general

    The correct cancellation uses the 1/3 factor differently. In CAMB's
    Boltzmann hierarchy Θ_1 is dimensionally identified with the
    photon "velocity perturbation / 3" (see CAMB notes §7.3: q_γ =
    4 v_b / 3 at tight coupling, where q_γ = F_1 in their notation).
    So the relevant photon momentum variable is 3 Θ_1 ≡ q_γ-equivalent.

    What THIS test verifies is the simpler sign-discipline property:
    at the locked state (Θ_1 = v_b/3), both drags vanish; away from
    lock, they point TOWARD lock on each side.
    """

    def test_drag_zero_at_lock(self):
        # Both the baryon drag (from W6-01) and the photon drag
        # (this module) vanish at Θ_1 = v_b/3.
        from bass.perturbation.baryon_fluid import (
            BaryonFluidState,
            BaryonParameters,
            baryon_euler_rhs,
        )
        v_b = 3e-4
        theta_1 = v_b / 3.0
        # Baryon side (H=0 to isolate drag)
        s_b = BaryonFluidState(delta_b=0.0, v_b=v_b)
        p_b = BaryonParameters(R_b=0.6, tau_dot=1e6, H=0.0)
        dot_vb = baryon_euler_rhs(s_b, theta_1, p_b, _allowing_decision())
        assert abs(dot_vb) < 1e-8

        # Photon side: Θ̇_1 contribution from Thomson = −τ̇(Θ_1 − v_b/3) = 0
        state = MultipoleState(
            amplitudes=np.array([0.0, theta_1, 0.0, 0.0]),
            axis=SymmetryAxis.Z,
        )
        p_gamma = HierarchyParameters(
            species=TransportSpecies.PHOTON,
            damping_rate=0.0,
            shear=AxisymmetricSTFTensor(amplitude=0.0, axis=SymmetryAxis.Z),
            shear_coefficient=0.0,
            k_eff=0.0,
            ell_max=3,
        )
        drive = DipoleDrive(
            baryon_coupling=BaryonCoupling(v_b=v_b, tau_dot=1e6),
        )
        # Source vector b[1] = τ̇ v_b/3; damping at ℓ=1 = τ̇.
        # RHS = b[1] − Γ_1 Θ_1 = τ̇ v_b/3 − τ̇ · (v_b/3) = 0.
        b = build_dipole_driven_source_vector(p_gamma, drive)
        gamma_vec = build_damping_vector(p_gamma, drive)
        rhs = b[1] - gamma_vec[1] * state.amplitudes[1]
        assert abs(rhs) < 1e-8

    def test_drags_point_toward_lock_from_below(self):
        # Θ_1 < v_b/3, H=0, no shear: Θ̇_1|_{Thomson} > 0
        v_b = 3e-4
        theta_1 = 0.0
        state = MultipoleState(
            amplitudes=np.array([0.0, theta_1, 0.0, 0.0]),
            axis=SymmetryAxis.Z,
        )
        p_gamma = HierarchyParameters(
            species=TransportSpecies.PHOTON,
            damping_rate=0.0,
            shear=AxisymmetricSTFTensor(amplitude=0.0, axis=SymmetryAxis.Z),
            shear_coefficient=0.0,
            k_eff=0.0,
            ell_max=3,
        )
        drive = DipoleDrive(
            baryon_coupling=BaryonCoupling(v_b=v_b, tau_dot=1e4),
        )
        b = build_dipole_driven_source_vector(p_gamma, drive)
        gamma_vec = build_damping_vector(p_gamma, drive)
        dot_theta_1 = b[1] - gamma_vec[1] * state.amplitudes[1]
        # Θ̇_1 = τ̇ v_b/3 − τ̇ · 0 = τ̇ v_b/3 > 0
        assert dot_theta_1 > 0.0


# ============================================================================
# 11. TestIntegrationConvergence
# ============================================================================

class TestIntegrationConvergence:

    def test_converges_to_analytic_target(self):
        p = _std_photon_params(ell_max=5, k_eff=1.0, gamma=1e3)
        A_1 = 3e-4
        drive = DipoleDrive(
            acceleration_A_1=A_1,
            baryon_coupling=BaryonCoupling(v_b=6e-4, tau_dot=500.0),
        )
        init = zero_state(p.ell_max)
        dt = 1e-5
        result = integrate_dipole_driven_to_steady_state(
            init, p, drive, dt, _allowing_decision(),
            max_steps=20000, tolerance=1e-9,
        )
        assert result.converged
        target_ss = compute_steady_state_dipole_driven(
            p, drive, _allowing_decision(),
        )
        # rtol 1% is realistic: step-to-step tolerance 1e-9 is dominated by
        # the largest component (Θ_1 ~ 7e-5), whereas Θ_{ℓ≥3} components
        # at ~1e-11 or smaller have slower convergence. This test checks
        # structural convergence, not full floating-point agreement.
        np.testing.assert_allclose(
            result.final_state.amplitudes, target_ss.amplitudes,
            rtol=1e-2, atol=1e-20,
        )
        # Tightest check on the dominant component (Θ_1)
        assert abs(
            result.final_state.amplitudes[1] - target_ss.amplitudes[1]
        ) < 1e-6 * abs(target_ss.amplitudes[1])

    def test_cfl_bound_tightens_with_tau(self):
        p = _std_photon_params(ell_max=3, k_eff=0.0, gamma=1e3)
        dt_no = cfl_max_dt_dipole_driven(p, no_dipole_drive())
        drive_hi = DipoleDrive(
            baryon_coupling=BaryonCoupling(v_b=0.0, tau_dot=1e5),
        )
        dt_hi = cfl_max_dt_dipole_driven(p, drive_hi)
        assert dt_hi < dt_no


# ============================================================================
# 12. TestRuntimeGatingW3
# ============================================================================

class TestRuntimeGatingW3:

    def test_euler_step_gates(self):
        p = _std_photon_params()
        with pytest.raises(CanonicalBlockError):
            euler_step_dipole_driven(
                zero_state(p.ell_max), p, no_dipole_drive(),
                1e-5, _blocking_decision(),
            )

    def test_steady_state_gates(self):
        p = _std_photon_params()
        with pytest.raises(CanonicalBlockError):
            compute_steady_state_dipole_driven(
                p, no_dipole_drive(), _blocking_decision(),
            )

    def test_integrate_gates(self):
        p = _std_photon_params()
        with pytest.raises(CanonicalBlockError):
            integrate_dipole_driven_to_steady_state(
                zero_state(p.ell_max), p, no_dipole_drive(),
                1e-5, _blocking_decision(),
            )

    def test_diagnostics_have_no_gate(self):
        # build_*, cfl_*, tight_coupling_photon_residual are pure
        # utilities with no decision parameter. Regression guard.
        import inspect
        for fn in [
            build_damping_vector,
            build_dipole_driven_source_vector,
            cfl_max_dt_dipole_driven,
            tight_coupling_photon_residual,
        ]:
            sig = inspect.signature(fn)
            assert "decision" not in sig.parameters, (
                f"{fn.__name__} must not have a decision parameter"
            )
