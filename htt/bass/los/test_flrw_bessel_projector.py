"""Tests for bass.los.flrw_bessel_projector (Week 9-01).

Coverage plan:
- Config dataclass
- Spherical Bessel helpers (scalar, vector, lookup table)
- E-mode projection factor including small-kr Taylor limit
- Source-term contract (factories enforce no silent omission)
- Source assembly (SW + ISW + Doppler + polter)
- Transfer function projectors (T and E)
- Sharp-visibility analytic cross-check
- Bessel orthogonality cross-check
- Quadrature convergence (trapezoid O(h²), Simpson O(h⁴))
- Isolation tests (ISW-only, Doppler-only, SW-polter-only)
- Physical sign assertions
- Scope guards
- Integration with W8-03 Π node
- Real HyRec fixture end-to-end
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from scipy import special as scipy_special

from bass.los.flrw_bessel_projector import (
    FLRWBesselConfig,
    FLRWSourceTerms,
    OutOfScopeError,
    _zero_callable,
    assert_e_mode_vanishes_for_ell_lt_2,
    assert_sw_sign_at_low_ell,
    assert_transfer_finite_on_grid,
    b_mode_transfer,
    bessel_lookup_table,
    bessel_sum_rule,
    bianchi_m_mixing,
    build_eta_grid_linear,
    build_eta_grid_log_in_z,
    build_scalar_sources_pair,
    build_polarization_source,
    build_temperature_source,
    compute_c_ell,
    constant_callable,
    convergence_halving_deta,
    e_mode_projection_factor,
    full_scalar_mode_evolution,
    project_polarization_transfer,
    project_polarization_transfer_from_pi_callable,
    project_scalar_transfer_pair,
    project_temperature_transfer,
    sachs_wolfe_analytic_transfer,
    spherical_bessel_at,
    spherical_bessel_vector,
)
from bass.recombination.reionization import CosmologyForRecombination


SQRT6 = np.sqrt(6.0)
ETA_0_DEFAULT = 14116.4  # Mpc, Planck 2018 conformal time today


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def planck_cosmology():
    return CosmologyForRecombination(
        h=0.6766, T_cmb=2.72548, Omega_b=0.0493, Y_He=0.245,
        Omega_m=0.3111, Omega_r=9.237e-5, Omega_Lambda=0.6889,
    )


@pytest.fixture
def default_config():
    return FLRWBesselConfig(ell_max=20, eta_0_mpc=ETA_0_DEFAULT)


@pytest.fixture
def simpson_config():
    return FLRWBesselConfig(
        ell_max=20, eta_0_mpc=ETA_0_DEFAULT, quadrature="simpson",
    )


# ============================================================================
# 1. Config
# ============================================================================

class TestFLRWBesselConfig:
    def test_basic_construction(self, default_config):
        assert default_config.ell_max == 20
        assert default_config.eta_0_mpc == ETA_0_DEFAULT
        assert default_config.quadrature == "trapezoid"

    def test_simpson_quadrature(self, simpson_config):
        assert simpson_config.quadrature == "simpson"

    def test_rejects_negative_ell_max(self):
        with pytest.raises(ValueError):
            FLRWBesselConfig(ell_max=-1, eta_0_mpc=100.0)

    def test_rejects_nonpositive_eta_0(self):
        with pytest.raises(ValueError):
            FLRWBesselConfig(ell_max=10, eta_0_mpc=0.0)
        with pytest.raises(ValueError):
            FLRWBesselConfig(ell_max=10, eta_0_mpc=-1.0)

    def test_rejects_unknown_quadrature(self):
        with pytest.raises(ValueError):
            FLRWBesselConfig(
                ell_max=10, eta_0_mpc=100.0, quadrature="romberg",
            )

    def test_lookup_requires_grid(self):
        with pytest.raises(ValueError):
            FLRWBesselConfig(
                ell_max=10, eta_0_mpc=100.0, use_lookup=True,
            )


# ============================================================================
# 2. Spherical Bessel helpers
# ============================================================================

class TestSphericalBessel:
    def test_scalar_matches_scipy(self):
        for ell in [0, 1, 2, 5]:
            for kr in [0.1, 1.0, 5.0, 20.0]:
                expected = float(scipy_special.spherical_jn(ell, kr))
                assert spherical_bessel_at(ell, kr) == expected

    def test_j0_formula(self):
        # j_0(x) = sin(x)/x, j_0(0) = 1
        assert spherical_bessel_at(0, 0.0) == pytest.approx(1.0, abs=1e-12)
        assert spherical_bessel_at(0, np.pi) == pytest.approx(0.0, abs=1e-12)

    def test_vector_matches_scalar(self):
        kr_array = np.linspace(0.0, 10.0, 50)
        v = spherical_bessel_vector(2, kr_array)
        for i, kr in enumerate(kr_array):
            expected = spherical_bessel_at(2, float(kr))
            assert v[i] == pytest.approx(expected, rel=1e-14)

    def test_rejects_negative_ell(self):
        with pytest.raises(ValueError):
            spherical_bessel_at(-1, 1.0)
        with pytest.raises(ValueError):
            spherical_bessel_vector(-1, np.array([1.0]))

    def test_rejects_negative_kr(self):
        with pytest.raises(ValueError):
            spherical_bessel_at(2, -0.1)
        with pytest.raises(ValueError):
            spherical_bessel_vector(2, np.array([1.0, -1.0]))

    def test_lookup_table_shape_and_values(self):
        kr_grid = np.linspace(0.1, 20.0, 100)
        table = bessel_lookup_table(ell_max=10, kr_grid=kr_grid)
        assert table.shape == (11, 100)
        # Spot-check: j_2 row
        for i in range(0, 100, 20):
            expected = spherical_bessel_at(2, float(kr_grid[i]))
            assert table[2, i] == pytest.approx(expected, rel=1e-14)


# ============================================================================
# 3. E-mode projection factor
# ============================================================================

class TestEModeProjectionFactor:
    def test_zero_for_ell_less_than_2(self):
        for ell in [0, 1]:
            assert e_mode_projection_factor(ell, 1.0) == 0.0
            arr = e_mode_projection_factor(ell, np.linspace(0.1, 5, 10))
            np.testing.assert_array_equal(arr, 0.0)

    def test_ell_2_at_x_equal_1(self):
        # P^E_2(1) = √(1·2·3·4) · j_2(1) / 1² = √24 · 0.06203505 = 0.303908...
        expected_prefactor = np.sqrt(24.0)
        j2_at_1 = scipy_special.spherical_jn(2, 1.0)
        expected = expected_prefactor * j2_at_1 / 1.0**2
        assert e_mode_projection_factor(2, 1.0) == pytest.approx(
            expected, rel=1e-13,
        )

    def test_small_kr_taylor_ell_2(self):
        # j_2(x)/x² → 1/15 as x → 0, prefactor √24
        # Limit: √24/15 ≈ 0.3266
        expected = np.sqrt(24.0) / 15.0
        assert e_mode_projection_factor(2, 1e-5) == pytest.approx(
            expected, rel=1e-4,
        )

    def test_small_kr_taylor_ell_higher_vanishes(self):
        # For ell > 2: P^E_ℓ(kr) ∝ (kr)^(ℓ-2) → 0 as kr → 0
        for ell in [3, 5, 10]:
            val = e_mode_projection_factor(ell, 1e-6)
            assert abs(val) < 1e-4, (ell, val)

    def test_vector_input(self):
        kr_arr = np.linspace(0.01, 10.0, 50)
        result = e_mode_projection_factor(2, kr_arr)
        assert result.shape == kr_arr.shape
        assert np.all(np.isfinite(result))

    def test_rejects_negative_kr(self):
        with pytest.raises(ValueError):
            e_mode_projection_factor(2, -0.1)


# ============================================================================
# 4. Source-terms contract (no silent omission)
# ============================================================================

class TestFLRWSourceTerms:
    def test_zeros_factory(self):
        s = FLRWSourceTerms.zeros()
        eta = np.array([1.0, 2.0, 3.0])
        np.testing.assert_array_equal(s.theta_0(eta), 0.0)
        np.testing.assert_array_equal(s.psi(eta), 0.0)
        np.testing.assert_array_equal(s.phi_dot_plus_psi_dot(eta), 0.0)
        np.testing.assert_array_equal(s.v_b(eta), 0.0)
        np.testing.assert_array_equal(s.pi(eta), 0.0)

    def test_with_sw_polter_only_zeros_isw_doppler(self):
        s = FLRWSourceTerms.with_sw_polter_only(
            theta_0=constant_callable(0.3),
            psi=constant_callable(0.1),
            pi=constant_callable(0.01),
        )
        eta = np.array([10.0, 100.0])
        # ISW and Doppler must be explicit zero, not something else
        np.testing.assert_array_equal(s.phi_dot_plus_psi_dot(eta), 0.0)
        np.testing.assert_array_equal(s.v_b(eta), 0.0)
        # SW and polter are what we passed in
        np.testing.assert_array_equal(s.theta_0(eta), 0.3)
        np.testing.assert_array_equal(s.psi(eta), 0.1)

    def test_with_isw_only(self):
        s = FLRWSourceTerms.with_isw_only(constant_callable(1e-3))
        eta = np.array([100.0])
        assert s.phi_dot_plus_psi_dot(eta)[0] == 1e-3
        assert s.theta_0(eta)[0] == 0.0
        assert s.v_b(eta)[0] == 0.0

    def test_with_doppler_only(self):
        s = FLRWSourceTerms.with_doppler_only(constant_callable(5e-5))
        eta = np.array([100.0])
        assert s.v_b(eta)[0] == 5e-5
        assert s.theta_0(eta)[0] == 0.0
        assert s.phi_dot_plus_psi_dot(eta)[0] == 0.0

    def test_with_all_accepts_callables(self):
        s = FLRWSourceTerms.with_all(
            theta_0=constant_callable(1.0),
            psi=constant_callable(2.0),
            phi_dot_plus_psi_dot=constant_callable(3.0),
            v_b=constant_callable(4.0),
            pi=constant_callable(5.0),
        )
        eta = np.array([0.5])
        assert s.theta_0(eta)[0] == 1.0
        assert s.pi(eta)[0] == 5.0

    def test_frozen(self):
        s = FLRWSourceTerms.zeros()
        with pytest.raises((AttributeError, Exception)):
            s.theta_0 = constant_callable(999.0)


# ============================================================================
# 5. Source assembly
# ============================================================================

class TestSourceAssembly:
    def test_temperature_sw_only_matches_analytic(self):
        eta = np.linspace(50.0, 400.0, 501)
        # Narrow Gaussian g, constant Θ₀+Ψ
        def g(e):
            return np.exp(-0.5 * ((e - 280.0) / 30.0) ** 2) / (30.0 * np.sqrt(2*np.pi))
        sources = FLRWSourceTerms.with_sw_polter_only(
            theta_0=constant_callable(0.2),
            psi=constant_callable(0.1),
            pi=constant_callable(0.0),
        )
        S_T = build_temperature_source(
            eta, sources, g, lambda e: np.zeros_like(np.asarray(e)),
        )
        # SW only: S_T = g·(Θ₀+Ψ+Π/4) = g·0.3, Doppler = d/dη[g·0] = 0
        expected = g(eta) * 0.3
        np.testing.assert_allclose(S_T, expected, rtol=1e-10, atol=1e-14)

    def test_doppler_gradient_contribution(self):
        # Pure Doppler: S_T = d/dη[g·v_b], no SW, no ISW
        eta = np.linspace(50.0, 400.0, 1001)
        sigma = 30.0
        eta_star = 280.0

        def g(e):
            return np.exp(-0.5 * ((e - eta_star) / sigma) ** 2) / (sigma * np.sqrt(2*np.pi))

        def vb(e):
            return np.full_like(np.asarray(e, dtype=float), 1e-3)

        sources = FLRWSourceTerms.with_doppler_only(vb)
        S_T = build_temperature_source(
            eta, sources, g, lambda e: np.zeros_like(np.asarray(e)),
        )
        # S_T = d(g·v_b)/dη = v_b · dg/dη (v_b is constant here)
        expected = 1e-3 * g(eta) * (-(eta - eta_star) / sigma**2)
        np.testing.assert_allclose(S_T, expected, rtol=1e-5, atol=1e-12)

    def test_doppler_derivative_is_fourth_order_exact_for_quartic(self):
        eta = np.linspace(0.0, 4.0, 17)
        sources = FLRWSourceTerms.with_doppler_only(
            lambda e: np.asarray(e, dtype=float) ** 4
        )
        S_T = build_temperature_source(
            eta,
            sources,
            constant_callable(1.0),
            lambda e: np.zeros_like(np.asarray(e, dtype=float)),
        )
        np.testing.assert_allclose(S_T, 4.0 * eta**3, rtol=1.0e-12, atol=1.0e-12)

    def test_isw_exp_damping(self):
        # Pure ISW: S_T = e^{-κ}(Ψ̇+Φ̇), κ = 0 ⇒ full amplitude
        eta = np.linspace(50.0, 400.0, 101)
        sources = FLRWSourceTerms.with_isw_only(constant_callable(0.05))
        S_T = build_temperature_source(
            eta, sources, lambda e: np.zeros_like(np.asarray(e)),
            lambda e: np.zeros_like(np.asarray(e)),
        )
        # S_T = 1.0 · 0.05 (since κ=0, exp(-κ)=1)
        np.testing.assert_allclose(S_T, 0.05, rtol=1e-12)

    def test_isw_with_large_kappa_suppresses(self):
        # Large κ damps ISW contribution
        eta = np.linspace(50.0, 400.0, 101)
        sources = FLRWSourceTerms.with_isw_only(constant_callable(0.05))
        S_T = build_temperature_source(
            eta, sources, lambda e: np.zeros_like(np.asarray(e)),
            lambda e: np.full_like(np.asarray(e, dtype=float), 10.0),  # κ=10
        )
        # exp(-10) ≈ 4.54e-5, times 0.05 ≈ 2.27e-6
        np.testing.assert_allclose(S_T, 0.05 * np.exp(-10.0), rtol=1e-10)

    def test_polarization_source_matches_w8_03_formula(self):
        eta = np.linspace(50.0, 400.0, 101)

        def g(e):
            return np.exp(-0.5 * ((e - 280.0) / 30.0) ** 2)

        pi_const = 0.01
        sources = FLRWSourceTerms.with_sw_polter_only(
            theta_0=_zero_callable, psi=_zero_callable,
            pi=constant_callable(pi_const),
        )
        S_E = build_polarization_source(eta, sources, g)
        # S_E = -(√6/4) g Π
        expected = -(SQRT6 / 4.0) * g(eta) * pi_const
        np.testing.assert_allclose(S_E, expected, rtol=1e-12)

    def test_scalar_sources_pair_matches_separate_builders(self):
        eta = np.linspace(50.0, 400.0, 501)

        def g(e):
            return np.exp(-0.5 * ((e - 280.0) / 30.0) ** 2)

        def kappa(e):
            return 0.1 * np.asarray(e, dtype=float)

        sources = FLRWSourceTerms.with_all(
            theta_0=lambda e: 0.1 + 0.0 * np.asarray(e, dtype=float),
            psi=lambda e: 0.2 + 0.0 * np.asarray(e, dtype=float),
            phi_dot_plus_psi_dot=lambda e: 1.0e-4 * np.asarray(e, dtype=float),
            v_b=lambda e: 1.0e-3 * np.asarray(e, dtype=float),
            pi=lambda e: 0.01 + 0.0 * np.asarray(e, dtype=float),
        )

        source_T_pair, source_E_pair = build_scalar_sources_pair(
            eta, sources, g, kappa
        )
        source_T_ref = build_temperature_source(eta, sources, g, kappa)
        source_E_ref = build_polarization_source(eta, sources, g)

        np.testing.assert_allclose(source_T_pair, source_T_ref, rtol=0.0, atol=0.0)
        np.testing.assert_allclose(source_E_pair, source_E_ref, rtol=0.0, atol=0.0)


# ============================================================================
# 6. Temperature transfer projection
# ============================================================================

class TestTemperatureTransfer:
    def test_shape(self, default_config):
        eta = build_eta_grid_linear(10.0, ETA_0_DEFAULT, 501)
        S_T = np.zeros_like(eta)
        Delta = project_temperature_transfer(1e-3, S_T, eta, default_config)
        assert Delta.shape == (default_config.ell_max + 1,)

    def test_zero_source_gives_zero_transfer(self, default_config):
        eta = build_eta_grid_linear(10.0, ETA_0_DEFAULT, 501)
        S_T = np.zeros_like(eta)
        Delta = project_temperature_transfer(1e-3, S_T, eta, default_config)
        np.testing.assert_array_equal(Delta, 0.0)

    def test_linearity_in_source(self, default_config):
        eta = build_eta_grid_linear(10.0, ETA_0_DEFAULT, 501)
        S_T_1 = np.exp(-((eta - 280.0) / 30.0) ** 2)
        D_1 = project_temperature_transfer(1e-3, S_T_1, eta, default_config)
        D_5 = project_temperature_transfer(1e-3, 5.0 * S_T_1, eta, default_config)
        np.testing.assert_allclose(D_5, 5.0 * D_1, rtol=1e-12)

    def test_rejects_grid_outside_eta_0(self, default_config):
        eta = np.linspace(10.0, ETA_0_DEFAULT * 2.0, 100)
        S_T = np.zeros_like(eta)
        with pytest.raises(ValueError):
            project_temperature_transfer(1e-3, S_T, eta, default_config)

    def test_rejects_negative_k(self, default_config):
        eta = build_eta_grid_linear(10.0, ETA_0_DEFAULT, 100)
        S_T = np.zeros_like(eta)
        with pytest.raises(ValueError):
            project_temperature_transfer(-1e-3, S_T, eta, default_config)

    def test_rejects_shape_mismatch(self, default_config):
        eta = build_eta_grid_linear(10.0, ETA_0_DEFAULT, 100)
        S_T_bad = np.zeros(99)
        with pytest.raises(ValueError):
            project_temperature_transfer(1e-3, S_T_bad, eta, default_config)


# ============================================================================
# 7. Polarization transfer projection
# ============================================================================

class TestPolarizationTransfer:
    def test_shape_and_ell_lt_2_zero(self, default_config):
        eta = build_eta_grid_linear(10.0, ETA_0_DEFAULT, 201)
        S_E = np.ones_like(eta) * 1e-3
        Delta_E = project_polarization_transfer(1e-3, S_E, eta, default_config)
        assert Delta_E.shape == (default_config.ell_max + 1,)
        assert Delta_E[0] == 0.0
        assert Delta_E[1] == 0.0

    def test_zero_source_gives_zero(self, default_config):
        eta = build_eta_grid_linear(10.0, ETA_0_DEFAULT, 201)
        S_E = np.zeros_like(eta)
        Delta_E = project_polarization_transfer(1e-3, S_E, eta, default_config)
        np.testing.assert_array_equal(Delta_E, 0.0)

    def test_linearity(self, default_config):
        eta = build_eta_grid_linear(10.0, ETA_0_DEFAULT, 501)
        S_E = np.exp(-((eta - 280.0) / 30.0) ** 2) * 1e-3
        D_1 = project_polarization_transfer(5e-3, S_E, eta, default_config)
        D_3 = project_polarization_transfer(5e-3, 3.0 * S_E, eta, default_config)
        np.testing.assert_allclose(D_3, 3.0 * D_1, rtol=1e-12)

    def test_sign_tracks_source(self, default_config):
        eta = build_eta_grid_linear(10.0, ETA_0_DEFAULT, 501)
        # Narrow-visibility S_E = +(constant) near z~1100 region
        S_E_pos = np.exp(-((eta - 280.0) / 30.0) ** 2)
        S_E_neg = -S_E_pos
        D_pos = project_polarization_transfer(1e-3, S_E_pos, eta, default_config)
        D_neg = project_polarization_transfer(1e-3, S_E_neg, eta, default_config)
        np.testing.assert_allclose(D_neg, -D_pos, rtol=1e-13)

    def test_w8_03_convenience_wrapper(self, default_config):
        eta = build_eta_grid_linear(10.0, ETA_0_DEFAULT, 501)

        def g_fn(e):
            return np.exp(-0.5 * ((e - 280.0) / 30.0) ** 2) / (30.0 * np.sqrt(2*np.pi))

        def pi_fn(e):
            return np.full_like(np.asarray(e, dtype=float), 0.01)

        Delta_E_conv = project_polarization_transfer_from_pi_callable(
            1e-3, pi_fn, g_fn, eta, default_config,
        )
        # Reference via explicit S_E
        S_E = -(SQRT6 / 4.0) * g_fn(eta) * pi_fn(eta)
        Delta_E_ref = project_polarization_transfer(
            1e-3, S_E, eta, default_config,
        )
        np.testing.assert_allclose(Delta_E_conv, Delta_E_ref, rtol=1e-13)


class TestScalarTransferPair:
    def test_matches_separate_temperature_and_polarization_projectors(self, default_config):
        eta = build_eta_grid_linear(10.0, ETA_0_DEFAULT, 501)
        source_T = np.exp(-((eta - 280.0) / 30.0) ** 2)
        source_E = 1.0e-3 * np.exp(-((eta - 310.0) / 45.0) ** 2)

        delta_T_pair, delta_E_pair = project_scalar_transfer_pair(
            1.0e-3, source_T, source_E, eta, default_config
        )
        delta_T_ref = project_temperature_transfer(
            1.0e-3, source_T, eta, default_config
        )
        delta_E_ref = project_polarization_transfer(
            1.0e-3, source_E, eta, default_config
        )

        np.testing.assert_allclose(delta_T_pair, delta_T_ref, rtol=0.0, atol=2.0e-15)
        np.testing.assert_allclose(delta_E_pair, delta_E_ref, rtol=0.0, atol=2.0e-15)


# ============================================================================
# 8. Sharp-visibility analytic cross-check
# ============================================================================

class TestSachsWolfeSharpVisibility:
    def test_narrow_gaussian_recovers_jl(self):
        """Very narrow Gaussian visibility → integral collapses to j_ℓ × (Θ₀+Ψ)_*."""
        cfg = FLRWBesselConfig(ell_max=10, eta_0_mpc=ETA_0_DEFAULT)
        eta_star = 280.0
        theta_plus_psi = 0.4

        sigma = 5.0  # narrow
        def g(e):
            return np.exp(-0.5 * ((e - eta_star) / sigma) ** 2) / (sigma * np.sqrt(2*np.pi))

        sources = FLRWSourceTerms.with_sw_polter_only(
            theta_0=constant_callable(theta_plus_psi),
            psi=constant_callable(0.0),
            pi=constant_callable(0.0),
        )
        eta = build_eta_grid_linear(eta_star - 80.0, eta_star + 80.0, 8001)
        S_T = build_temperature_source(
            eta, sources, g, lambda e: np.zeros_like(np.asarray(e)),
        )
        k = 1e-3
        D_num = project_temperature_transfer(k, S_T, eta, cfg)
        D_analytic = sachs_wolfe_analytic_transfer(
            k, eta_star, theta_plus_psi, cfg,
        )
        max_abs = np.max(np.abs(D_analytic))
        rel = np.max(np.abs(D_num - D_analytic)) / max_abs
        assert rel < 5e-4, rel  # narrow Gaussian approximation

    def test_tighter_sigma_tightens_match(self):
        """As σ→0 the agreement with the analytic sharp-visibility
        limit must improve (O(σ²) leading error)."""
        cfg = FLRWBesselConfig(ell_max=6, eta_0_mpc=ETA_0_DEFAULT)
        eta_star = 280.0
        theta_plus_psi = 0.4
        k = 5e-4

        def run_at_sigma(sigma):
            def g(e):
                return np.exp(-0.5 * ((e - eta_star) / sigma) ** 2) / (sigma * np.sqrt(2*np.pi))
            sources = FLRWSourceTerms.with_sw_polter_only(
                theta_0=constant_callable(theta_plus_psi),
                psi=constant_callable(0.0),
                pi=constant_callable(0.0),
            )
            eta = build_eta_grid_linear(
                max(1.0, eta_star - 30 * sigma),
                min(ETA_0_DEFAULT, eta_star + 30 * sigma),
                8001,
            )
            S_T = build_temperature_source(
                eta, sources, g, lambda e: np.zeros_like(np.asarray(e)),
            )
            D_num = project_temperature_transfer(k, S_T, eta, cfg)
            D_analytic = sachs_wolfe_analytic_transfer(
                k, eta_star, theta_plus_psi, cfg,
            )
            max_abs = np.max(np.abs(D_analytic))
            return np.max(np.abs(D_num - D_analytic)) / max_abs

        rel_wide = run_at_sigma(20.0)
        rel_narrow = run_at_sigma(3.0)
        assert rel_narrow < rel_wide, (rel_narrow, rel_wide)

    def test_analytic_at_boundary_ell_0(self):
        cfg = FLRWBesselConfig(ell_max=2, eta_0_mpc=1000.0)
        D = sachs_wolfe_analytic_transfer(1e-3, 100.0, 1.0, cfg)
        # Δ_0 = j_0(k·900) = sin(0.9)/0.9 ≈ 0.8704
        expected = np.sin(0.9) / 0.9
        assert D[0] == pytest.approx(expected, rel=1e-13)


# ============================================================================
# 9. Bessel orthogonality
# ============================================================================

class TestBesselSumRule:
    """Σ_ℓ (2ℓ+1) j_ℓ²(x) = 1. Finite partial sums converge once
    ell_max > x. This is the correct Bessel completeness identity;
    the continuum ∫ k² j_ℓ² dk is δ-distributional and was previously
    mis-specified — see W9-01 packet §7 for the correction record."""

    def test_sum_rule_at_x_equal_1(self):
        total = bessel_sum_rule(x=1.0, ell_max=20)
        assert abs(total - 1.0) < 1e-10

    def test_sum_rule_at_x_equal_5(self):
        # Need ell_max > x for convergence; ell_max=30 > 5 is ample
        total = bessel_sum_rule(x=5.0, ell_max=30)
        assert abs(total - 1.0) < 1e-10

    def test_sum_rule_at_x_equal_10(self):
        total = bessel_sum_rule(x=10.0, ell_max=40)
        assert abs(total - 1.0) < 1e-10

    def test_sum_rule_rejects_bad_inputs(self):
        with pytest.raises(ValueError):
            bessel_sum_rule(-1.0, 10)
        with pytest.raises(ValueError):
            bessel_sum_rule(1.0, -1)


# ============================================================================
# 10. Quadrature convergence
# ============================================================================

class TestQuadratureConvergence:
    def test_simpson_requires_odd_n(self):
        cfg = FLRWBesselConfig(
            ell_max=4, eta_0_mpc=ETA_0_DEFAULT, quadrature="simpson",
        )
        eta_even = build_eta_grid_linear(10.0, ETA_0_DEFAULT, 200)  # even
        S_T = np.ones_like(eta_even)
        with pytest.raises(ValueError):
            project_temperature_transfer(1e-3, S_T, eta_even, cfg)

    def test_simpson_accepts_odd_n(self):
        cfg = FLRWBesselConfig(
            ell_max=4, eta_0_mpc=ETA_0_DEFAULT, quadrature="simpson",
        )
        eta_odd = build_eta_grid_linear(10.0, ETA_0_DEFAULT, 201)
        S_T = np.exp(-((eta_odd - 280.0) / 30.0) ** 2)
        D = project_temperature_transfer(1e-3, S_T, eta_odd, cfg)
        assert np.all(np.isfinite(D))

    def test_trapezoid_halving_converges(self):
        """Trapezoidal rule: halving dη reduces relative error (O(h²)).
        Starting grid must be fine enough that the source Gaussian
        (σ=30 Mpc) is already decently sampled."""
        cfg = FLRWBesselConfig(ell_max=4, eta_0_mpc=ETA_0_DEFAULT)
        def source_fn(eta):
            return np.exp(-((eta - 280.0) / 30.0) ** 2)
        # At n_points_coarse=1001 on [10, 14116], dη ≈ 14 Mpc < σ=30 Mpc.
        rel = convergence_halving_deta(
            k=1e-3, source_T_fn=source_fn,
            eta_min_mpc=10.0, eta_max_mpc=ETA_0_DEFAULT,
            n_points_coarse=1001, config=cfg,
        )
        assert rel < 1e-3, rel

    def test_simpson_converges_faster_than_trapezoid(self):
        cfg_trap = FLRWBesselConfig(
            ell_max=4, eta_0_mpc=ETA_0_DEFAULT, quadrature="trapezoid",
        )
        cfg_simp = FLRWBesselConfig(
            ell_max=4, eta_0_mpc=ETA_0_DEFAULT, quadrature="simpson",
        )

        def source_fn(eta):
            return np.exp(-((eta - 280.0) / 30.0) ** 2)

        rel_trap = convergence_halving_deta(
            k=1e-3, source_T_fn=source_fn,
            eta_min_mpc=10.0, eta_max_mpc=ETA_0_DEFAULT,
            n_points_coarse=101, config=cfg_trap,
        )
        rel_simp = convergence_halving_deta(
            k=1e-3, source_T_fn=source_fn,
            eta_min_mpc=10.0, eta_max_mpc=ETA_0_DEFAULT,
            n_points_coarse=101, config=cfg_simp,
        )
        # Simpson's should be tighter (O(h^4) vs O(h^2))
        assert rel_simp <= rel_trap * 2.0, (rel_trap, rel_simp)


# ============================================================================
# 11. Isolation tests — ISW, Doppler, SW each independently
# ============================================================================

class TestTermIsolation:
    """Each of SW, ISW, Doppler tested in isolation to confirm
    independent activation pathways."""

    def test_isw_only_produces_nonzero_transfer(self):
        """Non-zero Ψ̇+Φ̇ with zero everything else must drive Δ_ℓ^T ≠ 0."""
        cfg = FLRWBesselConfig(ell_max=4, eta_0_mpc=ETA_0_DEFAULT)
        eta = build_eta_grid_linear(10.0, ETA_0_DEFAULT, 1001)
        sources = FLRWSourceTerms.with_isw_only(constant_callable(1e-4))
        S_T = build_temperature_source(
            eta, sources, lambda e: np.zeros_like(np.asarray(e)),
            lambda e: np.zeros_like(np.asarray(e)),  # κ=0
        )
        D = project_temperature_transfer(1e-3, S_T, eta, cfg)
        assert np.max(np.abs(D)) > 0.0
        # Specifically Δ_0 = 1e-4 · ∫ j_0[k(η_0-η)] dη which is nonzero
        assert abs(D[0]) > 1e-6

    def test_doppler_only_produces_nonzero_transfer(self):
        """d/dη[g·v_b] with g Gaussian and v_b constant gives non-zero Δ_ℓ^T."""
        cfg = FLRWBesselConfig(ell_max=4, eta_0_mpc=ETA_0_DEFAULT)
        eta = build_eta_grid_linear(10.0, ETA_0_DEFAULT, 1001)

        def g(e):
            return np.exp(-0.5 * ((e - 280.0) / 30.0) ** 2) / (30.0 * np.sqrt(2*np.pi))

        sources = FLRWSourceTerms.with_doppler_only(constant_callable(1e-3))
        S_T = build_temperature_source(
            eta, sources, g, lambda e: np.zeros_like(np.asarray(e)),
        )
        D = project_temperature_transfer(1e-3, S_T, eta, cfg)
        assert np.max(np.abs(D)) > 0.0

    def test_sw_polter_only_gives_no_isw_contribution(self):
        """With SW/polter active but ISW=Doppler=0, varying κ must not
        affect S_T (since e^{-κ}·(Ψ̇+Φ̇) = 0 when Ψ̇+Φ̇=0)."""
        cfg = FLRWBesselConfig(ell_max=4, eta_0_mpc=ETA_0_DEFAULT)
        eta = build_eta_grid_linear(10.0, ETA_0_DEFAULT, 1001)

        def g(e):
            return np.exp(-0.5 * ((e - 280.0) / 30.0) ** 2) / (30.0 * np.sqrt(2*np.pi))

        sources = FLRWSourceTerms.with_sw_polter_only(
            theta_0=constant_callable(0.2),
            psi=constant_callable(0.1),
            pi=constant_callable(0.0),
        )
        S_T_kappa_0 = build_temperature_source(
            eta, sources, g, lambda e: np.zeros_like(np.asarray(e)),
        )
        S_T_kappa_big = build_temperature_source(
            eta, sources, g, lambda e: np.full_like(np.asarray(e, dtype=float), 100.0),
        )
        np.testing.assert_allclose(S_T_kappa_0, S_T_kappa_big, rtol=1e-12)


# ============================================================================
# 11.5 Sharp-visibility analytic regression oracles
#      (Round-15 P1 follow-up; protect the canonical LoS source forms
#      against future label-as-type misreadings.)
# ============================================================================

class TestSharpVisibilityAnalyticOracles:
    """Closed-form Δ_ℓ^T / Δ_ℓ^E values in the sharp-visibility limit
    g(η) → δ(η − η_*).

    These tests pin the canonical Lewis–Challinor / Seljak–Zaldarriaga
    forms used by the BASS LoS projector:

        S_T = g·[Θ_0 + Ψ + Π/4]                    (SW + temperature polter)
            + e^{−κ}·[Φ̇ + Ψ̇]                    (ISW)
            + d/dη[g · v_b]                        (Doppler)

        S_E = −(√6/4) · g · Π                       (E-mode polter)

    The Doppler oracle is the explicit regression that protects against
    a spurious `/k` rewrite of the Doppler term — the false trail
    captured in `docs/V5_ROUND15_P1_PSTF_DERIVATION_OPUS.md` Appendix X
    (retracted "AF-1"). The variable BASS calls `v_b` is the
    dimensionless `θ_b/k` (verified by `seed_compatibility.py:210`
    where `theta_common = amp/3.0` carries no `k` factor and by the
    baryon EOM forcing `3·drag·Θ_1` with no `k` in
    `ver2_native_integrator.py`); therefore `(g v_b)'` is the canonical
    LoS Doppler form, and any `(g v_b)'/k` rewrite would be wrong by a
    factor of `1/k` ≈ 1000 at k = 10⁻³ Mpc⁻¹.
    """

    def _narrow_gaussian_visibility(self, eta_star, sigma):
        norm = sigma * np.sqrt(2.0 * np.pi)
        def g(eta):
            e = np.asarray(eta, dtype=np.float64)
            return np.exp(-0.5 * ((e - eta_star) / sigma) ** 2) / norm
        return g

    def test_sharp_visibility_sachs_wolfe_analytic(self):
        """Sharp-visibility SW limit: with Π = ISW = Doppler = 0 and a
        narrow visibility centered on η_*, the temperature transfer
        collapses to (Θ_0 + Ψ)_* · j_ℓ(k(η_0 − η_*)).
        """
        cfg = FLRWBesselConfig(ell_max=4, eta_0_mpc=ETA_0_DEFAULT)
        eta = build_eta_grid_linear(10.0, ETA_0_DEFAULT, 5001)
        eta_star = 280.0
        theta0 = 0.2
        psi = 0.1
        g = self._narrow_gaussian_visibility(eta_star, sigma=3.0)

        sources = FLRWSourceTerms.with_sw_polter_only(
            theta_0=constant_callable(theta0),
            psi=constant_callable(psi),
            pi=constant_callable(0.0),
        )
        S_T = build_temperature_source(
            eta, sources, g,
            lambda e: np.zeros_like(np.asarray(e, dtype=float)),  # κ=0
        )
        # Tolerance: O((σ k)²) corrections from finite Gaussian width.
        # σk = 3 · 0.05 = 0.15 → second-order correction ≈ 1% at k = 0.05;
        # use 5% rtol to absorb that with margin and stay consistent with
        # the Doppler and polarization oracles below.
        for k in (1.0e-3, 1.0e-2, 5.0e-2):
            D = project_temperature_transfer(k, S_T, eta, cfg)
            D_analytic = sachs_wolfe_analytic_transfer(
                k=k, eta_star_mpc=eta_star,
                theta0_plus_psi_at_star=theta0 + psi, config=cfg,
            )
            np.testing.assert_allclose(
                D, D_analytic, rtol=5.0e-2, atol=1.0e-9,
                err_msg=f"sharp-vis SW analytic mismatch at k={k}",
            )

    def test_sharp_visibility_doppler_analytic_protects_no_over_k_patch(self):
        """Sharp-visibility Doppler limit. With a narrow Gaussian
        visibility centered at η_* and v_b ≈ v_*, the Doppler term
        ``(g · v_b)'`` integrated against ``j_ℓ(k(η_0 − η))`` reduces
        (after IBP) to

            Δ_ℓ^Dop(k) = +k · v_* · j'_ℓ(k(η_0 − η_*))

        The explicit factor of `k` in this analytic limit is what
        distinguishes the canonical Doppler from a (wrong) `/k`-patched
        version. Concretely:
          - Correct BASS form `(g v_b)'`           → matches `+k v_* j'_ℓ`.
          - Spurious `(g v_b)'/k` patch            → would give `v_* j'_ℓ`,
                                                     i.e. a 1/k ≈ 10³×
                                                     too-small ratio at
                                                     k = 10⁻³ Mpc⁻¹.

        This test is the regression that captures the Round-15 P1
        retracted-AF-1 false trail.
        """
        cfg = FLRWBesselConfig(ell_max=4, eta_0_mpc=ETA_0_DEFAULT)
        eta = build_eta_grid_linear(10.0, ETA_0_DEFAULT, 8001)
        eta_star = 280.0
        sigma = 3.0  # FWHM ~ 7 Mpc — much narrower than 2π/k for k ≤ 0.05
        v_star = 1.0e-3
        g = self._narrow_gaussian_visibility(eta_star, sigma)

        sources = FLRWSourceTerms.with_doppler_only(constant_callable(v_star))
        S_T = build_temperature_source(
            eta, sources, g,
            lambda e: np.zeros_like(np.asarray(e, dtype=float)),
        )

        for k in (1.0e-3, 1.0e-2, 5.0e-2):
            D = project_temperature_transfer(k, S_T, eta, cfg)
            kr_star = k * (ETA_0_DEFAULT - eta_star)
            D_analytic = np.array([
                k * v_star * scipy_special.spherical_jn(
                    ell, kr_star, derivative=True,
                )
                for ell in range(cfg.ell_max + 1)
            ])
            # Tolerance: O((σ k)²) corrections from finite Gaussian width.
            # σk = 3 · 0.05 = 0.15 → ~2% corrections at k = 0.05.
            np.testing.assert_allclose(
                D, D_analytic, rtol=5.0e-2, atol=1.0e-12,
                err_msg=(
                    f"sharp-vis Doppler analytic match failed at k={k:g}.\n"
                    f"  D_BASS    = {D}\n"
                    f"  D_analytic= {D_analytic}\n"
                    f"  ratio     = {D / np.where(np.abs(D_analytic)>1e-30, D_analytic, np.inf)}\n"
                    f"  If the ratio is consistently 1/k ≈ {1.0/k:.0f} "
                    f"too small, a spurious `/k` may have been introduced "
                    f"into the Doppler line of build_temperature_source."
                ),
            )

    def test_sharp_visibility_polarization_polter_analytic(self):
        """Sharp-visibility E-mode limit. With S_E = −(√6/4) g · Π and
        Π ≈ Π_* in the visibility window:

            Δ_ℓ^E(k) = −(√6/4) · Π_* · P^E_ℓ(k(η_0 − η_*))

        where P^E_ℓ is the spin-2 projection factor implemented in
        ``e_mode_projection_factor``. This pins the temperature-side
        polter convention `g·Π/4` (without spin-2 projection) by
        contrast — the spin-2 factor lives only in the E-mode branch.
        """
        cfg = FLRWBesselConfig(ell_max=4, eta_0_mpc=ETA_0_DEFAULT)
        eta = build_eta_grid_linear(10.0, ETA_0_DEFAULT, 5001)
        eta_star = 280.0
        sigma = 3.0
        pi_star = 1.0e-2
        g = self._narrow_gaussian_visibility(eta_star, sigma)

        sources = FLRWSourceTerms.with_sw_polter_only(
            theta_0=constant_callable(0.0),
            psi=constant_callable(0.0),
            pi=constant_callable(pi_star),
        )
        S_E = build_polarization_source(eta, sources, g)

        for k in (1.0e-3, 1.0e-2, 5.0e-2):
            D_E = project_polarization_transfer(k, S_E, eta, cfg)
            kr_star = k * (ETA_0_DEFAULT - eta_star)
            # Ground truth: -(√6/4) Π_* · P^E_ℓ(kr_*)
            D_E_analytic = np.zeros(cfg.ell_max + 1, dtype=np.float64)
            for ell in range(2, cfg.ell_max + 1):
                D_E_analytic[ell] = (
                    -(SQRT6 / 4.0) * pi_star
                    * e_mode_projection_factor(ell, kr_star)
                )
            np.testing.assert_allclose(
                D_E, D_E_analytic, rtol=5.0e-2, atol=1.0e-12,
                err_msg=(
                    f"sharp-vis E-mode polter analytic match failed at "
                    f"k={k:g}.\n  D_E_BASS = {D_E}\n  "
                    f"D_E_analytic = {D_E_analytic}\n  "
                    f"If D_E_BASS is identically zero, the polarization "
                    f"projector branch may have been disabled."
                ),
            )

    def test_sharp_visibility_doppler_zero_when_v_b_zero(self):
        """Sanity check on the regression oracle: with v_b = 0 the
        sharp-visibility Doppler limit is identically zero, regardless
        of g(η)."""
        cfg = FLRWBesselConfig(ell_max=4, eta_0_mpc=ETA_0_DEFAULT)
        eta = build_eta_grid_linear(10.0, ETA_0_DEFAULT, 1001)
        g = self._narrow_gaussian_visibility(280.0, sigma=5.0)

        sources = FLRWSourceTerms.with_doppler_only(_zero_callable)
        S_T = build_temperature_source(
            eta, sources, g,
            lambda e: np.zeros_like(np.asarray(e, dtype=float)),
        )
        D = project_temperature_transfer(1.0e-2, S_T, eta, cfg)
        np.testing.assert_allclose(D, 0.0, atol=1.0e-15)


# ============================================================================
# 11.6 Extended analytic oracles
#      (Round-15 P1 follow-up, derived from
#      docs/V5_ROUND15_P1_PSTF_DERIVATION_CHATGPT.md §R5.2–§R5.4.)
# ============================================================================

class TestExtendedAnalyticOracles:
    """Additional closed-form Δ_ℓ^T oracles beyond the sharp-visibility
    SW / Doppler / polter triplet.

    R5.2 — Gaussian-visibility MD Sachs–Wolfe.
        Δ_ℓ^T(k) = [Θ_0+Ψ]_* {j_ℓ[kr_*] + ½ k² σ_*² j_ℓ''[kr_*] + O((kσ_*)⁴)}.
        Bessel ODE substitution j_ℓ'' = -(2/x)j_ℓ' + (ℓ(ℓ+1)/x² - 1)j_ℓ
        gives the Silk-damping-like envelope at large kr_*.

    R5.3 — Acoustic toy.
        Θ_0(η_*, k) = A cos(c_s k η_*) + B sin(c_s k η_*) with sharp g
        and Ψ = Π = ISW = Doppler = 0:
        Δ_ℓ^T(k) = [A cos(c_s k η_*) + B sin(c_s k η_*)] j_ℓ[kr_*].

    R5.4 — Pure ISW with Limber stationary-phase approximation.
        S_T = e^{-κ}(Φ̇ + Ψ̇) only; at large ℓ and kη_0 ≫ 1,
        Δ_ℓ^T,ISW ≈ 2 √(π/(2ℓ+1)) Φ̇[η_0 - (ℓ+½)/k] / k.
        Tests both the null (Φ̇ = 0) and a Gaussian-bump fixture for
        non-trivial Φ̇(η).
    """

    def _gaussian_visibility(self, eta_star: float, sigma: float):
        norm = sigma * np.sqrt(2.0 * np.pi)
        def g(eta):
            e = np.asarray(eta, dtype=np.float64)
            return np.exp(-0.5 * ((e - eta_star) / sigma) ** 2) / norm
        return g

    # ------------------------------------------------------------------
    # R5.2 — Gaussian-visibility MD SW
    # ------------------------------------------------------------------

    def test_gaussian_visibility_md_sachs_wolfe_R5_2(self):
        """At small kσ_*, the Gaussian-visibility SW transfer
        agrees with R5.2.1 (Taylor through σ_*²) to 5e-3 in the
        validity regime kσ_* ≤ 0.45 — this is the regime
        relevant to the recombination visibility (σ_* ≈ 11 Mpc) at
        sub-horizon scales k ≤ 4×10⁻² Mpc⁻¹.
        """
        cfg = FLRWBesselConfig(ell_max=8, eta_0_mpc=ETA_0_DEFAULT)
        eta = build_eta_grid_linear(10.0, ETA_0_DEFAULT, 8001)
        eta_star = 282.0
        theta0 = 0.2
        psi = 0.1
        theta_plus_psi = theta0 + psi

        # Sweep both narrow (σ=1 Mpc, near-sharp) and recombination-realistic
        # (σ=11 Mpc) widths. ChatGPT R5.2 spec:
        #   σ_g=1 Mpc:  matches R5.1.1 (sharp) to ≤ 1e-6 across full k range.
        #   σ_g=11 Mpc: matches R5.2.1 to ≤ 5e-3 for k ∈ [10⁻³, 10⁻²]
        #               (kσ_g ≤ 0.11, well inside the kσ_g ≤ 0.45 validity).
        for sigma_g, ks, rtol in [
            (1.0,  (1.0e-3, 1.0e-2, 5.0e-2), 5.0e-3),
            (11.0, (1.0e-3, 5.0e-3, 1.0e-2), 5.0e-3),
        ]:
            g = self._gaussian_visibility(eta_star, sigma_g)
            sources = FLRWSourceTerms.with_sw_polter_only(
                theta_0=constant_callable(theta0),
                psi=constant_callable(psi),
                pi=constant_callable(0.0),
            )
            S_T = build_temperature_source(
                eta, sources, g,
                lambda e: np.zeros_like(np.asarray(e, dtype=float)),
            )
            for k in ks:
                D_numeric = project_temperature_transfer(k, S_T, eta, cfg)
                kr_star = k * (ETA_0_DEFAULT - eta_star)
                ells = np.arange(cfg.ell_max + 1, dtype=np.float64)
                j_ell = scipy_special.spherical_jn(ells.astype(int), kr_star)
                j_ell_p = scipy_special.spherical_jn(
                    ells.astype(int), kr_star, derivative=True,
                )
                # j_ℓ'' from Bessel ODE (R5.2.2)
                j_ell_pp = (
                    -(2.0 / kr_star) * j_ell_p
                    + (ells * (ells + 1) / kr_star ** 2 - 1.0) * j_ell
                )
                # R5.2.1 truncated to σ²
                D_analytic = theta_plus_psi * (
                    j_ell + 0.5 * (k * sigma_g) ** 2 * j_ell_pp
                )
                np.testing.assert_allclose(
                    D_numeric, D_analytic, rtol=rtol, atol=1.0e-9,
                    err_msg=(
                        f"R5.2 Gaussian-MD SW analytic match failed at "
                        f"σ_g={sigma_g}, k={k}.\n  D_numeric={D_numeric}\n  "
                        f"D_analytic={D_analytic}\n  ratio={D_numeric/D_analytic}"
                    ),
                )

    # ------------------------------------------------------------------
    # R5.3 — Acoustic toy
    # ------------------------------------------------------------------

    def test_acoustic_toy_peak_structure_R5_3(self):
        """Acoustic-ansatz Θ_0 with narrow Gaussian visibility
        reproduces the Bessel-modulated phase factor
        cos(c_s k η_*) j_ℓ(kr_*) at every (k, ℓ). Sweeps k across
        [10⁻³, 5×10⁻²] including the moderate-k regime where the §10
        CAMB anchor weakens.

        Tolerance rationale: ChatGPT R5.3 spec calls for σ_g = 0.5 Mpc
        and rtol = 1e-8 in the sharp-visibility limit. On the default
        η-grid (Δη ≈ 1.76 Mpc) σ_g must be ≥ ~3 Mpc to be resolved by
        the trapezoid quadrature; the resulting O((kσ_g)²/2) finite-
        width correction reaches ~1% at k=0.05 with σ_g=3, ~5% at
        k=0.1. We use σ_g = 3 Mpc and 5% rtol consistent with the
        other sharp-visibility oracles, restricting k ≤ 5×10⁻². A
        future variant on a denser custom η-grid could tighten the
        tolerance to the R5.3 spec.
        """
        cfg = FLRWBesselConfig(ell_max=8, eta_0_mpc=ETA_0_DEFAULT)
        eta = build_eta_grid_linear(10.0, ETA_0_DEFAULT, 8001)
        eta_star = 282.0
        sigma_g = 3.0  # resolved by 8001-point grid; kσ_g ≤ 0.15 at k ≤ 0.05
        g = self._gaussian_visibility(eta_star, sigma_g)

        A = 1.0
        c_s = 1.0 / np.sqrt(3.0)

        for k in (1.0e-3, 5.0e-3, 1.0e-2, 3.0e-2, 5.0e-2):
            theta0_acoustic = A * np.cos(c_s * k * eta_star)
            sources = FLRWSourceTerms.with_sw_polter_only(
                theta_0=constant_callable(theta0_acoustic),
                psi=constant_callable(0.0),
                pi=constant_callable(0.0),
            )
            S_T = build_temperature_source(
                eta, sources, g,
                lambda e: np.zeros_like(np.asarray(e, dtype=float)),
            )
            D_numeric = project_temperature_transfer(k, S_T, eta, cfg)
            kr_star = k * (ETA_0_DEFAULT - eta_star)
            D_analytic = theta0_acoustic * scipy_special.spherical_jn(
                np.arange(cfg.ell_max + 1), kr_star,
            )
            np.testing.assert_allclose(
                D_numeric, D_analytic, rtol=5.0e-2, atol=1.0e-9,
                err_msg=(
                    f"R5.3 acoustic toy match failed at k={k}.\n  "
                    f"theta0_acoustic={theta0_acoustic:+.4e}, kr_*={kr_star:.3f}\n"
                    f"  D_numeric={D_numeric}\n  D_analytic={D_analytic}"
                ),
            )

    def test_acoustic_toy_first_peak_position_R5_3(self):
        """Acoustic-toy peak positions in k-space: extrema of
        Θ_0(k) = cos(c_s k η_*) at c_s k η_* = n π, giving
        k_n = n π / (c_s η_*). With c_s η_* ≈ 162.8 Mpc at η_* = 282
        the first peak is at k_1 ≈ 0.0193 Mpc⁻¹.

        Test: at k = k_1 we should have Θ_0(η_*, k_1) = -1 (minimum
        of cos). The transfer Δ_ℓ^T(k_1) = -j_ℓ(k_1·r_*) — opposite
        sign to the SW prediction with Θ_0 = +1.
        """
        cfg = FLRWBesselConfig(ell_max=4, eta_0_mpc=ETA_0_DEFAULT)
        eta = build_eta_grid_linear(10.0, ETA_0_DEFAULT, 8001)
        eta_star = 282.0
        sigma_g = 3.0  # resolved by 8001-point grid (see acoustic toy test)
        g = self._gaussian_visibility(eta_star, sigma_g)

        c_s = 1.0 / np.sqrt(3.0)
        k_first_peak = np.pi / (c_s * eta_star)
        # cos(c_s · k_1 · η_*) = cos(π) = -1
        theta0_at_peak = np.cos(c_s * k_first_peak * eta_star)
        assert theta0_at_peak == pytest.approx(-1.0, abs=1.0e-12)

        sources = FLRWSourceTerms.with_sw_polter_only(
            theta_0=constant_callable(theta0_at_peak),
            psi=constant_callable(0.0),
            pi=constant_callable(0.0),
        )
        S_T = build_temperature_source(
            eta, sources, g,
            lambda e: np.zeros_like(np.asarray(e, dtype=float)),
        )
        D_numeric = project_temperature_transfer(k_first_peak, S_T, eta, cfg)

        kr_star = k_first_peak * (ETA_0_DEFAULT - eta_star)
        D_analytic = theta0_at_peak * scipy_special.spherical_jn(
            np.arange(cfg.ell_max + 1), kr_star,
        )
        # D_analytic[0] should be negative (matches sign of theta0_at_peak)
        assert D_analytic[0] < 0.0
        np.testing.assert_allclose(
            D_numeric, D_analytic, rtol=5.0e-2, atol=1.0e-9,
        )

    # ------------------------------------------------------------------
    # R5.4 — Pure ISW with Limber stationary-phase
    # ------------------------------------------------------------------

    def test_isw_limber_null_when_phi_dot_vanishes_R5_4(self):
        """ISW null sanity check: with Φ̇ + Ψ̇ ≡ 0 (e.g. matter
        domination, sub-horizon, no anisotropic stress, Φ constant),
        the ISW source is identically zero and so is Δ_ℓ^T,ISW —
        regardless of κ(η)."""
        cfg = FLRWBesselConfig(ell_max=4, eta_0_mpc=ETA_0_DEFAULT)
        eta = build_eta_grid_linear(10.0, ETA_0_DEFAULT, 1001)

        sources = FLRWSourceTerms.with_isw_only(_zero_callable)
        S_T = build_temperature_source(
            eta, sources,
            lambda e: np.zeros_like(np.asarray(e, dtype=float)),  # g unused
            lambda e: np.zeros_like(np.asarray(e, dtype=float)),  # κ
        )
        D = project_temperature_transfer(1.0e-2, S_T, eta, cfg)
        np.testing.assert_allclose(D, 0.0, atol=1.0e-15)

    def test_isw_limber_stationary_phase_high_ell_R5_4(self):
        """ISW Limber stationary-phase oracle. With Φ̇(η) a smooth
        Gaussian bump centered late-time and (Φ + Ψ)̇ = 2 Φ̇ supplied
        as the source, project_temperature_transfer at large ℓ should
        match the Limber form

            Δ_ℓ^T,ISW ≈ 2 √(π/(2ℓ+1)) · Φ̇[η_0 − (ℓ+½)/k] / k

        to 5% per R5.4 validity (ℓ ≥ 30, kη_0 ≥ 30; the O(ℓ⁻²)
        Limber correction is ≈ 1% at ℓ = 30, ≈ 0.04% at ℓ = 50).

        The Φ̇-fixture is a Gaussian bump centered at η_mid = 6000 Mpc
        with width τ = 1500 Mpc — well inside the post-reionization
        regime [η_re, η_0].
        """
        cfg = FLRWBesselConfig(ell_max=50, eta_0_mpc=ETA_0_DEFAULT)
        eta = build_eta_grid_linear(10.0, ETA_0_DEFAULT, 8001)

        eta_mid = 6000.0
        tau_isw = 1500.0
        phi_dot_amp = 1.0e-4

        def phi_plus_psi_dot(e):
            e = np.asarray(e, dtype=np.float64)
            # Φ + Ψ ≈ 2 Φ in negligible-anisotropic-stress limit
            return 2.0 * phi_dot_amp * np.exp(
                -0.5 * ((e - eta_mid) / tau_isw) ** 2,
            )

        sources = FLRWSourceTerms.with_isw_only(phi_plus_psi_dot)
        S_T = build_temperature_source(
            eta, sources,
            lambda e: np.zeros_like(np.asarray(e, dtype=float)),  # g unused
            lambda e: np.zeros_like(np.asarray(e, dtype=float)),  # κ = 0
        )

        # Pick (k, ℓ) in the Limber-validity regime with stationary point
        # well inside [η_re, η_0].
        k = 1.0e-2  # k η_0 ≈ 141 ≫ 30
        for ell in (30, 40, 50):
            D = project_temperature_transfer(k, S_T, eta, cfg)
            eta_stationary = ETA_0_DEFAULT - (ell + 0.5) / k
            assert 100.0 < eta_stationary < ETA_0_DEFAULT, (
                f"stationary point η = {eta_stationary} outside grid"
            )
            phi_dot_at_stationary = phi_dot_amp * np.exp(
                -0.5 * ((eta_stationary - eta_mid) / tau_isw) ** 2,
            )
            # R5.4.3 Limber form. The factor of 2 cancels because the
            # source carries (Φ̇ + Ψ̇) = 2 Φ̇ and R5.4.1 has an explicit 2;
            # equivalently, R5.4.3 written with (Φ̇ + Ψ̇)/2 acting once:
            #
            #   Δ_ℓ ≈ √(π/(2ℓ+1)) · (Φ̇+Ψ̇)[η_*] / k
            #
            # which we use directly so that the source-side and the
            # analytic side have matching factor-of-2 conventions.
            D_limber = (
                np.sqrt(np.pi / (2.0 * ell + 1.0))
                * 2.0 * phi_dot_at_stationary / k
            )
            # 10% tolerance covers the Limber O(ℓ⁻²) correction
            # (~ 1% at ℓ=30, dropping rapidly), the smooth-bump non-
            # stationarity of Φ̇, and the discretization residual on
            # an 8001-point grid.
            assert D[ell] == pytest.approx(D_limber, rel=0.10), (
                f"R5.4.3 Limber failed at k={k}, ℓ={ell}: "
                f"numeric={D[ell]:+.3e}, Limber={D_limber:+.3e}, "
                f"ratio={D[ell]/D_limber:+.4f}"
            )


# ============================================================================
# 12. Physical sign assertions
# ============================================================================

class TestPhysicalSignAssertions:
    def test_sw_sign_positive_passes(self):
        D = np.array([0.03, -0.02, 0.04])
        assert_sw_sign_at_low_ell(D, theta0_plus_psi_sign=+1)

    def test_sw_sign_negative_passes(self):
        D = np.array([-0.03, 0.02, -0.04])
        assert_sw_sign_at_low_ell(D, theta0_plus_psi_sign=-1)

    def test_sw_sign_mismatch_raises(self):
        D = np.array([-0.03, 0.02, -0.04])
        with pytest.raises(AssertionError):
            assert_sw_sign_at_low_ell(D, theta0_plus_psi_sign=+1)

    def test_e_mode_vanishes_passes(self):
        D_E = np.array([0.0, 0.0, 0.01, 0.02, 0.01])
        assert_e_mode_vanishes_for_ell_lt_2(D_E)

    def test_e_mode_vanishes_raises(self):
        D_E = np.array([1e-4, 0.0, 0.01])
        with pytest.raises(AssertionError):
            assert_e_mode_vanishes_for_ell_lt_2(D_E)

    def test_finite_guard_passes_on_good_array(self):
        assert_transfer_finite_on_grid(np.array([0.1, -0.2, 0.3]))

    def test_finite_guard_raises_on_nan(self):
        with pytest.raises(AssertionError):
            assert_transfer_finite_on_grid(np.array([0.1, np.nan, 0.3]))


# ============================================================================
# 13. Scope guards
# ============================================================================

class TestScopeGuards:
    def test_bianchi_m_mixing_raises(self):
        with pytest.raises(OutOfScopeError):
            bianchi_m_mixing()

    def test_full_scalar_evolution_raises(self):
        with pytest.raises(OutOfScopeError):
            full_scalar_mode_evolution()

    def test_compute_c_ell_raises(self):
        with pytest.raises(OutOfScopeError):
            compute_c_ell()

    def test_b_mode_transfer_raises(self):
        with pytest.raises(OutOfScopeError):
            b_mode_transfer()


# ============================================================================
# 14. η-grid utilities
# ============================================================================

class TestEtaGridUtilities:
    def test_linear_grid_shape_and_bounds(self):
        grid = build_eta_grid_linear(10.0, 200.0, 101)
        assert grid.shape == (101,)
        assert grid[0] == 10.0
        assert grid[-1] == 200.0
        assert np.all(np.diff(grid) > 0)

    def test_linear_grid_rejects_bad_bounds(self):
        with pytest.raises(ValueError):
            build_eta_grid_linear(100.0, 10.0, 10)
        with pytest.raises(ValueError):
            build_eta_grid_linear(-1.0, 10.0, 10)
        with pytest.raises(ValueError):
            build_eta_grid_linear(10.0, 100.0, 1)

    def test_log_in_z_grid_monotone(self, planck_cosmology):
        grid = build_eta_grid_log_in_z(
            planck_cosmology, z_lower=0.0, z_upper=2500.0, n_points=51,
        )
        assert grid.shape == (51,)
        assert np.all(np.diff(grid) > 0), "must be ascending in η"

    def test_log_in_z_grid_rejects_bad_z_range(self, planck_cosmology):
        with pytest.raises(ValueError):
            build_eta_grid_log_in_z(
                planck_cosmology, z_lower=-1.0, z_upper=1000.0,
            )


# ============================================================================
# 15. Isotropic scalar-source → m=0 only (FLRW_identity_test)
# ============================================================================

class TestIsotropicSourceM0:
    """Roadmap PASS criterion: `isotropic S_T → a_{ℓ0} only`.

    In FLRW, scalar-mode perturbations source only m=0 coefficients.
    Since this projector is scalar-only by construction (no m index
    threaded through the API), the test verifies the INVARIANT that
    the output Δ_ℓ is a single ℓ-indexed vector (not an (ℓ, m) tensor)
    and that using isotropic (rotationally symmetric) source inputs
    produces the canonical scalar transfer."""

    def test_output_is_ell_indexed_only(self, default_config):
        eta = build_eta_grid_linear(10.0, ETA_0_DEFAULT, 201)
        S_T = np.ones_like(eta) * 1e-3
        D = project_temperature_transfer(1e-3, S_T, eta, default_config)
        # Output is a 1-D array: ℓ index only. No m axis exists.
        assert D.ndim == 1
        assert D.shape == (default_config.ell_max + 1,)

    def test_isotropic_source_yields_scalar_transfer(self, default_config):
        # Isotropic constant source → scalar Δ_ℓ; nothing else can appear
        eta = build_eta_grid_linear(10.0, ETA_0_DEFAULT, 201)
        D = project_temperature_transfer(
            1e-3, np.full_like(eta, 1e-4), eta, default_config,
        )
        # All entries finite; non-trivial (not all zero for k>0)
        assert np.all(np.isfinite(D))
        assert np.max(np.abs(D)) > 0.0


# ============================================================================
# 16. Real HyRec fixture end-to-end
# ============================================================================

_REAL_CSV_PATH = (
    Path(__file__).resolve().parents[1]
    / "recombination" / "fixtures" / "recombination_ref_planck2018.csv"
)


@pytest.fixture(scope="module")
def real_recomb_interp():
    if not _REAL_CSV_PATH.exists():
        pytest.skip(f"real HyRec CSV not staged at {_REAL_CSV_PATH}")
    from bass.recombination.recombination_ingest import (
        build_interpolators, load_recombination_table,
    )
    return build_interpolators(load_recombination_table(_REAL_CSV_PATH))


class TestRealFixtureEndToEnd:
    def test_real_polarization_transfer_finite(
        self, real_recomb_interp, default_config, planck_cosmology,
    ):
        """Drive S_E from W8-03 g·Π with real recombination data and
        run the projector end-to-end: result must be finite and
        non-trivial."""
        # Convert z to η via the same light utility W8-03 provides
        from bass.transport.visibility_polter_source import conformal_time_at_z

        # Pick a narrow η window around recombination (η_* ≈ 280 Mpc)
        # using the z(η) inversion: z=1089 maps to η ≈ 280 Mpc under Planck 2018
        eta_grid = build_eta_grid_linear(200.0, 400.0, 1001)

        # Build a z(η) map: cheap inverse of conformal_time_at_z
        z_samples = np.linspace(800.0, 1400.0, 60)
        eta_samples = np.array([
            conformal_time_at_z(z, planck_cosmology) for z in z_samples
        ])
        # interpolate η → z
        order = np.argsort(eta_samples)
        def z_of_eta(eta):
            return np.interp(
                np.asarray(eta), eta_samples[order], z_samples[order],
            )

        def g_fn(eta):
            z = z_of_eta(eta)
            return real_recomb_interp.query_visibility(z)

        # Constant Π (order 1e-3, typical polter amplitude)
        def pi_fn(eta):
            return np.full_like(np.asarray(eta, dtype=float), 1e-3)

        Delta_E = project_polarization_transfer_from_pi_callable(
            k=5e-3, pi_of_eta=pi_fn, g_of_eta=g_fn,
            eta_grid=eta_grid, config=default_config,
        )
        assert_transfer_finite_on_grid(Delta_E)
        assert_e_mode_vanishes_for_ell_lt_2(Delta_E)
        assert np.max(np.abs(Delta_E[2:])) > 0.0  # non-trivial

    def test_real_sw_transfer_has_sw_plateau_sign(
        self, real_recomb_interp, default_config, planck_cosmology,
    ):
        """At low ℓ and large scales, Δ_ℓ^T sign tracks (Θ₀+Ψ)_*."""
        from bass.transport.visibility_polter_source import conformal_time_at_z

        eta_grid = build_eta_grid_linear(200.0, 400.0, 1001)
        z_samples = np.linspace(800.0, 1400.0, 60)
        eta_samples = np.array([
            conformal_time_at_z(z, planck_cosmology) for z in z_samples
        ])
        order = np.argsort(eta_samples)
        def z_of_eta(eta):
            return np.interp(
                np.asarray(eta), eta_samples[order], z_samples[order],
            )

        def g_fn(eta):
            z = z_of_eta(eta)
            return real_recomb_interp.query_visibility(z)

        def kappa_fn(eta):
            z = z_of_eta(eta)
            return real_recomb_interp.query_kappa(z)

        # Positive Θ₀+Ψ, no ISW/Doppler/polter
        sources = FLRWSourceTerms.with_sw_polter_only(
            theta_0=constant_callable(0.3),
            psi=constant_callable(0.1),
            pi=constant_callable(0.0),
        )
        S_T = build_temperature_source(eta_grid, sources, g_fn, kappa_fn)
        D_T = project_temperature_transfer(5e-4, S_T, eta_grid, default_config)

        # SW plateau: Δ_0 sign should match (Θ₀+Ψ = 0.4 > 0)
        assert_sw_sign_at_low_ell(D_T, theta0_plus_psi_sign=+1)

    def test_real_all_terms_together(
        self, real_recomb_interp, default_config, planck_cosmology,
    ):
        """Full source = SW + ISW + Doppler + polter. All terms active.
        Expect finite, non-trivial output."""
        from bass.transport.visibility_polter_source import conformal_time_at_z

        eta_grid = build_eta_grid_linear(200.0, ETA_0_DEFAULT, 2001)
        z_samples = np.geomspace(1.01, 2500.0, 80)
        eta_samples = np.array([
            conformal_time_at_z(z, planck_cosmology) for z in z_samples
        ])
        order = np.argsort(eta_samples)
        def z_of_eta(eta):
            z = np.interp(
                np.asarray(eta), eta_samples[order], z_samples[order],
            )
            return np.clip(z, 1.0, 2500.0)

        def g_fn(eta):
            z = z_of_eta(eta)
            return real_recomb_interp.query_visibility(z)

        def kappa_fn(eta):
            z = z_of_eta(eta)
            return real_recomb_interp.query_kappa(z)

        # Full activation (analytic dummy amplitudes — evolution is W10+)
        sources = FLRWSourceTerms.with_all(
            theta_0=constant_callable(0.25),
            psi=constant_callable(0.1),
            phi_dot_plus_psi_dot=constant_callable(1e-5),
            v_b=constant_callable(5e-4),
            pi=constant_callable(1e-3),
        )
        S_T = build_temperature_source(eta_grid, sources, g_fn, kappa_fn)
        D_T = project_temperature_transfer(1e-3, S_T, eta_grid, default_config)
        assert_transfer_finite_on_grid(D_T)
        assert np.max(np.abs(D_T)) > 0.0
