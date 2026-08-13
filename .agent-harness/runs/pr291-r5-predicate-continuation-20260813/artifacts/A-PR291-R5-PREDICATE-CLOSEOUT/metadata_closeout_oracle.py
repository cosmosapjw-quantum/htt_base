#!/usr/bin/env python3
"""Metadata-only fail-closed oracle for the PR-291 predicate closeout."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[5]
RUN_ID = "pr291-r5-predicate-continuation-20260813"
ASSIGNMENT_ID = "A-PR291-R5-PREDICATE-CLOSEOUT"
CONTEXT_VERSION = "e9b385d7fbc4f8e47c97c3b0c7edae4e522d9be4e025d9342e26ab24829e3019"
BASE_SHA = "06ac20605ebc371b0f97ad6e91c802a51a9bf764"
CANDIDATE_SHA = "c39e57e5638a63e023783fb962521799ce87866b"
CANDIDATE_TREE = "62026afc31a915dc7f96c718fcc654c71a8ed53a"
PRODUCTION_HASH = "ba3cec1bec67dbbec36903374d00155467e8623af7aa07dfb2fb47b32e90000b"
SEAL_PATH = ".prguard/runtime/PR291_R5_PREDICATE_FINAL_CANDIDATE_SEAL.json"

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
    "quantifier_summary": ".agent-harness/runs/pr291-r5-quantifier-continuation-20260813/RUN_SUMMARY.json",
    "code": ".agent-harness/runs/pr291-authorized-r5-review-20260813/results/A-PR291-R5-CODE-REPLAY.json",
    "physstat": ".agent-harness/runs/pr291-authorized-r5-review-20260813/results/A-PR291-R5-PHYSSTAT.json",
    "claim": f".agent-harness/runs/{RUN_ID}/results/A-PR291-R5-PREDICATE-CLAIM.json",
}

EXPECTED_HASHES = {
    "seal": "be541b2933e7283cf5c0759bdf2eba8e22c75983d75f2e5edfc3f9dd7d6b6812",
    "spec": "7b074bbb2f22ae62d2222e0bd8f62c0fd5253fe28ac5fca0ce45d956c0ac69ec",
    "policy": "2354087be93139b2740ea8f6eeacc27f73a287d418fc35fcc012fcc6cf1fb835",
    "delta": "6eaeeb89ee33b4b38a147b33aefffea279f0e50403631ba2fc2ceb9da2d78096",
    "status": "aceafd6cf516b8b20057cfb52a504f08a40e59a97c79e891c7e4f0f3b038ae69",
    "status_mirror": "aceafd6cf516b8b20057cfb52a504f08a40e59a97c79e891c7e4f0f3b038ae69",
    "receipt": "f1d3c5b187e90dc5c2b703b0fd195068d999d838fb96dbdfb3164a79703bcfc3",
    "r5_summary": "c7d6e35b85d8cb89ee4e7fa75b48c920a264655edac63c85f852d7457237f96a",
    "extension_summary": "2dbc371052f7e95b7fef911a69cdacd20baf4833073c0984e4f7056d771c3805",
    "reauth_summary": "39c378ed9029d338ec929cb6f690d7f4c6f6ddd2945856b5c2b21f607279ff6b",
    "quantifier_summary": "950b41ec72bef52747ac09e40ce15eb16a2ce75ad549bb586a39621c834f4574",
    "code": "7ed84261bd6cc28d4bc66f22a2e5c36e503ed35ea7fd660545b762ceec383ce6",
    "physstat": "52217e596fff19d74e6389929d188ba040a6e3ae363375fbde41652b19453de6",
    "claim": "a26e09d90be648f4b3868a9d21ebae92dedf52773ce1e05744f818689b09128a",
}

NUMERICAL_FILES = {
    "htt/obsstat/cf4_post275_lane.py",
    "htt/src/common/cf4_observed_lane_activation.py",
    "scripts/codex_harness/run_pr291_cf4_lane.py",
    "tests/integration/test_cf4_post275_lane.py",
}


def data(key: str) -> bytes:
    return (ROOT / PATHS[key]).read_bytes()


def obj(key: str) -> dict:
    return json.loads(data(key))


def git(*args: str, input_bytes: bytes | None = None) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, input=input_bytes,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    return result.stdout.decode().strip()


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def main() -> int:
    checks: list[str] = []
    assignment, index, plan, seal = map(obj, ("assignment", "index", "plan", "seal"))
    policy, receipt, claim = map(obj, ("policy", "receipt", "claim"))
    code, physstat = obj("code"), obj("physstat")
    histories = [obj(k) for k in ("r5_summary", "extension_summary", "reauth_summary", "quantifier_summary")]
    status_bytes = data("status")
    status = yaml.safe_load(status_bytes)["stacked_pr_execution"]

    require(index["context_version"] == assignment["context_version"] == CONTEXT_VERSION, "context drift")
    require(assignment["assignment_sha256"] == "6738a3ba31af57a446cdd3d7a9f4f30a4957b004a9ea2bbaab04046890a8ea5b", "assignment seal drift")
    require(assignment["independence_mode"] == "adjudication", "independence mode drift")
    for key, expected in EXPECTED_HASHES.items():
        require(hashlib.sha256(data(key)).hexdigest() == expected, f"required input drift: {key}")
    require(status_bytes == data("status_mirror"), "status mirrors differ")
    checks.append("registered_context_inputs_and_status_mirror")

    binding = assignment["candidate_binding"]
    expected_binding = {
        "seal_path": SEAL_PATH, "seal_file_sha256": EXPECTED_HASHES["seal"],
        "seal_sha256": seal["seal_sha256"], "base_sha": BASE_SHA,
        "candidate_sha": CANDIDATE_SHA, "merge_base_sha": BASE_SHA,
        "candidate_tree_sha": CANDIDATE_TREE, "production_hash": PRODUCTION_HASH,
    }
    require(all(binding[k] == v for k, v in expected_binding.items()), "candidate binding drift")
    require(git("rev-parse", "HEAD") == CANDIDATE_SHA, "HEAD drift")
    require(git("rev-parse", "HEAD^{tree}") == CANDIDATE_TREE, "tree drift")
    require(git("merge-base", "HEAD", BASE_SHA) == BASE_SHA, "merge-base drift")
    require(git("status", "--porcelain", "--untracked-files=no") == "", "tracked tree dirty")
    commits = git("rev-list", "--reverse", f"{BASE_SHA}..HEAD").splitlines()
    rows = seal["stable_patch_ids"]
    require([r["commit"] for r in rows] == commits, "patch ordering drift")
    require(len({r["stable_patch_id"] for r in rows}) == len(rows) == len(commits), "patch IDs not unique")
    for row in rows:
        patch = subprocess.run(["git", "show", "--pretty=format:", "--binary", row["commit"]], cwd=ROOT, stdout=subprocess.PIPE, check=True).stdout
        require(git("patch-id", "--stable", input_bytes=patch).split()[0] == row["stable_patch_id"], "patch ID drift")
    checks.append("frozen_identity_clean_tree_and_unique_patch_ids")

    pr291, pr292 = status["prs"]["PR-291"], status["prs"]["PR-292"]
    require(plan["lifecycle_state"] == pr291["lifecycle"] == "VALIDATED", "PR-291 lifecycle promoted")
    require(status["merge_policy"] == "HUMAN_ONLY", "merge policy drift")
    require(pr291["sealed_head"] is pr291["pushed_ref"] is pr291["pr_url"] is None, "publication state mutated")
    require(pr292["lifecycle"] == "PLANNED" and pr292["gate_dispositions"]["eligibility"] == "INELIGIBLE", "PR-292 activated")
    require(pr292["predecessor_sealed_sha"] is None and pr292["assurance_budget"]["consumed"] == 0, "PR-292 work recorded")
    checks.append("validated_human_only_unpublished_pr292_ineligible")

    require([r["status"] for r in histories[0]["results"]] == ["pass", "pass"], "R5 PASS chronology drift")
    require(all([r["status"] for r in h["results"]] == ["fail", "fail"] for h in histories[1:]), "FAIL chronology drift")
    require(all(h["lifecycle_state"] == "VALIDATED" for h in histories), "historical lifecycle drift")
    require(code["status"] == physstat["status"] == "pass", "carried PASS drift")
    changed = set(git("diff", "--name-only", "5395853386b08b1fbf0b56a9e6c7a2a6e104ae5a..HEAD").splitlines())
    require(changed.isdisjoint(NUMERICAL_FILES), "numerical files changed after carried review")
    for key in ("pr291_common_module", "pr291_obsstat_module", "pr291_runner", "pr291_contract_test"):
        require(pr291["dependency_hashes"][key] == plan["dependency_hashes"][key], f"numerical hash drift: {key}")
    checks.append("historical_pass_fail_chronology_and_carried_numerical_passes")

    require(plan["assurance_budget"] == {"maximum": 16, "consumed": 16}, "ordinary budget drift")
    ext = plan["budget_exception"]
    require(ext["additional_assignments"] == 2 and ext["cumulative_start"] == 22 and ext["single_use"] is True, "predicate continuation drift")
    require(ext["allowed_assignment_ids"] == ["A-PR291-R5-PREDICATE-CLAIM", ASSIGNMENT_ID], "assignment accounting drift")
    require(pr291["authorized_assurance_extension_consumed"] == pr291["authorized_assurance_extension_maximum"] == 2, "extension accounting drift")
    require(pr291["authorized_assurance_reauthorization_consumed"] == pr291["authorized_assurance_reauthorization_maximum"] == 2, "reauthorization accounting drift")
    require(pr291["authorized_assurance_continuation_consumed"] == pr291["authorized_assurance_continuation_maximum"] == 2, "quantifier continuation accounting drift")
    checks.append("ordinary_16_and_named_extensions_through_cumulative_24")

    require(claim["status"] == "fail" and claim["gate_disposition"] == "FAIL", "claim result not strict FAIL")
    require({f["finding_id"] for f in claim["findings"]} == {"F-PR291-PREDICATE-FALSE-NEGATIVE", "F-PR291-PREDICATE-FALSE-POSITIVE"}, "finding identities drift")
    refs = " ".join(" ".join(f["evidence_refs"]) for f in claim["findings"])
    require("active_generic_actor" in refs and "passive_modal_auxiliary" in refs, "two false negatives absent")
    require(sum("negative_" in ref for f in claim["findings"] for ref in f["evidence_refs"]) >= 1, "negative controls absent")
    require("five" in claim["findings"][1]["statement"].lower(), "five false positives absent")
    checks.append("fresh_predicate_strict_fail_two_fn_five_fp")

    require(len(policy["required_review_cells"]) == len(set(policy["required_review_cells"])) == 16, "review policy not exact 16-cell")
    require(policy["claim_ceiling"] == "diagnostic_only" and policy["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS", "claim firewall drift")
    require(policy["ordinary_agent_push_forbidden"] is True and policy["ordinary_agent_pr_mutation_forbidden"] is True, "publication firewall drift")
    decision = receipt["decision"]
    require(decision["terminal"] == "BLOCKED_PREDECESSOR_FINAL_SUCCESS", "receipt terminal drift")
    require(decision["observed_data_executed"] is False and decision["numeric_outputs_written"] == [], "numeric execution recorded")
    require(decision["network_or_download_side_effect"] is False and decision["public_use"] is False, "side effect/public use recorded")
    require(decision["human_authorization_snapshot"]["ordinary_agent_can_mint"] is False, "ordinary agent can mint H-CF4")
    checks.append("claim_firewall_blocked_nonexecution_and_exact_16_cell_policy")

    print(json.dumps({
        "oracle": ASSIGNMENT_ID, "status": "PASS", "candidate_disposition": "FAIL",
        "lifecycle": "VALIDATED", "review_eligibility": "BLOCKED", "seal_eligibility": "BLOCKED",
        "pr292": "PLANNED_INELIGIBLE", "publication": "NONE_HUMAN_ONLY",
        "ordinary_budget": "16/16", "named_extensions": ["2/2", "2/2", "2/2"],
        "predicate_continuation": "2/2_after_this_closeout", "cumulative_assignments": 24,
        "predicate_mismatches": {"false_negatives": 2, "false_positives": 5}, "checks": checks,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
