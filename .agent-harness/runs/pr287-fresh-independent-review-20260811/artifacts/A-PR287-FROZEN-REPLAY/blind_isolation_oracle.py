#!/usr/bin/env python3
"""Emit a fail-closed receipt for a detected blind-results isolation breach."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "pr287-fresh-independent-review-20260811"
ASSIGNMENT_ID = "A-PR287-FROZEN-REPLAY"
CONTEXT_VERSION = "e9b385d7fbc4f8e47c97c3b0c7edae4e522d9be4e025d9342e26ab24829e3019"
ASSIGNMENT_PATH = f".agent-harness/runs/{RUN_ID}/assignments/{ASSIGNMENT_ID}.json"
SEAL_PATH = ".prguard/runtime/PR287_VALIDATED_CANDIDATE_SEAL.json"
POLICY_PATH = "docs/research_program/post_pr275/pr287_publication_policy.json"
INCIDENT = (
    "BLIND_RESULTS_ISOLATION_BREACH: a scoped process-status check for the "
    "assignment-local oracle unexpectedly exposed a live sibling PR-287 result "
    "path and gate_disposition=PASS write command before this reviewer submitted. "
    "The sibling result file was not opened, but sibling verdict metadata was "
    "visible, so no claim or acceptance verdict is issued."
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_sha256(value: dict[str, Any], *, omit: set[str] | None = None) -> str:
    payload = dict(value)
    for key in omit or set():
        payload.pop(key, None)
    return digest(
        json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
    )


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


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
    started_at = now()
    repo = Path.cwd().resolve()
    assignment = json.loads((repo / ASSIGNMENT_PATH).read_text(encoding="utf-8"))
    seal = json.loads((repo / SEAL_PATH).read_text(encoding="utf-8"))
    policy = json.loads((repo / POLICY_PATH).read_text(encoding="utf-8"))
    if assignment["context_version"] != CONTEXT_VERSION:
        raise SystemExit("assignment context drift")
    if assignment["candidate_binding"]["seal_sha256"] != seal["seal_sha256"]:
        raise SystemExit("candidate binding drift")
    if assignment["independence_mode"] != "blind-results":
        raise SystemExit("assignment independence mode drift")

    completed_at = now()
    report = {
        "schema_version": 1,
        "oracle_id": "PR287-BLIND-ISOLATION-BREACH-ORACLE",
        "run_id": RUN_ID,
        "assignment_id": ASSIGNMENT_ID,
        "context_version": CONTEXT_VERSION,
        "started_at": started_at,
        "completed_at": completed_at,
        "status": "PASS",
        "review_status": "ERROR",
        "acceptance_evidence": False,
        "claim_verdict_issued": False,
        "candidate_verdict_issued": False,
        "sibling_result_file_opened": False,
        "incident": INCIDENT,
        "containment": {
            "substantive_oracle_terminated": True,
            "tracked_or_shared_files_written": False,
            "replacement_blind_reviewer_required_for_acceptance": True,
        },
        "bindings": {
            "assignment_sha256": assignment["assignment_sha256"],
            "candidate_sha": seal["candidate_sha"],
            "candidate_seal_sha256": seal["seal_sha256"],
            "assignment_file_sha256": digest((repo / ASSIGNMENT_PATH).read_bytes()),
            "seal_file_sha256": digest((repo / SEAL_PATH).read_bytes()),
            "policy_file_sha256": digest((repo / POLICY_PATH).read_bytes()),
        },
    }
    output_rel = Path(args.output).as_posix()
    coverage_rel = Path(args.coverage_output).as_posix()
    output_path = repo / output_rel
    write_json(output_path, report)
    report_bytes = output_path.read_bytes()

    script_rel = Path(__file__).resolve().relative_to(repo).as_posix()
    argv = [
        str(Path(os.path.abspath(sys.executable))),
        "-B",
        script_rel,
        "--output",
        output_rel,
        "--coverage-output",
        coverage_rel,
    ]
    evidence = [output_rel, ASSIGNMENT_PATH, SEAL_PATH, POLICY_PATH]
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
        "correlated_review": True,
        "coverage_cells": [
            {
                "cell": cell,
                "status": "NOT_APPLICABLE",
                "evidence_refs": evidence,
                "rationale": (
                    "No acceptance verdict: sibling verdict metadata became visible "
                    "before submission, so the blind reviewer stopped fail-closed."
                ),
            }
            for cell in policy["required_review_cells"]
        ],
        "independent_oracles": [
            {
                "oracle_id": "PR287-BLIND-ISOLATION-BREACH-ORACLE",
                "kind": "invariant_checker",
                "status": "PASS",
                "argv": argv,
                "command_fingerprint": canonical_sha256({"argv": argv}),
                "returncode": 0,
                "timed_out": False,
                "started_at": started_at,
                "completed_at": completed_at,
                "artifact_path": output_rel,
                "artifact_sha256": digest(report_bytes),
                "artifact_bytes": len(report_bytes),
                "evidence_refs": evidence,
            }
        ],
    }
    coverage["coverage_sha256"] = canonical_sha256(
        coverage, omit={"coverage_sha256"}
    )
    write_json(repo / coverage_rel, coverage)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
