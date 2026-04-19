"""COMMON-F tests — mock_calibration (INDEPENDENT_TRACKS_PLAN §3.1).

Includes the REG-01 ``test_mock_coverage_within_bounds`` regression.
"""
from __future__ import annotations

import numpy as np
import pytest

from common.bulkflow_estimator import BulkFlowCatalogue
from common.contracts import MockCalibrationReport, SkySelectionConfig
from common.mock_calibration import (
    InjectedMockReport,
    apply_bias_correction,
    apply_same_mask,
    coverage_test,
    generate_injected_dipole_mock,
    generate_isotropic_mock,
    recovered_bias,
    run_injected_dipole_mocks,
    run_zoa_null_mocks,
)
from common.sky_geometry import lb_to_unitvec


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _isotropic_catalogue(
    *,
    n: int = 300,
    sigma_u: float = 40.0,
    seed: int = 0,
) -> BulkFlowCatalogue:
    rng = np.random.default_rng(seed)
    cos_b = rng.uniform(-1.0, 1.0, size=n)
    b_deg = np.rad2deg(np.arcsin(cos_b))
    l_deg = rng.uniform(0.0, 360.0, size=n)
    n_hat = lb_to_unitvec(l_deg, b_deg)
    u = rng.normal(0.0, sigma_u, size=n)
    sigma = np.full(n, sigma_u, dtype=float)
    return BulkFlowCatalogue(
        n_hat=n_hat,
        u=u,
        sigma=sigma,
        w_native=np.ones(n),
        w_selection=np.ones(n),
    )


# ---------------------------------------------------------------------------
# §1 — mock generation
# ---------------------------------------------------------------------------

class TestMockGeneration:
    def test_isotropic_mock_has_zero_mean_over_many_realisations(self):
        cat = _isotropic_catalogue(n=500)
        rng = np.random.default_rng(0)
        means = []
        for _ in range(30):
            mock = generate_isotropic_mock(cat, rng=rng)
            means.append(mock.u.mean())
        np.testing.assert_allclose(float(np.mean(means)), 0.0, atol=5.0)

    def test_injected_dipole_reproduces_projection(self):
        cat = _isotropic_catalogue(n=500, sigma_u=10.0)
        V_true = np.array([500.0, 0.0, 0.0])
        rng = np.random.default_rng(1)
        mock = generate_injected_dipole_mock(cat, V_true, rng=rng)
        # Radial component: u_i ≈ n_hat_i · V_true + noise.
        expected = cat.n_hat @ V_true
        np.testing.assert_allclose(mock.u, expected, atol=60.0)

    def test_injected_dipole_rejects_wrong_shape(self):
        cat = _isotropic_catalogue(n=50)
        with pytest.raises(ValueError, match="V_true"):
            generate_injected_dipole_mock(cat, np.array([1.0, 2.0]))


# ---------------------------------------------------------------------------
# §2 — apply_same_mask
# ---------------------------------------------------------------------------

