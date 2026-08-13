#!/usr/bin/env python3
"""Independent frozen-candidate invariant oracle for A-PR287-FROZEN-REPLAY-R3.

The oracle reads only the assignment's named inputs, the authoritative salvage
audit, and modules imported by the registered runner/test command.  Git use is
limited to rev-parse, diff, patch-id, and status.
"""

from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys

import yaml


ROOT = Path(__file__).resolve().parents[5]
RUN_ID = "pr287-fresh-independent-review-20260811"
ASSIGNMENT_ID = "A-PR287-FROZEN-REPLAY-R3"
BASE = "b955a050f19db853a93779506e8acb4e4a5352a9"
CANDIDATE = "06ee728054fd62423fa90bc6a5d714b9be8631e3"
TREE = "dd909b5d35a385b251547f6224b657346d7688f6"
TARGET_REF = "refs/remotes/origin/changeset/pr286-pillar-s-adjudication-recovery-20260810"
CANDIDATE_REF = "refs/heads/changeset/pr287-entropy-truth-recovery-20260811"
BLOCKER = "BLOCKED_CAPABILITY_ISOLATED_EXECUTOR_NOT_INSTALLED"
COMMITS = (
    "858091c113ea3ae4516cdfa6a6f8b8b167e14dc8",
    "eecf46cd7f911365ec278fadaaf1dabebe749265",
    "785895e939f472d625c327ab719fe2eae75c0fa1",
    "2ef6330da4a9a5564c8aa321e97a6ee4460e600c",
    CANDIDATE,
)
PATCH_IDS = (
    "1be41957cd4ee016277cb334c491aed4afc9c26c",
    "e8fec5909e1d136232d3238a29df0d0bf882d844",
    "8aefd21b4dfebceb3d3e8f48db6b14566e8a9d6f",
    "8dd4760adec48c969321486fd951f44fcac055e4",
    "54b3371720a7154778193d2cc8a94724d8b06899",
)
EXPECTED_INPUTS = {
    ".prguard/runtime/PR287_VALIDATED_CANDIDATE_SEAL.json": "fbe4787a82f650ec050fab020ae2c9545e9f7fe778ec2d6f5d4550470537712b",
    "docs/research_program/post_pr275/pr287_spec.yaml": "dbd0d6fe29a45e51a6850102ed4587ac38f8da7cfb52453552aa0a4ba704ac09",
    "docs/research_program/post_pr275/pr287_publication_policy.json": "30e24d1f9e77c5c206a64e7d8b639cfccd4c6bd9455a6893cbc69ae55ea1d155",
    "docs/PR_DELTAS/pr-287.md": "2071fb8c93006c1f7c79fa36a99bf2611db30dcc8ff2db7b632eec9feda33737",
    "docs/codex_handoff/pr_status.yaml": "1c6785cd22cf284ed6aebcb74e0acd9c0313f2072acac0c76677d2ee7679bf57",
    "machine_readable/pr_status.yaml": "1c6785cd22cf284ed6aebcb74e0acd9c0313f2072acac0c76677d2ee7679bf57",
    "scripts/codex_harness/run_pr287_post275_blind_replay.py": "23c46e3f55cf384ecee6f8409919e233df8c4ed8edcf695257f3573a4fa01a7c",
    "scripts/codex_harness/validate_pr_dag.py": "126ccf63e3a6d835584426e4c3d157be5482b1f7df39d0985638370366b40afc",
    "tests/integration/test_post275_blind_replay.py": "9a659feb3f5f00eabe42a9da4ee5fc7c8345b46e3c8e30cbe548baf17ba7e02b",
    "htt/src/common/post275_blind_replay.py": "95d458f939b7ff377e0810a288aaff1da7c254c69f0b836da0dcc61d95e30652",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_sha(value: object) -> str:
    return sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
    )


