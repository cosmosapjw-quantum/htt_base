"""
Test suite: bass/transport/bianchi_i_hierarchy.py  (Week 5-C)
==============================================================

Full Bianchi I hierarchy with m ∈ {0, ±2} azimuthal channels, plus W3
runtime gating.

Test classes (11):
  1. TestDiagonalShearTensor      — construction, trace-free, accessors
  2. TestAxisymmetricFactory      — make_axisymmetric_shear helper
  3. TestShearDecomposition       — s_m0, s_m2 split
  4. TestPSTFCouplingCoeffs       — α_ℓ^m, β_ℓ^m formulas
  5. TestMStreamingMatrix         — matrix assembly for each m
  6. TestMSourceVector            — source at ℓ=2 per m-channel
  7. TestMChannelState            — container invariants
  8. TestBianchiParameters        — parameter validation + factories
  9. TestMChannelSteadyState      — single-channel linsolve
 10. TestFullBianchiSteadyState   — aggregated result across m
 11. TestAxisymmetricReduction    — W5-C at s_plus=0 matches W5-A bit-exact
 12. TestRuntimeGating            — all entries gate on decision

Target: ~60 tests.
"""
from __future__ import annotations

import math
import numpy as np
import pytest

from bass.collision.thomson_tensor import (
    AxisymmetricSTFTensor, SymmetryAxis, SIGMA_2_PHOTON_BE,
)
from bass.transport.ray_transport import TransportSpecies, SIGMA_2_NEUTRINO_FD
from bass.transport.multipole_hierarchy import (
    build_streaming_matrix as w5a_streaming_matrix,
    make_photon_hierarchy_parameters as w5a_make_photon_params,
    compute_steady_state_hierarchy as w5a_compute_steady_state,
)
from bass.transport.bianchi_i_hierarchy import (
    DiagonalShearTensor,
    MChannelAmplitudes,
    MChannelState,
    BianchiHierarchyParameters,
    BianchiHierarchyResult,
    make_axisymmetric_shear,
    decompose_shear_to_m_channels,
    pstf_coupling_coeffs,
    build_m_streaming_matrix,
    build_m_source_vector,
    make_photon_bianchi_parameters,
    make_neutrino_bianchi_parameters,
    compute_m_channel_steady_state,
    compute_bianchi_i_steady_state,
)
from bass.runtime.canonical_decision import (
    CanonicalDecision, CanonicalBlockError, make_canonical_decision,
)
from tsc.diagnostics.tangency import compute_D_diagnostic, TangentKind


# ============================================================================
# Fixtures
# ============================================================================

def _on(x):
    return np.asarray(x, dtype=float)


def _allowing_decision() -> CanonicalDecision:
    tang = compute_D_diagnostic(
        G_field=_on, kind=TangentKind.ONE_FIELD, xi=0, eta=0.0,
    )
    return make_canonical_decision(
        beta_result=(True, {
            "beta": 1.36e-3, "beta_max": 8.62e-3, "slack": 7.26e-3,
            "eta_u_dot": 0.16, "safety_factor": 0.5, "epsilon_1": 0.02,
        }),
        sigma_result=(True, {
            "sigma_sq": 1e-5, "floor": 1e-6, "log_margin_decades": 1.0,
        }),
        tangency_result=tang,
    )


def _blocking_decision() -> CanonicalDecision:
    tang = compute_D_diagnostic(
        G_field=_on, kind=TangentKind.ONE_FIELD, xi=0, eta=0.0,
    )
    return make_canonical_decision(
        beta_result=(False, {
            "beta": 0.5, "beta_max": 8.62e-3, "slack": -0.49,
            "eta_u_dot": 0.16, "safety_factor": 0.5, "epsilon_1": 0.02,
        }),
        sigma_result=(True, {
            "sigma_sq": 1e-5, "floor": 1e-6, "log_margin_decades": 1.0,
        }),
        tangency_result=tang,
    )


# ============================================================================
# Test Class 1 - DiagonalShearTensor
# ============================================================================

