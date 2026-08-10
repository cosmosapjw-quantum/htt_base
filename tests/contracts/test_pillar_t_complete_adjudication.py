from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts/codex_harness/run_pr285_pillar_t_adjudication.py"
RECEIPT = (
    ROOT
    / "docs/research_program/post_pr275/pillar_t_adjudication"
    / "PILLAR_T_COMPLETE_ADJUDICATION_V1.json"
)


def _load_runner():
    spec = importlib.util.spec_from_file_location("pr285_runner", RUNNER)
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
    rows = payload["rows"]
    assert len(rows) == 80
    assert payload["summary"] == {
        "source_rows": 65,
        "source_partition_counts": {"S": 34, "T": 31},
        "vector_tensor_rows": 14,
        "failed_candidate_rows": 1,
        "terminal_counts": {
            "PASS": 11,
            "FAIL": 1,
            "INCONCLUSIVE_WITH_RECEIPT": 67,
            "BLOCKED_WITH_RECEIPT": 1,
        },
        "bare_not_adjudicated_count": 0,
    }


def test_every_row_has_required_receipt_fields(payload):
    required = {
        "row_id",
        "source_group",
        "source_statement",
        "source_statement_identity_sha256",
        "adjudicated_statement",
        "statement_relation",
        "premises",
        "premise_status",
        "domains",
        "domain_status",
        "proof_evidence",
        "counterexample_boundary",
        "verdict",
        "verdict_reason",
        "claim_ceiling",
    }
    for row in payload["rows"]:
        assert required <= row.keys(), row["row_id"]
        assert row["claim_ceiling"] == "diagnostic_only"
        assert row["verdict"] in {
            "PASS",
            "FAIL",
            "INCONCLUSIVE_WITH_RECEIPT",
            "BLOCKED_WITH_RECEIPT",
        }


def test_legacy_titles_preserve_source_status_without_promotion(payload, runner):
    rows = [
        r
        for r in payload["rows"]
        if r["source_group"] == "legacy_signature_inventory"
    ]
    source_rows = runner._load_yaml(runner.SIGNATURES_PATH)["source_groups"][
        "legacy_signature_inventory"
    ]["entries"]
    expected = {
        row["entry_id"]: (row["assumption_status"], row["domain_status"])
        for row in source_rows
    }
    assert len(rows) == 65
    assert {r["verdict"] for r in rows} == {"INCONCLUSIVE_WITH_RECEIPT"}
    assert {
        r["row_id"]: (r["premise_status"], r["domain_status"])
        for r in rows
    } == expected
    assert sum(r["premise_status"] == "DECLARED" for r in rows) == 12
    assert sum(r["domain_status"] == "DECLARED" for r in rows) == 12


def test_vector_tensor_dispositions_preserve_restricted_boundaries(payload):
    rows = {
        r["row_id"]: r
        for r in payload["rows"]
        if r["source_group"] == "vector_tensor_successor"
    }
    assert set(rows) == {f"VT-T{i}" for i in range(1, 15)}
    expected_pass = {
        "VT-T1", "VT-T2", "VT-T3", "VT-T4", "VT-T5", "VT-T6",
        "VT-T7", "VT-T9", "VT-T10", "VT-T11", "VT-T12",
    }
    assert {k for k, v in rows.items() if v["verdict"] == "PASS"} == expected_pass
    assert rows["VT-T8"]["verdict"] == "INCONCLUSIVE_WITH_RECEIPT"
    assert rows["VT-T8"]["statement_relation"] == "RESTRICTED_GENERIC_LOCAL_ELABORATION"
    assert rows["VT-T13"]["verdict"] == "INCONCLUSIVE_WITH_RECEIPT"
    assert rows["VT-T13"]["statement_relation"] == "PARTIAL_CHAIN_RULE_ONLY"
    assert rows["VT-T14"]["verdict"] == "BLOCKED_WITH_RECEIPT"
    assert rows["VT-T14"]["statement_relation"] == "EXTERNAL_GATE_REFUSAL"


def test_pr190_full_interval_counterexample_remains_fail(payload):
    row = next(r for r in payload["rows"] if r["source_group"] == "failed_candidate")
    assert row["row_id"] == "C-PR190-FULL-COMPARATOR-ATTAINABILITY"
    assert row["verdict"] == "FAIL"
    assert row["terminal_source_status"] == "COMPLETED_FAILED_WITH_RECEIPT"
    assert row["success_dependency_satisfied"] is False
    assert any("W2=0" in item["reason"] for item in row["counterexample_boundary"])


def test_cas_contract_has_all_four_axes_and_no_majority_vote(payload):
    cas = payload["cas_evidence"]
    assert cas["aggregate_status"] == "CAS_4AXIS_PASS"
    assert cas["required_axes"] == ["wolfram_xact", "sympy", "sage_singular", "lean"]
    assert cas["axis_statuses"] == {
        "wolfram_xact": "PASS",
        "sympy": "PASS",
        "sage_singular": "PASS",
        "lean": "PASS",
    }
    assert cas["majority_vote_forbidden"] is True
    assert cas["covered_rows"] == ["VT-T5", "VT-T6", "VT-T7", "VT-T8", "VT-T13"]


