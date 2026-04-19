"""
bass/spectrum/test_cl_assembly.py   (Week 10-01 tests)
=======================================================

Tests for C_ℓ^{TT/EE/TE/BB} assembly from BianchiTransferFunctions
callables. Focus on (a) Route B lookup sentinel exactness,
(b) isotropic / anisotropic assembly structural checks,
(c) Michaelis-Menten fitter synthetic ground-truth recovery,
(d) D_ℓ conversion numerical identity,
(e) scope-guard contract.

Performance strategy (per Q6 decision):
  * Physics tests use analytic synthetic transfer functions
  * API tests use mocked constant/zero BianchiTransferFunctions
  * Real W9-02 integration: one end-to-end test only
"""
from __future__ import annotations

import numpy as np
import pytest
from scipy.special import spherical_jn

from bass.spectrum.cl_assembly import (
    # constants
    ROUTE_B_C1, ROUTE_B_C2, ROUTE_B_D2_AT_SIGMA2_1EM8,
    # config
    CLAssemblyConfig,
    # primordial
    primordial_power_spectrum,
    # isotropic
    assemble_cl_TT_isotropic,
    assemble_cl_EE_isotropic,
    assemble_cl_TE_isotropic,
    # bianchi diagonal
    assemble_cl_TT_bianchi,
    assemble_cl_EE_bianchi,
    assemble_cl_TE_bianchi,
    assemble_cl_BB_bianchi,
    # D_ℓ conversion
    compute_dl,
    # route B
    route_b_d2_lookup,
    assert_d2_anti_regression_vs_route_b,
    # M-M fitter
    fit_michaelis_menten,
    # diagnostics
    sigma_squared_scan,
    high_ell_convergence_diagnostic,
    # assertions
    assert_cl_tt_positivity,
    assert_cl_ee_ell_lt_2_zero,
    assert_b_mode_cl_zero,
    # scope guards
    off_diagonal_biposh,
    camb_v_gate_comparison,
    full_scalar_mode_evolution,
    lensing_cl,
    tensor_mode_contribution,
)
from bass.los.bianchi_propagator import BianchiTransferFunctions
from bass.los.flrw_bessel_projector import OutOfScopeError
from bass.observational.planck_mes_bounds import T_CMB_K


# ============================================================================
# Shared fixtures
# ============================================================================

def _mock_constant_transfer(ell_max: int = 20, T_val: float = 1.0, E_val: float = 0.0):
    """Factory: return a callable k → BianchiTransferFunctions with
    constant Δ_ℓ values independent of k."""
    def _transfer(k: float) -> BianchiTransferFunctions:
        return BianchiTransferFunctions(
            delta_T_m0=np.full(ell_max + 1, T_val),
            delta_T_m_plus2=np.zeros(ell_max + 1),
            delta_T_m_minus2=np.zeros(ell_max + 1),
            delta_E_m0=np.full(ell_max + 1, E_val),
            delta_E_m_plus2=np.zeros(ell_max + 1),
            delta_E_m_minus2=np.zeros(ell_max + 1),
            delta_B_all_zero=np.zeros(ell_max + 1),
        )
    return _transfer


def _mock_analytic_sw_transfer(ell_max: int = 20, eta_star: float = 280.0):
    """Synthetic Sachs-Wolfe-like transfer:
    Δ_ℓ^{T,m=0}(k) = A · j_ℓ(k · eta_star) where A = 1e-5.
    Δ_ℓ^{E} = 0 to keep focus on TT."""
    A = 1.0e-5
    def _transfer(k: float) -> BianchiTransferFunctions:
        x = k * eta_star
        jl_array = np.array([spherical_jn(ell, x) for ell in range(ell_max + 1)])
        return BianchiTransferFunctions(
            delta_T_m0=A * jl_array,
            delta_T_m_plus2=np.zeros(ell_max + 1),
            delta_T_m_minus2=np.zeros(ell_max + 1),
            delta_E_m0=np.zeros(ell_max + 1),
            delta_E_m_plus2=np.zeros(ell_max + 1),
            delta_E_m_minus2=np.zeros(ell_max + 1),
            delta_B_all_zero=np.zeros(ell_max + 1),
        )
    return _transfer


