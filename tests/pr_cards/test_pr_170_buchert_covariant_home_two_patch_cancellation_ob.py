from __future__ import annotations

import copy
import hashlib
import json
from fractions import Fraction
from pathlib import Path

import pytest
import yaml

from common.buchert_two_patch import (
    BIANCHI_TYPES,
    TYPE_CURVATURE_PROVENANCE,
    TwoPatchState,
    barrow_tsagas_residual_q,
    buchert_total_q,
    external_type_closure_summary,
)
from scripts.codex_harness import collect_pr170_cas_receipts as collector
from scripts.codex_harness import run_pr170_axis as axis_runner
from scripts.codex_harness import run_pr170_buchert_two_patch as result_runner
from scripts.codex_harness.verify_pr170_sources import verify


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs/generated/pr170_cas/CAS_CONTRACT_PR170_BUCHERT_TWO_PATCH.json"
RUN_DIR = Path(".agent-harness/runs/pr170-cas-remediation-20260719")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_equal_expansion_identity_is_exact() -> None:
    state = TwoPatchState(Fraction(1, 2), 2, 2, 3, 3)
    assert state.hubble_domain == 2
    assert state.expansion_variance == 0
    assert state.q_buchert == -6
    assert state.omega_q_buchert == Fraction(1, 4)
    assert state.sigma2_domain_rms == Fraction(1, 4)
    assert state.bridge_residual == 0


def test_two_patch_cancellation_is_non_identifying() -> None:
    state = TwoPatchState(Fraction(1, 2), 3, 1, 3, 3)
    assert state.expansion_variance == 9
    assert state.mean_shear_sq == 3
    assert state.cancellation_residual == 0
    assert state.q_buchert == 0
    assert state.omega_q_buchert == 0
    assert state.sigma2_domain_rms == Fraction(1, 4)
    assert state.bridge_residual == -Fraction(1, 4)


def test_general_bridge_residual_formula() -> None:
    state = TwoPatchState(Fraction(1, 3), 5, 2, 2, 7)
    assert state.bridge_residual == state.expected_bridge_residual


def test_patch_exchange_preserves_derived_scalars() -> None:
    state = TwoPatchState(Fraction(1, 3), 5, 2, 2, 7)
    swapped = state.swapped()
    assert swapped.hubble_domain == state.hubble_domain
    assert swapped.expansion_variance == state.expansion_variance
    assert swapped.mean_shear_sq == state.mean_shear_sq
    assert swapped.q_buchert == state.q_buchert
    assert swapped.bridge_residual == state.bridge_residual


@pytest.mark.parametrize("weight", [0, 1, -1, Fraction(3, 2)])
def test_invalid_weights_fail_closed(weight: Fraction) -> None:
    with pytest.raises(ValueError, match="0 < lambda < 1"):
        TwoPatchState(weight, 2, 2, 0, 0)


def test_negative_squared_shear_fails_closed() -> None:
    with pytest.raises(ValueError, match="nonnegative"):
        TwoPatchState(Fraction(1, 2), 2, 2, -1, 0)


def test_zero_hubble_normalization_fails_closed() -> None:
    state = TwoPatchState(Fraction(1, 2), 1, -1, 0, 0)
    assert state.hubble_domain == 0
    with pytest.raises(ZeroDivisionError, match="H_D=0"):
        _ = state.omega_q_buchert
    with pytest.raises(ZeroDivisionError, match="H_D=0"):
        _ = state.sigma2_domain_rms


def test_buchert_and_barrow_tsagas_q_are_typed_distinct() -> None:
    assert buchert_total_q(Fraction(0), Fraction(1)) == -2
    assert barrow_tsagas_residual_q(Fraction(0), Fraction(1), Fraction(1)) == 0


def test_barrow_tsagas_impossible_moments_fail_closed() -> None:
    with pytest.raises(ValueError, match=r"mean_sigma_sq >= mean_sigma\^2"):
        barrow_tsagas_residual_q(Fraction(0), Fraction(0), Fraction(1))
    with pytest.raises(ValueError, match="mean_sigma >= 0"):
        barrow_tsagas_residual_q(Fraction(0), Fraction(1), Fraction(-1))


