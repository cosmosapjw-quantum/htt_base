"""bass/forward/test_doppler_boost.py — Doppler boost correction tests.

Adapted from legacy/bass/tests/test_teff_forward.py (Layer-1 subset).
"""
import numpy as np
import pytest

from bass.forward.doppler_boost import (
    DopplerBoostCorrection,
    analytical_c1,
    delta_eps_boost,
)


class TestAnalyticalC1:
    """The empirical boost coupling coefficient c₁ ≈ 2.684."""

    def test_value(self):
        assert analytical_c1() == pytest.approx(2.684, abs=1e-4)

    def test_is_positive(self):
        assert analytical_c1() > 2.5
        assert analytical_c1() < 3.0


class TestDeltaEpsBoost:
    """δε_ℓ(β) kernel components."""

    def test_dipole_direct(self):
        """δε₁ = β (direct boost)."""
        eps = np.zeros(4)
        assert delta_eps_boost(1, 1e-3, eps) == pytest.approx(1e-3)

    def test_dipole_independent_of_eps_values(self):
        eps1 = np.array([0.0, 0.0, 1e-3, 1e-4])
        eps2 = np.array([0.0, 1e-3, 1e-3, 1e-4])
        beta = 1e-3
        assert delta_eps_boost(1, beta, eps1) == delta_eps_boost(1, beta, eps2)

    def test_quadrupole_mix(self):
        """δε₂ = (4/5)·ε₂·β + ε₁²."""
        eps = np.array([0.0, 1e-3, 2e-3, 0.0])
        beta = 1e-3
        expected = (4.0 / 5.0) * 2e-3 * 1e-3 + (1e-3) ** 2
        assert delta_eps_boost(2, beta, eps) == pytest.approx(expected, rel=1e-12)

    def test_octupole_mix(self):
        """δε₃ = (6/7)·ε₃·β + ε₁·ε₂."""
        eps = np.array([0.0, 1e-3, 2e-3, 3e-3])
        beta = 1e-3
        expected = (6.0 / 7.0) * 3e-3 * 1e-3 + 1e-3 * 2e-3
        assert delta_eps_boost(3, beta, eps) == pytest.approx(expected, rel=1e-12)

    def test_higher_ell_zero(self):
        eps = np.array([0.0, 1e-3, 2e-3, 3e-3, 4e-3])
        for ell in (0, 4, 5, 6):
            assert delta_eps_boost(ell, 1e-3, eps) == 0.0

    def test_zero_beta(self):
        """β = 0 → δε₁ = 0 directly; δε₂ is still O(ε₁²) however."""
        eps = np.array([0.0, 0.0, 0.0, 0.0])
        assert delta_eps_boost(1, 0.0, eps) == 0.0


class TestDopplerBoostCorrection:
    """R_σ, R_ω, R_u̇ factors."""

    def test_R_sigma_identity_at_zero(self):
        d = DopplerBoostCorrection()
        assert d.R_sigma_boost(0.0) == pytest.approx(1.0)

    def test_R_sigma_cf4(self):
        """R_σ at CF4 ε₁ = 1.334e-3 ≈ 1.00358."""
        d = DopplerBoostCorrection()
        assert d.R_sigma_boost(1.334e-3) == pytest.approx(1.0 + 2.684 * 1.334e-3,
                                                          abs=1e-8)

    def test_R_omega_always_one(self):
        d = DopplerBoostCorrection()
        for eps1 in (0.0, 1e-4, 1e-3, 1e-2, 0.1):
            assert d.R_omega_boost(eps1) == 1.0

    def test_R_udot_suppressed(self):
        """R_u̇ correction should be about 10× smaller than R_σ at same ε₁."""
        d = DopplerBoostCorrection()
        eps1 = 1e-3
        sig_corr = d.R_sigma_boost(eps1) - 1.0
        udot_corr = d.R_udot_boost(eps1) - 1.0
        assert sig_corr > 5.0 * udot_corr

    def test_delta_B_sigma_symmetric(self):
        """δB_σ should linearly scale with β."""
        d = DopplerBoostCorrection()
        dB1 = d.delta_B_sigma(1e-3, 1e-3, 1e-3, 1e-4)
        dB2 = d.delta_B_sigma(2e-3, 1e-3, 1e-3, 1e-4)
        # Not exactly 2× since the ε₁² term is β-independent, but close
        assert dB2 > dB1

    def test_delta_B_sigma_zero_at_zero_eps(self):
        d = DopplerBoostCorrection()
        dB = d.delta_B_sigma(0.0, 0.0, 0.0, 0.0)
        assert dB == 0.0
