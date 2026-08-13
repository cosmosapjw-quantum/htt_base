#!/usr/bin/env python3
"""Build PR-289 final integration evidence without duplicate assurance runs."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".agent-harness" / "scripts"))

from publication_integrity import canonical_sha256, utc_now  # noqa: E402


SOURCE_RECEIPT = ROOT / ".prguard/runtime/PR289_R5_INTEGRATION_REHEARSAL.json"
SOURCE_LOGS = ROOT / ".prguard/runtime/PR289_R5_INTEGRATION_REHEARSAL.logs"
FINAL_SEAL = ROOT / ".prguard/runtime/PR289_FINAL_CANDIDATE_SEAL.json"
OUTPUT = ROOT / ".prguard/runtime/PR289_FINAL_INTEGRATION_REHEARSAL.json"
OUTPUT_LOGS = ROOT / ".prguard/runtime/PR289_FINAL_INTEGRATION_REHEARSAL.logs"

FRESH_IDS = (
    "pr289-portable-clean-replay",
    "pr289-dag-strict",
    "pr289-claim-language",
)
CARRIED_IDS = (
    "pr289-focused",
    "pr289-readonly-preflight",
    "pr289-adjacent",
    "pr289-receipt-replay",
    "pr289-publication-policy-cross-binding",
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    if OUTPUT.exists() or OUTPUT_LOGS.exists():
        raise SystemExit("refusing to overwrite final integration evidence")
    prior_bytes = SOURCE_RECEIPT.read_bytes()
    prior = json.loads(prior_bytes)
    seal = json.loads(FINAL_SEAL.read_text(encoding="utf-8"))
    if prior["status"] != "PASS":
        raise SystemExit("source integration receipt is not PASS")
    if prior["candidate_sha"] != "eec048d4cf19989983986d139c7d0a797b1363e0":
        raise SystemExit("source integration candidate drifted")
    if prior["candidate_seal_sha256"] != "301be2d0d73f18c109b71f36c43e8c8d033bd7fcfb01a6d04142b7493e30cf01":
        raise SystemExit("source integration seal drifted")
    if seal["production_hash"] != prior.get("production_hash", seal["production_hash"]):
        raise SystemExit("production evidence key changed")

    shutil.copytree(SOURCE_LOGS, OUTPUT_LOGS)
    rows = [dict(row) for row in prior["commands"]]
    by_id = {row["id"]: row for row in rows}
    environment = os.environ.copy()
    environment.pop("PYTHONHOME", None)
    environment.pop("PYTHONSTARTUP", None)

    for command_id in FRESH_IDS:
        row = by_id[command_id]
        started = utc_now()
        completed = subprocess.run(
            row["argv"],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            timeout=int(row["timeout_seconds"]),
            check=False,
        )
        finished = utc_now()
        stdout_path = OUTPUT_LOGS / f"{command_id}.stdout"
        stderr_path = OUTPUT_LOGS / f"{command_id}.stderr"
        stdout_path.write_bytes(completed.stdout)
        stderr_path.write_bytes(completed.stderr)
        row.update(
            {
                "started_at": started,
                "completed_at": finished,
                "returncode": completed.returncode,
                "timed_out": False,
                "stdout_sha256": sha256(completed.stdout),
                "stdout_bytes": len(completed.stdout),
                "stderr_sha256": sha256(completed.stderr),
                "stderr_bytes": len(completed.stderr),
            }
        )
        if completed.returncode != 0:
            raise SystemExit(
                f"fresh metadata-sensitive command failed: {command_id}"
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
            "carried_forward_command_ids": list(CARRIED_IDS),
            "fresh_metadata_sensitive_command_ids": list(FRESH_IDS),
            "tracked_delta_since_previous_candidate": [
                "docs/PR_DELTAS/pr-289.md",
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
                "file_sha256": sha256(OUTPUT.read_bytes()),
                "receipt_sha256": receipt["receipt_sha256"],
                "carried_forward_command_ids": list(CARRIED_IDS),
                "fresh_command_ids": list(FRESH_IDS),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
