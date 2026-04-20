"""COMMON-C tests — bulkflow_estimator (INDEPENDENT_TRACKS_PLAN §3.1)."""
from __future__ import annotations

import math

import numpy as np
import pytest

from common.bulkflow_estimator import (
    BulkFlowCatalogue,
    BulkFlowFit,
    ZoAResponseResult,
    baseline_selection_aware_artifact,
    bootstrap_covariance,
    bulk_flow_mask_ladder,
    diagnostic_plane_alignment_artifact,
    diagnostic_zoa_ladder_artifact,
    retention_vs_posterior_artifact,
    wls_bulk_flow,
)
from common.contracts import DynestyResult, MockCalibrationReport, SkySelectionConfig
from common.posterior_summary import fiducial_posterior_bundle
from common.sky_geometry import lb_to_unitvec


def _injected_catalogue(
    V_true: np.ndarray,
    *,
    n: int = 200,
    sigma_u: float = 30.0,
    seed: int = 0,
) -> BulkFlowCatalogue:
    """Build an isotropic catalogue whose radial velocities carry V_true + noise."""
    rng = np.random.default_rng(seed)
    cos_b = rng.uniform(-1.0, 1.0, size=n)
    b_deg = np.rad2deg(np.arcsin(cos_b))
    l_deg = rng.uniform(0.0, 360.0, size=n)
    n_hat = lb_to_unitvec(l_deg, b_deg)
    u_clean = n_hat @ V_true
    u = u_clean + rng.normal(0.0, sigma_u, size=n)
    sigma = np.full(n, sigma_u, dtype=float)
    return BulkFlowCatalogue(
        n_hat=n_hat,
        u=u,
        sigma=sigma,
        w_native=np.ones(n),
        w_selection=np.ones(n),
    )


def _fiducial_bundle_fixture() -> dict:
    rng = np.random.default_rng(123)
    center = np.array([220.0, 80.0, 40.0])
    samples = rng.normal(center, 20.0, size=(120, 3))
    result = DynestyResult(
        samples=samples,
        logwt=np.log(np.linspace(1.0, 3.0, samples.shape[0])),
        logz=9.5,
        ncall=77,
        config={"seed": 9, "sampler": "static"},
    )
    report = MockCalibrationReport(
        bias_amp=0.02,
        bias_direction_deg=1.5,
        coverage_68=0.69,
        credible_radius_deg=12.0,
        n_mock=80,
    )
    return fiducial_posterior_bundle(result, mock_report=report, nside_hpd=16)


# ---------------------------------------------------------------------------
# §1 — BulkFlowCatalogue invariants
# ---------------------------------------------------------------------------

class TestCatalogueInvariants:
    def test_accepts_clean_inputs(self):
        cat = _injected_catalogue(np.array([100.0, 0.0, 0.0]), n=10)
        assert cat.n_sources == 10

    def test_rejects_non_unit_nhat(self):
        bad = np.array([[1.0, 0.0, 0.0], [2.0, 0.0, 0.0]])
        with pytest.raises(ValueError, match="unit vectors"):
            BulkFlowCatalogue(
                n_hat=bad,
                u=np.zeros(2),
                sigma=np.ones(2),
                w_native=np.ones(2),
                w_selection=np.ones(2),
            )

    def test_rejects_negative_sigma(self):
        n_hat = np.eye(3)[:2]
        with pytest.raises(ValueError, match="sigma"):
            BulkFlowCatalogue(
                n_hat=n_hat,
                u=np.zeros(2),
                sigma=np.array([1.0, -1.0]),
                w_native=np.ones(2),
                w_selection=np.ones(2),
            )

    def test_rejects_shape_mismatch(self):
        with pytest.raises(ValueError, match="shape"):
            BulkFlowCatalogue(
                n_hat=np.eye(3)[:2],
                u=np.zeros(2),
                sigma=np.ones(3),
                w_native=np.ones(2),
                w_selection=np.ones(2),
            )


# ---------------------------------------------------------------------------
# §2 — wls_bulk_flow recovers injected V
# ---------------------------------------------------------------------------

