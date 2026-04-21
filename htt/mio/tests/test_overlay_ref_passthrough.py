"""Emitter-level regressions for ref-only TSC overlay passthrough."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from mio.bridges import promoted_artifacts
from mio.coherence.directional import (
    ARTEFACT_FILENAME as DIRECTIONAL_ARTEFACT_FILENAME,
    STANDARD_PROBES,
    emit_directional_coherence_artefact,
)
from mio.diagnostics.predictive_residuals import (
    ARTEFACT_FILENAME as RESIDUAL_ARTEFACT_FILENAME,
    ResidualChannelSlice,
    emit_predictive_residuals_artefact,
)
from mio.tension import ARTEFACT_FILENAME as TENSION_ARTEFACT_FILENAME
from mio.tension import emit_flrw_tension_artefact


def _assert_ref_only_overlay_payload(payload: dict, *, expected_ref: str) -> None:
    certificate = payload["certificate"]
    assert certificate["tsc_overlay_ref"] == expected_ref
    assert certificate["adequacy_indicators"]["tsc_overlay_attached"] is True
    assert "tsc_overlay_diagnostic_only" not in certificate["adequacy_indicators"]
    assert "tsc_overlay_diagnostic_only" not in certificate["domain_caveats"]


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


def test_directional_emitter_preserves_ref_only_overlay(tmp_path: Path):
    out = tmp_path / DIRECTIONAL_ARTEFACT_FILENAME
    payload = emit_directional_coherence_artefact(
        out,
        probes=STANDARD_PROBES,
        n_mock=200,
        rng=np.random.default_rng(seed=11),
        tsc_overlay_ref="tsc.overlay.external",
    )
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded == payload
    _assert_ref_only_overlay_payload(payload, expected_ref="tsc.overlay.external")


def test_predictive_residual_emitter_preserves_ref_only_overlay(tmp_path: Path):
    out = tmp_path / RESIDUAL_ARTEFACT_FILENAME
    payload = emit_predictive_residuals_artefact(
        out,
        (
            ResidualChannelSlice(
                model_label="FLRW_tilt",
                channel="TT",
                ell_min=2,
                ell_max=5,
                rms_residual=0.1,
                max_abs_residual=0.2,
                n_modes=4,
            ),
        ),
        atlas_ref="bass.atlas_lite",
        covariance_ref="cov:001",
        tsc_overlay_ref="tsc.overlay.external",
    )
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded == payload
    _assert_ref_only_overlay_payload(payload, expected_ref="tsc.overlay.external")


def test_flrw_tension_emitter_preserves_ref_only_overlay(tmp_path: Path):
    out = tmp_path / TENSION_ARTEFACT_FILENAME
    payload = emit_flrw_tension_artefact(
        out,
        {"T_directional": 2.5, "T_biposh": 0.3},
        {
            "T_directional": [0.2, 0.4, 0.5, 0.7],
            "T_biposh": [0.1, 0.2, 0.4, 0.6],
        },
        tsc_overlay_ref="tsc.overlay.external",
    )
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded == payload
    _assert_ref_only_overlay_payload(payload, expected_ref="tsc.overlay.external")


def test_promoted_bridge_preserves_ref_only_overlay(tmp_path: Path):
    out = tmp_path / promoted_artifacts.ARTEFACT_FILENAME
    payload = promoted_artifacts.emit_promoted_axis_ingestion_artefact(
        out,
        _sample_bundle(),
        tsc_overlay_ref="tsc.overlay.external",
    )
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded == payload
    _assert_ref_only_overlay_payload(payload, expected_ref="tsc.overlay.external")
