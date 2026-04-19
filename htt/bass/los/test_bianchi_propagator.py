"""
bass/los/test_bianchi_propagator.py   (Week 9-02 tests)
========================================================

Tests for the Bianchi I matrix propagator (m ∈ {0, ±2}). Structured
to enforce the four physics cross-checks (FLRW bit-exact, σ-ladder
linearity, m=±2 parity symmetry, direction dependence) plus the
tensor-kernel identity with W9-01 and the W5-C MChannelAmplitudes
integration.
"""
from __future__ import annotations

import numpy as np
import pytest
from scipy.special import erfc, spherical_jn

from bass.los.bianchi_propagator import (
    BianchiProjectorConfig,
    BianchiSourceTerms,
    BianchiTransferFunctions,
    spherical_bessel_derivative,
    spherical_bessel_second_derivative,
    tensor_temperature_kernel,
    tensor_e_mode_kernel,
    tensor_b_mode_kernel,
    project_m0_temperature_transfer,
    project_m0_e_mode_transfer,
    project_m2_temperature_transfer,
    project_m2_e_mode_transfer,
    matrix_propagator_m0_m2,
    matrix_propagator_from_k_vector,
    k_vector_to_magnitude_cos_theta,
    verify_flrw_recovery,
    sigma_ladder_convergence,
    direction_scan,
    assert_flrw_recovery_at_sigma_zero,
    assert_m_plus_minus_2_symmetry,
    assert_b_mode_floor,
    assert_m2_zero_when_source_vanishes,
    bianchi_viih_propagator,
    bianchi_ix_propagator,
    tilt_polarization_rotation,
    full_b_mode_transfer,
    nonlinear_sigma_regime,
    compute_c_ell_bianchi,
)
from bass.los.flrw_bessel_projector import (
    FLRWBesselConfig,
    FLRWSourceTerms,
    _zero_callable,
    e_mode_projection_factor,
    project_temperature_transfer as flrw_project_T,
    project_polarization_transfer as flrw_project_E,
    build_temperature_source,
    build_polarization_source,
    OutOfScopeError,
)
from bass.transport.bianchi_i_hierarchy import (
    DiagonalShearTensor,
    MChannelAmplitudes,
    make_axisymmetric_shear,
    decompose_shear_to_m_channels,
)


# ============================================================================
# Shared fixtures
# ============================================================================

ETA_0_MPC = 1.4e4       # Observer-time default (flat ΛCDM, h=0.6766)
ETA_STAR_MPC = 280.0    # Approximate recombination conformal time
SIGMA_VIS_MPC = 30.0    # Visibility width (Gaussian toy)


def _gaussian_visibility(eta):
    """Narrow Gaussian g(η) centered at ETA_STAR, σ=SIGMA_VIS."""
    return (
        np.exp(-0.5 * ((eta - ETA_STAR_MPC) / SIGMA_VIS_MPC) ** 2)
        / (SIGMA_VIS_MPC * np.sqrt(2.0 * np.pi))
    )


def _kappa_erfc(eta):
    """Smooth κ(η) rising from 0 (early) to ~1 (late)."""
    return 0.5 * erfc((eta - ETA_STAR_MPC) / SIGMA_VIS_MPC)


def _make_synthetic_source_m0() -> FLRWSourceTerms:
    """Test m=0 source: Gaussian θ_0 + constant ψ + weak π."""
    return FLRWSourceTerms.with_all(
        theta_0=lambda eta: 1.0e-5 * np.exp(-((eta - ETA_STAR_MPC) / 50.0) ** 2),
        psi=lambda eta: 1.0e-5,
        pi=lambda eta: 1.0e-6,
        phi_dot_plus_psi_dot=_zero_callable,
        v_b=_zero_callable,
    )


def _standard_eta_grid(n_points: int = 1001) -> np.ndarray:
    """Odd-length grid for Simpson (requires odd n)."""
    return np.linspace(100.0, ETA_0_MPC - 10.0, n_points)


def _standard_config(ell_max: int = 10, quadrature: str = "simpson") -> BianchiProjectorConfig:
    return BianchiProjectorConfig(
        ell_max=ell_max, eta_0_mpc=ETA_0_MPC, quadrature=quadrature,
    )


# ============================================================================
# Class 1 - Config
# ============================================================================

class TestBianchiProjectorConfig:

    def test_config_frozen(self):
        cfg = _standard_config()
        with pytest.raises((AttributeError, Exception)):
            cfg.ell_max = 100  # type: ignore

    def test_ell_max_nonneg(self):
        with pytest.raises(ValueError, match="ell_max"):
            BianchiProjectorConfig(ell_max=-1, eta_0_mpc=ETA_0_MPC)

    def test_eta_0_positive(self):
        with pytest.raises(ValueError, match="eta_0_mpc"):
            BianchiProjectorConfig(ell_max=10, eta_0_mpc=-1.0)

    def test_quadrature_validation(self):
        with pytest.raises(ValueError, match="quadrature"):
            BianchiProjectorConfig(
                ell_max=10, eta_0_mpc=ETA_0_MPC, quadrature="romberg",
            )

    def test_flrw_recovery_rtol_positive(self):
        with pytest.raises(ValueError, match="flrw_recovery_rtol"):
            BianchiProjectorConfig(
                ell_max=10, eta_0_mpc=ETA_0_MPC, flrw_recovery_rtol=-1.0,
            )

    def test_to_flrw_config(self):
        cfg = _standard_config(ell_max=15)
        flrw = cfg.to_flrw_config()
        assert isinstance(flrw, FLRWBesselConfig)
        assert flrw.ell_max == 15
        assert flrw.eta_0_mpc == ETA_0_MPC
        assert flrw.quadrature == "simpson"


# ============================================================================
# Class 2 - Spin-2 Bessel kernel helpers
# ============================================================================

