"""
Test suite: inverse_T_to_F.py (Week 3 Day 1)
=============================================

Exercises the Paper I inverse map F^{-1} Newton iteration:
  1. TestLinearResponseInverse (initial guess correctness)
  2. TestJacobianAnalytic     (vs finite differences)
  3. TestIsotropicInversion   (analytic trivial case)
  4. TestDipoleInversion      (pure dipole recovery)
  5. TestQuadrupoleInversion  (pure quadrupole recovery)
  6. TestMixedMultipoleInversion (L = 3 mixed)
  7. TestNewtonConvergence    (quadratic convergence rate)
  8. TestAdmissibilityBarrier (Theta > 0, BE eta <= 0)
  9. TestRoundtripClosure     (F^{-1} o F = id)
 10. TestEdgeCases            (error paths, extreme anisotropy)
 11. TestTwoFieldGivenEta     (inversion with supplied eta(mu))
"""
from __future__ import annotations

import numpy as np
import pytest

from tsc.charts.forward_F_to_T import (
    AxisymmetricField,
    axisymmetric_F,
    isotropic_theta,
    dipole_theta,
    quadrupole_theta,
)
from tsc.charts.inverse_T_to_F import (
    linear_response_inverse,
    invert_T_to_Theta_axisymmetric,
    roundtrip_relative_error,
    jacobian_finite_difference,
    _build_jacobian,
    InverseResult,
)
from tsc.charts.laguerre_basis import xi_moment


# ============================================================================
# Test Class 1 - Linear-response inverse (initial guess)
# ============================================================================

class TestLinearResponseInverse:
    """Verify the analytic initial-guess formulas are exact at linear order."""

    def test_isotropic_MB(self):
        # Theta_0 = 1, all higher = 0; T_0 = I_3(MB, 0) = 6, T_ell = 0 else
        T = np.array([6.0, 0.0, 0.0, 0.0])
        Theta = linear_response_inverse(T, xi=0, moment_order=3)
        assert Theta[0] == pytest.approx(1.0, abs=1e-14)
        assert np.allclose(Theta[1:], 0.0, atol=1e-14)

    def test_isotropic_BE(self):
        I3 = xi_moment(3, +1, 0.0)
        Theta_0_true = 2.0
        T = np.array([Theta_0_true ** 4 * I3])
        Theta = linear_response_inverse(T, xi=+1, moment_order=3)
        assert Theta[0] == pytest.approx(Theta_0_true, rel=1e-12)

    def test_dipole_linear_formula(self):
        # Paper I linear response: T_1 = (n+1) * Theta_0^n * Theta_1 * I_n
        n = 3
        xi = 0  # MB
        I3 = xi_moment(n, xi, 0.0)
        Theta_0, Theta_1 = 1.0, 0.05
        T = np.array([
            Theta_0 ** (n + 1) * I3,
            (n + 1) * Theta_0 ** n * Theta_1 * I3,
        ])
        rec = linear_response_inverse(T, xi=xi, moment_order=n)
        assert rec[0] == pytest.approx(Theta_0, rel=1e-14)
        assert rec[1] == pytest.approx(Theta_1, rel=1e-14)

    def test_moment_order_variants(self):
        # Same calculation for n = 2 (number) and n = 4 (stress)
        for n in (2, 3, 4):
            I_n = xi_moment(n, 0, 0.0)
            T_0_true = 1.5 ** (n + 1) * I_n
            rec = linear_response_inverse(
                np.array([T_0_true]), xi=0, moment_order=n,
            )
            assert rec[0] == pytest.approx(1.5, rel=1e-14)

    def test_rejects_nonpositive_T0(self):
        with pytest.raises(ValueError):
            linear_response_inverse(np.array([-1.0, 0.0]), xi=0)
        with pytest.raises(ValueError):
            linear_response_inverse(np.array([0.0, 0.1]), xi=0)

    def test_background_eta_MB(self):
        # For MB with eta_bg = 0.5, I_3 = e^0.5 * 6
        eta_bg = 0.5
        I3 = np.exp(eta_bg) * 6.0
        T_0_true = 1.0 ** 4 * I3
        rec = linear_response_inverse(
            np.array([T_0_true]), xi=0, eta_bg=eta_bg, moment_order=3,
        )
        assert rec[0] == pytest.approx(1.0, rel=1e-12)