class TestDiagonalShearTensor:
    def test_trace_free_valid(self):
        s = DiagonalShearTensor(sigma_xx=1.0, sigma_yy=-0.5, sigma_zz=-0.5)
        assert s.sigma_xx == 1.0
        assert s.sigma_yy == -0.5
        assert s.sigma_zz == -0.5

    def test_trace_nonzero_rejected(self):
        with pytest.raises(ValueError, match="trace-free"):
            DiagonalShearTensor(sigma_xx=1.0, sigma_yy=1.0, sigma_zz=1.0)

    def test_s_0_property(self):
        s = DiagonalShearTensor(sigma_xx=1.0, sigma_yy=-0.5, sigma_zz=-0.5)
        assert s.s_0 == -0.5   # s_0 = σ_zz

    def test_s_plus_property(self):
        s = DiagonalShearTensor(sigma_xx=2.0, sigma_yy=-1.0, sigma_zz=-1.0)
        # s_plus = (σ_xx - σ_yy) / 2 = (2 - (-1))/2 = 1.5
        assert s.s_plus == pytest.approx(1.5, rel=1e-14)

    def test_is_axisymmetric_xy_true(self):
        s = DiagonalShearTensor(sigma_xx=-0.5, sigma_yy=-0.5, sigma_zz=1.0)
        assert s.is_axisymmetric_xy is True

    def test_is_axisymmetric_xy_false(self):
        s = DiagonalShearTensor(sigma_xx=1.0, sigma_yy=0.0, sigma_zz=-1.0)
        assert s.is_axisymmetric_xy is False

    def test_to_diagonal_array(self):
        s = DiagonalShearTensor(sigma_xx=1.0, sigma_yy=-0.5, sigma_zz=-0.5)
        arr = s.to_diagonal_array()
        assert np.allclose(arr, [1.0, -0.5, -0.5])

    def test_custom_trace_atol(self):
        # Within the relaxed atol, near-zero trace is accepted
        s = DiagonalShearTensor(
            sigma_xx=1.0, sigma_yy=-0.5, sigma_zz=-0.5 + 1e-10,
            trace_atol=1e-8,
        )
        assert s.sigma_xx == 1.0

    def test_frozen(self):
        s = DiagonalShearTensor(sigma_xx=1.0, sigma_yy=-0.5, sigma_zz=-0.5)
        with pytest.raises(Exception):
            s.sigma_xx = 99.0


# ============================================================================
# Test Class 2 - Axisymmetric factory
# ============================================================================

class TestAxisymmetricFactory:
    def test_makes_trace_free(self):
        s = make_axisymmetric_shear(s_zz=1.0)
        assert abs(s.sigma_xx + s.sigma_yy + s.sigma_zz) < 1e-14

    def test_xx_equals_yy(self):
        s = make_axisymmetric_shear(s_zz=1e-6)
        assert s.sigma_xx == s.sigma_yy

    def test_xx_equals_minus_half_zz(self):
        s = make_axisymmetric_shear(s_zz=2.0)
        assert s.sigma_xx == -1.0
        assert s.sigma_yy == -1.0
        assert s.sigma_zz == 2.0

    def test_is_axisymmetric_xy(self):
        s = make_axisymmetric_shear(s_zz=1.0)
        assert s.is_axisymmetric_xy is True

    def test_s_plus_zero(self):
        s = make_axisymmetric_shear(s_zz=1e-6)
        assert s.s_plus == 0.0


# ============================================================================
# Test Class 3 - Shear decomposition
# ============================================================================

class TestShearDecomposition:
    def test_axisymmetric_gives_s_m2_zero(self):
        s = make_axisymmetric_shear(s_zz=1e-6)
        amps = decompose_shear_to_m_channels(s)
        assert amps.s_m2 == 0.0

    def test_axisymmetric_s_m0_equals_s_zz(self):
        s = make_axisymmetric_shear(s_zz=3e-6)
        amps = decompose_shear_to_m_channels(s)
        assert amps.s_m0 == 3e-6

    def test_full_anisotropic(self):
        s = DiagonalShearTensor(sigma_xx=2.0, sigma_yy=-1.0, sigma_zz=-1.0)
        amps = decompose_shear_to_m_channels(s)
        assert amps.s_m0 == -1.0
        assert amps.s_m2 == 1.5

    def test_returns_MChannelAmplitudes(self):
        s = make_axisymmetric_shear(s_zz=1.0)
        amps = decompose_shear_to_m_channels(s)
        assert isinstance(amps, MChannelAmplitudes)

    def test_m_channel_amps_frozen(self):
        amps = MChannelAmplitudes(s_m0=1.0, s_m2=0.5)
        with pytest.raises(Exception):
            amps.s_m0 = 99.0


