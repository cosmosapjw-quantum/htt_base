#!/usr/bin/env python3
"""Register a sealed, fail-closed assignment (schema v2, audit H3/H7).

One command produces a complete assignment: bounded claim IDs, risk tier,
hash-sealed required inputs, allowed tools, required outputs, and — for CAS
agents — the axis binding and contract hash. Registration is refused if any
of these is empty or unknown; the pre-PR-124 validator accepted an unknown
``agent_type`` with empty lists (confirmed negative probe), which is the
defect this closes. The spawn budget counts cumulatively across every run
sharing the plan's ``work_unit_id``, so opening a fresh run no longer resets
the budget.
"""
from __future__ import annotations

import argparse
import hashlib
import json

from _harness import (
    active_run_id,
    dump_json,
    is_safe_identifier,
    load_json,
    root,
    validate_assignment_payload,
)


def _hashed_ref(repo, rel: str) -> dict:
    path = repo / rel
    if not path.is_file():
        raise SystemExit(f"required input does not exist: {rel}")
    return {"path": rel, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def _work_unit_assignment_count(harness, work_unit_id) -> int:
    if not work_unit_id:
        return 0
    count = 0
    for plan_path in sorted(harness.glob("runs/*/RUN_PLAN.json")):
        try:
            plan = load_json(plan_path)
        except (OSError, json.JSONDecodeError):
            continue
        if plan.get("work_unit_id") != work_unit_id:
            continue
        count += len(sorted((plan_path.parent / "assignments").glob("*.json")))
    return count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assignment-id", required=True)
    parser.add_argument("--agent-type", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--parent-assignment-id")
    parser.add_argument(
        "--independence-mode",
        choices=["shared-core", "blind-results", "adjudication"],
        default="shared-core",
    )
    parser.add_argument(
        "--discovery-mode",
        choices=["targeted", "independent"],
        default="targeted",
    )
    parser.add_argument(
        "--independence-rationale",
        default=None,
        help="required when --discovery-mode independent",
    )
    parser.add_argument("--risk-tier", required=True, choices=["R0", "R1", "R2", "R3"])
    parser.add_argument("--claim-id", action="append", default=[])
    parser.add_argument(
        "--required-input",
        action="append",
        default=[],
        help="repo-relative path; hashed and sealed into the assignment",
    )
    parser.add_argument("--allowed-tool", action="append", default=[])
    parser.add_argument("--required-output", action="append", default=[])
    parser.add_argument("--allowed-sibling-result", action="append", default=[])
    parser.add_argument("--cas-axis", default=None,
                        choices=["wolfram_xact", "sympy", "sage_singular", "lean"])
    parser.add_argument("--cas-contract", default=None,
                        help="repo-relative CAS_CONTRACT path (hashed)")
    parser.add_argument(
        "--fork-mode",
        choices=["none", "all"],
        default="none",
        help="fork_turns default is none (audit Phase 0); 'all' needs --fork-justification",
    )
    parser.add_argument("--fork-justification", default=None)
    parser.add_argument("--may-spawn", action="store_true")
    args = parser.parse_args()

    if not is_safe_identifier(args.assignment_id):
        raise SystemExit("assignment-id must be a safe 1-128 character identifier")
    if args.parent_assignment_id and not is_safe_identifier(args.parent_assignment_id):
        raise SystemExit("parent-assignment-id must be a safe identifier")
    if args.fork_mode == "all" and not (args.fork_justification or "").strip():
        raise SystemExit("--fork-mode all requires --fork-justification")

    repo = root()
    harness = repo / ".agent-harness"
    run_id = active_run_id(repo)
    run_dir = harness / "runs" / run_id
    plan = load_json(run_dir / "RUN_PLAN.json")
    index = load_json(harness / "context" / "CONTEXT_INDEX.json")
    assignments_dir = run_dir / "assignments"
    existing = sorted(assignments_dir.glob("*.json"))
    max_total = int(plan["budget"]["max_total"])
    if len(existing) >= max_total:
        raise SystemExit(f"Assignment budget exhausted: {len(existing)}/{max_total}")

    work_unit_id = plan.get("work_unit_id")
    max_per_unit = int(plan.get("budget", {}).get("max_total_per_work_unit", 0) or 0)
    if work_unit_id and max_per_unit:
        unit_count = _work_unit_assignment_count(harness, work_unit_id)
        if unit_count >= max_per_unit:
            raise SystemExit(
                f"Cumulative work-unit budget exhausted for {work_unit_id}: "
                f"{unit_count}/{max_per_unit} (budget spans ALL runs of this "
                "work unit; a new run does not reset it)"
            )

    depth = 1
    if args.parent_assignment_id:
        parent_path = assignments_dir / f"{args.parent_assignment_id}.json"
        if not parent_path.is_file():
            raise SystemExit(f"Parent assignment not found: {parent_path}")
        parent = load_json(parent_path)
        if not parent.get("may_spawn", False):
            raise SystemExit("Parent assignment does not grant may_spawn=true.")
        depth = int(parent.get("depth", 1)) + 1
    max_depth = int(plan["budget"]["max_depth"])
    if depth > max_depth:
        raise SystemExit(f"Depth budget exceeded: requested {depth}, max {max_depth}")

    out = assignments_dir / f"{args.assignment_id}.json"
    if out.exists():
        raise SystemExit(f"Assignment already exists: {out}")

    value = load_json(harness / "templates" / "ASSIGNMENT.json")
    value.update(
        {
            "schema_version": 2,
            "run_id": run_id,
            "assignment_id": args.assignment_id,
            "parent_assignment_id": args.parent_assignment_id,
            "depth": depth,
            "agent_type": args.agent_type,
            "context_version": index["context_version"],
            "independence_mode": args.independence_mode,
            "discovery_mode": args.discovery_mode,
            "independence_rationale": args.independence_rationale,
            "risk_tier": args.risk_tier,
            "fork_mode": args.fork_mode,
            "fork_justification": args.fork_justification,
            "may_spawn": args.may_spawn,
            "claim_ids": args.claim_id,
            "task": args.task,
            "required_inputs": [_hashed_ref(repo, rel) for rel in args.required_input],
            "allowed_tools": args.allowed_tool,
            "required_outputs": args.required_output,
            "allowed_sibling_results": args.allowed_sibling_result,
            "result_path": f".agent-harness/runs/{run_id}/results/{args.assignment_id}.json",
            "status": "registered",
        }
    )
    if args.cas_axis:
        value["cas_axis"] = args.cas_axis
    if args.cas_contract:
        value["cas_contract"] = _hashed_ref(repo, args.cas_contract)

    errors = validate_assignment_payload(
        value,
        run_id=run_id,
        context_version=str(index["context_version"]),
        assignment_id=args.assignment_id,
        repo=repo,
    )
    if errors:
        raise SystemExit(
            "assignment registration REFUSED (fail-closed):\n- " + "\n- ".join(errors)
        )

    sealed = json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")
    value["assignment_sha256"] = hashlib.sha256(sealed).hexdigest()
    dump_json(out, value)
    print(out.relative_to(repo))
    print(
        f"RUN_ID={run_id} ASSIGNMENT_ID={args.assignment_id} "
        f"CONTEXT_VERSION={index['context_version']} INDEPENDENCE_MODE={args.independence_mode}"
    )


if __name__ == "__main__":
    main()
