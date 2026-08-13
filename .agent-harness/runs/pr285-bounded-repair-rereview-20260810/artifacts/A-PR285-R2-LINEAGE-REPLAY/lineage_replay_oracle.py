#!/usr/bin/env python3
"""Independent, assignment-local PR-285 lineage and receipt replay oracle."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[5]
RUN_ID = "pr285-bounded-repair-rereview-20260810"
ASSIGNMENT_ID = "A-PR285-R2-LINEAGE-REPLAY"
ARTIFACT_DIR = ROOT / ".agent-harness/runs" / RUN_ID / "artifacts" / ASSIGNMENT_ID
BASE = "0b3680a03f325e3f1fa1699528a5a59303ddb8b4"
IMPLEMENTATION = "8640cb23c78a2eea9dddf6fb21a1e3176d449c95"
CANDIDATE = "8682a13e8df75c48f6150af555ee231f62e7d9bc"
AUDIT_NAME = "HTT_PROCESS_INFLATION_SALVAGE_AUDIT_20260810.md"
AUDIT_SHA256 = "c42b44641a7655edc36c11e23a747433275285a4f342a824fa69dda88bd6f436"
FINAL_SEAL = ROOT / ".prguard/runtime/PR285_R2_FINAL_REVIEW_CANDIDATE_SEAL.json"
IMPLEMENTATION_SEAL = ROOT / ".prguard/runtime/PR285_R2_IMPLEMENTATION_CANDIDATE_SEAL.json"
IMPLEMENTATION_RECEIPT = ROOT / ".prguard/runtime/PR285_R2_IMPLEMENTATION_INTEGRATION_REHEARSAL.json"
POLICY = ROOT / "docs/research_program/post_pr275/pr285_publication_policy.json"
RUNNER = ROOT / "scripts/codex_harness/run_pr285_pillar_t_adjudication.py"
TRACKED_RECEIPT = ROOT / "docs/research_program/post_pr275/pillar_t_adjudication/PILLAR_T_COMPLETE_ADJUDICATION_V1.json"
STATUS = ROOT / "docs/codex_handoff/pr_status.yaml"
STATUS_MIRROR = ROOT / "machine_readable/pr_status.yaml"
PUBLICATION_INTEGRITY = ROOT / ".agent-harness/scripts/publication_integrity.py"

EXPECTED_GROUPS = {
    "G20": {
        "disposition": "INCLUDE",
        "representative_commit": "53b924233bc4285a4dbf7d2fda9666ddb16617a4",
        "duplicate_alias_commits": [
            "6a7139e2a53234023da4808884188b489279161e",
            "e972edfcf3fed34070e6e670d648a66e40e73c81",
            "50c3fb52c3f31d173922c41712ba6276fa633e99",
        ],
        "candidate_commit": "e0dc7d73ecbf25930daa0ff22871c86d99b00a40",
    },
    "G21": {
        "disposition": "INCLUDE",
        "representative_commit": "63faaa51a764bb93ac3ddf550c3d437642d9d81e",
        "duplicate_alias_commits": [
            "87356190621427655f66d9466e94ab72ab7147a7",
        ],
        "candidate_commit": "ca5c6117f9d028809616dbdd604ceb8da05e50cb",
    },
    "G22": {
        "disposition": "EXCLUDE_OBSOLETE",
        "representative_commit": "6e289afdba12b8a92f74c2d5de9beb123f7cf1e4",
        "duplicate_alias_commits": [],
        "candidate_commit": None,
    },
}

DEPENDENCY_PATHS = {
    "theorem_signatures": "docs/research_program/vector_tensor/THEOREM_SIGNATURES_V3.yaml",
    "vt_proof_program": "docs/research_program/vector_tensor/VECTOR_TENSOR_PROOF_PROGRAM_V1.yaml",
    "pr269_spec": "docs/research_program/vector_tensor/pr269_spec.yaml",
    "pr270_spec": "docs/research_program/vector_tensor/pr270_spec.yaml",
    "pillar_t_core_proofs": "docs/research_program/vector_tensor/proofs/PILLAR_T_CORE_PROOFS_V1.yaml",
    "pillar_s_core_proofs": "docs/research_program/vector_tensor/proofs/PILLAR_S_CORE_PROOFS_V1.yaml",
    "pillar_t_cas_proofs": "docs/research_program/vector_tensor/proofs/PILLAR_T_CAS_PROOFS_V1.yaml",
    "cas_contract": "docs/research_program/vector_tensor/cas/CAS_CONTRACT.json",
    "cas_run_spec": "docs/research_program/vector_tensor/cas/CAS_RUN_SPEC.json",
    "cas_adjudication": "docs/research_program/vector_tensor/cas/CAS_ADJUDICATION.json",
    "pr190_spec": "docs/research_program/strengthening/pr190_spec.yaml",
    "pr190_receipt": "docs/generated/pr190_attainability/attainability_report.json",
    "pr285_spec": "docs/research_program/post_pr275/pr285_spec.yaml",
    "publication_policy": "docs/research_program/post_pr275/pr285_publication_policy.json",
    "pr285_runner": "scripts/codex_harness/run_pr285_pillar_t_adjudication.py",
    "pr285_contract_test": "tests/contracts/test_pillar_t_complete_adjudication.py",
    "adjudication_receipt": "docs/research_program/post_pr275/pillar_t_adjudication/PILLAR_T_COMPLETE_ADJUDICATION_V1.json",
    "publication_integrity": ".agent-harness/scripts/publication_integrity.py",
    "publication_integrity_test": "scripts/codex_harness/test_publication_integrity.py",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_sha(value: dict[str, Any], *, omit: set[str] = set()) -> str:
    filtered = {key: item for key, item in value.items() if key not in omit}
    return sha(
        json.dumps(
            filtered,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    )


def run(*argv: str, cwd: Path = ROOT, input_bytes: bytes | None = None) -> bytes:
    completed = subprocess.run(
        argv,
        cwd=cwd,
        input=input_bytes,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"command failed ({completed.returncode}): {' '.join(argv)}\n"
            + completed.stderr.decode("utf-8", errors="replace")
        )
    return completed.stdout


def git(*argv: str, cwd: Path = ROOT, input_bytes: bytes | None = None) -> bytes:
    return run("git", *argv, cwd=cwd, input_bytes=input_bytes)


def text_git(*argv: str, cwd: Path = ROOT) -> str:
    return git(*argv, cwd=cwd).decode("utf-8").strip()


def patch_id(commit: str, *, repo: Path = ROOT) -> str:
    shown = git(
        "show",
        "--pretty=format:",
        "--binary",
        "--full-index",
        commit,
        cwd=repo,
    )
    result = git("patch-id", "--stable", cwd=repo, input_bytes=shown).decode("ascii").strip()
    if not result:
        raise AssertionError(f"commit has no stable patch ID: {commit}")
    return result.split()[0]


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"expected object: {path}")
    return value


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def audit_blob() -> bytes:
    matches: list[str] = []
    for line in text_git("rev-list", "--objects", "--all").splitlines():
        object_id, separator, path = line.partition(" ")
        if separator and path == AUDIT_NAME:
            matches.append(object_id)
    if not matches:
        raise AssertionError("salvage audit object is unavailable")
    bodies = {git("cat-file", "blob", object_id) for object_id in set(matches)}
    exact = [body for body in bodies if sha(body) == AUDIT_SHA256]
    if len(exact) != 1:
        raise AssertionError("salvage audit SHA-256 did not resolve uniquely")
    return exact[0]


def verify_lineage(policy: dict[str, Any], seal: dict[str, Any]) -> dict[str, Any]:
    body = audit_blob()
    audit_text = body.decode("utf-8")
    for marker in (
        "| G20 | 285 | `53b92423`; copies `6a7139e2,e972edfc,50c3fb52`",
        "| G21 | 285 | `63faaa51`; copy `87356190`",
        "| G22 | 285 | `6e289afd`",
        "include G20,G21; drop G22",
    ):
        if marker not in audit_text:
            raise AssertionError(f"audit mapping marker absent: {marker}")

    lineage = policy.get("logical_patch_lineage")
    if not isinstance(lineage, dict) or lineage != seal.get("logical_patch_lineage"):
        raise AssertionError("policy/seal logical lineage differs")
    if lineage.get("authority") != {
        "document_id": AUDIT_NAME,
        "sha256": AUDIT_SHA256,
    }:
        raise AssertionError("lineage authority does not bind the audited blob")
    if canonical_sha(lineage) != seal.get("logical_patch_lineage_sha256"):
        raise AssertionError("logical lineage content address differs")

    commits = text_git("rev-list", "--reverse", "--no-merges", f"{BASE}..{CANDIDATE}").splitlines()
    inventory = [{"commit": commit, "stable_patch_id": patch_id(commit)} for commit in commits]
    if inventory != seal.get("stable_patch_ids"):
        raise AssertionError("candidate stable-patch inventory differs from seal")
    candidate_by_commit = {row["commit"]: row["stable_patch_id"] for row in inventory}
    patch_counts: dict[str, int] = {}
    for value in candidate_by_commit.values():
        patch_counts[value] = patch_counts.get(value, 0) + 1
    if len(patch_counts) != len(inventory) or any(value != 1 for value in patch_counts.values()):
        raise AssertionError("candidate stable patch IDs are not unique")

    groups = {item["group_id"]: item for item in lineage.get("groups", [])}
    if set(groups) != set(EXPECTED_GROUPS):
        raise AssertionError("lineage does not contain exactly G20/G21/G22")
    for group_id, expected in EXPECTED_GROUPS.items():
        actual = groups[group_id]
        for field, value in expected.items():
            if actual.get(field) != value:
                raise AssertionError(f"{group_id} {field} differs from audit mapping")
        source_commits = [
            actual["representative_commit"],
            *actual["duplicate_alias_commits"],
        ]
        actual_ids = [patch_id(commit) for commit in source_commits]
        if len(set(actual_ids)) != 1 or actual_ids[0] != actual["stable_patch_id"]:
            raise AssertionError(f"{group_id} source aliases are not patch-equivalent")
        count = patch_counts.get(actual["stable_patch_id"], 0)
        if actual["disposition"] == "INCLUDE":
            candidate_commit = actual["candidate_commit"]
            if candidate_by_commit.get(candidate_commit) != actual["stable_patch_id"] or count != 1:
                raise AssertionError(f"{group_id} is not included exactly once")
        elif actual["candidate_commit"] is not None or count != 0:
            raise AssertionError(f"{group_id} obsolete patch is present")
    return {
        "audit_sha256": sha(body),
        "candidate_nonmerge_commits": len(commits),
        "unique_candidate_patch_ids": len(patch_counts),
        "groups": {
            key: {
                "disposition": groups[key]["disposition"],
                "stable_patch_id": groups[key]["stable_patch_id"],
                "candidate_count": patch_counts.get(groups[key]["stable_patch_id"], 0),
                "source_commit_count": 1 + len(groups[key]["duplicate_alias_commits"]),
            }
            for key in sorted(groups)
        },
    }


def verify_actual_guard(policy: dict[str, Any], seal: dict[str, Any]) -> dict[str, Any]:
    module = load_module(PUBLICATION_INTEGRITY, "pr285_publication_integrity_oracle")
    candidate_rows = seal["stable_patch_ids"]
    lineage = policy["logical_patch_lineage"]
    mutations: dict[str, dict[str, Any]] = {}

    wrong_patch = deepcopy(lineage)
    wrong_patch["groups"][0]["stable_patch_id"] = lineage["groups"][2]["stable_patch_id"]
    mutations["wrong_declared_patch_id"] = wrong_patch

    wrong_alias = deepcopy(lineage)
    wrong_alias["groups"][0]["duplicate_alias_commits"] = [
        lineage["groups"][1]["representative_commit"]
    ]
    mutations["wrong_alias"] = wrong_alias

    wrong_candidate = deepcopy(lineage)
    wrong_candidate["groups"][0]["candidate_commit"] = lineage["groups"][1]["candidate_commit"]
    mutations["wrong_candidate"] = wrong_candidate

    duplicate_group = deepcopy(lineage)
    duplicate_group["groups"].append(deepcopy(duplicate_group["groups"][0]))
    mutations["duplicate_group"] = duplicate_group

    obsolete_present = deepcopy(lineage)
    obsolete_present["groups"][2]["candidate_commit"] = lineage["groups"][0]["candidate_commit"]
    mutations["obsolete_candidate_nonnull"] = obsolete_present

    include_absent = deepcopy(lineage)
    include_absent["groups"][2]["disposition"] = "INCLUDE"
    mutations["include_without_candidate"] = include_absent

    killed: dict[str, str] = {}
    for mutation_id, mutated in mutations.items():
        try:
            module._validate_logical_patch_lineage(
                ROOT,
                mutated,
                candidate_patch_ids=candidate_rows,
            )
        except module.PublicationIntegrityError as exc:
            killed[mutation_id] = str(exc)
        else:
            raise AssertionError(f"logical-lineage mutation survived: {mutation_id}")

    scratch = ARTIFACT_DIR / ".oracle-duplicate-guard"
    shutil.rmtree(scratch, ignore_errors=True)
    scratch.mkdir()
    try:
        git("init", "-q", cwd=scratch)
        git("config", "user.email", "oracle@example.invalid", cwd=scratch)
        git("config", "user.name", "PR285 Oracle", cwd=scratch)
        target = scratch / "feature.txt"
        target.write_text("included\n", encoding="utf-8")
        git("add", "feature.txt", cwd=scratch)
        git("commit", "-qm", "base patch", cwd=scratch)
        target.unlink()
        git("add", "-u", cwd=scratch)
        git("commit", "-qm", "revert base patch", cwd=scratch)
        base = text_git("rev-parse", "HEAD", cwd=scratch)
        target.write_text("included\n", encoding="utf-8")
        git("add", "feature.txt", cwd=scratch)
        git("commit", "-qm", "reintroduce base patch", cwd=scratch)
        candidate = text_git("rev-parse", "HEAD", cwd=scratch)
        try:
            module.reject_duplicate_stable_patch_ids(
                scratch,
                base_sha=base,
                candidate_sha=candidate,
            )
        except module.PublicationIntegrityError as exc:
            duplicate_without_declaration = str(exc)
        else:
            raise AssertionError(
                "candidate duplicate stable patch survived without a lineage declaration"
            )
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    replayed = module.reject_duplicate_stable_patch_ids(
        ROOT,
        base_sha=BASE,
        candidate_sha=CANDIDATE,
    )
    if replayed != candidate_rows:
        raise AssertionError("unconditional candidate patch guard replay differs")
    return {
        "lineage_mutations_killed": killed,
        "unconditional_duplicate_guard_without_declaration": duplicate_without_declaration,
    }


def verify_seals_and_receipt(
    final_seal: dict[str, Any], implementation_seal: dict[str, Any]
) -> dict[str, Any]:
    for label, value, path in (
        ("final", final_seal, FINAL_SEAL),
        ("implementation", implementation_seal, IMPLEMENTATION_SEAL),
    ):
        if canonical_sha(value, omit={"seal_sha256"}) != value.get("seal_sha256"):
            raise AssertionError(f"{label} seal content address differs")
        if value.get("candidate_tree_sha") != text_git(
            "rev-parse", f"{value['candidate_sha']}^{{tree}}"
        ):
            raise AssertionError(f"{label} seal tree differs")
        if value.get("merge_base_sha") != text_git(
            "merge-base", value["base_sha"], value["candidate_sha"]
        ):
            raise AssertionError(f"{label} merge base differs")
        if sha(path.read_bytes()) not in {
            "641c72f627cb9a221dab61751bd971513bb1a2623f2d4b7281cd78dc7226060e",
            "02773cca24cdf455df4e96bd069c7abde4f186964aefa77c031bd2217534f149",
        }:
            raise AssertionError(f"{label} seal file SHA-256 differs")

    final_only_commits = text_git(
        "rev-list", "--reverse", f"{IMPLEMENTATION}..{CANDIDATE}"
    ).splitlines()
    if final_only_commits != [CANDIDATE]:
        raise AssertionError("final review candidate is not one bounded follow-up commit")
    final_only_paths = text_git(
        "diff", "--name-only", "--no-renames", f"{IMPLEMENTATION}..{CANDIDATE}"
    ).splitlines()
    expected_paths = [
        "docs/PR_DELTAS/pr-285.md",
        "docs/codex_handoff/pr_status.yaml",
        "machine_readable/pr_status.yaml",
    ]
    if final_only_paths != expected_paths:
        raise AssertionError("final review candidate changed non-status/delta bytes")
    if final_seal["production_hash"] != implementation_seal["production_hash"]:
        raise AssertionError("production hash changed after implementation integration")

    status = yaml.safe_load(STATUS.read_text(encoding="utf-8"))
    status_mirror = yaml.safe_load(STATUS_MIRROR.read_text(encoding="utf-8"))
    if status != status_mirror or STATUS.read_bytes() != STATUS_MIRROR.read_bytes():
        raise AssertionError("status mirrors differ")
    record = status["stacked_pr_execution"]["prs"]["PR-285"]
    if record["production_hash"] != final_seal["production_hash"]:
        raise AssertionError("status production hash differs from seal")
    if record["assurance_budget"] != {"maximum": 16, "consumed": 11}:
        raise AssertionError("bounded rereview changed assurance consumption")
    if record["gate_dispositions"] != {
        "eligibility": "PASS",
        "implementation": "PASS",
        "validation": "PASS",
        "harness": "PASS",
        "portability_replay": "PASS",
        "cas": "INCONCLUSIVE",
        "review": "DEFERRED",
        "seal": "INELIGIBLE",
        "push": "INELIGIBLE",
        "publication": "INELIGIBLE",
    }:
        raise AssertionError("status gate ceiling differs")

    dependency_hashes = record["dependency_hashes"]
    for key, path in DEPENDENCY_PATHS.items():
        implementation_bytes = git("show", f"{IMPLEMENTATION}:{path}")
        final_bytes = git("show", f"{CANDIDATE}:{path}")
        if implementation_bytes != final_bytes:
            raise AssertionError(f"dependency bytes changed after integration: {key}")
        if sha(final_bytes) != dependency_hashes[key]:
            raise AssertionError(f"status dependency hash differs: {key}")
    if dependency_hashes["salvage_audit"] != AUDIT_SHA256:
        raise AssertionError("status salvage-audit hash differs")

    receipt = load_json(IMPLEMENTATION_RECEIPT)
    if canonical_sha(receipt, omit={"receipt_sha256"}) != receipt.get("receipt_sha256"):
        raise AssertionError("implementation receipt content address differs")
    bindings = {
        "candidate_seal_sha256": implementation_seal["seal_sha256"],
        "candidate_sha": implementation_seal["candidate_sha"],
        "candidate_tree_sha": implementation_seal["candidate_tree_sha"],
        "diff_sha256": implementation_seal["diff_sha256"],
        "changed_files_sha256": implementation_seal["changed_files_sha256"],
        "latest_target_sha": implementation_seal["base_sha"],
        "integration_policy_sha256": implementation_seal["integration_policy"]["sha256"],
    }
    if any(receipt.get(key) != value for key, value in bindings.items()):
        raise AssertionError("implementation receipt does not cross-bind its seal")
    if receipt.get("status") != "PASS" or len(receipt.get("commands", [])) != 8:
        raise AssertionError("implementation receipt did not pass all commands")
    if any(
        command.get("returncode") != 0 or command.get("timed_out") is not False
        for command in receipt["commands"]
    ):
        raise AssertionError("implementation receipt contains a failed command")
    merge_tree = text_git(
        "-c",
        f"core.hooksPath={os.devnull}",
        "merge-tree",
        "--write-tree",
        "--no-messages",
        implementation_seal["base_sha"],
        implementation_seal["candidate_sha"],
    )
    if merge_tree != receipt["merged_tree_sha"]:
        raise AssertionError("implementation merged tree differs")
    return {
        "final_only_commit": final_only_commits[0],
        "final_only_paths": final_only_paths,
        "production_hash_unchanged": final_seal["production_hash"],
        "dependency_hash_count_unchanged": len(DEPENDENCY_PATHS) + 1,
        "assurance_consumed": 11,
        "implementation_receipt_commands": len(receipt["commands"]),
        "implementation_receipt_sha256": receipt["receipt_sha256"],
    }


def verify_receipt_and_write_boundary(policy: dict[str, Any]) -> dict[str, Any]:
    runner = load_module(RUNNER, "pr285_receipt_runner_oracle")
    payload = runner.build_complete_adjudication_receipt()
    if runner._serialized(payload) != TRACKED_RECEIPT.read_bytes():
        raise AssertionError("tracked receipt is not exact replay")
    if payload["receipt_content_sha256"] != runner.receipt_content_sha256(payload):
        raise AssertionError("receipt content address differs")
    if len(payload["rows"]) != 80:
        raise AssertionError("receipt row count differs")
    if any(row.get("claim_ceiling") != "diagnostic_only" for row in payload["rows"]):
        raise AssertionError("row claim ceiling was promoted")
    if payload["metadata"] != {
        **payload["metadata"],
        "claim_tier": "diagnostic_only",
        "transfer_source": "none",
        "observed_data_executed": False,
        "public_use": False,
        "family_identification_gate": "BLOCKED_PRE_NATIVE_ATLAS",
    }:
        raise AssertionError("receipt claim/family ceiling differs")
    if policy.get("claim_ceiling") != "diagnostic_only" or policy.get(
        "family_identification_gate"
    ) != "BLOCKED_PRE_NATIVE_ATLAS":
        raise AssertionError("policy claim/family ceiling differs")
    registry_ids = [row["mutation_id"] for row in payload["mutation_registry"]]
    result_ids = [row["mutation_id"] for row in payload["mutation_results"]]
    if registry_ids != result_ids or len(registry_ids) != 13:
        raise AssertionError("mutation result inventory differs")
    if any(
        not (
            row["executed"] is True
            and row["activated"] is True
            and row["killed"] is True
            and row["survivor"] is False
            and row["kill_marker"]
        )
        for row in payload["mutation_results"]
    ):
        raise AssertionError("registered receipt mutation survived")
    for binding in payload["source_bindings"]:
        path = ROOT / binding["path"]
        if not path.is_file() or path.is_symlink() or sha(path.read_bytes()) != binding["sha256"]:
            raise AssertionError(f"source binding differs: {binding['path']}")

    scratch = ARTIFACT_DIR / ".oracle-write-boundary"
    shutil.rmtree(scratch, ignore_errors=True)
    scratch.mkdir()
    original_root, original_output = runner.ROOT, runner.OUTPUT
    cases: list[str] = []
    try:
        ordinary_root = scratch / "ordinary"
        destination = ordinary_root / "generated/receipt.json"
        destination.parent.mkdir(parents=True)
        runner.ROOT, runner.OUTPUT = ordinary_root, destination
        runner._validate_output_destination_for_write()
        runner._atomic_write(b"atomic\n")
        if destination.read_bytes() != b"atomic\n" or destination.stat().st_nlink != 1:
            raise AssertionError("atomic write did not replace one regular file")
        cases.append("atomic_regular_replace")

        outside = scratch / "outside.txt"
        outside.write_text("preserve\n", encoding="utf-8")
        destination.unlink()
        destination.hardlink_to(outside)
        try:
            runner._validate_output_destination_for_write()
        except runner.PillarTAdjudicationError as exc:
            if "NOT_SINGLE_LINK_FILE" not in str(exc):
                raise
        else:
            raise AssertionError("hardlinked output was accepted")
        if outside.read_text(encoding="utf-8") != "preserve\n":
            raise AssertionError("hardlink rejection changed outside bytes")
        cases.append("hardlink_refused_before_build")

        destination.unlink()
        destination.symlink_to(outside)
        try:
            runner._validate_output_destination_for_write()
        except runner.PillarTAdjudicationError as exc:
            if "DESTINATION_SYMLINK" not in str(exc):
                raise
        else:
            raise AssertionError("symlink output was accepted")
        if outside.read_text(encoding="utf-8") != "preserve\n":
            raise AssertionError("symlink rejection changed outside bytes")
        cases.append("symlink_destination_refused")

        escape_root = scratch / "escape-root"
        escape_root.mkdir()
        runner.ROOT, runner.OUTPUT = escape_root, scratch / "escaped.json"
        try:
            runner._validate_output_destination_for_write()
        except runner.PillarTAdjudicationError as exc:
            if "ESCAPES_REPOSITORY_ROOT" not in str(exc):
                raise
        else:
            raise AssertionError("escaping output path was accepted")
        cases.append("path_escape_refused")

        symlink_root = scratch / "symlink-root"
        real_parent = scratch / "real-parent"
        symlink_root.mkdir()
        real_parent.mkdir()
        (symlink_root / "generated").symlink_to(real_parent, target_is_directory=True)
        runner.ROOT, runner.OUTPUT = symlink_root, symlink_root / "generated/receipt.json"
        try:
            runner._validate_output_destination_for_write()
        except runner.PillarTAdjudicationError as exc:
            if "OUTPUT_PARENT_NOT_REGULAR" not in str(exc):
                raise
        else:
            raise AssertionError("symlinked parent was accepted")
        cases.append("symlink_parent_refused")
    finally:
        runner.ROOT, runner.OUTPUT = original_root, original_output
        shutil.rmtree(scratch, ignore_errors=True)

    check = subprocess.run(
        [sys.executable, "-B", str(RUNNER), "check"],
        cwd=Path("/tmp"),
        capture_output=True,
        text=True,
        check=False,
    )
    if check.returncode != 0 or check.stdout != "ok=true\n":
        raise AssertionError("receipt check is not portable from /tmp")
    return {
        "rows": len(payload["rows"]),
        "source_bindings": len(payload["source_bindings"]),
        "registered_mutations_killed": len(payload["mutation_results"]),
        "write_boundary_cases": cases,
        "portable_check_from_tmp": True,
        "receipt_content_sha256": payload["receipt_content_sha256"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output).resolve()
    if output.parent != ARTIFACT_DIR or output.name != "lineage_replay_oracle_output.json":
        raise SystemExit("output must be the registered assignment-local oracle artifact")
    if text_git("status", "--porcelain=v1"):
        raise AssertionError("candidate worktree is not clean")
    if text_git("rev-parse", "HEAD") != CANDIDATE:
        raise AssertionError("HEAD differs from frozen candidate")

    policy = load_json(POLICY)
    final_seal = load_json(FINAL_SEAL)
    implementation_seal = load_json(IMPLEMENTATION_SEAL)
    result = {
        "schema_version": 1,
        "run_id": RUN_ID,
        "assignment_id": ASSIGNMENT_ID,
        "candidate_sha": CANDIDATE,
        "lineage_replay": verify_lineage(policy, final_seal),
        "hostile_guard_replay": verify_actual_guard(policy, final_seal),
        "seal_receipt_and_bounded_rereview": verify_seals_and_receipt(
            final_seal, implementation_seal
        ),
        "receipt_and_write_boundary": verify_receipt_and_write_boundary(policy),
        "status": "PASS",
    }
    payload = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode("utf-8")
    temporary = output.with_suffix(".tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, output)
    print(json.dumps({"ok": True, "output": str(output), "sha256": sha(payload)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
