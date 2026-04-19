"""
tests/test_laguerre_basis.py
=============================

Week 2 Day 1 test suite for the Paper I Laguerre basis module.

Mathematical identities verified:
  §1 — Generalized Laguerre polynomials (closed-form low-order + recurrence)
  §2 — Derivative identity: d/dx L_s^α = −L_{s-1}^{α+1}
  §3 — Orthogonality against w(x) = x^α e^{-x} on [0, ∞)
  §4 — Occupation functions Φ_ξ(z) for all three statistics
  §5 — Statistics moments I_{ξ,n} closed-form vs numerical
  §6 — Temperature scaling I_{ξ,n}(Θ) ∝ Θ^{n+1}
  §7 — PaperIBasis class API
  §8 — Edge cases and error handling

Run
---
    pytest test_laguerre_basis.py -v
"""
from __future__ import annotations

import math
import numpy as np
import pytest
from scipy.special import gamma, zeta
from scipy.integrate import quad

from tsc.charts.laguerre_basis import (
    laguerre_L, laguerre_L_derivative, laguerre_weight, laguerre_norm_squared,
    Xi, occupation_Phi, moment_I, moment_I_numeric,
    PaperIBasis,
)


# ═══════════════════════════════════════════════════════════════
# §1 — Generalized Laguerre polynomials: low-order closed form + recurrence
# ═══════════════════════════════════════════════════════════════

class TestLaguerrePolynomials:
    def test_L_0_is_one(self):
        """L_0^α(x) = 1 for any α, any x."""
        for alpha in [0.0, 0.5, 2.0, 3.5]:
            for x_val in [0.0, 0.5, 1.0, 5.0, 10.0]:
                assert laguerre_L(0, alpha, x_val) == 1.0

    def test_L_1_closed_form(self):
        """L_1^α(x) = 1 + α − x."""
        for alpha in [0.0, 1.0, 2.0]:
            for x_val in [0.0, 1.0, 3.0]:
                expected = 1.0 + alpha - x_val
                assert math.isclose(
                    laguerre_L(1, alpha, x_val), expected, rel_tol=1e-14,
                )

    def test_L_2_closed_form(self):
        """L_2^α(x) = (1/2)[(α+1)(α+2) − 2(α+2)x + x²]."""
        alpha = 2.0
        for x_val in [0.5, 1.0, 2.0, 5.0]:
            expected = 0.5 * (
                (alpha + 1.0) * (alpha + 2.0)
                - 2.0 * (alpha + 2.0) * x_val
                + x_val ** 2
            )
            assert math.isclose(
                laguerre_L(2, alpha, x_val), expected, rel_tol=1e-14,
            )

    def test_recurrence_consistency(self):
        """L_{s+1} computed by recurrence matches direct evaluation."""
        alpha = 2.0
        x_val = 1.5
        for s in [2, 3, 4, 5]:
            # Forward: L_{s+1} from L_s and L_{s-1}
            L_sm1 = laguerre_L(s - 1, alpha, x_val)
            L_s = laguerre_L(s, alpha, x_val)
            expected = (
                (2.0 * s + 1.0 + alpha - x_val) * L_s - (s + alpha) * L_sm1
            ) / (s + 1.0)
            direct = laguerre_L(s + 1, alpha, x_val)
            assert math.isclose(direct, expected, rel_tol=1e-12)

    def test_array_input_returns_array(self):
        x = np.linspace(0, 5, 10)
        result = laguerre_L(3, 2.0, x)
        assert isinstance(result, np.ndarray)
        assert result.shape == x.shape

    def test_scalar_input_returns_scalar(self):
        result = laguerre_L(3, 2.0, 1.5)
        assert isinstance(result, float)

    def test_invalid_s_raises(self):
        with pytest.raises(ValueError, match="s ≥ 0"):
            laguerre_L(-1, 2.0, 1.0)

    def test_invalid_alpha_raises(self):
        with pytest.raises(ValueError, match="α > −1"):
            laguerre_L(2, -1.0, 1.0)


