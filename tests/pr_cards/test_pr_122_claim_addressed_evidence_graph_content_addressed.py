from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
import yaml

from common.evidence_graph import (
    EvidenceAxes,
    EvidenceGraph,
    EvidenceGraphError,
    EvidenceNode,
    EvidenceNodeKind,
    EvidenceStatus,
    ProcessResult,
    TestExecution,
)
from common.mes_successor_registry import (
    MesConsumerIssueCode,
    finding_codes,
    scan_declared_mes_consumers,
)
from common.remediation_state import ScientificStatus


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC = REPO_ROOT / "docs/research_program/long_horizon_rescue/pr122_spec.yaml"
GRAPH = REPO_ROOT / "docs/generated/pr122_claim_evidence_graph.json"
TEST_EXECUTION = REPO_ROOT / "docs/generated/pr122_test_execution.json"
PR121_RECEIPT = REPO_ROOT / "docs/generated/pr121_hermetic_replay_receipt.json"
ARTIFACT_MANIFEST = REPO_ROOT / "docs/generated/pr122_artifact_manifest.json"
SCRIPT = REPO_ROOT / "scripts/codex_harness/build_claim_evidence_graph.py"
SOURCE_ONLY_LAUNCHER = REPO_ROOT / "scripts/codex_harness/run_pr122_source_only.sh"
AUTHORITY_SNAPSHOT = (
    REPO_ROOT
    / "docs/research_program/long_horizon_rescue/pr122_authority_snapshot.yaml"
)


