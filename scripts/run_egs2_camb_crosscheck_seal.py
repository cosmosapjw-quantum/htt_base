#!/usr/bin/env python3
"""Run the EGS2 B1 CAMB-visibility cross-check seal and write
docs/generated/seminative_camb_crosscheck_seal.json.

Engine-dependent lane (real CAMB background): follows the exit-2
registered-blocker pattern (like the Sage/Lean/mathlib runners) -- camb absent
or failing is a REGISTERED blocker (exit 2), never silence; a FAIL status on a
completed cross-check exits 1 (fail-closed). ``--check`` regenerates in memory
and diffs against disk.

Claim boundary: single-mode exact-FLRW-anchored diagnostic cross-check; no
data claim, no signal-discovery/geometry/probabilistic-inference claim.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
for p in (REPO, REPO / "htt", REPO / "htt/htt"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

OUT = REPO / "docs/generated/seminative_camb_crosscheck_seal.json"


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    check = "--check" in argv

    from htt.bass.transfer.visibility_camb_crosscheck import (
        seminative_camb_crosscheck_seal)
    seal = seminative_camb_crosscheck_seal()
    payload = json.dumps(seal, indent=2, default=float) + "\n"

    if seal["status"] == "BLOCKED_CAMB_UNAVAILABLE":
        print("REGISTERED BLOCKER: camb unavailable; seal not written",
              file=sys.stderr)
        return 2
    if seal["status"] != "PASS":
        print("CAMB CROSSCHECK SEAL FAIL", file=sys.stderr)
        return 1

    if check:
        if not OUT.exists() or OUT.read_text() != payload:
            print(f"stale camb cross-check seal: {OUT}", file=sys.stderr)
            return 1
        print("camb cross-check seal current")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(payload)
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