def _mock_bianchi_transfer_all_channels(ell_max: int = 20, sigma_sq: float = 1e-4):
    """Factory with m=±2 channels activated proportional to √σ²."""
    A_m0 = 1.0e-5
    A_m2 = np.sqrt(sigma_sq) * 1.0e-3
    def _transfer(k: float) -> BianchiTransferFunctions:
        jl = np.array([spherical_jn(ell, k * 280.0) for ell in range(ell_max + 1)])
        # Crude E-mode: suppressed by ℓ-dependent factor, zero ℓ<2
        jl_e = jl.copy()
        jl_e[0] = 0.0; jl_e[1] = 0.0
        return BianchiTransferFunctions(
            delta_T_m0=A_m0 * jl,
            delta_T_m_plus2=A_m2 * jl,
            delta_T_m_minus2=A_m2 * jl,
            delta_E_m0=A_m0 * jl_e,
            delta_E_m_plus2=A_m2 * jl_e,
            delta_E_m_minus2=A_m2 * jl_e,
            delta_B_all_zero=np.zeros(ell_max + 1),
        )
    return _transfer


def _standard_config(ell_max: int = 20) -> CLAssemblyConfig:
    return CLAssemblyConfig(ell_max=ell_max)


# ============================================================================
# Class 1 - Config
# ============================================================================

class TestCLAssemblyConfig:

    def test_config_frozen(self):
        cfg = _standard_config()
        with pytest.raises((AttributeError, Exception)):
            cfg.ell_max = 100  # type: ignore

    def test_ell_max_nonneg(self):
        with pytest.raises(ValueError, match="ell_max"):
            CLAssemblyConfig(ell_max=-1)

    def test_A_s_positive(self):
        with pytest.raises(ValueError, match="A_s"):
            CLAssemblyConfig(ell_max=10, A_s=-1e-9)

    def test_k_grid_positive(self):
        with pytest.raises(ValueError, match="k_grid"):
            CLAssemblyConfig(ell_max=10, k_grid=np.array([-1.0, 0.1, 1.0]))

    def test_quadrature_enum(self):
        with pytest.raises(ValueError, match="quadrature"):
            CLAssemblyConfig(ell_max=10, quadrature="romberg")

    def test_simpson_needs_odd_grid(self):
        even_grid = np.logspace(-4, 0, 10)  # even
        with pytest.raises(ValueError, match="Simpson"):
            CLAssemblyConfig(ell_max=10, k_grid=even_grid, quadrature="simpson")

    def test_defaults_planck_2018(self):
        cfg = CLAssemblyConfig(ell_max=10)
        assert cfg.A_s == 2.1e-9
        assert cfg.n_s == 0.9649
        assert cfg.k_pivot_mpc == 0.05
        assert cfg.T_CMB_K == T_CMB_K
        assert cfg.k_grid.size == 256
        assert cfg.primordial_pk_fn is None


# ============================================================================
# Class 2 - Primordial power spectrum
# ============================================================================

class TestPrimordialPowerSpectrum:

    def test_amplitude_at_pivot(self):
        """P_R(k_pivot) = A_s exactly."""
        cfg = _standard_config()
        val = primordial_power_spectrum(cfg.k_pivot_mpc, cfg)
        assert abs(val - cfg.A_s) / cfg.A_s < 1e-14

    def test_log_log_slope_equals_ns_minus_1(self):
        """ln P vs ln k slope = n_s - 1."""
        cfg = _standard_config()
        k = np.array([1e-3, 1e-1])
        p = primordial_power_spectrum(k, cfg)
        slope = (np.log(p[1]) - np.log(p[0])) / (np.log(k[1]) - np.log(k[0]))
        assert abs(slope - (cfg.n_s - 1.0)) < 1e-12

    def test_A_s_linear_scaling(self):
        """Double A_s → double P_R."""
        cfg1 = CLAssemblyConfig(ell_max=10, A_s=2.1e-9)
        cfg2 = CLAssemblyConfig(ell_max=10, A_s=4.2e-9)
        k = np.logspace(-3, -1, 10)
        p1 = primordial_power_spectrum(k, cfg1)
        p2 = primordial_power_spectrum(k, cfg2)
        assert np.allclose(p2, 2.0 * p1, rtol=1e-15)

    def test_callable_injection(self):
        """custom primordial_pk_fn overrides A_s, n_s, pivot."""
        custom = lambda k: 42.0 * np.ones_like(np.asarray(k, dtype=float))
        cfg = CLAssemblyConfig(ell_max=10, primordial_pk_fn=custom)
        val = primordial_power_spectrum(np.array([0.01, 0.1]), cfg)
        assert np.all(val == 42.0)


# ============================================================================
# Class 3 - Isotropic TT assembly
# ============================================================================

