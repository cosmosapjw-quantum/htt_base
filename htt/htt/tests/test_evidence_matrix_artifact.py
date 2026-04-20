"""Regression tests for 15model_evidence_matrix_v1.json."""
from __future__ import annotations

import json

import pytest

from htt.core.analysis_extended import (
    EVIDENCE_MODEL_TAGS,
    evidence_matrix_report_artifact,
)


def _scenario_results():
    out = {}
    scenarios = ["S1", "S2a", "S2b", "S2c", "S3"]
    for s_idx, scenario in enumerate(scenarios):
        rows = []
        for m_idx, tag in enumerate(EVIDENCE_MODEL_TAGS):
            rows.append({
                "tag": tag,
                "lnB": 25.0 - 0.75 * m_idx + 0.10 * s_idx,
                "err": 0.05 + 0.01 * m_idx,
            })
        out[scenario] = rows
    return out


def test_evidence_matrix_artifact_is_json_ready():
    artifact = evidence_matrix_report_artifact(
        _scenario_results(),
        metadata={"git_commit": "abc123"},
    )
    assert artifact["artifact_name"] == "15model_evidence_matrix_v1.json"
    assert artifact["scope_label"] == "report"
    assert artifact["production_allowed"] is False
    assert artifact["shape"]["n_models"] == 15
    assert artifact["shape"]["n_scenarios"] == 5
    assert artifact["model_order"] == EVIDENCE_MODEL_TAGS
    assert artifact["top_model_by_scenario"][0]["tag"] == "FLRW_tilt"
    assert artifact["config_hash"] != ""
    json.dumps(artifact)


def test_evidence_matrix_hash_is_deterministic_for_same_payload():
    a1 = evidence_matrix_report_artifact(_scenario_results())
    a2 = evidence_matrix_report_artifact(_scenario_results())
    a3 = evidence_matrix_report_artifact(
        _scenario_results(),
        metadata={"git_commit": "other"},
    )
    assert a1["config_hash"] == a2["config_hash"]
    assert a1["config_hash"] != a3["config_hash"]


def test_evidence_matrix_artifact_allows_scenario_subset():
    artifact = evidence_matrix_report_artifact(
        _scenario_results(),
        scenario_order=["S1", "S3"],
    )
    assert artifact["shape"]["n_scenarios"] == 2
    assert artifact["scenario_order"] == ["S1", "S3"]


def test_evidence_matrix_artifact_rejects_missing_model():
    bad = _scenario_results()
    bad["S2a"] = bad["S2a"][:-1]
    with pytest.raises(KeyError, match="missing model result"):
        evidence_matrix_report_artifact(bad)