# ============================================================================
# Test Class 2 - Jacobian analytic vs finite differences
# ============================================================================

class TestJacobianAnalytic:
    """Paper III-A Jacobian must match central finite differences."""

    def test_jacobian_BE(self):
        coeffs = np.array([1.0, 0.05, 0.03, 0.01])
        J_ana, _, _ = _build_jacobian(
            coeffs, xi=+1, eta=None, moment_order=3, L_out=3, n_quad=64,
        )
        J_fd = jacobian_finite_difference(
            coeffs, xi=+1, eta=None, moment_order=3, L_out=3, n_quad=64, h=1e-6,
        )
        rel_err = np.max(
            np.abs(J_ana - J_fd) / np.maximum(np.abs(J_ana), 1e-12)
        )
        assert rel_err < 1e-7

    def test_jacobian_MB(self):
        coeffs = np.array([1.0, 0.05, 0.03, 0.01])
        J_ana, _, _ = _build_jacobian(
            coeffs, xi=0, eta=None, moment_order=3, L_out=3, n_quad=64,
        )
        J_fd = jacobian_finite_difference(
            coeffs, xi=0, eta=None, moment_order=3, L_out=3, n_quad=64, h=1e-6,
        )
        rel_err = np.max(
            np.abs(J_ana - J_fd) / np.maximum(np.abs(J_ana), 1e-12)
        )
        assert rel_err < 1e-7

    def test_jacobian_FD(self):
        coeffs = np.array([1.0, 0.05, 0.03, 0.01])
        J_ana, _, _ = _build_jacobian(
            coeffs, xi=-1, eta=None, moment_order=3, L_out=3, n_quad=64,
        )
        J_fd = jacobian_finite_difference(
            coeffs, xi=-1, eta=None, moment_order=3, L_out=3, n_quad=64, h=1e-6,
        )
        rel_err = np.max(
            np.abs(J_ana - J_fd) / np.maximum(np.abs(J_ana), 1e-12)
        )
        assert rel_err < 1e-7

    def test_jacobian_isotropic_is_diagonal(self):
        # At iso Theta = Theta_0, Jacobian reduces to diag with
        # J_{ll} = (2 ell + 1) / 2 * (n+1) * Theta_0^n * I_n
        #         * int P_ell^2 dmu
        #       = (n+1) * Theta_0^n * I_n                 for all ell
        # because (2 ell + 1) / 2 * int P_ell^2 dmu = 1.
        n = 3
        Theta_0 = 1.5
        coeffs = np.array([Theta_0, 0.0, 0.0, 0.0])
        J, _, _ = _build_jacobian(
            coeffs, xi=0, eta=None, moment_order=n, L_out=3, n_quad=64,
        )
        I_n = xi_moment(n, 0, 0.0)
        diag_expected = (n + 1) * Theta_0 ** n * I_n
        for ell in range(4):
            assert J[ell, ell] == pytest.approx(diag_expected, rel=1e-12)
            for m in range(4):
                if m != ell:
                    assert abs(J[ell, m]) < 1e-10


# ============================================================================
# Test Class 3 - Isotropic inversion
# ============================================================================