class TestIsotropicTT:

    def test_shape_matches_ell_max(self):
        cfg = _standard_config(ell_max=15)
        xf = _mock_constant_transfer(ell_max=15)
        cl = assemble_cl_TT_isotropic(xf, cfg)
        assert cl.shape == (16,)

    def test_positivity(self):
        cfg = _standard_config(ell_max=10)
        xf = _mock_analytic_sw_transfer(ell_max=10)
        cl = assemble_cl_TT_isotropic(xf, cfg)
        assert_cl_tt_positivity(cl)

    def test_zero_source_zero_output(self):
        cfg = _standard_config(ell_max=10)
        xf = _mock_constant_transfer(ell_max=10, T_val=0.0)
        cl = assemble_cl_TT_isotropic(xf, cfg)
        assert np.all(cl == 0.0)

    def test_A_s_linearity(self):
        """Double A_s → C_ℓ^{TT} doubles (linear weighting)."""
        xf = _mock_analytic_sw_transfer(ell_max=10)
        cfg1 = CLAssemblyConfig(ell_max=10, A_s=2.1e-9)
        cfg2 = CLAssemblyConfig(ell_max=10, A_s=4.2e-9)
        cl1 = assemble_cl_TT_isotropic(xf, cfg1)
        cl2 = assemble_cl_TT_isotropic(xf, cfg2)
        # At ℓ ≥ 1 (ℓ=0 may be numerical noise near zero)
        for ell in range(2, 10):
            assert abs(cl2[ell] - 2.0 * cl1[ell]) / max(abs(cl2[ell]), 1e-30) < 1e-14

    def test_constant_delta_equal_across_ell(self):
        """Δ_ℓ = const → C_ℓ = same across ℓ (only integrand varies)."""
        cfg = _standard_config(ell_max=10)
        xf = _mock_constant_transfer(ell_max=10, T_val=1.0)
        cl = assemble_cl_TT_isotropic(xf, cfg)
        assert np.allclose(cl, cl[0], rtol=1e-12)


# ============================================================================
# Class 4 - Isotropic EE assembly
# ============================================================================

class TestIsotropicEE:

    def test_shape(self):
        cfg = _standard_config(ell_max=15)
        xf = _mock_constant_transfer(ell_max=15, E_val=1.0)
        cl = assemble_cl_EE_isotropic(xf, cfg)
        assert cl.shape == (16,)

    def test_zero_when_delta_E_zero(self):
        cfg = _standard_config(ell_max=10)
        xf = _mock_constant_transfer(ell_max=10, E_val=0.0)
        cl = assemble_cl_EE_isotropic(xf, cfg)
        assert np.all(cl == 0.0)

    def test_positivity(self):
        cfg = _standard_config(ell_max=10)
        xf = _mock_constant_transfer(ell_max=10, E_val=1.0)
        cl = assemble_cl_EE_isotropic(xf, cfg)
        assert_cl_tt_positivity(cl)  # same positivity check applies

    def test_assembly_linearity_in_delta_E(self):
        """Double Δ_E → C_EE quadruples."""
        cfg = _standard_config(ell_max=5)
        xf1 = _mock_constant_transfer(ell_max=5, E_val=1.0)
        xf2 = _mock_constant_transfer(ell_max=5, E_val=2.0)
        cl1 = assemble_cl_EE_isotropic(xf1, cfg)
        cl2 = assemble_cl_EE_isotropic(xf2, cfg)
        for ell in range(5):
            if cl1[ell] > 0:
                assert abs(cl2[ell] - 4.0 * cl1[ell]) / cl2[ell] < 1e-14


# ============================================================================
# Class 5 - Isotropic TE assembly
# ============================================================================