# ═══════════════════════════════════════════════════════════════
# §2 — Derivative identity
# ═══════════════════════════════════════════════════════════════

class TestLaguerreDerivative:
    def test_derivative_of_L0_is_zero(self):
        x = np.array([0.5, 1.0, 2.0, 5.0])
        dL0 = laguerre_L_derivative(0, 2.0, x)
        assert np.allclose(dL0, 0.0)

    def test_derivative_of_L1_is_minus_one(self):
        """d/dx L_1^α(x) = d/dx(1 + α − x) = −1."""
        x = np.linspace(0.1, 5.0, 20)
        dL1 = laguerre_L_derivative(1, 2.0, x)
        # Identity: −L_0^{α+1}(x) = −1
        assert np.allclose(dL1, -1.0)

    def test_derivative_formula_numerical(self):
        """d/dx L_s^α(x) = −L_{s-1}^{α+1}(x) via finite differences.

        Verifies the Paper I identity by comparing numerical derivative
        against the closed-form relationship.
        """
        alpha = 2.0
        x_val = 1.5
        h = 1e-6
        for s in [2, 3, 4, 5]:
            # Numerical derivative
            L_plus = laguerre_L(s, alpha, x_val + h)
            L_minus = laguerre_L(s, alpha, x_val - h)
            dL_numerical = (L_plus - L_minus) / (2.0 * h)
            # Identity
            dL_identity = laguerre_L_derivative(s, alpha, x_val)
            # Check match (numerical O(h²) ≈ 1e-10 error expected)
            assert math.isclose(
                dL_numerical, dL_identity, rel_tol=1e-8, abs_tol=1e-10,
            )


# ═══════════════════════════════════════════════════════════════
# §3 — Orthogonality against w(x) = x^α e^{-x}
# ═══════════════════════════════════════════════════════════════

class TestOrthogonality:
    def test_norm_squared_L0(self):
        """⟨L_0^α, L_0^α⟩ = Γ(α + 1) / 0! = Γ(α + 1)."""
        for alpha in [0.0, 1.0, 2.0, 3.0]:
            expected = gamma(alpha + 1.0)
            assert math.isclose(
                laguerre_norm_squared(0, alpha), expected, rel_tol=1e-14,
            )

    def test_norm_squared_L_s_vs_numerical(self):
        """Γ(s + α + 1) / s! should equal ∫₀^∞ x^α e^{-x} [L_s^α(x)]² dx."""
        alpha = 2.0
        for s in [0, 1, 2, 3]:
            # Closed form
            closed = laguerre_norm_squared(s, alpha)
            # Numerical
            integrand = lambda x: (
                x**alpha * np.exp(-x) * laguerre_L(s, alpha, x) ** 2
            )
            numerical, _ = quad(integrand, 0, np.inf, limit=200)
            assert math.isclose(closed, numerical, rel_tol=1e-8)

    def test_orthogonality_s_neq_sprime(self):
        """⟨L_s^α, L_{s'}^α⟩ = 0 for s ≠ s'."""
        alpha = 2.0
        for s in [0, 1, 2]:
            for sp in [0, 1, 2, 3]:
                if s == sp:
                    continue
                integrand = lambda x: (
                    x**alpha * np.exp(-x)
                    * laguerre_L(s, alpha, x)
                    * laguerre_L(sp, alpha, x)
                )
                inner, _ = quad(integrand, 0, np.inf, limit=200)
                assert abs(inner) < 1e-8, (
                    f"⟨L_{s}, L_{sp}⟩ = {inner} should be 0"
                )


# ═══════════════════════════════════════════════════════════════
# §4 — Occupation functions Φ_ξ(z)
# ═══════════════════════════════════════════════════════════════

