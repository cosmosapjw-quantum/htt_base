"""Tests for ``mio.bridges.promoted_artifacts``."""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

import mio.bridges as bridges
from mio.bridges import promoted_artifacts
from mio.tests._overlay_fixtures import build_pending_overlay
from workspace.contracts.mio_certificate import MioCertificate


def _sample_bundle() -> dict:
    return {
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


def test_ingest_fiducial_bundle_extracts_promoted_summary():
    summary = promoted_artifacts.ingest_fiducial_posterior_bundle(_sample_bundle())
    assert summary.axis_l_deg == pytest.approx(264.0)
    assert summary.axis_b_deg == pytest.approx(48.0)
    assert summary.coverage_68 == pytest.approx(0.68)
    assert summary.posterior_samples_ref == "posterior_samples.h5"


def test_ingest_rejects_non_promoted_axis():
    payload = _sample_bundle()
    payload["axis"]["production_allowed"] = False
    with pytest.raises(ValueError, match="axis must be production_allowed=True"):
        promoted_artifacts.ingest_fiducial_posterior_bundle(payload)


def test_ingest_rejects_raw_posterior_payload():
    payload = _sample_bundle()
    payload["posterior_samples"] = {"raw": [1, 2, 3]}
    with pytest.raises(ValueError, match="raw posterior_samples"):
        promoted_artifacts.ingest_fiducial_posterior_bundle(payload)


def test_to_mio_certificate_preserves_g19_contract():
    summary = promoted_artifacts.ingest_fiducial_posterior_bundle(_sample_bundle())
    cert = promoted_artifacts.to_mio_certificate(summary)
    assert isinstance(cert, MioCertificate)
    for field in dataclasses.fields(cert):
        assert "posterior" not in field.name.lower()
    with pytest.raises(NotImplementedError):
        cert.as_posterior_bundle()


def test_emit_promoted_axis_ingestion_artefact_round_trip(tmp_path: Path):
    out = tmp_path / promoted_artifacts.ARTEFACT_FILENAME
    overlay = build_pending_overlay()
    payload = promoted_artifacts.emit_promoted_axis_ingestion_artefact(
        out,
        _sample_bundle(),
        tsc_overlay=overlay,
    )
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded == payload
    assert payload["artifact_name"] == promoted_artifacts.ARTEFACT_FILENAME
    assert payload["certificate"]["report_type"] == "promoted_axis_ingest"
    assert payload["certificate"]["tsc_overlay_ref"] == "tsc.overlay"


def test_package_exports_promoted_artifacts_module():
    assert hasattr(bridges, "promoted_artifacts")
    assert "promoted_artifacts" in bridges.__all__


def test_package_exports_promoted_artifact_entrypoints():
    assert bridges.ARTEFACT_FILENAME == promoted_artifacts.ARTEFACT_FILENAME
    assert bridges.PromotedAxisSummary is promoted_artifacts.PromotedAxisSummary
    assert (
        bridges.ingest_fiducial_posterior_bundle
        is promoted_artifacts.ingest_fiducial_posterior_bundle
    )
    assert bridges.to_mio_certificate is promoted_artifacts.to_mio_certificate
    assert (
        bridges.emit_promoted_axis_ingestion_artefact
        is promoted_artifacts.emit_promoted_axis_ingestion_artefact
    )
    assert "ARTEFACT_FILENAME" in bridges.__all__
    assert "PromotedAxisSummary" in bridges.__all__
    assert "ingest_fiducial_posterior_bundle" in bridges.__all__
    assert "to_mio_certificate" in bridges.__all__
    assert "emit_promoted_axis_ingestion_artefact" in bridges.__all__