def test_process_success_is_complete_coverage_not_all_rows_proved(payload):
    assert payload["terminal"] == "PASS_COMPLETE_PILLAR_T_ADJUDICATION"
    assert payload["success_dependency_satisfied"] is True
    assert payload["scientific_status_effect"] == "ROW_LEVEL_TERMINAL_DISPOSITION_ONLY"
    assert payload["summary"]["terminal_counts"]["PASS"] < len(payload["rows"])


def test_claim_and_family_firewall(payload):
    metadata = payload["metadata"]
    assert metadata["claim_tier"] == "diagnostic_only"
    assert metadata["claim_level"] == {"scheme": "roadmap_rescue_v1", "level": "C2"}
    assert metadata["transfer_source"] == "none"
    assert metadata["observed_data_executed"] is False
    assert metadata["public_use"] is False
    assert metadata["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"


def test_source_bindings_are_regular_and_exact(payload):
    paths = set()
    for binding in payload["source_bindings"]:
        path = ROOT / binding["path"]
        assert path.is_file() and not path.is_symlink()
        assert binding["sha256"] == payload["source_binding_map"][binding["path"]]
        paths.add(binding["path"])
    assert "docs/research_program/vector_tensor/THEOREM_SIGNATURES_V3.yaml" in paths
    assert "docs/generated/pr190_attainability/attainability_report.json" in paths
    assert "docs/research_program/vector_tensor/cas/CAS_CONTRACT.json" in paths


def test_content_address_recomputes(payload, runner):
    assert payload["receipt_content_sha256"] == runner.receipt_content_sha256(payload)


@pytest.mark.parametrize(
    ("mutation_id", "marker"),
    [
        ("MU285-DROP-SOURCE-ROW", "LEGACY_INVENTORY_MISMATCH"),
        ("MU285-DROP-VT-ROW", "VT_INVENTORY_MISMATCH"),
        ("MU285-BARE-NOT-ADJUDICATED", "TERMINAL_VOCABULARY_INVALID"),
        ("MU285-WEAKEN-STATEMENT", "STATEMENT_IDENTITY_DRIFT"),
        (
            "MU285-LEGACY-STATUS-FLATTENED",
            "LEGACY_PREMISE_DOMAIN_STATUS_DRIFT",
        ),
        ("MU285-CAS-AXIS-OMITTED", "CAS_REQUIRED_AXES_MISMATCH"),
        ("MU285-CAS-MAJORITY-VOTE", "CAS_AGGREGATE_INVALID"),
        ("MU285-CAS-CONTRACT-DRIFT", "CAS_CONTRACT_DRIFT"),
        ("MU285-T8-GLOBAL-PROMOTION", "VT_T8_SCOPE_PROMOTION"),
        ("MU285-T13-FULL-DYNAMICS-PROMOTION", "VT_T13_SCOPE_PROMOTION"),
        ("MU285-T14-NATIVE-PROMOTION", "VT_T14_NATIVE_PROMOTION"),
        ("MU285-PR190-REFUTATION-LAUNDERED", "PR190_REFUTATION_LAUNDERED"),
        ("MU285-CLAIM-CEILING-PROMOTION", "CLAIM_FIREWALL_DRIFT"),
    ],
)
def test_each_registered_mutation_is_killed(payload, runner, mutation_id, marker):
    mutated = runner.apply_registered_mutation(deepcopy(payload), mutation_id)
    mutated["receipt_content_sha256"] = runner.receipt_content_sha256(mutated)
    with pytest.raises(runner.PillarTAdjudicationError, match=marker):
        runner.validate_complete_adjudication_receipt(mutated)


def test_generated_mutation_results_are_complete_and_killed(payload):
    expected = [item["mutation_id"] for item in payload["mutation_registry"]]
    results = payload["mutation_results"]
    assert [item["mutation_id"] for item in results] == expected
    assert all(item["executed"] and item["activated"] and item["killed"] for item in results)
    assert all(item["survivor"] is False for item in results)


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


@pytest.mark.parametrize(
    "corruption", ["missing", "duplicate", "reordered", "unexecuted", "empty_marker"]
)
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
        if corruption == "unexecuted":
            results[0]["executed"] = False
            return results
        results[0]["kill_marker"] = ""
        return results

    monkeypatch.setattr(runner, "_run_registered_mutations", corrupt)
    with pytest.raises(
        runner.PillarTAdjudicationError,
        match="MUTATION_RESULTS_INCOMPLETE|MUTATION_RESULT_INVALID",
    ):
        runner.build_complete_adjudication_receipt()


def test_tracked_receipt_is_exact_replay(payload):
    assert RECEIPT.is_file()
    assert json.loads(RECEIPT.read_text(encoding="utf-8")) == payload


def test_check_is_portable_from_tmp():
    completed = subprocess.run(
        [sys.executable, "-B", str(RUNNER), "check"],
        cwd=Path("/tmp"),
        text=True,
        capture_output=True,
        check=False,
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
