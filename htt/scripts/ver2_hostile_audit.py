"""Check and summarize VER2 hostile-audit runbooks."""
from __future__ import annotations

import argparse
import json
import sys

from workspace.contracts.validation_registry import (
    build_default_hostile_audit_runbooks,
    build_default_injection_manifests,
    build_default_null_manifests,
    build_default_theorem_to_test_map,
    build_default_validation_campaigns,
    hostile_audit_issues,
)


def _check_runbooks() -> int:
    runbooks = build_default_hostile_audit_runbooks()
    issues = hostile_audit_issues(
        theorem_map=build_default_theorem_to_test_map(),
        campaigns=build_default_validation_campaigns(),
        nulls=build_default_null_manifests(),
        injections=build_default_injection_manifests(),
        runbooks=runbooks,
    )
    if issues:
        print("[FAIL] hostile-audit runbook check")
        for issue in issues:
            print(f" - {issue}")
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
                    "campaign_refs": list(runbook.campaign_refs),
                    "theorem_refs": list(runbook.theorem_refs),
                    "baseline_checks": list(runbook.baseline_checks),
                    "adversarial_checks": list(runbook.adversarial_checks),
                    "physics_checks": list(runbook.physics_checks),
                    "numerical_checks": list(runbook.numerical_checks),
                    "regression_checks": list(runbook.regression_checks),
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
