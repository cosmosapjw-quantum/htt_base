from __future__ import annotations

import copy
from collections import Counter
from pathlib import Path
import subprocess
import sys

import pytest

from common.evidence_graph import EvidenceEdge, EvidenceEdgeKind, EvidenceGraph
from common.pr_retrace import (
    DataArtifactDisposition,
    RetraceContractError,
    RetraceDisposition,
    canonical_json_sha256,
    load_yaml_mapping,
    normalize_legacy_disposition,
    parse_legacy_actions,
    validate_data_artifact_inventory,
    validate_data_runbooks,
    validate_failure_debt,
    validate_github_index,
    validate_internal_ledger,
    validate_output_metadata,
    validate_recompute_matrix,
    validate_semantic_invalidation_graph,
    validate_source_snapshot,
    validate_supersession_map,
)


ROOT = Path(__file__).resolve().parents[2]
PROGRAM = ROOT / "docs/research_program/post_pr275"
SPEC = PROGRAM / "pr279_spec.yaml"
BACKLOG = ROOT / "docs/codex_handoff/pr_backlog.yaml"
STATUS = ROOT / "docs/codex_handoff/pr_status.yaml"
RUNNER = ROOT / "scripts/codex_harness/run_pr279_reverse_trace.py"
OUTPUTS = {
    "snapshot": PROGRAM / "pr279_source_snapshot.yaml",
    "ledger": PROGRAM / "PR_RETRACE_LEDGER.yaml",
    "github": PROGRAM / "github_publication_review_index.yaml",
    "graph": PROGRAM / "semantic_invalidation_graph.yaml",
    "supersession": PROGRAM / "supersession_map.yaml",
    "recompute": PROGRAM / "recompute_matrix.yaml",
    "failure_debt": PROGRAM / "failure_debt.yaml",
    "runbooks": PROGRAM / "data_runbooks.yaml",
    "inventory": PROGRAM / "data_artifact_disposition.yaml",
}


@pytest.fixture(scope="module")
def documents() -> dict[str, dict[str, object]]:
    return {key: load_yaml_mapping(path) for key, path in OUTPUTS.items()}


@pytest.fixture(scope="module")
def spec() -> dict[str, object]:
    return load_yaml_mapping(SPEC)


@pytest.fixture(scope="module")
def backlog() -> dict[str, object]:
    return load_yaml_mapping(BACKLOG)


@pytest.fixture(scope="module")
def status() -> dict[str, object]:
    return load_yaml_mapping(STATUS)


def test_portable_snapshot_reconstructs_all_registered_sources(
    documents: dict[str, dict[str, object]], spec: dict[str, object]
) -> None:
    snapshot = documents["snapshot"]
    validate_source_snapshot(snapshot, spec=spec)
    sources = snapshot["sources"]
    assert isinstance(sources, dict)
    assert sources["internal_inventory"]["sha256"] == (
        "7d7c62a08c6a6d175827e0fcb123c3ecdc758b9e25984e279bf9022d47751301"
    )
    assert sources["github_inventory"]["sha256"] == (
        "4aba19685b7e41c9efa14de1a942ae82f0765710902d67206d5bb4be6b685e84"
    )
    assert sources["redo_campaign"]["sha256"] == (
        "5cd35f64025122832f1c9242a0671393d6fc30c79c798e10e82655ab529c0453"
    )
    assert len(snapshot["data_group_normalization"]["groups"]) == 45


def test_portable_snapshot_rejects_self_rehashed_group_mutation(
    documents: dict[str, dict[str, object]], spec: dict[str, object]
) -> None:
    changed = copy.deepcopy(documents["snapshot"])
    grouping = changed["data_group_normalization"]
    grouping["groups"][0]["name"] = "mutated self-consistent group"
    grouping["groups_semantic_sha256"] = canonical_json_sha256(grouping["groups"])
    with pytest.raises(RetraceContractError):
        validate_source_snapshot(changed, spec=spec)


