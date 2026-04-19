"""
tests/test_channel_routing.py
==============================

Day 5 test suite covering:
  §1 — smoothstep_C2 mathematical properties
  §2 — W_R window function (C² continuity, zero outside, unit inside)
  §3 — Paper I Prop 5 coefficients
  §4 — boost_mixing_matrix structure
  §5 — boost_additive_velocity_terms
  §6 — apply_boost_to_teff — order-of-v consistency
  §7 — TiltRouter.route — all (effect, channel) pairs
  §8 — enforce_local_EE_zero sentinel
  §9 — apply_local_boost vs apply_global_tilt
  §10 — Combined router (both global and local active)
  §11 — Factory functions

Run
---
    pytest test_channel_routing.py -v
"""
from __future__ import annotations

import math
import numpy as np
import pytest

from bass.validation.channel_routing import (
    Channel, TiltEffect,
    smoothstep_C2, window_W_R, window_W_R_max_gradient,
    PROP5_COEFF_DIPOLE_FROM_QUADRUPOLE,
    PROP5_COEFF_QUADRUPOLE_FROM_DIPOLE,
    PROP5_COEFF_OCTUPOLE_FROM_QUADRUPOLE,
    boost_mixing_matrix, boost_additive_velocity_terms, apply_boost_to_teff,
    TiltRouter,
    make_global_only_router, make_local_only_router, make_combined_router,
)


CF4_BETA = 1.36e-3
LOCAL_V = np.array([369e3 / 299792.458, 0.0, 0.0])  # LG peculiar velocity ≈ 369 km/s
R_PATCH_MPC = 50.0  # typical local patch radius


# ═══════════════════════════════════════════════════════════════
# §1 — smoothstep_C2 properties
# ═══════════════════════════════════════════════════════════════

class TestSmoothstepC2:
    def test_q_zero_at_zero(self):
        assert smoothstep_C2(np.array([0.0])) == 0.0

    def test_q_one_at_one(self):
        assert smoothstep_C2(np.array([1.0])) == 1.0

    def test_q_monotone_on_unit_interval(self):
        t = np.linspace(0, 1, 100)
        q = smoothstep_C2(t)
        # Strictly increasing on (0, 1)
        assert np.all(np.diff(q) >= -1e-15)

    def test_q_half_equals_half(self):
        """At t=1/2, q = 10/32 - 15/32 + 6/32 = ... wait let me recompute.
        q(1/2) = 10(1/8) - 15(1/16) + 6(1/32) = 40/32 - 30/32 + 6/32 = 16/32 = 1/2."""
        assert math.isclose(smoothstep_C2(np.array([0.5]))[0], 0.5, abs_tol=1e-15)

    def test_derivative_zero_at_endpoints(self):
        """q'(0) = q'(1) = 0 — verified analytically.

        q(t) = 10t³ − 15t⁴ + 6t⁵ = t³(10 − 15t + 6t²)
        q'(t) = 30t² − 60t³ + 30t⁴ = 30 t² (1 − t)²

        The factored form q'(t) = 30 t² (1-t)² makes q'(0) = q'(1) = 0 exactly,
        not merely approximately. We verify numerically by sampling points
        close to 0 and 1 and checking q scales as the correct power.
        """
        # Near t=0: q ~ 10 t³ → q/t³ should approach 10
        t_left = 1e-4
        q_left = smoothstep_C2(np.array([t_left]))[0]
        assert math.isclose(q_left / t_left**3, 10.0, rel_tol=1e-3)

        # Near t=1: (1-q) ~ 10 (1-t)³ → (1-q)/(1-t)³ should approach 10
        t_right = 1.0 - 1e-4
        q_right = smoothstep_C2(np.array([t_right]))[0]
        one_minus_q = 1.0 - q_right
        one_minus_t = 1.0 - t_right
        assert math.isclose(one_minus_q / one_minus_t**3, 10.0, rel_tol=1e-3)

    def test_clips_outside_unit_interval(self):
        assert smoothstep_C2(np.array([-1.0]))[0] == 0.0
        assert smoothstep_C2(np.array([2.0]))[0] == 1.0


