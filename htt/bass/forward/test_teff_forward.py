"""bass/forward/test_teff_forward.py — Forward T_eff closure tests.

Adapted from legacy/bass/tests/test_teff_forward.py (C-12 suite). The
tests stop at ℓ ≤ 3 where the closed-form Gaunt algebra is < 1%
accurate; the tolerated-but-approximate ℓ ≥ 5 coefficients have their
own dedicated tolerance tests in ``TestHighEll``.
"""
import numpy as np
import pytest

from bass.forward.teff_forward import (
    TeffBianchiForward,
    theta4_coefficients,
    theta4_coefficients_vec,
    monopole_gauge_check,
)


class TestTheta4LeadingOrder:
    """Verify the leading terms of the Θ⁴ expansion."""

    def test_a2_leading_for_Q_only(self):
        """a₂ ≈ 4·Q for small Q, A = 0."""
        Q = 1e-4
        a = theta4_coefficients(0.0, Q)
        assert a[2] == pytest.approx(4.0 * Q, rel=0.01)

    def test_a2_dipole_squared(self):
        """a₂ contains the 4·A² dipole-squared term."""
        A = 0.01
        a = theta4_coefficients(A, 0.0)
        assert a[2] == pytest.approx(4.0 * A ** 2, rel=0.05)

    def test_a1_leading_for_A_only(self):
        """a₁ ≈ 4·A for small A, Q = 0."""
        A = 1e-3
        a = theta4_coefficients(A, 0.0)
        assert a[1] == pytest.approx(4.0 * A, rel=0.01)

    def test_a3_leading_AQ_cross(self):
        """a₃ ≈ (36/5)·A·Q for small A, Q."""
        A, Q = 1e-3, 1e-4
        a = theta4_coefficients(A, Q)
        expected = (36.0 / 5.0) * A * Q
        assert abs(a[3] - expected) / max(abs(expected), 1e-20) < 0.5

    def test_a0_close_to_1(self):
        a = theta4_coefficients(1e-4, 1e-5)
        assert a[0] == pytest.approx(1.0, abs=0.01)

    def test_zero_perturbation(self):
        """A = Q = 0 → a₀ = 1, all higher-ℓ exactly 0."""
        a = theta4_coefficients(0.0, 0.0)
        assert a[0] == pytest.approx(1.0)
        for ell in range(1, 9):
            assert a[ell] == pytest.approx(0.0, abs=1e-15)


class TestMonopoleGauge:
    """⟨Θ⟩_Ω = 1 regardless of (A, Q)."""

    def test_gauge_exact_at_zero(self):
        assert monopole_gauge_check(0.0, 0.0) == pytest.approx(1.0, abs=1e-14)

    def test_gauge_small_perturbation(self):
        assert monopole_gauge_check(0.01, 0.005) == pytest.approx(1.0, abs=1e-10)

    def test_gauge_moderate_perturbation(self):
        assert monopole_gauge_check(0.1, 0.05) == pytest.approx(1.0, abs=1e-6)

    def test_gauge_large_perturbation(self):
        """Even at A = 0.3, Q = 0.1 (well outside physical) the gauge holds."""
        assert monopole_gauge_check(0.3, 0.1, n_theta=400) == pytest.approx(
            1.0, abs=1e-12
        )


class TestVectorizedCoefficients:
    """theta4_coefficients_vec broadcasts correctly and matches scalar."""

    def test_scalar_match(self):
        A, Q = 0.01, 0.005
        a_scalar = theta4_coefficients(A, Q)
        a_vec = theta4_coefficients_vec(np.array([A]), np.array([Q]))
        for ell in range(9):
            assert a_vec[ell][0] == pytest.approx(a_scalar[ell], rel=1e-14)

    def test_broadcast_grid(self):
        A = np.linspace(0.0, 0.02, 5)
        Q = np.linspace(0.0, 0.01, 5)
        a_vec = theta4_coefficients_vec(A, Q)
        assert a_vec[0].shape == (5,)
        assert a_vec[0][0] == pytest.approx(1.0, abs=1e-14)