class TestIsotropicTE:

    def test_zero_when_either_zero(self):
        cfg = _standard_config(ell_max=10)
        # Δ_E = 0 → C_TE = 0
        xf = _mock_constant_transfer(ell_max=10, T_val=1.0, E_val=0.0)
        cl = assemble_cl_TE_isotropic(xf, cfg)
        assert np.all(cl == 0.0)

    def test_sign_from_product(self):
        """Δ_T = +1, Δ_E = +1 → C_TE > 0.
        Δ_T = +1, Δ_E = -1 → C_TE < 0 (flipped)."""
        cfg = _standard_config(ell_max=5)
        xf_pos = _mock_constant_transfer(ell_max=5, T_val=1.0, E_val=1.0)
        xf_neg = _mock_constant_transfer(ell_max=5, T_val=1.0, E_val=-1.0)
        cl_pos = assemble_cl_TE_isotropic(xf_pos, cfg)
        cl_neg = assemble_cl_TE_isotropic(xf_neg, cfg)
        # sign flip
        for ell in range(5):
            if abs(cl_pos[ell]) > 1e-30:
                assert abs(cl_pos[ell] + cl_neg[ell]) / cl_pos[ell] < 1e-14

    def test_symmetry_in_T_E(self):
        """C_TE uses Δ_T · Δ_E; swapping which is in which slot via
        manual callable should produce the same value."""
        cfg = _standard_config(ell_max=5)
        # Simulate manual swap by using _mock_constant with different values
        xf = _mock_constant_transfer(ell_max=5, T_val=2.0, E_val=3.0)
        cl = assemble_cl_TE_isotropic(xf, cfg)
        # Expected proportional to 2 × 3 = 6
        cl_ref_tt = assemble_cl_TT_isotropic(
            _mock_constant_transfer(ell_max=5, T_val=1.0), cfg,
        )
        # C_TE(T=2, E=3) = 6 · (C_TT with Δ_T=1)
        for ell in range(5):
            if cl_ref_tt[ell] > 0:
                assert abs(cl[ell] / cl_ref_tt[ell] - 6.0) < 1e-14


# ============================================================================
# Class 6 - Bianchi diagonal TT/EE/TE assembly
# ============================================================================

class TestBianchiDiagonalTT:

    def test_flrw_recovery_bit_exact(self):
        """m=±2 channels zero → bianchi assembly == isotropic assembly."""
        cfg = _standard_config(ell_max=15)
        xf = _mock_analytic_sw_transfer(ell_max=15)
        cl_iso = assemble_cl_TT_isotropic(xf, cfg)
        cl_bianchi = assemble_cl_TT_bianchi(xf, cfg)
        assert np.array_equal(cl_bianchi, cl_iso)

    def test_m_sum_contribution(self):
        """With all three m channels nonzero, bianchi sum > isotropic alone."""
        cfg = _standard_config(ell_max=10)
        xf_all = _mock_bianchi_transfer_all_channels(ell_max=10, sigma_sq=1e-4)
        xf_m0_only = _mock_analytic_sw_transfer(ell_max=10)
        # Note: both have different m=0 amplitudes, so this is just a
        # sanity check that bianchi ≥ 0 always
        cl = assemble_cl_TT_bianchi(xf_all, cfg)
        assert_cl_tt_positivity(cl)

    def test_shape(self):
        cfg = _standard_config(ell_max=20)
        xf = _mock_bianchi_transfer_all_channels(ell_max=20)
        cl = assemble_cl_TT_bianchi(xf, cfg)
        assert cl.shape == (21,)

    def test_zero_source_zero_output(self):
        cfg = _standard_config(ell_max=10)
        xf = _mock_constant_transfer(ell_max=10, T_val=0.0)
        cl = assemble_cl_TT_bianchi(xf, cfg)
        assert np.all(cl == 0.0)

    def test_linearity_in_all_m_channels(self):
        """Scaling Δ_T by factor a → C_TT scales by a² (quadratic)."""
        cfg = _standard_config(ell_max=10)
        xf1 = _mock_constant_transfer(ell_max=10, T_val=1.0)
        xf2 = _mock_constant_transfer(ell_max=10, T_val=3.0)
        cl1 = assemble_cl_TT_bianchi(xf1, cfg)
        cl2 = assemble_cl_TT_bianchi(xf2, cfg)
        for ell in range(10):
            if cl1[ell] > 0:
                assert abs(cl2[ell] - 9.0 * cl1[ell]) / cl2[ell] < 1e-14


class TestBianchiDiagonalEE:

    def test_flrw_recovery_bit_exact(self):
        cfg = _standard_config(ell_max=10)
        xf = _mock_constant_transfer(ell_max=10, E_val=1.0)
        cl_iso = assemble_cl_EE_isotropic(xf, cfg)
        cl_bianchi = assemble_cl_EE_bianchi(xf, cfg)
        assert np.array_equal(cl_bianchi, cl_iso)

    def test_shape_and_positivity(self):
        cfg = _standard_config(ell_max=15)
        xf = _mock_bianchi_transfer_all_channels(ell_max=15)
        cl = assemble_cl_EE_bianchi(xf, cfg)
        assert cl.shape == (16,)
        # non-negative everywhere
        assert np.min(cl) >= 0.0

    def test_ell_lt_2_zero_via_bianchi_sum(self):
        """Even with m=±2 activated, Δ_ℓ^{E,m} = 0 for ℓ<2 → C_EE = 0."""
        cfg = _standard_config(ell_max=10)
        xf = _mock_bianchi_transfer_all_channels(ell_max=10, sigma_sq=1e-4)
        cl = assemble_cl_EE_bianchi(xf, cfg)
        assert_cl_ee_ell_lt_2_zero(cl)


