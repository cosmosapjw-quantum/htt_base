#!/usr/bin/env python3
"""Merge result envelopes into MERGED_RESULTS.json.

PR-124 preflight (audit H6/H7):

- The dedup key is the NORMATIVE `(claim_id, evidence_fingerprint, verdict)`
  from AGENTS.md §5 — `evidence_refs` no longer participates, so the same
  finding cited through different refs merges into one row whose
  `evidence_refs` is the sorted union.
- Opposite verdicts on the same `(claim_id, evidence_fingerprint)` are
  emitted as a `conflicts` object and fail the merge (exit nonzero); there
  is no majority-vote path.
- Findings already resolved in the cross-run ledger
  (`.agent-harness/ledger/FINDING_LEDGER.jsonl`) are annotated
  `previously_resolved` with their resolution commit instead of being
  re-raised as new work.
"""
from __future__ import annotations

import json
from collections import defaultdict

from _harness import (
    cli_active_run_id,
    dump_json,
    load_json,
    root,
    utc_now,
    validate_assignment_payload,
    validate_result_payload,
)


def canonical_key(finding: dict) -> tuple:
    fingerprint = str(finding.get("evidence_fingerprint", ""))
    if not fingerprint:
        # Validation rejects this for independent results.  Retain the finding
        # ID in the fallback key anyway so malformed inputs cannot collapse.
        fingerprint = f"missing:{finding.get('finding_id', '')}"
    return (
        str(finding.get("claim_id", "")),
        fingerprint,
        str(finding.get("verdict", "")),
    )


def load_finding_ledger(repo) -> dict[tuple, str]:
    """Return {(claim_id, fingerprint, verdict): resolution_commit}."""

    path = repo / ".agent-harness" / "ledger" / "FINDING_LEDGER.jsonl"
    resolved: dict[tuple, str] = {}
    if not path.is_file():
        return resolved
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        commit = row.get("resolution_commit")
        if not commit:
            continue
        resolved[
            (
                str(row.get("claim_id", "")),
                str(row.get("evidence_fingerprint", "")),
                str(row.get("verdict", "")),
            )
        ] = str(commit)
    return resolved


def main() -> None:
    repo = root()
    run_id = cli_active_run_id(repo)
    assert run_id is not None
    run_dir = repo / ".agent-harness" / "runs" / run_id
    plan = load_json(run_dir / "RUN_PLAN.json")
    context_version = str(plan.get("context_version", ""))
    assignments = {
        path.stem: load_json(path)
        for path in sorted((run_dir / "assignments").glob("*.json"))
    }
    results = []
    errors = []
    for path in sorted((run_dir / "results").glob("*.json")):
        try:
            value = load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append({"path": str(path.relative_to(repo)), "error": str(exc)})
            continue
        assignment_id = value.get("assignment_id") if isinstance(value, dict) else None
        assignment = assignments.get(str(assignment_id))
        if assignment is None:
            errors.append(
                {"path": str(path.relative_to(repo)), "error": "unregistered result"}
            )
            continue
        validation_errors = validate_assignment_payload(
            assignment,
            run_id=run_id,
            context_version=context_version,
            assignment_id=str(assignment_id),
        ) + validate_result_payload(
            value,
            assignment,
            run_id=run_id,
            context_version=context_version,
        )
        if validation_errors:
            errors.append(
                {
                    "path": str(path.relative_to(repo)),
                    "error": "; ".join(validation_errors),
                }
            )
            continue
        if assignment.get("independence_mode") == "adjudication":
            continue
        results.append(value)

    groups: dict[tuple, list[dict]] = defaultdict(list)
    for result in results:
        for finding in result.get("findings", []):
            groups[canonical_key(finding)].append(
                {
                    "assignment_id": result.get("assignment_id"),
                    "agent_type": result.get("agent_type"),
                    "finding": finding,
                }
            )

    ledger = load_finding_ledger(repo)
    merged = []
    for key, items in groups.items():
        representative = dict(items[0]["finding"])
        refs = sorted(
            {
                str(ref)
                for item in items
                for ref in item["finding"].get("evidence_refs", [])
            }
        )
        representative["evidence_refs"] = refs
        representative["source_finding_ids"] = [
            item["finding"].get("finding_id") for item in items
        ]
        representative["supporting_assignments"] = [
            item["assignment_id"] for item in items
        ]
        representative["supporting_agent_types"] = [
            item["agent_type"] for item in items
        ]
        representative["duplicate_count"] = len(items)
        resolution = ledger.get(key)
        if resolution is not None:
            representative["previously_resolved"] = {
                "resolution_commit": resolution,
                "note": "already resolved in FINDING_LEDGER; verify the fix "
                "still holds instead of re-raising",
            }
        merged.append(representative)

    # Opposite verdicts on identical evidence auto-conflict (no majority).
    verdict_groups: dict[tuple, set[str]] = defaultdict(set)
    conflict_members: dict[tuple, list[dict]] = defaultdict(list)
    for result in results:
        for finding in result.get("findings", []):
            fingerprint = str(finding.get("evidence_fingerprint", ""))
            if not fingerprint:
                continue
            pair = (str(finding.get("claim_id", "")), fingerprint)
            verdict_groups[pair].add(str(finding.get("verdict", "")))
            conflict_members[pair].append(
                {
                    "assignment_id": result.get("assignment_id"),
                    "finding_id": finding.get("finding_id"),
                    "verdict": finding.get("verdict"),
                }
            )
    conflicts = [
        {
            "claim_id": pair[0],
            "evidence_fingerprint": pair[1],
            "verdicts": sorted(verdicts),
            "members": conflict_members[pair],
        }
        for pair, verdicts in sorted(verdict_groups.items())
        if len(verdicts) > 1
    ]

    output = {
        "schema_version": 1,
        "run_id": run_id,
        "generated_at": utc_now(),
        "result_count": len(results),
        "raw_finding_count": sum(len(result.get("findings", [])) for result in results),
        "unique_finding_count": len(merged),
        "findings": merged,
        "conflicts": conflicts,
        "errors": errors,
    }
    out = run_dir / "MERGED_RESULTS.json"
    dump_json(out, output)
    print(out.relative_to(repo))
    if errors:
        raise SystemExit("result merge rejected invalid envelopes")
    if conflicts:
        raise SystemExit(
            "verdict conflict on identical evidence — adjudicate with a "
            "minimal counterexample (majority vote is forbidden)"
        )


if __name__ == "__main__":
    main()
