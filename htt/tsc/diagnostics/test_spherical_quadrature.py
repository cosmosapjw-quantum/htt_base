"""
Test suite: tsc/diagnostics/spherical_quadrature.py  (Week 4 Day 5 Part 1)
===========================================================================

Test classes (6):
  1. TestSupportedOrders          — enum of supported orders
  2. TestQuadratureConstruction   — node / weight / normalization
  3. TestYLExactness              — Y_ℓ^0 integrated correctly up to the order
  4. TestMonomialExactness        — polynomial monomials up to the order
  5. TestIntegrationAPIs          — integrate_on_sphere, integrate_vectorized
  6. TestValidation               — error paths

Target: ~25 tests.
"""
from __future__ import annotations

import math
import numpy as np
import pytest

from tsc.diagnostics.spherical_quadrature import (
    SUPPORTED_ORDERS,
    LebedevQuadrature,
    lebedev_quadrature,
    supported_orders,
    integrate_on_sphere,
    integrate_vectorized,
    verify_spherical_harmonic_exactness,
    verify_monomial_integration,
)


# ============================================================================
# Test Class 1 - Supported orders
# ============================================================================

class TestSupportedOrders:
    def test_tuple_sorted(self):
        orders = supported_orders()
        assert list(orders) == sorted(orders)

    def test_contains_3_5_7(self):
        orders = supported_orders()
        for o in (3, 5, 7):
            assert o in orders

    def test_matches_module_constant(self):
        assert supported_orders() == SUPPORTED_ORDERS


# ============================================================================
# Test Class 2 - Construction invariants
# ============================================================================

class TestQuadratureConstruction:
    @pytest.mark.parametrize("order", [3, 5, 7])
    def test_returns_LebedevQuadrature(self, order):
        q = lebedev_quadrature(order)
        assert isinstance(q, LebedevQuadrature)
        assert q.order == order

    @pytest.mark.parametrize("order,expected_n", [(3, 6), (5, 14), (7, 26)])
    def test_node_count_matches_standard(self, order, expected_n):
        q = lebedev_quadrature(order)
        assert q.n_nodes == expected_n

    @pytest.mark.parametrize("order", [3, 5, 7])
    def test_weights_sum_to_one(self, order):
        q = lebedev_quadrature(order)
        assert q.weights.sum() == pytest.approx(1.0, abs=1e-14)

    @pytest.mark.parametrize("order", [3, 5, 7])
    def test_nodes_on_unit_sphere(self, order):
        q = lebedev_quadrature(order)
        norms = np.linalg.norm(q.nodes, axis=1)
        assert np.allclose(norms, 1.0, atol=1e-14)

    @pytest.mark.parametrize("order", [3, 5, 7])
    def test_weights_positive(self, order):
        q = lebedev_quadrature(order)
        assert np.all(q.weights > 0)

    def test_frozen_dataclass(self):
        q = lebedev_quadrature(5)
        with pytest.raises(Exception):
            q.order = 99


# ============================================================================
# Test Class 3 - Y_ℓ^0 exactness
# ============================================================================

class TestYLExactness:
    """Lebedev rule of order n is exact for Y_ℓ^m with ℓ ≤ n."""

    @pytest.mark.parametrize("ell", range(6))
    def test_order_5_exact_up_to_ell_5(self, ell):
        q = lebedev_quadrature(5)
        passes, err = verify_spherical_harmonic_exactness(
            q, ell, tolerance=1e-12,
        )
        assert passes, f"ell={ell}, err={err:.2e}"

    def test_order_5_fails_at_ell_6(self):
        # Beyond exactness; not a bug, just boundary
        q = lebedev_quadrature(5)
        passes, err = verify_spherical_harmonic_exactness(
            q, 6, tolerance=1e-12,
        )
        assert not passes
        assert err > 0.01   # noticeable error

    @pytest.mark.parametrize("ell", range(8))
    def test_order_7_exact_up_to_ell_7(self, ell):
        q = lebedev_quadrature(7)
        passes, err = verify_spherical_harmonic_exactness(
            q, ell, tolerance=1e-12,
        )
        assert passes, f"ell={ell}, err={err:.2e}"

    def test_Y_00_normalization(self):
        # ∫Y_0^0 dΩ/(4π) = 1/√(4π) exactly
        q = lebedev_quadrature(5)
        _, err = verify_spherical_harmonic_exactness(q, 0, tolerance=1e-14)
        assert err < 1e-14