def _load_builder():
    spec = importlib.util.spec_from_file_location("pr122_graph_builder", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_spec_registers_every_required_false_green_mutation_and_pr4_firewall() -> None:
    payload = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    mutations = set(payload["mutations"])
    assert {
        "nonexistent_python_selector",
        "zero_collected_python_selector",
        "zero_collected_rust_selector",
        "setup_or_teardown_failure_laundering",
        "stale_generator",
        "artifact_hash_mismatch",
        "invalid_manifest",
        "process_pass_with_blocked_science",
        "fabricated_or_unknown_principal",
        "unknown_authority_snapshot_schema",
        "self_signed_receipt",
        "author_equals_adjudicator",
        "self_or_circular_parent",
        "graph_dependency_cycle",
        "stale_mes_triple_or_registry_bypass",
        "arbitrary_ready_for_claims_object",
        "caller_supplied_pseudo_ppc_or_bayes_scalar",
    } <= mutations
    assert payload["claim_level"] == {
        "scheme": "roadmap_rescue_v1",
        "level": "C1",
    }
    assert payload["scientific_effect"] == "none"
    assert payload["data_scope"]["pr4_download"] == "not_started"
    assert payload["data_scope"]["pr4_data_work"] == "skip_entirely_by_user_scope"
    matrix = payload["mutation_execution_matrix"]
    assert {row["mutation_id"] for row in matrix} == mutations
    assert all(
        row["expected_outcome"] == "PASSED_REJECTION_OR_EXPLICIT_DOWNCLAIM"
        and row["test_node_id"].startswith("tests/")
        for row in matrix
    )


def test_process_pass_and_blocked_evidence_are_orthogonal_not_promoted() -> None:
    axes = EvidenceAxes(
        ProcessResult.PASS,
        EvidenceStatus.BLOCKED,
        ScientificStatus.OPEN,
    )
    assert axes.process_result is ProcessResult.PASS
    assert axes.evidence_status is EvidenceStatus.BLOCKED
    assert axes.scientific_status is ScientificStatus.OPEN


def test_arbitrary_readiness_field_is_rejected_at_graph_boundary() -> None:
    with pytest.raises(EvidenceGraphError, match="readiness field"):
        EvidenceNode(
            kind=EvidenceNodeKind.INPUT,
            label="spoof",
            content_sha256="1" * 64,
            axes=EvidenceAxes(
                ProcessResult.PASS,
                EvidenceStatus.PRESENT,
                ScientificStatus.OPEN,
            ),
            metadata={"ready_for_claims": True},
        )


def test_pytest_receipt_count_or_identity_spoof_is_rejected() -> None:
    payload = json.loads(TEST_EXECUTION.read_text(encoding="utf-8"))
    assert TestExecution.from_pytest_evidence(payload).is_authoritative is True

    count_spoof = copy.deepcopy(payload)
    count_spoof["counts"]["executed"] += 1
    unsigned = dict(count_spoof)
    unsigned.pop("content_sha256")
    count_spoof["content_sha256"] = hashlib.sha256(
        json.dumps(
            unsigned,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    with pytest.raises(EvidenceGraphError, match="count executed"):
        TestExecution.from_pytest_evidence(count_spoof)


def test_current_mes_all_consumer_scan_is_integrity_clean_but_release_blocked() -> None:
    builder = _load_builder()
    declarations = builder._mes_declarations(
        REPO_ROOT,
        REPO_ROOT
        / "docs/research_program/long_horizon_rescue/pr122_active_mes_consumers.yaml",
    )
    report = scan_declared_mes_consumers(REPO_ROOT, declarations)
    codes = finding_codes(report)
    assert report.consumers_scanned == len(declarations) >= 10
    assert MesConsumerIssueCode.SUCCESSOR_MISSING.value in codes
    assert MesConsumerIssueCode.SCIENTIFIC_AUTHORITY_BLOCKED.value in codes
    assert MesConsumerIssueCode.SUCCESSOR_POINTER_MISSING.value in codes
    assert MesConsumerIssueCode.SOURCE_HASH_MISMATCH.value not in codes
    assert report.release_allowed is False


def test_checked_in_graph_has_clean_mechanics_and_blocked_release_claims() -> None:
    graph = EvidenceGraph.from_record(json.loads(GRAPH.read_text(encoding="utf-8")))
    claims = {
        node.label: graph.closure(node.node_ref)
        for node in graph.nodes
        if node.kind is EvidenceNodeKind.CLAIM
    }
    assert claims["pr122.fail_closed_mechanics"].mechanics_closed is True
    blocked = claims["pr122.mes_release_authority"]
    assert blocked.process_result is ProcessResult.PASS
    assert blocked.evidence_status is EvidenceStatus.BLOCKED
    assert blocked.package_eligible is False
    d2 = claims["pr122.d2_rust_authority"]
    assert d2.process_result is ProcessResult.NOT_RUN
    assert d2.evidence_status is EvidenceStatus.BLOCKED
    assert d2.claim_release_eligible is False


def test_checked_in_graph_content_addresses_its_own_generator() -> None:
    graph = EvidenceGraph.from_record(json.loads(GRAPH.read_text(encoding="utf-8")))
    generator = next(
        node
        for node in graph.nodes
        if node.label == "codex_harness.build_claim_evidence_graph"
    )
    assert generator.kind is EvidenceNodeKind.PRODUCER
    assert generator.metadata["path"] == (
        "scripts/codex_harness/build_claim_evidence_graph.py"
    )
    assert generator.content_sha256 == hashlib.sha256(SCRIPT.read_bytes()).hexdigest()

    path_bound = {
        node.label: node
        for node in graph.nodes
        if isinstance(node.metadata.get("path"), str)
    }
    for label, relative in {
        "common.release_evidence_binding": "htt/src/common/release_evidence_binding.py",
        "common.pytest_execution_evidence": "htt/src/common/pytest_execution_evidence.py",
        "codex_harness.pr122_source_only_launcher": (
            "scripts/codex_harness/run_pr122_source_only.sh"
        ),
        "pr122_authority_snapshot": (
            "docs/research_program/long_horizon_rescue/" "pr122_authority_snapshot.yaml"
        ),
    }.items():
        node = path_bound[label]
        source = REPO_ROOT / relative
        assert node.metadata["path"] == relative
        assert node.content_sha256 == hashlib.sha256(source.read_bytes()).hexdigest()
    assert "status_snapshot" not in path_bound
    assert "inference_adequacy" not in path_bound


def test_pr122_authority_snapshot_is_an_immutable_exact_scope_slice(
    tmp_path: Path,
) -> None:
    builder = _load_builder()
    payload = yaml.safe_load(AUTHORITY_SNAPSHOT.read_text(encoding="utf-8"))
    registry = builder._authority_registry(AUTHORITY_SNAPSHOT)
    builder._validate_authority_snapshot(payload, registry)

    assert payload["immutable"] is True
    assert payload["scope"] == "PR-122"
    assert {row["principal_id"] for row in payload["principals"]} == {
        builder.AUTHOR,
        builder.ADJUDICATOR,
    }
    assert all(row["allowed_scopes"] == ["PR-122"] for row in payload["principals"])
    assert all(
        row["can_promote_scientific_status"] is False for row in payload["principals"]
    )

    broadened = copy.deepcopy(payload)
    broadened["principals"][0]["allowed_scopes"].append("PR-123")
    with pytest.raises(ValueError, match="broadens principal authority"):
        builder._validate_authority_snapshot(broadened, registry)

    for schema in (None, "htt.pr122.authority_snapshot.v2"):
        invalid = copy.deepcopy(payload)
        if schema is None:
            invalid.pop("schema")
        else:
            invalid["schema"] = schema
        invalid_path = tmp_path / f"authority-{schema or 'missing'}.yaml"
        invalid_path.write_text(
            yaml.safe_dump(invalid, sort_keys=False),
            encoding="utf-8",
        )
        with pytest.raises(
            ValueError,
            match="unsupported PR-122 authority snapshot schema",
        ):
            builder._authority_registry(invalid_path)


def test_failed_or_tampered_pr121_environment_receipt_is_rejected() -> None:
    builder = _load_builder()
    payload = json.loads(PR121_RECEIPT.read_text(encoding="utf-8"))
    builder._validate_pr121_environment_receipt(payload)

    failed = copy.deepcopy(payload)
    failed["overall_status"] = "failed"
    unsigned = {
        key: value for key, value in failed.items() if key != "receipt_content_hash"
    }
    failed["receipt_content_hash"] = hashlib.sha256(
        json.dumps(
            unsigned,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    with pytest.raises(EvidenceGraphError, match="not completed-success"):
        builder._validate_pr121_environment_receipt(failed)

    malformed = copy.deepcopy(payload)
    malformed["receipt_content_hash"] = "0" * 64
    with pytest.raises(EvidenceGraphError, match="content hash is invalid"):
        builder._validate_pr121_environment_receipt(malformed)


def test_pr122_artifact_manifest_covers_every_generated_output() -> None:
    payload = json.loads(ARTIFACT_MANIFEST.read_text(encoding="utf-8"))
    assert payload["schema"] == "htt.pr122.artifact_manifest.v1"
    paths = {row["path"] for row in payload["artifacts"]}
    assert {
        "docs/generated/pr122_claim_evidence_graph.json",
        "docs/generated/pr122_claim_closure_report.json",
        "docs/generated/pr122_claim_closure_report.md",
        "docs/generated/pr122_release_receipt.json",
        "docs/generated/pr122_parent_receipt.json",
        "docs/generated/pr122_mes_successor_scan.json",
        "docs/generated/pr122_test_execution.json",
    } <= paths
    assert payload["git_commit_or_worktree_state"].startswith("HEAD:")
