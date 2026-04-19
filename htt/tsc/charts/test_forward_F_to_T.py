"""
tests/test_forward_F_to_T.py
=============================

Week 2 Day 2 test suite for the Paper I forward map F.

Covers:
  §1 — AxisymmetricField construction and evaluation
  §2 — Admissibility checks (Θ > 0, BE η ≤ 0)
  §3 — Isotropic limit: T_0 = Θ_0^{n+1} I_n, higher T_ℓ = 0
  §4 — Dipole response: linear prediction matches at O(Θ_1)
  §5 — Quadrupole response: linear prediction matches at O(Θ_2)
  §6 — Parity (dipole input → no quadrupole at linear order)
  §7 — Moment order variation (n = 2, 3, 4)
  §8 — Statistics comparison (BE/FD/MB at same Θ)
  §9 — Linear response cross-check vs full nonlinear
  §10 — ForwardResult property access
  §11 — General 3D stub raises NotImplementedError

Run
---
    pytest test_forward_F_to_T.py -v
"""
from __future__ import annotations

import math
import numpy as np
import pytest

from tsc.charts.forward_F_to_T import (
    AxisymmetricField,
    isotropic_theta, dipole_theta, quadrupole_theta,
    check_theta_positive, check_be_admissibility,
    axisymmetric_F, isotropic_limit_T0, linear_response_F,
    general_F_stub,
    ForwardResult,
)
from tsc.charts.laguerre_basis import xi_moment


# ═══════════════════════════════════════════════════════════════
# §1 — AxisymmetricField construction
# ═══════════════════════════════════════════════════════════════

class TestAxisymmetricField:
    def test_construct_from_array(self):
        f = AxisymmetricField(coeffs=np.array([1.0, 0.5, 0.1]))
        assert f.L_max == 2

    def test_L_max_for_monopole_only(self):
        f = AxisymmetricField(coeffs=np.array([1.0]))
        assert f.L_max == 0

    def test_2d_array_raises(self):
        with pytest.raises(ValueError, match="1D"):
            AxisymmetricField(coeffs=np.array([[1.0, 2.0], [3.0, 4.0]]))

    def test_evaluate_monopole(self):
        """Θ = Θ_0 → Θ(μ) = Θ_0 for all μ."""
        f = AxisymmetricField(coeffs=np.array([2.5]))
        mu = np.linspace(-1, 1, 10)
        assert np.allclose(f.evaluate(mu), 2.5)

    def test_evaluate_dipole(self):
        """Θ = Θ_0 + Θ_1 P_1(μ) = Θ_0 + Θ_1 μ."""
        f = AxisymmetricField(coeffs=np.array([1.0, 0.3]))
        mu = np.array([-1.0, 0.0, 1.0])
        expected = np.array([1.0 - 0.3, 1.0, 1.0 + 0.3])
        assert np.allclose(f.evaluate(mu), expected)

    def test_factory_isotropic(self):
        Theta = isotropic_theta(3.0)
        assert np.allclose(Theta.evaluate(np.linspace(-1, 1, 5)), 3.0)

    def test_factory_quadrupole(self):
        Theta = quadrupole_theta(1.0, 0.1)
        # P_2(μ) = (3μ² - 1)/2
        # At μ = 0: P_2 = -1/2 → Θ = 1 - 0.05 = 0.95
        # At μ = 1: P_2 = 1 → Θ = 1.1
        assert math.isclose(Theta.evaluate(np.array([0.0]))[0], 0.95)
        assert math.isclose(Theta.evaluate(np.array([1.0]))[0], 1.1)

    def test_factory_dipole(self):
        Theta = dipole_theta(1.0, 0.2)
        # P_1(μ) = μ
        assert math.isclose(Theta.evaluate(np.array([0.5]))[0], 1.1)


# ═══════════════════════════════════════════════════════════════
# §2 — Admissibility
# ═══════════════════════════════════════════════════════════════