def test_portable_snapshot_rejects_redo_payload_self_rehash(
    documents: dict[str, dict[str, object]], spec: dict[str, object]
) -> None:
    changed = copy.deepcopy(documents["snapshot"])
    redo = changed["sources"]["redo_campaign"]
    redo["normalized_semantic_payload"]["claim_posture"] = (
        "NATIVE_FAMILY_IDENTIFIED"
    )
    redo["normalized_semantic_sha256"] = canonical_json_sha256(
        redo["normalized_semantic_payload"]
    )
    with pytest.raises(RetraceContractError):
        validate_source_snapshot(changed, spec=spec)


@pytest.mark.parametrize(
    "mutation",
    ["public_ceiling", "owner_transfer_sources"],
)
def test_portable_snapshot_rejects_claim_or_source_metadata_rewrite(
    documents: dict[str, dict[str, object]],
    spec: dict[str, object],
    mutation: str,
) -> None:
    changed = copy.deepcopy(documents["snapshot"])
    if mutation == "public_ceiling":
        changed["claim_tier_ceiling"] = "PUBLIC_RELEASE"
    else:
        changed["owner"] = "HTT"
        changed["transfer_source"] = "external transfer validated as native"
        changed["source_identities"] = []
    with pytest.raises(RetraceContractError):
        validate_source_snapshot(changed, spec=spec)


def test_internal_222_and_prospective_19_are_exact_and_separate(
    documents: dict[str, dict[str, object]],
    spec: dict[str, object],
    backlog: dict[str, object],
    status: dict[str, object],
) -> None:
    ledger = documents["ledger"]
    validate_internal_ledger(
        ledger,
        snapshot=documents["snapshot"],
        spec=spec,
        backlog=backlog,
        status=status,
    )
    historical = ledger["historical_internal_work_units"]
    prospective = ledger["prospective_post275_work_units"]
    historical_ids = [row["internal_pr_id"] for row in historical]
    prospective_ids = [row["internal_pr_id"] for row in prospective]
    assert len(historical_ids) == len(set(historical_ids)) == 222
    assert len(prospective_ids) == len(set(prospective_ids)) == 19
    assert set(historical_ids).isdisjoint(prospective_ids)
    assert prospective_ids == [f"PR-{number:03d}" for number in range(276, 295)]
    assert {
        row["internal_pr_id"]
        for row in historical
        if row["status_drifted_from_source"]
    } == {"PR-151", "PR-190"}


@pytest.mark.parametrize(
    "mutation",
    ["summary", "public_metadata", "erased_sources"],
)
def test_internal_ledger_rejects_summary_or_claim_metadata_rewrite(
    documents: dict[str, dict[str, object]],
    spec: dict[str, object],
    backlog: dict[str, object],
    status: dict[str, object],
    mutation: str,
) -> None:
    changed = copy.deepcopy(documents["ledger"])
    if mutation == "summary":
        changed["summary"]["orphan_work_unit_count"] = 222
    elif mutation == "public_metadata":
        changed["owner"] = "MIO"
        changed["claim_tier_ceiling"] = "PUBLIC_RELEASE"
        changed["transfer_source"] = "external transfer validated as native"
    else:
        changed["source_identities"] = []
    with pytest.raises(RetraceContractError):
        validate_internal_ledger(
            changed,
            snapshot=documents["snapshot"],
            spec=spec,
            backlog=backlog,
            status=status,
        )


def test_github_366_uses_a_distinct_identity_space(
    documents: dict[str, dict[str, object]], spec: dict[str, object]
) -> None:
    index = documents["github"]
    validate_github_index(index, snapshot=documents["snapshot"], spec=spec)
    ids = [row["github_record_id"] for row in index["records"]]
    assert len(ids) == len(set(ids)) == 366
    assert ids[0] == "GITHUB-PR-0002"
    assert ids[-1] == "GITHUB-PR-0367"
    assert not any(value.startswith("PR-") for value in ids)