class TestWLSRecovery:
    def test_recovers_injected_dipole(self):
        V_true = np.array([370.0, 0.0, 0.0])
        cat = _injected_catalogue(V_true, n=500, sigma_u=40.0, seed=123)
        fit = wls_bulk_flow(
            cat.n_hat,
            cat.u,
            sigma=cat.sigma,
            w_native=cat.w_native,
            w_selection=cat.w_selection,
        )
        np.testing.assert_allclose(fit.V_hat, V_true, atol=15.0)
        assert fit.n_sources == 500

    def test_covariance_is_symmetric_psd(self):
        V_true = np.array([0.0, 250.0, -100.0])
        cat = _injected_catalogue(V_true, n=300, sigma_u=50.0, seed=7)
        fit = wls_bulk_flow(
            cat.n_hat,
            cat.u,
            sigma=cat.sigma,
            w_native=cat.w_native,
            w_selection=cat.w_selection,
        )
        np.testing.assert_allclose(fit.cov, fit.cov.T, atol=1e-10)
        eigs = np.linalg.eigvalsh(fit.cov)
        assert eigs.min() >= -1e-12

    def test_requires_decomposition_when_w_absent(self):
        cat = _injected_catalogue(np.array([100.0, 0.0, 0.0]), n=20)
        with pytest.raises(ValueError, match="decomposition"):
            wls_bulk_flow(cat.n_hat, cat.u)

    def test_rejects_zero_weight_sum(self):
        cat = _injected_catalogue(np.array([100.0, 0.0, 0.0]), n=20)
        with pytest.raises(ValueError, match="sum to zero"):
            wls_bulk_flow(cat.n_hat, cat.u, w=np.zeros(cat.n_sources))


# ---------------------------------------------------------------------------
# §3 — REG-01: three-factor weight decomposition is logged
# ---------------------------------------------------------------------------

class TestWeightsDecompositionLogged:
    """REG-01: ``w_native × w_selection × w_measurement`` must all be logged.

    Downstream audits (ch08 §8.9) cross-check bulk-flow estimates against
    the specific per-factor weight histograms. Collapsing the decomposition
    into a single combined weight would make those audits undefined — and
    is precisely the regression REG-01 forbids.
    """

    def test_all_three_factors_present(self):
        V_true = np.array([250.0, -150.0, 80.0])
        cat = _injected_catalogue(V_true, n=120, seed=0)
        fit = wls_bulk_flow(
            cat.n_hat,
            cat.u,
            sigma=cat.sigma,
            w_native=cat.w_native,
            w_selection=cat.w_selection,
        )
        decomp = fit.weight_decomposition
        for key in ("w_native", "w_selection", "w_measurement"):
            assert key in decomp, (
                f"weight decomposition missing {key!r} — REG-01 violation"
            )
            assert decomp[key].shape == (cat.n_sources,)

    def test_measurement_weight_equals_inverse_variance(self):
        V_true = np.array([100.0, 0.0, 0.0])
        cat = _injected_catalogue(V_true, n=60, sigma_u=25.0, seed=1)
        fit = wls_bulk_flow(
            cat.n_hat,
            cat.u,
            sigma=cat.sigma,
            w_native=cat.w_native,
            w_selection=cat.w_selection,
        )
        expected = 1.0 / cat.sigma ** 2
        np.testing.assert_allclose(
            fit.weight_decomposition["w_measurement"], expected, rtol=1e-12
        )

    def test_decomposition_respects_sigma_star(self):
        V_true = np.array([100.0, 0.0, 0.0])
        cat = _injected_catalogue(V_true, n=30, sigma_u=30.0, seed=2)
        sigma_star = 50.0
        fit = wls_bulk_flow(
            cat.n_hat,
            cat.u,
            sigma=cat.sigma,
            w_native=cat.w_native,
            w_selection=cat.w_selection,
            sigma_star=sigma_star,
        )
        expected = 1.0 / (cat.sigma ** 2 + sigma_star ** 2)
        np.testing.assert_allclose(
            fit.weight_decomposition["w_measurement"], expected, rtol=1e-12
        )

    def test_decomposition_fallback_fills_ones_when_only_w_given(self):
        """When only a pre-combined ``w`` is supplied, the decomposition still
        exposes all three keys (native=1, selection=1, measurement=w)."""
        cat = _injected_catalogue(np.array([100.0, 0.0, 0.0]), n=20, seed=3)
        w = np.linspace(0.1, 1.0, cat.n_sources)
        fit = wls_bulk_flow(cat.n_hat, cat.u, w=w)
        decomp = fit.weight_decomposition
        for key in ("w_native", "w_selection", "w_measurement"):
            assert key in decomp

    def test_decomposition_entries_are_independent_copies(self):
        cat = _injected_catalogue(np.array([100.0, 0.0, 0.0]), n=15, seed=4)
        fit = wls_bulk_flow(
            cat.n_hat,
            cat.u,
            sigma=cat.sigma,
            w_native=cat.w_native,
            w_selection=cat.w_selection,
        )
        fit.weight_decomposition["w_native"][0] = -999.0
        assert cat.w_native[0] == 1.0, "mutating decomposition must not mutate input"


