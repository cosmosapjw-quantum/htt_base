"""COMMON-E tests — posterior_summary (INDEPENDENT_TRACKS_PLAN §3.1)."""
from __future__ import annotations

import json

import numpy as np
import pytest

from common.contracts import DynestyResult, MockCalibrationReport, PreferredAxis
from common.posterior_summary import (
    axis_from_posterior,
    credible_cone,
    fiducial_posterior_bundle,
    hpd_region_healpix,
    posterior_summary_dict,
    samples_to_lb_posterior,
)
from common.sky_geometry import lb_to_unitvec, unitvec_to_lb


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _gaussian_V_samples(
    V_center: np.ndarray,
    *,
    n: int = 2000,
    sigma: float = 40.0,
    seed: int = 0,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.normal(V_center, sigma, size=(n, 3))


# ---------------------------------------------------------------------------
# §1 — samples_to_lb_posterior
# ---------------------------------------------------------------------------

class TestSamplesToLbPosterior:
    def test_round_trip_for_axis_aligned_samples(self):
        samples = np.array([
            [100.0, 0.0, 0.0],
            [200.0, 0.0, 0.0],
            [300.0, 0.0, 0.0],
        ])
        out = samples_to_lb_posterior(samples)
        np.testing.assert_allclose(out["l_deg"], np.zeros(3), atol=1e-9)
        np.testing.assert_allclose(out["b_deg"], np.zeros(3), atol=1e-9)
        np.testing.assert_allclose(
            out["amplitude_kmps"], [100.0, 200.0, 300.0], atol=1e-9
        )
        np.testing.assert_allclose(out["weights"].sum(), 1.0, atol=1e-12)

    def test_drops_zero_magnitude_samples(self):
        samples = np.array([
            [0.0, 0.0, 0.0],
            [100.0, 0.0, 0.0],
            [200.0, 0.0, 0.0],
        ])
        out = samples_to_lb_posterior(samples)
        assert out["l_deg"].size == 2
        assert out["amplitude_kmps"].shape == (2,)

    def test_rejects_wrong_shape(self):
        with pytest.raises(ValueError, match=r"\(n, 3\)"):
            samples_to_lb_posterior(np.zeros((5, 2)))

    def test_rejects_negative_weights(self):
        samples = np.array([[100.0, 0.0, 0.0], [200.0, 0.0, 0.0]])
        with pytest.raises(ValueError, match="≥ 0"):
            samples_to_lb_posterior(samples, weights=np.array([-1.0, 1.0]))

    def test_weight_preservation_under_mask(self):
        samples = np.array([[0.0, 0.0, 0.0], [100.0, 0.0, 0.0]])
        weights = np.array([0.3, 0.7])
        out = samples_to_lb_posterior(samples, weights=weights)
        # Only the second sample survives — weight normalises to 1.
        np.testing.assert_allclose(out["weights"], [1.0])


# ---------------------------------------------------------------------------
# §2 — credible_cone
# ---------------------------------------------------------------------------

class TestCredibleCone:
    def test_recovers_center_for_isotropic_bundle(self):
        V_center = np.array([300.0, 0.0, 0.0])
        samples = _gaussian_V_samples(V_center, n=3000, sigma=20.0, seed=1)
        lb = samples_to_lb_posterior(samples)
        cone = credible_cone(
            lb["l_deg"], lb["b_deg"], level=0.68, weights=lb["weights"],
        )
        true_l, true_b = unitvec_to_lb(V_center / np.linalg.norm(V_center))
        # Compare longitudes modulo 360° (cone center may sit at either side
        # of the 0°/360° wrap).
        dl = (cone["center_l_deg"] - float(true_l) + 180.0) % 360.0 - 180.0
        assert abs(dl) < 1.5
        assert abs(cone["center_b_deg"] - float(true_b)) < 1.5
        # And radius is a small but positive angle.
        assert 0.5 < cone["radius_deg"] < 30.0

    def test_level_monotone_in_radius(self):
        V_center = np.array([0.0, 250.0, 0.0])
        samples = _gaussian_V_samples(V_center, n=4000, sigma=30.0, seed=2)
        lb = samples_to_lb_posterior(samples)
        r_68 = credible_cone(lb["l_deg"], lb["b_deg"], level=0.68)["radius_deg"]
        r_95 = credible_cone(lb["l_deg"], lb["b_deg"], level=0.95)["radius_deg"]
        assert r_95 >= r_68

    def test_rejects_degenerate_posterior(self):
        # Samples that cancel to zero mean direction (antipodal pair × many).
        samples_lb = np.array([[0.0, 0.0], [180.0, 0.0]])
        with pytest.raises(ValueError, match="degenerate"):
            credible_cone(samples_lb[:, 0], samples_lb[:, 1], level=0.5)

    def test_rejects_bad_level(self):
        with pytest.raises(ValueError, match="level"):
            credible_cone(np.array([0.0]), np.array([0.0]), level=0.0)
        with pytest.raises(ValueError, match="level"):
            credible_cone(np.array([0.0]), np.array([0.0]), level=1.0)


# ---------------------------------------------------------------------------
# §3 — hpd_region_healpix
# ---------------------------------------------------------------------------

class TestHPDRegion:
    def test_mass_covered_at_or_above_level(self):
        V_center = np.array([200.0, 100.0, 0.0])
        samples = _gaussian_V_samples(V_center, n=3000, sigma=25.0, seed=3)
        lb = samples_to_lb_posterior(samples)
        out = hpd_region_healpix(
            lb["l_deg"], lb["b_deg"], nside=16, level=0.68,
        )
        assert out["covered_fraction"] >= 0.68 - 1e-12
        assert out["n_pix_in_set"] >= 1
        assert out["mask_pix"].dtype == bool

    def test_density_sums_to_one(self):
        V = np.array([100.0, 0.0, 0.0])
        samples = _gaussian_V_samples(V, n=1000, sigma=20.0, seed=4)
        lb = samples_to_lb_posterior(samples)
        out = hpd_region_healpix(
            lb["l_deg"], lb["b_deg"], nside=8, level=0.68,
        )
        np.testing.assert_allclose(out["density"].sum(), 1.0, atol=1e-12)

    def test_higher_level_is_larger_set(self):
        V = np.array([120.0, 80.0, 40.0])
        samples = _gaussian_V_samples(V, n=2000, sigma=35.0, seed=5)
        lb = samples_to_lb_posterior(samples)
        o68 = hpd_region_healpix(lb["l_deg"], lb["b_deg"], nside=16, level=0.68)
        o95 = hpd_region_healpix(lb["l_deg"], lb["b_deg"], nside=16, level=0.95)
        assert o95["n_pix_in_set"] >= o68["n_pix_in_set"]


# ---------------------------------------------------------------------------
# §4 — axis_from_posterior (production gate path)
# ---------------------------------------------------------------------------

class TestAxisFromPosterior:
    def test_returns_production_allowed_axis(self):
        V_center = np.array([300.0, 0.0, 0.0])
        samples = _gaussian_V_samples(V_center, n=2000, sigma=20.0, seed=6)
        axis = axis_from_posterior(samples)
        assert isinstance(axis, PreferredAxis)
        assert axis.production_allowed is True
        assert axis.source == "fiducial_posterior"
        assert axis.provenance_hash != ""

    def test_axis_direction_tracks_posterior_mean(self):
        V_center = np.array([0.0, 400.0, 0.0])
        samples = _gaussian_V_samples(V_center, n=2000, sigma=15.0, seed=7)
        axis = axis_from_posterior(samples)
        # (0, 400, 0) → l ≈ 90°, b ≈ 0°.
        assert abs(axis.l_deg - 90.0) < 1.5
        assert abs(axis.b_deg) < 1.5

    def test_rejects_degenerate_posterior(self):
        # Symmetric antipodal pair → E[V] is exactly zero.
        samples = np.array([[100.0, 0.0, 0.0], [-100.0, 0.0, 0.0]])
        with pytest.raises(ValueError, match="degenerate"):
            axis_from_posterior(samples)

    def test_rejects_empty(self):
        with pytest.raises(ValueError, match="empty"):
            axis_from_posterior(np.zeros((0, 3)))

    def test_provenance_is_deterministic(self):
        V = np.array([120.0, 50.0, 30.0])
        samples = _gaussian_V_samples(V, n=500, sigma=10.0, seed=8)
        a1 = axis_from_posterior(samples, config={"run": "A"})
        a2 = axis_from_posterior(samples, config={"run": "A"})
        a3 = axis_from_posterior(samples, config={"run": "B"})
        assert a1.provenance_hash == a2.provenance_hash
        assert a1.provenance_hash != a3.provenance_hash


# ---------------------------------------------------------------------------
# §5 — posterior_summary_dict
# ---------------------------------------------------------------------------

class TestPosteriorSummaryDict:
    def test_bundle_contains_expected_keys(self):
        V_center = np.array([300.0, 0.0, 0.0])
        samples = _gaussian_V_samples(V_center, n=1500, sigma=25.0, seed=9)
        bundle = posterior_summary_dict(samples, evidence=12.5, nside_hpd=16)
        for key in (
            "logz", "lb_posterior", "amplitude_mean", "amplitude_std",
            "credible_cone", "hpd_region",
        ):
            assert key in bundle
        assert bundle["logz"] == 12.5

    def test_amplitude_stats_match_samples(self):
        V = np.array([500.0, 0.0, 0.0])
        samples = _gaussian_V_samples(V, n=1000, sigma=30.0, seed=10)
        bundle = posterior_summary_dict(samples, evidence=0.0, nside_hpd=16)
        amps = np.linalg.norm(samples, axis=1)
        np.testing.assert_allclose(bundle["amplitude_mean"], amps.mean(), rtol=1e-6)
        np.testing.assert_allclose(bundle["amplitude_std"], amps.std(), rtol=1e-6)


# ---------------------------------------------------------------------------
# §6 — fiducial_posterior_bundle
# ---------------------------------------------------------------------------

class TestFiducialPosteriorBundle:
    def _dynesty_result(self) -> DynestyResult:
        V = np.array([240.0, -80.0, 50.0])
        samples = _gaussian_V_samples(V, n=800, sigma=25.0, seed=11)
        # Deliberately unnormalised log-weights — the bundle builder should
        # stabilise and renormalise them internally.
        raw_w = np.linspace(1.0, 2.0, samples.shape[0])
        return DynestyResult(
            samples=samples,
            logwt=np.log(raw_w),
            logz=14.25,
            ncall=321,
            config={"seed": 17, "sampler": "static", "nlive": 128},
        )

    def _mock_report(self, coverage_68: float = 0.68) -> MockCalibrationReport:
        return MockCalibrationReport(
            bias_amp=0.03,
            bias_direction_deg=2.5,
            coverage_68=coverage_68,
            credible_radius_deg=15.0,
            n_mock=200,
            config={"coverage_95": 0.94},
        )

    def test_bundle_is_json_serialisable_and_production_gated(self):
        bundle = fiducial_posterior_bundle(
            self._dynesty_result(),
            mock_report=self._mock_report(),
            nside_hpd=16,
            metadata={
                "git_commit": "abc123",
                "input_data_hashes": ["deadbeef"],
            },
            posterior_samples_ref="posterior_samples_FLRW_tilt_S2.hdf5",
        )
        assert bundle["scope_label"] == "fiducial"
        assert bundle["production_allowed"] is True
        assert bundle["axis"]["production_allowed"] is True
        assert bundle["axis"]["source"] == "fiducial_posterior"
        assert bundle["mock_calibration"]["coverage_68"] == pytest.approx(0.68)
        assert bundle["posterior_samples_ref"].endswith(".hdf5")
        assert bundle["config_hash"] != ""
        assert bundle["python_version"] != ""
        # JSON artefact contract: no numpy arrays/scalars should remain.
        encoded = json.dumps(bundle)
        assert "fiducial_posterior_bundle_v1.json" in encoded

    def test_bundle_rejects_out_of_window_mock_coverage(self):
        with pytest.raises(ValueError, match="outside fiducial window"):
            fiducial_posterior_bundle(
                self._dynesty_result(),
                mock_report=self._mock_report(coverage_68=0.55),
            )

    def test_bundle_rejects_invalid_coverage_window(self):
        with pytest.raises(ValueError, match="coverage_window_68"):
            fiducial_posterior_bundle(
                self._dynesty_result(),
                mock_report=self._mock_report(),
                coverage_window_68=(0.80, 0.60),
            )