@pytest.mark.parametrize(
    "mutation",
    ["summary", "identity_space", "public_metadata"],
)
def test_github_index_rejects_conflation_or_claim_metadata_rewrite(
    documents: dict[str, dict[str, object]],
    spec: dict[str, object],
    mutation: str,
) -> None:
    changed = copy.deepcopy(documents["github"])
    if mutation == "summary":
        changed["summary"]["internal_identity_conflation_count"] = 366
    elif mutation == "identity_space":
        changed["identity_space"] = "internal_work_unit"
    else:
        changed["owner"] = "HTT"
        changed["claim_tier_ceiling"] = "PUBLIC_RELEASE"
        changed["source_identities"] = []
    with pytest.raises(RetraceContractError):
        validate_github_index(
            changed, snapshot=documents["snapshot"], spec=spec
        )


def test_legacy_grammar_is_lossless_for_all_rows_and_23_prefixes(
    documents: dict[str, dict[str, object]], spec: dict[str, object]
) -> None:
    rows = documents["snapshot"]["sources"]["internal_inventory"]["rows"]
    prefix_rows = 0
    for row in rows:
        source = row["disposition"]
        actions = parse_legacy_actions(source)
        normalized = normalize_legacy_disposition(
            source, spec, pr_id=row["pr_id"]
        )
        assert normalized.legacy_disposition == source
        assert normalized.legacy_actions == actions
        assert normalized.normalized_dispositions
        if source.startswith(("REBASE_THEN_", "RESUME_COMPLETE_THEN_")):
            prefix_rows += 1
    assert prefix_rows == 23
    with pytest.raises(RetraceContractError):
        parse_legacy_actions("REBASE_THEN_UNKNOWN_ACTION")


def test_exact_eleven_dispositions_and_total_recompute_routes(
    documents: dict[str, dict[str, object]]
) -> None:
    assert len(RetraceDisposition) == 11
    matrix = documents["recompute"]
    validate_recompute_matrix(
        matrix, ledger=documents["ledger"], inventory=documents["inventory"]
    )
    assert {row["disposition"] for row in matrix["routes"]} == {
        item.value for item in RetraceDisposition
    }
    assert all(
        row["routing_root_hints_are_authority"] is False
        for row in matrix["historical_work_units"]
    )


@pytest.mark.parametrize("section", ["historical_work_units", "data_artifacts"])
def test_recompute_matrix_rejects_duplicate_object_routes(
    documents: dict[str, dict[str, object]], section: str
) -> None:
    changed = copy.deepcopy(documents["recompute"])
    identity = "internal_pr_id" if section == "historical_work_units" else "artifact_id"
    changed[section][1][identity] = changed[section][0][identity]
    with pytest.raises(RetraceContractError):
        validate_recompute_matrix(
            changed,
            ledger=documents["ledger"],
            inventory=documents["inventory"],
        )


def test_recompute_matrix_rejects_unknown_historical_work_unit(
    documents: dict[str, dict[str, object]]
) -> None:
    changed = copy.deepcopy(documents["recompute"])
    changed["historical_work_units"][0]["internal_pr_id"] = "PR-999"
    with pytest.raises(RetraceContractError):
        validate_recompute_matrix(
            changed,
            ledger=documents["ledger"],
            inventory=documents["inventory"],
        )


def test_typed_lifecycle_graph_has_exact_roots_and_no_pr_title_edges(
    documents: dict[str, dict[str, object]], spec: dict[str, object]
) -> None:
    document = documents["graph"]
    validate_semantic_invalidation_graph(
        document,
        repo_root=ROOT,
        spec=spec,
        ledger=documents["ledger"],
        inventory=documents["inventory"],
    )
    graph = EvidenceGraph.from_record(document["typed_lifecycle_graph"])
    assert len(document["root_index"]) == 12
    dormant = [
        row
        for row in document["root_index"]
        if row["current_activation"] == "DORMANT_NO_CURRENT_TARGETS"
    ]
    assert [row["root_id"] for row in dormant] == ["ROOT-THEOREM-REGISTRY-V3"]
    assert dormant[0]["target_node_refs"] == []
    assert dormant[0]["edge_refs"] == []
    assert len(graph.edges) == document["summary"]["lifecycle_edge_count"]
    assert {
        edge.kind for edge in graph.edges
    } == {
        EvidenceEdgeKind.REQUIRES_RECALIBRATION,
        EvidenceEdgeKind.REQUIRES_REEXECUTION,
    }
    assert all(
        set(edge.metadata) == {"affected_capabilities", "reason_ref"}
        for edge in graph.edges
    )
    routing = document["routing_projection"]
    assert all(
        relation["kind"] in {"ROUTED_TO", "CONSUMED_BY"}
        for relation in routing["relations"]
    )
    assert document["capability_issuance"] == "forbidden"


