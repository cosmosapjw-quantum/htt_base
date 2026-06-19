from pathlib import Path
import hashlib
import re

import pytest
import yaml
from yaml.constructor import ConstructorError


ROOT = Path(__file__).resolve().parents[2]
DAG = ROOT / "docs/codex_handoff/pr_dag_research_program.yaml"
EXPERIMENT_REGISTRY = ROOT / "docs/generated/research_program_experiment_registry.yaml"
THEOREM_REGISTRY = ROOT / "docs/generated/research_program_theorem_registry.yaml"
CANONICAL_STATUS = ROOT / "docs/codex_handoff/pr_status.yaml"
CANONICAL_BACKLOG = ROOT / "docs/codex_handoff/pr_backlog.yaml"

REQUIRED_METADATA = {
    "owner",
    "implementation_scope",
    "claim_tier",
    "transfer_source",
    "config_hash",
    "input_hashes",
    "sky_support_status",
    "null_mock_status",
    "generating_command",
    "git_commit_or_worktree_state",
    "caveats",
}


class UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_mapping_no_duplicates(loader, node, deep=False):
    loader.flatten_mapping(node)
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping_no_duplicates,
)


def _load(path: Path):
    return _load_text(path.read_text(encoding="utf-8"))


def _load_text(text: str):
    return yaml.load(text, Loader=UniqueKeyLoader)