class TestAdmissibility:
    def test_positive_theta_passes(self):
        assert check_theta_positive(isotropic_theta(1.0))

    def test_negative_theta_fails(self):
        Theta = isotropic_theta(-0.5)
        assert not check_theta_positive(Theta)

    def test_marginally_positive_theta(self):
        """Θ = 1 + P_1(μ) → zero at μ = -1."""
        Theta = dipole_theta(1.0, 1.0)
        # At μ = -1, Θ = 0 (boundary of admissible)
        assert not check_theta_positive(Theta)

    def test_be_admissibility_none_eta(self):
        """η = None means one-field, trivially admissible."""
        assert check_be_admissibility(None)

    def test_be_admissibility_zero_eta(self):
        eta = AxisymmetricField(coeffs=np.array([0.0]))
        assert check_be_admissibility(eta)

    def test_be_admissibility_negative_eta(self):
        eta = AxisymmetricField(coeffs=np.array([-0.5]))
        assert check_be_admissibility(eta)

    def test_be_admissibility_positive_eta_fails(self):
        eta = AxisymmetricField(coeffs=np.array([0.5]))
        assert not check_be_admissibility(eta)


# ═══════════════════════════════════════════════════════════════
# §3 — Isotropic limit (the canonical sanity check)
# ═══════════════════════════════════════════════════════════════

class TestIsotropicLimit:
    @pytest.mark.parametrize("xi", [-1, 0, +1])
    def test_isotropic_T0_matches_I_n(self, xi):
        """For Θ ≡ 1: T_0 = I_n(ξ, 0)."""
        result = axisymmetric_F(xi, isotropic_theta(1.0), L_out=3)
        expected = xi_moment(3, xi, 0.0)
        assert math.isclose(result.T_0, expected, rel_tol=1e-10)

    @pytest.mark.parametrize("xi", [-1, 0, +1])
    def test_isotropic_higher_multipoles_vanish(self, xi):
        """For Θ ≡ 1, T_ℓ = 0 for ℓ ≥ 1."""
        result = axisymmetric_F(xi, isotropic_theta(1.0), L_out=3)
        assert abs(result.T_1) < 1e-13
        assert abs(result.T_2) < 1e-13
        assert abs(result.T_3) < 1e-13

    def test_isotropic_Theta_scaling(self):
        """T_0 ∝ Θ_0^{n+1}."""
        Theta_vals = [0.5, 1.0, 2.0, 3.0]
        for T0 in Theta_vals:
            result = axisymmetric_F(0, isotropic_theta(T0), L_out=0)
            expected = T0 ** 4 * xi_moment(3, 0, 0.0)  # MB: I_3 = 6
            assert math.isclose(result.T_0, expected, rel_tol=1e-10)

    @pytest.mark.parametrize("xi", [-1, 0, +1])
    def test_isotropic_limit_helper_matches(self, xi):
        result = axisymmetric_F(xi, isotropic_theta(1.5), L_out=0)
        expected = isotropic_limit_T0(xi, Theta_0=1.5)
        assert math.isclose(result.T_0, expected, rel_tol=1e-10)


# ═══════════════════════════════════════════════════════════════
# §4 — Dipole response (linear)
# ═══════════════════════════════════════════════════════════════

class TestDipoleResponse:
    """For Θ = Θ_0 + δ P_1(μ), linear prediction: T_1 = (n+1) Θ_0^n × δ × I_n."""

    def test_MB_dipole_T1(self):
        """MB: T_1 ≈ 4 × 1 × 0.01 × 6 = 0.24."""
        Theta = dipole_theta(1.0, 0.01)
        result = axisymmetric_F(0, Theta, L_out=3)
        expected = 4 * 1**3 * 0.01 * 6.0
        assert math.isclose(result.T_1, expected, rel_tol=5e-3)

    def test_BE_dipole_T1(self):
        """BE: T_1 ≈ 4 × 1 × 0.01 × I_3(BE) ≈ 0.2598."""
        Theta = dipole_theta(1.0, 0.01)
        result = axisymmetric_F(+1, Theta, L_out=3)
        expected = 4 * 1**3 * 0.01 * xi_moment(3, +1, 0.0)
        assert math.isclose(result.T_1, expected, rel_tol=5e-3)

    def test_FD_dipole_T1(self):
        Theta = dipole_theta(1.0, 0.01)
        result = axisymmetric_F(-1, Theta, L_out=3)
        expected = 4 * 1**3 * 0.01 * xi_moment(3, -1, 0.0)
        assert math.isclose(result.T_1, expected, rel_tol=5e-3)

    def test_dipole_input_no_odd_quadrupole(self):
        """Θ_1 input → T_2 is O(Θ_1²) (small), not O(Θ_1)."""
        Theta = dipole_theta(1.0, 0.01)
        result = axisymmetric_F(0, Theta, L_out=3)
        # T_2 should be much smaller than T_1
        assert abs(result.T_2) < 0.1 * abs(result.T_1)