# ═══════════════════════════════════════════════════════════════
# §2 — W_R window function
# ═══════════════════════════════════════════════════════════════

class TestWindowWR:
    def test_zero_outside_R_patch(self):
        r = np.array([60.0, 100.0, 500.0])
        W = window_W_R(r, R_patch=50.0)
        assert np.all(W == 0.0)

    def test_unit_inside_r_inner(self):
        r = np.array([0.0, 5.0, 20.0])  # all < 25 = 0.5 × 50
        W = window_W_R(r, R_patch=50.0, r_inner_fraction=0.5)
        assert np.allclose(W, 1.0)

    def test_taper_monotone_decreasing(self):
        r = np.linspace(25.0, 50.0, 100)  # taper region
        W = window_W_R(r, R_patch=50.0, r_inner_fraction=0.5)
        assert np.all(np.diff(W) <= 1e-15)  # non-increasing

    def test_midpoint_is_half(self):
        """At t=1/2 of taper, W = 1 - q(1/2) = 1 - 0.5 = 0.5."""
        r_mid = np.array([37.5])  # 0.5 × (25 + 50)
        W = window_W_R(r_mid, R_patch=50.0, r_inner_fraction=0.5)
        assert math.isclose(W[0], 0.5, abs_tol=1e-14)

    def test_invalid_R_patch_raises(self):
        with pytest.raises(ValueError, match="R_patch"):
            window_W_R(np.array([1.0]), R_patch=-1.0)

    def test_invalid_r_inner_fraction_raises(self):
        with pytest.raises(ValueError, match="r_inner_fraction"):
            window_W_R(np.array([1.0]), R_patch=50.0, r_inner_fraction=1.5)

    def test_max_gradient_formula(self):
        """max |∂_r W| = (15/8) / (R - r_inner)"""
        grad_max = window_W_R_max_gradient(R_patch=50.0, r_inner_fraction=0.5)
        expected = (15.0 / 8.0) / (50.0 * 0.5)
        assert math.isclose(grad_max, expected, rel_tol=1e-14)


# ═══════════════════════════════════════════════════════════════
# §3 — Paper I Prop 5 coefficients
# ═══════════════════════════════════════════════════════════════

class TestProp5Coefficients:
    def test_dipole_from_quadrupole_coefficient(self):
        """T̃_a gets −(4/5) T_ab v^b term."""
        assert PROP5_COEFF_DIPOLE_FROM_QUADRUPOLE == -4.0 / 5.0

    def test_quadrupole_from_dipole_coefficient(self):
        """T̃_ab gets +2 v_⟨a T_b⟩ term."""
        assert PROP5_COEFF_QUADRUPOLE_FROM_DIPOLE == +2.0

    def test_octupole_from_quadrupole_coefficient(self):
        """T̃_abc = 3 T_⟨ab v_c⟩."""
        assert PROP5_COEFF_OCTUPOLE_FROM_QUADRUPOLE == +3.0


# ═══════════════════════════════════════════════════════════════
# §4 — boost_mixing_matrix
# ═══════════════════════════════════════════════════════════════

