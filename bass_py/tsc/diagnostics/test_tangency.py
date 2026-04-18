"""
tests/test_tangency.py
=======================

Week 2 Day 3 test suite for the Paper I tangency diagnostic.

Covers:
  §1 — TangentKind enum and tangent basis construction
  §2 — Weighted inner product (cross-check against laguerre_basis)
  §3 — Gram matrix construction (symmetry, positive-definite)
  §4 — Moment vector computation
  §5 — On-manifold cross-checks (D = 0 to quadrature precision)
  §6 — Off-manifold cross-checks (D > 0 for x² input)
  §7 — Mixed field: fraction on manifold in [0, 1]
  §8 — One-field vs two-field comparisons
  §9 — L_0 leakage sentinel
  §10 — Convenience field constructors
  §11 — Edge cases (singular Gram, invalid xi)

Run
---
    pytest test_tangency.py -v
"""
from __future__ import annotations

import math
import numpy as np
import pytest

from tsc.diagnostics.tangency import (
    TangentKind, tangent_basis,
    weighted_inner_product, build_gram_matrix, build_moment_vector,
    compute_D_diagnostic, TangencyResult,
    on_manifold_field_one_field, on_manifold_field_two_field,
    off_manifold_field_quadratic, mixed_field,
    l0_leakage_residual,
)
from tsc.charts.laguerre_basis import xi_weight, xi_moment


# ═══════════════════════════════════════════════════════════════
# §1 — TangentKind + basis
# ═══════════════════════════════════════════════════════════════

class TestTangentBasis:
    def test_one_field_basis_has_one_element(self):
        basis = tangent_basis(TangentKind.ONE_FIELD)
        assert len(basis) == 1

    def test_two_field_basis_has_two_elements(self):
        basis = tangent_basis(TangentKind.TWO_FIELD)
        assert len(basis) == 2

    def test_one_field_basis_is_identity_function(self):
        basis = tangent_basis(TangentKind.ONE_FIELD)
        x = np.array([0.5, 1.0, 2.0])
        assert np.allclose(basis[0](x), x)

    def test_two_field_first_basis_is_constant_one(self):
        basis = tangent_basis(TangentKind.TWO_FIELD)
        x = np.array([0.5, 1.0, 2.0])
        assert np.allclose(basis[0](x), np.ones_like(x))

    def test_two_field_second_basis_is_identity(self):
        basis = tangent_basis(TangentKind.TWO_FIELD)
        x = np.array([0.5, 1.0, 2.0])
        assert np.allclose(basis[1](x), x)


# ═══════════════════════════════════════════════════════════════
# §2 — Weighted inner product
# ═══════════════════════════════════════════════════════════════

class TestWeightedInnerProduct:
    def test_one_one_matches_xi_moment_2(self):
        """⟨1, 1⟩_{*,s} = ∫ w(x) dx = ∫ x² e^{-x} dx (MB) = 2 = I_2(MB)."""
        one = lambda x: np.ones_like(np.asarray(x, dtype=float))
        ip = weighted_inner_product(one, one, xi=0, eta=0.0)
        assert math.isclose(ip, xi_moment(2, 0, 0.0), rel_tol=1e-7)

    def test_x_x_matches_xi_moment_4(self):
        """⟨x, x⟩_{*,s} = ∫ x² × x² × e^{-x} dx = 4! = 24 (MB)."""
        x_func = lambda x: np.asarray(x, dtype=float)
        ip = weighted_inner_product(x_func, x_func, xi=0, eta=0.0)
        assert math.isclose(ip, xi_moment(4, 0, 0.0), rel_tol=1e-7)

    def test_one_x_matches_xi_moment_3(self):
        """⟨1, x⟩_{*,s} = ∫ x² × x × e^{-x} dx = 3! = 6 (MB)."""
        one = lambda x: np.ones_like(np.asarray(x, dtype=float))
        x_func = lambda x: np.asarray(x, dtype=float)
        ip = weighted_inner_product(one, x_func, xi=0, eta=0.0)
        assert math.isclose(ip, xi_moment(3, 0, 0.0), rel_tol=1e-7)

    def test_BE_inner_product_matches_zeta(self):
        """⟨x, x⟩_{*,BE} = ∫ x⁴/(e^x − 1) dx = 4! × ζ(5) ≈ 24.886."""
        x_func = lambda x: np.asarray(x, dtype=float)
        ip = weighted_inner_product(x_func, x_func, xi=+1, eta=0.0)
        assert math.isclose(ip, xi_moment(4, +1, 0.0), rel_tol=1e-7)