def test_type_registry_is_exactly_eleven_and_partial() -> None:
    summary = external_type_closure_summary()
    assert len(BIANCHI_TYPES) == len(set(BIANCHI_TYPES)) == 11
    assert set(summary["resolved_types"]) == {"I", "V"}
    assert summary["resolved_type_count"] == 2
    assert summary["unresolved_type_count"] == 9
    assert summary["externally_authenticated_types"] == ("V",)
    assert summary["externally_authenticated_type_count"] == 1
    assert summary["internal_exact_types"] == ("I",)
    assert summary["internal_exact_type_count"] == 1
    assert summary["all_types_externally_closed"] is False
    assert TYPE_CURVATURE_PROVENANCE["V"] != TYPE_CURVATURE_PROVENANCE["VII_h"]


def test_source_records_are_content_addressed_without_raw_ci_requirement() -> None:
    receipt = verify(require_raw=False)
    assert receipt["ok"] is True
    assert all(row["equation_record_ok"] for row in receipt["sources"])


def test_contract_hashes_all_committed_inputs_and_axis_sources() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["schema_version"] == 2
    assert set(contract["axes"]) == {"wolfram_xact", "sympy", "sage_singular", "lean"}
    assert len(contract["target"]["canonical_type_registry"]) == 11
    assert len(contract["target"]["exact_test_obligations"]) == 15
    for row in contract["identity"]["source_input_hashes"]:
        assert _sha(ROOT / row["path"]) == row["sha256"]
    for details in contract["axes"].values():
        for row in details["sources"]:
            assert _sha(ROOT / row["path"]) == row["sha256"]


def test_contract_validator_rejects_vacuous_or_substituted_inventories() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    vacuous = copy.deepcopy(contract)
    vacuous["identity"]["source_input_hashes"] = []
    for details in vacuous["axes"].values():
        details["sources"] = []
        details["command"] = ""
        details["required_tool"] = ""
    assert axis_runner._validate_contract(vacuous)
    assert collector._validate_exact_contract_inventory(vacuous)

    substituted = copy.deepcopy(contract)
    substituted["axes"]["sympy"]["sources"] = substituted["axes"]["sage_singular"]["sources"]
    assert collector._validate_exact_contract_inventory(substituted)


def test_primary_provenance_refuses_universal_type_closure() -> None:
    payload = yaml.safe_load(
        (ROOT / "docs/research_program/long_horizon_rescue/pr170_primary_source_provenance.yaml").read_text(encoding="utf-8")
    )
    assert payload["type_curvature_registry"]["universal_external_closure"] is False
    assert payload["type_curvature_registry"]["V"].startswith("PASS_")
    assert payload["type_curvature_registry"]["VII_h"].startswith("UNRESOLVED_")


def test_collector_rejects_tampered_obligation(monkeypatch: pytest.MonkeyPatch) -> None:
    original_load = collector._load

    def tampered(path: Path) -> dict[str, object]:
        payload = original_load(path)
        if path.name == "A-PR170-CAS-SYMPY.json" and path.parent.name == "results":
            payload = copy.deepcopy(payload)
            payload["payload"]["cas_axis_result"]["checks"]["constant_expansion_bridge"] = False
        return payload

    monkeypatch.setattr(collector, "_load", tampered)
    _, collection = collector.build(RUN_DIR)
    assert collection["evidence_valid"] is False
    assert collection["aggregate_state"] == "EVIDENCE_INVALID"
    assert any("false/nonboolean" in error for error in collection["errors"])


def test_collector_rejects_outer_nested_status_disagreement(monkeypatch: pytest.MonkeyPatch) -> None:
    original_load = collector._load

    def tampered(path: Path) -> dict[str, object]:
        payload = original_load(path)
        if path.name == "A-PR170-CAS-LEAN.json" and path.parent.name == "results":
            payload = copy.deepcopy(payload)
            payload["status"] = "fail"
        return payload

    monkeypatch.setattr(collector, "_load", tampered)
    _, collection = collector.build(RUN_DIR)
    assert collection["evidence_valid"] is False
    assert any("outer/nested status mismatch" in error for error in collection["errors"])


