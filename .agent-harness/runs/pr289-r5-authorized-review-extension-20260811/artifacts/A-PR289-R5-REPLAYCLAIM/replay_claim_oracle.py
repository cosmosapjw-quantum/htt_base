#!/usr/bin/env python3
"""Independent PR-289 R5 replay/claim oracle for A-PR289-R5-REPLAYCLAIM."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import yaml


ROOT = Path(__file__).resolve().parents[5]
RUN_ID = "pr289-r5-authorized-review-extension-20260811"
ASSIGNMENT_ID = "A-PR289-R5-REPLAYCLAIM"
BASE = "27df5da040e27eeaad44873ba3424ff73fb4bb09"
CANDIDATE = "eec048d4cf19989983986d139c7d0a797b1363e0"
PR274 = "ff9ef9f45747e559c5343b463cf010dfc3a7432a"
RECEIPT_SHA = "92ca6a84f6c42f42de3dd33c7150fce7d1ef1672e4c6eaa407e8c36750928c34"
G45 = "7f9ac031f7c585076bb955cac6326d1b600992d8"
G46 = "834e15d76bd4517a26c2344536d201e1de9deb8f"
G47 = "91d8b8adb72ec8c1e07cfa46fe028fa56867290b"
G48 = "dde54a713ebb0408c3690f5b7d3fdded17e19ff3"
OBSOLETE = (
    "44091dea7341e96cbf152b1e42d072de977f8522",
    "a757eeee6c97e532a740a67909703d5ad394ab4a",
    "c2037e8ae1163db0f57b36355da24cf20ceea320",
)


def run(*argv: str, binary: bool = False) -> str | bytes:
    completed = subprocess.run(
        argv,
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=not binary,
    )
    return completed.stdout


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def patch_id(commit: str) -> str:
    shown = run(
        "git", "show", "--pretty=format:", "--binary", "--full-index", commit,
        binary=True,
    )
    computed = subprocess.run(
        ["git", "patch-id", "--stable"],
        cwd=ROOT,
        input=shown,
        check=True,
        capture_output=True,
    ).stdout.decode("ascii").strip()
    return computed.split()[0]


def commit_paths(commit: str) -> set[str]:
    output = run(
        "git", "diff-tree", "--no-commit-id", "--name-only", "-r",
        "--no-renames", commit,
    )
    assert isinstance(output, str)
    return set(output.splitlines())


def load_json(relative: str) -> dict[str, object]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def main() -> None:
    seal = load_json(".prguard/runtime/PR289_R5_CANDIDATE_SEAL.json")
    spec = yaml.safe_load(
        (ROOT / "docs/research_program/post_pr275/pr289_spec.yaml").read_text(
            encoding="utf-8"
        )
    )
    policy = load_json(
        "docs/research_program/post_pr275/pr289_publication_policy.json"
    )
    receipt = load_json("docs/generated/pr289_data_identity_v2_receipt.json")
    status = yaml.safe_load(
        (ROOT / "docs/codex_handoff/pr_status.yaml").read_text(encoding="utf-8")
    )
    mirror = yaml.safe_load(
        (ROOT / "machine_readable/pr_status.yaml").read_text(encoding="utf-8")
    )
    plan = load_json(f".agent-harness/runs/{RUN_ID}/RUN_PLAN.json")
    delta = (ROOT / "docs/PR_DELTAS/pr-289.md").read_text(encoding="utf-8")

    assert run("git", "rev-parse", "HEAD").strip() == CANDIDATE
    assert run("git", "rev-parse", "HEAD^{tree}").strip() == seal["candidate_tree_sha"]
    assert run("git", "merge-base", BASE, CANDIDATE).strip() == BASE
    assert run(
        "git", "rev-parse",
        "refs/remotes/origin/changeset/pr288-bayesian-evidence-recovery-20260811^{commit}",
    ).strip() == BASE
    assert seal["base_sha"] == seal["merge_base_sha"] == BASE
    assert seal["candidate_sha"] == CANDIDATE

    stack = status["stacked_pr_execution"]
    assert status == mirror
    assert stack["merge_policy"] == "HUMAN_ONLY"
    pr288 = stack["prs"]["PR-288"]
    pr289 = stack["prs"]["PR-289"]
    pr290 = stack["prs"]["PR-290"]
    assert pr288["lifecycle"] == "PR_OPEN"
    assert pr288["sealed_head"] == BASE
    assert pr289["predecessor_pr"] == "PR-288"
    assert pr289["base_sha"] == pr289["predecessor_sealed_sha"] == BASE
    assert pr289["lifecycle"] == "VALIDATED"
    assert pr289["lifecycle_history"] == ["PLANNED", "ACTIVE", "IMPLEMENTED", "VALIDATED"]
    assert pr289["gate_dispositions"] == {
        "eligibility": "PASS",
        "implementation": "PASS",
        "validation": "PASS",
        "code": "FAIL",
        "physics": "FAIL",
        "statistics": "FAIL",
        "claim": "PASS",
        "harness": "FAIL",
        "portability_replay": "PASS",
        "review": "FAIL",
    }
    assert pr290["lifecycle"] == "PLANNED"
    assert pr290["gate_dispositions"] == {"eligibility": "INELIGIBLE"}
    assert pr290["assurance_budget"] == {"maximum": 16, "consumed": 0}
    pr280_resolution = status["execution_resolutions"]["PR-280"]
    assert spec["dependency_contract"]["upstream_id"] == "PR-280"
    assert spec["dependency_contract"]["accepted_terminal"] == "COMPLETED_FAILED_WITH_RECEIPT"
    assert spec["dependency_contract"]["success_dependency_required"] is False
    assert pr280_resolution["resolution"] == "COMPLETED_FAILED_WITH_RECEIPT"
    assert pr280_resolution["success_dependency_satisfied"] is False

    exception = plan["budget_exception"]
    assert exception["kind"] == "single_run_reviewer_rereview"
    assert exception["run_id"] == RUN_ID
    assert exception["additional_assignments"] == 2
    assert exception["allowed_workflow_role"] == "reviewer"
    assert set(exception["allowed_assignment_ids"]) == {
        "A-PR289-R5-PHYSCODE", ASSIGNMENT_ID
    }
    assert exception["single_use"] is True

    candidate_commits = seal["candidate_commits"]
    candidate_patch_ids = [row["stable_patch_id"] for row in seal["stable_patch_ids"]]
    assert len(candidate_commits) == len(set(candidate_commits)) == 16
    assert patch_id(G45) == "122120d7f0b90b9dbe24be63fd0fdf0b56655484"
    assert candidate_patch_ids.count(patch_id(G45)) == 1
    assert patch_id(G46) == "8c57aa2af00713bc3be8c49001e9275e769fecda"
    assert candidate_patch_ids.count(patch_id(G46)) == 1
    assert all(patch_id(commit) not in candidate_patch_ids for commit in OBSOLETE)
    assert commit_paths("8cbbdb4dc32c75d276d13713e61a3fd8724f966c") < commit_paths(G47)
    assert commit_paths("fd36d51dc6b62b22373578cdee5f5e9c65bd88cc") < commit_paths(G48)
    for relative in (
        "docs/research_program/post_pr275/pr289_spec.yaml",
        "htt/src/common/data_identity.py",
        "scripts/codex_harness/run_pr289_data_identity_v2.py",
        "tests/contracts/test_data_identity_registry_v2.py",
    ):
        assert run("git", "show", f"{G47}:{relative}", binary=True) == run(
            "git", "show", f"8cbbdb4dc32c75d276d13713e61a3fd8724f966c:{relative}", binary=True
        )
    assert run(
        "git", "show", f"{G48}:tests/contracts/test_data_identity_registry_v2.py", binary=True
    ) == run(
        "git", "show",
        "fd36d51dc6b62b22373578cdee5f5e9c65bd88cc:tests/contracts/test_data_identity_registry_v2.py",
        binary=True,
    )

    historical = spec["historical_boundary"]
    for relative, key in (
        (historical["v1_registry"], "v1_registry_sha256"),
        (historical["v1_result"], "v1_result_sha256"),
    ):
        assert sha(ROOT / relative) == historical[key]
        archived = run("git", "show", f"{PR274}:{relative}", binary=True)
        assert hashlib.sha256(archived).hexdigest() == historical[key]

    mutation_ids = [row["mutation_id"] for row in spec["mutation_registry"]]
    mutation_rows = receipt["mutation_results"]
    assert len(mutation_ids) == len(set(mutation_ids)) == 33
    assert [row["mutation_id"] for row in mutation_rows] == mutation_ids
    assert all(
        row["executed"] is True
        and row["activated"] is True
        and row["killed"] is True
        and row["observed_marker"]
        for row in mutation_rows
    )
    for relative, identity in receipt["source_bindings"].items():
        assert sha(ROOT / relative) == identity.removeprefix("sha256:")

    sys.path.insert(0, str(ROOT / "htt/src"))
    from common.data_identity import (  # noqa: PLC0415
        AdmissionStatus,
        DataIdentityError,
        _mutation_descriptor,
        build_not_authorized_receipt,
        canonical_sha256,
        evaluate_lane_identity,
        load_lane_registry,
    )

    unsigned = dict(receipt)
    receipt_content_id = unsigned.pop("receipt_content_id")
    assert canonical_sha256(unsigned) == receipt_content_id
    generation = receipt["generation_identity"]
    assert generation["git_commit_or_worktree_state"] == (
        "BOUND_SOURCE_WORKTREE:" + canonical_sha256(receipt["source_bindings"])
    )
    assert generation["generating_procedure"] == [
        "python3", "-B", "scripts/codex_harness/run_pr289_data_identity_v2.py", "build"
    ]

    registry = load_lane_registry(
        ROOT / "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json"
    )
    with tempfile.TemporaryDirectory(prefix="pr289-r5-cross-lane-") as temporary:
        cf4 = registry.lane("CF4")
        descriptor = _mutation_descriptor(Path(temporary) / "cf4", cf4)
        decision = evaluate_lane_identity(
            registry=registry,
            lane_id="CF4",
            descriptor=descriptor,
            inspected_at_utc="2026-08-11T00:00:00+00:00",
        )
        assert decision.status is AdmissionStatus.ADMITTED_IDENTITY_ONLY
        try:
            build_not_authorized_receipt(registry.lane("PLANCK"), decision)
        except DataIdentityError as exc:
            assert "lane decision identity" in str(exc)
        else:
            raise AssertionError("cross-lane authorization mismatch was accepted")

    assert receipt["owner"] == "COMMON"
    assert receipt["scope"] == "external-data identity admission without acquisition or analysis"
    assert receipt["claim_tier"] == spec["claim_tier"] == policy["claim_ceiling"] == "diagnostic_only"
    assert receipt["claim_level"] == {"scheme": "roadmap_rescue_v1", "level": "C2"}
    assert receipt["transfer_source"] == "none"
    assert receipt["observed_data_executed"] is False
    assert receipt["public_use"] is False
    assert receipt["scientific_status_effect"] == "OPEN_UNCHANGED"
    assert receipt["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
    assert receipt["aggregate_status"] == "NO_ADMITTED_IDENTITIES"
    assert all(row["status"] == "REJECTED_NOT_PRESENT" for row in receipt["lane_decisions"])
    assert all(row["status"] == "NOT_AUTHORIZED" for row in receipt["authorization_receipts"])
    assert all(row["authorization_domain"] == "lane_data_execution" for row in receipt["authorization_receipts"])
    assert "The frozen R1 code/harness review is preserved as a substantive FAIL" in delta
    assert "That R2 wave preserved PASS for claim/provenance and replay/lineage" in delta
    assert "but it was\nnot accepted" in delta
    assert "The frozen R3 replay/claim lane" in delta
    assert "fresh combined R4 reviewer" in delta
    assert "packaging incident" in delta

    replay_results = []
    for interpreter in ("/usr/bin/python", "/usr/bin/python3", "/usr/bin/python3.10"):
        payload = json.loads(
            run(
                interpreter, "-B",
                "scripts/codex_harness/run_pr289_data_identity_v2.py", "check"
            )
        )
        assert payload["receipt_sha256"] == RECEIPT_SHA
        assert payload["observed_data_executed"] is False
        assert payload["public_use"] is False
        replay_results.append(payload["receipt_sha256"])
    assert len(set(replay_results)) == 1

    portable = json.loads(
        run(
            "/usr/bin/python3", "-B",
            "scripts/codex_harness/run_pr289_data_identity_v2.py", "portable"
        )
    )
    assert portable["schema"] == "PR289_PORTABLE_CLEAN_EVIDENCE_V2"
    assert portable["nested_exit_code"] == 0
    assert portable["source_root_differs_from_execution_root"] is True
    assert portable["external_roots_supplied"] is False
    assert portable["network_or_download_side_effect"] is False
    assert portable["source_root_pre_hash"] == portable["source_root_post_hash"]
    assert portable["clean_root_pre_hash"] == portable["clean_root_post_hash"]

    print(
        json.dumps(
            {
                "schema": "PR289_R5_REPLAY_CLAIM_ORACLE_V1",
                "assignment_id": ASSIGNMENT_ID,
                "candidate_sha": CANDIDATE,
                "predecessor_sha": BASE,
                "selected_lineage": {
                    "G45_exact_once": True,
                    "G46_exact_once": True,
                    "G47_bounded_subset": True,
                    "G48_bounded_subset": True,
                    "G39_G40_G42_absent": True,
                },
                "source_bound_receipt": True,
                "ordered_mutations": len(mutation_ids),
                "cross_lane_authorization_rejected": True,
                "interpreter_invariant_receipt_sha256": RECEIPT_SHA,
                "portable_clean_replay": True,
                "claim_ceiling": "diagnostic_only",
                "lifecycle": "VALIDATED",
                "historical_failures_preserved": True,
                "assurance_exception_bounded": True,
                "pr290": "INELIGIBLE_ZERO_CONSUMED",
                "merge_policy": "HUMAN_ONLY",
                "status": "PASS",
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