# ═══════════════════════════════════════════════════════════════
# §3 — Gram matrix properties
# ═══════════════════════════════════════════════════════════════

class TestGramMatrix:
    def test_one_field_gram_is_1x1(self):
        basis = tangent_basis(TangentKind.ONE_FIELD)
        G = build_gram_matrix(basis, xi=0)
        assert G.shape == (1, 1)

    def test_two_field_gram_is_2x2(self):
        basis = tangent_basis(TangentKind.TWO_FIELD)
        G = build_gram_matrix(basis, xi=0)
        assert G.shape == (2, 2)

    def test_gram_symmetric(self):
        for kind in [TangentKind.ONE_FIELD, TangentKind.TWO_FIELD]:
            basis = tangent_basis(kind)
            for xi in [-1, 0, +1]:
                G = build_gram_matrix(basis, xi=xi)
                assert np.allclose(G, G.T, rtol=1e-10)

    def test_gram_positive_definite(self):
        """All eigenvalues > 0 (Gram matrix of linearly independent functions)."""
        for kind in [TangentKind.ONE_FIELD, TangentKind.TWO_FIELD]:
            basis = tangent_basis(kind)
            for xi in [-1, 0, +1]:
                G = build_gram_matrix(basis, xi=xi)
                eigs = np.linalg.eigvalsh(G)
                assert np.all(eigs > 0), (
                    f"Gram eigenvalues: {eigs} for kind={kind}, ξ={xi}"
                )

    def test_two_field_MB_gram_values(self):
        """For MB: G_{11} = ⟨1,1⟩ = I_2 = 2; G_{12} = ⟨1,x⟩ = I_3 = 6;
        G_{22} = ⟨x,x⟩ = I_4 = 24."""
        basis = tangent_basis(TangentKind.TWO_FIELD)
        G = build_gram_matrix(basis, xi=0)
        assert math.isclose(G[0, 0], 2.0, rel_tol=1e-7)
        assert math.isclose(G[0, 1], 6.0, rel_tol=1e-7)
        assert math.isclose(G[1, 1], 24.0, rel_tol=1e-7)


# ═══════════════════════════════════════════════════════════════
# §4 — Moment vector
# ═══════════════════════════════════════════════════════════════

class TestMomentVector:
    def test_moment_vector_G_equals_x_one_field(self):
        """For G = x: b = ⟨x, x⟩ = 24 (MB)."""
        basis = tangent_basis(TangentKind.ONE_FIELD)
        b = build_moment_vector(on_manifold_field_one_field(1.0), basis, xi=0)
        assert b.shape == (1,)
        assert math.isclose(b[0], 24.0, rel_tol=1e-7)

    def test_moment_vector_G_equals_x_two_field(self):
        """For G = x: b_1 = ⟨1, x⟩ = 6, b_2 = ⟨x, x⟩ = 24 (MB)."""
        basis = tangent_basis(TangentKind.TWO_FIELD)
        b = build_moment_vector(on_manifold_field_one_field(1.0), basis, xi=0)
        assert b.shape == (2,)
        assert math.isclose(b[0], 6.0, rel_tol=1e-7)
        assert math.isclose(b[1], 24.0, rel_tol=1e-7)


# ═══════════════════════════════════════════════════════════════
# §5 — On-manifold cross-checks (Thm 6 tangent case)
# ═══════════════════════════════════════════════════════════════

