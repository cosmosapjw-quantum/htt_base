#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from _harness import (
    ActiveRunError,
    active_run_id,
    hash_files,
    load_json,
    root,
    validate_assignment_payload,
    validate_result_payload,
)


def validate_repo(repo: Path) -> dict:
    harness = repo / ".agent-harness"
    index_path = harness / "context" / "CONTEXT_INDEX.json"
    index = load_json(index_path)
    files = list(index.get("shared_files", []))
    actual, entries = hash_files(repo, files)
    errors: list[str] = []
    state_errors: list[dict[str, str]] = []

    if actual != index.get("context_version"):
        errors.append("Context files changed after the pack was built.")
    if not (harness / "generated" / "CONTEXT_PACK.md").is_file():
        errors.append("Generated CONTEXT_PACK.md is missing.")

    active = None
    try:
        active = active_run_id(repo, required=False)
    except ActiveRunError as exc:
        state_errors.append(exc.as_dict())
        errors.append(f"{exc.error_code}: {exc.message}")
    if active:
        run_dir = harness / "runs" / active
        plan = load_json(run_dir / "RUN_PLAN.json")
        if plan.get("context_version") != index.get("context_version"):
            errors.append("Active run was initialized against a stale context version.")
        assignments = sorted((run_dir / "assignments").glob("*.json"))
        if len(assignments) > int(plan["budget"]["max_total"]):
            errors.append("Assignment count exceeds run max_total.")
        ids: set[str] = set()
        assignment_by_id: dict[str, dict] = {}
        for path in assignments:
            value = load_json(path)
            aid = value.get("assignment_id")
            if aid in ids:
                errors.append(f"Duplicate assignment_id: {aid}")
            ids.add(aid)
            assignment_errors = validate_assignment_payload(
                value,
                run_id=active,
                context_version=str(index.get("context_version", "")),
                assignment_id=path.stem,
            )
            errors.extend(f"{path.name}: {item}" for item in assignment_errors)
            if isinstance(aid, str):
                assignment_by_id[aid] = value

        for path in sorted((run_dir / "results").glob("*.json")):
            try:
                value = load_json(path)
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"Invalid result JSON {path.name}: {exc}")
                continue
            aid = value.get("assignment_id") if isinstance(value, dict) else None
            assignment = assignment_by_id.get(str(aid))
            if assignment is None:
                errors.append(f"Unregistered result: {path.name}")
                continue
            expected = str(assignment.get("result_path", ""))
            if path.relative_to(repo).as_posix() != expected or path.is_symlink():
                errors.append(f"Result path does not match registration: {path.name}")
                continue
            result_errors = validate_result_payload(
                value,
                assignment,
                run_id=active,
                context_version=str(index.get("context_version", "")),
            )
            errors.extend(f"{path.name}: {item}" for item in result_errors)

    payload = {
        "ok": not errors,
        "context_version": actual,
        "active_run": active,
    }
    if errors:
        payload["errors"] = errors
    if state_errors:
        payload["state_errors"] = state_errors
    return payload


def main() -> None:
    payload = validate_repo(root())
    print(json.dumps(payload, indent=2))
    if not payload["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
