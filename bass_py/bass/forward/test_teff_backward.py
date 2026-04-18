"""bass/forward/test_teff_backward.py — Backward T_eff inversion tests.

Verifies the roundtrip
    (A, Q) --forward--> a_ℓ --backward--> (A', Q')
across the three inversion strategies:

    linear    : leading-order analytic inverse, error O((A, Q)²)
    lsq       : full nonlinear least-squares on a_ℓ up to ell_max
    projection: exact Gauss-Legendre L² projection of Θ (not Θ⁴)
"""
import numpy as np
import pytest

from bass.forward.teff_forward import theta4_coefficients, monopole_gauge_check
from bass.forward.teff_backward import (
    TeffBianchiBackward,
    teff_backward_linear,
    teff_backward_lsq,
    teff_backward_projection,
)


# ════════════════════════════════════════════════════════════════════
# Strategy 1: linear small-(A, Q) inversion
# ════════════════════════════════════════════════════════════════════

class TestLinearInversion:

    def test_exact_at_zero(self):
        A, Q = teff_backward_linear(0.0, 0.0)
        assert A == 0.0 and Q == 0.0

    def test_recovery_at_order_1em3(self):
        """At (A, Q) = (1e-3, 5e-4) linear inversion is good to ~10⁻⁶."""
        A_true, Q_true = 1e-3, 5e-4
        a = theta4_coefficients(A_true, Q_true)
        A, Q = teff_backward_linear(a[1], a[2])
        assert A == pytest.approx(A_true, abs=1e-5)
        assert Q == pytest.approx(Q_true, abs=1e-5)

    def test_degraded_at_order_1em1(self):
        """At (A, Q) = (0.05, 0.02) linear is only ~5% accurate."""
        A_true, Q_true = 0.05, 0.02
        a = theta4_coefficients(A_true, Q_true)
        A, Q = teff_backward_linear(a[1], a[2])
        assert abs(A - A_true) < 0.1 * A_true
        assert abs(Q - Q_true) < 0.1 * Q_true

    def test_Q_inferred_from_dipole_squared(self):
        """At A > 0, Q = 0: linear inversion should give Q ≈ 0 after subtracting 4A²."""
        A_true, Q_true = 1e-3, 0.0
        a = theta4_coefficients(A_true, Q_true)
        A, Q = teff_backward_linear(a[1], a[2])
        assert A == pytest.approx(A_true, rel=1e-3)
        assert abs(Q) < 1e-6


# ════════════════════════════════════════════════════════════════════
# Strategy 2: nonlinear LSQ
# ════════════════════════════════════════════════════════════════════

class TestLSQInversion:

    def test_high_precision_small(self):
        """LSQ recovers (A, Q) to ~10⁻¹⁰ for small amplitudes.

        Residual is limited by scipy.optimize.least_squares termination
        tolerances (xtol=1e-14) and by numerical conditioning of the
        Θ⁴ polynomial Jacobian at small (A, Q).
        """
        A_true, Q_true = 1e-3, 5e-4
        a = theta4_coefficients(A_true, Q_true)
        A, Q, res, info = teff_backward_lsq(a, ell_max=4)
        assert A == pytest.approx(A_true, abs=1e-10)
        assert Q == pytest.approx(Q_true, abs=1e-10)
        assert res < 1e-10

    def test_high_precision_moderate(self):
        """At (A, Q) = (0.05, 0.02) LSQ recovers to better than 10⁻⁸."""
        A_true, Q_true = 0.05, 0.02
        a = theta4_coefficients(A_true, Q_true)
        A, Q, res, info = teff_backward_lsq(a, ell_max=8)
        assert A == pytest.approx(A_true, abs=1e-8)
        assert Q == pytest.approx(Q_true, abs=1e-8)

    def test_reduced_ell_max(self):
        """Using only ℓ ≤ 2 still recovers (A, Q) well — but not as tightly."""
        A_true, Q_true = 1e-3, 5e-4
        a = theta4_coefficients(A_true, Q_true)
        A, Q, res, info = teff_backward_lsq(a, ell_max=2)
        assert A == pytest.approx(A_true, abs=1e-8)
        assert Q == pytest.approx(Q_true, abs=1e-8)

    def test_warmstart_x0(self):
        """Passing an explicit initial guess produces the same fixed point."""
        A_true, Q_true = 0.02, 0.01
        a = theta4_coefficients(A_true, Q_true)
        A1, Q1, _, _ = teff_backward_lsq(a, x0=(0.02, 0.01))
        A2, Q2, _, _ = teff_backward_lsq(a, x0=(0.0, 0.0))
        assert A1 == pytest.approx(A2, abs=1e-12)
        assert Q1 == pytest.approx(Q2, abs=1e-12)

    def test_weights_down_weight_high_ell(self):
        """Down-weighting ℓ ≥ 5 residuals should still recover (A, Q)."""
        A_true, Q_true = 1e-3, 5e-4
        a = theta4_coefficients(A_true, Q_true)
        weights = {5: 1e-3, 6: 1e-3, 7: 1e-3, 8: 1e-3}
        A, Q, _, _ = teff_backward_lsq(a, weights=weights)
        assert A == pytest.approx(A_true, abs=1e-10)
        assert Q == pytest.approx(Q_true, abs=1e-10)


