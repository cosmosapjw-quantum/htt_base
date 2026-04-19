"""
tests/test_boost_perturbative.py
=================================

Week 2 Day 4 test suite for Paper I perturbative boost + Thm 3 verification.

Covers:
  §1 — Aberration formula round-trip and edge cases
  §2 — Doppler factor: isotropic, small-v, γ-factor match
  §3 — Spatial boost `boost_theta_axisymmetric`: coefficient values match analytic
  §4 — Multipole-space boost `boost_multipoles_prop5`: dimensional correctness
  §5 — Thm 3 consistency check: isotropic Θ at multiple v values
  §6 — Order convergence: O(v²) for order=1, O(v³) for order=2
  §7 — Statistics independence (Thm 3 holds for BE/FD/MB)
  §8 — v = 0 invariance (identity)
  §9 — Thm3Result properties
  §10 — Edge cases (|v| ≥ 1 raises, wrong order raises)

Run
---
    pytest test_boost_perturbative.py -v
"""
from __future__ import annotations

import math
import numpy as np
import pytest

from tsc.charts.boost_perturbative import (
    relativistic_aberration_mu, doppler_factor,
    boost_theta_axisymmetric, boost_multipoles_prop5,
    thm3_consistency_check, boost_order_convergence,
    Thm3Result,
)
from tsc.charts.forward_F_to_T import (
    AxisymmetricField,
    isotropic_theta, dipole_theta, quadrupole_theta,
    axisymmetric_F,
)


# ═══════════════════════════════════════════════════════════════
# §1 — Relativistic aberration
# ═══════════════════════════════════════════════════════════════

class TestRelativisticAberration:
    def test_aberration_roundtrip(self):
        """μ → μ'(via forward) → μ (via inverse) should be identity."""
        mu_orig = np.array([-0.9, -0.5, 0.0, 0.5, 0.9])
        v = 0.1
        mu_prime = (mu_orig + v) / (1.0 + v * mu_orig)
        mu_recovered = relativistic_aberration_mu(mu_prime, v)
        assert np.allclose(mu_orig, mu_recovered, atol=1e-14)

    def test_aberration_at_zero_v(self):
        """v = 0 should give μ(μ') = μ'."""
        mu_prime = np.array([-0.5, 0.0, 0.5])
        mu = relativistic_aberration_mu(mu_prime, v=0.0)
        assert np.allclose(mu, mu_prime, atol=1e-15)

    def test_aberration_preserves_endpoints(self):
        """μ' = 1 (forward ẑ) maps to μ = 1 exactly (regardless of v)."""
        assert math.isclose(
            float(relativistic_aberration_mu(np.array([1.0]), v=0.5)[0]), 1.0
        )

    def test_superluminal_v_raises(self):
        with pytest.raises(ValueError, match=r"\|v\|"):
            relativistic_aberration_mu(np.array([0.0]), v=1.5)

    def test_v_exactly_c_raises(self):
        with pytest.raises(ValueError, match=r"\|v\|"):
            relativistic_aberration_mu(np.array([0.0]), v=1.0)


# ═══════════════════════════════════════════════════════════════
# §2 — Doppler factor
# ═══════════════════════════════════════════════════════════════

class TestDopplerFactor:
    def test_doppler_at_zero_v(self):
        """v = 0 should give D = 1."""
        D = doppler_factor(np.array([-0.5, 0.0, 0.5]), v=0.0)
        assert np.allclose(D, 1.0, atol=1e-15)

    def test_doppler_blueshift_at_mu_positive(self):
        """μ' > 0 (forward) + v > 0 → blueshift (D > 1)."""
        D = doppler_factor(np.array([0.5]), v=0.1)
        assert D[0] > 1.0

    def test_doppler_redshift_at_mu_negative(self):
        """μ' < 0 (backward) + v > 0 → redshift (D < 1)."""
        D = doppler_factor(np.array([-0.5]), v=0.1)
        assert D[0] < 1.0

    def test_doppler_linear_order_in_v(self):
        """D(μ, v) ≈ 1 + v μ at O(v)."""
        mu_prime = 0.3
        v = 1e-4
        D = doppler_factor(np.array([mu_prime]), v)[0]
        linear_approx = 1.0 + v * mu_prime
        assert math.isclose(D, linear_approx, rel_tol=1e-6)