# ═══════════════════════════════════════════════════════════════
# §5 — Quadrupole response (linear)
# ═══════════════════════════════════════════════════════════════

class TestQuadrupoleResponse:
    """For Θ = Θ_0 + δ P_2(μ), linear: T_2 = (n+1) Θ_0^n × δ × I_n."""

    def test_MB_quadrupole_T2(self):
        Theta = quadrupole_theta(1.0, 0.01)
        result = axisymmetric_F(0, Theta, L_out=3)
        expected = 4 * 1**3 * 0.01 * 6.0  # = 0.24
        assert math.isclose(result.T_2, expected, rel_tol=1e-2)

    def test_quadrupole_input_no_dipole(self):
        """Θ_2 input → T_1 = 0 (parity)."""
        Theta = quadrupole_theta(1.0, 0.01)
        result = axisymmetric_F(0, Theta, L_out=3)
        assert abs(result.T_1) < 1e-12

    def test_quadrupole_T3_vanishes_linear(self):
        """Θ_2 × P_2 source has no ℓ=3 projection at O(Θ_2)."""
        Theta = quadrupole_theta(1.0, 0.01)
        result = axisymmetric_F(0, Theta, L_out=3)
        # T_3 should be O(Θ_2²) at most
        assert abs(result.T_3) < 0.01 * abs(result.T_2)


# ═══════════════════════════════════════════════════════════════
# §6 — Moment order variation
# ═══════════════════════════════════════════════════════════════

class TestMomentOrder:
    def test_MB_moment_order_2(self):
        """n=2: I_2^MB = Γ(3) = 2."""
        result = axisymmetric_F(0, isotropic_theta(1.0),
                                L_out=0, moment_order=2)
        assert math.isclose(result.T_0, 2.0, rel_tol=1e-10)

    def test_MB_moment_order_3(self):
        """n=3: I_3^MB = Γ(4) = 6."""
        result = axisymmetric_F(0, isotropic_theta(1.0),
                                L_out=0, moment_order=3)
        assert math.isclose(result.T_0, 6.0, rel_tol=1e-10)

    def test_MB_moment_order_4(self):
        """n=4: I_4^MB = Γ(5) = 24."""
        result = axisymmetric_F(0, isotropic_theta(1.0),
                                L_out=0, moment_order=4)
        assert math.isclose(result.T_0, 24.0, rel_tol=1e-10)

    def test_invalid_moment_order_raises(self):
        with pytest.raises(ValueError, match="moment_order"):
            axisymmetric_F(0, isotropic_theta(1.0), moment_order=5)


# ═══════════════════════════════════════════════════════════════
# §7 — Statistics comparison
# ═══════════════════════════════════════════════════════════════

class TestStatisticsComparison:
    def test_BE_vs_FD_at_same_Theta(self):
        """BE and FD give different T_0 at same Θ."""
        Theta = isotropic_theta(1.0)
        r_BE = axisymmetric_F(+1, Theta, L_out=0)
        r_FD = axisymmetric_F(-1, Theta, L_out=0)
        r_MB = axisymmetric_F(0, Theta, L_out=0)
        # Expected: FD < MB < BE (from I_3 values: 5.68 < 6.0 < 6.49)
        assert r_FD.T_0 < r_MB.T_0 < r_BE.T_0

    def test_T1_ratios_across_statistics(self):
        """T_1(BE)/T_1(MB) = I_3(BE)/I_3(MB) at fixed Θ_1."""
        Theta = dipole_theta(1.0, 0.001)
        r_BE = axisymmetric_F(+1, Theta, L_out=1)
        r_MB = axisymmetric_F(0, Theta, L_out=1)
        ratio_measured = r_BE.T_1 / r_MB.T_1
        ratio_expected = xi_moment(3, +1, 0.0) / xi_moment(3, 0, 0.0)
        # = π⁴/90 ≈ 1.0823
        assert math.isclose(ratio_measured, ratio_expected, rel_tol=1e-3)


