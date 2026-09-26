#!/usr/bin/env python3
"""Build or verify the PR-204 ACT two-branch closure card."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml


REPO = Path(__file__).resolve().parents[2]
for root in (REPO, REPO / "htt", REPO / "htt/src"):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from obsstat.act_inband_modulation import semantic_digest  # noqa: E402
from obsstat.act_modulation_closure import (  # noqa: E402
    ActModulationClosureError,
    build_closure_card,
)


SPEC = REPO / "docs/research_program/long_horizon_rescue/pr204_spec.yaml"
MODULE = REPO / "htt/obsstat/act_modulation_closure.py"
OUTPUT = REPO / "docs/generated/pr204_result_card.json"
SOURCE_KEYS = {
    "result": "docs/generated/pr177_act_modulation_result.json",
    "mask": "docs/generated/pr177_mask_control.json",
    "mc": "docs/generated/pr177_mc_resolution.json",
    "result_card": "docs/generated/pr177_result_card.json",
    "availability": "docs/generated/pr152_availability_decision.json",
    "inventory": "docs/generated/pr152_inventory.json",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1 << 20):
            digest.update(block)
    return digest.hexdigest()


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ActModulationClosureError(f"{path.relative_to(REPO)} must be an object")
    return value


def _spec() -> dict[str, Any]:
    value = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ActModulationClosureError("PR-204 spec must be a mapping")
    if value.get("schema") != "htt.long_horizon.pr204_act_closure.v1":
        raise ActModulationClosureError("PR-204 spec schema mismatch")
    return value


def build() -> dict[str, object]:
    spec = _spec()
    identities = spec.get("source_identities")
    if not isinstance(identities, dict):
        raise ActModulationClosureError("source identities missing from PR-204 spec")
    sources: dict[str, dict[str, Any]] = {}
    for key, relative in SOURCE_KEYS.items():
        path = REPO / relative
        expected = identities.get(relative)
        actual = _sha256(path)
        if expected != actual:
            raise ActModulationClosureError(
                f"source identity mismatch: {relative}: expected {expected}, found {actual}"
            )
        sources[key] = _json(path)
    payload = build_closure_card(spec=spec, **sources)
    payload["implementation_sha256"] = {
        str(SPEC.relative_to(REPO)): _sha256(SPEC),
        str(MODULE.relative_to(REPO)): _sha256(MODULE),
        str(Path(__file__).resolve().relative_to(REPO)): _sha256(Path(__file__).resolve()),
    }
    payload["generating_command"] = (
        "PYTHONDONTWRITEBYTECODE=1 python3 -B "
        "scripts/codex_harness/run_pr204_act_closure.py --write"
    )
    payload["semantic_digest"] = semantic_digest(payload)
    return payload


def _bytes(payload: dict[str, object]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        expected = _bytes(build())
        if args.write:
            OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            OUTPUT.write_bytes(expected)
            print(f"WROTE {OUTPUT.relative_to(REPO)}")
            return 0
        if not OUTPUT.is_file():
            raise ActModulationClosureError("PR-204 result card is missing")
        if OUTPUT.read_bytes() != expected:
            raise ActModulationClosureError("PR-204 result card is stale")
        print("PASS PR-204 ACT release-summary/raw-QE closure")
        return 0
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