# ═══════════════════════════════════════════════════════════════
# §3 — Spatial boost on axisymmetric Θ field
# ═══════════════════════════════════════════════════════════════

class TestSpatialBoost:
    """Verify analytic Legendre coefficients for isotropic Θ = 1 boost."""

    def test_isotropic_coeffs_at_small_v(self):
        """For isotropic Θ_0 = 1, boost by v gives:
            Θ'_0 = 1 - v²/6 + O(v⁴)
            Θ'_1 = v + v³/10 + O(v⁵)
            Θ'_2 = (2/3) v² + O(v⁴)
            Θ'_3 = (2/5) v³ + O(v⁵)
        """
        v = 0.001
        Theta_boosted = boost_theta_axisymmetric(isotropic_theta(1.0), v)
        # Θ_0 ≈ 1 - v²/6
        assert math.isclose(
            Theta_boosted.coeffs[0], 1.0 - v ** 2 / 6.0, rel_tol=1e-9
        )
        # Θ_1 ≈ v (leading order)
        assert math.isclose(Theta_boosted.coeffs[1], v, rel_tol=1e-5)
        # Θ_2 ≈ (2/3) v²
        assert math.isclose(
            Theta_boosted.coeffs[2], (2.0 / 3.0) * v ** 2, rel_tol=1e-5
        )
        # Θ_3 ≈ (2/5) v³
        assert math.isclose(
            Theta_boosted.coeffs[3], (2.0 / 5.0) * v ** 3, rel_tol=1e-3
        )

    def test_v_zero_preserves_field(self):
        """No boost → same field."""
        Theta = dipole_theta(1.0, 0.01)
        Theta_boosted = boost_theta_axisymmetric(Theta, v=0.0, L_max_out=3)
        assert np.allclose(
            Theta_boosted.coeffs[: Theta.L_max + 1], Theta.coeffs, atol=1e-12
        )

    def test_superluminal_v_raises(self):
        with pytest.raises(ValueError, match=r"\|v\|"):
            boost_theta_axisymmetric(isotropic_theta(1.0), v=2.0)

    def test_output_is_axisymmetric_field(self):
        result = boost_theta_axisymmetric(isotropic_theta(1.0), v=0.01)
        assert isinstance(result, AxisymmetricField)
        assert result.L_max >= 3

    def test_boost_of_dipole_input(self):
        """Boosting Θ = 1 + 0.01 P_1(μ) by small v should produce recognizable
        mixture that still has dominant dipole structure."""
        v = 1e-3
        Theta = dipole_theta(1.0, 0.01)
        Theta_boosted = boost_theta_axisymmetric(Theta, v)
        # Dipole should shift by roughly v (boost) + existing 0.01
        assert Theta_boosted.coeffs[1] > 0.005


# ═══════════════════════════════════════════════════════════════
# §4 — Multipole-space boost with dimensional convention
# ═══════════════════════════════════════════════════════════════