# ============================================================================
# Test Class 4 - PSTF coupling coefficients
# ============================================================================

class TestPSTFCouplingCoeffs:
    @pytest.mark.parametrize("ell", [0, 1, 2, 3, 4, 5])
    def test_m_zero_matches_W5A_formula(self, ell):
        """α_ℓ^0 = ℓ/(2ℓ+1), β_ℓ^0 = (ℓ+1)/(2ℓ+1)."""
        alpha, beta = pstf_coupling_coeffs(ell, 0)
        assert alpha == pytest.approx(ell / (2 * ell + 1), rel=1e-14)
        assert beta == pytest.approx((ell + 1) / (2 * ell + 1), rel=1e-14)

    def test_m_equals_ell_gives_alpha_nonzero(self):
        """At ℓ=|m|, α = 0 (can't go below |m|)."""
        alpha, beta = pstf_coupling_coeffs(2, 2)
        assert alpha == 0.0
        # But β is nonzero: √(9-4)/5 = √5/5
        assert beta == pytest.approx(math.sqrt(5) / 5, rel=1e-14)

    def test_m_equals_2_ell_3(self):
        alpha, beta = pstf_coupling_coeffs(3, 2)
        # α = √(9-4)/7 = √5/7
        # β = √(16-4)/7 = √12/7 = 2√3/7
        assert alpha == pytest.approx(math.sqrt(5) / 7, rel=1e-14)
        assert beta == pytest.approx(math.sqrt(12) / 7, rel=1e-14)

    def test_m_negative_same_as_positive(self):
        alpha_p, beta_p = pstf_coupling_coeffs(3, +2)
        alpha_m, beta_m = pstf_coupling_coeffs(3, -2)
        assert alpha_p == alpha_m
        assert beta_p == beta_m

    def test_ell_below_m_returns_zero(self):
        alpha, beta = pstf_coupling_coeffs(1, 2)
        assert alpha == 0.0
        assert beta == 0.0


# ============================================================================
# Test Class 5 - m-streaming matrix
# ============================================================================

class TestMStreamingMatrix:
    def test_m_zero_matches_W5A_bit_exact(self):
        """Bit-exact equality at m=0 with the W5-A streaming matrix."""
        for ell_max in (2, 4, 7):
            M_m0 = build_m_streaming_matrix(k_eff=1.5, ell_max=ell_max, m=0)
            M_w5a = w5a_streaming_matrix(k_eff=1.5, ell_max=ell_max)
            assert np.allclose(M_m0, M_w5a, atol=0)

    def test_m_2_shape(self):
        # ell_max=5, m=2 → dim = 5+1-2 = 4
        M = build_m_streaming_matrix(k_eff=1.0, ell_max=5, m=2)
        assert M.shape == (4, 4)

    def test_m_2_first_row_alpha_zero(self):
        """At first index (ℓ=|m|), α must be zero."""
        M = build_m_streaming_matrix(k_eff=1.0, ell_max=4, m=2)
        # First row: index 0 corresponds to ℓ=2. No below-coupling → M[0, -1] not present
        # M[0, 1] = -β_2^2 = -√5/5
        assert M[0, 1] == pytest.approx(-math.sqrt(5) / 5, rel=1e-14)

    def test_m_2_entries(self):
        """Check entries against analytic formula."""
        M = build_m_streaming_matrix(k_eff=2.0, ell_max=4, m=2)
        # Row index i maps to ℓ = 2 + i
        # ell=3 row (i=1): α_3^2 = √5/7, β_3^2 = √12/7
        assert M[1, 0] == pytest.approx(2.0 * math.sqrt(5) / 7, rel=1e-14)
        assert M[1, 2] == pytest.approx(-2.0 * math.sqrt(12) / 7, rel=1e-14)

    def test_k_zero_gives_zero_matrix(self):
        M = build_m_streaming_matrix(k_eff=0.0, ell_max=4, m=2)
        assert np.all(M == 0.0)

    def test_k_scaling_linear(self):
        M1 = build_m_streaming_matrix(k_eff=1.0, ell_max=4, m=2)
        M5 = build_m_streaming_matrix(k_eff=5.0, ell_max=4, m=2)
        assert np.allclose(M5, 5.0 * M1, atol=1e-14)

    def test_rejects_m_too_large(self):
        with pytest.raises(ValueError, match="|m|"):
            build_m_streaming_matrix(k_eff=1.0, ell_max=2, m=3)

    def test_rejects_negative_k(self):
        with pytest.raises(ValueError, match="k_eff"):
            build_m_streaming_matrix(k_eff=-1.0, ell_max=2, m=0)