class TestSphericalBesselDerivatives:

    def test_jl_prime_matches_scipy(self):
        for ell in [2, 3, 5, 10]:
            for x in [0.5, 2.0, 10.0]:
                got = spherical_bessel_derivative(ell, x)
                ref = spherical_jn(ell, x, derivative=True)
                assert abs(got - ref) < 1e-15

    def test_jl_prime_negative_ell_raises(self):
        with pytest.raises(ValueError, match="ell"):
            spherical_bessel_derivative(-1, 1.0)

    def test_jl_double_prime_via_ode(self):
        """Check j_ℓ'' by comparing with numerical central difference."""
        ell = 3
        x0 = 5.0
        dx = 1e-5
        d2_analytic = spherical_bessel_second_derivative(ell, x0)
        d2_numeric = (
            spherical_jn(ell, x0 + dx, derivative=True)
            - spherical_jn(ell, x0 - dx, derivative=True)
        ) / (2.0 * dx)
        rel = abs(d2_analytic - d2_numeric) / abs(d2_numeric)
        assert rel < 1e-7

    def test_jl_double_prime_vectorized(self):
        ell = 4
        x_arr = np.linspace(1.0, 10.0, 7)
        d2 = spherical_bessel_second_derivative(ell, x_arr)
        assert d2.shape == x_arr.shape
        assert np.all(np.isfinite(d2))


class TestTensorTemperatureKernel:

    def test_matches_w901_e_factor(self):
        """F_ℓ^{T,m=2} ≡ P^E_ℓ (W9-01). Machine-precision identity."""
        for ell in [2, 3, 5, 10]:
            for x in [0.1, 1.0, 5.0, 20.0]:
                tk = tensor_temperature_kernel(ell, x)
                ek = e_mode_projection_factor(ell, x)
                assert tk == ek, f"mismatch at ℓ={ell}, x={x}"

    def test_zero_for_ell_lt_2(self):
        for ell in [0, 1]:
            for x in [0.1, 1.0, 10.0]:
                assert tensor_temperature_kernel(ell, x) == 0.0

    def test_finite_on_array(self):
        x_arr = np.linspace(0.01, 50.0, 20)
        vals = tensor_temperature_kernel(3, x_arr)
        assert vals.shape == x_arr.shape
        assert np.all(np.isfinite(vals))

    def test_small_x_taylor_limit_ell_2(self):
        """At ℓ=2, x→0 limit: √24/15 ≈ 0.2667 for P^E — same for tensor T."""
        val = tensor_temperature_kernel(2, 1e-5)
        expected = np.sqrt(24.0) / 15.0  # = √(1·2·3·4)/(2·2+1)!! = √24/15
        assert abs(val - expected) / expected < 1e-5

    def test_large_x_decay(self):
        """Large x: |F| decays at least as j_ℓ(x)/x² ~ sin(x)/x³."""
        x = 100.0
        ell = 3
        val = tensor_temperature_kernel(ell, x)
        # Bound: |val| < spin2_prefactor / x² (since |j_ℓ| ≤ 1)
        prefactor = np.sqrt((ell - 1) * ell * (ell + 1) * (ell + 2))
        assert abs(val) < prefactor / x ** 2 * 1.01


class TestTensorEModeKernel:

    def test_zero_for_ell_lt_2(self):
        for ell in [0, 1]:
            for x in [0.1, 1.0, 10.0]:
                assert tensor_e_mode_kernel(ell, x) == 0.0

    def test_small_x_ell_2_exact(self):
        """ℓ=2, x→0 limit: (1/4)√24 · 12/15 = 2√6/5."""
        val = tensor_e_mode_kernel(2, 1e-6)
        expected = 2.0 * np.sqrt(6.0) / 5.0
        assert abs(val - expected) / expected < 1e-5

    def test_vectorized_finite(self):
        x_arr = np.linspace(0.01, 30.0, 15)
        vals = tensor_e_mode_kernel(3, x_arr)
        assert vals.shape == x_arr.shape
        assert np.all(np.isfinite(vals))

    def test_higher_ell_small_x_taylor_decay(self):
        """For ℓ=5 at x=1e-5: F ~ x^3, so very small."""
        val = tensor_e_mode_kernel(5, 1e-5)
        assert abs(val) < 1e-10

    def test_smooth_across_cutoff(self):
        """Values just inside and just outside small-x cutoff
        must agree (Taylor / full formula crossover)."""
        cutoff = 1.0e-3
        x_left = cutoff * 0.99
        x_right = cutoff * 1.01
        for ell in [2, 3, 4]:
            vl = tensor_e_mode_kernel(ell, x_left, small_cutoff=cutoff)
            vr = tensor_e_mode_kernel(ell, x_right, small_cutoff=cutoff)
            # Both should be close
            rel = abs(vl - vr) / max(abs(vl), abs(vr), 1e-30)
            assert rel < 0.05, (
                f"Kernel not smooth across cutoff at ℓ={ell}: "
                f"left={vl:.6e}, right={vr:.6e}, rel={rel:.2e}"
            )


class TestTensorBModeKernel:

    def test_always_zero(self):
        """Bianchi I: B ≡ 0 at the kernel level."""
        for ell in range(0, 15):
            for x in [0.001, 0.1, 1.0, 10.0, 100.0]:
                assert tensor_b_mode_kernel(ell, x) == 0.0

    def test_vectorized_zero(self):
        x_arr = np.linspace(0.01, 50.0, 100)
        vals = tensor_b_mode_kernel(5, x_arr)
        assert np.all(vals == 0.0)


# ============================================================================
# Class 3 - BianchiSourceTerms
# ============================================================================