class TestIsotropicInversion:
    """Trivial case: isotropic input should converge at initial guess."""

    def test_iso_MB_n3(self):
        Theta_true = isotropic_theta(value=1.0)
        fwd = axisymmetric_F(xi=0, Theta=Theta_true, L_out=3, moment_order=3)
        res = invert_T_to_Theta_axisymmetric(
            fwd.T_ell, xi=0, moment_order=3, tol=1e-10,
        )
        assert res.converged
        assert res.Theta.coeffs[0] == pytest.approx(1.0, abs=1e-12)
        assert np.allclose(res.Theta.coeffs[1:], 0.0, atol=1e-12)

    def test_iso_BE_n3(self):
        Theta_true = isotropic_theta(value=1.5)
        fwd = axisymmetric_F(xi=+1, Theta=Theta_true, L_out=3, moment_order=3)
        res = invert_T_to_Theta_axisymmetric(
            fwd.T_ell, xi=+1, moment_order=3, tol=1e-10,
        )
        assert res.converged
        assert res.Theta.coeffs[0] == pytest.approx(1.5, rel=1e-11)

    def test_iso_FD_n2(self):
        Theta_true = isotropic_theta(value=0.8)
        fwd = axisymmetric_F(xi=-1, Theta=Theta_true, L_out=2, moment_order=2)
        res = invert_T_to_Theta_axisymmetric(
            fwd.T_ell, xi=-1, moment_order=2, tol=1e-10,
        )
        assert res.converged
        assert res.Theta.coeffs[0] == pytest.approx(0.8, rel=1e-11)

    def test_iso_zero_Newton_iters(self):
        # Pure isotropy => linear-response guess already exact, Newton skipped
        Theta_true = isotropic_theta(value=2.0)
        fwd = axisymmetric_F(xi=0, Theta=Theta_true, L_out=3, moment_order=3)
        res = invert_T_to_Theta_axisymmetric(fwd.T_ell, xi=0, tol=1e-10)
        # Initial guess is exact up to numerical zeros in higher modes
        assert res.n_iter <= 1


# ============================================================================
# Test Class 4 - Dipole inversion
# ============================================================================

class TestDipoleInversion:
    """Pure dipole Theta = Theta_0 + Theta_1 * P_1 recovery."""

    def _check_dipole(self, xi, Theta_0, Theta_1, tol=1e-10, atol=1e-9):
        Theta_true = dipole_theta(Theta_0=Theta_0, Theta_1=Theta_1)
        fwd = axisymmetric_F(
            xi=xi, Theta=Theta_true, L_out=3, moment_order=3,
        )
        res = invert_T_to_Theta_axisymmetric(
            fwd.T_ell, xi=xi, moment_order=3, tol=tol,
        )
        assert res.converged, (
            f"failed to converge; final_res = {res.final_residual:.2e}"
        )
        assert res.Theta.coeffs[0] == pytest.approx(Theta_0, abs=atol)
        assert res.Theta.coeffs[1] == pytest.approx(Theta_1, abs=atol)
        assert abs(res.Theta.coeffs[2]) < atol
        assert abs(res.Theta.coeffs[3]) < atol
        return res

    def test_dipole_MB_small(self):
        res = self._check_dipole(xi=0, Theta_0=1.0, Theta_1=0.05)
        assert res.n_iter <= 5

    def test_dipole_BE_small(self):
        res = self._check_dipole(xi=+1, Theta_0=1.0, Theta_1=0.05)
        assert res.n_iter <= 5

    def test_dipole_FD_small(self):
        res = self._check_dipole(xi=-1, Theta_0=1.0, Theta_1=0.05)
        assert res.n_iter <= 5

    def test_dipole_MB_moderate(self):
        res = self._check_dipole(xi=0, Theta_0=1.0, Theta_1=0.2, atol=1e-8)
        assert res.n_iter <= 8


# ============================================================================
# Test Class 5 - Quadrupole inversion
# ============================================================================

