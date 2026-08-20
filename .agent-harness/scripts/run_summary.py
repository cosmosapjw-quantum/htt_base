#!/usr/bin/env python3
"""Emit a compact RUN_SUMMARY.json per run (audit retention policy).

Retention (PR-124 preflight): routine run directories are no longer
committed. Long-term evidence per run is this summary — one row per result
with `{path, sha256, bytes}` — plus any individually promoted load-bearing
artifact (CAS receipts, adjudications, decisive falsifiers) recorded in the
tracked `.agent-harness/runs/RETENTION_LEDGER.jsonl`. Raw logs and duplicate
envelopes are summarised here and then left uncommitted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from _harness import dump_json, load_json, root


def summarize_run(repo: Path, run_dir: Path, disposition: str) -> dict:
    plan_path = run_dir / "RUN_PLAN.json"
    plan = load_json(plan_path) if plan_path.is_file() else {}
    assignments = {
        path.stem: load_json(path)
        for path in sorted((run_dir / "assignments").glob("*.json"))
        if path.is_file()
    }
    results = []
    for path in sorted((run_dir / "results").glob("*.json")):
        data = path.read_bytes()
        try:
            payload = json.loads(data)
        except json.JSONDecodeError:
            payload = {}
        assignment = assignments.get(path.stem, {})
        results.append(
            {
                "assignment_id": path.stem,
                "agent_type": payload.get("agent_type")
                or assignment.get("agent_type"),
                "status": payload.get("status"),
                "gate_disposition": payload.get("gate_disposition"),
                "path": path.relative_to(repo).as_posix(),
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
            }
        )
    merged_path = run_dir / "MERGED_RESULTS.json"
    merged = None
    if merged_path.is_file():
        data = merged_path.read_bytes()
        merged = {
            "path": merged_path.relative_to(repo).as_posix(),
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
        }
    return {
        "schema_version": 1,
        "run_id": run_dir.name,
        "work_unit_id": plan.get("work_unit_id"),
        "change_set_id": plan.get("change_set_id"),
        "publication_group_id": plan.get("publication_group_id"),
        "created_at": plan.get("created_at"),
        "context_version": plan.get("context_version"),
        "candidate_binding": plan.get("candidate_binding"),
        "execution_mode": plan.get("execution_mode"),
        "lifecycle_state": plan.get("lifecycle_state"),
        "evidence_key": plan.get("evidence_key"),
        "assurance_budget": plan.get("assurance_budget"),
        "publication_mode": plan.get("publication_mode"),
        "github_pr_created_by_harness": plan.get(
            "github_pr_created_by_harness", False
        ),
        "publication_state": "NOT_PUBLISHED_BY_HARNESS",
        "assignment_count": len(assignments),
        "results": results,
        "merged_results": merged,
        "disposition": disposition,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run-id")
    group.add_argument("--all", action="store_true")
    parser.add_argument(
        "--disposition",
        default="active",
        help="e.g. active | historical_frozen | summarized_discardable",
    )
    args = parser.parse_args()

    repo = root()
    runs = repo / ".agent-harness" / "runs"
    targets = (
        sorted(p for p in runs.iterdir() if p.is_dir())
        if args.all
        else [runs / args.run_id]
    )
    for run_dir in targets:
        if not run_dir.is_dir():
            raise SystemExit(f"Run does not exist: {run_dir.name}")
        summary = summarize_run(repo, run_dir, args.disposition)
        out = run_dir / "RUN_SUMMARY.json"
        dump_json(out, summary)
        print(out.relative_to(repo))


if __name__ == "__main__":
    main()