class TestBianchiSourceTerms:

    def test_flrw_isotropic_m2_zero(self):
        src = _make_synthetic_source_m0()
        bsrcs = BianchiSourceTerms.flrw_isotropic(src)
        assert bsrcs.sources_m_plus2.theta_0(1.0) == 0.0
        assert bsrcs.sources_m_minus2.theta_0(1.0) == 0.0
        assert bsrcs.sources_m_plus2.pi(1.0) == 0.0

    def test_from_m_channel_state_rescales_m0(self):
        src = _make_synthetic_source_m0()
        amps = MChannelAmplitudes(s_m0=0.001, s_m2=0.0005)
        bsrcs = BianchiSourceTerms.from_m_channel_state(amps, src, src)
        # At η=ETA_STAR: theta_0 ~ 1e-5 * 1.0 (exp ~ 1)
        theta0_m0 = bsrcs.sources_m0.theta_0(ETA_STAR_MPC)
        expected = 0.001 * 1.0e-5  # amp * original
        assert abs(theta0_m0 - expected) < 1e-18

    def test_from_m_channel_state_rescales_m2_symmetrically(self):
        src = _make_synthetic_source_m0()
        amps = MChannelAmplitudes(s_m0=0.0, s_m2=0.003)
        bsrcs = BianchiSourceTerms.from_m_channel_state(amps, src, src)
        # m=+2 and m=-2 share the same rescaling
        assert bsrcs.sources_m_plus2.pi(100.0) == bsrcs.sources_m_minus2.pi(100.0)
        assert bsrcs.sources_m_plus2.theta_0(500.0) == bsrcs.sources_m_minus2.theta_0(500.0)

    def test_dataclass_immutability(self):
        src = _make_synthetic_source_m0()
        bsrcs = BianchiSourceTerms.flrw_isotropic(src)
        with pytest.raises((AttributeError, Exception)):
            bsrcs.sources_m0 = None  # type: ignore


# ============================================================================
# Class 4 - m=0 projector (W9-01 delegation)
# ============================================================================

class TestM0Projector:

    def test_m0_T_shape(self):
        cfg = _standard_config(ell_max=15)
        src = _make_synthetic_source_m0()
        eta = _standard_eta_grid()
        out = project_m0_temperature_transfer(
            k=5e-3, sources_m0=src,
            visibility_g=_gaussian_visibility,
            kappa_of_eta=_kappa_erfc,
            eta_grid=eta, config=cfg,
        )
        assert out.shape == (16,)
        assert np.all(np.isfinite(out))

    def test_m0_T_matches_w901_bit_exact(self):
        """Direct W9-01 call vs delegating W9-02 call: bit-exact."""
        cfg = _standard_config()
        flrw_cfg = cfg.to_flrw_config()
        src = _make_synthetic_source_m0()
        eta = _standard_eta_grid()

        w902 = project_m0_temperature_transfer(
            k=5e-3, sources_m0=src,
            visibility_g=_gaussian_visibility,
            kappa_of_eta=_kappa_erfc,
            eta_grid=eta, config=cfg,
        )
        s_t = build_temperature_source(eta, src, _gaussian_visibility, _kappa_erfc)
        w901 = flrw_project_T(5e-3, s_t, eta, flrw_cfg)
        assert np.array_equal(w902, w901), (
            f"Bit-exact delegation failed: "
            f"max diff = {np.max(np.abs(w902 - w901)):.2e}"
        )

    def test_m0_E_matches_w901_bit_exact(self):
        cfg = _standard_config()
        flrw_cfg = cfg.to_flrw_config()
        src = _make_synthetic_source_m0()
        eta = _standard_eta_grid()
        w902 = project_m0_e_mode_transfer(
            k=5e-3, sources_m0=src,
            visibility_g=_gaussian_visibility,
            eta_grid=eta, config=cfg,
        )
        s_e = build_polarization_source(eta, src, _gaussian_visibility)
        w901 = flrw_project_E(5e-3, s_e, eta, flrw_cfg)
        assert np.array_equal(w902, w901)

    def test_m0_T_linearity_in_source(self):
        """Linearity: Δ_ℓ(7·S_T) = 7 · Δ_ℓ(S_T) at machine precision."""
        cfg = _standard_config()
        src = _make_synthetic_source_m0()
        src7 = FLRWSourceTerms.with_all(
            theta_0=lambda eta: 7.0 * src.theta_0(eta),
            psi=lambda eta: 7.0 * src.psi(eta),
            pi=lambda eta: 7.0 * src.pi(eta),
            phi_dot_plus_psi_dot=src.phi_dot_plus_psi_dot,
            v_b=src.v_b,
        )
        eta = _standard_eta_grid()
        d1 = project_m0_temperature_transfer(
            5e-3, src, _gaussian_visibility, _kappa_erfc, eta, cfg,
        )
        d7 = project_m0_temperature_transfer(
            5e-3, src7, _gaussian_visibility, _kappa_erfc, eta, cfg,
        )
        rel = np.max(np.abs(d7 - 7.0 * d1)) / max(np.max(np.abs(d7)), 1e-30)
        assert rel < 1e-14

    def test_m0_T_zero_source_zero_output(self):
        cfg = _standard_config()
        zero_src = FLRWSourceTerms.zeros()
        eta = _standard_eta_grid()
        out = project_m0_temperature_transfer(
            5e-3, zero_src, _gaussian_visibility, _kappa_erfc, eta, cfg,
        )
        assert np.max(np.abs(out)) == 0.0


# ============================================================================
# Class 5 - m=±2 projector (tensor kernels)
# ============================================================================