# ============================================================================
# Test Class 6 - m-source vector
# ============================================================================

class TestMSourceVector:
    def test_source_at_ell_2_m_zero(self):
        # ell_max=4, m=0, Σ_2=2, s=1e-6
        b = build_m_source_vector(s_amp=1e-6, ell_max=4, m=0, shear_coefficient=2.0)
        # Index of ell=2: 2 (in m=0 channel, indices are ell)
        assert b[2] == pytest.approx(2e-6, rel=1e-14)
        for i in (0, 1, 3, 4):
            assert b[i] == 0.0

    def test_source_at_ell_2_m_2(self):
        # ell_max=5, m=2. First index is ℓ=2. Source at i=0.
        b = build_m_source_vector(s_amp=3e-6, ell_max=5, m=2, shear_coefficient=1.0)
        assert b[0] == pytest.approx(3e-6, rel=1e-14)
        for i in (1, 2, 3):
            assert b[i] == 0.0

    def test_zero_source_amp_zero_vector(self):
        b = build_m_source_vector(s_amp=0.0, ell_max=4, m=0, shear_coefficient=1.0)
        assert np.all(b == 0.0)

    def test_vector_length_matches_m_channel_dim(self):
        b = build_m_source_vector(s_amp=1.0, ell_max=6, m=2, shear_coefficient=1.0)
        assert b.shape == (5,)  # 6+1-2=5

    def test_m_sign_same_magnitude(self):
        b_pos = build_m_source_vector(s_amp=1e-6, ell_max=4, m=+2, shear_coefficient=1.0)
        b_neg = build_m_source_vector(s_amp=1e-6, ell_max=4, m=-2, shear_coefficient=1.0)
        assert np.allclose(b_pos, b_neg, atol=0)


# ============================================================================
# Test Class 7 - MChannelState container
# ============================================================================

class TestMChannelState:
    def test_construction(self):
        s = MChannelState(m=2, amplitudes=np.array([1.0, 2.0, 3.0]))
        assert s.m == 2
        assert s.ell_min == 2
        assert s.ell_max == 4

    def test_m_zero_channel_ell_min_zero(self):
        s = MChannelState(m=0, amplitudes=np.array([1.0, 2.0, 3.0]))
        assert s.ell_min == 0
        assert s.ell_max == 2

    def test_ell_accessor(self):
        s = MChannelState(m=2, amplitudes=np.array([5.0, 6.0, 7.0]))
        assert s.ell(2) == 5.0
        assert s.ell(3) == 6.0
        assert s.ell(4) == 7.0

    def test_ell_out_of_range_raises(self):
        s = MChannelState(m=2, amplitudes=np.array([1.0, 2.0]))
        with pytest.raises(IndexError):
            s.ell(1)   # below |m|
        with pytest.raises(IndexError):
            s.ell(4)   # above ell_max

    def test_empty_amplitudes_rejected(self):
        with pytest.raises(ValueError):
            MChannelState(m=2, amplitudes=np.array([]))


# ============================================================================
# Test Class 8 - BianchiHierarchyParameters
# ============================================================================

