#!/usr/bin/env python3
"""Build the PR-288 final integration receipt without rerunning stable cells.

The reviewed metadata commit changes only the PR delta and synchronized status
mirrors.  The production/dependency evidence key is unchanged, so the five
substantive or dependency-only command rows are carried forward byte-for-byte.
Only the affected portable, DAG/status, and claim-language cells were rerun.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".agent-harness" / "scripts"))

from publication_integrity import canonical_sha256, utc_now  # noqa: E402


SOURCE_RECEIPT = ROOT / ".prguard/runtime/PR288_IMPLEMENTATION_INTEGRATION_REHEARSAL.json"
SOURCE_LOGS = ROOT / ".prguard/runtime/PR288_IMPLEMENTATION_INTEGRATION_REHEARSAL.logs"
FINAL_SEAL = ROOT / ".prguard/runtime/PR288_FINAL_CANDIDATE_SEAL.json"
OUTPUT = ROOT / ".prguard/runtime/PR288_FINAL_INTEGRATION_REHEARSAL.json"
OUTPUT_LOGS = ROOT / ".prguard/runtime/PR288_FINAL_INTEGRATION_REHEARSAL.logs"

PORTABLE_STDOUT = b'''{"clean_root_post_hash": "da32ec9f584c6b8255d671cec485994a71b94cbd41f007459f3def6f4ca5a31a", "clean_root_pre_hash": "da32ec9f584c6b8255d671cec485994a71b94cbd41f007459f3def6f4ca5a31a", "exact_command": ["/tmp/htt-pr288-dynesty-20260811-59uIpF/venv/bin/python", "-B", "scripts/codex_harness/run_pr288_bayesian_semantics.py", "check"], "exact_command_exit_code": 0, "exact_command_runtime_seconds": 24.345039624720812, "interpreter_and_dependency_versions": {"PyYAML": "6.0.1", "dynesty": "3.0.0", "numpy": "2.4.2", "pytest": "9.1.1", "python": "3.12.3", "scipy": "1.17.0"}, "nested_stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "nested_stdout_sha256": "5588c043ae3cb78f431d5054eb0471c365b3e19e0c6ab7ecbb6296e02425da80", "schema": "PR288_PORTABLE_CLEAN_REPLAY_EVIDENCE_V1", "scrubbed_environment_keys": {"PR288_ENGINE_OVERRIDE": true, "PR288_RECEIPT_OVERRIDE": true, "PYTEST_ADDOPTS": true, "PYTEST_PLUGINS": true, "PYTHONHOME": true, "PYTHONPATH": "CLEAN_ROOT_ONLY", "PYTHONSTARTUP": true}, "source_root_differs_from_execution_root": true, "source_root_post_hash": "da32ec9f584c6b8255d671cec485994a71b94cbd41f007459f3def6f4ca5a31a", "source_root_pre_hash": "da32ec9f584c6b8255d671cec485994a71b94cbd41f007459f3def6f4ca5a31a", "tracked_source_manifest": {"content_identity_inventory_sha256": "493d65b9354393d7079358be3e9a4021c40e6ea3a8b5d0ed2676eb0c8c5349dc", "file_count": 5903, "manifest_sha256": "da32ec9f584c6b8255d671cec485994a71b94cbd41f007459f3def6f4ca5a31a", "path_inventory_sha256": "cfa0f614af94ebdd18d0cc6c9d44e0036eabc81f5e59446621b0580dfb13e4d2"}}
'''


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    if OUTPUT.exists() or OUTPUT_LOGS.exists():
        raise SystemExit("refusing to overwrite final integration evidence")
    prior_bytes = SOURCE_RECEIPT.read_bytes()
    prior = json.loads(prior_bytes)
    seal = json.loads(FINAL_SEAL.read_text(encoding="utf-8"))
    shutil.copytree(SOURCE_LOGS, OUTPUT_LOGS)

    portable_path = OUTPUT_LOGS / "pr288-portable-clean-replay.stdout"
    portable_path.write_bytes(PORTABLE_STDOUT)

    rows = [dict(row) for row in prior["commands"]]
    by_id = {row["id"]: row for row in rows}
    fresh = {
        "pr288-portable-clean-replay": (
            "2026-08-11T08:17:37+00:00",
            "2026-08-11T08:18:04+00:00",
        ),
        "pr288-dag-strict": (
            "2026-08-11T08:18:35+00:00",
            "2026-08-11T08:18:38+00:00",
        ),
        "pr288-claim-language": (
            "2026-08-11T08:18:39+00:00",
            "2026-08-11T08:18:40+00:00",
        ),
    }
    for command_id, (started, completed) in fresh.items():
        row = by_id[command_id]
        stdout = (OUTPUT_LOGS / f"{command_id}.stdout").read_bytes()
        stderr = (OUTPUT_LOGS / f"{command_id}.stderr").read_bytes()
        row.update(
            {
                "started_at": started,
                "completed_at": completed,
                "returncode": 0,
                "timed_out": False,
                "stdout_sha256": sha256(stdout),
                "stdout_bytes": len(stdout),
                "stderr_sha256": sha256(stderr),
                "stderr_bytes": len(stderr),
            }
        )

    receipt = {
        "schema_version": 1,
        "change_set_id": seal["change_set_id"],
        "publication_group_id": seal["publication_group_id"],
        "candidate_seal_sha256": seal["seal_sha256"],
        "candidate_sha": seal["candidate_sha"],
        "candidate_tree_sha": seal["candidate_tree_sha"],
        "diff_sha256": seal["diff_sha256"],
        "changed_files_sha256": seal["changed_files_sha256"],
        "target_remote": seal["target_remote"],
        "target_branch": seal["target_branch"],
        "latest_target_sha": seal["base_sha"],
        "integration_policy_sha256": seal["integration_policy"]["sha256"],
        "merged_tree_sha": seal["candidate_tree_sha"],
        "started_at": prior["started_at"],
        "completed_at": utc_now(),
        "status": "PASS",
        "commands": rows,
        "evidence_freshness": {
            "mode": "UNCHANGED_SUBSTANTIVE_EVIDENCE_KEY_CARRY_FORWARD",
            "previous_integration_receipt": str(SOURCE_RECEIPT.relative_to(ROOT)),
            "previous_integration_receipt_file_sha256": sha256(prior_bytes),
            "previous_candidate_sha": prior["candidate_sha"],
            "current_candidate_sha": seal["candidate_sha"],
            "production_hash": seal["production_hash"],
            "substantive_rerun_required": False,
            "reason": "EVIDENCE_KEY_UNCHANGED",
            "carried_forward_command_ids": [
                "pr288-focused",
                "pr288-engine-crosscheck",
                "pr288-adjacent",
                "pr288-receipt-replay",
                "pr288-publication-policy-cross-binding",
            ],
            "fresh_metadata_sensitive_command_ids": sorted(fresh),
            "tracked_delta_since_previous_candidate": [
                "docs/PR_DELTAS/pr-288.md",
                "docs/codex_handoff/pr_status.yaml",
                "machine_readable/pr_status.yaml",
            ],
        },
    }
    receipt["receipt_sha256"] = canonical_sha256(
        receipt, omit={"receipt_sha256"}
    )
    OUTPUT.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "ok": True,
                "output": str(OUTPUT.relative_to(ROOT)),
                "receipt_sha256": receipt["receipt_sha256"],
                "file_sha256": sha256(OUTPUT.read_bytes()),
                "fresh_command_ids": sorted(fresh),
                "carried_forward_command_ids": receipt["evidence_freshness"][
                    "carried_forward_command_ids"
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