class TestBoostMixingMatrix:
    def test_identity_at_zero_v(self):
        B = boost_mixing_matrix(v=0.0, ell_max=3)
        assert np.allclose(B, np.eye(4))

    def test_diagonal_is_one(self):
        v = 1e-3
        B = boost_mixing_matrix(v=v, ell_max=3)
        for ell in range(4):
            assert math.isclose(B[ell, ell], 1.0, rel_tol=1e-14)

    def test_dipole_from_quadrupole_entry(self):
        """B[1, 2] = -(4/5) v"""
        v = 1e-3
        B = boost_mixing_matrix(v=v, ell_max=3)
        assert math.isclose(B[1, 2], -4.0 / 5.0 * v, rel_tol=1e-14)

    def test_quadrupole_from_dipole_entry(self):
        """B[2, 1] = +2 v"""
        v = 1e-3
        B = boost_mixing_matrix(v=v, ell_max=3)
        assert math.isclose(B[2, 1], 2.0 * v, rel_tol=1e-14)

    def test_octupole_from_quadrupole_entry(self):
        """B[3, 2] = +3 v"""
        v = 1e-3
        B = boost_mixing_matrix(v=v, ell_max=3)
        assert math.isclose(B[3, 2], 3.0 * v, rel_tol=1e-14)

    def test_invalid_v_raises(self):
        with pytest.raises(ValueError, match="v.*< 1"):
            boost_mixing_matrix(v=1.5, ell_max=3)

    def test_invalid_ell_max_raises(self):
        with pytest.raises(ValueError, match="ell_max"):
            boost_mixing_matrix(v=0.1, ell_max=0)

    def test_ell_max_one_only_has_identity(self):
        """With ell_max=1, only ℓ=0,1 present → no Prop 5 entries above."""
        B = boost_mixing_matrix(v=1e-3, ell_max=1)
        assert B.shape == (2, 2)
        assert np.allclose(B, np.eye(2))


# ═══════════════════════════════════════════════════════════════
# §5 — boost_additive_velocity_terms
# ═══════════════════════════════════════════════════════════════

class TestBoostAdditiveTerms:
    def test_monopole_gets_minus_one_sixth_v_sq(self):
        v = 1e-3
        a = boost_additive_velocity_terms(v=v, ell_max=3)
        assert math.isclose(a[0], -v**2 / 6.0, rel_tol=1e-14)

    def test_dipole_gets_v(self):
        v = 1e-3
        a = boost_additive_velocity_terms(v=v, ell_max=3)
        assert math.isclose(a[1], v, rel_tol=1e-14)

    def test_quadrupole_gets_v_squared(self):
        v = 1e-3
        a = boost_additive_velocity_terms(v=v, ell_max=3)
        assert math.isclose(a[2], v**2, rel_tol=1e-14)

    def test_octupole_gets_nothing(self):
        """Pure-velocity octupole vanishes at this order."""
        a = boost_additive_velocity_terms(v=1e-3, ell_max=3)
        assert a[3] == 0.0


# ═══════════════════════════════════════════════════════════════
# §6 — apply_boost_to_teff (linear consistency)
# ═══════════════════════════════════════════════════════════════

class TestApplyBoost:
    def test_zero_v_is_identity(self):
        T = np.array([1.0, 0.5, 0.2, 0.1])
        T_tilde = apply_boost_to_teff(T, v=0.0)
        assert np.allclose(T_tilde, T)

    def test_dipole_response_at_linear_order(self):
        """T̃_1 = T_1 + v − (4/5) v T_2 at linear order.

        For T = [T_0, 0, T_2, 0] and small v, T̃_1 = v − (4/5) v T_2.
        """
        T_0, T_2 = 1.0, 0.3
        T = np.array([T_0, 0.0, T_2, 0.0])
        v = 1e-4
        T_tilde = apply_boost_to_teff(T, v=v)
        expected_T1 = v - (4.0 / 5.0) * v * T_2
        assert math.isclose(T_tilde[1], expected_T1, rel_tol=1e-10)

    def test_quadrupole_response_at_linear_order(self):
        """T̃_2 = T_2 + 2 v T_1 + v² at leading order.

        For small v, the v² term is subdominant to 2 v T_1 for T_1 ~ O(1).
        """
        T_0, T_1 = 1.0, 0.5
        T = np.array([T_0, T_1, 0.0, 0.0])
        v = 1e-4
        T_tilde = apply_boost_to_teff(T, v=v)
        expected_T2 = 0.0 + 2.0 * v * T_1 + v**2
        assert math.isclose(T_tilde[2], expected_T2, rel_tol=1e-10)

    def test_induced_octupole_from_pure_quadrupole(self):
        """T̃_3 = 3 v T_2 when T_3 = 0 initially."""
        T_2 = 0.4
        T = np.array([1.0, 0.0, T_2, 0.0])
        v = 2e-4
        T_tilde = apply_boost_to_teff(T, v=v)
        assert math.isclose(T_tilde[3], 3.0 * v * T_2, rel_tol=1e-10)


