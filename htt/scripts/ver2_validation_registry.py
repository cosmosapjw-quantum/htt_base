"""Emit and check the VER2 validation campaign registry."""
from __future__ import annotations

import argparse
import json
import sys

from workspace.contracts.validation_registry import (
    build_default_theorem_to_test_map,
    build_default_validation_campaigns,
    build_default_hostile_audit_runbooks,
    build_default_injection_manifests,
    build_default_null_manifests,
    validation_registry_issues,
    validation_registry_payload,
)


def _check_registry() -> int:
    theorem_map = build_default_theorem_to_test_map()
    campaigns = build_default_validation_campaigns()
    nulls = build_default_null_manifests()
    injections = build_default_injection_manifests()
    runbooks = build_default_hostile_audit_runbooks()
    issues = validation_registry_issues(
        theorem_map=theorem_map,
        campaigns=campaigns,
        nulls=nulls,
        injections=injections,
        runbooks=runbooks,
    )
    if issues:
        print("[FAIL] validation registry check")
        for issue in issues:
            print(f" - {issue}")
        return 1
    print(
        "[PASS] validation registry check "
        f"({len(theorem_map)} theorems, {len(campaigns)} campaigns, "
        f"{len(nulls)} nulls, {len(injections)} injections, "
        f"{len(runbooks)} runbooks)"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.check:
        return _check_registry()
    payload = validation_registry_payload()
    if args.json:
        json.dump(payload, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0
    print(
        "VER2 validation registry: "
        f"{len(payload['theorem_map'])} theorems, "
        f"{len(payload['campaigns'])} campaigns, "
        f"manuscript_export_blocked={payload['manuscript_export_blocked']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