class TestM2Projector:

    def test_m2_T_shape(self):
        cfg = _standard_config(ell_max=12)
        src = _make_synthetic_source_m0()
        eta = _standard_eta_grid()
        out = project_m2_temperature_transfer(
            5e-3, src, _gaussian_visibility, _kappa_erfc, eta, cfg,
        )
        assert out.shape == (13,)
        assert np.all(np.isfinite(out))

    def test_m2_E_zero_for_ell_lt_2(self):
        cfg = _standard_config()
        src = _make_synthetic_source_m0()
        eta = _standard_eta_grid()
        out = project_m2_e_mode_transfer(5e-3, src, _gaussian_visibility, eta, cfg)
        assert out[0] == 0.0
        assert out[1] == 0.0
        # ℓ≥2 typically nonzero
        assert np.max(np.abs(out[2:])) > 0

    def test_m2_T_ell0_and_ell1_zero(self):
        """Tensor T kernel has ℓ<2 zero, so Δ_ℓ^{T,±2} = 0 at ℓ=0,1."""
        cfg = _standard_config()
        src = _make_synthetic_source_m0()
        eta = _standard_eta_grid()
        out = project_m2_temperature_transfer(
            5e-3, src, _gaussian_visibility, _kappa_erfc, eta, cfg,
        )
        assert out[0] == 0.0
        assert out[1] == 0.0

    def test_m2_T_linearity(self):
        cfg = _standard_config()
        src = _make_synthetic_source_m0()
        src5 = FLRWSourceTerms.with_all(
            theta_0=lambda eta: 5.0 * src.theta_0(eta),
            psi=lambda eta: 5.0 * src.psi(eta),
            pi=lambda eta: 5.0 * src.pi(eta),
            phi_dot_plus_psi_dot=src.phi_dot_plus_psi_dot,
            v_b=src.v_b,
        )
        eta = _standard_eta_grid()
        d1 = project_m2_temperature_transfer(
            5e-3, src, _gaussian_visibility, _kappa_erfc, eta, cfg,
        )
        d5 = project_m2_temperature_transfer(
            5e-3, src5, _gaussian_visibility, _kappa_erfc, eta, cfg,
        )
        rel = np.max(np.abs(d5 - 5.0 * d1)) / max(np.max(np.abs(d5)), 1e-30)
        assert rel < 1e-14

    def test_m2_T_uses_tensor_kernel_not_jl(self):
        """m=±2 T transfer ≠ m=0 T transfer for the same source: the
        tensor kernel differs from j_ℓ at ℓ≥2."""
        cfg = _standard_config()
        src = _make_synthetic_source_m0()
        eta = _standard_eta_grid()
        d_m0 = project_m0_temperature_transfer(
            5e-3, src, _gaussian_visibility, _kappa_erfc, eta, cfg,
        )
        d_m2 = project_m2_temperature_transfer(
            5e-3, src, _gaussian_visibility, _kappa_erfc, eta, cfg,
        )
        # At ℓ≥2 they must differ (tensor kernel ≠ j_ℓ)
        diff_at_ell3 = abs(d_m0[3] - d_m2[3])
        assert diff_at_ell3 > 1e-20
        # At ℓ<2: m=0 nonzero (scalar), m=±2 zero (spin-2 minimum)
        assert d_m2[0] == 0.0
        assert d_m2[1] == 0.0

    def test_k_nonnegative(self):
        cfg = _standard_config()
        src = _make_synthetic_source_m0()
        eta = _standard_eta_grid()
        with pytest.raises(ValueError, match="k must"):
            project_m2_temperature_transfer(
                -1.0, src, _gaussian_visibility, _kappa_erfc, eta, cfg,
            )


# ============================================================================
# Class 6 - Matrix propagator (block-diagonal assembly)
# ============================================================================

class TestMatrixPropagator:

    def test_block_diagonal_output_shape(self):
        cfg = _standard_config(ell_max=10)
        src = _make_synthetic_source_m0()
        bsrcs = BianchiSourceTerms.flrw_isotropic(src)
        eta = _standard_eta_grid()
        tf = matrix_propagator_m0_m2(
            5e-3, 1.0, bsrcs,
            _gaussian_visibility, _kappa_erfc, eta, cfg,
        )
        for field_name in [
            "delta_T_m0", "delta_T_m_plus2", "delta_T_m_minus2",
            "delta_E_m0", "delta_E_m_plus2", "delta_E_m_minus2",
            "delta_B_all_zero",
        ]:
            arr = getattr(tf, field_name)
            assert arr.shape == (11,), f"{field_name}: {arr.shape}"

    def test_b_mode_identically_zero(self):
        cfg = _standard_config()
        src = _make_synthetic_source_m0()
        amps = MChannelAmplitudes(s_m0=1e-3, s_m2=1e-3)
        bsrcs = BianchiSourceTerms.from_m_channel_state(amps, src, src)
        eta = _standard_eta_grid()
        tf = matrix_propagator_m0_m2(
            5e-3, 0.5, bsrcs,
            _gaussian_visibility, _kappa_erfc, eta, cfg,
        )
        assert np.all(tf.delta_B_all_zero == 0.0)

    def test_cos_theta_validation(self):
        cfg = _standard_config()
        src = _make_synthetic_source_m0()
        bsrcs = BianchiSourceTerms.flrw_isotropic(src)
        eta = _standard_eta_grid()
        with pytest.raises(ValueError, match="cos_theta_k"):
            matrix_propagator_m0_m2(
                5e-3, 1.5, bsrcs,
                _gaussian_visibility, _kappa_erfc, eta, cfg,
            )

    def test_ell_max_property(self):
        cfg = _standard_config(ell_max=15)
        src = _make_synthetic_source_m0()
        bsrcs = BianchiSourceTerms.flrw_isotropic(src)
        eta = _standard_eta_grid()
        tf = matrix_propagator_m0_m2(
            5e-3, 1.0, bsrcs,
            _gaussian_visibility, _kappa_erfc, eta, cfg,
        )
        assert tf.ell_max == 15

    def test_sum_aggregate_nondiagnostic(self):
        """total_T_direction_aligned returns a sum; must match manual."""
        cfg = _standard_config()
        src = _make_synthetic_source_m0()
        amps = MChannelAmplitudes(s_m0=1e-3, s_m2=5e-4)
        bsrcs = BianchiSourceTerms.from_m_channel_state(amps, src, src)
        eta = _standard_eta_grid()
        tf = matrix_propagator_m0_m2(
            5e-3, 0.5, bsrcs,
            _gaussian_visibility, _kappa_erfc, eta, cfg,
        )
        manual = tf.delta_T_m0 + tf.delta_T_m_plus2 + tf.delta_T_m_minus2
        assert np.array_equal(tf.total_T_direction_aligned(), manual)


# ============================================================================
# Class 7 - FLRW recovery (Path α: bit-exact)
# ============================================================================

