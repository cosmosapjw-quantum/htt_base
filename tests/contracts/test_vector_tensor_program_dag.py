from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from pathlib import Path
import sys

import pytest
import yaml

from common.vector_tensor_program_registry import (
    CANONICAL_DAG_DEPENDENCIES,
    CANONICAL_DAG_EXTENSION,
    ProofClass,
    VectorTensorProgramRegistryError,
    load_vector_tensor_program_registry,
)


ROOT = Path(__file__).resolve().parents[2]
INTAKE = (
    ROOT
    / "docs/research_program/vector_tensor/PROGRAM_INTAKE_REGISTRY_V1.yaml"
)
PROGRAM = (
    ROOT
    / "docs/research_program/vector_tensor/"
    "VECTOR_TENSOR_PROOF_PROGRAM_V1.yaml"
)
PROPOSAL = (
    ROOT
    / "docs/research_program/vector_tensor/"
    "proof_registry_two_pillars.yaml"
)
BACKLOG = ROOT / "docs/codex_handoff/pr_backlog.yaml"
STATUS = ROOT / "docs/codex_handoff/pr_status.yaml"
POLICY = (
    ROOT
    / "docs/research_program/vector_tensor/pr260_publication_policy.json"
)

EXPECTED_DEPENDENCIES = {
    "PR-261": ["PR-260", "PR-249", "PR-256"],
    "PR-262": ["PR-261", "PR-254"],
    "PR-263": ["PR-261", "PR-257"],
    "PR-264": ["PR-262", "PR-263"],
    "PR-265": ["PR-264", "PR-250"],
    "PR-266": ["PR-264"],
    "PR-267": [
        "PR-263",
        "PR-265",
        "PR-266",
        "PR-255",
        "PR-256",
        "PR-258",
    ],
    "PR-268": ["PR-262", "PR-263", "PR-267"],
    "PR-269": ["PR-268"],
    "PR-270": ["PR-269"],
    "PR-271": ["PR-268"],
    "PR-272": ["PR-271"],
    "PR-273": ["PR-270", "PR-272"],
    "PR-274": ["PR-273"],
    "PR-275": ["PR-274"],
}


