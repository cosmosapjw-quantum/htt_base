#!/usr/bin/env python3
"""Independent evidence-freshness and publication-closeout oracle for PR-284."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

import yaml


ROOT = Path(__file__).resolve().parents[5]
RUN_ID = "pr284-stacked-publication-policy-review-20260810"
ASSIGNMENT_ID = "A-PR284-STACK-CLOSEOUT"
ASSIGNMENT_PATH = ROOT / f".agent-harness/runs/{RUN_ID}/assignments/{ASSIGNMENT_ID}.json"
SEAL_PATH = ROOT / ".prguard/runtime/PR284_STACK_POLICY_CANDIDATE_SEAL.json"
REHEARSAL_PATH = ROOT / ".prguard/runtime/PR284_STACK_POLICY_INTEGRATION_REHEARSAL.json"
POLICY_PATH = ROOT / "docs/research_program/post_pr275/pr284_publication_policy.json"
SPEC_PATH = ROOT / "docs/research_program/post_pr275/pr284_spec.yaml"
RECEIPT_PATH = ROOT / "docs/generated/pr284_depth_path_doob_receipt.json"
STATUS_PATH = ROOT / "docs/codex_handoff/pr_status.yaml"
STATUS_MIRROR_PATH = ROOT / "machine_readable/pr_status.yaml"
RUN_PLAN_PATH = ROOT / f".agent-harness/runs/{RUN_ID}/RUN_PLAN.json"
BLOCKER_PATH = ROOT / ".prguard/runtime/PR284_PUBLICATION_BLOCKER.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(payload: dict[str, object], omitted: str) -> str:
    value = dict(payload)
    value.pop(omitted, None)
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def _run(*argv: str) -> str:
    completed = subprocess.run(
        argv,
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    )
    return completed.stdout.strip()


def _parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def main() -> None:
    assignment = json.loads(ASSIGNMENT_PATH.read_text(encoding="utf-8"))
    seal = json.loads(SEAL_PATH.read_text(encoding="utf-8"))
    rehearsal = json.loads(REHEARSAL_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    run_plan = json.loads(RUN_PLAN_PATH.read_text(encoding="utf-8"))
    blocker = json.loads(BLOCKER_PATH.read_text(encoding="utf-8"))

    for required in assignment["required_inputs"]:
        assert _sha256(ROOT / required["path"]) == required["sha256"]
    assert _sha256(SEAL_PATH) == assignment["candidate_binding"]["seal_file_sha256"]
    for key, expected in assignment["candidate_binding"].items():
        if key == "state":
            continue
        seal_key = "seal_sha256" if key == "seal_sha256" else key
        if key == "seal_path" or key == "seal_file_sha256":
            continue
        assert seal[seal_key] == expected
    assert _run("git", "rev-parse", "HEAD") == seal["candidate_sha"]
    assert _run("git", "rev-parse", "HEAD^{tree}") == seal["candidate_tree_sha"]
    assert _run("git", "status", "--porcelain") == ""

    assert rehearsal["receipt_sha256"] == _canonical_sha256(rehearsal, "receipt_sha256")
    binding_fields = (
        "candidate_sha",
        "candidate_tree_sha",
        "diff_sha256",
        "changed_files_sha256",
    )
    assert rehearsal["candidate_seal_sha256"] == seal["seal_sha256"]
    for field in binding_fields:
        assert rehearsal[field] == seal[field]
    assert rehearsal["status"] == "PASS"
    assert rehearsal["latest_target_sha"] == seal["base_sha"] == (
        "b6b6952d52f59bbe05477ef3b02292a98fe92baa"
    )
    assert rehearsal["merged_tree_sha"] == seal["candidate_tree_sha"]
    assert rehearsal["integration_policy_sha256"] == _sha256(POLICY_PATH)
    completed = _parse_utc(rehearsal["completed_at"])
    age_seconds = (datetime.now(timezone.utc) - completed).total_seconds()
    assert 0 <= age_seconds <= policy["max_receipt_age_seconds"]

    command_ids = [row["id"] for row in rehearsal["commands"]]
    policy_ids = [row["id"] for row in policy["required_commands"]]
    assert command_ids == policy_ids
    assert len(command_ids) == 7
    for observed, required in zip(rehearsal["commands"], policy["required_commands"], strict=True):
        assert observed["policy_argv"] == required["argv"]
        assert observed["returncode"] == 0
        assert observed["timed_out"] is False
        assert observed["stderr_sha256"] == hashlib.sha256(b"").hexdigest()

    assert policy["max_open_prs"] == 2
    assert policy["max_stack_depth"] == 2
    assert policy["max_file_overlap_prs"] == 1
    assert policy["max_direct_to_target_prs"] == 1
    assert policy["max_prs_per_change_set"] == 1
    assert policy["ordinary_agent_push_forbidden"] is True
    assert policy["ordinary_agent_pr_mutation_forbidden"] is True
    attended = policy["attended_publication"]
    assert attended["requires_current_turn_authorization"] is True
    assert set(attended["forbidden_actions"]) == {"force_push", "approve", "merge", "ruleset_mutation"}

    boundary = {
        "claim_tier": "diagnostic_only",
        "transfer_source": "none",
        "observed_data_executed": False,
        "public_use": False,
        "family_identification_gate": "BLOCKED_PRE_NATIVE_ATLAS",
    }
    for key, expected in boundary.items():
        assert spec[key] == receipt[key] == expected
    assert policy["claim_ceiling"] == "diagnostic_only"
    assert policy["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
    assert spec["owner"] == receipt["owner"] == "HTT"

    assert STATUS_PATH.read_bytes() == STATUS_MIRROR_PATH.read_bytes()
    status = yaml.safe_load(STATUS_PATH.read_text(encoding="utf-8"))
    prs = status["stacked_pr_execution"]["prs"]
    pr284 = prs["PR-284"]
    pr285 = prs["PR-285"]
    assert pr284["lifecycle"] == "REVIEWED"
    assert pr284["sealed_head"] is None
    assert pr284["pushed_ref"] is None
    assert pr284["pr_url"] is None
    assert pr284["gate_dispositions"]["review"] == "DEFERRED"
    assert pr284["gate_dispositions"]["seal"] == "INELIGIBLE"
    assert pr284["gate_dispositions"]["push"] == "INELIGIBLE"
    assert pr284["gate_dispositions"]["publication"] == "INELIGIBLE"
    assert pr284["assurance_budget"] == {"maximum": 16, "consumed": 16}
    assert pr285["lifecycle"] == "PLANNED"
    assert pr285["gate_dispositions"] == {"eligibility": "INELIGIBLE"}
    assert pr285["assurance_budget"] == {"maximum": 16, "consumed": 0}
    assert pr285["sealed_head"] is pr285["pushed_ref"] is pr285["pr_url"] is None

    assert seal["production_hash"] == run_plan["production_hash"] == pr284["production_hash"]
    assert run_plan["dependency_hashes"] == run_plan["evidence_key"]["dependency_hashes"]
    assert run_plan["dependency_hashes"] == pr284["dependency_hashes"]
    assert run_plan["evidence_key"]["production_hash"] == seal["production_hash"]

    exception = run_plan["budget_exception"]
    assert exception == {
        "exception_id": "PR284-STACK-PUBLICATION-20260810",
        "kind": "single_run_reviewer_rereview",
        "run_id": RUN_ID,
        "work_unit_id": "PR-284",
        "authorized_by": "user-PROCESS_INFLATION_RECOVERY_PHASE2-20260810",
        "reason": "stacked-publication-policy-repair-and-bounded-assurance-extension",
        "baseline_limit": 16,
        "additional_assignments": 2,
        "allowed_workflow_role": "reviewer",
        "allowed_assignment_ids": ["A-PR284-STACK-POLICY", "A-PR284-STACK-CLOSEOUT"],
        "single_use": True,
    }
    assert exception["baseline_limit"] + exception["additional_assignments"] == 18
    assert "merge" not in exception and "publication" not in exception and "push" not in exception

    assert _sha256(BLOCKER_PATH) == "86ccc2382d64b8779f0a99d008ed4188f6dbc2c4d07dff9c32160a85db99c6aa"
    assert set(blocker["actions_not_executed"]) == {
        "git_push",
        "pull_request_create",
        "merge",
        "approve",
        "force_push",
        "ruleset_mutation",
    }

    remote_branch = _run(
        "git",
        "ls-remote",
        "--heads",
        "origin",
        "refs/heads/changeset/pr284-finite-depth-law-recovery-20260810",
    )
    assert remote_branch == ""
    pr284_live = json.loads(
        _run(
            "gh",
            "pr",
            "list",
            "--repo",
            "cosmosapjw-quantum/htt_base",
            "--head",
            "changeset/pr284-finite-depth-law-recovery-20260810",
            "--state",
            "all",
            "--json",
            "number,state,headRefName,baseRefName,url",
        )
    )
    assert pr284_live == []
    predecessor = json.loads(
        _run(
            "gh",
            "pr",
            "view",
            "380",
            "--repo",
            "cosmosapjw-quantum/htt_base",
            "--json",
            "number,state,headRefName,headRefOid,baseRefName,mergeStateStatus,url",
        )
    )
    assert predecessor["state"] == "OPEN"
    assert predecessor["mergeStateStatus"] == "BLOCKED"
    assert predecessor["headRefOid"] == seal["base_sha"]

    print(
        json.dumps(
            {
                "oracle": ASSIGNMENT_ID,
                "status": "PASS",
                "rehearsal_age_seconds": round(age_seconds, 3),
                "checks": [
                    "required_inputs_candidate_head_tree_and_clean_state_match",
                    "fresh_rehearsal_content_address_and_seal_binding_match",
                    "seven_policy_commands_zero_and_not_timed_out",
                    "production_and_dependency_evidence_key_unchanged",
                    "claim_owner_transfer_observed_public_family_boundaries_hold",
                    "status_mirrors_synchronized_and_pr285_zero_budget_ineligible",
                    "single_use_two_reviewer_exception_bounds_16_to_18_only",
                    "exception_and_policy_grant_no_merge_or ordinary-agent publication authority",
                    "live_remote_has_no_pr284_branch_or_pull_request",
                    "predecessor_remains_open_blocked_at_exact_target_sha",
                ],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