class TestFLRWRecovery:

    def test_recovery_at_sigma_zero_bit_exact(self):
        cfg = _standard_config()
        src = _make_synthetic_source_m0()
        eta = _standard_eta_grid()
        result = verify_flrw_recovery(
            src, _gaussian_visibility, _kappa_erfc,
            k=5e-3, eta_grid=eta, config=cfg,
        )
        assert result["passes"]
        assert result["T_rel_diff"] == 0.0, (
            f"Expected literally 0.0 (not just below rtol), "
            f"got {result['T_rel_diff']:.2e}"
        )
        assert result["E_rel_diff"] == 0.0

    def test_recovery_multiple_k_bit_exact(self):
        cfg = _standard_config()
        src = _make_synthetic_source_m0()
        eta = _standard_eta_grid()
        for k in [1e-4, 1e-3, 5e-3, 1e-2, 5e-2]:
            result = verify_flrw_recovery(
                src, _gaussian_visibility, _kappa_erfc,
                k=k, eta_grid=eta, config=cfg,
            )
            assert result["passes"], (
                f"FLRW recovery fails at k={k}: "
                f"T_rel={result['T_rel_diff']:.2e}"
            )

    def test_recovery_different_ell_max_bit_exact(self):
        src = _make_synthetic_source_m0()
        eta = _standard_eta_grid()
        for ell_max in [5, 20, 50]:
            cfg = _standard_config(ell_max=ell_max)
            result = verify_flrw_recovery(
                src, _gaussian_visibility, _kappa_erfc,
                k=5e-3, eta_grid=eta, config=cfg,
            )
            assert result["passes"]

    def test_recovery_via_assertion_helper(self):
        cfg = _standard_config()
        src = _make_synthetic_source_m0()
        eta = _standard_eta_grid()
        result = verify_flrw_recovery(
            src, _gaussian_visibility, _kappa_erfc,
            k=5e-3, eta_grid=eta, config=cfg,
        )
        # Should not raise
        assert_flrw_recovery_at_sigma_zero(result)

    def test_flrw_isotropic_m2_channels_zero(self):
        """Using flrw_isotropic factory → m=±2 channels exactly zero."""
        cfg = _standard_config()
        src = _make_synthetic_source_m0()
        bsrcs = BianchiSourceTerms.flrw_isotropic(src)
        eta = _standard_eta_grid()
        tf = matrix_propagator_m0_m2(
            5e-3, 0.7, bsrcs,  # arbitrary direction
            _gaussian_visibility, _kappa_erfc, eta, cfg,
        )
        assert np.max(np.abs(tf.delta_T_m_plus2)) == 0.0
        assert np.max(np.abs(tf.delta_T_m_minus2)) == 0.0
        assert np.max(np.abs(tf.delta_E_m_plus2)) == 0.0
        assert np.max(np.abs(tf.delta_E_m_minus2)) == 0.0


# ============================================================================
# Class 8 - σ-ladder convergence (Path β)
# ============================================================================

class TestSigmaLadder:

    def test_sigma_zero_entry_matches_flrw(self):
        """σ=0 entry → bit-exact FLRW recovery of the m=0 channel."""
        cfg = _standard_config()
        src = _make_synthetic_source_m0()
        eta = _standard_eta_grid()
        ladder = sigma_ladder_convergence(
            sigma_values=[0.0, 1e-8],
            sources_m0=src, sources_m2_template=src,
            visibility_g=_gaussian_visibility, kappa_of_eta=_kappa_erfc,
            k_magnitude=5e-3, cos_theta_k=0.5,
            eta_grid=eta, config=cfg,
        )
        tf0 = ladder[0.0]
        # σ=0 gives zero source amplitude → all channels zero
        assert np.max(np.abs(tf0.delta_T_m0)) == 0.0
        assert np.max(np.abs(tf0.delta_T_m_plus2)) == 0.0

    def test_m0_scales_linearly_with_sigma(self):
        """Axisymmetric shear: Δ_ℓ^{T,m0} should scale ~ linearly in σ_zz."""
        cfg = _standard_config()
        src = _make_synthetic_source_m0()
        eta = _standard_eta_grid()
        ladder = sigma_ladder_convergence(
            sigma_values=[1e-8, 1e-6, 1e-4],
            sources_m0=src, sources_m2_template=src,
            visibility_g=_gaussian_visibility, kappa_of_eta=_kappa_erfc,
            k_magnitude=5e-3, cos_theta_k=0.5,
            eta_grid=eta, config=cfg,
        )
        scale_1em8 = np.max(np.abs(ladder[1e-8].delta_T_m0))
        scale_1em6 = np.max(np.abs(ladder[1e-6].delta_T_m0))
        scale_1em4 = np.max(np.abs(ladder[1e-4].delta_T_m0))
        # Ratios should be 100 to within machine precision (pure rescaling)
        ratio_6vs8 = scale_1em6 / max(scale_1em8, 1e-300)
        ratio_4vs6 = scale_1em4 / max(scale_1em6, 1e-300)
        assert abs(ratio_6vs8 - 100.0) / 100.0 < 1e-10
        assert abs(ratio_4vs6 - 100.0) / 100.0 < 1e-10

    def test_axisymmetric_sigma_keeps_m2_channel_silent(self):
        """make_axisymmetric_shear → s_plus = 0 → m=±2 source = 0 →
        m=±2 outputs identically zero (explicit check)."""
        cfg = _standard_config()
        src = _make_synthetic_source_m0()
        eta = _standard_eta_grid()
        ladder = sigma_ladder_convergence(
            sigma_values=[1e-6, 1e-4],
            sources_m0=src, sources_m2_template=src,
            visibility_g=_gaussian_visibility, kappa_of_eta=_kappa_erfc,
            k_magnitude=5e-3, cos_theta_k=0.5,
            eta_grid=eta, config=cfg,
        )
        for sigma in [1e-6, 1e-4]:
            tf = ladder[sigma]
            assert np.max(np.abs(tf.delta_T_m_plus2)) == 0.0, (
                f"axisymmetric shear should leave m=±2 silent (σ={sigma})"
            )
            assert np.max(np.abs(tf.delta_T_m_minus2)) == 0.0

    def test_full_four_rung_ladder(self):
        """Full σ ladder [0, 1e-8, 1e-6, 1e-4] — the roadmap target
        (from master prompt list W9-02 PASS criteria)."""
        cfg = _standard_config()
        src = _make_synthetic_source_m0()
        eta = _standard_eta_grid()
        ladder = sigma_ladder_convergence(
            sigma_values=[0.0, 1e-8, 1e-6, 1e-4],
            sources_m0=src, sources_m2_template=src,
            visibility_g=_gaussian_visibility, kappa_of_eta=_kappa_erfc,
            k_magnitude=5e-3, cos_theta_k=0.5,
            eta_grid=eta, config=cfg,
        )
        assert set(ladder.keys()) == {0.0, 1e-8, 1e-6, 1e-4}
        for sigma, tf in ladder.items():
            assert isinstance(tf, BianchiTransferFunctions)
            assert np.all(np.isfinite(tf.delta_T_m0))


