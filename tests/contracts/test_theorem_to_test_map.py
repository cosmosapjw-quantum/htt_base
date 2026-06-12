from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from common.semantic_guards import scan_text
from common.semantic_guards.no_overclaim import render_issues
from tsc.validation.theorem_map import CORE_THEOREM_MAP, build_tsc_validation_witnesses


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = REPO_ROOT / "docs" / "generated" / "theorem_to_test_map_legacy_tsc.json"
DOC = REPO_ROOT / "docs" / "deprecation" / "theorem_to_test_map.md"
GENERATOR = REPO_ROOT / "scripts" / "codex_harness" / "generate_theorem_to_test_map.py"


def _payload() -> dict[str, object]:
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def test_generated_audit_map_matches_legacy_theorem_source() -> None:
    payload = _payload()
    rows = payload["theorems"]
    assert isinstance(rows, list)

    by_theorem = {entry.theorem: entry for entry in CORE_THEOREM_MAP}
    generated = {str(row["theorem_id"]): row for row in rows}

    assert set(generated) == set(by_theorem)
    for theorem_id, source in by_theorem.items():
        row = generated[theorem_id]
        assert row["legacy_status"] == "validation_obligation_only"
        assert row["audit_only"] is True
        assert row["validation_obligation_only"] is True
        assert row["legacy_source_owner"] == "TSC_LEGACY"
        assert row["legacy_source_scope"] == "tsc_legacy"
        assert row["legacy_tests"] == list(source.tests)
        assert row["metrics_recorded"] == list(source.metrics)
        assert row["required_artifacts"] == list(source.required_artifacts)

    source_witnesses = build_tsc_validation_witnesses()
    source_witness_by_key = {
        (witness.theorem, witness.test_id): witness for witness in source_witnesses
    }
    generated_witness_by_key = {
        (str(row["theorem_id"]), witness["test_id"]): witness
        for row in rows
        for witness in row["witnesses"]
    }
    assert set(generated_witness_by_key) == set(source_witness_by_key)
    for key, source in source_witness_by_key.items():
        witness = generated_witness_by_key[key]
        assert witness["category"] == source.category
        assert witness["path"] == source.path
        assert witness["purpose"] == source.purpose
        assert witness["artifact_refs"] == list(source.artifact_refs)


def test_witness_paths_remain_live_test_nodes() -> None:
    payload = _payload()
    witness_paths = []
    for row in payload["theorems"]:
        for witness in row["witnesses"]:
            assert witness["witness_role"] == "legacy_test_witness_only"
            assert witness["production_claim_allowed"] is False
            path = str(witness["path"])
            file_part = path.split("::", 1)[0]
            assert (REPO_ROOT / file_part).exists(), path
            witness_paths.append(path)
            assert witness["category"]
            assert witness["purpose"]

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            *sorted(set(witness_paths)),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_metadata_marks_artifact_common_audit_only() -> None:
    metadata = _payload()["metadata"]

    assert metadata["schema_version"] == "pr032.legacy_theorem_to_test_map.v1"
    assert metadata["owner"] == "COMMON"
    assert metadata["implementation_scope"] == "common"
    assert metadata["bundle_kind"] == "common_contract"
    assert metadata["legacy_source_owner"] == "TSC_LEGACY"
    assert metadata["legacy_source_scope"] == "tsc_legacy"
    assert metadata["claim_tier"] == "diagnostic_only"
    assert metadata["production_status"] == "diagnostic_only"
    assert metadata["artifact_role"] == "legacy_theorem_to_test_audit_map"
    assert metadata["audit_only"] is True
    assert metadata["legacy_active_science_owner"] is False
    assert metadata["transfer_source"] == "none"
    assert metadata["sky_support_status"] == "not_directional"
    assert metadata["null_mock_status"] == "not_statistical"
    assert metadata["covariance_status"] == "not_statistical"
    assert metadata["config_hash"]
    assert metadata["input_hashes"]
    assert metadata["generating_command"]
    assert metadata["git_commit_or_worktree_state"]
    assert metadata["consumable_as_production_claim"] is False
    assert metadata["consumable_as_solver_validation"] is False
    assert metadata["consumable_as_htt_evidence"] is False
    assert metadata["consumable_as_mio_certificate"] is False
    assert metadata["consumable_as_family_identification"] is False


def test_rows_block_all_production_and_family_promotion_paths() -> None:
    payload = _payload()
    required_nonclaims = {
        "production_observation_claim",
        "observable_adequacy",
        "htt_evidence",
        "mio_certificate",
        "posterior_or_likelihood_support",
        "transfer_validation",
        "native_solver_validation",
        "native_solver_result",
        "null_calibration",
        "mask_or_sky_coverage_support",
        "covariance_support",
        "response_rank_support",
        "equivalence_class_breaking",
        "morphology_atlas_support",
        "morphology_compatibility",
        "geometry_or_family_identification",
    }

    assert set(payload["metadata"]["does_not_establish"]) >= required_nonclaims
    for row in payload["theorems"]:
        assert row["claim_tier_ceiling"] == "diagnostic_only"
        assert row["production_claim_allowed"] is False
        assert row["observation_claim_allowed"] is False
        assert row["observable_adequacy_established"] is False
        assert row["native_solver_validation_allowed"] is False
        assert row["transfer_validation_allowed"] is False
        assert row["consumable_as_htt_evidence"] is False
        assert row["consumable_as_mio_certificate"] is False
        assert row["consumable_as_family_identification"] is False
        assert set(row["does_not_establish"]) >= required_nonclaims


def test_generator_rebuilds_same_legacy_rows(tmp_path: Path) -> None:
    output = tmp_path / "theorem_to_test_map_legacy_tsc.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(GENERATOR),
            "--write",
            str(output),
            "--generated-on",
            "2026-06-13T00:00:00+00:00",
            "--git-state",
            "test-state",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    regenerated = json.loads(output.read_text(encoding="utf-8"))
    current = _payload()
    assert regenerated["theorems"] == current["theorems"]
    ignored = {"generated_on", "generating_command", "git_commit_or_worktree_state"}
    assert {
        key: value
        for key, value in regenerated["metadata"].items()
        if key not in ignored
    } == {
        key: value for key, value in current["metadata"].items() if key not in ignored
    }
    assert str(GENERATOR.relative_to(REPO_ROOT)) in "\n".join(
        current["metadata"]["input_hashes"]
    )
    assert regenerated["metadata"]["generating_command"].endswith(
        "scripts/codex_harness/generate_theorem_to_test_map.py "
        f"--write {output} --generated-on 2026-06-13T00:00:00+00:00 "
        "--git-state test-state"
    )


def test_deprecation_doc_and_json_pass_claim_language_guard() -> None:
    issues = []
    issues.extend(scan_text(ARTIFACT.read_text(encoding="utf-8"), path=ARTIFACT))
    issues.extend(scan_text(DOC.read_text(encoding="utf-8"), path=DOC))

    assert not issues, render_issues(issues)


def test_deprecation_doc_states_non_consumption_boundary() -> None:
    text = DOC.read_text(encoding="utf-8").lower()

    for phrase in (
        "legacy theorem-to-test audit map",
        "audit only",
        "validation obligations",
        "tsc_legacy",
        "diagnostic-only",
        "not production validation",
        "not htt evidence",
        "not a mio certificate",
        "not native solver validation",
        "not family identification",
    ):
        assert phrase in text