# ════════════════════════════════════════════════════════════════════
# Strategy 3: exact Gauss-Legendre projection of Θ (not Θ⁴)
# ════════════════════════════════════════════════════════════════════

class TestProjectionInversion:
    """Projection on the FIRST-order field Θ = 1 + A P₁ + Q P₂ is exact."""

    def test_projection_on_pure_first_order(self):
        A_true, Q_true = 0.01, 0.005

        def theta(x):
            return 1.0 + A_true * x + Q_true * 0.5 * (3 * x * x - 1)

        r = teff_backward_projection(theta)
        # Gauss-Legendre with 200 nodes integrates P_2 exactly; residual
        # is roundoff from sum. ~10⁻¹³ is realistic.
        assert r['a0'] == pytest.approx(1.0, abs=1e-13)
        assert r['A'] == pytest.approx(A_true, abs=1e-13)
        assert r['Q'] == pytest.approx(Q_true, abs=1e-13)

    def test_projection_with_explicit_grid(self):
        from numpy.polynomial.legendre import leggauss
        A_true, Q_true = 0.02, 0.01
        x, w = leggauss(128)
        vals = 1.0 + A_true * x + Q_true * 0.5 * (3 * x * x - 1)
        r = teff_backward_projection(
            vals, cos_theta_nodes=x, quad_weights=w
        )
        assert r['A'] == pytest.approx(A_true, abs=1e-13)
        assert r['Q'] == pytest.approx(Q_true, abs=1e-13)

    def test_projection_rejects_mismatched_shape(self):
        with pytest.raises(ValueError):
            teff_backward_projection(
                np.array([0.0, 1.0]),
                cos_theta_nodes=np.array([0.5]),
                quad_weights=np.array([1.0]),
            )

    def test_projection_requires_nodes_weights_for_array(self):
        with pytest.raises(ValueError):
            teff_backward_projection(np.array([1.0, 1.0, 1.0]))

    def test_projection_monopole_gauge_of_forward(self):
        """Projection of the forward Θ sees the gauge: a0 = 1 exactly."""
        A_true, Q_true = 0.01, 0.005

        def theta(x):
            return 1.0 + A_true * x + Q_true * 0.5 * (3 * x * x - 1)

        r = teff_backward_projection(theta, n_theta=400)
        assert r['a0'] == pytest.approx(1.0, abs=1e-14)

    def test_projection_does_not_recover_AQ_from_theta4(self):
        """Projection of Θ⁴ gives the Legendre coefficient a₁ of the
        OUTPUT field, not the closure parameter A.

        For Θ⁴, a₁ ≈ 4·A at leading order, so the returned 'A' is
        approximately 4·A (NOT the generating closure A).
        """
        A_true, Q_true = 0.01, 0.005

        def theta_fourth(x):
            th = 1.0 + A_true * x + Q_true * 0.5 * (3 * x * x - 1)
            return th ** 4

        r = teff_backward_projection(theta_fourth)
        # a_1 of Θ⁴ = 4·A·(1 + 6Q/5 + ...). The projection returns
        # exactly that (since the formula is a_ℓ = (2ℓ+1)·⟨Θ⁴·P_ℓ⟩).
        assert r['A'] == pytest.approx(4.0 * A_true, rel=0.02)