class TestOccupationFunction:
    def test_MB_is_exp_minus_z(self):
        """Φ_0(z) = e^{-z}."""
        for z in [0.5, 1.0, 2.0, 5.0]:
            assert math.isclose(
                occupation_Phi(0, z), math.exp(-z), rel_tol=1e-14,
            )

    def test_BE_matches_planck(self):
        """Φ_+(z) = 1/(e^z − 1)."""
        for z in [0.5, 1.0, 2.0, 5.0]:
            expected = 1.0 / (math.exp(z) - 1.0)
            assert math.isclose(
                occupation_Phi(+1, z), expected, rel_tol=1e-14,
            )

    def test_FD_matches_fermi(self):
        """Φ_-(z) = 1/(e^z + 1)."""
        for z in [0.0, 0.5, 1.0, 2.0, 5.0]:
            expected = 1.0 / (math.exp(z) + 1.0)
            assert math.isclose(
                occupation_Phi(-1, z), expected, rel_tol=1e-14,
            )

    def test_FD_at_zero_is_half(self):
        """Φ_-(0) = 1/2 (classical Fermi level)."""
        assert math.isclose(occupation_Phi(-1, 0.0), 0.5, rel_tol=1e-14)

    def test_array_input(self):
        z = np.array([0.5, 1.0, 2.0])
        result = occupation_Phi(+1, z)
        assert isinstance(result, np.ndarray)
        assert result.shape == (3,)

    def test_invalid_xi_raises(self):
        with pytest.raises(ValueError, match="ξ must be"):
            occupation_Phi(2, 1.0)


# ═══════════════════════════════════════════════════════════════
# §5 — Statistics moments: closed-form vs numerical
# ═══════════════════════════════════════════════════════════════

class TestMoments:
    def test_MB_moment_equals_factorial(self):
        """I_{0,n} = n!"""
        for n in [0, 1, 2, 3, 4]:
            expected = math.factorial(n)
            assert math.isclose(moment_I(0, n), expected, rel_tol=1e-14)

    def test_BE_moment_equals_gamma_zeta(self):
        """I_{+,n} = Γ(n+1) ζ(n+1) for n ≥ 1."""
        # Known values
        # n=1: ζ(2) = π²/6 ≈ 1.6449
        # n=2: 2 ζ(3) ≈ 2.4041
        # n=3: 6 ζ(4) = π⁴/15 ≈ 6.4939
        expected_values = {
            1: float(zeta(2)),             # 1! × ζ(2)
            2: 2.0 * float(zeta(3)),        # 2! × ζ(3)
            3: 6.0 * float(zeta(4)),        # 3! × ζ(4)
            4: 24.0 * float(zeta(5)),       # 4! × ζ(5)
        }
        for n, expected in expected_values.items():
            assert math.isclose(moment_I(+1, n), expected, rel_tol=1e-12)

    def test_FD_moment_matches_formula(self):
        """I_{-,n} = (1 − 2^{-n}) Γ(n+1) ζ(n+1) for n ≥ 1."""
        for n in [1, 2, 3, 4]:
            be_moment = moment_I(+1, n)
            expected = (1.0 - 2.0 ** (-n)) * be_moment
            assert math.isclose(moment_I(-1, n), expected, rel_tol=1e-12)

    def test_FD_moment_n0_equals_log2(self):
        """∫₀^∞ 1/(e^x + 1) dx = ln 2."""
        assert math.isclose(moment_I(-1, 0), math.log(2.0), rel_tol=1e-14)

    def test_BE_n0_raises(self):
        """BE monopole diverges — must raise informatively."""
        with pytest.raises(ValueError, match="diverges"):
            moment_I(+1, 0)

    def test_moment_I_closed_form_matches_numerical(self):
        """Closed-form moment_I agrees with scipy quad integration."""
        for xi in [-1, 0, +1]:
            for n in [1, 2, 3]:
                closed = moment_I(xi, n)
                numerical = moment_I_numeric(xi, n)
                assert math.isclose(closed, numerical, rel_tol=1e-6)

    def test_BE_moment_3_is_planck_law(self):
        """I_{+,3} = π⁴/15 — the Stefan-Boltzmann prefactor."""
        # ∫₀^∞ x³/(e^x − 1) dx = π⁴/15
        expected = math.pi ** 4 / 15.0
        assert math.isclose(moment_I(+1, 3), expected, rel_tol=1e-12)


