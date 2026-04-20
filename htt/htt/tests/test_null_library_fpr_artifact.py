"""Regression tests for null_library_fpr_v1.json."""
from __future__ import annotations

import json

import pytest

from htt.core.analysis_extended import EVIDENCE_MODEL_TAGS
from htt.nulls.runner import ALL_FAMILIES, null_library_fpr_report_artifact


def _model_results():
    families = [fam.name for fam in ALL_FAMILIES]
    out = {}
    for m_idx, tag in enumerate(EVIDENCE_MODEL_TAGS):
        fam_payload = {}
        for f_idx, family in enumerate(families):
            fam_payload[family] = {
                "n_datasets": 100,
                "fp_rate_Pi005": 0.01 * (f_idx + 1) + 0.001 * m_idx,
                "fp_rate_lnB5": 0.02 * (f_idx + 1) + 0.001 * m_idx,
                "lnB_median": -2.0 + 0.1 * f_idx,
                "lnB_std": 0.5 + 0.05 * f_idx,
                "beta_median_mean": 1e-4 * (m_idx + 1),
            }
        out[tag] = {
            "_meta": {"n_families": 5},
            "families": fam_payload,
            "union_fp_Pi005": 0.05 + 0.001 * m_idx,
            "target": {"individual_fp_max": 0.05, "union_fp_max": 0.01},
        }
    return out


def test_null_library_fpr_artifact_is_json_ready():
    artifact = null_library_fpr_report_artifact(
        _model_results(),
        metadata={"git_commit": "abc123"},
    )
    assert artifact["artifact_name"] == "null_library_fpr_v1.json"
    assert artifact["scope_label"] == "report"
    assert artifact["production_allowed"] is False
    assert artifact["shape"]["n_families"] == 5
    assert artifact["shape"]["n_models"] == 15
    assert artifact["model_order"] == EVIDENCE_MODEL_TAGS
    assert len(artifact["family_order"]) == 5
    assert len(artifact["union_fp_Pi005_by_model"]) == 15
    assert artifact["config_hash"] != ""
    json.dumps(artifact)


def test_null_library_fpr_hash_is_deterministic_for_same_payload():
    a1 = null_library_fpr_report_artifact(_model_results())
    a2 = null_library_fpr_report_artifact(_model_results())
    a3 = null_library_fpr_report_artifact(
        _model_results(),
        metadata={"git_commit": "other"},
    )
    assert a1["config_hash"] == a2["config_hash"]
    assert a1["config_hash"] != a3["config_hash"]


def test_null_library_fpr_artifact_rejects_missing_family():
    bad = _model_results()
    first = EVIDENCE_MODEL_TAGS[0]
    family = next(iter(bad[first]["families"]))
    del bad[first]["families"][family]
    with pytest.raises(KeyError, match="missing family result"):
        null_library_fpr_report_artifact(bad)