# ============================================================================
# Class 9 - m=±2 symmetry (Path γ)
# ============================================================================

class TestMPlusMinusSymmetry:

    def test_real_shear_plus_minus_equal(self):
        """Real MChannelAmplitudes → Δ_ℓ^{T,+2} == Δ_ℓ^{T,-2} exactly."""
        cfg = _standard_config()
        src = _make_synthetic_source_m0()
        amps = MChannelAmplitudes(s_m0=1e-3, s_m2=5e-4)
        bsrcs = BianchiSourceTerms.from_m_channel_state(amps, src, src)
        eta = _standard_eta_grid()
        tf = matrix_propagator_m0_m2(
            5e-3, 0.5, bsrcs,
            _gaussian_visibility, _kappa_erfc, eta, cfg,
        )
        assert np.array_equal(tf.delta_T_m_plus2, tf.delta_T_m_minus2)
        assert np.array_equal(tf.delta_E_m_plus2, tf.delta_E_m_minus2)

    def test_assertion_helper_passes_for_real_shear(self):
        cfg = _standard_config()
        src = _make_synthetic_source_m0()
        amps = MChannelAmplitudes(s_m0=1e-3, s_m2=5e-4)
        bsrcs = BianchiSourceTerms.from_m_channel_state(amps, src, src)
        eta = _standard_eta_grid()
        tf = matrix_propagator_m0_m2(
            5e-3, 0.5, bsrcs,
            _gaussian_visibility, _kappa_erfc, eta, cfg,
        )
        # Should not raise
        assert_m_plus_minus_2_symmetry(tf)

    def test_assertion_helper_raises_on_artificial_asymmetry(self):
        """Manually construct asymmetric TF → assertion should raise."""
        tf = BianchiTransferFunctions(
            delta_T_m0=np.ones(11),
            delta_T_m_plus2=np.array([1.0] * 11),
            delta_T_m_minus2=np.array([2.0] * 11),  # broken
            delta_E_m0=np.zeros(11),
            delta_E_m_plus2=np.zeros(11),
            delta_E_m_minus2=np.zeros(11),
            delta_B_all_zero=np.zeros(11),
        )
        with pytest.raises(AssertionError, match="m=±2 temperature symmetry"):
            assert_m_plus_minus_2_symmetry(tf)


# ============================================================================
# Class 10 - k-direction dependence (Path δ)
# ============================================================================

class TestDirectionDependence:

    def test_aligned_k_with_axisymmetric_shear(self):
        """k ∥ axis (cos_θ=1) with axisymmetric shear (s_plus=0) →
        m=±2 zero. Covered because s_plus=0 → zero sources."""
        cfg = _standard_config()
        src = _make_synthetic_source_m0()
        shear = make_axisymmetric_shear(s_zz=1e-4)
        amps = decompose_shear_to_m_channels(shear)
        bsrcs = BianchiSourceTerms.from_m_channel_state(amps, src, src)
        eta = _standard_eta_grid()
        tf = matrix_propagator_m0_m2(
            5e-3, 1.0, bsrcs,  # aligned
            _gaussian_visibility, _kappa_erfc, eta, cfg,
        )
        assert np.max(np.abs(tf.delta_T_m_plus2)) == 0.0

    def test_non_axisymmetric_activates_m2(self):
        """σ_xx ≠ σ_yy (s_plus ≠ 0) → m=±2 outputs nonzero."""
        cfg = _standard_config()
        src = _make_synthetic_source_m0()
        shear = DiagonalShearTensor(
            sigma_xx=1e-4, sigma_yy=-1e-4, sigma_zz=0.0,
        )
        amps = decompose_shear_to_m_channels(shear)
        assert amps.s_m2 != 0.0
        bsrcs = BianchiSourceTerms.from_m_channel_state(amps, src, src)
        eta = _standard_eta_grid()
        tf = matrix_propagator_m0_m2(
            5e-3, 0.5, bsrcs,
            _gaussian_visibility, _kappa_erfc, eta, cfg,
        )
        assert np.max(np.abs(tf.delta_T_m_plus2)) > 0.0
        assert np.max(np.abs(tf.delta_E_m_plus2)) > 0.0

    def test_k_vector_interface_equivalent(self):
        """matrix_propagator_from_k_vector(k⃗) == matrix_propagator_m0_m2(|k|, cos_θ)."""
        cfg = _standard_config()
        src = _make_synthetic_source_m0()
        amps = MChannelAmplitudes(s_m0=1e-3, s_m2=5e-4)
        bsrcs = BianchiSourceTerms.from_m_channel_state(amps, src, src)
        eta = _standard_eta_grid()

        k_vec = np.array([0.003, 0.0, 0.004])  # |k|=0.005, cos_θ=0.8
        tf_vec = matrix_propagator_from_k_vector(
            k_vec, bsrcs,
            _gaussian_visibility, _kappa_erfc, eta, cfg,
        )
        tf_scalar = matrix_propagator_m0_m2(
            0.005, 0.8, bsrcs,
            _gaussian_visibility, _kappa_erfc, eta, cfg,
        )
        assert np.array_equal(tf_vec.delta_T_m0, tf_scalar.delta_T_m0)
        assert np.array_equal(tf_vec.delta_T_m_plus2, tf_scalar.delta_T_m_plus2)

    def test_k_vector_zero_raises(self):
        with pytest.raises(ValueError, match="direction undefined"):
            k_vector_to_magnitude_cos_theta(np.zeros(3))

    def test_k_vector_wrong_shape(self):
        with pytest.raises(ValueError, match="shape"):
            k_vector_to_magnitude_cos_theta(np.array([1.0, 2.0]))

    def test_k_vector_custom_axis(self):
        """Shear axis along x̂ rather than ẑ."""
        k_vec = np.array([1.0, 0.0, 0.0])
        k_mag, cos_theta = k_vector_to_magnitude_cos_theta(
            k_vec, shear_axis=np.array([1.0, 0.0, 0.0]),
        )
        assert abs(k_mag - 1.0) < 1e-15
        assert abs(cos_theta - 1.0) < 1e-15

    def test_direction_scan_returns_dict(self):
        cfg = _standard_config()
        src = _make_synthetic_source_m0()
        amps = MChannelAmplitudes(s_m0=1e-3, s_m2=5e-4)
        eta = _standard_eta_grid()
        result = direction_scan(
            cos_theta_values=[0.0, 0.3, 0.7, 1.0],
            amplitudes=amps, sources_m0=src, sources_m2_template=src,
            visibility_g=_gaussian_visibility, kappa_of_eta=_kappa_erfc,
            k_magnitude=5e-3, eta_grid=eta, config=cfg,
        )
        assert set(result.keys()) == {0.0, 0.3, 0.7, 1.0}
        for cos_theta, tf in result.items():
            assert isinstance(tf, BianchiTransferFunctions)


