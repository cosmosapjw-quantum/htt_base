"""SK-07M VER2 manifest/readiness regression tests for MIO."""
from __future__ import annotations

import numpy as np

from mio.bridges import promoted_artifacts
from mio.coherence.directional import STANDARD_PROBES, resultant_vector
from mio.coherence.directional import to_mio_certificate as directional_to_mio_certificate
from mio.decomposition.evidence_anatomy import (
    summarize_evidence_anatomy,
    to_mio_certificate as evidence_to_mio_certificate,
)
from mio.diagnostics.predictive_residuals import (
    ResidualChannelSlice,
    build_predictive_residual_atlas,
    to_mio_certificate as residuals_to_mio_certificate,
)
from mio.extraction.hj01_shear import ShearExtractorReport
from mio.extraction.hj01_shear import to_mio_certificate as shear_to_mio_certificate
from mio.interface.manifest import MioPrerequisites, assess_mio_readiness
from mio.interface.mio_certificate import build_mio_certificate, certificate_to_payload
from mio.tension.flrw_tension import (
    evaluate_flrw_tension,
    to_mio_certificate as flrw_to_mio_certificate,
)


def test_build_certificate_can_auto_materialize_ver2_manifest():
    readiness = assess_mio_readiness(
        MioPrerequisites(
            requires_covariance=True,
            has_covariance=False,
            eligible_for_production=True,
        )
    )
    cert = build_mio_certificate(
        report_type="directional_coherence",
        probe_name="CMB",
        channel="dipole",
        departure_variables={"resultant_R": 0.9},
        adequacy_indicators={"isotropy_p_lt_0p01": True},
        consistency_metrics={"chi2_per_dof": 1.0},
        domain_caveats=["masked_sky_partial"],
        reduction_status="diagnostic-only",
        generated_by="mio.test",
        input_data_hashes=["h1"],
        readiness=readiness,
        artifact_id="mio.test.certificate",
        artifact_path="artifacts/mio/test.json",
    )
    assert cert.manifest is not None
    assert cert.manifest.owner == "MIO"
    assert cert.manifest.production_status == "blocked_missing_covariance"
    payload = certificate_to_payload(cert)
    assert payload["manifest"]["production_status"] == "blocked_missing_covariance"


def test_directional_certificate_blocks_without_covariance_and_nulls():
    cert = directional_to_mio_certificate(
        STANDARD_PROBES,
        p_iso=0.02,
        resultant=resultant_vector(STANDARD_PROBES),
    )
    assert cert.manifest is not None
    assert cert.manifest.production_status == "blocked_missing_covariance"
    assert "covariance_prerequisite_missing" in cert.domain_caveats


def test_directional_certificate_can_reach_production_candidate():
    cert = directional_to_mio_certificate(
        STANDARD_PROBES,
        p_iso=0.02,
        resultant=resultant_vector(STANDARD_PROBES),
        has_covariance=True,
        has_null_mocks=True,
        sky_support_status="complete",
    )
    assert cert.manifest is not None
    assert cert.manifest.production_status == "production_candidate"
    assert "public_grade=production-grade" in cert.domain_caveats


def test_shear_certificate_marks_missing_covariance():
    report = ShearExtractorReport(
        ell=np.arange(2, 5),
        sigma2_per_ell=np.array([0.1, 0.2, 0.15]),
        sigma_sigma2_per_ell=np.array([0.05, 0.05, 0.05]),
        sigma2_best=0.15,
        sigma2_best_uncertainty=0.03,
        chi2_independence=1.0,
        dof_independence=2,
        p_value_independence=0.6,
        dropped_ells=(),
        bianchi_type="I",
        atlas_name="synthetic",
    )
    cert = shear_to_mio_certificate(report)
    assert cert.manifest is not None
    assert cert.manifest.production_status == "blocked_missing_covariance"
    assert "atlas_ready" in cert.manifest.passed_gates
    assert "covariance_ready" in cert.manifest.failed_gates


def test_flrw_tension_marks_missing_null_mock_calibration_by_default():
    report = evaluate_flrw_tension(
        {"T_directional": 1.2},
        {"T_directional": [0.1, 0.2, 1.0, 1.5]},
    )
    cert = flrw_to_mio_certificate(report)
    assert cert.manifest is not None
    assert cert.manifest.production_status == "blocked_missing_null_mocks"
    assert "null_mock_prerequisite_missing" in cert.domain_caveats


def test_evidence_anatomy_stays_diagnostic_only_by_design():
    report = summarize_evidence_anatomy({"cmb": 1.0, "cf4": 0.3})
    cert = evidence_to_mio_certificate(report)
    assert cert.manifest is not None
    assert cert.manifest.production_status == "diagnostic_only"
    assert "public_grade=diagnostic-only" in cert.domain_caveats


def test_predictive_residuals_block_without_atlas_or_covariance():
    atlas = build_predictive_residual_atlas(
        [
            ResidualChannelSlice(
                model_label="FLRW",
                channel="TT",
                ell_min=2,
                ell_max=10,
                rms_residual=0.2,
                max_abs_residual=0.5,
                n_modes=9,
            )
        ]
    )
    cert = residuals_to_mio_certificate(atlas)
    assert cert.manifest is not None
    assert cert.manifest.production_status == "blocked_missing_atlas"


def test_predictive_residuals_can_reach_production_candidate():
    atlas = build_predictive_residual_atlas(
        [
            ResidualChannelSlice(
                model_label="FLRW",
                channel="TT",
                ell_min=2,
                ell_max=10,
                rms_residual=0.2,
                max_abs_residual=0.5,
                n_modes=9,
            )
        ],
        atlas_ref="atlas:001",
        covariance_ref="cov:001",
    )
    cert = residuals_to_mio_certificate(atlas)
    assert cert.manifest is not None
    assert cert.manifest.production_status == "production_candidate"


def test_promoted_axis_bridge_stays_diagnostic_only():
    summary = promoted_artifacts.ingest_fiducial_posterior_bundle(
        {
            "artifact_name": "fiducial_posterior_bundle_v1.json",
            "config_hash": "bundle-hash",
            "production_allowed": True,
            "posterior_samples_ref": "posterior_samples.h5",
            "mock_calibration_ref": "mock_report.json",
            "logz": 12.3,
            "ncall": 456,
            "axis": {
                "l_deg": 264.0,
                "b_deg": 48.0,
                "label": "posterior_mean",
                "source": "fiducial_posterior",
                "weight_mode": "dynesty_logwt",
                "selection_mode": "mock_calibrated",
                "production_allowed": True,
                "provenance_hash": "axis-hash",
            },
            "posterior_summary": {
                "credible_cone_68": {
                    "center_l_deg": 264.0,
                    "center_b_deg": 48.0,
                    "radius_deg": 12.5,
                    "level": 0.68,
                }
            },
            "mock_calibration": {
                "coverage_68": 0.68,
                "credible_radius_deg": 12.5,
                "passed_window": True,
            },
        }
    )
    cert = promoted_artifacts.to_mio_certificate(summary)
    assert cert.manifest is not None
    assert cert.manifest.production_status == "diagnostic_only"