# ---------------------------------------------------------------------------
# §4 — Mask ladder
# ---------------------------------------------------------------------------

class TestBulkFlowMaskLadder:
    def test_ladder_yields_per_cut_fits(self):
        V_true = np.array([200.0, 0.0, 0.0])
        cat = _injected_catalogue(V_true, n=400, seed=11)
        res = bulk_flow_mask_ladder(
            cat, np.array([0.0, 5.0, 10.0, 20.0, 30.0]), nside=16,
        )
        assert isinstance(res, ZoAResponseResult)
        assert res.bcut_deg.shape == (5,)
        assert res.V_hat.shape == (5, 3)
        assert res.retention_fraction.shape == (5,)
        # bcut=0 keeps every pixel
        assert math.isclose(res.retention_fraction[0], 1.0, abs_tol=1e-12)
        # retention is monotonic non-increasing in bcut
        diffs = np.diff(res.retention_fraction)
        assert np.all(diffs <= 1e-12)

    def test_aggressive_cut_produces_nan_fit(self):
        V_true = np.array([100.0, 0.0, 0.0])
        rng = np.random.default_rng(33)
        n = 20
        # Force every source into the galactic plane.
        l_deg = rng.uniform(0.0, 360.0, size=n)
        b_deg = rng.uniform(-2.0, 2.0, size=n)
        n_hat = lb_to_unitvec(l_deg, b_deg)
        u = n_hat @ V_true + rng.normal(0.0, 10.0, size=n)
        cat = BulkFlowCatalogue(
            n_hat=n_hat,
            u=u,
            sigma=np.full(n, 10.0),
            w_native=np.ones(n),
            w_selection=np.ones(n),
        )
        res = bulk_flow_mask_ladder(cat, np.array([50.0]), nside=16)
        assert np.all(np.isnan(res.V_hat))
        assert res.fits[0].diagnostics.get("underdetermined") is True


# ---------------------------------------------------------------------------
# §5 — Bootstrap covariance
# ---------------------------------------------------------------------------

class TestBootstrapCovariance:
    def test_bootstrap_covariance_symmetric_psd(self):
        V_true = np.array([200.0, 100.0, -50.0])
        cat = _injected_catalogue(V_true, n=150, seed=5)
        out = bootstrap_covariance(cat, n_boot=64, rng=np.random.default_rng(99))
        cov = out["cov"]
        np.testing.assert_allclose(cov, cov.T, atol=1e-10)
        eigs = np.linalg.eigvalsh(cov)
        assert eigs.min() >= -1e-8
        assert out["V_hat_mean"].shape == (3,)
        assert out["V_boot"].shape == (out["n_boot"], 3)

    def test_bootstrap_centers_on_injected_V(self):
        V_true = np.array([300.0, 0.0, 0.0])
        cat = _injected_catalogue(V_true, n=300, seed=6)
        out = bootstrap_covariance(cat, n_boot=128, rng=np.random.default_rng(7))
        np.testing.assert_allclose(out["V_hat_mean"], V_true, atol=20.0)