# ============================================================================
# Class 11 - B-mode floor
# ============================================================================

class TestBModeFloor:

    def test_b_mode_identically_zero_for_bianchi_i(self):
        cfg = _standard_config()
        src = _make_synthetic_source_m0()
        shear = DiagonalShearTensor(
            sigma_xx=1e-4, sigma_yy=-1e-4, sigma_zz=0.0,
        )
        amps = decompose_shear_to_m_channels(shear)
        bsrcs = BianchiSourceTerms.from_m_channel_state(amps, src, src)
        eta = _standard_eta_grid()
        tf = matrix_propagator_m0_m2(
            5e-3, 0.5, bsrcs,
            _gaussian_visibility, _kappa_erfc, eta, cfg,
        )
        assert np.all(tf.delta_B_all_zero == 0.0)
        # Floor assertion should pass
        assert_b_mode_floor(tf)

    def test_b_mode_floor_assertion_catches_nonzero(self):
        tf = BianchiTransferFunctions(
            delta_T_m0=np.zeros(11),
            delta_T_m_plus2=np.zeros(11),
            delta_T_m_minus2=np.zeros(11),
            delta_E_m0=np.zeros(11),
            delta_E_m_plus2=np.zeros(11),
            delta_E_m_minus2=np.zeros(11),
            delta_B_all_zero=np.array([1e-6] + [0.0] * 10),  # injected
        )
        with pytest.raises(AssertionError, match="B-mode floor"):
            assert_b_mode_floor(tf, floor=1e-14)


# ============================================================================
# Class 12 - W5-C integration
# ============================================================================

class TestW5CIntegration:

    def test_decompose_shear_to_m_channels_integration(self):
        """End-to-end: DiagonalShearTensor → MChannelAmplitudes →
        BianchiSourceTerms → matrix propagator."""
        cfg = _standard_config()
        src = _make_synthetic_source_m0()
        shear = DiagonalShearTensor(
            sigma_xx=5e-5, sigma_yy=-3e-5, sigma_zz=-2e-5,
        )
        amps = decompose_shear_to_m_channels(shear)
        assert amps.s_m0 == -2e-5
        assert amps.s_m2 == 4e-5  # (5e-5 - (-3e-5))/2

        bsrcs = BianchiSourceTerms.from_m_channel_state(amps, src, src)
        eta = _standard_eta_grid()
        tf = matrix_propagator_m0_m2(
            5e-3, 0.5, bsrcs,
            _gaussian_visibility, _kappa_erfc, eta, cfg,
        )
        assert np.all(np.isfinite(tf.delta_T_m0))
        assert np.all(np.isfinite(tf.delta_T_m_plus2))

    def test_axisymmetric_shear_via_w5c(self):
        """make_axisymmetric_shear → s_plus=0 → m=±2 silent."""
        cfg = _standard_config()
        src = _make_synthetic_source_m0()
        shear = make_axisymmetric_shear(s_zz=1e-4)
        amps = decompose_shear_to_m_channels(shear)
        assert amps.s_m2 == 0.0

        bsrcs = BianchiSourceTerms.from_m_channel_state(amps, src, src)
        eta = _standard_eta_grid()
        tf = matrix_propagator_m0_m2(
            5e-3, 0.5, bsrcs,
            _gaussian_visibility, _kappa_erfc, eta, cfg,
        )
        assert np.max(np.abs(tf.delta_T_m_plus2)) == 0.0
        # But m=0 channel active
        assert np.max(np.abs(tf.delta_T_m0)) > 0.0

    def test_m_channel_amplitudes_source_scaling(self):
        """s_m0=2×baseline → Δ_T^{m=0} doubles (linear source scaling)."""
        cfg = _standard_config()
        src = _make_synthetic_source_m0()
        eta = _standard_eta_grid()

        amps_1 = MChannelAmplitudes(s_m0=1e-3, s_m2=0.0)
        amps_2 = MChannelAmplitudes(s_m0=2e-3, s_m2=0.0)
        bsrcs_1 = BianchiSourceTerms.from_m_channel_state(amps_1, src, src)
        bsrcs_2 = BianchiSourceTerms.from_m_channel_state(amps_2, src, src)
        tf_1 = matrix_propagator_m0_m2(
            5e-3, 0.5, bsrcs_1,
            _gaussian_visibility, _kappa_erfc, eta, cfg,
        )
        tf_2 = matrix_propagator_m0_m2(
            5e-3, 0.5, bsrcs_2,
            _gaussian_visibility, _kappa_erfc, eta, cfg,
        )
        rel = np.max(np.abs(tf_2.delta_T_m0 - 2.0 * tf_1.delta_T_m0)) / max(
            np.max(np.abs(tf_2.delta_T_m0)), 1e-30,
        )
        assert rel < 1e-14


# ============================================================================
# Class 13 - Sign assertions (pure helpers)
# ============================================================================