class TestQuadrupoleInversion:
    """Pure quadrupole Theta = Theta_0 + Theta_2 * P_2 recovery."""

    def _check_quad(self, xi, Theta_0, Theta_2, tol=1e-10, atol=1e-9):
        Theta_true = quadrupole_theta(Theta_0=Theta_0, Theta_2=Theta_2)
        fwd = axisymmetric_F(
            xi=xi, Theta=Theta_true, L_out=3, moment_order=3,
        )
        res = invert_T_to_Theta_axisymmetric(
            fwd.T_ell, xi=xi, moment_order=3, tol=tol,
        )
        assert res.converged
        assert res.Theta.coeffs[0] == pytest.approx(Theta_0, abs=atol)
        assert abs(res.Theta.coeffs[1]) < atol
        assert res.Theta.coeffs[2] == pytest.approx(Theta_2, abs=atol)
        assert abs(res.Theta.coeffs[3]) < atol
        return res

    def test_quadrupole_MB(self):
        self._check_quad(xi=0, Theta_0=1.0, Theta_2=0.04)

    def test_quadrupole_BE(self):
        self._check_quad(xi=+1, Theta_0=1.0, Theta_2=0.04)

    def test_quadrupole_FD(self):
        self._check_quad(xi=-1, Theta_0=1.0, Theta_2=0.04)

    def test_quadrupole_parity_no_dipole_leak(self):
        # Pure Theta_2 input should give zero T_1 (parity);
        # inversion must return Theta_1 = 0 (machine zero).
        Theta_true = quadrupole_theta(Theta_0=1.0, Theta_2=0.05)
        fwd = axisymmetric_F(
            xi=0, Theta=Theta_true, L_out=3, moment_order=3,
        )
        res = invert_T_to_Theta_axisymmetric(fwd.T_ell, xi=0, tol=1e-11)
        assert abs(res.Theta.coeffs[1]) < 1e-10
        assert abs(res.Theta.coeffs[3]) < 1e-10


# ============================================================================
# Test Class 6 - Mixed multipole inversion
# ============================================================================

class TestMixedMultipoleInversion:
    """Mixed Theta with nonzero coeffs at multiple ell."""

    def _check_mixed(self, xi, coeffs, atol=1e-9):
        Theta_true = AxisymmetricField(coeffs=coeffs, name="Theta_true")
        fwd = axisymmetric_F(
            xi=xi, Theta=Theta_true, L_out=len(coeffs) - 1, moment_order=3,
        )
        res = invert_T_to_Theta_axisymmetric(
            fwd.T_ell, xi=xi, moment_order=3, tol=1e-11,
        )
        assert res.converged
        for ell, c in enumerate(coeffs):
            assert res.Theta.coeffs[ell] == pytest.approx(c, abs=atol), (
                f"ell = {ell}: got {res.Theta.coeffs[ell]}, expected {c}"
            )
        return res

    def test_mixed_MB_L3(self):
        self._check_mixed(xi=0, coeffs=np.array([1.0, 0.08, 0.04, 0.02]))

    def test_mixed_BE_L3(self):
        self._check_mixed(xi=+1, coeffs=np.array([1.0, 0.08, 0.04, 0.02]))

    def test_mixed_FD_L3(self):
        self._check_mixed(xi=-1, coeffs=np.array([1.0, 0.08, 0.04, 0.02]))

    def test_mixed_sign_patterns(self):
        self._check_mixed(xi=0, coeffs=np.array([1.0, -0.05, 0.03, -0.01]))

    def test_mixed_L4(self):
        self._check_mixed(
            xi=0, coeffs=np.array([1.0, 0.05, 0.03, 0.02, 0.01]),
        )


# ============================================================================
# Test Class 7 - Newton convergence rate
# ============================================================================

class TestNewtonConvergence:
    """Newton quadratic convergence and iteration-count scaling."""

    def test_quadratic_convergence_MB(self):
        # Residual should shrink roughly by r_{k+1} / r_k^2 bounded
        Theta_true = dipole_theta(Theta_0=1.0, Theta_1=0.1)
        fwd = axisymmetric_F(xi=0, Theta=Theta_true, L_out=3, moment_order=3)
        res = invert_T_to_Theta_axisymmetric(fwd.T_ell, xi=0, tol=1e-12)
        r = res.residual_history
        # Expect at least one step where r_{k+1} < r_k^{1.5}
        saw_quadratic = any(
            r[k + 1] < r[k] ** 1.5 + 1e-16 for k in range(len(r) - 1)
        )
        assert saw_quadratic, f"no super-linear step observed: {r}"

    def test_iteration_count_small_anisotropy(self):
        # Small anisotropy => initial guess very good; few iters
        Theta_true = AxisymmetricField(coeffs=np.array([1.0, 0.01, 0.005]))
        fwd = axisymmetric_F(xi=0, Theta=Theta_true, L_out=2, moment_order=3)
        res = invert_T_to_Theta_axisymmetric(fwd.T_ell, xi=0, tol=1e-10)
        assert res.n_iter <= 3

    def test_iteration_count_moderate_anisotropy(self):
        Theta_true = AxisymmetricField(coeffs=np.array([1.0, 0.1, 0.05, 0.02]))
        fwd = axisymmetric_F(xi=0, Theta=Theta_true, L_out=3, moment_order=3)
        res = invert_T_to_Theta_axisymmetric(fwd.T_ell, xi=0, tol=1e-10)
        assert res.n_iter <= 6

    def test_condition_number_bounded_small_anisotropy(self):
        # At small anisotropy the Jacobian is near-diagonal, cond ~ O(1)
        Theta_true = AxisymmetricField(coeffs=np.array([1.0, 0.02, 0.01]))
        fwd = axisymmetric_F(xi=0, Theta=Theta_true, L_out=2, moment_order=3)
        res = invert_T_to_Theta_axisymmetric(fwd.T_ell, xi=0, tol=1e-10)
        assert res.jacobian_cond < 3.0


