#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from _harness import (
    ActiveRunError,
    active_run_id,
    context_entries,
    load_json,
    load_validated_context_pack,
    resolve_live_context,
    root,
    validate_assignment_payload,
)
from strict_result_validation import load_and_validate_registered_result_file


def validate_repo(repo: Path) -> dict:
    harness = repo / ".agent-harness"
    index_path = harness / "context" / "CONTEXT_INDEX.json"
    index = load_json(index_path)
    errors: list[str] = []
    state_errors: list[dict[str, str]] = []
    actual = ""
    entries: list[tuple[str, str]] = []

    try:
        max_chars = int(index.get("max_injected_chars", 0))
    except (TypeError, ValueError):
        max_chars = None
        errors.append("max_injected_chars must be an integer in the 8-12 KiB budget.")
    if max_chars is not None and not 8192 <= max_chars <= 12288:
        errors.append("max_injected_chars must stay within the 8-12 KiB budget.")

    context_shape_ok = True
    try:
        actual, entries, _ = context_entries(repo, index)
    except (OSError, UnicodeError, ValueError) as exc:
        context_shape_ok = False
        errors.append(f"Context index or Tier-0 sources are invalid: {exc}")
    if context_shape_ok:
        if actual != index.get("context_version"):
            errors.append("Context files changed after the pack was built.")
        if index.get("file_hashes") != dict(entries):
            errors.append("CONTEXT_INDEX.json file_hashes do not match shared files.")
        try:
            load_validated_context_pack(repo, index)
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append(f"Generated context view is invalid: {exc}")

    active = None
    live_context = None
    try:
        active = active_run_id(repo, required=False)
    except ActiveRunError as exc:
        state_errors.append(exc.as_dict())
        errors.append(f"{exc.error_code}: {exc.message}")
    if not state_errors:
        try:
            live_context = resolve_live_context(repo, index)
        except (
            ActiveRunError,
            OSError,
            UnicodeDecodeError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            errors.append(f"Live context could not be resolved: {exc}")
    if active:
        run_dir = harness / "runs" / active
        plan = load_json(run_dir / "RUN_PLAN.json")
        if plan.get("context_version") != index.get("context_version"):
            errors.append("Active run was initialized against a stale context version.")
        assignments = sorted((run_dir / "assignments").glob("*.json"))
        if len(assignments) > int(plan["budget"]["max_total"]):
            errors.append("Assignment count exceeds run max_total.")
        ids: set[str] = set()
        for path in assignments:
            if path.is_symlink() or not path.is_file():
                errors.append(f"{path.name}: assignment is not a regular file")
                continue
            try:
                value = load_json(path)
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"{path.name}: invalid assignment JSON: {exc}")
                continue
            if not isinstance(value, dict):
                errors.append(f"{path.name}: assignment is not a JSON object")
                continue
            aid = value.get("assignment_id")
            if aid in ids:
                errors.append(f"Duplicate assignment_id: {aid}")
            ids.add(aid)
            assignment_errors = validate_assignment_payload(
                value,
                run_id=active,
                context_version=str(index.get("context_version", "")),
                assignment_id=path.stem,
                repo=repo,
            )
            errors.extend(f"{path.name}: {item}" for item in assignment_errors)

        for path in sorted((run_dir / "results").glob("*.json")):
            validation = load_and_validate_registered_result_file(
                repo,
                path,
                run_id=active,
                context_version=str(index.get("context_version", "")),
            )
            errors.extend(f"{path.name}: {item}" for item in validation.errors)

    payload = {
        "ok": not errors,
        "context_version": actual,
        "active_run": active,
    }
    if live_context is not None:
        payload["live_context"] = live_context
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
