"""Emit and check the VER2 validation campaign registry."""
from __future__ import annotations

import argparse
import json
import sys

from workspace.contracts.validation_registry import (
    build_default_theorem_to_test_map,
    build_default_validation_campaigns,
    validation_registry_payload,
)


def _check_registry() -> int:
    theorem_map = build_default_theorem_to_test_map()
    campaigns = build_default_validation_campaigns()
    theorem_ids = {entry.theorem_id for entry in theorem_map}
    missing_refs = sorted(
        ref
        for campaign in campaigns
        for ref in campaign.theorem_refs
        if ref not in theorem_ids
    )
    if missing_refs:
        print(f"[FAIL] unknown theorem refs in campaigns: {missing_refs}")
        return 1
    if not all(entry.artifact_refs for entry in theorem_map):
        print("[FAIL] theorem map contains entry without artifact refs")
        return 1
    print(
        "[PASS] validation registry check "
        f"({len(theorem_map)} theorems, {len(campaigns)} campaigns)"
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
