#!/usr/bin/env python3
"""Read-only oracle for the frozen PR-290 replay/claim review.

The oracle deliberately does not read sibling results or aggregate harness state.
It validates only the registered assignment, its named inputs, the frozen seal,
the candidate Git graph, and the PR-290 policy/status/receipt contracts.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import yaml


RUN_ID = "pr290-frozen-independent-review-20260811"
ASSIGNMENT_ID = "A-PR290-FROZEN-REPLAYCLAIM"
CONTEXT_VERSION = "e9b385d7fbc4f8e47c97c3b0c7edae4e522d9be4e025d9342e26ab24829e3019"
ROOT = Path(__file__).resolve().parents[4]
ASSIGNMENT = ROOT / ".agent-harness/runs" / RUN_ID / "assignments" / f"{ASSIGNMENT_ID}.json"
CONTEXT_INDEX = ROOT / ".agent-harness/context/CONTEXT_INDEX.json"
SEAL = ROOT / ".prguard/runtime/PR290_VALIDATED_CANDIDATE_SEAL.json"
SPEC = ROOT / "docs/research_program/post_pr275/pr290_spec.yaml"
POLICY = ROOT / "docs/research_program/post_pr275/pr290_publication_policy.json"
RECEIPT = ROOT / "docs/research_program/post_pr275/data_runs/planck/PR290_NONEXECUTION_RECEIPT.json"
STATUS = ROOT / "docs/codex_handoff/pr_status.yaml"
STATUS_MIRROR = ROOT / "machine_readable/pr_status.yaml"
DELTA = ROOT / "docs/PR_DELTAS/pr-290.md"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_hash(payload: object) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return sha256_bytes(encoded)


def git(*args: str, input_bytes: bytes | None = None) -> bytes:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    ).stdout


def patch_id(commit: str) -> str:
    patch = git("show", "--pretty=format:", commit)
    output = git("patch-id", "--stable", input_bytes=patch).decode("ascii").split()
    if not output:
        raise RuntimeError(f"commit {commit} has no stable patch ID")
    return output[0]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    assignment = json.loads(ASSIGNMENT.read_text(encoding="utf-8"))
    context = json.loads(CONTEXT_INDEX.read_text(encoding="utf-8"))
    seal = json.loads(SEAL.read_text(encoding="utf-8"))
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    status = yaml.safe_load(STATUS.read_text(encoding="utf-8"))
    delta = DELTA.read_text(encoding="utf-8")

    cells: list[dict[str, object]] = []

    def cell(cell_id: str, checks: dict[str, bool], evidence: list[str]) -> None:
        for label, passed in checks.items():
            require(passed, f"{cell_id}: {label}")
        cells.append(
            {
                "cell_id": cell_id,
                "status": "PASS",
                "checks": checks,
                "evidence": evidence,
            }
        )

    require(assignment["run_id"] == RUN_ID, "run ID drifted")
    require(assignment["assignment_id"] == ASSIGNMENT_ID, "assignment ID drifted")
    require(assignment["context_version"] == CONTEXT_VERSION, "assignment context drifted")
    require(context["context_version"] == CONTEXT_VERSION, "context index drifted")
    for item in assignment["required_inputs"]:
        actual = sha256_bytes((ROOT / item["path"]).read_bytes())
        require(actual == item["sha256"], f"required input drifted: {item['path']}")

    unsigned_seal = dict(seal)
    declared_seal_hash = unsigned_seal.pop("seal_sha256")
    commits = seal["candidate_commits"]
    recomputed_patch_ids = [patch_id(commit) for commit in commits]
    declared_patch_ids = [row["stable_patch_id"] for row in seal["stable_patch_ids"]]
    changed = [
        {"status": line.split("\t", 1)[0], "path": line.split("\t", 1)[1]}
        for line in git("diff", "--name-status", seal["base_sha"], seal["candidate_sha"])
        .decode("utf-8")
        .splitlines()
        if line
    ]
    pr289 = status["stacked_pr_execution"]["prs"]["PR-289"]
    cell(
        "candidate_identity",
        {
            "head_matches_candidate": git("rev-parse", "HEAD").decode().strip() == seal["candidate_sha"],
            "tree_matches_seal": git("rev-parse", "HEAD^{tree}").decode().strip() == seal["candidate_tree_sha"],
            "merge_base_matches": git("merge-base", seal["base_sha"], seal["candidate_sha"]).decode().strip() == seal["merge_base_sha"],
            "seal_self_hash_matches": canonical_hash(unsigned_seal) == declared_seal_hash,
            "patch_ids_recompute": recomputed_patch_ids == declared_patch_ids,
            "patch_ids_unique": len(set(recomputed_patch_ids)) == len(recomputed_patch_ids),
            "changed_files_match": changed == seal["changed_files"],
            "pr289_exact_sealed_base": pr289["sealed_head"] == seal["base_sha"] == policy["target_sha"],
            "g49_g50_g51_g52_g53_selection_recorded": all(token in delta for token in ("G49", "G50", "G51", "G52", "G53")),
            "g54_and_historical_receipt_excluded": "Excluded obsolete G54" in delta and [p for p in git("ls-files", "docs/research_program/post_pr275/data_runs/planck").decode().splitlines() if "PR290" in p] == ["docs/research_program/post_pr275/data_runs/planck/PR290_NONEXECUTION_RECEIPT.json"],
        },
        [str(SEAL.relative_to(ROOT)), str(DELTA.relative_to(ROOT)), "git graph and stable patch IDs"],
    )

    boundary = spec["scientific_boundary"]
    output = spec["output_contract"]
    cell(
        "spec_before_execution",
        {
            "preactivation_only": output["current_allowed_outputs"] == ["preactivation_nonexecution_receipt", "synthetic_operator_test_evidence"],
            "observed_outputs_forbidden": "observed_p_value_or_exceedance" in output["current_forbidden_outputs"],
            "future_result_disabled": output["future_observed_result_contract"]["current_status"] == "DISABLED_PREACTIVATION",
            "preflight_before_payload": output["output_containment"]["preflight_before_payload_generation"] is True,
        },
        [str(SPEC.relative_to(ROOT)), "tests/integration/test_planck_post275_lane.py"],
    )

    dependency = {row["pr_id"]: row for row in receipt["dependency_snapshot"]}
    pr287_status = status["stacked_pr_execution"]["prs"]["PR-287"]
    cell(
        "dependency_terminal_replay",
        {
            "typed_predecessor_terminal": receipt["terminal"] == "BLOCKED_PREDECESSOR_FINAL_SUCCESS",
            "pr287_not_regraded": pr287_status["gate_dispositions"]["fresh_execution"] == "INCONCLUSIVE",
            "pr287_receipt_absent": dependency["PR-287"]["terminal_receipt"]["satisfied"] is False,
            "pr288_receipt_bound": dependency["PR-288"]["terminal_receipt"]["file_sha256"] == "sha256:" + sha256_bytes((ROOT / "docs/generated/pr288_bayesian_semantics_receipt.json").read_bytes()),
            "pr289_receipt_bound": dependency["PR-289"]["terminal_receipt"]["file_sha256"] == "sha256:" + sha256_bytes((ROOT / "docs/generated/pr289_data_identity_v2_receipt.json").read_bytes()),
        },
        [str(RECEIPT.relative_to(ROOT)), str(STATUS.relative_to(ROOT))],
    )

    data_snapshot = receipt["data_identity_snapshot"]
    human = receipt["human_gate_snapshot"]
    cell(
        "data_identity_and_human_authorization_separation",
        {
            "identity_not_admitted": data_snapshot["admission_status"] == "REJECTED_NOT_PRESENT" and data_snapshot["satisfied"] is False,
            "human_not_authorized": human["status"] == "NOT_AUTHORIZED" and human["satisfied"] is False,
            "distinct_gate": data_snapshot["required_human_gate_id"] == human["gate_id"] == "H-PLANCK",
            "no_authorization_receipt": human["receipt_sha256"] is None,
        },
        [str(RECEIPT.relative_to(ROOT)), str(SPEC.relative_to(ROOT))],
    )

    tests_text = (ROOT / "tests/integration/test_planck_post275_lane.py").read_text(encoding="utf-8")
    runner_text = (ROOT / "scripts/codex_harness/run_pr290_planck_lane.py").read_text(encoding="utf-8")
    obsstat_text = (ROOT / "htt/obsstat/planck_post275_lane.py").read_text(encoding="utf-8")
    cell(
        "preflight_before_first_write",
        {
            "hardlink_preflight_test": "test_output_preflight_rejects_hardlink_before_payload_generation" in tests_text,
            "symlink_preflight_test": "test_output_preflight_rejects_symlink_parent_and_existing_result_directory" in tests_text,
            "atomic_recheck_test": "test_atomic_write_rechecks_results_after_directory_fsync" in tests_text,
            "runner_atomic_write": "def _atomic_write(" in runner_text,
        },
        ["scripts/codex_harness/run_pr290_planck_lane.py", "tests/integration/test_planck_post275_lane.py"],
    )

    snapshot = receipt["operator_snapshot"]
    cell(
        "synthetic_operator_identity",
        {
            "local_boost_synthetic_only": snapshot["response_and_active_estimand_status"]["local_boost"] == "synthetic_operator_contract_only",
            "fixture_disallows_observed_claims": "observed_number" in spec["pipeline_contract"]["synthetic_contract_fixture"]["cannot_support"],
            "exact_boost_zero_test": "test_exact_boost_zero_is_finite_identity_and_domain_is_checked" in tests_text,
        },
        ["htt/obsstat/boost_biposh_residual.py", "htt/obsstat/planck_post275_lane.py", str(SPEC.relative_to(ROOT))],
    )

    pipeline = spec["pipeline_contract"]
    cell(
        "observation_null_pipeline_equivalence",
        {
            "identical_pipeline_required": pipeline["identical_observation_null_pipeline"] is True,
            "identity_enforcer_present": "def require_common_operator_identity(" in obsstat_text,
            "both_components_required": "REQUIRED_COMPONENTS = (\"SMICA\", \"Commander\")" in obsstat_text,
        },
        ["htt/obsstat/planck_post275_lane.py", str(SPEC.relative_to(ROOT))],
    )

    mask = pipeline["mask_beam_contract"]
    units = pipeline["harmonic_and_unit_contract"]
    cell(
        "mask_beam_harmonic_conventions",
        {
            "mask_deconvolution_blocked": mask["current_status"] == "BLOCKED_UNDECONVOLVED",
            "target_beam_unbound": mask["target_beam_id"] is None,
            "harmonic_convention_frozen": units["scalar_harmonics"] == "orthonormal_Condon_Shortley",
            "biposh_units_typed": units["biposh_A_units"] == "microK_CMB^2" and units["biposh_D_units"] == "microK_CMB^4",
        },
        [str(SPEC.relative_to(ROOT)), "htt/obsstat/planck_post275_lane.py"],
    )

    covariance = pipeline["covariance_contract"]
    cell(
        "full_covariance_and_null_contract",
        {
            "diagonal_forbidden": covariance["diagonal_shortcut_allowed"] is False,
            "feature_covariance_blocked": covariance["current_status"] == "BLOCKED_FEATURE_VECTOR_UNREGISTERED",
            "null_not_executed": receipt["owner_scope_and_claim_boundary"]["null_mock_status"] == "NOT_EXECUTED",
            "full_covariance_validator_present": "def validate_full_joint_covariance(" in obsstat_text,
        },
        [str(SPEC.relative_to(ROOT)), str(RECEIPT.relative_to(ROOT)), "htt/obsstat/planck_post275_lane.py"],
    )

    rank = pipeline["global_rank_contract"]
    cell(
        "look_elsewhere_and_component_replication",
        {
            "observation_inclusive_rank": rank["estimator"] == "observation_inclusive_leave_one_out_pooled_max_rank",
            "conservative_ties": rank["tie_policy"] == "conservative_greater_or_equal",
            "both_components": pipeline["observation_products"] == ["SMICA", "Commander"],
            "component_replication_tested": "test_common_operator_identity_and_full_covariance_fail_closed" in tests_text,
        },
        [str(SPEC.relative_to(ROOT)), "htt/obsstat/planck_post275_lane.py", "tests/integration/test_planck_post275_lane.py"],
    )

    result_directory = ROOT / output["observed_result_directory"]
    cell(
        "blocked_no_numeric_output",
        {
            "zero_numeric_outputs": receipt["numeric_outputs_written"] == [],
            "observed_false": receipt["observed_data_executed"] is False,
            "network_false": receipt["network_or_download_side_effect"] is False,
            "public_false": receipt["public_use"] is False,
            "result_directory_absent": not result_directory.exists(),
        },
        [str(RECEIPT.relative_to(ROOT)), "python3 -B scripts/codex_harness/run_pr290_planck_lane.py check"],
    )

    command_ids = [row["id"] for row in policy["required_commands"]]
    cell(
        "portable_clean_integration",
        {
            "portable_command_registered": "pr290-portable-clean" in command_ids,
            "portable_requires_clean_head": "portable replay requires a clean committed candidate" in runner_text,
            "clean_archive_execution": "git\", \"archive\", \"HEAD" in runner_text,
            "environment_scrubbed": "HTT_H_PLANCK_AUTHORITY_KEY_FILE" in runner_text and "PYTHONPATH" in runner_text,
        },
        [str(POLICY.relative_to(ROOT)), "scripts/codex_harness/run_pr290_planck_lane.py"],
    )

    cell(
        "publication_policy_cross_binding",
        {
            "seven_commands": len(policy["required_commands"]) == 7,
            "policy_hash_in_seal": seal["integration_policy"]["sha256"] == sha256_bytes(POLICY.read_bytes()),
            "policy_identity_in_seal": seal["integration_policy"]["policy_id"] == policy["policy_id"],
            "publication_mutation_forbidden": policy["ordinary_agent_pr_mutation_forbidden"] is True,
        },
        [str(SEAL.relative_to(ROOT)), str(POLICY.relative_to(ROOT))],
    )

    owner_boundary = receipt["owner_scope_and_claim_boundary"]
    cell(
        "claim_and_family_ceiling",
        {
            "c2_diagnostic_only": boundary["claim_level"] == {"scheme": "roadmap_rescue_v1", "level": "C2"} and boundary["claim_tier"] == "diagnostic_only",
            "transfer_none": boundary["transfer_source"] == owner_boundary["transfer_source"] == "none",
            "observed_and_public_false": boundary["observed_data_executed"] is False and boundary["public_use"] is False,
            "family_gate_blocked": boundary["family_identification_gate"] == receipt["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS",
            "owners_separated": owner_boundary["artifact_owners"] == {"activation_manifests_and_semantic_guards": "COMMON", "model_dependent_inference": "HTT_NOT_EXECUTED", "observable_features_and_null_features": "OBSSTAT"},
        },
        [str(SPEC.relative_to(ROOT)), str(RECEIPT.relative_to(ROOT)), str(DELTA.relative_to(ROOT))],
    )

    stack = status["stacked_pr_execution"]
    pr290 = stack["prs"]["PR-290"]
    pr291 = stack["prs"]["PR-291"]
    cell(
        "latest_target_integration",
        {
            "status_mirror_identical": STATUS.read_bytes() == STATUS_MIRROR.read_bytes(),
            "human_only_merge": stack["merge_policy"] == "HUMAN_ONLY",
            "pr290_validated": pr290["lifecycle"] == "VALIDATED" and pr290["sealed_head"] is None and pr290["pushed_ref"] is None,
            "pr291_ineligible_zero_budget": pr291["gate_dispositions"] == {"eligibility": "INELIGIBLE"} and pr291["assurance_budget"]["consumed"] == 0,
            "target_exact": policy["target_sha"] == seal["base_sha"] and policy["target_ref"] == "origin/changeset/pr289-native-data-identity-recovery-20260811",
        },
        [str(STATUS.relative_to(ROOT)), str(STATUS_MIRROR.relative_to(ROOT)), str(POLICY.relative_to(ROOT))],
    )

    required_cells = policy["required_review_cells"]
    require([row["cell_id"] for row in cells] == required_cells, "review cell order/inventory drifted")
    payload = {
        "schema": "htt.pr290.frozen_replay_claim_oracle.v1",
        "run_id": RUN_ID,
        "assignment_id": ASSIGNMENT_ID,
        "context_version": CONTEXT_VERSION,
        "status": "PASS",
        "cell_count": len(cells),
        "cells": cells,
    }
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(
            json.dumps(
                {
                    "schema": "htt.pr290.frozen_replay_claim_oracle.v1",
                    "run_id": RUN_ID,
                    "assignment_id": ASSIGNMENT_ID,
                    "context_version": CONTEXT_VERSION,
                    "status": "FAIL",
                    "error": f"{type(exc).__name__}: {exc}",
                },
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        raise SystemExit(1)