@pytest.mark.parametrize("mutation", ["orphan", "missing_reason"])
def test_typed_lifecycle_mutations_fail_closed(
    documents: dict[str, dict[str, object]],
    spec: dict[str, object],
    mutation: str,
) -> None:
    changed = copy.deepcopy(documents["graph"])
    edge = changed["typed_lifecycle_graph"]["edges"][0]
    if mutation == "orphan":
        edge["target_ref"] = "0" * 64
    else:
        edge["metadata"].pop("reason_ref")
    with pytest.raises(RetraceContractError):
        validate_semantic_invalidation_graph(
            changed,
            repo_root=ROOT,
            spec=spec,
            ledger=documents["ledger"],
            inventory=documents["inventory"],
        )


def test_unindexed_typed_lifecycle_edge_fails_closed(
    documents: dict[str, dict[str, object]], spec: dict[str, object]
) -> None:
    changed = copy.deepcopy(documents["graph"])
    graph = EvidenceGraph.from_record(changed["typed_lifecycle_graph"])
    targets = [
        node
        for node in graph.nodes
        if str(node.metadata.get("artifact_id", "")).startswith("DATA-ART-")
    ]
    injected = EvidenceEdge(
        kind=EvidenceEdgeKind.REQUIRES_RECALIBRATION,
        source_ref=targets[0].node_ref,
        target_ref=targets[1].node_ref,
        metadata={
            "affected_capabilities": ["PUBLIC_RELEASE"],
            "reason_ref": targets[0].content_sha256,
        },
    )
    changed["typed_lifecycle_graph"]["edges"].append(injected.to_record())
    changed["summary"]["lifecycle_edge_count"] += 1
    with pytest.raises(RetraceContractError):
        validate_semantic_invalidation_graph(
            changed,
            repo_root=ROOT,
            spec=spec,
            ledger=documents["ledger"],
            inventory=documents["inventory"],
        )


def test_data_inventory_exactization_and_direct_falsification_boundary(
    documents: dict[str, dict[str, object]], spec: dict[str, object]
) -> None:
    inventory = documents["inventory"]
    validate_data_artifact_inventory(
        inventory,
        repo_root=ROOT,
        spec=spec,
        snapshot=documents["snapshot"],
    )
    assert Counter(row["disposition"] for row in inventory["artifacts"]) == {
        DataArtifactDisposition.REDO_REQUIRED.value: 20,
        DataArtifactDisposition.REDO_UPGRADE.value: 14,
        DataArtifactDisposition.PRESERVE.value: 5,
        DataArtifactDisposition.BLOCKED.value: 6,
    }
    direct = [
        row
        for row in inventory["artifacts"]
        if row["disposition_basis"] == "direct_registered_falsification"
    ]
    assert [row["source_group_id"] for row in direct] == ["DA-R01"]
    nonmaterialized = [row for row in inventory["artifacts"] if not row["materialized"]]
    assert [row["source_group_id"] for row in nonmaterialized] == ["DA-B02"]
    preserved = [
        row for row in inventory["artifacts"] if row["disposition"] == "PRESERVE"
    ]
    assert all(not row["invalidation_roots"] for row in preserved)
    mes_seal = next(
        row for row in preserved if row["source_group_id"] == "DA-P04"
    )
    assert mes_seal["normalized_dispositions"] == ["STABLE_REPLAY"]


def test_unknown_data_disposition_is_rejected(
    documents: dict[str, dict[str, object]], spec: dict[str, object]
) -> None:
    changed = copy.deepcopy(documents["inventory"])
    changed["artifacts"][0]["disposition"] = "READY_FOR_PUBLICATION"
    with pytest.raises(RetraceContractError):
        validate_data_artifact_inventory(
            changed,
            repo_root=ROOT,
            spec=spec,
            snapshot=documents["snapshot"],
        )