# ============================================================================
# Test Class 8 - Admissibility barrier
# ============================================================================

class TestAdmissibilityBarrier:
    """Theta(mu) > 0 guard; BE eta <= 0 guard."""

    def test_rejects_negative_Theta_initial(self):
        # Construct T_ell that linear-response inverse would map to a
        # near-zero Theta_0, and force a user-supplied bad initial guess.
        bad_guess = AxisymmetricField(coeffs=np.array([0.5, 0.8, 0.3, 0.1]))
        # This guess has Theta(mu=-1) = 0.5 - 0.8 + 0.3 - 0.1 = -0.1 < 0
        assert not all(
            bad_guess.evaluate(np.linspace(-1, 1, 50)) > 0
        )
        T_dummy = np.array([6.0, 0.1, 0.05, 0.01])
        with pytest.raises(ValueError, match="Theta"):
            invert_T_to_Theta_axisymmetric(
                T_dummy, xi=0,
                initial_guess=bad_guess,
                check_admissibility=True,
            )

    def test_BE_rejects_positive_eta(self):
        bad_eta = AxisymmetricField(coeffs=np.array([0.1]))
        T_dummy = np.array([6.0, 0.1])
        with pytest.raises(ValueError, match="eta"):
            invert_T_to_Theta_axisymmetric(
                T_dummy, xi=+1, eta=bad_eta,
            )

    def test_bypass_admissibility_flag(self):
        # Allow non-positive Theta iterate if caller opts in. Result may
        # not be physical but should not raise.
        Theta_true = dipole_theta(Theta_0=1.0, Theta_1=0.05)
        fwd = axisymmetric_F(xi=0, Theta=Theta_true, L_out=3, moment_order=3)
        res = invert_T_to_Theta_axisymmetric(
            fwd.T_ell, xi=0, check_admissibility=False, tol=1e-10,
        )
        assert res.converged


# ============================================================================
# Test Class 9 - Roundtrip F^{-1} o F = id
# ============================================================================

class TestRoundtripClosure:
    """Forward-inverse cycle closure at machine precision."""

    def test_roundtrip_isotropic_all_stats(self):
        for xi in (-1, 0, +1):
            Theta_true = isotropic_theta(value=1.3)
            max_err, res = roundtrip_relative_error(
                Theta_true=Theta_true, xi=xi, moment_order=3,
                L_out=2, tol=1e-11,
            )
            assert max_err < 1e-10

    def test_roundtrip_dipole_MB(self):
        Theta_true = dipole_theta(Theta_0=1.0, Theta_1=0.08)
        max_err, _ = roundtrip_relative_error(
            Theta_true=Theta_true, xi=0, L_out=3, tol=1e-11,
        )
        assert max_err < 1e-9

    def test_roundtrip_quadrupole_BE(self):
        Theta_true = quadrupole_theta(Theta_0=1.0, Theta_2=0.04)
        max_err, _ = roundtrip_relative_error(
            Theta_true=Theta_true, xi=+1, L_out=3, tol=1e-11,
        )
        assert max_err < 1e-9

    def test_roundtrip_mixed_FD(self):
        Theta_true = AxisymmetricField(
            coeffs=np.array([1.0, 0.06, 0.03, 0.01]),
        )
        max_err, _ = roundtrip_relative_error(
            Theta_true=Theta_true, xi=-1, L_out=3, tol=1e-11,
        )
        assert max_err < 1e-9

    def test_roundtrip_moderate_anisotropy(self):
        # Stress test: amp up to 0.2
        Theta_true = AxisymmetricField(
            coeffs=np.array([1.0, 0.2, 0.1, 0.05]),
        )
        max_err, _ = roundtrip_relative_error(
            Theta_true=Theta_true, xi=0, L_out=3, tol=1e-11,
        )
        assert max_err < 1e-8