class TestOnManifold:
    """When G ∈ V_s exactly, D_{s,≥2} = 0 to quadrature precision."""

    def test_G_equals_x_is_tangent_one_field_MB(self):
        """G = x ∈ span{x}. D_{≥2} should be machine zero."""
        result = compute_D_diagnostic(
            on_manifold_field_one_field(1.0),
            TangentKind.ONE_FIELD, xi=0,
        )
        assert result.D < 1e-7
        assert result.is_tangent

    def test_G_equals_x_is_tangent_one_field_BE(self):
        result = compute_D_diagnostic(
            on_manifold_field_one_field(1.0),
            TangentKind.ONE_FIELD, xi=+1,
        )
        assert result.is_tangent

    def test_G_equals_x_is_tangent_one_field_FD(self):
        result = compute_D_diagnostic(
            on_manifold_field_one_field(1.0),
            TangentKind.ONE_FIELD, xi=-1,
        )
        assert result.is_tangent

    def test_G_equals_1_plus_halfx_tangent_two_field(self):
        """G = 1 + 0.5x ∈ span{1, x}."""
        for xi in [-1, 0, +1]:
            result = compute_D_diagnostic(
                on_manifold_field_two_field(1.0, 0.5),
                TangentKind.TWO_FIELD, xi=xi,
            )
            assert result.is_tangent, (
                f"ξ={xi}: D={result.D}, rel_res={result.relative_residual}"
            )

    def test_recovered_slope_matches_input(self):
        """If G = 2×x, regression should recover coefficient c ≈ 2 (1-field)."""
        slope = 2.0
        result = compute_D_diagnostic(
            on_manifold_field_one_field(slope),
            TangentKind.ONE_FIELD, xi=0,
        )
        assert math.isclose(result.coefficients[0], slope, rel_tol=1e-6)

    def test_recovered_intercept_slope_match_input(self):
        """If G = 1 + 0.5x, 2-field regression gives (c_1, c_2) ≈ (1, 0.5)."""
        result = compute_D_diagnostic(
            on_manifold_field_two_field(1.0, 0.5),
            TangentKind.TWO_FIELD, xi=0,
        )
        assert math.isclose(result.coefficients[0], 1.0, rel_tol=1e-6)
        assert math.isclose(result.coefficients[1], 0.5, rel_tol=1e-6)

    def test_fraction_on_manifold_unity_for_tangent(self):
        result = compute_D_diagnostic(
            on_manifold_field_two_field(1.0, 0.3),
            TangentKind.TWO_FIELD, xi=0,
        )
        assert math.isclose(result.fraction_on_manifold, 1.0, abs_tol=1e-6)


# ═══════════════════════════════════════════════════════════════
# §6 — Off-manifold cross-checks
# ═══════════════════════════════════════════════════════════════

class TestOffManifold:
    """G containing x² or higher is off-manifold."""

    def test_G_equals_xsq_off_manifold_one_field(self):
        """G = x² has both L_0 leakage and x² content → off-manifold."""
        result = compute_D_diagnostic(
            off_manifold_field_quadratic(1.0),
            TangentKind.ONE_FIELD, xi=0,
        )
        assert not result.is_tangent
        assert result.D > 0.1

    def test_G_equals_xsq_off_manifold_two_field(self):
        """Even with span{1, x}, x² mode is off-manifold."""
        result = compute_D_diagnostic(
            off_manifold_field_quadratic(1.0),
            TangentKind.TWO_FIELD, xi=0,
        )
        assert not result.is_tangent
        assert result.D > 0.1

    def test_G_equals_1_is_off_manifold_for_one_field(self):
        """Constant G is NOT on span{x} — correctly flagged as off-manifold."""
        result = compute_D_diagnostic(
            lambda x: 0 * np.asarray(x) + 1.0,
            TangentKind.ONE_FIELD, xi=0,
        )
        assert not result.is_tangent
        # Actually should be significantly off: relative residual > 0.3
        assert result.relative_residual > 0.3

    def test_G_equals_1_is_on_manifold_for_two_field(self):
        """Constant G IS on span{1, x} — correctly flagged as tangent."""
        result = compute_D_diagnostic(
            lambda x: 0 * np.asarray(x) + 1.0,
            TangentKind.TWO_FIELD, xi=0,
        )
        assert result.is_tangent

    def test_two_field_reduces_residual_vs_one_field(self):
        """Adding the constant basis reduces residual when G has a constant mode."""
        G = mixed_field(a=1.0, b=0.5, c=0.1)  # with constant part
        r1 = compute_D_diagnostic(G, TangentKind.ONE_FIELD, xi=0)
        r2 = compute_D_diagnostic(G, TangentKind.TWO_FIELD, xi=0)
        # 2-field projection should leave less residual than 1-field
        assert r2.D < r1.D


# ═══════════════════════════════════════════════════════════════
# §7 — Mixed fields: fraction analysis
# ═══════════════════════════════════════════════════════════════

class TestMixedFields:
    def test_fraction_on_manifold_in_unit_interval(self):
        result = compute_D_diagnostic(
            mixed_field(1.0, 0.5, 0.3),
            TangentKind.TWO_FIELD, xi=+1,
        )
        assert 0 <= result.fraction_on_manifold <= 1

    def test_high_x_squared_lowers_on_manifold_fraction(self):
        """Increasing x² content reduces on-manifold fraction."""
        r_low = compute_D_diagnostic(
            mixed_field(1.0, 0.5, 0.01),
            TangentKind.TWO_FIELD, xi=0,
        )
        r_high = compute_D_diagnostic(
            mixed_field(1.0, 0.5, 0.5),
            TangentKind.TWO_FIELD, xi=0,
        )
        assert r_high.fraction_on_manifold < r_low.fraction_on_manifold


