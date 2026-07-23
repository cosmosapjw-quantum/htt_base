#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

TRACK_II_MARKERS = {
    "native_bianchi_transfer",
    "native_bianchi_solver",
    "geometry_family_posterior",
    "native_remote_observer_field",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--track", choices=["I", "II"], required=True)
    parser.add_argument("--capabilities", default="")
    parser.add_argument("--solver-receipt")
    args = parser.parse_args()
    caps = {x.strip() for x in args.capabilities.split(",") if x.strip()}
    violations = sorted(caps & TRACK_II_MARKERS) if args.track == "I" else []
    solver_ok = bool(args.solver_receipt and Path(args.solver_receipt).exists())
    if args.track == "II" and not solver_ok:
        print(json.dumps({"status": "BLOCKED_NATIVE_REQUIRED", "track": args.track, "solver_receipt": args.solver_receipt}, indent=2))
        return 3
    if violations:
        print(json.dumps({"status": "FAIL", "track": args.track, "forbidden_track_ii_capabilities": violations}, indent=2))
        return 2
    print(json.dumps({"status": "PASS", "track": args.track, "capabilities": sorted(caps), "solver_receipt_verified": solver_ok}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