def test_collector_rejects_posthoc_assignment_context_rewrite(monkeypatch: pytest.MonkeyPatch) -> None:
    original_load = collector._load

    def tampered(path: Path) -> dict[str, object]:
        payload = original_load(path)
        if path.name == "A-PR170-CAS-SYMPY.json" and path.parent.name in {"assignments", "results"}:
            payload = copy.deepcopy(payload)
            payload["context_version"] = "posthoc-context"
            if path.parent.name == "assignments":
                payload["assignment_sha256"] = collector._assignment_self_hash(payload)
        return payload

    monkeypatch.setattr(collector, "_load", tampered)
    _, collection = collector.build(RUN_DIR)
    assert collection["evidence_valid"] is False
    assert any("pre-axis authorization" in error for error in collection["errors"])


def test_cas_blocked_result_pack_withholds_scalar_claims() -> None:
    result = json.loads((ROOT / "docs/generated/pr170_result_card.json").read_text(encoding="utf-8"))
    assert result["process_gate_status"] == "BLOCKED"
    assert result["cas_aggregate"] == "CAS_BLOCKED"
    assert result["identity_result"] is None
    assert result["two_patch_measurement"] is None
    assert result["physical_witness_status"] == "WITHHELD_CAS_BLOCKED"
    assert result["x_C_Buchert_home_status"] == "NO_CURRENTLY_AUTHENTICATED_X_C_WIDE_BUCHERT_HOME"
    assert result["new_theorem"] is False
    assert result["family_identification"] is False
    assert result["native_transfer_validation"] is False


def test_manifest_hashes_every_result_artifact() -> None:
    manifest = json.loads((ROOT / "docs/generated/pr170_artifact_manifest.json").read_text(encoding="utf-8"))
    for row in manifest["artifacts"]:
        assert _sha(ROOT / row["path"]) == row["sha256"]
    assert manifest["scientific_state"]["cas_aggregate"] == "CAS_BLOCKED"
    assert manifest["scientific_state"]["scalar_result"] == "WITHHELD"
    assert manifest["scientific_state"]["external_type_curvature_closure"] == "1_of_11"
    assert manifest["scientific_state"]["internal_definitional_exact_type_closure"] == "1_of_11"
    assert manifest["scientific_state"]["witness_status"] == "WITHHELD_CAS_BLOCKED"


def test_all_registered_mutations_are_detected() -> None:
    report = json.loads((ROOT / "docs/generated/pr170_mutation_report.json").read_text(encoding="utf-8"))
    assert report["registered_count"] == 10
    assert report["detected_count"] == 10
    assert report["all_detected"] is True
    assert all(row.get("target") for row in report["mutations"])
    assert all(row.get("command") for row in report["mutations"])
    assert all(row.get("test_node") for row in report["mutations"])


def test_blocked_route_mutations_are_executed_and_detected() -> None:
    report = json.loads((ROOT / "docs/generated/pr170_mutation_report.json").read_text(encoding="utf-8"))
    rows = {row["mutation_id"]: row for row in report["mutations"]}
    for mutation_id in (
        "B001_CLAIM_LEVEL_PROMOTION",
        "B002_METADATA_PUBLIC_PROMOTION",
        "B003_PROCESS_PASS_PROMOTION",
        "B004_IDENTITY_RESULT_INJECTION",
        "B005_MEASUREMENT_INJECTION",
        "B006_LOCAL_PUBLIC_PROMOTION",
        "B007_FAMILY_PROMOTION",
        "B008_NATIVE_PROMOTION",
        "B009_EXTERNAL_TYPE_I_PROMOTION",
        "B010_ERRATUM_BINDING_DROP",
    ):
        assert rows[mutation_id]["execution_kind"] == "live_mutant_through_blocked_claim_validator"
        assert rows[mutation_id]["detected"] is True
        assert rows[mutation_id]["expected_failure"] in rows[mutation_id]["observed_violations"]


