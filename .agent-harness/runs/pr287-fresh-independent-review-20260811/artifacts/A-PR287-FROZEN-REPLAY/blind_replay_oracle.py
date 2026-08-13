#!/usr/bin/env python3
"""Independent PR-287 replay, lineage, and portability oracle."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


RUN_ID = "pr287-fresh-independent-review-20260811"
ASSIGNMENT_ID = "A-PR287-FROZEN-REPLAY"
CONTEXT_VERSION = "e9b385d7fbc4f8e47c97c3b0c7edae4e522d9be4e025d9342e26ab24829e3019"
BASE_SHA = "b955a050f19db853a93779506e8acb4e4a5352a9"
CANDIDATE_SHA = "06ee728054fd62423fa90bc6a5d714b9be8631e3"
SEAL_PATH = ".prguard/runtime/PR287_VALIDATED_CANDIDATE_SEAL.json"
SPEC_PATH = "docs/research_program/post_pr275/pr287_spec.yaml"
POLICY_PATH = "docs/research_program/post_pr275/pr287_publication_policy.json"
DELTA_PATH = "docs/PR_DELTAS/pr-287.md"
STATUS_PATH = "docs/codex_handoff/pr_status.yaml"
STATUS_MIRROR_PATH = "machine_readable/pr_status.yaml"
RUNNER_PATH = "scripts/codex_harness/run_pr287_post275_blind_replay.py"
DAG_VALIDATOR_PATH = "scripts/codex_harness/validate_pr_dag.py"
TEST_PATH = "tests/integration/test_post275_blind_replay.py"
COMMON_PATH = "htt/src/common/post275_blind_replay.py"
PLAN_PATH = f".agent-harness/runs/{RUN_ID}/RUN_PLAN.json"
ASSIGNMENT_PATH = f".agent-harness/runs/{RUN_ID}/assignments/{ASSIGNMENT_ID}.json"
AUDIT_PATH = Path(
    "/home/cosmosapjw/Dropbox/bianchi/htt_base/"
    "HTT_PROCESS_INFLATION_SALVAGE_AUDIT_20260810.md"
)
AUDIT_SHA256 = "c42b44641a7655edc36c11e23a747433275285a4f342a824fa69dda88bd6f436"
EXECUTION_BLOCKER = "BLOCKED_CAPABILITY_ISOLATED_EXECUTOR_NOT_INSTALLED"

REQUIRED_HASHES = {
    SEAL_PATH: "fbe4787a82f650ec050fab020ae2c9545e9f7fe778ec2d6f5d4550470537712b",
    SPEC_PATH: "dbd0d6fe29a45e51a6850102ed4587ac38f8da7cfb52453552aa0a4ba704ac09",
    POLICY_PATH: "30e24d1f9e77c5c206a64e7d8b639cfccd4c6bd9455a6893cbc69ae55ea1d155",
    DELTA_PATH: "2071fb8c93006c1f7c79fa36a99bf2611db30dcc8ff2db7b632eec9feda33737",
    STATUS_PATH: "1c6785cd22cf284ed6aebcb74e0acd9c0313f2072acac0c76677d2ee7679bf57",
    STATUS_MIRROR_PATH: "1c6785cd22cf284ed6aebcb74e0acd9c0313f2072acac0c76677d2ee7679bf57",
    RUNNER_PATH: "23c46e3f55cf384ecee6f8409919e233df8c4ed8edcf695257f3573a4fa01a7c",
    DAG_VALIDATOR_PATH: "126ccf63e3a6d835584426e4c3d157be5482b1f7df39d0985638370366b40afc",
    TEST_PATH: "9a659feb3f5f00eabe42a9da4ee5fc7c8345b46e3c8e30cbe548baf17ba7e02b",
    COMMON_PATH: "95d458f939b7ff377e0810a288aaff1da7c254c69f0b836da0dcc61d95e30652",
}

EXPECTED_COMMITS = [
    "858091c113ea3ae4516cdfa6a6f8b8b167e14dc8",
    "eecf46cd7f911365ec278fadaaf1dabebe749265",
    "785895e939f472d625c327ab719fe2eae75c0fa1",
    "2ef6330da4a9a5564c8aa321e97a6ee4460e600c",
    "06ee728054fd62423fa90bc6a5d714b9be8631e3",
]
EXPECTED_MESSAGES = [
    "PR-287: activate exact predecessor stack",
    "PR-287: rebase blind replay contract",
    "PR-287: recover typed blind replay contracts",
    "PR-287: accept legal active lifecycle progression",
    "PR-287: record frozen validation",
]
SOURCE_GROUPS = {
    "G28": "e64f7ac5",
    "G29": "2d8bcfe3568eebecae1eb7c52cfc4dc22ea951ad",
    "G30": "5f2c89e0",
    "G31": "cad9afc8",
    "G32": "d4c878e0",
    "G33": "23790d1a",
    "G34": "68454021",
    "G35": "e1b7119a",
    "G36": "e0c0f90a",
    "G37": "aedd2164",
    "G38": "0f29d9e9",
}
SELECTED_GROUPS = ["G28", "G29", "G31", "G32", "G33", "G34", "G35", "G36", "G37"]
EXCLUDED_GROUPS = ["G30", "G38"]
STALE_G29_PATHS = {
    "docs/generated/claim_ledger.json",
    "docs/generated/status_matrix.md",
    "docs/generated/status_snapshot.json",
    "docs/research_program/post_pr275/pillar_s_adjudication/PILLAR_S_COMPLETE_ADJUDICATION_V1.json",
}
OWNER_PATHS = {
    "PACK_A": "htt/src/common/post275_blind_replay.py",
    "PACK_B": "htt/htt/htt/infer/post275_blind_replay.py",
    "PACK_C": "htt/mio/reports/post275_blind_replay.py",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_sha256(value: dict[str, Any], *, omit: set[str] | None = None) -> str:
    payload = dict(value)
    for key in omit or set():
        payload.pop(key, None)
    return sha256_bytes(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    )


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(repo: Path, relative: str) -> dict[str, Any]:
    value = json.loads((repo / relative).read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"{relative} is not a JSON object")
    return value


def git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )
    require(
        completed.returncode == 0,
        f"git {' '.join(args)} failed: {completed.stderr.strip()}",
    )
    return completed.stdout.strip()


def stable_patch_id(repo: Path, commit: str) -> str:
    shown = subprocess.run(
        ["git", "show", "--pretty=format:", "--binary", commit],
        cwd=repo,
        check=False,
        capture_output=True,
    )
    require(shown.returncode == 0, f"cannot render patch {commit}")
    computed = subprocess.run(
        ["git", "patch-id", "--stable"],
        cwd=repo,
        input=shown.stdout,
        check=False,
        capture_output=True,
        text=False,
    )
    require(computed.returncode == 0, f"cannot patch-id {commit}")
    fields = computed.stdout.decode("ascii").split()
    require(fields, f"empty patch-id for {commit}")
    return fields[0]


def run_command(repo: Path, argv: list[str], timeout: int) -> dict[str, Any]:
    started_at = iso_now()
    started = time.perf_counter()
    timed_out = False
    try:
        completed = subprocess.run(
            argv,
            cwd=repo,
            check=False,
            capture_output=True,
            timeout=timeout,
        )
        returncode = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        returncode = 124
        stdout = exc.stdout or b""
        stderr = exc.stderr or b""
    completed_at = iso_now()
    runtime = time.perf_counter() - started
    return {
        "argv": argv,
        "timeout_seconds": timeout,
        "started_at": started_at,
        "completed_at": completed_at,
        "runtime_seconds": runtime,
        "returncode": returncode,
        "timed_out": timed_out,
        "stdout_sha256": sha256_bytes(stdout),
        "stdout_bytes": len(stdout),
        "stdout_tail": stdout.decode("utf-8", errors="replace")[-2000:],
        "stderr_sha256": sha256_bytes(stderr),
        "stderr_bytes": len(stderr),
        "stderr_tail": stderr.decode("utf-8", errors="replace")[-2000:],
    }


def parse_single_json_output(row: dict[str, Any], label: str) -> dict[str, Any]:
    lines = [line for line in row["stdout_tail"].splitlines() if line.strip()]
    require(lines, f"{label} emitted no JSON")
    value = json.loads(lines[-1])
    require(isinstance(value, dict), f"{label} output is not an object")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--coverage-output", required=True)
    args = parser.parse_args()
    started_at = iso_now()

    repo = Path(git(Path.cwd(), "rev-parse", "--show-toplevel")).resolve()
    output_rel = Path(args.output).as_posix()
    coverage_rel = Path(args.coverage_output).as_posix()
    require(not Path(output_rel).is_absolute(), "output must be repository-relative")
    require(not Path(coverage_rel).is_absolute(), "coverage must be repository-relative")

    checks: dict[str, bool] = {}
    details: dict[str, Any] = {}
    observed_hashes = {
        relative: sha256_bytes((repo / relative).read_bytes())
        for relative in REQUIRED_HASHES
    }
    require(observed_hashes == REQUIRED_HASHES, "required input hash drift")
    require(sha256_bytes(AUDIT_PATH.read_bytes()) == AUDIT_SHA256, "audit hash drift")
    checks["required_inputs_and_authoritative_audit_exact"] = True

    plan = read_json(repo, PLAN_PATH)
    assignment = read_json(repo, ASSIGNMENT_PATH)
    seal = read_json(repo, SEAL_PATH)
    policy = read_json(repo, POLICY_PATH)
    spec = yaml.safe_load((repo / SPEC_PATH).read_text(encoding="utf-8"))
    status_bytes = (repo / STATUS_PATH).read_bytes()
    status = yaml.safe_load(status_bytes)
    require((repo / STATUS_MIRROR_PATH).read_bytes() == status_bytes, "status mirror drift")
    require(plan["context_version"] == assignment["context_version"] == CONTEXT_VERSION, "context drift")
    require(plan["candidate_binding"] == assignment["candidate_binding"], "candidate binding drift")
    checks["context_plan_assignment_and_status_mirror_exact"] = True

    scripts_dir = repo / ".agent-harness/scripts"
    sys.path.insert(0, str(scripts_dir))
    from publication_integrity import validate_candidate_seal_payload

    require(not validate_candidate_seal_payload(seal, repo=repo), "candidate seal invalid")
    require(git(repo, "rev-parse", "HEAD") == CANDIDATE_SHA, "HEAD drift")
    require(git(repo, "status", "--porcelain=v1", "--untracked-files=all") == "", "dirty worktree")
    require(seal["candidate_sha"] == CANDIDATE_SHA, "sealed candidate drift")
    require(seal["base_sha"] == seal["merge_base_sha"] == BASE_SHA, "sealed base drift")
    require(git(repo, "merge-base", BASE_SHA, CANDIDATE_SHA) == BASE_SHA, "merge base drift")
    require(
        git(repo, "rev-parse", "refs/remotes/origin/changeset/pr286-pillar-s-adjudication-recovery-20260810") == BASE_SHA,
        "PR-286 target ref drift",
    )
    checks["candidate_seal_head_base_and_clean_state_exact"] = True

    commits = git(repo, "rev-list", "--reverse", f"{BASE_SHA}..{CANDIDATE_SHA}").splitlines()
    require(commits == EXPECTED_COMMITS == seal["candidate_commits"], "candidate commit sequence drift")
    messages = [git(repo, "show", "-s", "--format=%s", commit) for commit in commits]
    require(messages == EXPECTED_MESSAGES, "candidate commit message sequence drift")
    patch_ids = [stable_patch_id(repo, commit) for commit in commits]
    require(
        patch_ids == [row["stable_patch_id"] for row in seal["stable_patch_ids"]],
        "candidate stable patch-id replay drift",
    )
    require(len(patch_ids) == len(set(patch_ids)) == 5, "candidate patch IDs are not unique")
    require(git(repo, "rev-list", "--merges", f"{BASE_SHA}..{CANDIDATE_SHA}") == "", "candidate contains merge commit")
    checks["five_unique_stable_patch_ids_and_linear_lineage"] = True

    audit_text = AUDIT_PATH.read_text(encoding="utf-8")
    require("include G28, G29/2d8 reviewed lineage, G31~G37; drop G30,G38 and the entire old" in audit_text, "audit selected-lineage clause missing")
    require("PR-287 dirty overlay" in audit_text, "audit dirty-overlay exclusion missing")
    require("transitive publication_integrity/profile_registry origin binding" in audit_text, "audit transitive repair clause missing")
    require("owner factory path/bytes provenance" in audit_text, "audit owner repair clause missing")
    resolved_groups = {
        group: git(repo, "rev-parse", f"{revision}^{{commit}}")
        for group, revision in SOURCE_GROUPS.items()
    }
    require(resolved_groups["G29"] == SOURCE_GROUPS["G29"], "G29 reviewed 2d8 identity drift")
    source_patch_ids = {
        group: stable_patch_id(repo, commit)
        for group, commit in resolved_groups.items()
    }
    require(
        not ({source_patch_ids[group] for group in EXCLUDED_GROUPS} & set(patch_ids)),
        "excluded G30/G38 patch entered candidate lineage",
    )
    changed_paths = set(git(repo, "diff", "--name-only", f"{BASE_SHA}..{CANDIDATE_SHA}").splitlines())
    require(not (changed_paths & STALE_G29_PATHS), "stale G29 generated/global snapshot entered candidate")
    require(
        git(repo, "rev-parse", f"aedd2164:{OWNER_PATHS['PACK_B']}")
        == git(repo, "rev-parse", f"{CANDIDATE_SHA}:{OWNER_PATHS['PACK_B']}"),
        "selected G37 HTT owner module lineage drift",
    )
    require(
        git(repo, "rev-parse", f"aedd2164:{OWNER_PATHS['PACK_C']}")
        == git(repo, "rev-parse", f"{CANDIDATE_SHA}:{OWNER_PATHS['PACK_C']}"),
        "selected G37 MIO owner module lineage drift",
    )
    delta = (repo / DELTA_PATH).read_text(encoding="utf-8")
    normalized_delta = " ".join(delta.split())
    require(SOURCE_GROUPS["G29"] in delta, "delta lacks selected G29 identity")
    require(
        "G30, G38, duplicate aliases, and the old dirty overlay are also excluded"
        in normalized_delta,
        "delta lacks exclusions",
    )
    checks["selected_G28_G29_G31_G37_and_exclusions_verified"] = True

    rows = status["stacked_pr_execution"]["prs"]
    require(all(pr in status["completed"] for pr in [f"PR-{n}" for n in range(281, 287)]), "predecessor completion set drift")
    require(rows["PR-286"]["lifecycle"] == "PR_OPEN", "PR-286 is not PR_OPEN")
    require(rows["PR-286"]["sealed_head"] == BASE_SHA, "PR-286 sealed head drift")
    require(rows["PR-287"]["base_sha"] == rows["PR-287"]["predecessor_sealed_sha"] == BASE_SHA, "PR-287 base chain drift")
    require(rows["PR-287"]["lifecycle"] == "VALIDATED", "PR-287 lifecycle drift")
    require(rows["PR-287"]["execution_blocker"] == EXECUTION_BLOCKER, "typed blocker drift")
    require(rows["PR-287"]["gate_dispositions"]["fresh_execution"] == "INCONCLUSIVE", "fresh execution disposition drift")
    for previous, current in [("PR-283", "PR-284"), ("PR-284", "PR-285"), ("PR-285", "PR-286")]:
        require(rows[current]["base_sha"] == rows[previous]["sealed_head"], f"{current} base chain drift")
        require(rows[current]["predecessor_sealed_sha"] == rows[previous]["sealed_head"], f"{current} predecessor seal drift")
        require(rows[current]["lifecycle"] == "PR_OPEN", f"{current} is not PR_OPEN")
    checks["exact_PR286_base_and_PR_OPEN_chain"] = True

    require(spec["claim_tier"] == "diagnostic_only", "claim tier drift")
    require(spec["transfer_source"] == "none", "transfer source drift")
    require(spec["observed_data_executed"] is False and spec["public_use"] is False, "observed/public boundary drift")
    require(spec["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS", "family gate drift")
    require(spec["fresh_artifact_contracts"]["analyst_executor_status"] == EXECUTION_BLOCKER, "spec executor blocker drift")
    mutation_ids = [row["mutation_id"] for row in spec["mutation_registry"]]
    require(len(mutation_ids) == len(set(mutation_ids)) == 30, "mutation registry completeness drift")
    require(len(policy["required_review_cells"]) == 30, "review cell count drift")
    checks["claim_ceiling_executor_and_mutation_contract_exact"] = True

    for extra in (repo / "htt/src", repo / "htt"):
        sys.path.insert(0, str(extra))
    from common import post275_blind_replay as contracts

    _, harness_provenance = contracts._canonical_harness_validation_modules()
    provenance_map = {name: {"path": path, "sha256": digest} for name, path, digest in harness_provenance}
    dependency_key = {
        "publication_integrity": "publication_integrity",
        "profile_registry": "profile_registry",
        "_harness": "harness_kernel",
        "strict_result_validation": "strict_result_validation",
    }
    require(set(provenance_map) == set(dependency_key), "transitive harness provenance set drift")
    for module_name, key in dependency_key.items():
        require(provenance_map[module_name]["sha256"] == plan["dependency_hashes"][key], f"{module_name} hash drift")

    owner_provenance: dict[str, dict[str, str]] = {}
    owner_modules = {
        "PACK_A": (contracts.BlindReplayPackKind.PACK_A, "common.post275_blind_replay"),
        "PACK_B": (contracts.BlindReplayPackKind.PACK_B, "htt.infer.post275_blind_replay"),
        "PACK_C": (contracts.BlindReplayPackKind.PACK_C, "mio.reports.post275_blind_replay"),
    }
    for name, (kind, module_name) in owner_modules.items():
        factory, provenance = contracts._owner_factory_provenance(
            kind=kind, factory_module=module_name
        )
        observed = dict(provenance)
        require(factory.__module__ == module_name, f"{name} factory module drift")
        require(observed["module"] == module_name, f"{name} provenance module drift")
        require(observed["source_path"] == OWNER_PATHS[name], f"{name} source path drift")
        require(observed["source_sha256"] == sha256_bytes((repo / OWNER_PATHS[name]).read_bytes()), f"{name} source hash drift")
        owner_provenance[name] = observed
    checks["transitive_harness_and_owner_factory_provenance_exact"] = True

    python = str(Path(os.path.abspath(sys.executable)))
    command_results: list[dict[str, Any]] = []
    for registered in policy["required_commands"]:
        argv = list(registered["argv"])
        if argv[0] == "{python}":
            argv[0] = python
        row = run_command(repo, argv, int(registered["timeout_seconds"]))
        row["id"] = registered["id"]
        require(row["returncode"] == 0 and row["timed_out"] is False, f"policy command failed: {registered['id']}")
        command_results.append(row)
    require(len(command_results) == 8, "policy command count drift")
    by_id = {row["id"]: row for row in command_results}
    check_payload = parse_single_json_output(by_id["pr287-fresh-receipt-replay"], "check")
    historical_payload = parse_single_json_output(by_id["pr287-historical-pr273-replay"], "historical")
    for lane, payload in (("check", check_payload), ("historical", historical_payload)):
        require(payload["requested_lane"] == lane, f"{lane} lane identity drift")
        require(payload["status"] == "ACTIVATED", f"{lane} activation drift")
        require(payload["execution_blocker"] == EXECUTION_BLOCKER, f"{lane} blocker drift")
        require(payload["execution_disposition"] == "INCONCLUSIVE", f"{lane} disposition drift")
        require(payload["fresh_artifacts_present"] is False, f"{lane} created fresh artifacts")
    require(check_payload["receipt_content_id"] == historical_payload["receipt_content_id"], "lane activation identity drift")

    portable = parse_single_json_output(by_id["pr287-portable-clean-replay"], "portable")
    manifest = portable["tracked_source_manifest_and_content_ids"]
    require(manifest["file_count"] == 5896, "portable tracked file count drift")
    hashes = {
        portable["source_root_pre_hash"],
        portable["source_root_post_hash"],
        portable["clean_root_pre_hash"],
        portable["clean_root_post_hash"],
        manifest["manifest_sha256"],
    }
    require(len(hashes) == 1, "portable pre/post/root manifest drift")
    require(portable["source_root_differs_from_execution_root"] is True, "portable root was not isolated")
    require(portable["zero_untracked_truth_submission_adjudication_or_pack_inputs"] is True, "portable lane admitted fresh inputs")
    require(portable["exact_command_exit_code"] == 0, "portable nested command failed")
    require(portable["execution_blocker"] == EXECUTION_BLOCKER, "portable blocker drift")
    require(portable["execution_disposition"] == "INCONCLUSIVE", "portable disposition drift")
    require("9 passed" in by_id["pr287-publication-policy-cross-binding"]["stdout_tail"], "publication policy count drift")
    require("OK: 244 PRs, DAG valid" in by_id["pr287-dag-strict"]["stdout_tail"], "DAG verdict drift")
    require("No forbidden claim language detected." in by_id["pr287-claim-language"]["stdout_tail"], "claim scan drift")
    checks["all_policy_commands_and_5896_file_portability_pass"] = True

    fresh_paths = [repo / path for path in spec["fresh_artifact_contracts"]["artifact_paths"].values()]
    require(not any(path.exists() for path in fresh_paths), "fresh truth/submission/adjudication/pack artifact exists")
    checks["fresh_lane_remains_unexecuted_and_typed_blocked"] = True

    require(all(checks.values()), "one or more oracle checks failed")
    completed_at = iso_now()
    details.update(
        {
            "base_sha": BASE_SHA,
            "candidate_sha": CANDIDATE_SHA,
            "candidate_tree_sha": seal["candidate_tree_sha"],
            "candidate_seal_sha256": seal["seal_sha256"],
            "candidate_patch_ids": patch_ids,
            "source_group_commits": resolved_groups,
            "source_group_patch_ids": source_patch_ids,
            "selected_groups": SELECTED_GROUPS,
            "excluded_groups": EXCLUDED_GROUPS,
            "owner_factory_provenance": owner_provenance,
            "harness_module_provenance": provenance_map,
            "activation_receipt_content_id": check_payload["receipt_content_id"],
            "portable_manifest": manifest,
            "portable_root_hash": next(iter(hashes)),
            "execution_blocker": EXECUTION_BLOCKER,
            "execution_disposition": "INCONCLUSIVE",
            "fresh_artifacts_present": False,
            "mutation_count": len(mutation_ids),
            "policy_command_count": len(command_results),
        }
    )
    report = {
        "schema_version": 1,
        "oracle_id": "PR287-FROZEN-BLIND-REPLAY-ORACLE",
        "run_id": RUN_ID,
        "assignment_id": ASSIGNMENT_ID,
        "context_version": CONTEXT_VERSION,
        "started_at": started_at,
        "completed_at": completed_at,
        "status": "PASS",
        "checks": checks,
        "details": details,
        "required_input_hashes": observed_hashes,
        "authoritative_audit": {
            "path": str(AUDIT_PATH),
            "sha256": AUDIT_SHA256,
        },
        "policy_command_results": command_results,
    }
    output_path = repo / output_rel
    write_json(output_path, report)
    report_bytes = output_path.read_bytes()

    script_rel = Path(__file__).resolve().relative_to(repo).as_posix()
    argv = [
        python,
        "-B",
        script_rel,
        "--output",
        output_rel,
        "--coverage-output",
        coverage_rel,
    ]
    common_evidence = [output_rel, SEAL_PATH, SPEC_PATH, POLICY_PATH, DELTA_PATH]
    coverage_cells = [
        {
            "cell": cell,
            "status": "PASS",
            "evidence_refs": common_evidence,
            "rationale": (
                "Fresh blind replay oracle independently checked the exact frozen "
                "candidate, selective lineage, policy command, portable clean-root, "
                "typed-blocker, provenance, mutation, ownership, and claim-boundary "
                "contracts without reading any sibling or historical result envelope."
            ),
        }
        for cell in policy["required_review_cells"]
    ]
    coverage = {
        "schema_version": 1,
        "run_id": RUN_ID,
        "assignment_id": ASSIGNMENT_ID,
        "change_set_id": seal["change_set_id"],
        "publication_group_id": seal["publication_group_id"],
        "candidate_seal_sha256": seal["seal_sha256"],
        "candidate_sha": seal["candidate_sha"],
        "candidate_tree_sha": seal["candidate_tree_sha"],
        "diff_sha256": seal["diff_sha256"],
        "changed_files_sha256": seal["changed_files_sha256"],
        "completed_at": completed_at,
        "first_verdict_read_only": True,
        "correlated_review": False,
        "coverage_cells": coverage_cells,
        "independent_oracles": [
            {
                "oracle_id": "PR287-FROZEN-BLIND-REPLAY-ORACLE",
                "kind": "invariant_checker",
                "status": "PASS",
                "argv": argv,
                "command_fingerprint": canonical_sha256({"argv": argv}),
                "returncode": 0,
                "timed_out": False,
                "started_at": started_at,
                "completed_at": completed_at,
                "artifact_path": output_rel,
                "artifact_sha256": sha256_bytes(report_bytes),
                "artifact_bytes": len(report_bytes),
                "evidence_refs": common_evidence,
            }
        ],
    }
    coverage["coverage_sha256"] = canonical_sha256(coverage, omit={"coverage_sha256"})
    write_json(repo / coverage_rel, coverage)
    print(json.dumps({"status": "PASS", "checks": checks, "details": details}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
