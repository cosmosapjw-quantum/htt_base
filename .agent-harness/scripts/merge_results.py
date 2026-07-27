#!/usr/bin/env python3
"""Merge result envelopes into MERGED_RESULTS.json.

PR-124 preflight (audit H6/H7):

- The dedup key is `(claim_id, evidence_fingerprint, verdict)`;
  `evidence_refs` is the sorted union. Statement text is explanatory prose,
  not identity.
- `evidence_fingerprint` identifies the scoped finding/proposition, not merely
  a source. Opposite verdicts on the same `(claim_id, evidence_fingerprint)`
  are emitted as a `conflicts` object and fail the merge (exit nonzero); a
  paraphrase cannot launder a conflict and there is no majority-vote path.
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
    declared_result_path,
    dump_json,
    historical_run_ids,
    load_json,
    root,
    run_merge_input_manifest,
    run_merge_input_sha256,
    utc_now,
    validate_assignment_payload,
)
from strict_result_validation import load_and_validate_registered_result_file


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


def ledger_key(finding: dict) -> tuple:
    """Return the cross-run identity; prose is deliberately not identity."""

    return (
        str(finding.get("claim_id", "")),
        str(finding.get("evidence_fingerprint", "")),
        str(finding.get("verdict", "")),
    )


def load_finding_ledger(repo) -> dict[tuple, str]:
    """Return resolved finding keys mapped to resolution commits."""

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
        claim_id = str(row.get("claim_id", ""))
        if claim_id.startswith("RUN-"):
            continue
        resolved[
            (
                claim_id,
                str(row.get("evidence_fingerprint", "")),
                str(row.get("verdict", "")),
            )
        ] = str(commit)
    return resolved


def main() -> None:
    repo = root()
    run_id = cli_active_run_id(repo)
    assert run_id is not None
    if run_id in historical_run_ids(repo):
        raise SystemExit(
            "historical schema-v1 runs are read-only; merge replay must not rewrite them"
        )
    run_dir = repo / ".agent-harness" / "runs" / run_id
    plan = load_json(run_dir / "RUN_PLAN.json")
    index = load_json(repo / ".agent-harness" / "context" / "CONTEXT_INDEX.json")
    context_version = str(index.get("context_version", ""))
    results = []
    errors = []
    assignments = {}
    for path in sorted((run_dir / "assignments").glob("*.json")):
        relative = str(path.relative_to(repo))
        if path.is_symlink() or not path.is_file():
            errors.append(
                {"path": relative, "error": "assignment is not a regular file"}
            )
            continue
        try:
            assignment = load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append({"path": relative, "error": f"invalid assignment JSON: {exc}"})
            continue
        if not isinstance(assignment, dict):
            errors.append(
                {"path": relative, "error": "assignment is not a JSON object"}
            )
            continue
        assignment_errors = validate_assignment_payload(
            assignment,
            run_id=run_id,
            context_version=context_version,
            assignment_id=path.stem,
            repo=repo,
        )
        errors.extend(
            {"path": relative, "error": error} for error in assignment_errors
        )
        assignments[path.stem] = assignment
    valid_assignment_ids: set[str] = set()
    result_dispositions = []
    if plan.get("context_version") != context_version:
        errors.append(
            {
                "path": str((run_dir / "RUN_PLAN.json").relative_to(repo)),
                "error": "active run context_version is stale",
            }
        )
    for path in sorted((run_dir / "results").glob("*.json")):
        validation = load_and_validate_registered_result_file(
            repo,
            path,
            run_id=run_id,
            context_version=context_version,
        )
        if validation.errors:
            errors.append(
                {
                    "path": str(path.relative_to(repo)),
                    "error": "; ".join(validation.errors),
                }
            )
            continue
        value = validation.result
        assignment = validation.assignment
        assert value is not None and assignment is not None
        assignment_id = str(assignment.get("assignment_id"))
        valid_assignment_ids.add(assignment_id)
        result_dispositions.append(
            {
                "assignment_id": assignment_id,
                "status": value.get("status"),
                "claim_results": value.get("claim_results", []),
                "reported_errors": value.get("errors", []),
                "launch_evidence": validation.launch_evidence,
                "files_read_evidence": value.get("files_read_evidence"),
                "execution_evidence": value.get("execution_evidence"),
            }
        )
        if assignment.get("independence_mode") == "adjudication":
            continue
        results.append(value)

    for assignment_id in assignments:
        if assignment_id not in valid_assignment_ids:
            expected = repo / declared_result_path(run_id, assignment_id)
            if not expected.is_file():
                errors.append(
                    {
                        "path": str(expected.relative_to(repo)),
                        "error": "registered assignment has no result",
                    }
                )

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
        representative["supporting_evidence_origins"] = sorted(
            {
                str(result.get("launch_evidence", "unverified"))
                for result in results
                if result.get("assignment_id")
                in {item["assignment_id"] for item in items}
            }
        )
        representative["duplicate_count"] = len(items)
        resolution = ledger.get(ledger_key(representative))
        if resolution is not None:
            representative["previously_resolved"] = {
                "resolution_commit": resolution,
                "note": "already resolved in FINDING_LEDGER; verify the fix "
                "still holds instead of re-raising",
            }
        merged.append(representative)

    # Opposite verdicts on the same scoped evidence/proposition auto-conflict.
    # Statement text is explanatory prose, not a conflict identity: otherwise
    # semantically opposite paraphrases could evade adjudication.
    verdict_groups: dict[tuple, set[str]] = defaultdict(set)
    conflict_members: dict[tuple, list[dict]] = defaultdict(list)
    for result in results:
        for finding in result.get("findings", []):
            fingerprint = str(finding.get("evidence_fingerprint", ""))
            if not fingerprint:
                continue
            pair = (
                str(finding.get("claim_id", "")),
                fingerprint,
            )
            verdict_groups[pair].add(str(finding.get("verdict", "")))
            conflict_members[pair].append(
                {
                    "assignment_id": result.get("assignment_id"),
                    "finding_id": finding.get("finding_id"),
                    "verdict": finding.get("verdict"),
                    "statement": finding.get("statement"),
                }
            )
    conflicts = [
        {
            "claim_id": pair[0],
            "evidence_fingerprint": pair[1],
            "statements": sorted(
                {
                    str(member.get("statement", "")).strip()
                    for member in conflict_members[pair]
                }
            ),
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
        "process_status": (
            "INVALID_ENVELOPES"
            if errors
            else "CONFLICTS_REQUIRE_ADJUDICATION"
            if conflicts
            else "STRUCTURALLY_VALID"
        ),
        "claim_gate_status": "NOT_EVALUATED",
        "result_count": len(results),
        "raw_finding_count": sum(len(result.get("findings", [])) for result in results),
        "unique_finding_count": len(merged),
        "result_dispositions": result_dispositions,
        "findings": merged,
        "conflicts": conflicts,
        "errors": errors,
    }
    try:
        merge_inputs = run_merge_input_manifest(repo, run_dir)
    except ValueError as exc:
        errors.append(
            {
                "path": str(run_dir.relative_to(repo)),
                "error": str(exc),
            }
        )
        merge_inputs = []
    output.update(
        {
            "work_unit_id": plan.get("work_unit_id"),
            "change_set_id": plan.get("change_set_id"),
            "publication_group_id": plan.get("publication_group_id"),
            "assignment_count": len(assignments),
            "validated_result_count": len(valid_assignment_ids),
            "merge_inputs": merge_inputs,
            "merge_input_sha256": run_merge_input_sha256(merge_inputs),
        }
    )
    output["process_status"] = (
        "INVALID_ENVELOPES"
        if errors
        else "CONFLICTS_REQUIRE_ADJUDICATION"
        if conflicts
        else "STRUCTURALLY_VALID"
    )
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