class TestMultipoleBoost:
    def test_v_zero_identity(self):
        """v = 0 → T_prime = T_ell."""
        T = np.array([6.0, 0.1, 0.05, 0.01])
        T_prime = boost_multipoles_prop5(T, v=0.0, moment_order=3, order=2)
        assert np.allclose(T_prime, T, atol=1e-14)

    def test_dipole_additive_magnitude(self):
        """For isotropic T_0 = 6 (MB), boost gives ΔT_1 = (n+1) T_0 v = 24v."""
        T_iso = np.array([6.0, 0.0, 0.0, 0.0])
        v = 1e-3
        T_prime = boost_multipoles_prop5(T_iso, v, moment_order=3, order=1)
        assert math.isclose(T_prime[1], 24.0 * v, rel_tol=1e-10)

    def test_monopole_shift_at_order_2(self):
        """At order=2, T_0 gets (-(n+1)/6 + n(n+1)/6) × T_0 × v² = (n+1)²/6 × T_0 × v²
        Wait: that's -(n+1)/6 + (n(n+1)/2) × (1/3) = -(n+1)/6 + n(n+1)/6 = (n-1)(n+1)/6
        For n=3: (3-1)(3+1)/6 = 8/6 = 4/3. So T_0' = T_0 × (1 + 4/3 × v²).
        """
        T_iso = np.array([6.0, 0.0, 0.0])
        v = 1e-3
        T_prime = boost_multipoles_prop5(T_iso, v, moment_order=3, order=2)
        # Expected net shift: (n-1)(n+1)/6 × T_0 × v² = (8/6) × 6 × 1e-6 = 8e-6
        expected_shift = (8.0 / 6.0) * 6.0 * v ** 2
        actual_shift = T_prime[0] - 6.0
        assert math.isclose(actual_shift, expected_shift, rel_tol=1e-10)

    def test_quadrupole_induced_at_order_2(self):
        """For isotropic T_0 = 6, ΔT_2 = [(2/3)(n+1) + n(n+1)(2/6)] T_0 v²
        = [8/3 + 4] × 6 × v² = (20/3) × 6 × v² = 40 v²"""
        T_iso = np.array([6.0, 0.0, 0.0])
        v = 1e-3
        T_prime = boost_multipoles_prop5(T_iso, v, moment_order=3, order=2)
        expected = 40.0 * v ** 2
        assert math.isclose(T_prime[2], expected, rel_tol=1e-10)

    def test_invalid_order_raises(self):
        T = np.array([6.0, 0.0, 0.0])
        with pytest.raises(ValueError, match="order"):
            boost_multipoles_prop5(T, v=0.01, order=3)

    def test_moment_order_scaling(self):
        """ΔT_1 = (n+1) T_0 v scales as (n+1)."""
        T_iso = np.array([6.0, 0.0, 0.0])
        v = 1e-3
        T_n3 = boost_multipoles_prop5(T_iso, v, moment_order=3, order=1)
        T_n4 = boost_multipoles_prop5(T_iso, v, moment_order=4, order=1)
        ratio = T_n4[1] / T_n3[1]
        assert math.isclose(ratio, 5.0 / 4.0, rel_tol=1e-10)


# ═══════════════════════════════════════════════════════════════
# §5 — Thm 3 consistency check
# ═══════════════════════════════════════════════════════════════

class TestThm3Consistency:
    """Paper I Thm 3: for one-field (η=0), Path 1 (spatial) = Path 2 (multipole)."""

    def test_isotropic_input_small_v_agrees(self):
        """At v = 1e-4, rel_residual should be < 10⁻⁸ for isotropic input."""
        r = thm3_consistency_check(isotropic_theta(1.0), v=1e-4,
                                    xi=0, L_compare=2, boost_order=2)
        assert r.relative_residual < 1e-8

    def test_isotropic_input_moderate_v(self):
        """At v = 1e-3, residual should be in the 10⁻⁹ range for order=2."""
        r = thm3_consistency_check(isotropic_theta(1.0), v=1e-3,
                                    xi=0, L_compare=2, boost_order=2)
        assert r.relative_residual < 1e-8

    def test_result_contains_both_paths(self):
        r = thm3_consistency_check(isotropic_theta(1.0), v=1e-3, xi=0,
                                    L_compare=2, boost_order=2)
        assert r.T_ell_spatial.shape == (3,)  # L_compare + 1
        assert r.T_ell_multipole.shape == (3,)
        assert r.residual.shape == (3,)


# ═══════════════════════════════════════════════════════════════
# §6 — Order convergence (critical Day 4 correctness check)
# ═══════════════════════════════════════════════════════════════

