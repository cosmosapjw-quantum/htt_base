"""Regression tests for matched_complexity_report_v1.json."""
from __future__ import annotations

import json

import pytest

from htt.infer import matched_complexity_report_artifact


def test_matched_complexity_report_artifact_is_json_ready():
    artifact = matched_complexity_report_artifact(
        metadata={"git_commit": "abc123"},
    )
    assert artifact["artifact_name"] == "matched_complexity_report_v1.json"
    assert artifact["scope_label"] == "report"
    assert artifact["production_allowed"] is False
    assert artifact["summary"]["overall_pass"] is True
    assert [c["code"] for c in artifact["controls"]] == ["C0", "C1", "C2", "C3"]
    assert artifact["controls"][0]["matched_complexity_passed"] is None
    assert artifact["controls"][1]["reference_control"] is True
    assert artifact["controls"][2]["matched_complexity_passed"] is True
    assert artifact["controls"][3]["matched_complexity_passed"] is True
    assert artifact["config_hash"] != ""
    json.dumps(artifact)


def test_matched_complexity_report_hash_is_deterministic_for_same_payload():
    a1 = matched_complexity_report_artifact(metadata={"git_commit": "same"})
    a2 = matched_complexity_report_artifact(metadata={"git_commit": "same"})
    a3 = matched_complexity_report_artifact(metadata={"git_commit": "other"})
    assert a1["config_hash"] == a2["config_hash"]
    assert a1["config_hash"] != a3["config_hash"]


def test_matched_complexity_report_allows_subset_request():
    artifact = matched_complexity_report_artifact(control_codes=["C2", "C3"])
    assert artifact["controls_requested"] == ["C2", "C3"]
    assert [c["code"] for c in artifact["controls"]] == ["C2", "C3"]
    assert artifact["controls_audited"] == ["C2", "C3"]


def test_matched_complexity_report_rejects_unknown_control():
    with pytest.raises(KeyError, match="Unknown control code"):
        matched_complexity_report_artifact(control_codes=["C1", "CX"])
