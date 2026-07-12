#!/usr/bin/env python3
"""Run the EGS3 external-data lanes (DESI / ACT / JWST) and write the seal.

Deterministic (fixed mock seed + fixed on-disk data); --check byte-diffs the
regenerated seal against docs/generated/external_lanes_seal.json. The lanes
that need a missing companion product emit a registered blocker, never a
substitute estimate.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
for p in (REPO, REPO / "htt", REPO / "htt/htt"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from htt.obsstat.egs3_external_lanes import external_lanes_seal  # noqa: E402

OUT = REPO / "docs/generated/external_lanes_seal.json"


def _render(payload: dict) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    payload = external_lanes_seal()
    rendered = _render(payload)
    if args.check:
        if not OUT.exists() or OUT.read_text() != rendered:
            print("STALE external_lanes_seal.json", file=sys.stderr)
            return 1
        print("external_lanes seal current")
        return 0
    OUT.write_text(rendered)
    print(f"wrote {OUT} status={payload['status']}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
