
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "survivor_triage_under_test",
    ROOT / "scripts" / "extract_theory_survivor_surface.py",
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


def _row(
    claim_id: str,
    *,
    synthetic: bool = False,
    verdict: str = "PASS",
    terminal: str = "PROMOTED",
    observed: bool = False,
) -> dict[str, object]:
    statement = f"Registered statement for {claim_id}"
    return {
        "claim_id": claim_id,
        "source_row_id": claim_id.split(":")[-1],
        "source_group": "vector_tensor_successor",
        "source_partition": "VT-S" if synthetic else "T",
        "source_statement": statement,
        "adjudicated_statement": statement,
        "source_statement_identity_sha256": hashlib.sha256(
            statement.encode("utf-8")
        ).hexdigest(),
        "broad_verdict": verdict,
        "scientific_terminal_state": terminal,
        "scientific_attempted": True,
        "theory_result_class": (
            "PREREGISTERED_SYNTHETIC_RESULT_NOT_THEOREM"
            if synthetic
            else "EXACT_OR_CONDITIONAL_THEOREM_CORE"
        ),
        "current_release_disposition": (
            "REPORT_AS_SYNTHETIC_VALIDATION_ONLY"
            if synthetic
            else "CANDIDATE_AFTER_CURRENT_REPLAY_REPAIR"
        ),
        "promotion_disposition": (
            "REPORT_AS_SYNTHETIC_VALIDATION_ONLY"
            if synthetic
            else "CANDIDATE_AFTER_CURRENT_REPLAY_REPAIR"
        ),
        "claim_ceiling": "diagnostic_only",
        "observed_data_used": observed,
        "evidence_refs": [f"evidence/{claim_id}.json"],
        "linked_claim_ids": [],
    }


def _scoped(
    candidate_id: str,
    parent: str,
    *,
    kind: str = "RESTRICTED_EXACT_THEOREM_CORE",
    terminal: str = "PROMOTED",
) -> dict[str, object]:
    statement = f"Scoped statement for {candidate_id}"
    return {
        "candidate_id": candidate_id,
        "candidate_kind": kind,
        "source_candidate_id": parent,
        "statement": statement,
        "statement_identity_sha256": hashlib.sha256(
            statement.encode("utf-8")
        ).hexdigest(),
        "scientific_terminal_state": terminal,
        "scientific_attempted": True,
        "current_release_disposition": (
            "SCOPED_SYNTHETIC_RESULT_ONLY_PARENT_REMAINS_DEFERRED"
            if "SYNTHETIC" in kind
            else "HISTORICAL_CAS4_PASS_CURRENT_REPLAY_INCOMPLETE"
        ),
        "claim_ceiling": "diagnostic_only",
        "observed_data_used": False,
        "evidence_refs": [f"evidence/{candidate_id}.json"],
    }


