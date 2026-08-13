#!/usr/bin/env python3
"""Metadata-only fail-closed oracle for the final PR-291 quantifier closeout."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[5]
RUN_ID = "pr291-r5-quantifier-continuation-20260813"
ASSIGNMENT_ID = "A-PR291-R5-QUANTIFIER-CLOSEOUT"
CONTEXT_VERSION = "e9b385d7fbc4f8e47c97c3b0c7edae4e522d9be4e025d9342e26ab24829e3019"
SEAL_PATH = ".prguard/runtime/PR291_R5_QUANTIFIER_FINAL_CANDIDATE_SEAL.json"
SEAL_FILE_SHA256 = "4f9119ff3e38f2faea43086bb4276aa116cb2d47f830d13dfa8e7886d2df4071"
CANDIDATE_SHA = "38802323415fe7dc88f63e58d53b316ec9b52c04"
CANDIDATE_TREE = "602a35f0e6e5063ff6677cf2913521975126f588"
BASE_SHA = "06ac20605ebc371b0f97ad6e91c802a51a9bf764"
PRODUCTION_HASH = "01a620679c8ae134752cd92f0a8863254b1ac3d8abb16888c3860bdfa47fa9e7"

PATHS = {
    "assignment": f".agent-harness/runs/{RUN_ID}/assignments/{ASSIGNMENT_ID}.json",
    "index": ".agent-harness/context/CONTEXT_INDEX.json",
    "plan": f".agent-harness/runs/{RUN_ID}/RUN_PLAN.json",
    "seal": SEAL_PATH,
    "spec": "docs/research_program/post_pr275/pr291_spec.yaml",
    "policy": "docs/research_program/post_pr275/pr291_publication_policy.json",
    "delta": "docs/PR_DELTAS/pr-291.md",
    "status": "docs/codex_handoff/pr_status.yaml",
    "status_mirror": "machine_readable/pr_status.yaml",
    "receipt": "docs/research_program/post_pr275/data_runs/cf4/PR291_NONEXECUTION_RECEIPT.json",
    "r5_summary": ".agent-harness/runs/pr291-authorized-r5-review-20260813/RUN_SUMMARY.json",
    "extension_summary": ".agent-harness/runs/pr291-r5-claim-closeout-extension-20260813/RUN_SUMMARY.json",
    "reauth_summary": ".agent-harness/runs/pr291-r5-claim-reauthorization-20260813/RUN_SUMMARY.json",
    "code": ".agent-harness/runs/pr291-authorized-r5-review-20260813/results/A-PR291-R5-CODE-REPLAY.json",
    "physstat": ".agent-harness/runs/pr291-authorized-r5-review-20260813/results/A-PR291-R5-PHYSSTAT.json",
    "extension_claim": ".agent-harness/runs/pr291-r5-claim-closeout-extension-20260813/results/A-PR291-R5-CLAIM.json",
    "reauth_claim": ".agent-harness/runs/pr291-r5-claim-reauthorization-20260813/results/A-PR291-R5-CLAIM-CODE-REVIEW.json",
    "current_claim": f".agent-harness/runs/{RUN_ID}/results/A-PR291-R5-QUANTIFIER-CLAIM.json",
}

EXPECTED_HASHES = {
    "seal": SEAL_FILE_SHA256,
    "spec": "7b074bbb2f22ae62d2222e0bd8f62c0fd5253fe28ac5fca0ce45d956c0ac69ec",
    "policy": "2354087be93139b2740ea8f6eeacc27f73a287d418fc35fcc012fcc6cf1fb835",
    "delta": "2255e7764f6a14cc67da29f6b2e706dc104b7bf662172fc4d787520b65cbd271",
    "status": "01bad28ab094812487a2f385b8aba4e03ff38b5efe78d284ea1582c36542cc05",
    "status_mirror": "01bad28ab094812487a2f385b8aba4e03ff38b5efe78d284ea1582c36542cc05",
    "receipt": "e8dd1f72a87ed7937836784e3495db8a6f3aeb2b983a532d8bd0e119311150d6",
    "r5_summary": "c7d6e35b85d8cb89ee4e7fa75b48c920a264655edac63c85f852d7457237f96a",
    "extension_summary": "2dbc371052f7e95b7fef911a69cdacd20baf4833073c0984e4f7056d771c3805",
    "reauth_summary": "39c378ed9029d338ec929cb6f690d7f4c6f6ddd2945856b5c2b21f607279ff6b",
}

NUMERICAL_FILES = {
    "htt/obsstat/cf4_post275_lane.py",
    "htt/src/common/cf4_observed_lane_activation.py",
    "scripts/codex_harness/run_pr291_cf4_lane.py",
    "tests/integration/test_cf4_post275_lane.py",
}


def read_bytes(key: str) -> bytes:
    return (ROOT / PATHS[key]).read_bytes()


def read_json(key: str) -> dict:
    return json.loads(read_bytes(key))


def git(*args: str, input_bytes: bytes | None = None) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return proc.stdout.decode("utf-8").strip()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    checks: list[str] = []

    assignment = read_json("assignment")
    index = read_json("index")
    plan = read_json("plan")
    seal = read_json("seal")
    policy = read_json("policy")
    receipt = read_json("receipt")
    code = read_json("code")
    physstat = read_json("physstat")
    extension_claim = read_json("extension_claim")
    reauth_claim = read_json("reauth_claim")
    current_claim = read_json("current_claim")
    r5_summary = read_json("r5_summary")
    extension_summary = read_json("extension_summary")
    reauth_summary = read_json("reauth_summary")
    status_bytes = read_bytes("status")
    status = yaml.safe_load(status_bytes)

    require(index["context_version"] == CONTEXT_VERSION, "context version drift")
    require(assignment["context_version"] == CONTEXT_VERSION, "assignment context drift")
    require(assignment["assignment_sha256"] == "b9fbc3332ea81b34fc53a17b0ab3fb3b8ad1e00f8683959b2113167c40904a42", "assignment seal drift")
    require(assignment["independence_mode"] == "adjudication", "wrong independence mode")
    checks.append("context_and_assignment_binding")

    for key, expected in EXPECTED_HASHES.items():
        actual = hashlib.sha256(read_bytes(key)).hexdigest()
        require(actual == expected, f"required input hash drift: {key}")
    require(status_bytes == read_bytes("status_mirror"), "status mirror differs")
    checks.append("required_input_hashes_and_status_mirror")

    binding = assignment["candidate_binding"]
    for key, expected in {
        "seal_path": SEAL_PATH,
        "seal_file_sha256": SEAL_FILE_SHA256,
        "seal_sha256": seal["seal_sha256"],
        "base_sha": BASE_SHA,
        "candidate_sha": CANDIDATE_SHA,
        "merge_base_sha": BASE_SHA,
        "candidate_tree_sha": CANDIDATE_TREE,
        "production_hash": PRODUCTION_HASH,
    }.items():
        require(binding[key] == expected, f"candidate binding drift: {key}")
    require(git("rev-parse", "HEAD") == CANDIDATE_SHA, "HEAD drift")
    require(git("rev-parse", "HEAD^{tree}") == CANDIDATE_TREE, "tree drift")
    require(git("merge-base", "HEAD", BASE_SHA) == BASE_SHA, "merge-base drift")
    require(git("status", "--porcelain", "--untracked-files=no") == "", "tracked tree dirty")
    checks.append("frozen_candidate_identity_and_clean_tree")

    commits = git("rev-list", "--reverse", f"{BASE_SHA}..HEAD").splitlines()
    require(commits == seal["candidate_commits"], "candidate commit list drift")
    patch_rows = seal["stable_patch_ids"]
    patch_ids = [row["stable_patch_id"] for row in patch_rows]
    require(len(patch_ids) == len(set(patch_ids)) == len(commits), "stable patch IDs are not unique")
    require([row["commit"] for row in patch_rows] == commits, "patch/commit ordering drift")
    for row in patch_rows:
        patch = subprocess.run(
            ["git", "show", "--pretty=format:", "--binary", row["commit"]],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        ).stdout
        computed = git("patch-id", "--stable", input_bytes=patch).split()[0]
        require(computed == row["stable_patch_id"], f"stable patch ID drift: {row['commit']}")
    checks.append("unique_recomputed_stable_patch_ids")

    require(plan["lifecycle_state"] == "VALIDATED", "run plan lifecycle drift")
    require(plan["assurance_budget"] == {"maximum": 16, "consumed": 16}, "ordinary budget drift")
    exception = plan["budget_exception"]
    require(exception["additional_assignments"] == 2, "continuation size drift")
    require(exception["allowed_assignment_ids"] == ["A-PR291-R5-QUANTIFIER-CLAIM", ASSIGNMENT_ID], "continuation assignments drift")
    require(exception["single_use"] is True and exception["cumulative_start"] == 20, "continuation boundary drift")
    checks.append("ordinary_16_of_16_and_current_continuation_projected_2_of_2")

    stack = status["stacked_pr_execution"]
    pr291 = stack["prs"]["PR-291"]
    pr292 = stack["prs"]["PR-292"]
    require(stack["merge_policy"] == "HUMAN_ONLY", "merge policy drift")
    require(pr291["lifecycle"] == "VALIDATED", "PR-291 promoted despite failed claim")
    require(pr291["sealed_head"] is None and pr291["pushed_ref"] is None and pr291["pr_url"] is None, "publication state mutated")
    require(pr291["assurance_budget"] == {"maximum": 16, "consumed": 16}, "ordinary status budget drift")
    require(pr291["authorized_assurance_extension_consumed"] == pr291["authorized_assurance_extension_maximum"] == 2, "first extension not 2/2")
    require(pr291["authorized_assurance_reauthorization_consumed"] == pr291["authorized_assurance_reauthorization_maximum"] == 2, "reauthorization not 2/2")
    require(pr291["authorized_assurance_continuation_maximum"] == 2, "continuation maximum drift")
    require(pr292["lifecycle"] == "PLANNED" and pr292["gate_dispositions"]["eligibility"] == "INELIGIBLE", "PR-292 activated early")
    require(pr292["predecessor_sealed_sha"] is None and pr292["assurance_budget"]["consumed"] == 0, "PR-292 received unauthorized work")
    checks.append("validated_human_only_no_publication_and_pr292_ineligible")

    require([row["status"] for row in r5_summary["results"]] == ["pass", "pass"], "carried R5 pass chronology drift")
    require(code["status"] == physstat["status"] == "pass", "carried lane no longer PASS")
    require(code["gate_disposition"] == physstat["gate_disposition"] == "PASS", "carried lane gate drift")
    require(extension_claim["status"] == extension_claim["gate_disposition"].lower() == "fail", "first claim failure drift")
    require(reauth_claim["status"] == reauth_claim["gate_disposition"].lower() == "fail", "quantifier claim failure drift")
    require([row["status"] for row in extension_summary["results"]] == ["fail", "fail"], "first failed closeout chronology drift")
    require([row["status"] for row in reauth_summary["results"]] == ["fail", "fail"], "second failed closeout chronology drift")
    require(all(summary["lifecycle_state"] == "VALIDATED" for summary in (r5_summary, extension_summary, reauth_summary)), "historical lifecycle drift")
    checks.append("carried_pass_and_prior_fail_chronology")

    changed_since_carried = set(git("diff", "--name-only", "5395853386b08b1fbf0b56a9e6c7a2a6e104ae5a..HEAD").splitlines())
    require(changed_since_carried.isdisjoint(NUMERICAL_FILES), "carried numerical file changed")
    require(pr291["production_hash"] == plan["production_hash"] == PRODUCTION_HASH, "production hash drift")
    for key in ("pr291_common_module", "pr291_obsstat_module", "pr291_runner", "pr291_contract_test"):
        require(pr291["dependency_hashes"][key] == plan["dependency_hashes"][key], f"numerical dependency drift: {key}")
    checks.append("unchanged_numerical_hashes_carry_code_replay_physstat")

    require(current_claim["status"] == "fail" and current_claim["gate_disposition"] == "FAIL", "fresh claim is not strict FAIL")
    require(len(current_claim["findings"]) == 1, "unexpected current finding count")
    finding = current_claim["findings"][0]
    require(finding["finding_id"] == "F-PR291-R5-QUANTIFIER-CLAIM-001", "current finding identity drift")
    require(finding["severity"] == "high" and finding["verdict"] == "fail", "current finding severity/verdict drift")
    require("seven" in finding["statement"].lower(), "seven-bypass statement missing")
    require("reordered passive" in current_claim["claim_results"][0]["summary"], "passive/scalar family bypass summary missing")
    checks.append("fresh_claim_strict_fail_seven_false_negatives")

    require(policy["claim_ceiling"] == "diagnostic_only", "claim ceiling drift")
    require(policy["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS", "family gate drift")
    require(policy["ordinary_agent_push_forbidden"] is True, "push firewall relaxed")
    require(policy["ordinary_agent_pr_mutation_forbidden"] is True, "PR firewall relaxed")
    require(len(policy["required_review_cells"]) == len(set(policy["required_review_cells"])) == 16, "review policy is not exact 16-cell")
    checks.append("claim_firewall_and_exact_16_cell_policy")

    decision = receipt["decision"]
    require(decision["terminal"] == "BLOCKED_PREDECESSOR_FINAL_SUCCESS", "nonexecution terminal drift")
    require(decision["observed_data_executed"] is False, "observed data executed")
    require(decision["numeric_outputs_written"] == [], "numeric outputs written")
    require(decision["network_or_download_side_effect"] is False, "network side effect recorded")
    require(decision["public_use"] is False, "public use recorded")
    require(receipt["claim_tier"] == "diagnostic_only" and receipt["transfer_source"] == "none", "receipt claim metadata drift")
    checks.append("blocked_nonexecution_receipt")

    print(json.dumps({
        "oracle": ASSIGNMENT_ID,
        "status": "PASS",
        "candidate_disposition": "FAIL",
        "lifecycle": "VALIDATED",
        "review_eligibility": "BLOCKED",
        "seal_eligibility": "BLOCKED",
        "pr292": "PLANNED_INELIGIBLE",
        "publication": "NONE_HUMAN_ONLY",
        "ordinary_budget": "16/16",
        "prior_extensions": ["2/2", "2/2"],
        "current_continuation": "2/2_after_this_closeout",
        "checks": checks,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