# ═══════════════════════════════════════════════════════════════
# §7 — TiltRouter.route: (effect, channel) pairs
# ═══════════════════════════════════════════════════════════════

class TestTiltRouter:
    def test_global_routes_to_TT_nonzero(self):
        router = TiltRouter(beta_bar=CF4_BETA)
        assert math.isclose(
            router.route(TiltEffect.GLOBAL, Channel.TT), CF4_BETA,
        )

    def test_global_routes_to_EE_nonzero(self):
        """Global cosmological tilt sources Thomson-coupled EE."""
        router = TiltRouter(beta_bar=CF4_BETA)
        assert math.isclose(
            router.route(TiltEffect.GLOBAL, Channel.EE), CF4_BETA,
        )

    def test_global_routes_to_BB_zero(self):
        """Linear baryon-only architecture: no BB from global tilt."""
        router = TiltRouter(beta_bar=CF4_BETA)
        assert router.route(TiltEffect.GLOBAL, Channel.BB) == 0.0

    def test_local_routes_to_TT_nonzero(self):
        v_mag = float(np.linalg.norm(LOCAL_V))
        router = TiltRouter(v_loc=LOCAL_V, R_patch_mpc=R_PATCH_MPC)
        assert math.isclose(
            router.route(TiltEffect.LOCAL, Channel.TT), v_mag,
        )

    def test_local_routes_to_EE_exactly_zero(self):
        """STRUCTURAL: local observer motion does NOT source EE. v_loc large."""
        router = TiltRouter(v_loc=LOCAL_V, R_patch_mpc=R_PATCH_MPC)
        assert router.route(TiltEffect.LOCAL, Channel.EE) == 0.0

    def test_local_routes_to_TE_zero(self):
        router = TiltRouter(v_loc=LOCAL_V, R_patch_mpc=R_PATCH_MPC)
        assert router.route(TiltEffect.LOCAL, Channel.TE) == 0.0

    def test_local_routes_to_BB_zero(self):
        router = TiltRouter(v_loc=LOCAL_V, R_patch_mpc=R_PATCH_MPC)
        assert router.route(TiltEffect.LOCAL, Channel.BB) == 0.0


# ═══════════════════════════════════════════════════════════════
# §8 — enforce_local_EE_zero sentinel
# ═══════════════════════════════════════════════════════════════

class TestEnforceLocalEEZero:
    def test_passes_for_zero_local(self):
        router = make_global_only_router(CF4_BETA)
        router.enforce_local_EE_zero()  # should not raise

    def test_passes_for_nonzero_local_with_architectural_zero_EE(self):
        """Even with |v_loc| large, route(LOCAL, EE) should return 0."""
        router = make_local_only_router(LOCAL_V, R_patch_mpc=R_PATCH_MPC)
        router.enforce_local_EE_zero()  # architecture enforces zero


# ═══════════════════════════════════════════════════════════════
# §9 — apply_local_boost vs apply_global_tilt
# ═══════════════════════════════════════════════════════════════

class TestBoostApplication:
    def test_local_boost_uses_v_loc_magnitude(self):
        T = np.array([1.0, 0.5, 0.2, 0.1])
        v_loc = np.array([1e-4, 0.0, 0.0])
        router = TiltRouter(v_loc=v_loc, R_patch_mpc=R_PATCH_MPC)
        T_tilde_router = router.apply_local_boost(T)
        T_tilde_direct = apply_boost_to_teff(T, v=1e-4)
        assert np.allclose(T_tilde_router, T_tilde_direct)

    def test_global_tilt_uses_beta_bar(self):
        T = np.array([1.0, 0.5, 0.2, 0.1])
        router = make_global_only_router(beta_bar=2e-3)
        T_tilde_router = router.apply_global_tilt(T)
        T_tilde_direct = apply_boost_to_teff(T, v=2e-3)
        assert np.allclose(T_tilde_router, T_tilde_direct)

    def test_local_vs_global_use_different_v_values(self):
        """Local and global should give different results in combined router."""
        T = np.array([1.0, 0.5, 0.2, 0.1])
        router = make_combined_router(
            beta_bar=1e-3, v_loc=np.array([5e-4, 0, 0]),
            R_patch_mpc=R_PATCH_MPC,
        )
        T_tilde_local = router.apply_local_boost(T)
        T_tilde_global = router.apply_global_tilt(T)
        assert not np.allclose(T_tilde_local, T_tilde_global)