# ═══════════════════════════════════════════════════════════════
# §6 — Temperature scaling
# ═══════════════════════════════════════════════════════════════

class TestTemperatureScaling:
    def test_MB_moment_scales_as_Theta_to_n_plus_one(self):
        """I_{0,n}(Θ) = Θ^{n+1} I_{0,n}(1)."""
        for n in [1, 2, 3]:
            I_at_1 = moment_I(0, n, Theta=1.0)
            I_at_2 = moment_I(0, n, Theta=2.0)
            assert math.isclose(I_at_2, 2.0 ** (n + 1) * I_at_1, rel_tol=1e-14)

    def test_BE_moment_scales_as_Theta_to_n_plus_one(self):
        for n in [1, 2, 3, 4]:
            I_at_1 = moment_I(+1, n, Theta=1.0)
            I_at_Theta = moment_I(+1, n, Theta=0.5)
            assert math.isclose(
                I_at_Theta, 0.5 ** (n + 1) * I_at_1, rel_tol=1e-14,
            )

    def test_invalid_Theta_raises(self):
        with pytest.raises(ValueError, match="Θ"):
            moment_I(0, 2, Theta=0.0)


# ═══════════════════════════════════════════════════════════════
# §7 — PaperIBasis class API
# ═══════════════════════════════════════════════════════════════

class TestPaperIBasis:
    def test_construct_photon_basis(self):
        basis = PaperIBasis(xi=+1, alpha=2.0, s_max=4)
        assert basis.statistics_name() == "BE"

    def test_evaluate_L0(self):
        basis = PaperIBasis(xi=+1, alpha=2.0, s_max=3)
        assert basis.evaluate(0, 1.5) == 1.0

    def test_evaluate_beyond_s_max_raises(self):
        basis = PaperIBasis(xi=+1, alpha=2.0, s_max=2)
        with pytest.raises(IndexError, match="s_max"):
            basis.evaluate(5, 1.5)

    def test_norm_squared_from_basis(self):
        basis = PaperIBasis(xi=+1, alpha=2.0, s_max=3)
        # ⟨L_0, L_0⟩ = Γ(α+1) = Γ(3) = 2
        assert math.isclose(basis.norm_squared(0), 2.0, rel_tol=1e-14)

    def test_occupation_moment_from_basis(self):
        basis = PaperIBasis(xi=+1, alpha=2.0, s_max=3)
        I_3 = basis.occupation_moment(n=3, Theta=1.0)
        assert math.isclose(I_3, math.pi ** 4 / 15.0, rel_tol=1e-12)

    def test_all_three_statistics_families(self):
        for xi, name in [(+1, "BE"), (-1, "FD"), (0, "MB")]:
            basis = PaperIBasis(xi=xi, alpha=2.0)
            assert basis.statistics_name() == name

    def test_invalid_xi_raises(self):
        with pytest.raises(ValueError, match="ξ"):
            PaperIBasis(xi=2, alpha=2.0)

    def test_invalid_alpha_raises(self):
        with pytest.raises(ValueError, match="α"):
            PaperIBasis(xi=+1, alpha=-1.5)


# ═══════════════════════════════════════════════════════════════
# §8 — Sanity: Stefan-Boltzmann prefactor for photons
# ═══════════════════════════════════════════════════════════════