def _assert_minimum_metadata(payload):
    assert REQUIRED_METADATA <= set(payload)
    assert payload["owner"]
    assert payload["implementation_scope"]
    assert payload["claim_tier"] in {"diagnostic_only", "blocked"}
    assert payload["transfer_source"] in {"none", "external_proxy"}
    assert re.fullmatch(r"sha256:[0-9a-f]{64}", str(payload["config_hash"]))
    assert isinstance(payload["input_hashes"], list)
    assert payload["input_hashes"]
    for entry in payload["input_hashes"]:
        assert isinstance(entry, dict)
        assert set(entry) == {"path", "sha256"}
        assert isinstance(entry["path"], str) and entry["path"]
        assert re.fullmatch(r"[0-9a-f]{64}", entry["sha256"])
        path = ROOT / entry["path"]
        assert path.is_file(), entry["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]
    assert payload["sky_support_status"]
    assert payload["null_mock_status"]
    assert payload["generating_command"]
    assert payload["git_commit_or_worktree_state"]
    assert isinstance(payload["caveats"], list) and payload["caveats"]


def test_research_program_yaml_loader_rejects_duplicate_keys():
    with pytest.raises(ConstructorError):
        _load_text("status_surface: proposed_only\nstatus_surface: canonical\n")


def test_research_program_dag_has_expected_order_and_blocks_native_family_id():
    payload = _load(DAG)
    _assert_minimum_metadata(payload)
    ids = [row["id"] for row in payload["prs"]]
    assert len(ids) == len(set(ids))

    for required in [
        "PR-N00",
        "PR-N01",
        "PR-N02",
        "PR-N03",
        "PR-N04",
        "PR-N10",
        "PR-N11",
        "PR-N12",
        "PR-N13",
        "PR-N20",
        "PR-N21",
        "PR-N22",
        "PR-N30",
        "PR-N31",
        "PR-N32",
        "PR-N40",
        "PR-N41",
        "PR-N50",
        "PR-N51",
    ]:
        assert required in ids
    assert payload["status_surface"] == "proposed_only"
    assert payload["does_not_overwrite"] == "docs/codex_handoff/pr_status.yaml"
    assert payload["policy"]["native_lowell_solver_implementation_allowed"] is False
    assert (
        payload["policy"]["family_identification_claims_blocked_pre_native_atlas"]
        is True
    )
    assert payload["policy"]["external_transfer_native_promotion_allowed"] is False
    assert payload["policy"]["mio_htt_evidence_merge_allowed"] is False
    assert payload["policy"]["scalar_feature_family_identification_allowed"] is False
    assert payload["policy"]["proposal_rows_satisfy_dependencies"] is False
    blocked = next(row for row in payload["prs"] if row["id"] == "PR-N51")
    assert blocked["status"] == "blocked_until_native_solver"


def test_research_program_dag_dependencies_are_internal_and_topological():
    payload = _load(DAG)
    ids = [row["id"] for row in payload["prs"]]
    seen: set[str] = set()

    for row in payload["prs"]:
        assert {
            "id",
            "title",
            "owner",
            "depends",
            "status",
            "allowed_use",
            "required_gates",
            "blocked_claims",
        } <= set(row)
        depends = row.get("depends", [])
        assert isinstance(depends, list)
        assert all(dep in ids for dep in depends), row["id"]
        assert all(dep in seen for dep in depends), row["id"]
        assert row["status"] in {"proposed", "schema_only", "blocked_until_native_solver"}
        assert row["allowed_use"] in {"design", "diagnostic", "external_audit"}
        assert isinstance(row["required_gates"], list)
        assert row["required_gates"]
        assert isinstance(row["blocked_claims"], list)
        assert row["blocked_claims"]
        assert row["owner"] in {
            "COMMON",
            "HTT",
            "MIO",
            "OBSSTAT",
            "OBSSTAT_HTT",
            "BASS",
            "BASS_COMMON",
        }
        seen.add(row["id"])


def test_research_program_dag_enforces_calibration_and_family_gates():
    rows = {row["id"]: row for row in _load(DAG)["prs"]}

    assert rows["PR-N11"]["depends"] == ["PR-N10"]
    assert rows["PR-N13"]["depends"] == ["PR-N12"]
    assert rows["PR-N31"]["depends"] == ["PR-N30"]
    assert rows["PR-N20"]["depends"] == ["PR-N11", "PR-N13", "PR-N02"]
    assert rows["PR-N32"]["depends"] == ["PR-N31", "PR-N04"]

    assert {"full_covariance", "local_flow_mock_bank"} <= set(rows["PR-N11"]["required_gates"])
    assert {"matched_mock_catalogs", "full_covariance"} <= set(rows["PR-N13"]["required_gates"])
    assert {"end_to_end_simulations", "full_covariance"} <= set(rows["PR-N31"]["required_gates"])
    assert {"full_cross_probe_covariance", "matched_mocks", "held_out_probe"} <= set(
        rows["PR-N20"]["required_gates"]
    )
    assert {
        "matched_nulls",
        "masks",
        "full_covariance",
        "transfer_provenance",
        "response_rank_audit",
        "nuisance_projection",
    } <= set(rows["PR-N22"]["required_gates"])
    assert {"null_mask_covariance_summary", "mio_htt_separation", "scalar_non_identification"} <= set(
        rows["PR-N40"]["required_gates"]
    )
    assert {"response_rank_summary", "nuisance_projection_summary"} <= set(
        rows["PR-N40"]["required_gates"]
    )
    assert {
        "native_morphology_atlas",
        "family_equivalence_separation",
        "response_rank_audit",
        "nuisance_projection",
        "ppc",
        "held_out_morphology_prediction",
        "orientation_look_elsewhere_correction",
    } <= set(rows["PR-N51"]["required_gates"])
    assert rows["PR-N51"]["status"] == "blocked_until_native_solver"
    assert "PR-N22" in rows["PR-N51"]["depends"]
    assert "PR-N31" in rows["PR-N51"]["depends"]


def test_research_program_registries_cover_dag_without_promotion():
    dag = _load(DAG)
    experiment = _load(EXPERIMENT_REGISTRY)
    theorem = _load(THEOREM_REGISTRY)
    _assert_minimum_metadata(experiment)
    _assert_minimum_metadata(theorem)

    dag_ids = {row["id"] for row in dag["prs"]}
    experiment_prs = {
        pr_id
        for row in experiment["experiments"]
        for pr_id in row["pr_ids"]
    }
    theorem_prs = {
        pr_id
        for row in theorem["theorem_tracks"]
        for pr_id in row["pr_ids"]
    }

    assert experiment["claim_tier"] == "diagnostic_only"
    assert theorem["claim_tier"] == "diagnostic_only"
    assert experiment["status_surface"] == "proposal_registry_only"
    assert theorem["status_surface"] == "proposal_registry_only"
    assert experiment_prs <= dag_ids
    assert theorem_prs <= dag_ids
    assert dag_ids <= experiment_prs | theorem_prs
    assert {"PR-N02", "PR-N10", "PR-N11", "PR-N13", "PR-N20", "PR-N22", "PR-N31", "PR-N40"} <= experiment_prs
    assert {"PR-N04", "PR-N11", "PR-N13", "PR-N31", "PR-N32", "PR-N50", "PR-N51"} <= theorem_prs
    for row in experiment["experiments"]:
        assert {
            "id",
            "title",
            "owner",
            "pr_ids",
            "allowed_use",
            "status",
            "required_artifacts",
            "blocked_claims",
        } <= set(row)
        assert row["allowed_use"] in {"design", "diagnostic", "external_audit"}
        assert row["status"] == "proposed"
        assert row["pr_ids"]
        assert row["required_artifacts"]
        assert row["blocked_claims"]
    for row in theorem["theorem_tracks"]:
        assert {
            "id",
            "title",
            "owner",
            "pr_ids",
            "status",
            "required_inputs",
            "allowed_claim_tier",
            "blocked_claims",
        } <= set(row)
        assert row["status"] in {"specified", "proposed", "blocked_until_native_solver"}
        assert row["allowed_claim_tier"] in {"diagnostic_only", "blocked"}
        assert row["pr_ids"]
        assert row["required_inputs"]
        assert row["blocked_claims"]

    e6 = next(row for row in experiment["experiments"] if row["id"] == "E6")
    assert {"matched_mock_catalogs", "full_covariance", "random_catalog_null_bank"} <= set(
        e6["required_artifacts"]
    )
    assert "jackknife_as_matched_null" in e6["blocked_claims"]
    t5 = next(row for row in theorem["theorem_tracks"] if row["id"] == "T5")
    assert "compatibility" not in t5["title"].lower()
    assert "exact_mask_noise_simulations" in t5["required_inputs"]
    assert {"response_rank_audit", "nuisance_projection"} <= set(t5["required_inputs"])
    t6 = next(row for row in theorem["theorem_tracks"] if row["id"] == "T6")
    assert t6["status"] == "blocked_until_native_solver"
    assert {
        "native_convergence_report",
        "external_cross_check",
        "response_rank_audit",
        "nuisance_projection",
        "matched_complexity_alternatives",
        "prior_stability",
        "ppc_and_held_out_morphology_prediction",
        "orientation_look_elsewhere_correction",
    } <= set(t6["required_inputs"])


def test_research_program_dag_does_not_mutate_canonical_status():
    status = _load(CANONICAL_STATUS)
    backlog = _load(CANONICAL_BACKLOG)

    for key in ("completed", "blocked", "skipped"):
        assert not any(
            pr_id.startswith("PR-N") for pr_id in status.get(key, [])
        ), key
    in_progress = status.get("in_progress")
    assert in_progress is None or not str(in_progress).startswith("PR-N")

    canonical_order = backlog["policy"]["topological_order"]
    canonical_prs = [row["id"] for row in backlog["prs"]]
    assert not any(pr_id.startswith("PR-N") for pr_id in canonical_order)
    assert not any(pr_id.startswith("PR-N") for pr_id in canonical_prs)