# ════════════════════════════════════════════════════════════════════
# Unified class interface
# ════════════════════════════════════════════════════════════════════

class TestBackwardClass:

    def test_dispatch_linear(self):
        A_true, Q_true = 1e-3, 5e-4
        a = theta4_coefficients(A_true, Q_true)
        back = TeffBianchiBackward()
        A, Q = back.invert(a_ell=a, method='linear')
        assert A == pytest.approx(A_true, abs=1e-5)

    def test_dispatch_lsq(self):
        A_true, Q_true = 1e-3, 5e-4
        a = theta4_coefficients(A_true, Q_true)
        back = TeffBianchiBackward()
        A, Q, res, _ = back.invert(a_ell=a, method='lsq')
        assert res < 1e-10
        assert A == pytest.approx(A_true, abs=1e-10)
        assert Q == pytest.approx(Q_true, abs=1e-10)

    def test_dispatch_projection(self):
        A_true, Q_true = 0.01, 0.005

        def theta(x):
            return 1.0 + A_true * x + Q_true * 0.5 * (3 * x * x - 1)

        back = TeffBianchiBackward()
        r = back.invert(theta_samples=theta, method='projection')
        assert r['A'] == pytest.approx(A_true, abs=1e-13)
        assert r['Q'] == pytest.approx(Q_true, abs=1e-13)

    def test_unknown_method(self):
        back = TeffBianchiBackward()
        with pytest.raises(ValueError):
            back.invert(a_ell={0: 1.0}, method='bogus')

    def test_missing_arg_raises(self):
        back = TeffBianchiBackward()
        with pytest.raises(ValueError):
            back.invert(method='linear')
        with pytest.raises(ValueError):
            back.invert(method='projection')


# ════════════════════════════════════════════════════════════════════
# Full roundtrip checks
# ════════════════════════════════════════════════════════════════════

class TestRoundtrip:
    """Forward → Backward → (A', Q') matches true (A, Q)."""

    @pytest.mark.parametrize("A_true,Q_true", [
        (1e-5, 1e-6),
        (1e-3, 5e-4),
        (1e-2, 5e-3),
        (0.05, 0.02),
    ])
    def test_lsq_roundtrip(self, A_true, Q_true):
        """LSQ recovers (A, Q) to ~10⁻⁸ for small/moderate amplitudes."""
        a = theta4_coefficients(A_true, Q_true)
        A, Q, res, _ = teff_backward_lsq(a)
        assert A == pytest.approx(A_true, abs=1e-8)
        assert Q == pytest.approx(Q_true, abs=1e-8)
        assert res < 1e-9

    @pytest.mark.parametrize("A_true,Q_true", [
        (1e-4, 1e-4),
        (1e-3, 5e-4),
    ])
    def test_linear_roundtrip_small(self, A_true, Q_true):
        """Linear inversion matches true (A, Q) at O((A, Q)²)."""
        a = theta4_coefficients(A_true, Q_true)
        A, Q = teff_backward_linear(a[1], a[2])
        scale = max(A_true, Q_true)
        assert abs(A - A_true) < 10.0 * scale ** 2
        assert abs(Q - Q_true) < 10.0 * scale ** 2

    def test_projection_roundtrip_exact(self):
        """Projection on Θ (not Θ⁴) reaches ~10⁻¹³ (quadrature roundoff)."""
        A_true, Q_true = 0.03, 0.015

        def theta(x):
            return 1.0 + A_true * x + Q_true * 0.5 * (3 * x * x - 1)

        r = teff_backward_projection(theta, n_theta=400)
        assert abs(r['A'] - A_true) + abs(r['Q'] - Q_true) < 1e-12
