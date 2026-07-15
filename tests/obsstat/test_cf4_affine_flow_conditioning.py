"""Claim boundary for retained CF4++ affine reconstruction functionals."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


def test_affine_report_is_reconstruction_conditioned_not_observed_amplitude() -> None:
    report = json.loads(
        (REPO / "docs/generated/cf4_affine_flow_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert report["status"] == "RECONSTRUCTION_CONDITIONED_SYSTEMATICS_DIAGNOSTIC"
    assert report["artifact_mode"] == "paper_appendix_conditioned"
    assert report["allowed_use"] == "paper_appendix"
    assert report["analysis_mode"] == "reconstruction_conditioned_method_systematics"
    assert report["transfer_source"] == "external_proxy_cf4_wf_reconstruction"
    assert report["finding_state"]["finding_id"] == "C1-K5-MV-F1"
    assert report["finding_state"]["scientific_status"] == "OPEN"
    assert report["observational_amplitude_claim_allowed"] is False
    assert report["global_tilt_claim_allowed"] is False
    assert report["cosmological_inference_allowed"] is False
    assert report["radius_sweep"]  # numeric reconstruction functionals are retained


def test_affine_figure_manifest_keeps_the_same_open_finding_boundary() -> None:
    figure = REPO / "figures/observed_current/fig_observed_cf4_affine_flow.png"
    manifest = json.loads(
        (
            REPO
            / "figures/observed_current/fig_observed_cf4_affine_flow.manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["artifact_mode"] == "paper_appendix_conditioned"
    assert manifest["allowed_use"] == "paper_appendix"
    assert manifest["analysis_mode"] == "reconstruction_conditioned_method_systematics"
    assert manifest["artifact_sha256"] == "sha256:" + hashlib.sha256(
        figure.read_bytes()
    ).hexdigest()
    assert manifest["finding_state"]["scientific_status"] == "OPEN"
    assert manifest["observational_amplitude_claim_allowed"] is False
    assert manifest["global_tilt_claim_allowed"] is False