def matrix() -> dict[str, object]:
    exact = [_row(f"PILLAR_T:EXACT-{index:02d}") for index in range(24)]
    synthetic = [
        _row(f"PILLAR_S:SYNTH-{index:02d}", synthetic=True)
        for index in range(8)
    ]
    parents = [
        _row("PARENT:LOCAL-CHART", verdict="INCONCLUSIVE_WITH_RECEIPT", terminal="UNRESOLVED"),
        _row("PARENT:CHAIN-RULE", verdict="INCONCLUSIVE_WITH_RECEIPT", terminal="UNRESOLVED"),
        _row("PARENT:NEGATIVE", verdict="FAIL", terminal="REFUTED"),
        _row("PARENT:SYNTHETIC", synthetic=True, verdict="BLOCKED_WITH_RECEIPT", terminal="DEFERRED"),
    ]
    scoped = [
        _scoped("NARROW:LOCAL-CHART", "PARENT:LOCAL-CHART"),
        _scoped("NARROW:CHAIN-RULE", "PARENT:CHAIN-RULE"),
        _scoped("NARROW:NEGATIVE", "PARENT:NEGATIVE", kind="EXACT_NEGATIVE_THEOREM"),
        _scoped(
            "NARROW:SYNTHETIC",
            "PARENT:SYNTHETIC",
            kind="PREREGISTERED_SYNTHETIC_METHOD_VALIDATION",
        ),
        _scoped(
            "PR284_NEW:FINITE-REGISTERED-PATH",
            "PILLAR_S:II-3.2",
            kind="FOUR_AXIS_PROOF_ATTEMPT",
            terminal="UNRESOLVED",
        ),
    ]
    return {
        "schema": "htt.theory_promotion_matrix.v1",
        "counts": {
            "exact_or_conditional_theory_pass_rows": 24,
            "synthetic_only_pass_rows": 8,
            "row_level_pass_total": 32,
            "scientific_candidate_count": 41,
            "scientific_terminal_state_counts": {
                "PROMOTED": 36,
                "REFUTED": 1,
                "UNRESOLVED": 3,
                "DEFERRED": 1,
                "NOT_ATTEMPTED": 0,
            },
        },
        "candidate_coverage_proof": {
            "candidate_count": 41,
            "coverage_complete": True,
            "missing_terminal_state_count": 0,
            "unknown_terminal_state_count": 0,
            "duplicate_candidate_id_count": 0,
            "supplemental_scoped_candidates_expected": 5,
            "supplemental_scoped_candidates_classified": 5,
        },
        "scope": {
            "observed_data_used": False,
            "observed_analysis_in_scope": False,
            "native_solver_in_scope": False,
        },
        "semantic_links": [
            {
                "claims": ["PILLAR_T:EXACT-00", "PILLAR_T:EXACT-01"],
                "relation": "DUPLICATE_EXACT_CORE",
                "note": "Keep both rows; do not count them as two unique theorems.",
            },
            {
                "claims": ["PARENT:LOCAL-CHART", "PILLAR_T:EXACT-02"],
                "relation": "NARROWER_LOCAL_CORE_ONLY",
                "note": "The scoped child does not broaden its parent.",
            },
        ],
        "supplemental_scoped_candidates": scoped,
        "rows": exact + synthetic + parents,
    }


def build(value: dict[str, object]) -> dict[str, object]:
    return MOD.build_surface(
        value,
        source={
            "commit": "463f0999949bf8534c60ad7973b7342705c2e3d6",
            "git_blob": "56af1713ef8c4718598e10012819d5ab62c6e37a",
            "path": "docs/research_program/theory_promotion/THEORY_PROMOTION_MATRIX_V1.json",
            "sha256": "0" * 64,
        },
    )


def test_exact_registered_surface_has_24_plus_8_plus_5_rows():
    surface = build(matrix())
    assert surface["coverage"]["exact_or_conditional_broad"] == 24
    assert surface["coverage"]["synthetic_broad"] == 8
    assert surface["coverage"]["scoped_children"] == 5
    assert surface["coverage"]["included_total"] == 36
    assert surface["coverage"]["deferred_total"] == 1
    assert len(surface["candidates"]) == 37
    assert surface["unique_theorem_count"] is None
    assert surface["release_authority"] is False


def test_registered_survivor_triage_detects_injected_eligible_candidate():
    value = matrix()
    value["rows"].append(_row("PILLAR_T:INJECTED-ELIGIBLE"))
    with pytest.raises(MOD.SurvivorTriageError, match="broad PASS count"):
        build(value)


def test_research_decision_changes_when_source_or_replay_evidence_is_mutated():
    first = matrix()
    second = deepcopy(first)
    second["rows"][0]["evidence_refs"].append("evidence/new-independent-replay.json")
    assert build(first)["content_id"] != build(second)["content_id"]


def test_broad_parent_and_narrow_child_have_distinct_statement_identities():
    surface = build(matrix())
    children = {
        row["candidate_id"]: row
        for row in surface["candidates"]
        if row["source_kind"] == "SCOPED_CHILD"
    }
    child = children["NARROW:LOCAL-CHART"]
    assert child["parent_candidate_id"] == "PARENT:LOCAL-CHART"
    assert child["candidate_id"] != child["parent_candidate_id"]
    edges = {
        (tuple(item["claims"]), item["relation"])
        for item in surface["relations"]
    }
    assert (
        ("PARENT:LOCAL-CHART", "NARROW:LOCAL-CHART"),
        "PARENT_CHILD",
    ) in edges