# ═══════════════════════════════════════════════════════════════
# §8 — Linear response cross-check
# ═══════════════════════════════════════════════════════════════

class TestLinearResponseCrossCheck:
    def test_linear_response_matches_full_at_small_perturbation(self):
        """At very small Θ_1, full nonlinear ≈ linear response."""
        Theta_0 = 1.0
        Theta_1 = 1e-5  # small perturbation
        Theta = dipole_theta(Theta_0, Theta_1)
        full_result = axisymmetric_F(0, Theta, L_out=2)
        linear_result = linear_response_F(0, Theta_0, np.array([Theta_1]))
        # T_0 and T_1 should agree to O(Θ_1²) ~ 10⁻¹⁰
        assert math.isclose(full_result.T_0, linear_result[0], rel_tol=1e-8)
        assert math.isclose(full_result.T_1, linear_result[1], rel_tol=1e-4)

    def test_linear_response_formula_MB(self):
        """linear_response_F for MB, Θ_0 = 1, Θ_1 = 0.1: T_1 = 4 × 1 × 0.1 × 6 = 2.4."""
        T_lin = linear_response_F(0, Theta_0=1.0,
                                  Theta_ell_in=np.array([0.1]))
        assert math.isclose(T_lin[1], 2.4, rel_tol=1e-14)


# ═══════════════════════════════════════════════════════════════
# §9 — ForwardResult property access
# ═══════════════════════════════════════════════════════════════

class TestForwardResult:
    def test_result_properties(self):
        Theta = quadrupole_theta(1.0, 0.05)
        result = axisymmetric_F(0, Theta, L_out=3)
        assert isinstance(result.T_0, float)
        assert isinstance(result.T_1, float)
        assert isinstance(result.T_2, float)
        assert isinstance(result.T_3, float)

    def test_result_T_ell_array_shape(self):
        result = axisymmetric_F(0, isotropic_theta(1.0), L_out=3)
        assert result.T_ell.shape == (4,)

    def test_low_L_out_missing_higher_multipoles(self):
        """L_out=1 → T_2 and T_3 return 0 as fallback."""
        result = axisymmetric_F(0, isotropic_theta(1.0), L_out=1)
        assert result.T_2 == 0.0
        assert result.T_3 == 0.0


# ═══════════════════════════════════════════════════════════════
# §10 — Admissibility failures in F
# ═══════════════════════════════════════════════════════════════

class TestFAdmissibility:
    def test_negative_Theta_raises(self):
        Theta = AxisymmetricField(coeffs=np.array([-1.0]))
        with pytest.raises(ValueError, match="positive"):
            axisymmetric_F(0, Theta)

    def test_BE_positive_eta_raises(self):
        Theta = isotropic_theta(1.0)
        eta = AxisymmetricField(coeffs=np.array([0.5]))
        with pytest.raises(ValueError, match="BE requires"):
            axisymmetric_F(+1, Theta, eta=eta)

    def test_invalid_xi_raises(self):
        with pytest.raises(ValueError, match="ξ"):
            axisymmetric_F(5, isotropic_theta(1.0))

    def test_disable_admissibility_check_for_theta(self):
        """With check_admissibility=False, F runs for Θ < 0 (unphysical but
        numerically computable). BE admissibility (η ≤ 0) is always enforced
        at xi_moment level regardless — defense-in-depth.
        """
        Theta = AxisymmetricField(coeffs=np.array([-1.0]))  # unphysical
        result = axisymmetric_F(0, Theta, check_admissibility=False)
        # Should produce some finite value (may be unphysical)
        assert np.isfinite(result.T_0)


# ═══════════════════════════════════════════════════════════════
# §11 — General 3D stub
# ═══════════════════════════════════════════════════════════════

class TestGeneral3DStub:
    def test_stub_raises_not_implemented(self):
        with pytest.raises(NotImplementedError, match="Week 3"):
            general_F_stub()