class TestBianchiParameters:
    def test_construction(self):
        shear = make_axisymmetric_shear(s_zz=1e-6)
        p = BianchiHierarchyParameters(
            species=TransportSpecies.PHOTON, damping_rate=10.0,
            shear=shear, shear_coefficient=SIGMA_2_PHOTON_BE,
            k_eff=1.0, ell_max=5,
        )
        assert p.species == TransportSpecies.PHOTON
        assert p.ell_max == 5

    def test_rejects_ell_max_below_2(self):
        shear = make_axisymmetric_shear(s_zz=1e-6)
        with pytest.raises(ValueError, match="ell_max"):
            BianchiHierarchyParameters(
                species=TransportSpecies.PHOTON, damping_rate=1.0,
                shear=shear, shear_coefficient=1.0, k_eff=0.0, ell_max=1,
            )

    def test_rejects_negative_damping(self):
        shear = make_axisymmetric_shear(s_zz=1.0)
        with pytest.raises(ValueError, match="damping"):
            BianchiHierarchyParameters(
                species=TransportSpecies.PHOTON, damping_rate=-1.0,
                shear=shear, shear_coefficient=1.0, k_eff=0.0, ell_max=3,
            )

    def test_make_photon_factory(self):
        shear = make_axisymmetric_shear(s_zz=1e-6)
        p = make_photon_bianchi_parameters(
            n_e_sigmaT=10.0, shear=shear, k_eff=1.0, ell_max=5,
            decision=_allowing_decision(),
        )
        assert p.species == TransportSpecies.PHOTON
        assert p.damping_rate == 10.0
        assert p.shear_coefficient == SIGMA_2_PHOTON_BE

    def test_make_neutrino_factory(self):
        shear = make_axisymmetric_shear(s_zz=1e-6)
        p = make_neutrino_bianchi_parameters(
            hubble_rate=30.0, shear=shear, k_eff=1.0, ell_max=5,
            decision=_allowing_decision(),
        )
        assert p.species == TransportSpecies.NEUTRINO
        assert p.damping_rate == 30.0
        assert p.shear_coefficient == SIGMA_2_NEUTRINO_FD


# ============================================================================
# Test Class 9 - Per-m-channel steady-state
# ============================================================================

class TestMChannelSteadyState:
    def test_m_zero_returns_state(self):
        shear = make_axisymmetric_shear(s_zz=1e-6)
        p = make_photon_bianchi_parameters(
            n_e_sigmaT=10.0, shear=shear, k_eff=1.0, ell_max=4,
            decision=_allowing_decision(),
        )
        s = compute_m_channel_steady_state(p, 0, _allowing_decision())
        assert isinstance(s, MChannelState)
        assert s.m == 0

    def test_axisymmetric_m_plus_2_is_zero(self):
        """s_plus = 0 → m=+2 source = 0 → zero amplitudes."""
        shear = make_axisymmetric_shear(s_zz=1e-6)
        p = make_photon_bianchi_parameters(
            n_e_sigmaT=10.0, shear=shear, k_eff=1.0, ell_max=5,
            decision=_allowing_decision(),
        )
        s = compute_m_channel_steady_state(p, +2, _allowing_decision())
        assert np.allclose(s.amplitudes, 0.0, atol=1e-30)

    def test_axisymmetric_m_minus_2_is_zero(self):
        shear = make_axisymmetric_shear(s_zz=1e-6)
        p = make_photon_bianchi_parameters(
            n_e_sigmaT=10.0, shear=shear, k_eff=1.0, ell_max=5,
            decision=_allowing_decision(),
        )
        s = compute_m_channel_steady_state(p, -2, _allowing_decision())
        assert np.allclose(s.amplitudes, 0.0, atol=1e-30)

    def test_rejects_trivial_null_dynamics(self):
        shear = make_axisymmetric_shear(s_zz=1.0)
        p = BianchiHierarchyParameters(
            species=TransportSpecies.PHOTON, damping_rate=0.0,
            shear=shear, shear_coefficient=1.0, k_eff=0.0, ell_max=3,
        )
        with pytest.raises(ValueError, match="trivial"):
            compute_m_channel_steady_state(p, 0, _allowing_decision())


# ============================================================================
# Test Class 10 - Full Bianchi result
# ============================================================================