# ============================================================================
# Test Class 4 - Monomial exactness
# ============================================================================

class TestMonomialExactness:
    """Polynomial exactness degrees for cartesian monomials."""

    def test_constant_is_unity(self):
        q = lebedev_quadrature(5)
        passes, obs, exp = verify_monomial_integration(q, (0, 0, 0))
        assert passes
        assert obs == pytest.approx(1.0, abs=1e-14)

    @pytest.mark.parametrize("powers", [
        (1, 0, 0), (3, 0, 0), (1, 1, 0), (2, 1, 0),
    ])
    def test_odd_power_integrates_to_zero(self, powers):
        q = lebedev_quadrature(5)
        passes, obs, _ = verify_monomial_integration(q, powers)
        assert passes
        assert abs(obs) < 1e-14

    @pytest.mark.parametrize("powers", [
        (2, 0, 0), (4, 0, 0), (2, 2, 0), (2, 0, 2),
    ])
    def test_even_degree_under_order_5_exact(self, powers):
        q = lebedev_quadrature(5)
        deg = sum(powers)
        assert deg <= 5
        passes, _, _ = verify_monomial_integration(q, powers)
        assert passes

    def test_degree_6_not_guaranteed_exact_at_order_5(self):
        q = lebedev_quadrature(5)
        passes, obs, exp = verify_monomial_integration(q, (6, 0, 0))
        # Not asserted as fail-exact, but observed differs from analytic
        assert abs(obs - exp) > 1e-6

    def test_permutation_symmetry(self):
        """∫x²y² = ∫y²x² = ∫x²z² = etc. under octahedral symmetry."""
        q = lebedev_quadrature(5)
        _, obs_xy, _ = verify_monomial_integration(q, (2, 2, 0))
        _, obs_yz, _ = verify_monomial_integration(q, (0, 2, 2))
        _, obs_xz, _ = verify_monomial_integration(q, (2, 0, 2))
        assert obs_xy == pytest.approx(obs_yz, rel=1e-14)
        assert obs_xy == pytest.approx(obs_xz, rel=1e-14)


# ============================================================================
# Test Class 5 - Integration APIs
# ============================================================================

class TestIntegrationAPIs:
    def test_integrate_constant_is_one(self):
        q = lebedev_quadrature(5)
        result = integrate_on_sphere(lambda n: 1.0, q)
        assert result == pytest.approx(1.0, abs=1e-14)

    def test_integrate_z_squared_is_one_third(self):
        # ⟨z²⟩ = 1/3
        q = lebedev_quadrature(5)
        result = integrate_on_sphere(lambda n: float(n[2] ** 2), q)
        assert result == pytest.approx(1.0 / 3.0, rel=1e-14)

    def test_integrate_vectorized_matches_callable(self):
        q = lebedev_quadrature(5)
        f_vals = q.nodes[:, 2] ** 2
        result_vec = integrate_vectorized(f_vals, q)
        result_call = integrate_on_sphere(lambda n: float(n[2] ** 2), q)
        assert result_vec == pytest.approx(result_call, rel=1e-14)

    def test_integrate_vectorized_rejects_wrong_shape(self):
        q = lebedev_quadrature(5)
        wrong = np.ones(q.n_nodes - 1)
        with pytest.raises(ValueError, match="entries"):
            integrate_vectorized(wrong, q)


# ============================================================================
# Test Class 6 - Validation and error paths
# ============================================================================

class TestValidation:
    def test_rejects_unsupported_order(self):
        with pytest.raises(ValueError, match="order"):
            lebedev_quadrature(4)

    def test_rejects_order_zero(self):
        with pytest.raises(ValueError, match="order"):
            lebedev_quadrature(0)

    def test_verify_spherical_harmonic_rejects_negative_ell(self):
        q = lebedev_quadrature(5)
        with pytest.raises(ValueError, match="ell"):
            verify_spherical_harmonic_exactness(q, -1)

    def test_verify_monomial_rejects_negative_power(self):
        q = lebedev_quadrature(5)
        with pytest.raises(ValueError, match="powers"):
            verify_monomial_integration(q, (-1, 0, 0))