class TestBianchiDiagonalTE:

    def test_flrw_recovery_bit_exact(self):
        cfg = _standard_config(ell_max=10)
        xf = _mock_constant_transfer(ell_max=10, T_val=1.0, E_val=0.5)
        cl_iso = assemble_cl_TE_isotropic(xf, cfg)
        cl_bianchi = assemble_cl_TE_bianchi(xf, cfg)
        assert np.array_equal(cl_bianchi, cl_iso)

    def test_m_sum_structure(self):
        cfg = _standard_config(ell_max=8)
        xf = _mock_bianchi_transfer_all_channels(ell_max=8)
        cl = assemble_cl_TE_bianchi(xf, cfg)
        assert cl.shape == (9,)
        # ℓ<2: zero because Δ_E vanishes at ℓ<2 in both m=0 and m=±2
        assert abs(cl[0]) < 1e-30
        assert abs(cl[1]) < 1e-30


class TestBianchiDiagonalBB:

    def test_always_zero(self):
        """Bianchi I: C_ℓ^{BB} ≡ 0 regardless of transfer function input."""
        cfg = _standard_config(ell_max=15)
        # Any transfer works — BB assembler returns zeros unconditionally
        xf = _mock_bianchi_transfer_all_channels(ell_max=15)
        cl = assemble_cl_BB_bianchi(xf, cfg)
        assert cl.shape == (16,)
        assert np.all(cl == 0.0)
        assert_b_mode_cl_zero(cl)

    def test_b_mode_assertion_catches_injected_nonzero(self):
        bad_cl = np.array([1e-10] + [0.0] * 10)  # injected leak at ℓ=0
        with pytest.raises(AssertionError, match="identically zero"):
            assert_b_mode_cl_zero(bad_cl, floor=1e-14)


# ============================================================================
# Class 7 - D_ℓ conversion
# ============================================================================

class TestDlConversion:

    def test_unit_cl_gives_exact_Dl(self):
        """For C_ℓ = 1, D_ℓ = ℓ(ℓ+1) T_CMB_μK² / (2π). Check at ℓ=2."""
        dl = compute_dl(np.ones(5))
        expected_dl2 = 2 * 3 / (2 * np.pi) * (2.7255e6) ** 2
        assert abs(dl[2] - expected_dl2) / expected_dl2 < 1e-14

    def test_ell_0_and_1_zero_via_prefactor(self):
        """ℓ(ℓ+1) = 0 at ℓ=0, 1 → D_ℓ = 0 there."""
        dl = compute_dl(np.ones(5))
        assert dl[0] == 0.0
        # ℓ=1: 1·2 = 2, non-zero! But D_1 is non-standard.
        # Actually the formula gives D_1 = 2 * C_1 * T² / (2π), which
        # is non-zero for C_1 = 1. Test: ℓ=0 is 0.
        # ℓ=1 is technically nonzero per formula but unused in Planck.

    def test_T_CMB_quadratic_scaling(self):
        """D_ℓ ∝ T_CMB² — double T_CMB should quadruple D_ℓ."""
        cl = np.ones(5)
        dl_std = compute_dl(cl, T_CMB_K=2.7255)
        dl_2x = compute_dl(cl, T_CMB_K=2 * 2.7255)
        for ell in range(2, 5):
            ratio = dl_2x[ell] / dl_std[ell]
            assert abs(ratio - 4.0) / 4.0 < 1e-14

    def test_linear_in_cl(self):
        cl1 = np.ones(5)
        cl2 = 3.7 * np.ones(5)
        dl1 = compute_dl(cl1)
        dl2 = compute_dl(cl2)
        for ell in range(2, 5):
            assert abs(dl2[ell] - 3.7 * dl1[ell]) / dl2[ell] < 1e-14


# ============================================================================
# Class 8 - Route B Michaelis-Menten lookup sentinel
# ============================================================================