def test_data_inventory_summary_or_claim_promotion_is_rejected(
    documents: dict[str, dict[str, object]], spec: dict[str, object]
) -> None:
    changed = copy.deepcopy(documents["inventory"])
    changed["artifacts"][0]["claim_ceiling"] = "PUBLIC_RELEASE"
    changed["summary"]["counts"]["REDO_UPGRADE"] += 1
    with pytest.raises(RetraceContractError):
        validate_data_artifact_inventory(
            changed,
            repo_root=ROOT,
            spec=spec,
            snapshot=documents["snapshot"],
        )


def test_supersession_preserves_history_and_withholds_hash_conflict(
    documents: dict[str, dict[str, object]]
) -> None:
    document = documents["supersession"]
    validate_supersession_map(document, repo_root=ROOT)
    graph = EvidenceGraph.from_record(document["typed_supersession_graph"])
    assert len(graph.edges) == 5
    assert all(edge.kind is EvidenceEdgeKind.SUPERSEDED_BY for edge in graph.edges)
    withheld = document["withheld_relations"]
    assert [row["relation_id"] for row in withheld] == [
        "WITHHELD-PR248-PR252-HASH-CONTRADICTION"
    ]
    assert withheld[0]["pinned_migration_sha256"] != withheld[0][
        "current_migration_sha256"
    ]
    assert document["preserved_falsified_history"][0]["historical_pr"] == "PR-190"
    assert document["preserved_falsified_history"][0]["successor"] is None


def test_supersession_relation_cannot_point_at_a_different_typed_edge(
    documents: dict[str, dict[str, object]]
) -> None:
    changed = copy.deepcopy(documents["supersession"])
    changed["relations"][0]["edge_ref"] = changed["relations"][1]["edge_ref"]
    with pytest.raises(RetraceContractError):
        validate_supersession_map(changed, repo_root=ROOT)


def test_supersession_relation_ids_are_exact_and_unique(
    documents: dict[str, dict[str, object]]
) -> None:
    changed = copy.deepcopy(documents["supersession"])
    changed["relations"][1]["relation_id"] = changed["relations"][0]["relation_id"]
    with pytest.raises(RetraceContractError):
        validate_supersession_map(changed, repo_root=ROOT)


@pytest.mark.parametrize("section", ["preserved_falsified_history", "related_invalidations"])
def test_supersession_auxiliary_history_is_exact(
    documents: dict[str, dict[str, object]], section: str
) -> None:
    changed = copy.deepcopy(documents["supersession"])
    row = changed[section][0]
    if section == "preserved_falsified_history":
        row["historical_pr"] = "PR-999"
        row["disposition"] = "STABLE_REPLAY"
    else:
        row["historical_pr"] = "PR-999"
        row["relation"] = "SUPERSEDED_BY"
        row["reason_ref"] = "0" * 64
    with pytest.raises(RetraceContractError):
        validate_supersession_map(changed, repo_root=ROOT)


def test_failure_debt_is_typed_and_act_dependency_is_not_misreported(
    documents: dict[str, dict[str, object]], backlog: dict[str, object]
) -> None:
    debt = documents["failure_debt"]
    validate_failure_debt(
        debt, backlog=backlog, inventory=documents["inventory"]
    )
    rows = {row["debt_id"]: row for row in debt["rows"]}
    assert len(rows["DEBT-NATIVE-SOLVER-ATLAS"]["affected_prs"]) == 18
    assert "PR-289" in backlog["policy"]["dependency_overlays"]["additions"]["PR-204"]
    assert "consumes PR-289" in rows["DEBT-ACT-ADMISSION-AUTHORIZATION"]["effect"]
    assert rows["DEBT-PR248-PR252-HASH-CONTRADICTION"]["next_work_unit"] is None