def test_blocked_claim_validator_rejects_c3_promotion() -> None:
    paths = {
        "source_provenance": "pr170_source_provenance_receipt.json",
        "exact_identity": "pr170_exact_identity.json",
        "two_patch_witness": "pr170_two_patch_witness.json",
        "type_closure": "pr170_type_closure.json",
        "physical_admissibility": "pr170_physical_admissibility.json",
        "candidate_branch_supersession": "pr170_candidate_branch_supersession.json",
        "result_card": "pr170_result_card.json",
        "active_consumer_inventory": "pr170_active_consumer_inventory.json",
    }
    surface = {
        name: json.loads((ROOT / "docs/generated" / filename).read_text(encoding="utf-8"))
        for name, filename in paths.items()
    }
    assert result_runner._blocked_claim_surface_violations(surface) == []
    surface["result_card"]["metadata"]["claim_level"]["level"] = "C3"
    assert "result_card:claim_level" in result_runner._blocked_claim_surface_violations(surface)


def test_result_generator_rejects_forged_cas_collection(monkeypatch: pytest.MonkeyPatch) -> None:
    real = json.loads((ROOT / "docs/generated/pr170_cas_collection_receipt.json").read_text(encoding="utf-8"))
    forged = copy.deepcopy(real)
    forged["contract_sha256"] = "0" * 64
    forged["axis_statuses"] = {axis: "FAIL" for axis in ("wolfram_xact", "sympy", "sage_singular", "lean")}
    original_load = result_runner._load_json

    def fake_load(path: Path) -> dict[str, object]:
        if path == ROOT / result_runner.CAS_COLLECTION:
            return forged
        return original_load(path)

    monkeypatch.setattr(result_runner, "_load_json", fake_load)
    monkeypatch.setattr(result_runner, "rebuild_cas_collection", lambda run_dir: ({}, forged))
    with pytest.raises(RuntimeError, match="valid CAS collection"):
        result_runner.build()


def test_candidate_source_and_consumer_inventory_are_content_addressed() -> None:
    supersession = json.loads((ROOT / "docs/generated/pr170_candidate_branch_supersession.json").read_text(encoding="utf-8"))
    binding = supersession["immutable_candidate_source"]
    assert _sha(ROOT / binding["path"]) == binding["file_sha256"]
    assert _sha(ROOT / binding["mirror_path"]) == binding["mirror_file_sha256"]
    assert binding["semantic_mirror_match"] is True

    inventory = json.loads((ROOT / "docs/generated/pr170_active_consumer_inventory.json").read_text(encoding="utf-8"))
    for row in inventory["consumers"]:
        assert _sha(ROOT / row["path"]) == row["sha256"]
    assert inventory["active_production_consumer_count"] == 0

    erratum = yaml.safe_load(
        (ROOT / "docs/research_program/long_horizon_rescue/pr170_spec_erratum.yaml").read_text(encoding="utf-8")
    )
    assert erratum["frozen_spec"]["sha256"] == _sha(ROOT / erratum["frozen_spec"]["path"])
    assert erratum["corrected_interpretation"]["externally_authenticated_types"] == ["V"]
    assert erratum["corrected_interpretation"]["internal_definitional_exact_types"] == ["I"]


def test_closeout_receipt_preserves_failures_and_binds_remediation() -> None:
    receipt = json.loads(
        (ROOT / "docs/generated/pr170_closeout_review_receipt.json").read_text(encoding="utf-8")
    )
    assert receipt["review_verdicts_preserved"] == {
        "claim": "fail",
        "harness": "fail",
        "physics": "fail",
        "final_adjudication": "FAIL_NOT_READY",
    }
    for path, expected in receipt["review_inputs"].items():
        assert _sha(ROOT / path) == expected
    for path, expected in receipt["remediated_surface_hashes"].items():
        assert _sha(ROOT / path) == expected
    assert all(row["status"] == "remediated" for row in receipt["finding_resolutions"])
    terminal = receipt["terminal_adjudication"]
    assert terminal["process_gate_status"] == "BLOCKED"
    assert terminal["scientific_result"] == "source_provenance_audit_only_cas_blocked"
    assert terminal["scalar_identity_result"] == "WITHHELD"
    assert terminal["public_use"] is False
    assert receipt["fresh_post_fix_reviewer"] is False