class TestOrderConvergence:
    """Residual ‖Path 1 − Path 2‖ should scale as v^{order+1}."""

    def test_order_1_residual_scales_as_v_squared(self):
        """order=1 → residual ∝ v² (next-order term is v²)."""
        v_list = [1e-4, 1e-3]
        results = boost_order_convergence(
            isotropic_theta(1.0), v_list, xi=0, boost_order=1,
        )
        ratio = results[1].residual_norm / results[0].residual_norm
        # v factor 10 → residual factor 100 for O(v²)
        assert 80 < ratio < 150, (
            f"order=1 ratio = {ratio}, expected ~100"
        )

    def test_order_2_residual_scales_as_v_cubed(self):
        """order=2 → residual ∝ v³ (next-order term is v³)."""
        v_list = [1e-3, 1e-2]
        results = boost_order_convergence(
            isotropic_theta(1.0), v_list, xi=0, boost_order=2,
        )
        ratio = results[1].residual_norm / results[0].residual_norm
        # v factor 10 → residual factor 1000 for O(v³)
        assert 800 < ratio < 1500, (
            f"order=2 ratio = {ratio}, expected ~1000"
        )

    def test_order_2_at_v_3e_minus_2(self):
        """At v = 3e-2 still within perturbative regime for order=2."""
        v_list = [1e-2, 3e-2]
        results = boost_order_convergence(
            isotropic_theta(1.0), v_list, xi=0, boost_order=2,
        )
        ratio = results[1].residual_norm / results[0].residual_norm
        # v factor 3 → residual factor 27 for O(v³)
        assert 20 < ratio < 35, (
            f"v factor 3 ratio = {ratio}, expected ~27"
        )


# ═══════════════════════════════════════════════════════════════
# §7 — Statistics independence (Thm 3 universality)
# ═══════════════════════════════════════════════════════════════

class TestStatisticsIndependence:
    """Paper I Thm 3 holds for all ξ — same residual magnitude."""

    def test_all_statistics_same_residual(self):
        v = 1e-3
        residuals = {}
        for xi in [-1, 0, +1]:
            r = thm3_consistency_check(isotropic_theta(1.0), v=v,
                                        xi=xi, L_compare=2, boost_order=2)
            residuals[xi] = r.relative_residual
        # All three should agree to ~5 significant figures (only I_n scale differs)
        ref = residuals[0]
        for xi, val in residuals.items():
            assert math.isclose(val, ref, rel_tol=5e-3), (
                f"ξ={xi}: {val} vs ref {ref}"
            )


# ═══════════════════════════════════════════════════════════════
# §8 — Thm3Result properties
# ═══════════════════════════════════════════════════════════════

class TestThm3Result:
    def test_residual_norm_property(self):
        r = thm3_consistency_check(isotropic_theta(1.0), v=1e-3, xi=0,
                                    L_compare=2, boost_order=2)
        assert r.residual_norm == pytest.approx(np.linalg.norm(r.residual))

    def test_spatial_norm_property(self):
        r = thm3_consistency_check(isotropic_theta(1.0), v=1e-3, xi=0,
                                    L_compare=2, boost_order=2)
        assert r.spatial_norm == pytest.approx(np.linalg.norm(r.T_ell_spatial))

    def test_L_compare_attribute(self):
        r = thm3_consistency_check(isotropic_theta(1.0), v=1e-3, xi=0,
                                    L_compare=3, boost_order=2)
        assert r.L_compare == 3
        assert len(r.T_ell_spatial) == 4

    def test_v_and_xi_preserved(self):
        r = thm3_consistency_check(isotropic_theta(1.0), v=5e-3, xi=+1,
                                    L_compare=2, boost_order=2)
        assert r.v == 5e-3
        assert r.xi == +1


# ═══════════════════════════════════════════════════════════════
# §9 — Edge cases
# ═══════════════════════════════════════════════════════════════

class TestEdgeCases:
    def test_boost_with_moment_order_2(self):
        """Use n=2 (number moment) instead of default n=3 (energy)."""
        T = np.array([2.0, 0.0, 0.0])  # n=2: T_0 = I_2(MB) = 2
        v = 1e-3
        T_prime = boost_multipoles_prop5(T, v, moment_order=2, order=1)
        # ΔT_1 = (n+1) T_0 v = 3 × 2 × v = 6v
        assert math.isclose(T_prime[1], 6.0 * v, rel_tol=1e-10)

    def test_doppler_superluminal_raises(self):
        with pytest.raises(ValueError, match=r"\|v\|"):
            doppler_factor(np.array([0.5]), v=2.0)

    def test_boost_zero_v_doesnt_raise(self):
        """v = 0 explicitly allowed (identity transformation)."""
        r = boost_theta_axisymmetric(isotropic_theta(1.0), v=0.0)
        assert r is not None
