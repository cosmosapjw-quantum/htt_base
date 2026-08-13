#!/usr/bin/env python3
"""Independent bounded oracle for the PR-284 stacked-publication policy review."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[5]
SCRIPTS = REPO / ".agent-harness" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from _harness import (  # noqa: E402
    enforce_work_unit_assignment_budget,
    validate_review_rereview_budget_exception,
)
from publication_integrity import (  # noqa: E402
    PublicationIntegrityError,
    classify_publication_command,
    load_publication_policy,
    validate_candidate_seal_payload,
    validate_integration_receipt_payload,
    validate_pr_inventory_payload,
)


RUN_ID = "pr284-stacked-publication-policy-review-20260810"
ASSIGNMENT_ID = "A-PR284-STACK-POLICY"
SEAL_REL = ".prguard/runtime/PR284_STACK_POLICY_CANDIDATE_SEAL.json"
POLICY_REL = "docs/research_program/post_pr275/pr284_publication_policy.json"
INTEGRATION_REL = ".prguard/runtime/PR284_STACK_POLICY_INTEGRATION_REHEARSAL.json"
RUN_PLAN_REL = f".agent-harness/runs/{RUN_ID}/RUN_PLAN.json"
INVENTORY_REL = (
    f".agent-harness/runs/{RUN_ID}/artifacts/{ASSIGNMENT_ID}/live_inventory.json"
)


def load(rel: str) -> dict:
    return json.loads((REPO / rel).read_text(encoding="utf-8"))


def digest(rel: str) -> str:
    return hashlib.sha256((REPO / rel).read_bytes()).hexdigest()


def probe_error(inventory: dict, seal: dict, policy: dict, needle: str) -> str:
    errors = validate_pr_inventory_payload(inventory, seal=seal, policy=policy)
    if len(errors) != 1 or needle not in errors[0]:
        raise AssertionError(f"expected {needle!r}, got {errors!r}")
    return errors[0]


def main() -> None:
    seal = load(SEAL_REL)
    policy_bytes, policy = load_publication_policy(REPO, POLICY_REL)
    integration = load(INTEGRATION_REL)
    plan = load(RUN_PLAN_REL)
    inventory = load(INVENTORY_REL)

    assert digest(SEAL_REL) == "ec986572ee5f5e7854e962004b40e7f3cd6d9527798bb13baa111c88f8bc8476"
    assert digest(POLICY_REL) == "6b19c380a96ddac1f98f0bcb774519d3fe3b555d4411a6f8e8f72876c0758446"
    assert digest(INTEGRATION_REL) == "479364e525cf8c6d759abe9dde90a711094ae15fe21a6feb5fe03ae607bd98e6"
    assert hashlib.sha256(policy_bytes).hexdigest() == digest(POLICY_REL)
    assert validate_candidate_seal_payload(seal, repo=REPO) == []
    assert seal["candidate_sha"] == "0b3680a03f325e3f1fa1699528a5a59303ddb8b4"
    assert seal["base_sha"] == "b6b6952d52f59bbe05477ef3b02292a98fe92baa"
    assert seal["integration_policy"]["sha256"] == digest(POLICY_REL)

    expected_limits = {
        "max_open_prs": 2,
        "max_direct_to_target_prs": 1,
        "max_prs_per_change_set": 1,
        "max_stack_depth": 2,
        "max_file_overlap_prs": 1,
    }
    assert {key: policy[key] for key in expected_limits} == expected_limits
    assert policy["ordinary_agent_push_forbidden"] is True
    assert policy["ordinary_agent_pr_mutation_forbidden"] is True
    attended = policy["attended_publication"]
    assert attended["direct_mutation_commands_forbidden"] is True
    assert set(attended["forbidden_actions"]) == {
        "force_push", "approve", "merge", "ruleset_mutation"
    }

    rows = inventory["open_prs"]
    assert len(rows) == 1
    predecessor = rows[0]
    assert predecessor["number"] == 380
    assert predecessor["head_branch"] == seal["target_branch"]
    assert predecessor["head_sha"] == seal["base_sha"]
    candidate_paths = {row["path"] for row in seal["changed_files"]}
    overlap_paths = sorted(candidate_paths & set(predecessor["changed_files"]))
    assert overlap_paths
    assert validate_pr_inventory_payload(inventory, seal=seal, policy=policy) == []

    probes: dict[str, str] = {}
    second = copy.deepcopy(predecessor)
    second.update({
        "number": 381,
        "head_branch": "changeset/unrelated-second",
        "head_sha": "2" * 40,
        "change_set_id": "CS-UNRELATED-SECOND",
        "publication_group_id": "PG-UNRELATED-SECOND",
        "changed_files": ["unrelated.txt"],
    })
    two_open = copy.deepcopy(inventory)
    two_open["open_prs"].append(second)
    from publication_integrity import canonical_sha256
    two_open["inventory_sha256"] = canonical_sha256(two_open, omit={"inventory_sha256"})
    probes["second_open_slot"] = probe_error(two_open, seal, policy, "open-PR budget")

    depth_three = copy.deepcopy(inventory)
    depth_three["open_prs"][0]["stack_depth"] = 2
    depth_three["inventory_sha256"] = canonical_sha256(depth_three, omit={"inventory_sha256"})
    probes["candidate_depth_three"] = probe_error(depth_three, seal, policy, "stack-depth budget")

    overlap_policy = copy.deepcopy(policy)
    overlap_policy["max_open_prs"] = 3
    overlap_policy["max_stack_depth"] = 3
    second_overlap = copy.deepcopy(two_open)
    second_overlap["open_prs"][1]["changed_files"] = [overlap_paths[0]]
    second_overlap["inventory_sha256"] = canonical_sha256(second_overlap, omit={"inventory_sha256"})
    probes["second_overlap"] = probe_error(second_overlap, seal, overlap_policy, "overlaps open PR")

    direct = copy.deepcopy(inventory)
    direct["open_prs"][0]["base_branch"] = seal["target_branch"]
    direct["inventory_sha256"] = canonical_sha256(direct, omit={"inventory_sha256"})
    probes["second_direct_to_target"] = probe_error(direct, seal, policy, "direct-to-target PR budget")

    duplicate = copy.deepcopy(inventory)
    duplicate["open_prs"][0]["change_set_id"] = seal["change_set_id"]
    duplicate["inventory_sha256"] = canonical_sha256(duplicate, omit={"inventory_sha256"})
    probes["duplicate_change_set"] = probe_error(duplicate, seal, policy, "change-set already")

    denied_commands = {
        "ordinary_push": "git push origin HEAD",
        "ordinary_pr_mutation": "gh pr create --title x --body y",
        "merge": "gh pr merge 380",
        "force_push": "git push --force origin HEAD",
        "approval": "gh pr review 380 --approve",
        "ruleset_mutation": "gh api -X PUT repos/o/r/rulesets/1 -f enforcement=active",
    }
    command_denials = {}
    for name, command in denied_commands.items():
        denied, reason = classify_publication_command(command)
        assert denied and reason
        command_denials[name] = reason

    exception = validate_review_rereview_budget_exception(plan, run_id=RUN_ID)
    assert exception is not None
    assert exception["kind"] == "single_run_reviewer_rereview"
    assert exception["baseline_limit"] == 16
    assert exception["additional_assignments"] == 2
    assert exception["allowed_workflow_role"] == "reviewer"
    assert exception["allowed_assignment_ids"] == [
        "A-PR284-STACK-POLICY", "A-PR284-STACK-CLOSEOUT"
    ]
    assert exception["single_use"] is True
    assert plan["budget"]["max_total_per_work_unit"] == 16
    enforce_work_unit_assignment_budget(
        plan,
        run_id=RUN_ID,
        assignment_id=ASSIGNMENT_ID,
        workflow_role="reviewer",
        cumulative_count=16,
        current_run_assignment_ids=set(),
    )
    rejected_roles = {}
    for role in ("implementer", "adjudicator"):
        try:
            enforce_work_unit_assignment_budget(
                plan,
                run_id=RUN_ID,
                assignment_id=ASSIGNMENT_ID,
                workflow_role=role,
                cumulative_count=16,
                current_run_assignment_ids=set(),
            )
        except PublicationIntegrityError as exc:
            rejected_roles[role] = str(exc)
        else:
            raise AssertionError(f"budget exception unexpectedly admitted {role}")

    assert integration["candidate_seal_sha256"] == seal["seal_sha256"]
    assert integration["integration_policy_sha256"] == digest(POLICY_REL)
    assert integration["candidate_sha"] == seal["candidate_sha"]
    command_results = integration["commands"]
    assert len(command_results) == 7
    assert all(row["returncode"] == 0 and row["timed_out"] is False for row in command_results)
    integration_errors = validate_integration_receipt_payload(
        integration,
        seal=seal,
        policy=policy,
        repo=REPO,
    )
    assert integration_errors == [], integration_errors

    print(json.dumps({
        "status": "PASS",
        "candidate_sha": seal["candidate_sha"],
        "policy_sha256": digest(POLICY_REL),
        "live_inventory": {
            "observed_at": inventory["observed_at"],
            "inventory_sha256": inventory["inventory_sha256"],
            "open_pr_numbers": [row["number"] for row in rows],
            "predecessor_head_sha": predecessor["head_sha"],
            "overlap_paths": overlap_paths,
        },
        "synthetic_rejections": probes,
        "command_denials": command_denials,
        "assurance_exception": {
            "run_id": exception["run_id"],
            "baseline_limit": exception["baseline_limit"],
            "additional_assignments": exception["additional_assignments"],
            "allowed_workflow_role": exception["allowed_workflow_role"],
            "allowed_assignment_ids": exception["allowed_assignment_ids"],
            "single_use": exception["single_use"],
            "ordinary_global_max": plan["budget"]["max_total_per_work_unit"],
            "rejected_roles": rejected_roles,
        },
        "integration_rehearsal": {
            "receipt_sha256": integration["receipt_sha256"],
            "command_ids": [row["id"] for row in command_results],
            "passed": len(command_results),
        },
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