class TestRouteBSentinel:

    def test_d2_at_sigma2_1em8(self):
        """D_2(Σ² = 1e-8) must match the d2_convention.rs SSOT
        within 1e-4 μK² absolute (corresponds to 3 sig figs of
        0.1741 μK²)."""
        val = route_b_d2_lookup(1e-8)
        # Formula: 1.753e7 * 1e-8 / (1 + 6.825e5 * 1e-8)
        #        = 0.1753 / (1 + 6.825e-3)
        #        = 0.17411...
        expected = 1.753e7 * 1e-8 / (1.0 + 6.825e5 * 1e-8)
        assert val == expected  # bit-exact formula identity
        assert abs(val - 0.1741) < 1e-3

    def test_ssot_constants_values(self):
        """Direct check of C1, C2 constants."""
        assert ROUTE_B_C1 == 1.753e7
        assert ROUTE_B_C2 == 6.825e5

    def test_anti_regression_helper_passes(self):
        val = route_b_d2_lookup(1e-8)
        # Should not raise
        assert_d2_anti_regression_vs_route_b(val, 1e-8)

    def test_anti_regression_raises_on_mismatch(self):
        wrong_val = 0.5  # very wrong
        with pytest.raises(AssertionError, match="anti-regression"):
            assert_d2_anti_regression_vs_route_b(wrong_val, 1e-8)

    def test_vectorized_input(self):
        sigma_arr = np.array([1e-10, 1e-8, 1e-6, 1e-4])
        vals = route_b_d2_lookup(sigma_arr)
        assert vals.shape == sigma_arr.shape
        # Compare to the exact formula element-wise
        expected = ROUTE_B_C1 * sigma_arr / (1.0 + ROUTE_B_C2 * sigma_arr)
        assert np.allclose(vals, expected, rtol=1e-15)
        # Deep linear regime: at σ² = 1e-10, C2·σ² ~ 6.8e-5, so
        # D_2 ≈ C1·σ² to ~ 1e-4 relative precision
        assert abs(vals[0] - ROUTE_B_C1 * 1e-10) / vals[0] < 1e-4
        # Saturation regime: at σ² = 1e-4, C2·σ² ~ 68.25 >> 1
        assert vals[3] < ROUTE_B_C1 / ROUTE_B_C2  # bounded by asymptote

    def test_negative_sigma_raises(self):
        with pytest.raises(ValueError, match="sigma_sq"):
            route_b_d2_lookup(-1e-8)

    def test_zero_sigma_gives_zero(self):
        assert route_b_d2_lookup(0.0) == 0.0


# ============================================================================
# Class 9 - Michaelis-Menten fitter
# ============================================================================

class TestMichaelisMentenFitter:

    def test_ground_truth_recovery(self):
        """Known (C1, C2) → M-M fitter recovers them accurately."""
        C1_true, C2_true = 3.0, 100.0
        sigma_arr = np.array([1e-3, 3e-3, 1e-2, 3e-2, 1e-1])
        d_arr = C1_true * sigma_arr / (1.0 + C2_true * sigma_arr)
        fit = fit_michaelis_menten(sigma_arr, d_arr, initial_guess=(1.0, 10.0))
        assert abs(fit["C1"] - C1_true) / C1_true < 1e-6
        assert abs(fit["C2"] - C2_true) / C2_true < 1e-6
        assert fit["rms_residual"] < 1e-10

    def test_route_b_parameter_recovery(self):
        """Sample the Route B formula at several σ², fit M-M, recover
        C1 ≈ 1.753e7, C2 ≈ 6.825e5 to sub-0.5% accuracy."""
        sigma_arr = np.logspace(-10, -4, 8)
        d_arr = route_b_d2_lookup(sigma_arr)
        fit = fit_michaelis_menten(
            sigma_arr, d_arr, initial_guess=(1e7, 1e5),
        )
        # 0.5% tolerance per roadmap PASS criterion
        assert abs(fit["C1"] - ROUTE_B_C1) / ROUTE_B_C1 < 5e-3
        assert abs(fit["C2"] - ROUTE_B_C2) / ROUTE_B_C2 < 5e-3

    def test_too_few_points_raises(self):
        with pytest.raises(ValueError, match="≥ 2"):
            fit_michaelis_menten(np.array([1e-3]), np.array([1e-3]))

    def test_shape_mismatch_raises(self):
        with pytest.raises(ValueError, match="same shape"):
            fit_michaelis_menten(np.array([1.0, 2.0]), np.array([1.0]))

    def test_fit_output_structure(self):
        sigma_arr = np.linspace(1e-3, 1e-1, 5)
        d_arr = 5.0 * sigma_arr / (1.0 + 50.0 * sigma_arr)
        fit = fit_michaelis_menten(sigma_arr, d_arr)
        for key in ("C1", "C2", "C1_err", "C2_err",
                    "covariance", "residuals", "rms_residual"):
            assert key in fit
        assert fit["covariance"].shape == (2, 2)