# ---------------------------------------------------------------------------
# §6 — JSON artifacts (Mode 0 / Mode 1)
# ---------------------------------------------------------------------------

class TestDirectionalArtifacts:
    def test_diagnostic_zoa_ladder_artifact_is_json_ready(self):
        cat = _injected_catalogue(np.array([220.0, -40.0, 30.0]), n=300, seed=9)
        artifact = diagnostic_zoa_ladder_artifact(
            cat,
            metadata={"git_commit": "abc123"},
        )
        assert artifact["artifact_name"] == "diag_zoa_ladder_v1.json"
        assert artifact["scope_label"] == "diagnostic"
        assert artifact["production_allowed"] is False
        assert len(artifact["bcut_deg"]) == 7
        assert len(artifact["axis_instability_deg"]) == 7
        assert artifact["config_hash"] != ""
        import json

        json.dumps(artifact)

    def test_baseline_selection_aware_artifact_reports_mode_gate(self):
        cat = _injected_catalogue(np.array([260.0, 50.0, -30.0]), n=350, seed=10)
        cfg = SkySelectionConfig(
            zoa_half_angle_deg=10.0,
            min_retention_fraction=0.3,
            nside=16,
            smooth_sigma_pix=1.0,
        )
        baseline = baseline_selection_aware_artifact(
            cat,
            cfg,
            n_boot=48,
            metadata={"random_seed": 123},
        )
        assert baseline["artifact_name"] == "baseline_selection_aware_v1.json"
        assert baseline["scope_label"] == "baseline"
        assert baseline["production_allowed"] is False
        assert baseline["retention_fraction"] >= 0.3
        assert baseline["mode0_to_mode1_gate_passed"] is True
        assert baseline["bootstrap"]["n_boot"] > 10
        assert baseline["axis"]["selection_mode"] == "angular_completeness"

    def test_baseline_gate_fails_when_retention_floor_not_met(self):
        cat = _injected_catalogue(np.array([180.0, 0.0, 0.0]), n=250, seed=11)
        cfg = SkySelectionConfig(
            zoa_half_angle_deg=30.0,
            min_retention_fraction=0.95,
            nside=16,
            smooth_sigma_pix=1.0,
        )
        baseline = baseline_selection_aware_artifact(
            cat,
            cfg,
            n_boot=32,
        )
        assert baseline["retention_fraction"] < cfg.min_retention_fraction
        assert baseline["mode0_to_mode1_gate_passed"] is False

    def test_plane_alignment_artifact_summarises_axis_path(self):
        cat = _injected_catalogue(np.array([190.0, 30.0, -15.0]), n=320, seed=12)
        diagnostic = diagnostic_zoa_ladder_artifact(cat)
        alignment = diagnostic_plane_alignment_artifact(
            diagnostic,
            metadata={"git_commit": "def456"},
        )
        assert alignment["artifact_name"] == "diag_plane_alignment_v1.json"
        assert alignment["scope_label"] == "diagnostic"
        assert alignment["production_allowed"] is False
        assert alignment["n_valid_axes"] >= 1
        assert 0.0 <= alignment["resultant_R"] <= 1.0
        assert len(alignment["step_drift_deg"]) == len(alignment["bcut_deg"])
        import json

        json.dumps(alignment)

    def test_retention_vs_posterior_artifact_compares_mode0_and_mode2(self):
        cat = _injected_catalogue(np.array([220.0, -20.0, 35.0]), n=280, seed=13)
        diagnostic = diagnostic_zoa_ladder_artifact(cat)
        bundle = _fiducial_bundle_fixture()
        comparison = retention_vs_posterior_artifact(diagnostic, bundle)
        assert comparison["artifact_name"] == "retention_vs_posterior_v1.json"
        assert comparison["scope_label"] == "diagnostic_vs_fiducial"
        assert comparison["production_allowed"] is False
        assert len(comparison["posterior_shift_deg"]) == len(comparison["bcut_deg"])
        assert comparison["credible_cone_95_deg"] >= comparison["credible_cone_68_deg"]
        assert len(comparison["within_68_cone"]) == len(comparison["bcut_deg"])
        import json

        json.dumps(comparison)