def git(*argv: str, binary: bool = False) -> bytes | str:
    completed = subprocess.run(
        ["git", *argv], cwd=ROOT, check=True, capture_output=True
    )
    return completed.stdout if binary else completed.stdout.decode().strip()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def changed_files() -> list[dict[str, str]]:
    raw = git(
        "diff", "--name-status", "--no-renames", "-z", f"{BASE}..{CANDIDATE}",
        binary=True,
    )
    assert isinstance(raw, bytes)
    parts = [item for item in raw.split(b"\0") if item]
    require(len(parts) % 2 == 0, "malformed changed-file inventory")
    return [
        {
            "status": parts[index].decode("ascii"),
            "path": parts[index + 1].decode("utf-8"),
        }
        for index in range(0, len(parts), 2)
    ]


def category(path: str) -> str:
    parts = Path(path).parts
    lowered = path.lower()
    name = Path(path).name.lower()
    if (
        path.startswith(".agent-harness/runs/")
        or path.startswith(".prguard/runtime/")
        or path.startswith("docs/PR_DELTAS/")
        or any(token in name for token in ("receipt", "seal", "review_envelope"))
    ):
        return "receipts"
    if path.startswith(("docs/generated/", "figures/generated/", ".agent-harness/generated/")):
        return "generated"
    if path.startswith("tests/") or "tests" in parts or name.startswith("test_") or name.endswith("_test.py"):
        return "tests"
    if (
        path.startswith(("scripts/", ".agent-harness/", "docs/codex_handoff/", "machine_readable/", "docs/research_program/"))
        or path in {"AGENTS.md", "AGENTS.md.fragment"}
        or lowered.endswith(("_policy.json", "_spec.yaml"))
    ):
        return "runners"
    return "production"


def module_origin_check(module_name: str, relative: str, symbol: str) -> str:
    expected = (ROOT / relative).resolve()
    module = importlib.import_module(module_name)
    function = getattr(module, symbol)
    spec = module.__spec__
    loader = spec.loader if spec else None
    origins = (
        Path(module.__file__).resolve(),
        Path(spec.origin).resolve(),
        Path(loader.path).resolve(),
        Path(function.__code__.co_filename).resolve(),
    )
    require(all(item == expected for item in origins), f"module origin drift: {module_name}")
    return sha256(expected.read_bytes())


