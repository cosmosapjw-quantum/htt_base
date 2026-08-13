#!/usr/bin/env python3
"""Independent, read-only PR-289 frozen-candidate replay oracle."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[5]
RUN_ID = "pr289-frozen-independent-review-20260811"
ASSIGNMENT_ID = "A-PR289-FROZEN-REPLAY"
BASE = "27df5da040e27eeaad44873ba3424ff73fb4bb09"
CANDIDATE = "1ad54d3c5a484816128a1df93d54953589780520"
TREE = "67ec8432a6557bb460dfe8015b361fe9f6c00d1d"
SEAL_FILE_SHA256 = "8aa29e14dcd7e704235a524634dcab219c46728df47da7b9ba8d5885f27271d5"
SEAL_SHA256 = "0347f2f5011309909423c4e27e090556c95c2a237e7d9c7a5ab3781087407a47"

REQUIRED_INPUTS = {
    ".prguard/runtime/PR289_CANDIDATE_SEAL.json": SEAL_FILE_SHA256,
    "docs/research_program/post_pr275/pr289_spec.yaml": "75c466e103941b2a3592644718a9b88c4f48391196ada08c7610c760eea924fc",
    "docs/research_program/post_pr275/pr289_publication_policy.json": "16f8f3c37340d7a11ec3961825b626a43942ceced6e2db812b55738cbeb8b302",
    "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json": "e72eee5fd720318367bd38b90412aa0286f521be7cb47b7a988df4e579ab167f",
    "htt/src/common/data_identity.py": "91a148a67ff0b338cd5aedef5efc81039607302f8473e93ddf37fa70ed399539",
    "tests/contracts/test_data_identity_registry_v2.py": "df17c8c6d5e02298ae53c367a2919872e5ceea9d3e837d31193b1bf5a6ecb971",
    "scripts/codex_harness/run_pr289_data_identity_v2.py": "27f7d531515910ed6758780b029e4c1c7bb2299585d4b51a85ea5340151c86b4",
    "docs/generated/pr289_data_identity_v2_receipt.json": "15caa3ea64b302736e01261942173e08d85c7197545d299d7bb5582763623d5b",
    "docs/research_program/post_pr275/data_runbooks.yaml": "b9e369041fef302e1ed172d9bd414f7ead7482625dc1d2d1a26b8f04a1ba29de",
    "docs/harness/CLAIM_LEDGER.md": "86389d3d0c432f6adfa66982bc36c93bfb8868f6b71a519309f7c4f8bc8d848b",
    "docs/PR_DELTAS/pr-289.md": "20ef5426fe50b5cb42980b177b3e4aba16cf0af007076a4a7ab68a860e4cf2e9",
    "docs/codex_handoff/pr_status.yaml": "64b72e89b95ba595543bcebe53906524755e941e6610c5419a7637afb88c1e3b",
}

EXPECTED_COMMITS = [
    "df548eefdc703d02773d9539cd12e54348534800",
    "c4b1b1774e5faa2125b2e9ad6167b331a300d2a0",
    "ac898295db4ec60e52973ad7c180bd0f24e0ee4d",
    "8cbbdb4dc32c75d276d13713e61a3fd8724f966c",
    "fd36d51dc6b62b22373578cdee5f5e9c65bd88cc",
    "3889defa7a8836db171bd198946de8a6b86ebcf5",
    "ae35b887d87b35ad741621e39c0653aff6e83057",
    "6fc726bd7f512bd5d6576468d807d16084c65bc8",
    CANDIDATE,
]

EXPECTED_PATCH_IDS = [
    "fd24654567276d9c010016ee58f37cea75eef0c8",
    "122120d7f0b90b9dbe24be63fd0fdf0b56655484",
    "8c57aa2af00713bc3be8c49001e9275e769fecda",
    "71b143a3fd6b6e9899174d56e760bbf1f3f38d89",
    "da3256235bd064f766ee478155f796be13065b81",
    "52d53b7b5c28e6acda0f314260415d90e792a24b",
    "bdae1ef3ebeb7002bbd7eb7d76a7371e230ba14f",
    "fe315a1b815b1a5710db5cf982c9a5c6c3d2ba75",
    "366360cd5531c4cecdc62c8a1237d4ccd2acc3ee",
]

RECOVERY_GROUPS = {
    "G39": ["44091dea7341e96cbf152b1e42d072de977f8522"],
    "G40": ["a757eeee6c97e532a740a67909703d5ad394ab4a"],
    "G42": [
        "c2037e8ae1163db0f57b36355da24cf20ceea320",
        "681285b042c99402ea2e7ed3a19cea4b5c6bc5f4",
        "da3cdb829f00c50339ea7c1c178c7499768dbc10",
    ],
    "G45": [
        "7f9ac031f7c585076bb955cac6326d1b600992d8",
        "d697fe08fff9a4fa465ef7fb3022c59c19fd4305",
        "db41afc8d89d79e2a47db9ebc0eecaee8ccb5679",
    ],
    "G46": [
        "834e15d76bd4517a26c2344536d201e1de9deb8f",
        "6a9f9d5e84d08e4bd3fe0caa0b17e3925d8090a9",
    ],
    "G47": [
        "91d8b8adb72ec8c1e07cfa46fe028fa56867290b",
        "52386845290f47ad6243cc537447942ef6bf12db",
    ],
    "G48": [
        "dde54a713ebb0408c3690f5b7d3fdded17e19ff3",
        "48e280d9b4b7d88dadf7fff857fca7910defb563",
    ],
}

POLICY_COMMANDS = [
    ["/usr/bin/python3", "-B", "scripts/codex_harness/run_pr289_data_identity_v2.py", "focused"],
    ["/usr/bin/python3", "-B", "scripts/codex_harness/run_pr289_data_identity_v2.py", "preflight"],
    ["/usr/bin/python3", "-B", "scripts/codex_harness/run_pr289_data_identity_v2.py", "adjacent"],
    ["/usr/bin/python3", "-B", "scripts/codex_harness/run_pr289_data_identity_v2.py", "check"],
    ["/usr/bin/python3", "-B", "scripts/codex_harness/run_pr289_data_identity_v2.py", "portable"],
    [
        "/usr/bin/python3", "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q",
        "scripts/codex_harness/test_publication_integrity.py", "-k",
        "policy_nonrelaxable_metadata_fails_closed or candidate_seal_cross_binds_declared_policy_identity",
    ],
    [
        "/usr/bin/python3", "-B", "scripts/codex_harness/validate_pr_dag.py",
        "docs/codex_handoff/pr_backlog.yaml", "--status",
        "docs/codex_handoff/pr_status.yaml", "--strict-rescue-slice",
    ],
    [
        "/usr/bin/python3", "-B", "scripts/check_claim_language.py", "--strict-missing",
        "--include-archives", "htt/src/common/data_identity.py",
        "tests/contracts/test_data_identity_registry_v2.py",
        "docs/research_program/post_pr275/pr289_spec.yaml",
        "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json",
        "docs/research_program/post_pr275/data_runbooks.yaml",
        "docs/harness/CLAIM_LEDGER.md",
        "docs/generated/pr289_data_identity_v2_receipt.json",
        "docs/PR_DELTAS/pr-289.md",
    ],
]


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return sha256_bytes(raw)


def run(argv: list[str], *, timeout: int = 1800) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def git(*args: str, check: bool = True) -> str:
    proc = run(["git", *args], timeout=300)
    if check and proc.returncode:
        raise AssertionError(f"git {' '.join(args)} failed: {proc.stderr}")
    return proc.stdout.strip()


def patch_id(commit: str) -> str:
    shown = run(["git", "show", "--pretty=format:", "--binary", commit], timeout=300)
    assert shown.returncode == 0, shown.stderr
    proc = subprocess.run(
        ["git", "patch-id", "--stable"],
        cwd=ROOT,
        input=shown.stdout,
        text=True,
        capture_output=True,
        timeout=300,
        check=False,
    )
    assert proc.returncode == 0 and proc.stdout.strip(), proc.stderr
    return proc.stdout.split()[0]


def blob(commit: str, path: str) -> str | None:
    proc = run(["git", "rev-parse", f"{commit}:{path}"], timeout=300)
    return proc.stdout.strip() if proc.returncode == 0 else None


def status_card(payload: dict[str, Any], pr_id: str) -> dict[str, Any]:
    return payload["stacked_pr_execution"]["prs"][pr_id]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    output.resolve().relative_to(
        ROOT / ".agent-harness" / "runs" / RUN_ID / "artifacts" / ASSIGNMENT_ID
    )

    checks: list[dict[str, Any]] = []

    def checked(name: str, condition: bool, evidence: Any) -> None:
        checks.append({"check": name, "status": "PASS" if condition else "FAIL", "evidence": evidence})
        if not condition:
            raise AssertionError(f"{name}: {evidence}")

    actual_hashes = {
        path: sha256_bytes((ROOT / path).read_bytes()) for path in REQUIRED_INPUTS
    }
    checked("required_input_hashes", actual_hashes == REQUIRED_INPUTS, actual_hashes)

    seal = json.loads((ROOT / ".prguard/runtime/PR289_CANDIDATE_SEAL.json").read_text())
    checked("seal_identity", seal["seal_sha256"] == SEAL_SHA256, seal["seal_sha256"])
    checked("candidate_head", git("rev-parse", "HEAD") == CANDIDATE, git("rev-parse", "HEAD"))
    checked("candidate_tree", git("rev-parse", "HEAD^{tree}") == TREE, git("rev-parse", "HEAD^{tree}"))
    checked("merge_base", git("merge-base", BASE, CANDIDATE) == BASE, git("merge-base", BASE, CANDIDATE))
    checked(
        "exact_latest_target",
        git("rev-parse", "refs/remotes/origin/changeset/pr288-bayesian-evidence-recovery-20260811") == BASE,
        BASE,
    )
    seal_verify = run([
        "/usr/bin/python3", ".agent-harness/scripts/candidate_seal.py", "verify",
        "--seal", ".prguard/runtime/PR289_CANDIDATE_SEAL.json",
    ], timeout=300)
    checked("candidate_seal_black_box_verify", seal_verify.returncode == 0, seal_verify.stderr)

    commits = git("rev-list", "--reverse", f"{BASE}..{CANDIDATE}").splitlines()
    checked("linear_commit_inventory", commits == EXPECTED_COMMITS, commits)
    parents = [git("show", "-s", "--format=%P", commit).split() for commit in commits]
    checked("linear_single_parent_chain", all(len(row) == 1 for row in parents), parents)
    patch_ids = [patch_id(commit) for commit in commits]
    checked("stable_patch_ids_exact", patch_ids == EXPECTED_PATCH_IDS, patch_ids)
    checked("stable_patch_ids_unique", len(set(patch_ids)) == len(patch_ids), patch_ids)

    group_patch_ids = {name: [patch_id(commit) for commit in rows] for name, rows in RECOVERY_GROUPS.items()}
    checked("g45_alias_patch_identity", len(set(group_patch_ids["G45"])) == 1 == int(group_patch_ids["G45"][0] == EXPECTED_PATCH_IDS[1]), group_patch_ids["G45"])
    checked("g46_alias_patch_identity", len(set(group_patch_ids["G46"])) == 1 == int(group_patch_ids["G46"][0] == EXPECTED_PATCH_IDS[2]), group_patch_ids["G46"])
    checked("g47_alias_patch_identity", len(set(group_patch_ids["G47"])) == 1, group_patch_ids["G47"])
    checked("g48_alias_patch_identity", len(set(group_patch_ids["G48"])) == 1, group_patch_ids["G48"])
    excluded = [commit for name in ("G39", "G40", "G42") for commit in RECOVERY_GROUPS[name]]
    ancestry = {}
    for commit in excluded:
        proc = run(["git", "merge-base", "--is-ancestor", commit, CANDIDATE], timeout=300)
        ancestry[commit] = proc.returncode
    checked("g39_g40_g42_not_ancestors", all(rc == 1 for rc in ancestry.values()), ancestry)

    core_paths = (
        "htt/src/common/data_identity.py",
        "scripts/codex_harness/run_pr289_data_identity_v2.py",
        "tests/contracts/test_data_identity_registry_v2.py",
    )
    g47_blobs = {
        path: [blob("8cbbdb4dc32c75d276d13713e61a3fd8724f966c", path), blob("91d8b8ad", path)]
        for path in core_paths
    }
    checked("g47_bounded_core_blobs", all(a == b for a, b in g47_blobs.values()), g47_blobs)
    checked(
        "g47_stale_receipt_excluded",
        blob("8cbbdb4dc32c75d276d13713e61a3fd8724f966c", "docs/generated/pr289_data_identity_v2_receipt.json") is None,
        "candidate core commit does not add generated receipt",
    )
    g48_test = "tests/contracts/test_data_identity_registry_v2.py"
    checked("g48_bounded_test_blob", blob("fd36d51", g48_test) == blob("dde54a71", g48_test), blob("fd36d51", g48_test))
    checked(
        "g48_stale_receipt_excluded",
        "docs/generated/pr289_data_identity_v2_receipt.json" not in git("diff-tree", "--no-commit-id", "--name-only", "-r", "fd36d51"),
        "portable salvage commit does not touch generated receipt",
    )

    spec = yaml.safe_load((ROOT / "docs/research_program/post_pr275/pr289_spec.yaml").read_text())
    registry = json.loads((ROOT / "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json").read_text())
    receipt = json.loads((ROOT / "docs/generated/pr289_data_identity_v2_receipt.json").read_text())
    status = yaml.safe_load((ROOT / "docs/codex_handoff/pr_status.yaml").read_text())
    backlog = yaml.safe_load((ROOT / "docs/codex_handoff/pr_backlog.yaml").read_text())

    checked("registry_content_address", receipt["registry_content_id"] == "sha256:" + canonical_sha256(registry), receipt["registry_content_id"])
    receipt_without_id = dict(receipt)
    receipt_without_id.pop("receipt_content_id")
    checked("receipt_content_address", receipt["receipt_content_id"] == "sha256:" + canonical_sha256(receipt_without_id), receipt["receipt_content_id"])
    bindings = receipt["source_bindings"]
    binding_checks = {
        path: binding == "sha256:" + sha256_bytes((ROOT / path).read_bytes())
        for path, binding in bindings.items()
    }
    checked("fresh_receipt_source_bindings", all(binding_checks.values()), binding_checks)
    historical_receipt_blobs = {commit: blob(commit, "docs/generated/pr289_data_identity_v2_receipt.json") for commit in RECOVERY_GROUPS["G47"] + RECOVERY_GROUPS["G48"]}
    checked(
        "no_historical_receipt_blob_reuse",
        all(value != blob(CANDIDATE, "docs/generated/pr289_data_identity_v2_receipt.json") for value in historical_receipt_blobs.values()),
        historical_receipt_blobs,
    )
    mutation_ids = [row["mutation_id"] for row in spec["mutation_registry"]]
    receipt_mutations = [row["mutation_id"] for row in receipt["mutation_results"]]
    checked("registered_mutation_exact_order", mutation_ids == receipt_mutations and len(mutation_ids) == 30, receipt_mutations)
    checked("registered_mutations_live_killed", all(row["executed"] and row["activated"] and row["killed"] for row in receipt["mutation_results"]), len(receipt["mutation_results"]))
    checked("zero_admission", receipt["aggregate_status"] == "NO_ADMITTED_IDENTITIES" and all(row["status"] == "REJECTED_NOT_PRESENT" for row in receipt["lane_decisions"]), receipt["aggregate_status"])
    checked("zero_authorization", all(row["status"] == "NOT_AUTHORIZED" for row in receipt["authorization_receipts"]), [row["status"] for row in receipt["authorization_receipts"]])
    checked("claim_ceiling", receipt["claim_tier"] == "diagnostic_only" and receipt["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS" and not receipt["observed_data_executed"] and not receipt["public_use"], receipt["claim_tier"])

    lane_expectations = {
        "PLANCK": (13, "H-PLANCK", "common.planck_native_identity.v1"),
        "CF4": (9, "H-CF4", "common.cf4_native_identity.v1"),
        "HSC_KIDS": (15, "H-HSC-KiDS", "common.hsc_kids_native_identity.v1"),
        "ACT": (7, "H-ACT", "common.registered_product_native_identity.v1"),
        "DESI": (5, "H-DESI", "common.registered_product_native_identity.v1"),
        "JWST_SN": (5, "H-JWST", "common.registered_product_native_identity.v1"),
    }
    observed_lanes = {
        lane["lane_id"]: (len(lane["required_component_ids"]), lane["required_human_gate_id"], lane["native_identity_schema"])
        for lane in registry["lanes"]
    }
    checked("machine_lane_cardinality_and_gate_identity", observed_lanes == lane_expectations, observed_lanes)
    desi = next(row for row in registry["lanes"] if row["lane_id"] == "DESI")
    checked("desi_exact_mock_cardinality", desi["component_cardinality"]["ezmock_inventory"] == 1000 and desi["component_cardinality"]["abacus_inventory"] == 25, desi["component_cardinality"])
    pr280_resolution = status["execution_resolutions"]["PR-280"]
    checked("pr280_terminal_receipt_no_success", pr280_resolution["resolution"] == "COMPLETED_FAILED_WITH_RECEIPT" and pr280_resolution["success_dependency_satisfied"] is False, pr280_resolution)
    pr289 = status_card(status, "PR-289")
    pr290 = status_card(status, "PR-290")
    backlog_pr289 = next(row for row in backlog["prs"] if row["id"] == "PR-289")
    checked("workflow_authorization_domain", backlog_pr289["authorization_domain"] == "workflow_only" and backlog_pr289["execution_authorization"] == "EXPLICIT_USER_AUTHORIZED", {"authorization_domain": backlog_pr289["authorization_domain"], "execution_authorization": backlog_pr289["execution_authorization"]})
    checked("pr290_ineligible_zero_budget", pr290["gate_dispositions"]["eligibility"] == "INELIGIBLE" and pr290["assurance_budget"]["consumed"] == 0 and pr290["lifecycle"] == "PLANNED", pr290)
    checked("immutable_pr274_hashes", spec["historical_boundary"]["v1_replay_commit"] == "ff9ef9f45747e559c5343b463cf010dfc3a7432a" and bindings[spec["historical_boundary"]["v1_registry"]] == "sha256:" + spec["historical_boundary"]["v1_registry_sha256"] and bindings[spec["historical_boundary"]["v1_result"]] == "sha256:" + spec["historical_boundary"]["v1_result_sha256"], spec["historical_boundary"])

    command_results = []
    for argv in POLICY_COMMANDS:
        started = time.monotonic()
        proc = run(argv)
        elapsed = time.monotonic() - started
        result = {
            "argv": argv,
            "returncode": proc.returncode,
            "runtime_seconds": elapsed,
            "stdout_sha256": sha256_bytes(proc.stdout.encode()),
            "stderr_sha256": sha256_bytes(proc.stderr.encode()),
            "stdout_tail": proc.stdout.strip().splitlines()[-3:],
            "stderr_tail": proc.stderr.strip().splitlines()[-3:],
        }
        command_results.append(result)
        checked("policy_command:" + argv[-1], proc.returncode == 0, result)

    portable = next(row for row in command_results if row["argv"][-1] == "portable")
    portable_payload = json.loads(portable["stdout_tail"][-1])
    pr_delta = (ROOT / "docs/PR_DELTAS/pr-289.md").read_text()
    old_portable_hash = "2b1bdb16a40aa65553d43e8764eccd11819b2f779f7ed15c49105678b121a3d6"
    notes = []
    if old_portable_hash in pr_delta and portable_payload["source_tracked_manifest_sha256"] != old_portable_hash:
        notes.append({
            "severity": "low",
            "statement": "PR delta labels a pre-finalization portable manifest hash as current; fresh portable replay passes with the sealed tree's different manifest hash.",
            "recorded_hash": old_portable_hash,
            "fresh_hash": portable_payload["source_tracked_manifest_sha256"],
            "acceptance_effect": "nonblocking because the exact fresh policy command passed and source/archive pre/post identities agree",
        })

    report = {
        "schema": "htt.pr289.frozen_independent_oracle.v1",
        "run_id": RUN_ID,
        "assignment_id": ASSIGNMENT_ID,
        "candidate_sha": CANDIDATE,
        "candidate_tree_sha": TREE,
        "status": "PASS",
        "checks": checks,
        "policy_commands": command_results,
        "notes": notes,
    }
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "checks": len(checks),
        "policy_commands": len(command_results),
        "notes": len(notes),
        "output": str(output.resolve().relative_to(ROOT)),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