class TestPhysicalSanity:
    def test_photon_energy_density_coefficient(self):
        """For a blackbody, u_γ = (π²/15) (k_B T)⁴ / (ℏc)³.

        In our x-variable: ∫₀^∞ x³/(e^x − 1) dx = π⁴/15. The factor 8π from
        the phase space integration gives the full Stefan-Boltzmann constant.
        """
        I_3 = moment_I(+1, 3, Theta=1.0)
        expected = math.pi ** 4 / 15.0
        assert math.isclose(I_3, expected, rel_tol=1e-12)

    def test_neutrino_to_photon_ratio(self):
        """For the same temperature, ρ_ν / ρ_γ = (7/8) per species.

        From the moment: I_{-,3} / I_{+,3} = 1 − 2^{-3} = 7/8.
        """
        ratio = moment_I(-1, 3) / moment_I(+1, 3)
        assert math.isclose(ratio, 7.0 / 8.0, rel_tol=1e-14)

    def test_BE_vs_MB_at_high_moment(self):
        """In the classical limit (large n), I_{+,n} → I_{0,n} because
        ζ(n) → 1 as n → ∞.
        """
        for n in [10, 15, 20]:
            be = moment_I(+1, n)
            mb = moment_I(0, n)
            # ζ(n+1) very close to 1 at large n
            assert math.isclose(be / mb, float(zeta(n + 1.0)), rel_tol=1e-14)
            # And ratio approaches 1
            assert abs(be / mb - 1.0) < 1e-3


# ═══════════════════════════════════════════════════════════════
# §9 — Week 2 Day 1 extensions: fugacity, stiffness ratios, Gram matrix
# ═══════════════════════════════════════════════════════════════

from tsc.charts.laguerre_basis import (
    xi_moment, I4_over_I3, shear_source_coeff, xi_weight,
    laguerre_inner_product, gram_matrix, verify_mb_orthogonality,
    SpectralStiffness, build_stiffness_table,
)


class TestFugacityMoments:
    """Fugacity-dependent ξ-moments I_n(ξ, η) for η ≠ 0."""

    def test_eta_zero_falls_back_to_moment_I(self):
        for xi in [-1, 0, +1]:
            n = 3
            fallback = xi_moment(n, xi, eta=0.0)
            direct = moment_I(xi, n, 1.0)
            assert math.isclose(fallback, direct, rel_tol=1e-14)

    def test_BE_positive_eta_raises(self):
        """BE admissibility: η ≤ 0 required."""
        with pytest.raises(ValueError, match="η ≤ 0"):
            xi_moment(3, +1, eta=0.5)

    def test_MB_exp_eta_scaling(self):
        """I_n^MB(η) = e^η × n!."""
        for eta in [-1.0, 0.5, 2.0]:
            for n in [2, 3, 4]:
                I = xi_moment(n, 0, eta)
                expected = math.exp(eta) * math.factorial(n)
                assert math.isclose(I, expected, rel_tol=1e-10)

    def test_FD_negative_eta_decreases_I3(self):
        I_eta_zero = xi_moment(3, -1, 0.0)
        I_eta_neg = xi_moment(3, -1, -1.0)
        assert I_eta_neg < I_eta_zero

    def test_BE_negative_eta_decreases_I3(self):
        I_eta_zero = xi_moment(3, +1, 0.0)
        I_eta_neg = xi_moment(3, +1, -0.5)
        assert I_eta_neg < I_eta_zero


class TestSpectralStiffnessRatios:
    """I_4/I_3 and Σ_2 spectral-stiffness values (ch05 §sec:shear-source)."""

    def test_BE_ratio_matches_canonical(self):
        """BE: 24 ζ(5) / (π⁴/15) ≈ 3.8322."""
        from scipy.special import zeta
        expected = 24.0 * float(zeta(5)) / (math.pi ** 4 / 15.0)
        assert math.isclose(I4_over_I3(+1), expected, rel_tol=1e-10)
        assert math.isclose(I4_over_I3(+1), 3.8322, abs_tol=0.001)

    def test_FD_ratio_approximately_4_11(self):
        ratio = I4_over_I3(-1)
        assert math.isclose(ratio, 4.11, abs_tol=0.01)

    def test_MB_ratio_exactly_four(self):
        """MB: Γ(5)/Γ(4) = 4!/3! = 4."""
        assert math.isclose(I4_over_I3(0), 4.0, rel_tol=1e-14)

    def test_Sigma_2_BE(self):
        """Σ_2^{BE} = (8/15) × 3.8322 ≈ 2.044."""
        assert math.isclose(shear_source_coeff(+1), 2.044, abs_tol=0.002)

    def test_Sigma_2_FD(self):
        assert math.isclose(shear_source_coeff(-1), 2.190, abs_tol=0.002)

    def test_Sigma_2_MB_exact(self):
        assert math.isclose(shear_source_coeff(0), 32.0 / 15.0, rel_tol=1e-14)

    def test_ordering_BE_MB_FD(self):
        """Expected ordering: BE < MB < FD."""
        assert I4_over_I3(+1) < I4_over_I3(0) < I4_over_I3(-1)