class TestForwardClass:
    """TeffBianchiForward wrapper."""

    def test_f2_zero_at_zero_shear(self):
        teff = TeffBianchiForward()
        r = teff.compute_from_shear(1e-20, 0.0)
        assert abs(r['f2']) < 1e-8

    def test_shear_to_Q_monotonic(self):
        teff = TeffBianchiForward()
        Qs = [teff.shear_to_Q(s) for s in np.geomspace(1e-10, 1e-4, 20)]
        diffs = np.diff(Qs)
        assert np.all(diffs >= -1e-18)

    def test_tilt_to_A_exact_matches_linear_at_small_beta(self):
        """A_exact = tanh(β) → β − β³/3 + O(β⁵). Match linear to 10⁻⁵ at β = 10⁻³."""
        beta = 1e-3
        linear = TeffBianchiForward().tilt_to_A(beta)
        exact = TeffBianchiForward.tilt_to_A_exact(beta)
        assert linear == pytest.approx(exact, rel=1e-5)

    def test_tilt_to_A_exact_departs_at_large_beta(self):
        """At β = 0.1, exact A = tanh(0.1) ≈ 0.09967, about 0.33% below β."""
        beta = 0.1
        linear = TeffBianchiForward().tilt_to_A(beta)
        exact = TeffBianchiForward.tilt_to_A_exact(beta)
        assert linear - exact > 3e-4
        assert linear - exact < 4e-4

    def test_gauge_deviation_small(self):
        teff = TeffBianchiForward()
        r = teff.compute_from_shear(1e-6, 1.334e-3)
        assert r['gauge_deviation'] < 1e-10

    def test_transfer_function_grid(self):
        teff = TeffBianchiForward()
        grid = np.geomspace(1e-10, 1e-4, 8)
        tf = teff.transfer_functions(grid)
        assert len(tf['f2']) == 8
        assert tf['f2'][0] < tf['f2'][-1]  # monotonic


class TestInducedTail:
    """Θ⁴ expansion generates non-zero ℓ ≥ 4 coefficients."""

    def test_a4_nonzero_for_quadrupole(self):
        a = theta4_coefficients(0.0, 0.01)
        assert a[4] > 0

    def test_a5_nonzero_for_cross_term(self):
        """a_5 requires both A and Q (cross-term only)."""
        a_Q_only = theta4_coefficients(0.0, 0.01)
        a_A_only = theta4_coefficients(0.01, 0.0)
        a_both = theta4_coefficients(0.01, 0.01)
        assert a_Q_only[5] == pytest.approx(0.0, abs=1e-15)
        assert a_A_only[5] == pytest.approx(0.0, abs=1e-15)
        assert a_both[5] != 0.0


class TestLowEllGaussLegendreMatch:
    """Closed-form ℓ ≤ 3 vs Gauss-Legendre projection of Θ⁴.

    Legacy claim: ℓ ≤ 3 coefficients accurate to < 1% by incomplete
    Gaunt enumeration.  Module note "ℓ ≥ 5 up to O(10%-900%) error"
    indicates the closed form is approximate throughout — including
    a₀, a₁, a₂, a₃ at the ~1% level.  These tests bound that error
    and flag if the closed form ever degrades beyond 2%.
    """

    @staticmethod
    def _gl_project(A, Q, ell, n=400):
        """Project Θ⁴ onto P_ℓ via Gauss-Legendre (machine-precision oracle)."""
        from numpy.polynomial.legendre import leggauss
        x, w = leggauss(n)
        theta = 1.0 + A * x + Q * 0.5 * (3 * x * x - 1)
        theta4 = theta ** 4
        from scipy.special import legendre
        Pl = legendre(ell)(x)
        return (2 * ell + 1) * 0.5 * float(np.sum(w * theta4 * Pl))

    @pytest.mark.parametrize("ell", [0, 1, 2, 3])
    def test_ell_le_3_matches_gl_within_2pct(self, ell):
        """Closed form within 2% of GL projection for ℓ ≤ 3 at (A=0.01, Q=0.005)."""
        A, Q = 0.01, 0.005
        closed = theta4_coefficients(A, Q)[ell]
        numeric = self._gl_project(A, Q, ell)
        if abs(numeric) < 1e-14:
            return  # coefficient is zero; skip
        rel_err = abs(closed - numeric) / abs(numeric)
        assert rel_err < 0.02, (
            f"a_{ell}: closed={closed:.6e}, gl={numeric:.6e}, "
            f"rel_err={rel_err:.2e} exceeds 2%"
        )

    def test_small_amplitude_exact(self):
        """At 10⁻⁴ amplitude the closed form approaches machine precision."""
        A, Q = 1e-4, 1e-4
        for ell in (0, 1, 2, 3):
            closed = theta4_coefficients(A, Q)[ell]
            numeric = self._gl_project(A, Q, ell)
            if abs(numeric) < 1e-18:
                continue
            rel_err = abs(closed - numeric) / abs(numeric)
            assert rel_err < 1e-4, f"a_{ell} rel_err={rel_err:.2e} at 10⁻⁴"