def test_failure_debt_exact_projection_rejects_summary_rewrite(
    documents: dict[str, dict[str, object]], backlog: dict[str, object]
) -> None:
    changed = copy.deepcopy(documents["failure_debt"])
    changed["summary"]["open_count"] = 0
    with pytest.raises(RetraceContractError):
        validate_failure_debt(
            changed,
            backlog=backlog,
            inventory=documents["inventory"],
        )


def test_seven_runbooks_separate_admission_authorization_and_ownership(
    documents: dict[str, dict[str, object]], backlog: dict[str, object]
) -> None:
    runbooks = documents["runbooks"]
    validate_data_runbooks(runbooks, backlog=backlog)
    assert len(runbooks["runbooks"]) == 7
    for row in runbooks["runbooks"]:
        assert row["admission_is_execution_authorization"] is False
        assert row["achieved_capability"] is None
        assert row["ownership"]["MIO"].startswith("diagnostic")
        assert row["ownership"]["HTT"].startswith("model-dependent")
    desi = next(row for row in runbooks["runbooks"] if row["lane"] == "DESI")
    assert "BGS_ANY remains a distinct estimand" in desi["required_input_contract"]


def test_data_runbook_rejects_public_release_ceiling(
    documents: dict[str, dict[str, object]], backlog: dict[str, object]
) -> None:
    changed = copy.deepcopy(documents["runbooks"])
    changed["runbooks"][0]["maximum_initial_capability"] = "PUBLIC_RELEASE"
    with pytest.raises(RetraceContractError):
        validate_data_runbooks(changed, backlog=backlog)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("execution_authorization_gate", "FAKE_GATE"),
        (
            "transfer_provenance",
            "external transfer validated as native",
        ),
    ],
)
def test_data_runbook_rejects_gate_or_transfer_firewall_mutation(
    documents: dict[str, dict[str, object]],
    backlog: dict[str, object],
    field: str,
    value: str,
) -> None:
    changed = copy.deepcopy(documents["runbooks"])
    changed["runbooks"][0][field] = value
    with pytest.raises(RetraceContractError):
        validate_data_runbooks(changed, backlog=backlog)


def test_data_runbook_rejects_mio_inference_ownership(
    documents: dict[str, dict[str, object]], backlog: dict[str, object]
) -> None:
    changed = copy.deepcopy(documents["runbooks"])
    changed["runbooks"][0]["ownership"]["MIO"] = (
        "model-dependent posterior and evidence"
    )
    with pytest.raises(RetraceContractError):
        validate_data_runbooks(changed, backlog=backlog)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("current_state", "EXECUTED_AND_AUTHORIZED"),
        ("claim_ceiling", "PUBLIC_RELEASE"),
        ("no_claim_exit", "PLANCK_FAMILY_IDENTIFIED"),
    ],
)
def test_data_runbook_rejects_state_or_claim_promotion(
    documents: dict[str, dict[str, object]],
    backlog: dict[str, object],
    field: str,
    value: str,
) -> None:
    changed = copy.deepcopy(documents["runbooks"])
    changed["runbooks"][0][field] = value
    if field == "no_claim_exit":
        changed["summary"].update(
            {
                "admitted_lane_count": 7,
                "authorized_lane_count": 7,
                "executed_lane_count": 7,
                "family_identification_count": 7,
            }
        )
    with pytest.raises(RetraceContractError):
        validate_data_runbooks(changed, backlog=backlog)


def test_every_derived_output_has_required_global_metadata(
    documents: dict[str, dict[str, object]]
) -> None:
    for name, document in documents.items():
        validate_output_metadata(document)
        assert document["claim_tier_ceiling"] == "diagnostic_only", name


def test_github_internal_identity_conflation_mutation_is_rejected(
    documents: dict[str, dict[str, object]], spec: dict[str, object]
) -> None:
    changed = copy.deepcopy(documents["github"])
    changed["records"][0]["github_record_id"] = "PR-002"
    with pytest.raises(RetraceContractError):
        validate_github_index(
            changed, snapshot=documents["snapshot"], spec=spec
        )


def test_generator_check_is_byte_exact() -> None:
    result = subprocess.run(
        [sys.executable, "-B", str(RUNNER), "check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert '"ok": true' in result.stdout