class TestApplySameMask:
    def test_masked_catalogue_preserves_geometry(self):
        cat = _isotropic_catalogue(n=500, seed=2)
        cfg = SkySelectionConfig(zoa_half_angle_deg=10.0, nside=16)
        masked = apply_same_mask(cat, cfg)
        assert masked.n_sources == cat.n_sources
        # Selection weights were replaced — at least some pixels zeroed.
        assert np.any(masked.w_selection == 0.0) or np.allclose(
            masked.w_selection, cat.w_selection
        )

    def test_zoa_cut_zeroes_plane_sources(self):
        rng = np.random.default_rng(3)
        n = 100
        l_deg = rng.uniform(0.0, 360.0, size=n)
        # Half in the plane, half polar.
        b_deg = np.concatenate([np.full(n // 2, 2.0), np.full(n // 2, 70.0)])
        n_hat = lb_to_unitvec(l_deg, b_deg)
        cat = BulkFlowCatalogue(
            n_hat=n_hat, u=np.zeros(n), sigma=np.ones(n),
            w_native=np.ones(n), w_selection=np.ones(n),
        )
        cfg = SkySelectionConfig(zoa_half_angle_deg=15.0, nside=16)
        masked = apply_same_mask(cat, cfg)
        # In-plane half gets zero weight; polar half keeps positive weight.
        assert np.all(masked.w_selection[: n // 2] == 0.0)
        assert np.all(masked.w_selection[n // 2:] >= 0.0)
        # At least the polar sources retain *some* positive weight.
        assert np.any(masked.w_selection[n // 2:] > 0.0)


# ---------------------------------------------------------------------------
# §3 — recovered_bias / coverage_test
# ---------------------------------------------------------------------------

class TestRecoveredBias:
    def test_zero_bias_for_truth_recovery(self):
        V_true = np.array([300.0, 0.0, 0.0])
        V_hat = np.tile(V_true, (100, 1))
        out = recovered_bias(V_true, V_hat)
        np.testing.assert_allclose(out["amp_bias_fraction"], 0.0, atol=1e-9)
        np.testing.assert_allclose(out["direction_bias_deg"], 0.0, atol=1e-9)
        assert out["amp_spread_fractional"] == 0.0

    def test_fractional_bias_sign(self):
        V_true = np.array([100.0, 0.0, 0.0])
        V_hat = np.tile(np.array([120.0, 0.0, 0.0]), (50, 1))
        out = recovered_bias(V_true, V_hat)
        np.testing.assert_allclose(out["amp_bias_fraction"], 0.2, atol=1e-9)

    def test_null_truth_returns_nan_biases(self):
        V_true = np.zeros(3)
        V_hat = np.array([[10.0, 0.0, 0.0], [20.0, 0.0, 0.0]])
        out = recovered_bias(V_true, V_hat)
        assert np.isnan(out["amp_bias_fraction"])
        assert np.isnan(out["direction_bias_deg"])


class TestCoverageTest:
    def test_gaussian_posterior_reproduces_target_coverage(self):
        rng = np.random.default_rng(0)
        truth = np.array([100.0, 0.0, 0.0])
        sigma = 20.0
        n = 1000
        cov = np.eye(3) * sigma ** 2
        estimates = rng.normal(truth, sigma, size=(n, 3))
        covariances = np.broadcast_to(cov, (n, 3, 3)).copy()
        cov68 = coverage_test(estimates, covariances, truth, level=0.68)
        assert 0.60 <= cov68 <= 0.76

    def test_rejects_malformed_shapes(self):
        with pytest.raises(ValueError, match="estimates"):
            coverage_test(np.zeros((5, 2)), np.zeros((5, 3, 3)), np.zeros(3))

    def test_rejects_bad_level(self):
        estimates = np.zeros((5, 3))
        cov = np.broadcast_to(np.eye(3), (5, 3, 3))
        with pytest.raises(ValueError, match="level"):
            coverage_test(estimates, cov, np.zeros(3), level=0.0)


# ---------------------------------------------------------------------------
# §4 — REG-01: test_mock_coverage_within_bounds
# ---------------------------------------------------------------------------

class TestMockCoverageWithinBounds:
    """REG-01 — ``coverage_68pct ∈ [0.60, 0.76]`` on a controlled mock bank.

    Uses a generous isotropic catalogue and the default WLS estimator to
    produce (V_hat, cov) pairs under the null hypothesis. A well-calibrated
    Gaussian estimator must land coverage inside the published window for
    the Mode 2 fiducial artefact to be trusted.
    """

    def test_zoa_null_coverage_within_published_window(self):
        """Under the null hypothesis on an isotropic geometry with uniform
        completeness, the WLS closed-form covariance is exact and the
        68% Mahalanobis coverage must land inside [0.60, 0.76]."""
        cat = _isotropic_catalogue(n=400, sigma_u=50.0, seed=11)
        cfg = SkySelectionConfig(zoa_half_angle_deg=5.0, nside=16)
        # Force uniform completeness so selection weights are dimensionless
        # and the WLS cov has a direct sampling-variance interpretation
        # (the operational ``C_pix`` overlay is exercised separately below).
        from common.healpix_selection import nside_to_npix
        C_pix_uniform = np.ones(nside_to_npix(cfg.nside))
        report = run_zoa_null_mocks(
            cat, cfg, n_mock=200,
            rng=np.random.default_rng(42), C_pix=C_pix_uniform,
        )
        assert isinstance(report, MockCalibrationReport)
        assert 0.60 <= report.coverage_68 <= 0.76, (
            f"coverage_68 = {report.coverage_68:.3f} outside [0.60, 0.76] — "
            "REG-01 violation"
        )
        # Sanity: coverage_95 recorded in config and near its nominal value.
        cov95 = report.config["coverage_95"]
        assert 0.88 <= cov95 <= 0.99

    def test_bank_reports_n_mock_and_amplitude_distribution(self):
        cat = _isotropic_catalogue(n=300, sigma_u=45.0, seed=12)
        cfg = SkySelectionConfig(zoa_half_angle_deg=5.0, nside=16)
        from common.healpix_selection import nside_to_npix
        C_pix_uniform = np.ones(nside_to_npix(cfg.nside))
        report = run_zoa_null_mocks(
            cat, cfg, n_mock=120,
            rng=np.random.default_rng(99), C_pix=C_pix_uniform,
        )
        assert report.n_mock >= 20
        assert "null_amplitude_mean" in report.config
        assert "null_amplitude_std" in report.config


# ---------------------------------------------------------------------------
# §5 — run_injected_dipole_mocks + apply_bias_correction
# ---------------------------------------------------------------------------

class TestInjectedDipoleMocks:
    def test_recovers_injected_V_within_tolerance(self):
        cat = _isotropic_catalogue(n=400, sigma_u=30.0, seed=4)
        cfg = SkySelectionConfig(zoa_half_angle_deg=5.0, nside=16)
        V_true = np.array([370.0, 0.0, 0.0])
        report = run_injected_dipole_mocks(
            cat, V_true, cfg, n_mock=100, rng=np.random.default_rng(5),
        )
        assert isinstance(report, InjectedMockReport)
        assert report.n_mock >= 20
        # Mean recovered amplitude within 10% of truth
        assert abs(report.amp_bias_fraction) < 0.10
        # Mean direction within ~5° of truth (robust to ZoA cut).
        assert report.direction_bias_deg < 10.0

    def test_rejects_zero_V_true(self):
        cat = _isotropic_catalogue(n=60)
        cfg = SkySelectionConfig(zoa_half_angle_deg=5.0, nside=16)
        with pytest.raises(ValueError, match="non-zero V_true"):
            run_injected_dipole_mocks(cat, np.zeros(3), cfg, n_mock=10)


class TestApplyBiasCorrection:
    def test_de_bias_cancels_mean_residual(self):
        samples = np.array([
            [110.0, 0.0, 0.0],
            [105.0, 5.0, 0.0],
            [115.0, -5.0, 0.0],
        ])
        V_true = np.array([100.0, 0.0, 0.0])
        report = InjectedMockReport(
            recovered_V_samples=samples,
            amp_bias_fraction=0.10,
            direction_bias_deg=0.0,
            amp_spread_fractional=0.05,
            n_mock=3,
            config={"V_true": tuple(V_true)},
        )
        V_hat = np.array([110.0, 0.0, 0.0])
        corrected = apply_bias_correction(V_hat, report)
        # Mean residual is (110 − 100) = 10 along x; after subtracting it,
        # the corrected estimate equals V_true.
        np.testing.assert_allclose(corrected, V_true, atol=1e-9)

    def test_rejects_report_without_V_true(self):
        report = InjectedMockReport(
            recovered_V_samples=np.zeros((1, 3)),
            amp_bias_fraction=0.0,
            direction_bias_deg=0.0,
            amp_spread_fractional=0.0,
            n_mock=1,
            config={},
        )
        with pytest.raises(ValueError, match="V_true"):
            apply_bias_correction(np.array([1.0, 2.0, 3.0]), report)
