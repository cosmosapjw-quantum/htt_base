#!/usr/bin/env python3
"""Validate, summarize, and close the local active harness run."""

from __future__ import annotations

import argparse
import json

from _harness import (
    ActiveRunError,
    active_run_id,
    clear_active_run_pointers,
    dump_json,
    is_safe_identifier,
    root,
    utc_now,
)
from run_summary import summarize_run
from validate_harness import validate_repo


def fail(code: str, message: str, **extra: object) -> None:
    error = {"code": code, "message": message}
    print(json.dumps({"ok": False, "error": error, **extra}, indent=2))
    raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run-id",
        help="optional identity guard; refuse to close a different active run",
    )
    parser.add_argument(
        "--abandon",
        action="store_true",
        help=(
            "clear local pointer state without validating or deleting the run directory; "
            "use only to recover invalid or dangling state"
        ),
    )
    args = parser.parse_args()
    if args.run_id is not None and not is_safe_identifier(args.run_id):
        fail(
            "INVALID_ACTIVE_RUN_POINTER",
            "--run-id must be a safe 1-128 character identifier.",
        )

    repo = root()
    if args.abandon:
        if args.run_id is not None:
            fail(
                "INCOMPATIBLE_ARGUMENTS",
                "--run-id cannot be combined with --abandon.",
            )
        try:
            cleared = clear_active_run_pointers(repo)
        except ActiveRunError as exc:
            fail(exc.error_code, exc.message)
        if not cleared:
            fail(
                "NO_ACTIVE_RUN",
                "No active-run pointer exists to abandon.",
            )
        print(
            json.dumps(
                {
                    "ok": True,
                    "abandoned": True,
                    "cleared_pointers": cleared,
                    "run_directory_deleted": False,
                },
                indent=2,
            )
        )
        return

    try:
        run_id = active_run_id(repo)
    except ActiveRunError as exc:
        fail(exc.error_code, exc.message, state_error=exc.as_dict())
    assert run_id is not None
    if args.run_id is not None and run_id != args.run_id:
        fail(
            "ACTIVE_RUN_MISMATCH",
            "The active run does not match --run-id.",
            active_run=run_id,
        )
    validation = validate_repo(repo)
    if not validation["ok"]:
        fail(
            "HARNESS_VALIDATION_FAILED",
            "The active run must validate before normal close.",
            validation=validation,
        )

    run_dir = repo / ".agent-harness" / "runs" / run_id
    summary = summarize_run(repo, run_dir, "summarized_discardable")
    summary["closed_at"] = utc_now()
    summary_path = run_dir / "RUN_SUMMARY.json"
    dump_json(summary_path, summary)
    try:
        cleared = clear_active_run_pointers(repo, expected_run_id=run_id)
    except ActiveRunError as exc:
        fail(
            exc.error_code,
            exc.message,
            summary=summary_path.relative_to(repo).as_posix(),
        )
    print(
        json.dumps(
            {
                "ok": True,
                "abandoned": False,
                "closed_run": run_id,
                "summary": summary_path.relative_to(repo).as_posix(),
                "cleared_pointers": cleared,
                "run_directory_deleted": False,
                "active_run": None,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