# ============================================================================
# Test Class 10 - Edge cases and error paths
# ============================================================================

class TestEdgeCases:
    """Input validation, extreme amplitudes, zero vectors."""

    def test_invalid_xi(self):
        with pytest.raises(ValueError):
            invert_T_to_Theta_axisymmetric(
                np.array([6.0, 0.1]), xi=2,
            )

    def test_invalid_moment_order(self):
        with pytest.raises(ValueError):
            invert_T_to_Theta_axisymmetric(
                np.array([6.0, 0.1]), xi=0, moment_order=5,
            )

    def test_rejects_zero_observation(self):
        # All-zero T would divide by zero when normalizing residual;
        # also T_0 = 0 fails the linear-response inverse positivity check.
        with pytest.raises(ValueError):
            invert_T_to_Theta_axisymmetric(
                np.zeros(3), xi=0,
            )

    def test_non_1d_input_raises(self):
        with pytest.raises(ValueError):
            invert_T_to_Theta_axisymmetric(
                np.zeros((2, 2)), xi=0,
            )

    def test_rectangular_system_rejected(self):
        # Day 1 scope: square only. L_Theta != L_T should raise.
        with pytest.raises(ValueError):
            invert_T_to_Theta_axisymmetric(
                np.array([6.0, 0.1, 0.05]), xi=0, L_Theta=5,
            )

    def test_returns_InverseResult_type(self):
        T = np.array([6.0, 0.1])
        res = invert_T_to_Theta_axisymmetric(T, xi=0, tol=1e-9)
        assert isinstance(res, InverseResult)
        assert isinstance(res.Theta, AxisymmetricField)
        assert isinstance(res.residual_history, tuple)
        assert res.final_residual == res.residual_history[-1]


# ============================================================================
# Test Class 11 - Two-field with given eta
# ============================================================================

class TestTwoFieldGivenEta:
    """Recovery of Theta when eta(mu) is supplied externally."""

    def test_FD_with_iso_eta(self):
        eta = AxisymmetricField(coeffs=np.array([-0.1]))
        Theta_true = AxisymmetricField(coeffs=np.array([1.0, 0.1, 0.04, 0.02]))
        max_err, res = roundtrip_relative_error(
            Theta_true=Theta_true, xi=-1, eta=eta, L_out=3, tol=1e-11,
        )
        assert res.converged
        assert max_err < 1e-9

    def test_MB_with_dipole_eta(self):
        eta = AxisymmetricField(coeffs=np.array([-0.05, -0.02]))
        Theta_true = AxisymmetricField(coeffs=np.array([1.0, 0.08, 0.03, 0.01]))
        max_err, res = roundtrip_relative_error(
            Theta_true=Theta_true, xi=0, eta=eta, L_out=3, tol=1e-11,
        )
        assert res.converged
        assert max_err < 1e-9

    def test_BE_with_negative_eta_admissible(self):
        # BE allows eta <= 0; mildly negative eta should be fine
        eta = AxisymmetricField(coeffs=np.array([-0.2]))
        Theta_true = AxisymmetricField(coeffs=np.array([1.0, 0.05, 0.03]))
        max_err, res = roundtrip_relative_error(
            Theta_true=Theta_true, xi=+1, eta=eta, L_out=2, tol=1e-11,
        )
        assert res.converged
        assert max_err < 1e-9