def _yaml(path: Path) -> dict[str, object]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _counts(rows, field: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for row in rows:
        value = str(row[field])
        result[value] = result.get(value, 0) + 1
    return result


def _mutated_registry(tmp_path: Path, mutate) -> Path:
    payload = copy.deepcopy(_yaml(INTAKE))
    mutate(payload)
    path = tmp_path / "mutated-intake.yaml"
    path.write_text(
        yaml.safe_dump(
            payload,
            sort_keys=False,
            allow_unicode=True,
            width=100,
        ),
        encoding="utf-8",
    )
    return path


def test_registered_source_schema_ids_and_statuses_are_preserved() -> None:
    programme = _yaml(PROGRAM)
    proposal = _yaml(PROPOSAL)

    assert programme["schema"] == "htt.vector_tensor_proof_program.draft.v1"
    assert programme["status"] == "REGISTERED"
    assert programme["source_status"] == "PROPOSED_NOT_REGISTERED_IN_CANONICAL_DAG"
    assert programme["registration"]["scientific_status_effect"] == "none"
    assert proposal["schema"] == "htt.proof_registry.two_pillars.v1"
    assert proposal["registration_status"] == "REGISTERED"
    assert proposal["source_status"] == "PROPOSED_REGISTRY_ROWS"
    assert proposal["registration"]["scientific_status_effect"] == "none"


def test_generator_is_deterministic_and_current() -> None:
    result = _run(
        sys.executable,
        "-B",
        "scripts/codex_harness/intake_vector_tensor_program.py",
        "--check",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "65 legacy, 58 proposal rows, U9/TC20/ST25" in result.stdout


def test_loader_reconstructs_exact_source_partitions_without_reinterpretation() -> None:
    registry = load_vector_tensor_program_registry(ROOT)
    raw = _yaml(INTAKE)

    assert len(registry.legacy_signatures) == 65
    assert len(registry.proposal_rows) == 58
    assert len(registry.obligations) == 54
    assert len(registry.vt_theorems) == 28
    assert _counts(
        raw["legacy_signature_inventory"]["entries"], "source_partition"
    ) == {"T": 31, "S": 34}
    assert _counts(
        raw["proposal_registry_rows"]["entries"], "source_partition"
    ) == {"I": 30, "II": 24, "BRIDGE": 4}
    assert _counts(
        raw["obligation_classes"]["entries"], "proof_class"
    ) == {"U": 9, "TC": 20, "ST": 25}
    assert _counts(
        raw["vt_theorem_obligations"]["entries"], "proof_class"
    ) == {"TC": 14, "ST": 14}

    aliases = raw["cardinality_aliases"]
    assert aliases["requested_pillar_T_65"] == "legacy_signature_inventory"
    assert aliases["requested_pillar_S_58"] == "proposal_registry_rows"
    for source_partition in ("31 T", "34 S", "30 I", "24 II", "4 BRIDGE"):
        assert source_partition in aliases["semantic_guard"]


def test_all_registered_ids_are_disjoint_and_metadata_complete() -> None:
    registry = load_vector_tensor_program_registry(ROOT)
    raw = _yaml(INTAKE)
    ids = [entry.entry_id for entry in registry.all_entries]

    assert len(ids) == 65 + 58 + 54 + 28
    assert len(ids) == len(set(ids))
    assert {entry.proof_class for entry in registry.all_entries} == {
        ProofClass.U,
        ProofClass.TC,
        ProofClass.ST,
    }
    backlog_ids = {card["id"] for card in _yaml(BACKLOG)["prs"]}
    for entry in registry.all_entries:
        assert entry.registry_owner
        assert entry.dependencies
        assert set(entry.dependencies) <= backlog_ids
        evidence_file = entry.evidence_path.split("#", 1)[0]
        assert (ROOT / evidence_file).is_file(), entry.entry_id
        assert entry.claim_ceiling == "diagnostic_only"

    for section in (
        "legacy_signature_inventory",
        "proposal_registry_rows",
        "obligation_classes",
        "vt_theorem_obligations",
    ):
        for row in raw[section]["entries"]:
            assert row["registry_owner"]
            assert row["dependencies"]
            assert row["evidence_path"]
            assert row["claim_ceiling"] == "diagnostic_only"
            assert row.get("scientific_owner") or row.get("owner_route")
    for row in raw["proposal_registry_rows"]["entries"]:
        assert len(row["statement_identity_sha256"]) == 64


def test_source_identities_are_hash_bound_to_tracked_files() -> None:
    registry = load_vector_tensor_program_registry(ROOT)

    assert {source.source_id for source in registry.source_identities} == {
        f"A{index}" for index in range(1, 9)
    }
    for source in registry.source_identities:
        tracked = ROOT / source.tracked_path
        assert hashlib.sha256(tracked.read_bytes()).hexdigest() == (
            source.tracked_sha256
        )
        assert len(source.source_attachment_sha256) == 64
        assert source.normalization in {
            "registered_wrapper",
            "content_preserved_with_terminal_lf",
            "git_conflict_sentinel_normalized_with_note",
        }


def test_pr261_275_cards_match_revalidated_dag_and_common_contract() -> None:
    registry = load_vector_tensor_program_registry(ROOT)
    backlog = _yaml(BACKLOG)
    status = _yaml(STATUS)
    cards = {card["id"]: card for card in backlog["prs"]}
    order = backlog["policy"]["topological_order"]

    assert tuple(order[order.index("PR-261"): order.index("PR-275") + 1]) == (
        CANONICAL_DAG_EXTENSION
    )
    assert registry.canonical_dag_dependencies == CANONICAL_DAG_DEPENDENCIES
    for pr_id, dependencies in EXPECTED_DEPENDENCIES.items():
        card = cards[pr_id]
        assert card["depends"] == dependencies
        assert card["dependency_contracts"] == [
            {"upstream_id": dependency, "mode": "requires_success"}
            for dependency in dependencies
        ]
        assert {
            "owner",
            "dependencies",
            "capability",
            "inputs",
            "outputs",
            "forbidden",
            "tests",
            "kill",
            "claim_tier_ceiling",
        } - set(card) == {"dependencies"}
        assert card["owner"]
        assert card["capability"]
        assert card["inputs"]
        assert card["outputs"]
        assert card["tests"]
        assert card["kill"]
        assert card["claim_tier_ceiling"] == "diagnostic_only"
        forbidden = " ".join(card["forbidden"]).lower()
        assert "native" in forbidden
        assert "family-identification" in forbidden
        assert card["public_use"] is False
        assert card["solver_gate_required"] is False
        assert card["scientific_status_on_intake"] == "OPEN"

    # The vector/tensor programme is complete; a later registered card may be
    # the sole foreground task without changing any PR-261..275 disposition.
    assert status["in_progress"] in (
        None,
        "PR-276",
        "PR-277",
        "PR-288",
        "PR-299",
        "PR-300",
        "PR-307",
        "PR-308",
        "PR-309",
        "PR-310",
        "PR-311",
        "PR-312",
        "PR-313",
    )
    assert "PR-260" in status["completed"]
    assert status["execution_resolutions"]["PR-260"][
        "resolution"
    ] == "COMPLETED_SUCCESS"
    assert status["execution_resolutions"]["PR-260"][
        "scientific_status_effect"
    ] == "none_programme_registration_only"
    assert status["execution_resolutions"]["PR-260"]["public_use"] is False
    completed_extension = tuple(
        pr_id
        for pr_id in CANONICAL_DAG_EXTENSION
        if pr_id in status["completed"]
    )
    pending_extension = tuple(
        pr_id
        for pr_id in CANONICAL_DAG_EXTENSION
        if pr_id in status["pending"]
    )
    assert "PR-261" in completed_extension
    assert set(completed_extension).isdisjoint(pending_extension)
    assert set(completed_extension) | set(pending_extension) == set(
        EXPECTED_DEPENDENCIES
    )
    for pr_id in completed_extension:
        assert set(EXPECTED_DEPENDENCIES[pr_id]) <= set(status["completed"])
        resolution = status["execution_resolutions"][pr_id]
        assert resolution["resolution"] == "COMPLETED_SUCCESS"
        assert resolution["success_dependency_satisfied"] is True
        assert resolution["scientific_status_after"] == "OPEN"
        assert resolution["public_use"] is False
    assert all(
        status["execution_lane"][pr_id] == "defensible"
        for pr_id in EXPECTED_DEPENDENCIES
    )


def test_canonical_dag_and_compatibility_mirrors_validate() -> None:
    dag = _run(
        sys.executable,
        "-B",
        "scripts/codex_harness/validate_pr_dag.py",
        "docs/codex_handoff/pr_backlog.yaml",
        "--status",
        "docs/codex_handoff/pr_status.yaml",
        "--strict-rescue-slice",
    )
    assert dag.returncode == 0, dag.stdout + dag.stderr
    assert "OK: 259 PRs, DAG valid" in dag.stdout

    mirrors = _run(
        sys.executable,
        "-B",
        "scripts/codex_harness/sync_pr_dag_mirrors.py",
        "--check",
    )
    assert mirrors.returncode == 0, mirrors.stdout + mirrors.stderr


def test_publication_policy_requires_portable_review_cells_and_commands() -> None:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))

    assert policy["change_set_id"] == "CS-PR260-VECTOR-TENSOR-INTAKE"
    assert policy["publication_group_id"] == "PG-PR260-VECTOR-TENSOR-INTAKE"
    assert policy["target_ref"] == "origin/research/pr04-multicomponent"
    assert {
        "source_schema_identity",
        "source_cardinality_and_partition",
        "identifier_disjointness",
        "proof_class_owner_dependency_evidence",
        "cardinality_alias_semantics",
        "pr261_275_dependency_order",
        "canonical_mirror_equivalence",
        "mutation_refusal",
        "claim_ceiling",
        "latest_target_integration",
    } <= set(policy["required_review_cells"])
    commands = {row["id"]: row["argv"] for row in policy["required_commands"]}
    assert commands["pr260-focused"] == [
        "{python}",
        "-B",
        "scripts/codex_harness/run_pr260_intake.py",
        "focused",
    ]
    assert commands["pr260-smoke"] == [
        "{python}",
        "-B",
        "scripts/codex_harness/run_pr260_intake.py",
        "smoke",
    ]
    assert policy["ordinary_agent_push_forbidden"] is True
    assert policy["ordinary_agent_pr_mutation_forbidden"] is True


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p.update(schema="htt.vector_tensor_program_intake.v0"),
        lambda p: p["legacy_signature_inventory"]["entries"].pop(),
        lambda p: p["proposal_registry_rows"]["entries"][0].update(
            id=p["legacy_signature_inventory"]["entries"][0]["id"]
        ),
        lambda p: p["obligation_classes"]["entries"][0].update(
            proof_class="UNKNOWN"
        ),
        lambda p: p["vt_theorem_obligations"]["entries"][0].update(
            dependencies=[]
        ),
        lambda p: p["proposal_registry_rows"]["entries"][0].update(
            evidence_path=""
        ),
        lambda p: p["cardinality_aliases"].update(
            requested_pillar_T_65="scientific_pillar_T"
        ),
        lambda p: p["claim_boundary"].update(native_solver_result=True),
        lambda p: p["source_identities"][0].update(tracked_sha256="0" * 64),
        lambda p: p.update(
            canonical_dag_extension=list(reversed(p["canonical_dag_extension"]))
        ),
        lambda p: p["canonical_dag_dependencies"]["PR-273"].remove("PR-270"),
    ],
)
def test_loader_rejects_registry_mutations(tmp_path: Path, mutate) -> None:
    path = _mutated_registry(tmp_path, mutate)
    with pytest.raises(VectorTensorProgramRegistryError):
        load_vector_tensor_program_registry(ROOT, path)