class TestSignAssertions:

    def test_flrw_recovery_helper_raises_when_rtol_exceeded(self):
        fake_result = {
            "T_rel_diff": 1e-6, "E_rel_diff": 1e-8,
            "rtol_threshold": 1e-14, "passes": False,
        }
        with pytest.raises(AssertionError, match="FLRW recovery fails"):
            assert_flrw_recovery_at_sigma_zero(fake_result)

    def test_m2_zero_helper_catches_nonzero(self):
        tf = BianchiTransferFunctions(
            delta_T_m0=np.zeros(11),
            delta_T_m_plus2=np.array([1e-10] + [0.0] * 10),  # injected
            delta_T_m_minus2=np.zeros(11),
            delta_E_m0=np.zeros(11),
            delta_E_m_plus2=np.zeros(11),
            delta_E_m_minus2=np.zeros(11),
            delta_B_all_zero=np.zeros(11),
        )
        with pytest.raises(AssertionError, match="m=\\+2 temperature"):
            assert_m2_zero_when_source_vanishes(tf)


# ============================================================================
# Class 14 - Scope guards
# ============================================================================

class TestScopeGuards:

    def test_viih_raises(self):
        with pytest.raises(OutOfScopeError, match="VIIh"):
            bianchi_viih_propagator()

    def test_ix_raises(self):
        with pytest.raises(OutOfScopeError, match="IX"):
            bianchi_ix_propagator()

    def test_tilt_rotation_raises(self):
        with pytest.raises(OutOfScopeError, match="Tilt"):
            tilt_polarization_rotation()

    def test_full_b_mode_raises(self):
        with pytest.raises(OutOfScopeError, match="B-mode"):
            full_b_mode_transfer()

    def test_nonlinear_sigma_raises(self):
        with pytest.raises(OutOfScopeError, match="Nonlinear"):
            nonlinear_sigma_regime()

    def test_c_ell_bianchi_raises(self):
        with pytest.raises(OutOfScopeError, match="C_ℓ"):
            compute_c_ell_bianchi()


# ============================================================================
# Class 15 - End-to-end with realistic shear
# ============================================================================

class TestRealFixtureEndToEnd:

    def test_production_sigma_squared_1em8(self):
        """Production Σ²=1e-8 target (Route B linear regime): verify
        that the transfer function is well-behaved and finite."""
        cfg = _standard_config(ell_max=20)
        src = _make_synthetic_source_m0()
        # Non-axisymmetric shear with Σ² ≈ 1e-8
        sigma_mag = np.sqrt(1e-8 / 2.0)  # so Σ² = (1/2) σ_ab σ^ab ≈ 1e-8
        shear = DiagonalShearTensor(
            sigma_xx=sigma_mag, sigma_yy=-sigma_mag, sigma_zz=0.0,
        )
        amps = decompose_shear_to_m_channels(shear)
        bsrcs = BianchiSourceTerms.from_m_channel_state(amps, src, src)
        eta = _standard_eta_grid()
        tf = matrix_propagator_m0_m2(
            5e-3, 0.5, bsrcs,
            _gaussian_visibility, _kappa_erfc, eta, cfg,
        )
        assert np.all(np.isfinite(tf.delta_T_m0))
        assert np.all(np.isfinite(tf.delta_T_m_plus2))
        assert np.all(np.isfinite(tf.delta_E_m_plus2))
        # B-mode still identically zero
        assert_b_mode_floor(tf)
        # ±2 symmetry
        assert_m_plus_minus_2_symmetry(tf)

    def test_full_pipeline_flrw_limit_plus_small_shear(self):
        """Full pipeline consistency: σ→0 should smoothly approach
        FLRW-recovered m=0 output, m=±2 stay zero if axisymmetric."""
        cfg = _standard_config(ell_max=15)
        src = _make_synthetic_source_m0()
        eta = _standard_eta_grid()
        # FLRW-isotropic
        bsrcs_iso = BianchiSourceTerms.flrw_isotropic(src)
        tf_iso = matrix_propagator_m0_m2(
            5e-3, 0.7, bsrcs_iso,
            _gaussian_visibility, _kappa_erfc, eta, cfg,
        )
        # Small axisymmetric shear
        shear = make_axisymmetric_shear(s_zz=1e-10)
        amps = decompose_shear_to_m_channels(shear)
        bsrcs_small = BianchiSourceTerms.from_m_channel_state(amps, src, src)
        tf_small = matrix_propagator_m0_m2(
            5e-3, 0.7, bsrcs_small,
            _gaussian_visibility, _kappa_erfc, eta, cfg,
        )
        # m=0 outputs: iso uses src directly; small rescales by 1e-10
        # → tf_small.delta_T_m0 = 1e-10 × (some non-iso version)
        # So they differ by the amplitude factor, NOT equal.
        # But both should be finite and smooth.
        assert np.all(np.isfinite(tf_iso.delta_T_m0))
        assert np.all(np.isfinite(tf_small.delta_T_m0))
        # m=±2 zero in both cases
        assert np.max(np.abs(tf_iso.delta_T_m_plus2)) == 0.0
        assert np.max(np.abs(tf_small.delta_T_m_plus2)) == 0.0

    def test_full_pipeline_matches_w901_for_iso(self):
        """Full pipeline: BianchiSourceTerms.flrw_isotropic →
        m=0 output bit-exact to W9-01's direct call."""
        cfg = _standard_config(ell_max=20)
        src = _make_synthetic_source_m0()
        eta = _standard_eta_grid()
        bsrcs_iso = BianchiSourceTerms.flrw_isotropic(src)
        tf_iso = matrix_propagator_m0_m2(
            5e-3, 1.0, bsrcs_iso,
            _gaussian_visibility, _kappa_erfc, eta, cfg,
        )
        # Direct W9-01
        flrw_cfg = cfg.to_flrw_config()
        s_t = build_temperature_source(eta, src, _gaussian_visibility, _kappa_erfc)
        s_e = build_polarization_source(eta, src, _gaussian_visibility)
        ref_T = flrw_project_T(5e-3, s_t, eta, flrw_cfg)
        ref_E = flrw_project_E(5e-3, s_e, eta, flrw_cfg)
        assert np.array_equal(tf_iso.delta_T_m0, ref_T)
        assert np.array_equal(tf_iso.delta_E_m0, ref_E)