# ═══════════════════════════════════════════════════════════════
# §10 — Combined router
# ═══════════════════════════════════════════════════════════════

class TestCombinedRouter:
    def test_both_active(self):
        router = make_combined_router(
            beta_bar=CF4_BETA, v_loc=LOCAL_V, R_patch_mpc=R_PATCH_MPC,
        )
        assert router.is_global_active()
        assert router.is_local_active()

    def test_combined_TT_has_both_contributions(self):
        """Both global and local contribute to TT channel."""
        router = make_combined_router(
            beta_bar=CF4_BETA, v_loc=LOCAL_V, R_patch_mpc=R_PATCH_MPC,
        )
        assert router.route(TiltEffect.GLOBAL, Channel.TT) > 0
        assert router.route(TiltEffect.LOCAL, Channel.TT) > 0

    def test_combined_EE_only_has_global_contribution(self):
        """Only global contributes to EE; local is ENFORCED zero."""
        router = make_combined_router(
            beta_bar=CF4_BETA, v_loc=LOCAL_V, R_patch_mpc=R_PATCH_MPC,
        )
        assert router.route(TiltEffect.GLOBAL, Channel.EE) > 0
        assert router.route(TiltEffect.LOCAL, Channel.EE) == 0.0

    def test_window_accessible_when_R_patch_set(self):
        router = make_combined_router(
            beta_bar=CF4_BETA, v_loc=LOCAL_V, R_patch_mpc=R_PATCH_MPC,
        )
        r = np.array([0.0, 25.0, 50.0, 100.0])
        W = router.window(r)
        assert W[0] == 1.0
        assert W[-1] == 0.0

    def test_window_raises_when_R_patch_not_set(self):
        router = make_global_only_router(CF4_BETA)  # R_patch_mpc=None
        with pytest.raises(ValueError, match="R_patch_mpc"):
            router.window(np.array([1.0]))


# ═══════════════════════════════════════════════════════════════
# §11 — Factory functions
# ═══════════════════════════════════════════════════════════════

class TestFactories:
    def test_global_only_factory(self):
        router = make_global_only_router(CF4_BETA)
        assert router.is_global_active()
        assert not router.is_local_active()

    def test_local_only_factory(self):
        router = make_local_only_router(LOCAL_V, R_patch_mpc=R_PATCH_MPC)
        assert not router.is_global_active()
        assert router.is_local_active()
        assert router.R_patch_mpc == R_PATCH_MPC

    def test_combined_factory_all_fields_set(self):
        router = make_combined_router(
            beta_bar=CF4_BETA, v_loc=LOCAL_V, R_patch_mpc=R_PATCH_MPC,
        )
        assert router.beta_bar == CF4_BETA
        assert np.allclose(router.v_loc, LOCAL_V)
        assert router.R_patch_mpc == R_PATCH_MPC

    def test_summary_structure(self):
        router = make_combined_router(
            beta_bar=CF4_BETA, v_loc=LOCAL_V, R_patch_mpc=R_PATCH_MPC,
        )
        summary = router.summary()
        assert summary['global_active'] is True
        assert summary['local_active'] is True
        assert 'routing' in summary
        assert 'global-TT' in summary['routing']
        assert 'local-EE' in summary['routing']
        assert summary['routing']['local-EE'] == 0.0
