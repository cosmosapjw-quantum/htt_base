"""PR-154 card: concrete host analysis and covariance non-identification."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[2]
SPEC = REPO / "docs/research_program/long_horizon_rescue/pr154_spec.yaml"
GENERATED = REPO / "docs/generated"


def _load(name: str) -> dict:
    return json.loads((GENERATED / name).read_text(encoding="utf-8"))


def test_observed_families_are_separate_concrete_numerically_certified_results() -> None:
    cchp = _load("pr154_cchp_observed.json")
    shoes = _load("pr154_shoes_observed.json")
    assert (cchp["dataset"], cchp["n_hosts"]) == ("cchp_trgb_jagb", 7)
    assert (shoes["dataset"], shoes["n_hosts"]) == ("shoes_jwst_hst", 13)
    assert cchp["dataset"] != shoes["dataset"]
    assert cchp["contrast"] != shoes["contrast"]
    for payload in (cchp, shoes):
        assert payload["numerical_status"] == "PASS"
        assert payload["terminal_classification"] == "TOTAL_UNCERTAINTY_NOT_IDENTIFIED"
        assert payload["independence_sensitivity"]["primary_total_uncertainty"] is False
        assert payload["independence_sensitivity"]["gaussian"]["numerical_status"] == "PASS"
        assert all(row["numerical_status"] == "PASS" for row in
                   payload["independence_sensitivity"]["student_t"].values())


def test_covariance_envelope_and_cf4_scenarios_do_not_promote_missing_inputs() -> None:
    covariance = _load("pr154_covariance_envelope.json")
    assert covariance["source_families_pooled"] is False
    assert covariance["total_uncertainty_identified"] is False
    assert all(
        row["structured_covariance_scan"]["numerical_status"] == "PASS"
        for row in covariance["families"].values()
    )
    cf4 = _load("pr154_cf4_scenarios.json")
    assert cf4["observed_crossmatch_receipt"][
        "independently_verified_identity_count"] == 0
    assert cf4["observed_crossmatch_receipt"]["nonzero_observed_overlap_used"] is False
    for family in cf4["families"].values():
        counts = Counter(row["classification"] for row in family["cells"])
        assert counts["MATERIAL_GAIN_SCENARIO"] == 0
        assert all(row["observed_result"] is False for row in family["cells"])
        assert all(
            row["classification"] != "MATERIAL_GAIN_SCENARIO"
            for row in family["cells"] if row["nuisance_slope_mag"] == 0.0
        )


def test_manifest_hashes_outputs_and_common_owns_semantic_gates() -> None:
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    manifest = _load("pr154_artifact_manifest.json")
    mutation = _load("pr154_mutation_report.json")
    assert manifest["scientific_result"] == "TOTAL_UNCERTAINTY_NOT_IDENTIFIED"
    assert manifest["calibration_status"] == "PASS"
    assert manifest["owner"] == "COMMON"
    assert manifest["scientific_owner"] == "HTT"
    assert mutation["artifact_metadata"]["owner"] == "COMMON"
    assert mutation["artifact_metadata"]["scientific_owner"] == "HTT"
    assert mutation["surviving_mutation_count"] == 0
    for relative, expected in manifest["artifacts"].items():
        assert hashlib.sha256((REPO / relative).read_bytes()).hexdigest() == expected
    assert spec["data_scope"]["pr4_commands_run_required"] == 0
    assert manifest["planck_pr3_raw_deleted"] is False