# ═══════════════════════════════════════════════════════════════
# §8 — Statistics comparison
# ═══════════════════════════════════════════════════════════════

class TestStatisticsComparison:
    def test_D_diagnostic_finite_for_all_statistics(self):
        for xi in [-1, 0, +1]:
            result = compute_D_diagnostic(
                off_manifold_field_quadratic(1.0),
                TangentKind.TWO_FIELD, xi=xi,
            )
            assert math.isfinite(result.D)
            assert math.isfinite(result.D_sq)
            assert result.D >= 0

    def test_relative_residual_nonnegative(self):
        for xi in [-1, 0, +1]:
            result = compute_D_diagnostic(
                mixed_field(1.0, 0.5, 0.3),
                TangentKind.TWO_FIELD, xi=xi,
            )
            assert result.relative_residual >= 0


# ═══════════════════════════════════════════════════════════════
# §9 — L_0 leakage (Paper I Lemma B.1, Prop 8)
# ═══════════════════════════════════════════════════════════════

class TestL0Leakage:
    def test_l0_leakage_consistent_for_pure_x(self):
        """For G = x, both naive and exact should give D ≈ 0."""
        G = on_manifold_field_one_field(1.0)
        D_naive, D_exact = l0_leakage_residual(G, xi=0)
        assert D_naive < 1e-6
        assert D_exact < 1e-6

    def test_l0_leakage_detects_constant_mode(self):
        """For G = 1 + x, the naive span{x} projection treats 1 as off-manifold."""
        G = lambda x: 1.0 + np.asarray(x, dtype=float)
        D_naive, D_exact = l0_leakage_residual(G, xi=0)
        # Naive and exact are equivalent for 1-field (same weighted projection);
        # the point is that both correctly flag the L_0 leakage as off-manifold.
        assert D_naive > 0.1
        assert D_exact > 0.1


# ═══════════════════════════════════════════════════════════════
# §10 — Convenience field constructors
# ═══════════════════════════════════════════════════════════════

class TestConvenienceFields:
    def test_on_manifold_field_one_field_evaluates(self):
        G = on_manifold_field_one_field(2.5)
        x = np.array([0.5, 1.0, 2.0])
        assert np.allclose(G(x), 2.5 * x)

    def test_on_manifold_field_two_field_evaluates(self):
        G = on_manifold_field_two_field(0.7, 1.3)
        x = np.array([0.5, 1.0, 2.0])
        assert np.allclose(G(x), 0.7 + 1.3 * x)

    def test_quadratic_field_evaluates(self):
        G = off_manifold_field_quadratic(3.0)
        x = np.array([2.0])
        assert math.isclose(G(x)[0], 12.0)

    def test_mixed_field_evaluates(self):
        G = mixed_field(1.0, 2.0, 3.0)
        x = np.array([2.0])
        # 1 + 2×2 + 3×4 = 17
        assert math.isclose(G(x)[0], 17.0)


# ═══════════════════════════════════════════════════════════════
# §11 — Edge cases
# ═══════════════════════════════════════════════════════════════

class TestEdgeCases:
    def test_unknown_tangent_kind_raises(self):
        class FakeKind:
            pass
        with pytest.raises(ValueError, match="Unknown TangentKind"):
            tangent_basis(FakeKind())

    def test_result_attributes_all_finite(self):
        result = compute_D_diagnostic(
            mixed_field(1.0, 0.5, 0.3),
            TangentKind.TWO_FIELD, xi=0,
        )
        assert math.isfinite(result.tangent_norm_sq)
        assert math.isfinite(result.total_norm_sq)
        assert math.isfinite(result.D_sq)
        assert math.isfinite(result.D)

    def test_D_sq_nonnegative_despite_cancellation(self):
        """Even when floating-point cancellation gives tiny negative D_sq,
        we clamp to 0 (cannot have imaginary D)."""
        G = on_manifold_field_one_field(1.0)  # should give D ≈ 0
        result = compute_D_diagnostic(G, TangentKind.ONE_FIELD, xi=0)
        assert result.D_sq >= 0
        assert result.D >= 0

    def test_gram_matrix_returned_in_result(self):
        result = compute_D_diagnostic(
            on_manifold_field_one_field(1.0),
            TangentKind.ONE_FIELD, xi=0,
        )
        assert result.gram_matrix.shape == (1, 1)
        assert result.moment_vector.shape == (1,)
