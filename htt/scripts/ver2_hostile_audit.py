"""Check and summarize VER2 hostile-audit runbooks."""
from __future__ import annotations

import argparse
import json
import sys

from workspace.contracts.validation_registry import (
    build_default_hostile_audit_runbooks,
)


def _check_runbooks() -> int:
    runbooks = build_default_hostile_audit_runbooks()
    bad = [
        runbook.runbook_id
        for runbook in runbooks
        if not (
            runbook.baseline_checks
            and runbook.adversarial_checks
            and runbook.physics_checks
            and runbook.numerical_checks
            and runbook.regression_checks
        )
    ]
    if bad:
        print(f"[FAIL] incomplete hostile-audit runbooks: {bad}")
        return 1
    print(f"[PASS] hostile-audit runbook check ({len(runbooks)} runbooks)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    runbooks = build_default_hostile_audit_runbooks()
    if args.check:
        return _check_runbooks()
    if args.json:
        json.dump(
            [
                {
                    "runbook_id": runbook.runbook_id,
                    "title": runbook.title,
                    "theorem_refs": list(runbook.theorem_refs),
                    "quarantine_conditions": list(runbook.quarantine_conditions),
                }
                for runbook in runbooks
            ],
            sys.stdout,
            indent=2,
            sort_keys=True,
        )
        sys.stdout.write("\n")
        return 0
    print(f"VER2 hostile-audit runbooks: {len(runbooks)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
