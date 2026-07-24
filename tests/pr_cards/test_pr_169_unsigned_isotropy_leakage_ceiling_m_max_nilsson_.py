"""PR-169 acceptance tests for the exact algebraic-only result."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from copy import deepcopy
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest
import yaml


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "htt" / "src"))

from common.unsigned_isotropy_leakage import (  # noqa: E402
    REQUIRED_PHYSICAL_GATES,
    ComparatorPoint,
    PhysicalPromotionReceipt,
    PromotionCoherenceKey,
    QuadraticSectorSymbol,
    ReceiptStatus,
    UnsignedLeakageError,
    adjudicate_physical_bundle,
    exact_ceiling_receipt,
    require_typed_symbol_bridge,
    route_terminal_result,
)


GENERATED = REPO / "docs/generated"
AXES = ("wolfram_xact", "sympy", "sage_singular", "lean")


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _runner_module():
    path = REPO / "scripts/codex_harness/run_pr169_unsigned_leakage.py"
    spec = importlib.util.spec_from_file_location("pr169_runner", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _collector_module():
    path = REPO / "scripts/codex_harness/collect_pr169_cas_receipts.py"
    spec = importlib.util.spec_from_file_location("pr169_collector", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _axis_bundle(version: str, axis: str):
    collector = _collector_module()
    config = collector.VERSIONS[version]
    assignment_id = config["ids"][axis]
    run = REPO / ".agent-harness/runs" / config["run_id"]
    assignment = _json(run / "assignments" / f"{assignment_id}.json")
    outer = _json(run / "results" / f"{assignment_id}.json")
    contract = _json(REPO / config["contract"])
    return collector, config, contract, assignment, outer


def _reseal_assignment(collector, assignment: dict) -> None:
    unsigned = dict(assignment)
    unsigned.pop("assignment_sha256")
    assignment["assignment_sha256"] = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def test_exact_rational_ceiling_fixtures_and_uncapped_family() -> None:
    receipt = exact_ceiling_receipt(Fraction(3, 10))
    assert receipt["full_ceiling"] == "6/5"
    assert receipt["slice_ceiling"] == "3/5"
    assert receipt["full_fixture"]["x_C"] == "0"
    assert receipt["slice_fixture"]["x_C"] == "0"
    assert receipt["uncapped_family_fixture"]["M_unsigned"] == "3/5"

    for a in (Fraction(1, 101), Fraction(7, 3), Fraction(10**6)):
        point = ComparatorPoint(a, a, 0, 0)
        assert point.x_c() == 0
        assert point.m_unsigned() == 2 * a


def test_historical_v1_failure_and_v2_four_axis_pass_are_both_preserved() -> None:
    collection = _json(GENERATED / "pr169_cas_collection_receipt.json")
    assert collection["versions"]["v1"]["aggregate_status"] == "CAS_FAIL"
    assert collection["versions"]["v2"]["aggregate_status"] == "CAS_4AXIS_PASS"
    assert collection["cross_version_result_reuse"] is False
    for version, expected in (("v1", "FAIL"), ("v2", "PASS")):
        contract_sha = collection["versions"][version]["contract_sha256"]
        for axis in AXES:
            normalized_path = GENERATED / f"pr169_cas/{version}/axis_result_{axis}.json"
            outer_path = GENERATED / (
                f"pr169_cas/{version}/harness_receipts/outer_result_{axis}.json"
            )
            assignment_path = GENERATED / (
                f"pr169_cas/{version}/harness_receipts/assignment_{axis}.json"
            )
            normalized = _json(normalized_path)
            outer = _json(outer_path)
            assignment = _json(assignment_path)
            assert normalized["status"] == expected
            assert normalized["contract_sha256"] == contract_sha
            assert normalized["sibling_results_read"] == []
            assert outer["payload"]["cas_axis_result"] == normalized
            assert outer["assignment_id"] == assignment["assignment_id"]
            assert assignment["independence_mode"] == "blind-results"
            assert assignment["allowed_sibling_results"] == []
            hashes = collection["versions"][version]["receipt_hashes"][axis]
            assert hashes["normalized_result_sha256"] == _sha(normalized_path)
            assert hashes["outer_result_sha256"] == _sha(outer_path)
            assert hashes["assignment_sha256"] == _sha(assignment_path)

    v1_resolutions = collection["versions"]["v1"]["required_input_resolution"]
    v2_resolutions = collection["versions"]["v2"]["required_input_resolution"]
    v1_sympy = {
        row["requested_path"]: row for row in v1_resolutions["sympy"]
    }
    v2_sympy = {
        row["requested_path"]: row for row in v2_resolutions["sympy"]
    }
    source = "htt/src/common/pr169_sympy_axis.py"
    assert v1_sympy[source]["resolution"] == "sealed_v1_source_snapshot"
    assert v1_sympy[source]["resolved_path"].startswith(
        "docs/generated/pr169_cas/v1/source_snapshot/"
    )
    assert v2_sympy[source]["resolution"] == "current_repository_input"


def test_stored_cas_results_are_diagnostic_only() -> None:
    runner = _runner_module()
    status = runner._current_cas_status()
    assert status["aggregate_status"] == "CAS_BLOCKED"
    assert status["historical_aggregate_statuses"] == {
        "v1": "CAS_FAIL",
        "v2": "CAS_4AXIS_PASS",
    }
    assert status["stored_cas_diagnostic_only"] is True
    assert status["claim_promotion_cas_eligible"] is False


def test_nilsson_weyl_symbol_cannot_be_substituted_for_vorticity() -> None:
    with pytest.raises(UnsignedLeakageError, match="missing an exact-model derivation"):
        require_typed_symbol_bridge(
            QuadraticSectorSymbol.W_N2,
            QuadraticSectorSymbol.V2,
            exact_derivation_sha256=None,
        )
    provenance = yaml.safe_load(
        (REPO / "docs/research_program/long_horizon_rescue/"
         "pr169_primary_source_provenance.yaml").read_text(encoding="utf-8")
    )
    assert provenance["typed_bridge"]["direct_substitution_status"] == (
        "forbidden_unproved"
    )
    nilsson_fact = next(
        row for row in provenance["source_facts"]
        if row["fact_id"] == "NILSSON-W-IS-WEYL"
    )
    assert "Weyl" in nilsson_fact["normalized_statement"]


def _key(*, state: str = "a") -> PromotionCoherenceKey:
    return PromotionCoherenceKey(
        model_id="registered-test-model",
        model_version="v1",
        witness_id="witness-1",
        state_hash=state * 64,
        convention_hash="b" * 64,
        source_hashes=("c" * 64,),
        pr169_contract_hash="d" * 64,
    )


def test_physical_bundle_is_typed_complete_and_fail_closed() -> None:
    missing = adjudicate_physical_bundle([])
    assert missing["bundle_status"] == "MISSING"
    assert missing["missing_gate_ids"] == sorted(REQUIRED_PHYSICAL_GATES)
    assert missing["scientific_result_if_cas_passes"] == "algebraic_only"

    key = _key()
    receipts = [
        PhysicalPromotionReceipt(
            gate_id=gate,
            status=ReceiptStatus.PASS,
            coherence_key=key,
            evidence_hashes=("e" * 64,),
            issuer=f"independent-{index}",
            evidence_class="exact_model",
        )
        for index, gate in enumerate(REQUIRED_PHYSICAL_GATES)
    ]
    complete = adjudicate_physical_bundle(receipts, expected_key=key)
    assert complete["bundle_status"] == "PASS"
    assert complete["constructive_promotion_allowed"] is True

    duplicate = adjudicate_physical_bundle([*receipts, receipts[0]], expected_key=key)
    assert duplicate["bundle_status"] == "FAIL"
    assert duplicate["duplicate_gate_ids"] == [REQUIRED_PHYSICAL_GATES[0]]


@pytest.mark.parametrize(
    ("cas_status", "bundle", "semantic", "artifact", "process", "result"),
    [
        ("CAS_4AXIS_PASS", "MISSING", True, True, "PASS", "algebraic_only"),
        ("CAS_4AXIS_PASS", "FAIL", True, True, "PASS", "algebraic_only"),
        (
            "CAS_4AXIS_PASS",
            "PASS",
            True,
            True,
            "PASS",
            "constructive_constraint_and_admissibility_conditional",
        ),
        ("CAS_FAIL", "PASS", True, True, "FAIL", "none"),
        ("CAS_BLOCKED", "PASS", True, True, "BLOCKED", "none"),
        ("CAS_CONFLICT", "PASS", True, True, "BLOCKED", "none"),
        ("CAS_4AXIS_PASS", "PASS", False, True, "FAIL", "none"),
        ("CAS_4AXIS_PASS", "PASS", True, False, "FAIL", "none"),
    ],
)
def test_terminal_router_is_total_and_failure_precedence_is_fixed(
    cas_status: str,
    bundle: str,
    semantic: bool,
    artifact: bool,
    process: str,
    result: str,
) -> None:
    routed = route_terminal_result(
        cas_status,
        bundle,
        semantic_gate_pass=semantic,
        artifact_gate_pass=artifact,
    )
    assert routed["process_gate_status"] == process
    assert routed["scientific_result"] == result
    assert routed["public_use"] is False


def test_active_consumer_scan_passes_and_real_scanner_catches_mutation() -> None:
    runner = _runner_module()
    scan = runner.scan_active_consumers()
    assert scan["inventory_file_count"] >= 100
    assert scan["unresolved_active_claim_count"] == 0
    assert scan["pass"] is True
    mutated = runner.scan_active_consumers(
        extra_texts=(("mutation/claim.txt", "x_C=0 proves FLRW isotropy"),)
    )
    assert mutated["unresolved_active_claim_count"] == 1
    assert mutated["unresolved_active_claims"][0]["path"] == "mutation/claim.txt"


@pytest.mark.parametrize(
    "text",
    [
        "This is not a caveat: x_C=0 proves FLRW isotropy",
        "W_N2 is identical to V2",
        "V2 = W_N2",
        "x_C is a scalar measure of FLRW departure",
        "x_C constrains global anisotropy",
        "Vanishing tilt guarantees FLRW recovery",
    ],
)
def test_semantic_claim_mutations_cannot_hide_behind_nearby_language(text: str) -> None:
    runner = _runner_module()
    digest = hashlib.sha256(text.encode()).hexdigest()
    scan = runner.scan_active_consumers(
        extra_texts=(("mutation/semantic.txt", text),)
    )
    finding = next(
        row for row in scan["risk_findings"]
        if row["path"] == "mutation/semantic.txt" and row["file_sha256"] == digest
    )
    assert finding["classification"] == "active_claim"
    assert finding["disposition"] == "unresolved"


def test_refutation_is_match_local_and_backlog_has_no_blanket_exemption() -> None:
    runner = _runner_module()
    refuted = "x_C=0 does not prove FLRW isotropy"
    promoted = "x_C=0 proves FLRW isotropy"
    scan = runner.scan_active_consumers(
        extra_texts=(
            ("mutation/refuted.txt", refuted),
            ("docs/codex_handoff/pr_backlog.yaml", promoted),
        )
    )
    refuted_row = next(
        row for row in scan["risk_findings"]
        if row["path"] == "mutation/refuted.txt"
    )
    backlog_digest = hashlib.sha256(promoted.encode()).hexdigest()
    backlog_row = next(
        row for row in scan["risk_findings"]
        if row["path"] == "docs/codex_handoff/pr_backlog.yaml"
        and row["file_sha256"] == backlog_digest
    )
    assert refuted_row["classification"] == "explicit_refutation"
    assert backlog_row["classification"] == "active_claim"


def test_consumer_classification_schema_rejects_missing_unknown_and_mismatch() -> None:
    runner = _runner_module()
    base = {
        "finding_kind": "signed_scalar_isotropy_promotion",
        "path": "mutation/schema.txt",
        "file_sha256": "a" * 64,
        "line": 1,
        "text_sha256": "b" * 64,
        "classification": "active_claim",
        "disposition": "unresolved",
    }
    runner.validate_consumer_records([base])
    missing = dict(base)
    missing.pop("classification")
    unknown = dict(base, classification="unknown")
    missing_disposition = dict(base)
    missing_disposition.pop("disposition")
    unknown_disposition = dict(base, disposition="unknown")
    mismatch = dict(base, disposition="allowed_guard_surface")
    for mutation in (
        missing,
        unknown,
        missing_disposition,
        unknown_disposition,
        mismatch,
    ):
        with pytest.raises(ValueError):
            runner.validate_consumer_records([mutation])


def test_cas_collector_rejects_forged_or_incomplete_evidence() -> None:
    collector, config, contract, assignment, outer = _axis_bundle("v2", "sympy")

    forged_assignment = deepcopy(assignment)
    forged_assignment["task"] = "forged without resealing"
    with pytest.raises(ValueError, match="self-hash mismatch"):
        collector._validate_axis_evidence(
            "v2", config, contract, "sympy", forged_assignment, outer
        )

    bad_outer = deepcopy(outer)
    bad_outer["status"] = "error"
    with pytest.raises(ValueError, match="outer status"):
        collector._validate_axis_evidence(
            "v2", config, contract, "sympy", assignment, bad_outer
        )

    missing_obligation = deepcopy(outer)
    missing_obligation["payload"]["cas_axis_result"]["checks"].pop(
        "full_ceiling_attained"
    )
    with pytest.raises(ValueError, match="obligations incomplete"):
        collector._validate_axis_evidence(
            "v2", config, contract, "sympy", assignment, missing_obligation
        )

    drifted_input = deepcopy(assignment)
    runner_ref = next(
        row for row in drifted_input["required_inputs"]
        if row["path"] == "scripts/codex_harness/run_pr169_axis_v2.py"
    )
    runner_ref["sha256"] = "f" * 64
    _reseal_assignment(collector, drifted_input)
    with pytest.raises(ValueError, match="required input drift"):
        collector._validate_axis_evidence(
            "v2", config, contract, "sympy", drifted_input, outer
        )


def test_current_results_table_has_scoped_vorticity_zero_column() -> None:
    table = _json(GENERATED / "egs_results_table_v9.json")
    row = next(row for row in table["rows"] if row["theorem_id"] == "EGS3-A1")
    assert "registered response map" in row["key_result"]
    assert "full vorticity transfer" in row["key_result"]
    assert "order-independent" not in row["key_result"]
    assert "Weyl-blind" not in row["key_result"]


def test_candidate_card_is_hash_bound_and_superseded_without_rewrite() -> None:
    receipt = _json(GENERATED / "pr169_candidate_branch_supersession.json")
    runner = _runner_module()
    backlog = yaml.safe_load(
        (REPO / "docs/codex_handoff/pr_backlog.yaml").read_text(encoding="utf-8")
    )
    card = runner._find_card(backlog, "PR-169")
    assert receipt["authoritative_card"]["card_semantic_sha256"] == (
        runner.semantic_sha256(card)
    )
    assert receipt["authoritative_card"]["card_rewritten"] is False
    assert receipt["kill_switch_activated"] is True
    assert receipt["disposition"].endswith("algebraic_only_result")


def test_historical_result_manifest_hashes_and_metadata_are_exact() -> None:
    manifest = _json(GENERATED / "pr169_artifact_manifest.json")
    card = _json(GENERATED / "pr169_result_card.json")
    assert manifest["scientific_result"] == "algebraic_only"
    assert manifest["cas_aggregate"] == "CAS_4AXIS_PASS"
    assert manifest["physical_bundle_status"] == "MISSING"
    assert card["result_status"] == "ALGEBRAIC_ONLY_EXACT_COMPARATOR_RESULT"
    assert card["family_identification"] is False
    assert card["native_solver_validation"] is False
    for path, expected in manifest["artifact_hashes"].items():
        assert _sha(REPO / path) == expected

    runner = _runner_module()
    for key in runner.REQUIRED_METADATA:
        assert key in manifest
        assert key in card


def test_historical_closeout_preserves_failures_and_binds_remediation() -> None:
    receipt = _json(GENERATED / "pr169_closeout_review_receipt.json")
    assert receipt["review_verdicts_preserved"] == {
        "science_claim": "fail",
        "harness_code": "FAIL_P1",
    }
    assert all(
        row["status"] == "remediated"
        for row in receipt["finding_resolutions"]
    )
    current_authority_surfaces = {
        "scripts/codex_harness/collect_pr169_cas_receipts.py",
        "scripts/codex_harness/run_pr169_unsigned_leakage.py",
        "tests/pr_cards/test_pr_169_unsigned_isotropy_leakage_ceiling_m_max_nilsson_.py",
    }
    for group in ("review_inputs", "remediated_surface_hashes"):
        for path, expected in receipt[group].items():
            assert len(expected) == 64
            if path not in current_authority_surfaces:
                assert _sha(REPO / path) == expected
    terminal = receipt["terminal_adjudication"]
    assert terminal["process_gate_status"] == "PASS"
    assert terminal["scientific_result"] == "algebraic_only"
    assert terminal["physical_promotion"] is False
    assert terminal["public_use"] is False


def test_historical_checks_remain_currently_cas_blocked() -> None:
    collector = subprocess.run(
        [
            sys.executable,
            "-B",
            "scripts/codex_harness/collect_pr169_cas_receipts.py",
            "--check",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    assert collector.returncode == 2, collector.stdout + collector.stderr
    collector_receipt = json.loads(collector.stdout)
    assert collector_receipt["current_aggregate"] == "CAS_BLOCKED"
    assert collector_receipt["historical_aggregates"] == {
        "v1": "CAS_FAIL",
        "v2": "CAS_4AXIS_PASS",
    }
    assert collector_receipt["claim_promotion_cas_eligible"] is False

    runner = subprocess.run(
        [
            sys.executable,
            "-B",
            "scripts/codex_harness/run_pr169_unsigned_leakage.py",
            "--check",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    assert runner.returncode == 2, runner.stdout + runner.stderr
    runner_receipt = json.loads(runner.stdout)
    assert runner_receipt["cas_aggregate"] == "CAS_BLOCKED"
    assert runner_receipt["scientific_result"] == "none"
    assert runner_receipt["claim_promotion_cas_eligible"] is False


def test_write_refuses_to_replace_frozen_result_pack() -> None:
    paths = [
        *sorted(GENERATED.glob("pr169_*.json")),
        *sorted((GENERATED / "pr169_cas").rglob("*.json")),
    ]
    before = {path: _sha(path) for path in paths}
    for command in (
        [
            sys.executable,
            "-B",
            "scripts/codex_harness/collect_pr169_cas_receipts.py",
        ],
        [
            sys.executable,
            "-B",
            "scripts/codex_harness/run_pr169_unsigned_leakage.py",
            "--write",
        ],
    ):
        completed = subprocess.run(
            command,
            cwd=REPO,
            text=True,
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 2
        assert "refusing to overwrite" in completed.stderr
    assert {path: _sha(path) for path in paths} == before


def test_mutation_report_has_no_survivors() -> None:
    report = _json(GENERATED / "pr169_mutation_report.json")
    assert report["surviving_mutation_count"] == 0
    assert report["survivors"] == []
    assert all(row["detected"] for row in report["mutations"])