class TestGramMatrix:
    """Laguerre Gram matrix under physical (ξ-weighted) inner product."""

    def test_MB_gram_is_diagonal(self):
        G = gram_matrix(n_basis=3, xi=0, eta=0.0, alpha=2.0)
        off_diag = G - np.diag(np.diag(G))
        assert np.max(np.abs(off_diag)) < 1e-8

    def test_MB_gram_diagonal_matches_analytical(self):
        """G_{ss}^MB = Γ(s+α+1)/s!. For α=2: (s+2)(s+1)."""
        G = gram_matrix(n_basis=4, xi=0, eta=0.0, alpha=2.0)
        expected_diag = np.array([2.0, 6.0, 12.0, 20.0])
        assert np.allclose(np.diag(G), expected_diag, rtol=1e-8)

    def test_BE_gram_is_NOT_diagonal(self):
        G = gram_matrix(n_basis=3, xi=+1, eta=0.0, alpha=2.0)
        off_diag = G - np.diag(np.diag(G))
        assert np.max(np.abs(off_diag)) > 1e-3

    def test_FD_gram_is_NOT_diagonal(self):
        G = gram_matrix(n_basis=3, xi=-1, eta=0.0, alpha=2.0)
        off_diag = G - np.diag(np.diag(G))
        assert np.max(np.abs(off_diag)) > 1e-3

    def test_gram_matrix_symmetric(self):
        for xi in [-1, 0, +1]:
            G = gram_matrix(n_basis=3, xi=xi, eta=0.0, alpha=2.0)
            assert np.allclose(G, G.T, rtol=1e-10)

    def test_verify_mb_orthogonality(self):
        is_ortho, G, diag = verify_mb_orthogonality(n_basis=5, alpha=2.0, rtol=1e-5)
        assert bool(is_ortho) is True


class TestStiffnessReferenceTable:
    """build_stiffness_table() canonical values."""

    def test_table_has_three_entries(self):
        table = build_stiffness_table()
        assert set(table.keys()) == {'BE', 'FD', 'MB'}

    def test_BE_entry_fields(self):
        table = build_stiffness_table()
        entry = table['BE']
        assert entry.xi == +1
        assert entry.eta == 0.0
        assert math.isclose(entry.I4_over_I3, 3.8322, abs_tol=0.001)
        assert math.isclose(entry.Sigma_2, 2.044, abs_tol=0.002)

    def test_FD_entry_fields(self):
        table = build_stiffness_table()
        entry = table['FD']
        assert entry.xi == -1
        assert math.isclose(entry.I4_over_I3, 4.11, abs_tol=0.01)

    def test_MB_entry_fields(self):
        table = build_stiffness_table()
        entry = table['MB']
        assert entry.xi == 0
        assert math.isclose(entry.I4_over_I3, 4.0, rel_tol=1e-14)
        assert math.isclose(entry.Sigma_2, 32.0 / 15.0, rel_tol=1e-14)

    def test_entries_are_frozen_dataclass(self):
        table = build_stiffness_table()
        entry = table['BE']
        with pytest.raises(Exception):
            entry.xi = 0  # frozen → raises FrozenInstanceError