def test_semantic_duplicate_links_are_retained_without_row_collapse():
    surface = build(matrix())
    ids = [row["candidate_id"] for row in surface["candidates"]]
    assert len(ids) == len(set(ids)) == 37
    links = [
        item for item in surface["relations"]
        if item["relation"] == "DUPLICATE_EXACT_CORE"
    ]
    assert links == [{
        "claims": ["PILLAR_T:EXACT-00", "PILLAR_T:EXACT-01"],
        "relation": "DUPLICATE_EXACT_CORE",
        "note": "Keep both rows; do not count them as two unique theorems.",
        "source": "PR405_SEMANTIC_LINK",
    }]


def test_observed_data_use_is_rejected():
    value = matrix()
    value["rows"][0]["observed_data_used"] = True
    with pytest.raises(MOD.SurvivorTriageError, match="observed data"):
        build(value)


def test_duplicate_candidate_identity_is_rejected():
    value = matrix()
    value["rows"][1]["claim_id"] = value["rows"][0]["claim_id"]
    with pytest.raises(MOD.SurvivorTriageError, match="duplicate candidate"):
        build(value)


def test_missing_statement_identity_is_rejected():
    value = matrix()
    del value["rows"][0]["source_statement_identity_sha256"]
    with pytest.raises(MOD.SurvivorTriageError, match="statement identity"):
        build(value)


def test_surface_contains_no_truth_novelty_or_publication_assignment():
    surface = build(matrix())
    serialized = json.dumps(surface, sort_keys=True)
    for forbidden in ("truth_status", "novelty_status", "publication_role"):
        assert forbidden not in serialized


def test_output_is_deterministic_under_input_row_permutation():
    first = matrix()
    second = deepcopy(first)
    second["rows"] = list(reversed(second["rows"]))
    second["supplemental_scoped_candidates"] = list(
        reversed(second["supplemental_scoped_candidates"])
    )
    assert build(first) == build(second)


def test_git_object_mode_binds_commit_blob_and_content(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.email", "test@example.invalid"],
        check=True,
    )
    path = repo / "matrix.json"
    path.write_text(json.dumps(matrix(), sort_keys=True), encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "matrix.json"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "matrix"], check=True)
    commit = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip()
    blob = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD:matrix.json"], text=True
    ).strip()

    loaded, source = MOD.load_git_source(
        repo=repo,
        ref=commit,
        path="matrix.json",
        expected_blob=blob,
    )
    surface = MOD.build_surface(loaded, source=source)
    assert source["commit"] == commit
    assert source["git_blob"] == blob
    assert source["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert surface["source"]["git_blob"] == blob


def test_cli_refuses_existing_output_without_explicit_replace(tmp_path):
    matrix_path = tmp_path / "matrix.json"
    output = tmp_path / "surface.json"
    matrix_path.write_text(json.dumps(matrix()), encoding="utf-8")
    output.write_text("preserve", encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "extract_theory_survivor_surface.py"),
            "--matrix",
            str(matrix_path),
            "--output",
            str(output),
        ],
        text=True,
        capture_output=True,
    )
    assert completed.returncode != 0
    assert output.read_text(encoding="utf-8") == "preserve"


def test_repository_source_id_seed_has_37_unique_rows_and_pr284_deferred():
    seed_path = (
        ROOT
        / "docs"
        / "research_program"
        / "theory_promotion"
        / "closeout"
        / "REGISTERED_SURVIVOR_SEED.json"
    )
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    rows = seed["rows"]
    ids = [row["candidate_id"] for row in rows]
    assert len(ids) == len(set(ids)) == 37
    assert seed["counts"] == {
        "exact_or_conditional_broad_included": 24,
        "synthetic_broad_included": 8,
        "scoped_included": 4,
        "scoped_deferred": 1,
        "included_total": 36,
        "registered_total": 37,
    }
    dispositions = {
        name: sum(row["triage_disposition"] == name for row in rows)
        for name in ("INCLUDED", "DEFERRED", "EXCLUDED")
    }
    assert dispositions == {"INCLUDED": 36, "DEFERRED": 1, "EXCLUDED": 0}
    pr284 = next(
        row
        for row in rows
        if row["candidate_id"] == "PR284_NEW:FINITE-REGISTERED-PATH"
    )
    assert pr284["triage_disposition"] == "DEFERRED"
    assert pr284["parent_candidate_id"] == "PILLAR_S:II-3.2"