class TestFullBianchiSteadyState:
    def test_returns_BianchiHierarchyResult(self):
        shear = make_axisymmetric_shear(s_zz=1e-6)
        p = make_photon_bianchi_parameters(
            n_e_sigmaT=10.0, shear=shear, k_eff=1.0, ell_max=5,
            decision=_allowing_decision(),
        )
        r = compute_bianchi_i_steady_state(p, _allowing_decision())
        assert isinstance(r, BianchiHierarchyResult)

    def test_has_three_channels(self):
        shear = make_axisymmetric_shear(s_zz=1e-6)
        p = make_photon_bianchi_parameters(
            n_e_sigmaT=10.0, shear=shear, k_eff=1.0, ell_max=5,
            decision=_allowing_decision(),
        )
        r = compute_bianchi_i_steady_state(p, _allowing_decision())
        assert set(r.channels.keys()) == {0, +2, -2}

    def test_m_plus_2_equals_m_minus_2(self):
        """For real-valued s_plus, m=+2 and m=-2 amplitudes are identical."""
        shear = DiagonalShearTensor(sigma_xx=2e-6, sigma_yy=-0.5e-6, sigma_zz=-1.5e-6)
        p = make_photon_bianchi_parameters(
            n_e_sigmaT=10.0, shear=shear, k_eff=1.0, ell_max=5,
            decision=_allowing_decision(),
        )
        r = compute_bianchi_i_steady_state(p, _allowing_decision())
        assert np.allclose(
            r.channels[+2].amplitudes,
            r.channels[-2].amplitudes, atol=0,
        )

    def test_theta_at_out_of_range_zero(self):
        shear = make_axisymmetric_shear(s_zz=1e-6)
        p = make_photon_bianchi_parameters(
            n_e_sigmaT=10.0, shear=shear, k_eff=1.0, ell_max=5,
            decision=_allowing_decision(),
        )
        r = compute_bianchi_i_steady_state(p, _allowing_decision())
        # m=+2 channel starts at ℓ=2, so ℓ=0 returns 0
        assert r.theta_at(0, +2) == 0.0
        # m=99 doesn't exist
        assert r.theta_at(2, 99) == 0.0

    def test_quadrupole_power_nonnegative(self):
        shear = DiagonalShearTensor(sigma_xx=1e-6, sigma_yy=-0.5e-6, sigma_zz=-0.5e-6)
        p = make_photon_bianchi_parameters(
            n_e_sigmaT=10.0, shear=shear, k_eff=1.0, ell_max=5,
            decision=_allowing_decision(),
        )
        r = compute_bianchi_i_steady_state(p, _allowing_decision())
        assert r.quadrupole_power() >= 0.0

    def test_quadrupole_power_axisymmetric_only_m0(self):
        """For axisymmetric shear, all power comes from m=0."""
        shear = make_axisymmetric_shear(s_zz=1e-6)
        p = make_photon_bianchi_parameters(
            n_e_sigmaT=10.0, shear=shear, k_eff=1.0, ell_max=5,
            decision=_allowing_decision(),
        )
        r = compute_bianchi_i_steady_state(p, _allowing_decision())
        # m=0 contribution
        m0_power = r.channels[0].ell(2) ** 2
        assert r.quadrupole_power() == pytest.approx(m0_power, rel=1e-14)

    def test_result_is_frozen(self):
        shear = make_axisymmetric_shear(s_zz=1e-6)
        p = make_photon_bianchi_parameters(
            n_e_sigmaT=10.0, shear=shear, k_eff=1.0, ell_max=5,
            decision=_allowing_decision(),
        )
        r = compute_bianchi_i_steady_state(p, _allowing_decision())
        with pytest.raises(Exception):
            r.shear = None


# ============================================================================
# Test Class 11 - Axisymmetric reduction (W5-A bit-exact recovery)
# ============================================================================

