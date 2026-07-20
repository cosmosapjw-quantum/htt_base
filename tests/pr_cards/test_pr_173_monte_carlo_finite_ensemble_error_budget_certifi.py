from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest
import yaml

from obsstat.finite_ensemble import (
    INPUT_AVAILABLE,
    INPUT_PARTIAL_FORBIDDEN,
    LINEAGE_CERTIFIED,
    LINEAGE_INVALID,
    LINEAGE_MISSING,
    RESOLVED,
    UNRESOLVED,
    FiniteEnsembleError,
    certificate_errors,
    not_certifiable_certificate,
    not_evaluated_certificate,
    rank_certificate,
    semantic_digest,
)
from scripts.codex_harness.run_pr173_finite_ensemble import validate_report


REPO = Path(__file__).resolve().parents[2]
SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr173_spec.yaml"
REPORT_PATH = REPO / "docs/generated/pr173_error_budget_report.json"


def _json(relative: str) -> dict:
    value = json.loads((REPO / relative).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _spec() -> dict:
    value = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _report() -> dict:
    return _json("docs/generated/pr173_error_budget_report.json")


def _reseal(payload: dict) -> dict:
    payload["semantic_digest"] = semantic_digest(payload)
    return payload


def test_result_pack_is_reproducible_and_byte_current() -> None:
    completed = subprocess.run(
        [
            str(REPO / "venv/bin/python"),
            "-B",
            str(REPO / "scripts/codex_harness/run_pr173_finite_ensemble.py"),
            "--check",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
        env={
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": str(REPO / "htt"),
            "PYTHONHASHSEED": "0",
            "OPENBLAS_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
        },
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    receipt = json.loads(completed.stdout)
    assert receipt["ok"] is True
    assert receipt["summary"] == {
        "all_routes_typed": True,
        "not_certifiable_count": 5,
        "not_evaluated_count": 1,
        "resolved_count": 0,
        "target_count": 7,
        "unresolved_count": 1,
    }


def test_planck_rank_is_exact_and_unresolved_at_registered_boundary() -> None:
    target = _report()["targets"][0]
    certificate = target["certificate"]
    assert target["target_id"] == "PR173-PLANCK-RANK"
    assert target["input_availability_status"] == INPUT_AVAILABLE
    assert target["replicate_lineage_status"] == LINEAGE_CERTIFIED
    assert target["numerical_resolution_status"] == UNRESOLVED
    assert certificate["rank_fraction"] == "39/1000"
    assert certificate["finite_resolution_fraction"] == "1/1000"
    assert certificate["uncertainty_method"] == "whole_cluster_bootstrap_plus_one_rank"
    assert certificate["uncertainty_interval"][0] < 0.05 < certificate["uncertainty_interval"][1]
    assert certificate["guard_interval"][0] < 0.05 < certificate["guard_interval"][1]
    assert certificate["boundary"] == 0.05
    assert certificate["confidence_level"] == 0.95
    assert certificate["gaussian_sigma_emitted"] is False


def test_availability_lineage_and_numerical_axes_do_not_collapse() -> None:
    by_id = {row["target_id"]: row for row in _report()["targets"]}
    assert by_id["PR173-ACT-RANK"]["reported_rank_identity"]["rank_fraction"] == "146/401"
    for target_id in ("PR173-ACT-RANK", "PR173-ACT-BANDPOWER-MEAN"):
        row = by_id[target_id]
        assert row["input_availability_status"] == INPUT_AVAILABLE
        assert row["replicate_lineage_status"] == LINEAGE_INVALID
        assert row["numerical_resolution_status"] is None
    for target_id in (
        "PR173-MIO-PI",
        "PR173-CF4-INJECTION-RMSE",
        "PR173-CF4-FSIGMA8",
    ):
        row = by_id[target_id]
        assert row["input_availability_status"] == INPUT_AVAILABLE
        assert row["replicate_lineage_status"] == LINEAGE_MISSING
        assert row["numerical_resolution_status"] is None
    desi = by_id["PR173-DESI-RANK"]
    assert desi["input_availability_status"] == INPUT_PARTIAL_FORBIDDEN
    assert desi["replicate_lineage_status"] is None
    assert desi["numerical_resolution_status"] is None
    assert desi["partial_mock_count_used"] == 0


def test_mock_dispersion_and_aggregate_rmse_are_not_mc_error_budgets() -> None:
    by_id = {row["target_id"]: row for row in _report()["targets"]}
    fsigma = by_id["PR173-CF4-FSIGMA8"]
    assert fsigma["reported_values"]["mock_sigma_role"] == (
        "scientific_mock_dispersion_not_MC_standard_error"
    )
    assert fsigma["certificate"]["mc_se"] is None
    injection = by_id["PR173-CF4-INJECTION-RMSE"]
    assert injection["reported_values"]["aggregate_only"] is True
    assert injection["certificate"]["mc_se"] is None


def test_source_receipts_hash_small_metadata_but_not_raw_or_support_payloads() -> None:
    report = _report()
    assert report["small_metadata_hashing_performed"] is True
    assert report["raw_payload_hashing_performed"] is False
    for receipt in report["source_authority_receipts"]:
        assert receipt["matched"] is True
        assert receipt["raw_payload_rehashed_by_pr173"] is False
        if receipt["support_only"]:
            assert receipt["actual_metadata_sha256"] is None
            assert receipt["small_metadata_bytes_hashed"] is False
        else:
            path = REPO / receipt["artifact"]
            assert hashlib.sha256(path.read_bytes()).hexdigest() == receipt["actual_metadata_sha256"]
            assert receipt["actual_metadata_sha256"] == receipt["expected_sha256"]


def test_registered_mutations_all_execute_and_are_killed() -> None:
    mutation = _json("docs/generated/pr173_mutation_report.json")
    assert mutation["registered_count"] == 18
    assert mutation["executed_count"] == 18
    assert mutation["killed_count"] == 18
    assert mutation["survivors"] == []
    assert all(row["executed"] and row["killed"] for row in mutation["mutations"])


def test_validator_rejects_promotions_hash_drift_and_partial_use() -> None:
    spec = _spec()

    false_planck = copy.deepcopy(_report())
    false_planck["targets"][0]["numerical_resolution_status"] = RESOLVED
    _reseal(false_planck)
    assert validate_report(false_planck, spec)

    false_act = copy.deepcopy(_report())
    false_act["targets"][1]["numerical_resolution_status"] = UNRESOLVED
    _reseal(false_act)
    assert any("numerical" in error for error in validate_report(false_act, spec))

    partial_desi = copy.deepcopy(_report())
    partial_desi["targets"][-1]["partial_mock_count_used"] = 1
    _reseal(partial_desi)
    assert any("partial mock" in error for error in validate_report(partial_desi, spec))

    hash_drift = copy.deepcopy(_report())
    hash_drift["source_authority_receipts"][0]["actual_metadata_sha256"] = "0" * 64
    _reseal(hash_drift)
    assert any("byte hash" in error for error in validate_report(hash_drift, spec))


def test_validator_rejects_coordinated_uncertainty_and_provenance_forgery() -> None:
    spec = _spec()
    forged = copy.deepcopy(_report())
    original = forged["targets"][0]["certificate"]
    replacement = rank_certificate(
        n_null=original["n_null"],
        exceedance_count=original["exceedance_count"],
        uncertainty_interval=[0.001, 0.051],
        boundary=original["boundary"],
        direction=original["direction"],
        confidence_level=original["confidence_level"],
        uncertainty_method=original["uncertainty_method"],
        mc_se=0.0,
    )
    forged["targets"][0]["certificate"] = replacement
    forged["targets"][0]["numerical_resolution_status"] = replacement[
        "numerical_resolution_status"
    ]
    _reseal(forged)
    assert any(
        "frozen-source reconstruction" in error
        for error in validate_report(forged, spec)
    )

    for mutate in (
        lambda value: value["targets"][0]["uncertainty_receipt"].update(
            {"mc_se": 999.0}
        ),
        lambda value: value["targets"][0]["upstream_bootstrap_reproduction"].update(
            {"matched": False}
        ),
        lambda value: value.update({"config_hash": "0" * 64}),
        lambda value: value["input_hashes"].update(
            {"htt/obsstat/finite_ensemble.py": "0" * 64}
        ),
        lambda value: value["targets"][0].update({"source": "forged_source"}),
    ):
        candidate = copy.deepcopy(_report())
        mutate(candidate)
        _reseal(candidate)
        assert validate_report(candidate, spec)


def test_certificate_validator_rejects_boundary_unit_and_boolean_count_drift() -> None:
    certificate = copy.deepcopy(_report()["targets"][0]["certificate"])
    certificate["boundary_unit"] = "km/s"
    assert certificate_errors(certificate)

    certificate = copy.deepcopy(_report()["targets"][0]["certificate"])
    certificate["n_null"] = True
    assert certificate_errors(certificate)

    with pytest.raises(FiniteEnsembleError):
        rank_certificate(
            n_null=99,
            exceedance_count=3,
            uncertainty_interval=[0.04, 0.04],
            boundary=0.05,
            direction="below",
            confidence_level=1.0,
            uncertainty_method="fixture",
        )
    with pytest.raises(FiniteEnsembleError):
        rank_certificate(
            n_null=99,
            exceedance_count=3,
            uncertainty_interval=[0.04, 0.04],
            boundary=True,
            direction="below",
            confidence_level=0.95,
            uncertainty_method="fixture",
        )


def test_blocked_certificate_primitives_never_emit_numerical_status() -> None:
    lineage = not_certifiable_certificate(
        reason="fixture",
        required_method="registered_method",
        lineage_status=LINEAGE_MISSING,
    )
    assert lineage["numerical_resolution_status"] is None
    assert certificate_errors(lineage) == []
    unavailable = not_evaluated_certificate(
        reason="fixture",
        required_method="registered_method",
        availability_status=INPUT_PARTIAL_FORBIDDEN,
    )
    assert unavailable["replicate_lineage_status"] is None
    assert unavailable["numerical_resolution_status"] is None
    assert certificate_errors(unavailable) == []


def test_card_manifest_and_claim_boundary_preserve_process_science_split() -> None:
    card = _json("docs/generated/pr173_result_card.json")
    manifest = _json("docs/generated/pr173_artifact_manifest.json")
    assert card["process_execution_status"] == "PASS_REPRODUCIBLE_TERMINAL_EVIDENCE"
    assert card["success_dependency_satisfied"] is True
    assert card["scientific_status"] == "OPEN"
    assert card["scientific_result"] == (
        "0_RESOLVED_1_NUMERICALLY_UNRESOLVED_5_NOT_CERTIFIABLE_1_NOT_EVALUATED"
    )
    assert manifest["success_dependency_satisfied"] is True
    assert manifest["artifact_count"] == 4
    for relative, expected in manifest["artifacts"].items():
        assert hashlib.sha256((REPO / relative).read_bytes()).hexdigest() == expected
    for key in (
        "owner",
        "implementation_scope",
        "claim_tier",
        "transfer_source",
        "config_hash",
        "input_hashes",
        "sky_support_status",
        "mask_status",
        "covariance_status",
        "null_mock_status",
        "generating_command",
        "git_commit",
        "worktree_state",
    ):
        assert key in manifest
    serialized = json.dumps(_report()).lower()
    for forbidden in (
        "bianchi geometry detected",
        "bianchi family identified",
        "raw-qe reproduction",
    ):
        assert forbidden not in serialized


def test_review_history_is_byte_preserved_including_stale_and_fail_receipts() -> None:
    completed = subprocess.run(
        [
            str(REPO / "venv/bin/python"),
            "-B",
            str(REPO / "scripts/codex_harness/archive_pr173_reviews.py"),
            "--check",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    manifest = _json("docs/generated/pr173_reviews/manifest.json")
    assert manifest["review_count"] == 11
    assert manifest["copy_mode"] == "byte_for_byte"
    assert manifest["review_statuses"] == {
        "final_claim": "pass",
        "final_code": "fail",
        "final_statistics": "pass",
        "intake_claim": "fail",
        "intake_harness": "pass",
        "intake_statistics": "pass",
        "remediation_claim": "pass",
        "remediation_code": "pass",
        "stale_final_claim": "error",
        "stale_final_code": "error",
        "stale_final_statistics": "error",
    }
    for row in manifest["reviews"]:
        destination = REPO / row["destination_path"]
        assert hashlib.sha256(destination.read_bytes()).hexdigest() == row["sha256"]
