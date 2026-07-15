"""bass/forward/test_teff_mes_bounds.py — Two-layer MES bound tests.

Adapted from legacy/bass/tests/test_teff_forward.py (Layer-2 + F-invariance
+ VN-04 cross-check).
"""
import pytest

from bass.forward.teff_mes_bounds import TeffMESBounds, VN04_SCENARIOS


class TestLayerDominance:
    """Layer 1 (Doppler, O(β)) dominates Layer 2 (Gaunt, O(β²)) by 10³."""

    def test_boost_dominates_gaunt(self):
        mes = TeffMESBounds()
        eps1, eps2 = 1.2e-3, 9.0e-4
        R_boost = mes.R_sigma_boost(eps1)
        R_gaunt = mes.R_sigma_gaunt(eps1, eps2)
        boost_contrib = abs(R_boost - 1.0)
        gaunt_contrib = abs(R_gaunt - 1.0)
        assert boost_contrib > 100 * gaunt_contrib


class TestVN04CrossCheck:
    """R_σ^{combined} matches VN-04 empirical at S1/S2/S3 to < 1%."""

    @pytest.mark.parametrize("name", list(VN04_SCENARIOS.keys()))
    def test_scenario_within_1pct(self, name):
        mes = TeffMESBounds()
        results = mes.cross_check_vn04()
        assert results[name]['within_1pct'], (
            f"{name} rel_error={results[name]['rel_error']:.4e} exceeds 1%"
        )

    def test_all_scenarios_converge(self):
        mes = TeffMESBounds()
        results = mes.cross_check_vn04()
        for name, r in results.items():
            assert r['rel_error'] < 0.01, f"{name}: {r}"
            assert 1.0 < r['R_ours'] < 1.05


class TestZeroInputs:
    """At ε₁ = 0 all shear corrections vanish; vorticity always exactly 1."""

    def test_R_sigma_zero_at_zero_eps1(self):
        mes = TeffMESBounds()
        assert mes.R_sigma_boost(0.0) == pytest.approx(1.0)
        assert mes.R_sigma_gaunt(0.0, 1e-3) == pytest.approx(1.0)
        assert mes.R_sigma_combined(0.0, 1e-3) == pytest.approx(1.0)

    def test_R_omega_always_one(self):
        mes = TeffMESBounds()
        for eps1 in (0.0, 1e-4, 1e-3, 1e-2):
            assert mes.R_omega_combined(eps1, 0.0) == 1.0


class TestUniversalRatios:

    def test_omega_sigma_ratio_1478(self):
        mes = TeffMESBounds()
        r = mes.universal_ratios_analytical()
        assert r['Delta_omega_over_Delta_sigma'] == pytest.approx(1.478, abs=0.01)

    def test_udot_sigma_ratio_small(self):
        mes = TeffMESBounds()
        r = mes.universal_ratios_analytical()
        assert r['Delta_udot_over_Delta_sigma'] < 0.01

    def test_contains_c1_and_c2(self):
        """Ratios dict exposes the coupling constants."""
        mes = TeffMESBounds()
        r = mes.universal_ratios_analytical()
        assert r['c1'] == pytest.approx(2.684, abs=1e-4)
        assert r['c2'] == pytest.approx(4.18)


class TestFillingFractionCorrection:
    """F invariance breakdown: ΔF < 0 when R_σ > 1 and Ω_tilt > 0."""

    def test_correction_sign_negative(self):
        mes = TeffMESBounds()
        r = mes.filling_fraction_correction(
            x=1e-6, x_max=1.233e-3, Omega_tilt=4.4e-8, R_sigma=1.003,
        )
        assert r['Delta_F'] < 0

    def test_magnitude_synthetic_bounded(self):
        """ΔF/F is small but nonzero for a synthetic perturbation."""
        mes = TeffMESBounds()
        R_sigma = mes.R_sigma_combined(1.2e-3, 9.0e-4)
        r = mes.filling_fraction_correction(
            x=1e-6, x_max=1.233e-3, Omega_tilt=4.4e-8, R_sigma=R_sigma,
        )
        assert abs(r['Delta_F_over_F']) > 0
        assert abs(r['Delta_F_over_F']) < 0.1

    def test_zero_tilt_preserves_F(self):
        mes = TeffMESBounds()
        r = mes.filling_fraction_correction(
            x=1e-6, x_max=1.233e-3, Omega_tilt=0.0, R_sigma=1.003,
        )
        assert r['Delta_F'] == pytest.approx(0.0)
        assert r['F_teff'] == pytest.approx(r['F_lin'])

    def test_R_sigma_eq_1_preserves_F(self):
        """If R_σ = 1 (no boost) there is no correction regardless of Ω_tilt."""
        mes = TeffMESBounds()
        r = mes.filling_fraction_correction(
            x=1e-6, x_max=1.233e-3, Omega_tilt=4.4e-8, R_sigma=1.0,
        )
        assert r['Delta_F'] == pytest.approx(0.0, abs=1e-30)

    def test_zero_x_max(self):
        mes = TeffMESBounds()
        r = mes.filling_fraction_correction(
            x=1.0, x_max=0.0, Omega_tilt=0.0, R_sigma=1.0,
        )
        assert r == {'F_lin': 0.0, 'F_teff': 0.0, 'Delta_F': 0.0, 'Delta_F_over_F': 0.0}


class TestIntegrationWithForward:
    """Combined test: use theta4_coefficients → a_ℓ → ε_ℓ → MES bound correction."""

    def test_forward_to_mes_chain(self):
        """Roundtrip: A=β, Q=(5/3)√(6Σ²) → a_ℓ → (ε₁, ε₂) → R_σ."""
        from bass.forward.teff_forward import TeffBianchiForward
        teff = TeffBianchiForward()
        mes = TeffMESBounds()

        Sigma2 = 1e-6
        beta = 1.2e-3
        r = teff.compute_from_shear(Sigma2, beta)
        # Convert a_ℓ to effective ε_ℓ (= a_ℓ / 4)
        eps1 = r['a_ell'][1] / 4.0
        eps2 = r['a_ell'][2] / 4.0
        assert eps1 == pytest.approx(beta, rel=0.02)  # ε₁ ≈ β for small Q
        R_sigma = mes.R_sigma_combined(eps1, eps2)
        assert R_sigma > 1.0
        assert R_sigma < 1.01  # tiny in this synthetic small-beta regime