def main() -> int:
    checks: list[str] = []
    for relative, expected in EXPECTED_INPUTS.items():
        require(sha256((ROOT / relative).read_bytes()) == expected, f"input hash drift: {relative}")
    checks.append("ten_required_input_hashes")

    seal = json.loads((ROOT / ".prguard/runtime/PR287_VALIDATED_CANDIDATE_SEAL.json").read_text())
    unsigned = dict(seal)
    internal = unsigned.pop("seal_sha256")
    require(canonical_sha(unsigned) == internal, "candidate seal checksum drift")
    require(seal["candidate_sha"] == CANDIDATE and seal["base_sha"] == BASE, "seal SHA drift")
    require(seal["candidate_tree_sha"] == TREE, "seal tree drift")
    checks.append("candidate_seal_self_hash")

    require(git("rev-parse", "HEAD") == CANDIDATE, "HEAD drift")
    require(git("rev-parse", "--verify", CANDIDATE_REF) == CANDIDATE, "candidate ref drift")
    require(git("rev-parse", "--verify", TARGET_REF) == BASE, "target ref drift")
    require(git("rev-parse", f"{CANDIDATE}^{{tree}}") == TREE, "candidate tree drift")
    require(git("status", "--porcelain=v1") == "", "candidate worktree is dirty")
    checks.append("head_target_tree_and_clean_status")

    previous = BASE
    computed_patch_ids: list[dict[str, str]] = []
    for commit, expected_patch_id in zip(COMMITS, PATCH_IDS, strict=True):
        require(git("rev-parse", f"{commit}^") == previous, f"nonlinear candidate chain: {commit}")
        diff = subprocess.run(
            ["git", "diff", f"{commit}^", commit], cwd=ROOT, check=True, capture_output=True
        )
        patch = subprocess.run(
            ["git", "patch-id", "--stable"], cwd=ROOT, input=diff.stdout, check=True, capture_output=True
        ).stdout.decode().split()[0]
        require(patch == expected_patch_id, f"stable patch ID drift: {commit}")
        computed_patch_ids.append({"commit": commit, "stable_patch_id": patch})
        previous = commit
    require(len(set(PATCH_IDS)) == len(PATCH_IDS), "duplicate candidate patch ID")
    require(computed_patch_ids == seal["stable_patch_ids"], "sealed patch inventory drift")
    require(canonical_sha({"stable_patch_ids": computed_patch_ids}) == seal["stable_patch_ids_sha256"], "patch inventory hash drift")
    require(canonical_sha({"commits": list(COMMITS)}) == seal["candidate_commits_sha256"], "commit inventory hash drift")
    checks.append("linear_unique_stable_patch_inventory")

    diff = git(
        "diff", "--binary", "--full-index", "--no-color", "--no-ext-diff",
        "--no-textconv", "--no-renames", "--submodule=short", f"{BASE}..{CANDIDATE}",
        binary=True,
    )
    assert isinstance(diff, bytes)
    require(sha256(diff) == seal["diff_sha256"], "candidate diff hash drift")
    files = changed_files()
    require(files == seal["changed_files"], "changed-file inventory drift")
    require(canonical_sha({"changed_files": files}) == seal["changed_files_sha256"], "changed-file hash drift")
    counts = {key: 0 for key in ("production", "tests", "runners", "receipts", "generated")}
    production_rows = []
    for row in files:
        kind = category(row["path"])
        counts[kind] += 1
        if kind == "production":
            production_rows.append({
                "path": row["path"], "status": row["status"],
                "blob_sha256": None if row["status"] == "D" else sha256((ROOT / row["path"]).read_bytes()),
            })
    require(counts == seal["diff_stat"], "diff category counts drift")
    require(canonical_sha({"files": production_rows}) == seal["production_hash"], "production hash drift")
    checks.append("diff_changed_files_and_production_hash")

    canonical_status_bytes = (ROOT / "docs/codex_handoff/pr_status.yaml").read_bytes()
    require(canonical_status_bytes == (ROOT / "machine_readable/pr_status.yaml").read_bytes(), "status mirror drift")
    status = yaml.safe_load(canonical_status_bytes)
    stack = status["stacked_pr_execution"]
    require(stack["execution_mode"] == "AUTO_STACKED_PR", "stack mode drift")
    require(stack["active_implementation_pr"] == "PR-287", "active PR drift")
    required_heads = {
        "PR-283": ("ff9ef9f45747e559c5343b463cf010dfc3a7432a", "b6b6952d52f59bbe05477ef3b02292a98fe92baa"),
        "PR-284": ("b6b6952d52f59bbe05477ef3b02292a98fe92baa", "0b3680a03f325e3f1fa1699528a5a59303ddb8b4"),
        "PR-285": ("0b3680a03f325e3f1fa1699528a5a59303ddb8b4", "16bc6db511b8b7228e5c4dcb95c65074fe519f24"),
        "PR-286": ("16bc6db511b8b7228e5c4dcb95c65074fe519f24", BASE),
    }
    for pr_id, (expected_base, expected_head) in required_heads.items():
        row = stack["prs"][pr_id]
        require(row["base_sha"] == expected_base and row["sealed_head"] == expected_head, f"{pr_id} chain drift")
        require(row["lifecycle"] == "PR_OPEN" and row["gate_dispositions"]["review"] == "PASS", f"{pr_id} lifecycle drift")
        resolution = status["execution_resolutions"][pr_id]
        require(resolution["resolution"] == "COMPLETED_SUCCESS" and resolution["success_dependency_satisfied"] is True, f"{pr_id} resolution drift")
    current = stack["prs"]["PR-287"]
    require(current["base_sha"] == BASE and current["predecessor_sealed_sha"] == BASE, "PR-287 base drift")
    require(current["lifecycle"] == "VALIDATED" and current["execution_blocker"] == BLOCKER, "PR-287 typed blocker drift")
    checks.append("status_mirror_and_exact_pr_open_chain")

    scripts = ROOT / ".agent-harness/scripts"
    sys.path.insert(0, str(scripts))
    harness_hashes = {
        "publication_integrity": module_origin_check("publication_integrity", ".agent-harness/scripts/publication_integrity.py", "load_publication_policy"),
        "profile_registry": module_origin_check("profile_registry", ".agent-harness/scripts/profile_registry.py", "load_profile_registry"),
        "harness_kernel": module_origin_check("_harness", ".agent-harness/scripts/_harness.py", "validate_run_plan_payload"),
        "strict_result_validation": module_origin_check("strict_result_validation", ".agent-harness/scripts/strict_result_validation.py", "load_and_validate_registered_result_file"),
    }
    dependencies = current["dependency_hashes"]
    require(all(dependencies[key] == value for key, value in harness_hashes.items()), "transitive harness byte binding drift")
    sys.path.insert(0, str(ROOT / "htt"))
    sys.path.insert(0, str(ROOT / "htt/src"))
    module_origin_check("common.post275_blind_replay", "htt/src/common/post275_blind_replay.py", "build_common_pack_a")
    module_origin_check("htt.infer.post275_blind_replay", "htt/htt/htt/infer/post275_blind_replay.py", "build_htt_pack_b")
    module_origin_check("mio.reports.post275_blind_replay", "htt/mio/reports/post275_blind_replay.py", "build_mio_pack_c")
    checks.append("transitive_harness_and_owner_factory_origin")

    spec = yaml.safe_load((ROOT / "docs/research_program/post_pr275/pr287_spec.yaml").read_text())
    policy = json.loads((ROOT / "docs/research_program/post_pr275/pr287_publication_policy.json").read_text())
    runner = (ROOT / "scripts/codex_harness/run_pr287_post275_blind_replay.py").read_text()
    require(spec["fresh_artifact_contracts"]["analyst_executor_status"] == BLOCKER, "spec blocker drift")
    require(spec["fresh_artifact_contracts"]["execution_disposition"] == "INCONCLUSIVE", "spec disposition drift")
    require(BLOCKER in runner and "_assert_no_fresh_outputs" in runner, "runner blocker containment drift")
    require(len(policy["required_commands"]) == 8 and len(policy["required_review_cells"]) == 30, "policy inventory drift")
    checks.append("typed_executor_blocker_and_policy_inventory")

    audit = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base/HTT_PROCESS_INFLATION_SALVAGE_AUDIT_20260810.md").read_text()
    delta = (ROOT / "docs/PR_DELTAS/pr-287.md").read_text()
    for token in ("G28, **G29(2d8 lineage)**, G31~G37", "G30,G38, old dirty overlay"):
        require(token in audit, f"authoritative salvage token missing: {token}")
    require("2d8bcfe3568eebecae1eb7c52cfc4dc22ea951ad" in delta, "reviewed G29 provenance missing")
    require("G30, G38, duplicate aliases, and the old dirty overlay are also\nexcluded" in delta, "excluded-lineage statement drift")
    checks.append("authorized_lineage_inclusion_and_exclusion")

    print(json.dumps({
        "schema": "PR287_FROZEN_REPLAY_INVARIANT_ORACLE_V1",
        "run_id": RUN_ID,
        "assignment_id": ASSIGNMENT_ID,
        "candidate_sha": CANDIDATE,
        "base_sha": BASE,
        "status": "PASS",
        "checks": checks,
        "check_count": len(checks),
        "stable_patch_ids": list(PATCH_IDS),
        "execution_disposition": "INCONCLUSIVE",
        "execution_blocker": BLOCKER,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
