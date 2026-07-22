#!/usr/bin/env python3
"""Launcher-owned profile/context receipts (audit H1/H2/H5).

A task name in a spawn prompt is NOT evidence that a custom profile was
loaded. This receipt binds the launch to the installed profile registry
(name + config sha256), the fork mode, the context delivery mode, and the
effective-context hash. `verify` blocks (exit 2) on requested/actual profile
mismatch or stale config/context; a MISSING or unattested receipt does not
block — it downgrades the launch to `generic_prompted` with
`correlation_group=parent_llm`, so the result can never be counted as an
independent custom-profile reviewer.
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
    utc_now,
)
from profile_registry import ProfileRegistryError, load_profile_registry


def _receipt_path(harness, run_id: str, assignment_id: str):
    return harness / "runs" / run_id / "launches" / f"{assignment_id}.json"


def _role_file_hashes(repo, index, agent_type: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for rel in index.get("role_files", {}).get(agent_type, []):
        path = repo / rel
        digest = (
            hashlib.sha256(path.read_bytes()).hexdigest()
            if path.is_file()
            else "MISSING"
        )
        rows.append((rel, digest))
    return rows


def cmd_create(args) -> int:
    repo = root()
    harness = repo / ".agent-harness"
    run_id = cli_active_run_id(repo)
    assert run_id is not None
    if not is_safe_identifier(args.assignment_id):
        raise SystemExit("assignment-id must be a safe identifier")
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
        "correlation_group": None,
        "created_at": utc_now(),
    }
    role_files = _role_file_hashes(repo, index, actual)
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
        receipt["actual_profile"] = "generic_prompted"
        receipt["correlation_group"] = "parent_llm"
        dump_json(path, receipt)
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
    if receipt.get("requested_profile") != receipt.get("actual_profile"):
        errors.append(
            "requested profile "
            f"{receipt.get('requested_profile')!r} != actual "
            f"{receipt.get('actual_profile')!r}"
        )
    try:
        registry = load_profile_registry(repo)
    except ProfileRegistryError as exc:
        errors.append(str(exc))
        registry = {}
    profile = registry.get(str(receipt.get("actual_profile")))
    if profile is None:
        errors.append(f"profile not installed: {receipt.get('actual_profile')!r}")
    elif profile["config_sha256"] != receipt.get("config_sha256"):
        errors.append(
            "profile config drifted since launch receipt was created "
            f"({receipt.get('actual_profile')})"
        )

    index = load_json(harness / "context" / "CONTEXT_INDEX.json")
    assignment_path = (
        harness / "runs" / run_id / "assignments" / f"{args.assignment_id}.json"
    )
    if not assignment_path.is_file():
        errors.append(f"assignment missing: {args.assignment_id}")
    else:
        role_files = _role_file_hashes(
            repo, index, str(receipt.get("actual_profile"))
        )
        expected = compute_effective_context_sha256(
            index, assignment_path.read_bytes(), role_files, receipt
        )
        if expected != receipt.get("effective_context_sha256"):
            errors.append(
                "effective context is stale (role file, assignment, required "
                "input, or injection config changed since launch)"
            )
        # Re-validate the assignment fail-closed at launch time: this catches
        # a required-input file whose bytes drifted after sealing (the
        # assignment stores the input hash, so the assignment bytes alone do
        # not change).
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
        choices=["hook_injected", "file_fallback"],
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
