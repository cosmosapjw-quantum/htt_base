"""Regression tests for advanced-diagnostics report artifacts."""
from __future__ import annotations

import json

from htt.core.advanced_diagnostics import (
    cross_channel_coherence_report_artifact,
    loocv_report_artifact,
    posterior_predictive_report_artifact,
    redshift_tomography_report_artifact,
)


def _ablation_fixture() -> dict:
    return {
        "channels": {
            "no_CF4": {"lnB": 21.1},
            "no_CatWISE": {"lnB": 24.8},
        }
    }


def test_cross_channel_coherence_artifact_is_json_ready():
    artifact = cross_channel_coherence_report_artifact(
        metadata={"git_commit": "abc123"},
    )
    assert artifact["artifact_name"] == "cross_channel_coherence_v1.json"
    assert artifact["scope_label"] == "report"
    assert artifact["production_allowed"] is False
    assert len(artifact["channel_order"]) == 3
    assert len(artifact["pairwise_tension_sigma_matrix"]) == 3
    assert artifact["config_hash"] != ""
    json.dumps(artifact)


def test_posterior_predictive_artifact_is_json_ready():
    artifact = posterior_predictive_report_artifact(
        model_name="FLRW_tilt",
        beta_med=1.36e-3,
        metadata={"git_commit": "abc123"},
    )
    assert artifact["artifact_name"] == "posterior_predictive_v1.json"
    assert artifact["scope_label"] == "report"
    assert artifact["production_allowed"] is False
    assert artifact["model"] == "FLRW_tilt"
    assert "beta_CF4" in artifact["observables"]
    assert "beta_CF4" in artifact["pulls"]
    json.dumps(artifact)


def test_loocv_report_artifact_is_json_ready():
    artifact = loocv_report_artifact(
        _ablation_fixture(),
        lnB_full=26.33,
        metadata={"git_commit": "abc123"},
    )
    assert artifact["artifact_name"] == "loocv_report_v1.json"
    assert artifact["scope_label"] == "report"
    assert artifact["production_allowed"] is False
    assert artifact["n_dropped_channels"] == 2
    assert artifact["most_sensitive_channel"]["delta_lnB"] >= 0.0
    json.dumps(artifact)


def test_loocv_report_hash_changes_with_lnB_full():
    a1 = loocv_report_artifact(_ablation_fixture(), lnB_full=26.33)
    a2 = loocv_report_artifact(_ablation_fixture(), lnB_full=26.33)
    a3 = loocv_report_artifact(_ablation_fixture(), lnB_full=12.0)
    assert a1["config_hash"] == a2["config_hash"]
    assert a1["config_hash"] != a3["config_hash"]


def test_redshift_tomography_artifact_is_json_ready():
    artifact = redshift_tomography_report_artifact(
        metadata={"git_commit": "abc123"},
    )
    assert artifact["artifact_name"] == "redshift_tomography_v1.json"
    assert artifact["scope_label"] == "report"
    assert artifact["production_allowed"] is False
    assert artifact["n_bins"] == len(artifact["bins"])
    assert artifact["n_bins"] >= 3
    json.dumps(artifact)