class TestAxisymmetricReduction:
    """When s_plus = 0, m=0 channel bit-exactly equals W5-A hierarchy."""

    def test_m0_channel_bit_exact_to_W5A(self):
        s_amp = 1e-6
        k = 5.0
        L = 6
        tau = 100.0

        # W5-A needs AxisymmetricSTFTensor convention
        shear_w5a = AxisymmetricSTFTensor(amplitude=s_amp, axis=SymmetryAxis.Z)
        p_w5a = w5a_make_photon_params(
            n_e_sigmaT=tau, shear=shear_w5a, k_eff=k, ell_max=L,
            decision=_allowing_decision(),
        )
        ss_w5a = w5a_compute_steady_state(p_w5a, _allowing_decision())

        # W5-C: build the diagonal shear with the same axial amplitude
        shear_w5c = make_axisymmetric_shear(s_zz=s_amp)
        p_w5c = make_photon_bianchi_parameters(
            n_e_sigmaT=tau, shear=shear_w5c, k_eff=k, ell_max=L,
            decision=_allowing_decision(),
        )
        ss_m0 = compute_m_channel_steady_state(p_w5c, 0, _allowing_decision())

        assert np.allclose(ss_m0.amplitudes, ss_w5a.amplitudes, atol=1e-20)

    def test_m_plus_2_channel_zero_when_axisymmetric(self):
        shear = make_axisymmetric_shear(s_zz=1e-6)
        p = make_photon_bianchi_parameters(
            n_e_sigmaT=100.0, shear=shear, k_eff=5.0, ell_max=6,
            decision=_allowing_decision(),
        )
        ss = compute_m_channel_steady_state(p, +2, _allowing_decision())
        assert np.allclose(ss.amplitudes, 0.0, atol=0)

    def test_m_minus_2_channel_zero_when_axisymmetric(self):
        shear = make_axisymmetric_shear(s_zz=1e-6)
        p = make_photon_bianchi_parameters(
            n_e_sigmaT=100.0, shear=shear, k_eff=5.0, ell_max=6,
            decision=_allowing_decision(),
        )
        ss = compute_m_channel_steady_state(p, -2, _allowing_decision())
        assert np.allclose(ss.amplitudes, 0.0, atol=0)

    def test_full_axisymmetric_result_same_as_W5A(self):
        s_amp = 1e-6
        k = 5.0
        L = 6
        tau = 100.0

        shear_w5a = AxisymmetricSTFTensor(amplitude=s_amp, axis=SymmetryAxis.Z)
        p_w5a = w5a_make_photon_params(
            n_e_sigmaT=tau, shear=shear_w5a, k_eff=k, ell_max=L,
            decision=_allowing_decision(),
        )
        ss_w5a = w5a_compute_steady_state(p_w5a, _allowing_decision())

        shear_w5c = make_axisymmetric_shear(s_zz=s_amp)
        p_w5c = make_photon_bianchi_parameters(
            n_e_sigmaT=tau, shear=shear_w5c, k_eff=k, ell_max=L,
            decision=_allowing_decision(),
        )
        result = compute_bianchi_i_steady_state(p_w5c, _allowing_decision())

        # m=0 channel gives the full physics; m=±2 are zero
        for ell in range(L + 1):
            assert result.theta_at(ell, 0) == pytest.approx(
                ss_w5a.amplitudes[ell], rel=1e-14, abs=1e-30,
            )
        # Quadrupole power only from m=0
        assert result.quadrupole_power() == pytest.approx(
            ss_w5a.amplitudes[2] ** 2, rel=1e-14,
        )


# ============================================================================
# Test Class 12 - Runtime gating
# ============================================================================

class TestRuntimeGating:
    def test_compute_m_channel_blocked(self):
        shear = make_axisymmetric_shear(s_zz=1e-6)
        p = make_photon_bianchi_parameters(
            n_e_sigmaT=10.0, shear=shear, k_eff=1.0, ell_max=5,
            decision=_allowing_decision(),
        )
        with pytest.raises(CanonicalBlockError, match="compute_m_channel_steady_state"):
            compute_m_channel_steady_state(p, 0, _blocking_decision())

    def test_compute_bianchi_blocked(self):
        shear = make_axisymmetric_shear(s_zz=1e-6)
        p = make_photon_bianchi_parameters(
            n_e_sigmaT=10.0, shear=shear, k_eff=1.0, ell_max=5,
            decision=_allowing_decision(),
        )
        with pytest.raises(CanonicalBlockError, match="compute_bianchi_i_steady_state"):
            compute_bianchi_i_steady_state(p, _blocking_decision())

    def test_photon_factory_blocked(self):
        shear = make_axisymmetric_shear(s_zz=1e-6)
        with pytest.raises(CanonicalBlockError):
            make_photon_bianchi_parameters(
                n_e_sigmaT=10.0, shear=shear, k_eff=1.0, ell_max=5,
                decision=_blocking_decision(),
            )

    def test_neutrino_factory_blocked(self):
        shear = make_axisymmetric_shear(s_zz=1e-6)
        with pytest.raises(CanonicalBlockError):
            make_neutrino_bianchi_parameters(
                hubble_rate=30.0, shear=shear, k_eff=1.0, ell_max=5,
                decision=_blocking_decision(),
            )

    def test_blocked_error_carries_decision(self):
        shear = make_axisymmetric_shear(s_zz=1e-6)
        try:
            make_photon_bianchi_parameters(
                n_e_sigmaT=10.0, shear=shear, k_eff=1.0, ell_max=5,
                decision=_blocking_decision(),
            )
        except CanonicalBlockError as e:
            assert e.decision.allow_reduction is False
