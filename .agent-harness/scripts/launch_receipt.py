#!/usr/bin/env python3
"""Locally recorded profile/context receipts (audit H1/H2/H5).

A task name in a spawn prompt is NOT evidence that a custom profile was
loaded. This self-declared receipt binds the launch to the installed profile
registry (name + config sha256), the fork mode, the context delivery mode, and the
effective-context hash. `verify` blocks (exit 2) on requested/actual profile
mismatch or stale config/context; a MISSING or unattested receipt does not
block — it downgrades the launch to `generic_prompted` with
`correlation_group=parent_llm`, so the result can never be counted as an
independent custom-profile reviewer. ``--attested`` remains a compatibility
name for a caller assertion; it is not platform-authenticated provenance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys

from _harness import (
    cli_active_run_id,
    compute_effective_context_sha256,
    dump_json,
    is_safe_identifier,
    load_json,
    root,
    role_file_hashes,
    utc_now,
)
from profile_registry import load_profile_registry
from strict_result_validation import validate_launch_payload


def _receipt_path(harness, run_id: str, assignment_id: str):
    return harness / "runs" / run_id / "launches" / f"{assignment_id}.json"


def cmd_create(args) -> int:
    repo = root()
    harness = repo / ".agent-harness"
    run_id = cli_active_run_id(repo)
    assert run_id is not None
    if not is_safe_identifier(args.assignment_id):
        raise SystemExit("assignment-id must be a safe identifier")
    if args.delivery_mode != "hook_injected":
        raise SystemExit(
            "file fallback is disabled; context must be delivered by the validated hook"
        )
    assignment_path = (
        harness / "runs" / run_id / "assignments" / f"{args.assignment_id}.json"
    )
    if not assignment_path.is_file():
        raise SystemExit(f"assignment is not registered: {args.assignment_id}")
    assignment_bytes = assignment_path.read_bytes()
    index = load_json(harness / "context" / "CONTEXT_INDEX.json")

    registry = load_profile_registry(repo)
    requested = args.requested_profile
    actual = args.actual_profile or requested
    profile = registry.get(actual)
    receipt = {
        "schema_version": 1,
        "launch_id": hashlib.sha256(
            f"{run_id}:{args.assignment_id}:{utc_now()}".encode("utf-8")
        ).hexdigest(),
        "run_id": run_id,
        "assignment_id": args.assignment_id,
        "requested_profile": requested,
        "actual_profile": actual,
        "config_sha256": profile["config_sha256"] if profile else None,
        "sandbox": profile["sandbox_mode"] if profile else None,
        "model": args.model,
        "fork_mode": args.fork_mode,
        "context_delivery_mode": args.delivery_mode,
        "attested": bool(args.attested),
        "evidence_origin": "self_declared",
        "correlation_group": None,
        "created_at": utc_now(),
    }
    role_files = role_file_hashes(repo, index, actual)
    receipt["effective_context_sha256"] = compute_effective_context_sha256(
        index, assignment_bytes, role_files, receipt
    )
    out = _receipt_path(harness, run_id, args.assignment_id)
    dump_json(out, receipt)
    print(out.relative_to(repo))
    print(f"LAUNCH_ID={receipt['launch_id']}")
    return 0


def cmd_verify(args) -> int:
    repo = root()
    harness = repo / ".agent-harness"
    run_id = cli_active_run_id(repo)
    assert run_id is not None
    path = _receipt_path(harness, run_id, args.assignment_id)
    if not path.is_file():
        print(
            json.dumps(
                {
                    "verdict": "downgraded",
                    "actual_profile": "generic_prompted",
                    "correlation_group": "parent_llm",
                    "reason": "no launch receipt; independent-profile credit removed",
                }
            )
        )
        return 0
    receipt = load_json(path)
    if not receipt.get("attested"):
        print(
            json.dumps(
                {
                    "verdict": "downgraded",
                    "actual_profile": "generic_prompted",
                    "correlation_group": "parent_llm",
                    "reason": "receipt is unattested; treated as generic prompted agent",
                }
            )
        )
        return 0

    errors: list[str] = []
    index = load_json(harness / "context" / "CONTEXT_INDEX.json")
    assignment_path = (
        harness / "runs" / run_id / "assignments" / f"{args.assignment_id}.json"
    )
    if not assignment_path.is_file():
        errors.append(f"assignment missing: {args.assignment_id}")
    else:
        from _harness import validate_assignment_payload

        assignment = load_json(assignment_path)
        errors.extend(
            validate_assignment_payload(
                assignment,
                run_id=run_id,
                context_version=str(index.get("context_version", "")),
                assignment_id=args.assignment_id,
                repo=repo,
            )
        )
        launch_errors, _ = validate_launch_payload(
            receipt,
            assignment,
            repo=repo,
            assignment_path=assignment_path,
            index=index,
        )
        errors.extend(launch_errors)

    if errors:
        print(
            json.dumps({"verdict": "blocked", "errors": errors}, ensure_ascii=False)
        )
        return 2
    print(json.dumps({"verdict": "ok", "launch_id": receipt.get("launch_id")}))
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create")
    create.add_argument("--assignment-id", required=True)
    create.add_argument("--requested-profile", required=True)
    create.add_argument("--actual-profile", default=None)
    create.add_argument("--model", default=None)
    create.add_argument("--fork-mode", choices=["none", "all"], default="none")
    create.add_argument(
        "--delivery-mode",
        choices=["hook_injected"],
        default="hook_injected",
    )
    create.add_argument("--attested", action="store_true")

    verify = sub.add_parser("verify")
    verify.add_argument("--assignment-id", required=True)

    args = parser.parse_args()
    if args.command == "create":
        sys.exit(cmd_create(args))
    sys.exit(cmd_verify(args))


if __name__ == "__main__":
    main()