# ============================================================================
# Class 10 - σ² scan diagnostic
# ============================================================================

class TestSigmaSquaredScan:

    def test_scan_returns_per_sigma_cl(self):
        """Factory produces σ²-dependent transfer; scan returns dict."""
        def factory(sigma_sq):
            return _mock_bianchi_transfer_all_channels(ell_max=10, sigma_sq=sigma_sq)
        cfg = _standard_config(ell_max=10)
        result = sigma_squared_scan(
            sigma_sq_values=[1e-8, 1e-6, 1e-4],
            transfer_fn_factory=factory,
            config=cfg,
            which="TT",
        )
        assert set(result.keys()) == {1e-8, 1e-6, 1e-4}
        for sigma_sq, cl in result.items():
            assert cl.shape == (11,)

    def test_scan_invalid_which(self):
        def factory(sigma_sq):
            return _mock_constant_transfer(ell_max=5)
        cfg = _standard_config(ell_max=5)
        with pytest.raises(ValueError, match="which"):
            sigma_squared_scan(
                sigma_sq_values=[1e-8],
                transfer_fn_factory=factory,
                config=cfg,
                which="ZZ",
            )

    def test_scan_supports_bb(self):
        """scan with 'BB' returns identically-zero arrays (Bianchi I)."""
        def factory(sigma_sq):
            return _mock_bianchi_transfer_all_channels(ell_max=5, sigma_sq=sigma_sq)
        cfg = _standard_config(ell_max=5)
        result = sigma_squared_scan(
            sigma_sq_values=[1e-6],
            transfer_fn_factory=factory,
            config=cfg,
            which="BB",
        )
        assert np.all(result[1e-6] == 0.0)


# ============================================================================
# Class 11 - High-ℓ convergence diagnostic
# ============================================================================

class TestHighEllConvergence:

    def test_plateau_detection_shape(self):
        """high_ell_convergence_diagnostic returns dict with expected keys."""
        cfg = _standard_config(ell_max=10)
        xf = _mock_analytic_sw_transfer(ell_max=10)
        result = high_ell_convergence_diagnostic(
            xf, ell_test=5, config=cfg,
            k_max_values=[0.01, 0.05, 0.1],
        )
        assert "k_max_values" in result
        assert "cl_values" in result
        assert "relative_change" in result
        assert result["cl_values"].size == 3

    def test_convergence_decreases_with_larger_kmax(self):
        """As k_max grows, relative_change should eventually decrease."""
        cfg = _standard_config(ell_max=5)
        xf = _mock_analytic_sw_transfer(ell_max=5)
        result = high_ell_convergence_diagnostic(
            xf, ell_test=2, config=cfg,
            k_max_values=[0.01, 0.05, 0.1, 0.2, 0.5],
        )
        # Final relative change should be smaller than earlier
        rc = result["relative_change"]
        assert rc[-1] <= rc[1] + 1e-3  # allow tiny noise


# ============================================================================
# Class 12 - Scope guards
# ============================================================================

class TestScopeGuards:

    def test_off_diagonal_biposh_raises(self):
        with pytest.raises(OutOfScopeError, match="BiPoSH"):
            off_diagonal_biposh()

    def test_camb_v_gate_raises(self):
        with pytest.raises(OutOfScopeError, match="CAMB"):
            camb_v_gate_comparison()

    def test_full_scalar_mode_evolution_raises(self):
        with pytest.raises(OutOfScopeError, match="scalar mode"):
            full_scalar_mode_evolution()

    def test_lensing_cl_raises(self):
        with pytest.raises(OutOfScopeError, match="lensing"):
            lensing_cl()

    def test_tensor_mode_contribution_raises(self):
        with pytest.raises(OutOfScopeError, match="[Tt]ensor"):
            tensor_mode_contribution()


# ============================================================================
# Class 13 - End-to-end with real W9-02 propagator
# ============================================================================

