from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts/codex_harness/run_pr286_pillar_s_adjudication.py"
RECEIPT = (
    ROOT / "docs/research_program/post_pr275/pillar_s_adjudication"
    / "PILLAR_S_COMPLETE_ADJUDICATION_V1.json"
)


def _load_runner():
    spec = importlib.util.spec_from_file_location("pr286_runner", RUNNER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def runner():
    return _load_runner()


@pytest.fixture(scope="module")
def payload(runner):
    return runner.build_complete_adjudication_receipt()


def test_exact_inventory_and_terminal_counts(payload):
    assert len(payload["rows"]) == 72
    assert payload["summary"] == {
        "source_rows": 58,
        "source_partition_counts": {"BRIDGE": 4, "I": 30, "II": 24},
        "source_proof_class_counts": {"ST": 24, "TC": 30, "U": 4},
        "vector_tensor_rows": 14,
        "terminal_counts": {
            "PASS": 21,
            "FAIL": 0,
            "INCONCLUSIVE_WITH_RECEIPT": 50,
            "BLOCKED_WITH_RECEIPT": 1,
        },
        "bare_not_adjudicated_count": 0,
    }


def test_every_row_has_evidence_class_specific_fields(payload):
    required = {
        "row_id", "source_group", "source_statement",
        "source_statement_identity_sha256", "adjudicated_statement",
        "statement_relation", "evidence_class", "estimand", "sampling_law",
        "covariance_assumptions", "finite_or_asymptotic_status",
        "implementation_evidence", "preregistration_evidence",
        "coverage_evidence", "negative_controls", "assumptions",
        "negative_control_terminal", "positive_cell_terminal",
        "units_normalization_and_frame", "sign_orientation_convention",
        "prior_applicability_and_identity", "rank_and_identification_scope",
        "singular_value_and_principal_angle_status", "counterexample_boundary",
        "verdict", "verdict_reason", "claim_ceiling",
    }
    for row in payload["rows"]:
        assert required <= row.keys(), row["row_id"]
        assert row["claim_ceiling"] == "diagnostic_only"
        assert row["verdict"] in {
            "PASS", "FAIL", "INCONCLUSIVE_WITH_RECEIPT", "BLOCKED_WITH_RECEIPT",
        }


def test_source_proven_cas_rows_only_are_exact_pass(payload):
    rows = {
        r["row_id"]: r for r in payload["rows"]
        if r["source_group"] == "proposal_registry_rows"
    }
    expected_pass = {"I-2.1", "I-2.2", "I-2.3", "I-2.9", "I-5.1", "I-5.2", "I-5.3", "I-5.4"}
    assert len(rows) == 58
    assert {key for key, row in rows.items() if row["verdict"] == "PASS"} == expected_pass
    for key in expected_pass:
        row = rows[key]
        assert row["evidence_class"] == "EXACT_PROOF"
        assert row["finite_or_asymptotic_status"] == "EXACT"
        assert row["coverage_evidence"] == "NOT_APPLICABLE_EXACT_PROPOSITION"


def test_source_exact_passes_bind_claim_contract_and_four_axis_adjudication(payload):
    rows = {row["row_id"]: row for row in payload["rows"]}
    for row_id in {"I-2.1", "I-2.2", "I-2.3", "I-2.9"}:
        evidence = rows[row_id]["implementation_evidence"]
        assert evidence["legacy_claim_id"] in evidence["cas_contract"]["claim_ids"]
        assert evidence["cas_contract"]["contract_id"] == "CAS-PR257-ORBIT-CATALOGUE-V2-001"
        assert evidence["cas_contract"]["aggregate_status"] == "CAS_4AXIS_PASS"
    for row_id in {"I-5.1", "I-5.2", "I-5.3", "I-5.4"}:
        evidence = rows[row_id]["implementation_evidence"]
        assert evidence["legacy_claim_id"] in evidence["cas_contract"]["claim_ids"]
        assert evidence["cas_contract"]["contract_id"] == "CAS-PR254-ANCHOR-GEOMETRY-001"
        assert evidence["cas_contract"]["aggregate_status"] == "CAS_4AXIS_PASS"


def test_source_oracle_and_active_labels_do_not_self_promote(payload):
    rows = [
        r for r in payload["rows"]
        if r["source_group"] == "proposal_registry_rows"
        and r["source_status"] != "PROVEN_CAS4"
    ]
    assert len(rows) == 50
    assert {r["verdict"] for r in rows} == {"INCONCLUSIVE_WITH_RECEIPT"}
    assert all(r["source_status"] != r["verdict"] for r in rows)


def test_null_source_statements_remain_unavailable(payload):
    rows = {
        r["row_id"]: r for r in payload["rows"]
        if r["source_group"] == "proposal_registry_rows"
    }
    for row_id in {"I-5.5", "I-6.1", "I-6.2", "I-6.3", "II-4.1", "II-4.2", "II-4.3", "II-4.5", "II-5.4"}:
        assert rows[row_id]["source_statement"] is None
        assert rows[row_id]["adjudicated_statement"] == "UNAVAILABLE_SOURCE_STATEMENT"
        assert rows[row_id]["verdict"] == "INCONCLUSIVE_WITH_RECEIPT"


def test_vt_s_exact_and_synthetic_evidence_stay_distinct(payload):
    rows = {
        r["row_id"]: r for r in payload["rows"]
        if r["source_group"] == "vector_tensor_successor"
    }
    exact = {"VT-S1", "VT-S2", "VT-S4", "VT-S7", "VT-S8"}
    synthetic = {"VT-S3", "VT-S5", "VT-S6", "VT-S9", "VT-S10", "VT-S11", "VT-S12", "VT-S13"}
    assert set(rows) == {f"VT-S{i}" for i in range(1, 15)}
    assert all(rows[key]["evidence_class"] == "EXACT_TYPED_PROOF" for key in exact)
    assert all(rows[key]["verdict"] == "PASS" for key in exact)
    assert all(rows[key]["evidence_class"] == "PREREGISTERED_SYNTHETIC_VALIDATION_ONLY" for key in synthetic)
    assert all(rows[key]["verdict"] == "PASS" for key in synthetic)
    assert all(rows[key]["source_status_effect"] == "RETAIN_CONDITIONAL_PROGRAM" for key in synthetic)
    assert rows["VT-S14"]["verdict"] == "BLOCKED_WITH_RECEIPT"
    assert rows["VT-S14"]["source_status_effect"] == "RETAIN_PROGRAM_OBLIGATION"


def test_preregistered_statistical_fields_and_negative_controls(payload):
    rows = {r["row_id"]: r for r in payload["rows"]}
    for row_id in ["VT-S3", "VT-S5", "VT-S6", "VT-S9", "VT-S10", "VT-S11", "VT-S12", "VT-S13", "VT-S14"]:
        row = rows[row_id]
        assert row["estimand"] != "UNAVAILABLE"
        assert row["sampling_law"] != "UNAVAILABLE"
        assert row["finite_or_asymptotic_status"] == "FINITE_PREREGISTERED_SYNTHETIC"
        assert row["preregistration_evidence"]
        assert isinstance(row["coverage_evidence"], dict)
        assert row["negative_controls"]
    assert rows["VT-S3"]["negative_controls"]["misspecified_covariance_negative_control"]["failure_visible"] is True
    assert rows["VT-S5"]["negative_controls"]["adversarial_failure_map"]
    assert rows["VT-S9"]["negative_controls"]["unadjusted_failure_preserved"] is True
    assert rows["VT-S10"]["negative_controls"]["weak"]["status"] == "ABSTAIN_WEAK_IDENTIFICATION"
    assert rows["VT-S13"]["negative_controls"]["finite_library_sensitivity"] > 0
    assert all(
        rows[row_id]["negative_control_terminal"]
        == "EXPECTED_NEGATIVE_CONTROL_KILLED"
        for row_id in ["VT-S3", "VT-S5", "VT-S6", "VT-S9", "VT-S10", "VT-S11", "VT-S12", "VT-S13", "VT-S14"]
    )


def test_implementation_and_semantic_types_are_byte_bound(payload):
    bundle = payload["synthetic_implementation_bundle"]
    assert bundle["provenance_grade"] == "CURRENT_REPLAY_BOUND_NOT_PRE_RESULT_EXTERNAL_SEAL"
    assert bundle["source_hashes"]["scripts/codex_harness/build_pr272_pillar_s_inference.py"]
    assert bundle["source_hashes"]["htt/src/common/vector_tensor_statistical_inference.py"]
    rows = {row["row_id"]: row for row in payload["rows"]}
    assert rows["VT-S8"]["sign_orientation_convention"].startswith("ORDERED_CONTRAST_X_A_MINUS_X_B")
    assert rows["VT-S11"]["rank_and_identification_scope"]["global_orbit_separation_claimed"] is False
    rank = rows["VT-S14"]["rank_and_identification_scope"]
    assert rank["joint_design_rank"] == 2
    assert rank["whitened_principal_angle_radians"] > rank["principal_angle_floor_radians"]
    assert rank["proportional_design_negative_control"] == {
        "status": "ABSTAIN_NON_IDENTIFIED",
        "selected_candidate": "INDETERMINATE",
        "expected_terminal": "EXPECTED_NEGATIVE_CONTROL_KILLED",
    }
    assert all(
        rows[row_id]["prior_applicability_and_identity"]
        == "NOT_APPLICABLE_NO_PRIOR_IN_REGISTERED_ROW"
        for row_id in [f"VT-S{i}" for i in range(1, 15)]
    )


def test_vts14_rank_contract_uses_whitened_normalized_design(runner):
    contract = runner._vts14_rank_contract(
        {
            "covariance": [[1.0, 0.0], [0.0, 1.0e-32]],
            "local_design": [1.0, 0.0],
            "global_design": [1.0, 1.0e-16],
            "mask_path_id": "anisotropic-rank-probe",
        }
    )
    assert contract["joint_design_rank"] == 2
    assert contract["rank_metric"] == (
        "COLUMN_NORMALIZED_COVARIANCE_WHITENED_DESIGN"
    )
    assert contract["hostile_numeric_controls"] == {
        "extreme_spd_finite_gls": "TYPED_REFUSAL",
        "large_scale_finite_gls": "TYPED_REFUSAL",
        "whitened_rank_probe": {
            "selected_candidate": "LOCAL",
            "status": "VALIDATED_REGISTERED_SYNTHETIC",
        },
        "zero_design": "TYPED_REFUSAL",
    }


def test_pr287_consumer_binding_preserves_row_level_nonpromotion(payload):
    contract = payload["future_consumer_contract"]
    assert contract["consumer"] == "PR-287"
    assert contract["upstream_terminal_required"] == "PASS_COMPLETE_PILLAR_S_ADJUDICATION"
    assert contract["upstream_success_semantics"] == "PROCESS_COMPLETION_ONLY"
    assert contract["preserve_inconclusive_and_blocked"] is True
    assert contract["synthetic_validation_effect"] == "NO_OBSERVED_OR_SOURCE_PROOF_PROMOTION"
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(ROOT / "scripts/codex_harness/validate_pr_dag.py"),
            str(ROOT / "docs/codex_handoff/pr_backlog.yaml"),
            "--status",
            str(ROOT / "docs/codex_handoff/pr_status.yaml"),
            "--strict-rescue-slice",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_process_success_is_terminal_coverage_not_universal_proof(payload):
    assert payload["terminal"] == "PASS_COMPLETE_PILLAR_S_ADJUDICATION"
    assert payload["success_dependency_satisfied"] is True
    assert payload["scientific_status_effect"] == "ROW_LEVEL_EVIDENCE_SPECIFIC_DISPOSITION_ONLY"
    assert payload["summary"]["terminal_counts"]["PASS"] < len(payload["rows"])


def test_claim_and_ownership_firewall(payload):
    metadata = payload["metadata"]
    assert metadata["claim_tier"] == "diagnostic_only"
    assert metadata["claim_level"] == {"scheme": "roadmap_rescue_v1", "level": "C2"}
    assert metadata["transfer_source"] == "none"
    assert metadata["observed_data_executed"] is False
    assert metadata["public_use"] is False
    assert metadata["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
    assert payload["ownership"] == {
        "COMMON": "exact contracts and proof identities",
        "OBSSTAT": "observable estimands features nulls and covariance inputs",
        "HTT": "model-dependent calibration coverage and inference diagnostics",
        "MIO": "diagnostic residual and coherence consumers only",
    }
    assert payload["mio_forbidden_outputs"] == ["likelihood", "posterior", "Bayes_factor", "evidence"]


def test_source_bindings_and_content_address(payload, runner):
    for binding in payload["source_bindings"]:
        path = ROOT / binding["path"]
        assert path.is_file() and not path.is_symlink()
        assert payload["source_binding_map"][binding["path"]] == binding["sha256"]
    assert payload["receipt_content_sha256"] == runner.receipt_content_sha256(payload)


def test_mutable_orchestration_is_validated_but_not_claim_source_bound(payload, runner):
    mutable_orchestration = {
        runner.BACKLOG_PATH,
        runner.BACKLOG_MIRROR_PATH,
        runner.BACKLOG_JSON_PATH,
        runner.BACKLOG_JSON_MIRROR_PATH,
        runner.DAG_VALIDATOR_PATH,
    }
    assert mutable_orchestration.isdisjoint(payload["source_binding_map"])
    assert runner._future_consumer_contract()["consumer"] == "PR-287"


@pytest.mark.parametrize(
    ("mutation_id", "marker"),
    [
        ("MU286-DROP-SOURCE-ROW", "SOURCE_INVENTORY_MISMATCH"),
        ("MU286-DROP-VTS-ROW", "VTS_INVENTORY_MISMATCH"),
        ("MU286-BARE-SOURCE-STATUS", "TERMINAL_VOCABULARY_INVALID"),
        ("MU286-STATEMENT-DRIFT", "STATEMENT_IDENTITY_DRIFT"),
        ("MU286-EXACT-BY-SIMULATION", "EXACT_EVIDENCE_CLASS_INVALID"),
        ("MU286-ORACLE-LABEL-AS-PROOF", "SOURCE_STATUS_PROMOTION"),
        ("MU286-ESTIMAND-DRIFT", "STATISTICAL_IDENTITY_DRIFT"),
        ("MU286-LAW-COVARIANCE-DRIFT", "STATISTICAL_IDENTITY_DRIFT"),
        ("MU286-SEED-TOLERANCE-DRIFT", "PREREGISTRATION_DRIFT"),
        ("MU286-HIDE-NEGATIVE-CONTROL", "NEGATIVE_CONTROL_HIDDEN"),
        ("MU286-VTS14-DATA-PROMOTION", "VTS14_ADMITTED_DATA_PROMOTION"),
        ("MU286-MIO-POSTERIOR", "OWNERSHIP_FIREWALL_DRIFT"),
        ("MU286-CLAIM-PROMOTION", "CLAIM_FIREWALL_DRIFT"),
        ("MU286-CAS-BINDING-DRIFT", "CAS_SOURCE_EVIDENCE_DRIFT"),
        ("MU286-IMPLEMENTATION-BINDING-DRIFT", "IMPLEMENTATION_IDENTITY_DRIFT"),
        ("MU286-SEMANTIC-TYPE-DRIFT", "SEMANTIC_TYPE_DRIFT"),
        ("MU286-NEGATIVE-CONTROL-SURVIVES", "NEGATIVE_CONTROL_TERMINAL_DRIFT"),
        ("MU286-VTS14-PROPORTIONAL-DESIGN", "VTS14_LOCAL_GLOBAL_RANK_GATE"),
        ("MU286-VTS14-NUMERIC-GUARD-DRIFT", "SEMANTIC_TYPE_DRIFT"),
    ],
)
def test_each_registered_mutation_is_killed(payload, runner, mutation_id, marker):
    mutated = runner.apply_registered_mutation(deepcopy(payload), mutation_id)
    mutated["receipt_content_sha256"] = runner.receipt_content_sha256(mutated)
    with pytest.raises(runner.PillarSAdjudicationError, match=marker):
        runner.validate_complete_adjudication_receipt(mutated)


def test_mutation_results_complete_and_killed(payload):
    ids = [item["mutation_id"] for item in payload["mutation_registry"]]
    results = payload["mutation_results"]
    assert [item["mutation_id"] for item in results] == ids
    assert all(item["executed"] and item["activated"] and item["killed"] for item in results)
    assert all(item["survivor"] is False for item in results)
    assert all(item["evidence_fingerprint"] for item in results)


def test_build_executes_every_registered_mutation_in_exact_order(monkeypatch, runner):
    calls = []
    original = runner.apply_registered_mutation

    def recording_apply(payload, mutation_id):
        calls.append(mutation_id)
        return original(payload, mutation_id)

    monkeypatch.setattr(runner, "apply_registered_mutation", recording_apply)
    built = runner.build_complete_adjudication_receipt()
    expected = [item["mutation_id"] for item in built["mutation_registry"]]
    assert calls == expected


@pytest.mark.parametrize("corruption", ["missing", "duplicate", "reordered", "empty_marker"])
def test_build_rejects_forged_mutation_execution(monkeypatch, runner, corruption):
    original = runner._run_registered_mutations

    def corrupt(payload):
        results = original(payload)
        if corruption == "missing":
            return results[:-1]
        if corruption == "duplicate":
            return [*results[:-1], deepcopy(results[-2])]
        if corruption == "reordered":
            return [results[1], results[0], *results[2:]]
        results[0]["kill_marker"] = ""
        return results

    monkeypatch.setattr(runner, "_run_registered_mutations", corrupt)
    with pytest.raises(runner.PillarSAdjudicationError, match="MUTATION_RESULTS_INCOMPLETE|MUTATION_RESULT_INVALID"):
        runner.build_complete_adjudication_receipt()


def test_tracked_receipt_exact_replay(payload):
    assert json.loads(RECEIPT.read_text(encoding="utf-8")) == payload


def test_check_portable_from_tmp():
    completed = subprocess.run(
        [sys.executable, "-B", str(RUNNER), "check"],
        cwd=Path("/tmp"), text=True, capture_output=True, check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_build_refuses_hardlinked_output_before_payload_generation(
    monkeypatch, tmp_path, runner
):
    generated = tmp_path / "generated"
    generated.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text("preserve\n", encoding="utf-8")
    destination = generated / "receipt.json"
    destination.hardlink_to(outside)
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "OUTPUT", destination, raising=False)

    def must_not_build():
        raise AssertionError("builder ran before destination preflight")

    monkeypatch.setattr(runner, "build_complete_adjudication_receipt", must_not_build)
    assert runner.main(["build"]) == 1
    assert outside.read_text(encoding="utf-8") == "preserve\n"


def test_clean_git_archive_replay():
    completed = subprocess.run(
        [sys.executable, "-B", str(RUNNER), "portable"],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