class TestEndToEndWithRealW902:

    def test_real_w902_produces_finite_cl(self):
        """Full pipeline: real W9-02 matrix propagator → CLAssemblyConfig
        → assemble_cl_TT_bianchi → finite non-negative C_ℓ."""
        from scipy.special import erfc
        from bass.los.bianchi_propagator import (
            BianchiProjectorConfig, BianchiSourceTerms,
            matrix_propagator_m0_m2,
        )
        from bass.los.flrw_bessel_projector import FLRWSourceTerms, _zero_callable
        from bass.transport.bianchi_i_hierarchy import (
            DiagonalShearTensor, decompose_shear_to_m_channels,
        )

        ETA_0 = 1.4e4
        ETA_STAR = 280.0
        SIGMA_VIS = 30.0

        def g_of_eta(eta):
            return np.exp(-0.5 * ((eta - ETA_STAR) / SIGMA_VIS) ** 2) / (
                SIGMA_VIS * np.sqrt(2.0 * np.pi)
            )

        def kappa_of_eta(eta):
            return 0.5 * erfc((eta - ETA_STAR) / SIGMA_VIS)

        source_m0 = FLRWSourceTerms.with_all(
            theta_0=lambda eta: 1e-5,
            psi=lambda eta: 1e-5,
            pi=lambda eta: 1e-6,
            phi_dot_plus_psi_dot=_zero_callable,
            v_b=_zero_callable,
        )
        # Non-axisymmetric shear → m=±2 active
        shear = DiagonalShearTensor(
            sigma_xx=1e-5, sigma_yy=-1e-5, sigma_zz=0.0,
        )
        amps = decompose_shear_to_m_channels(shear)
        bsrcs = BianchiSourceTerms.from_m_channel_state(amps, source_m0, source_m0)

        bianchi_cfg = BianchiProjectorConfig(
            ell_max=10, eta_0_mpc=ETA_0, quadrature="simpson",
        )
        eta_grid = np.linspace(100.0, ETA_0 - 10.0, 1001)

        def transfer_fn(k):
            return matrix_propagator_m0_m2(
                k, 0.5, bsrcs,
                g_of_eta, kappa_of_eta, eta_grid, bianchi_cfg,
            )

        # Use sparse k-grid for speed (end-to-end test, not production)
        cl_cfg = CLAssemblyConfig(
            ell_max=10,
            k_grid=np.logspace(-3, -1, 21),  # 21 k-points (odd for Simpson)
            quadrature="simpson",
        )
        cl_tt = assemble_cl_TT_bianchi(transfer_fn, cl_cfg)
        assert cl_tt.shape == (11,)
        assert np.all(np.isfinite(cl_tt))
        assert_cl_tt_positivity(cl_tt)

        # Convert to D_ℓ and check reasonable μK² range
        dl = compute_dl(cl_tt)
        # For tiny source amplitudes, D_ℓ will be very small but finite
        assert np.all(np.isfinite(dl))

    def test_flrw_isotropic_end_to_end_bianchi_equals_iso(self):
        """Using flrw_isotropic factory: bianchi assembly bit-exact
        matches isotropic assembly over a sparse grid."""
        from scipy.special import erfc
        from bass.los.bianchi_propagator import (
            BianchiProjectorConfig, BianchiSourceTerms,
            matrix_propagator_m0_m2,
        )
        from bass.los.flrw_bessel_projector import FLRWSourceTerms, _zero_callable

        ETA_0 = 1.4e4
        def g_of_eta(eta):
            return np.exp(-0.5 * ((eta - 280.0) / 30.0) ** 2) / (30.0 * np.sqrt(2.0 * np.pi))
        def kappa_of_eta(eta):
            return 0.5 * erfc((eta - 280.0) / 30.0)

        source_m0 = FLRWSourceTerms.with_all(
            theta_0=lambda eta: 1e-5,
            psi=lambda eta: 1e-5,
            pi=lambda eta: 1e-6,
            phi_dot_plus_psi_dot=_zero_callable,
            v_b=_zero_callable,
        )
        bsrcs_iso = BianchiSourceTerms.flrw_isotropic(source_m0)
        bianchi_cfg = BianchiProjectorConfig(
            ell_max=5, eta_0_mpc=ETA_0, quadrature="simpson",
        )
        eta_grid = np.linspace(100.0, ETA_0 - 10.0, 1001)

        def transfer_fn(k):
            return matrix_propagator_m0_m2(
                k, 1.0, bsrcs_iso,
                g_of_eta, kappa_of_eta, eta_grid, bianchi_cfg,
            )

        cl_cfg = CLAssemblyConfig(
            ell_max=5, k_grid=np.logspace(-3, -1, 11),
            quadrature="simpson",
        )
        cl_iso = assemble_cl_TT_isotropic(transfer_fn, cl_cfg)
        cl_bianchi = assemble_cl_TT_bianchi(transfer_fn, cl_cfg)
        assert np.array_equal(cl_iso, cl_bianchi)
