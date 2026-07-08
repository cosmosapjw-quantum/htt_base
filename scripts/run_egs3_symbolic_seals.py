#!/usr/bin/env python3
"""Run the EGS3 SymPy seals (parent identity + Bianchi V constraint) and write

  docs/generated/parent_identity_seal.json
  docs/generated/bianchi_v_constraint_seal.json

Deterministic (pure symbolic algebra + fixed numeric witnesses, no timestamps;
the sympy version is recorded inside each seal). Fail-closed: any failing check
sets status FAIL and the script exits 1 -- a seal is never written as PASS by
fallback. ``--check`` regenerates in memory and diffs against disk (exit 1 +
stale list on drift).

Claim boundary: symbolic convention/legacy-recovery seals only; no data claim,
no detection, family/geometry, native-solver, or posterior claim.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

OUTPUTS = {
    "parent_identity_seal.json": "parent",
    "bianchi_v_constraint_seal.json": "bianchi_v",
}
OUT_DIR = REPO / "docs/generated"


def build_payloads() -> dict[str, str]:
    from htt.obsstat.egs3_parent_identity import parent_identity_seal
    from htt.obsstat.egs3_bianchi_v_constraint import bianchi_v_seal
    seals = {"parent": parent_identity_seal(), "bianchi_v": bianchi_v_seal()}
    return {
        name: json.dumps(seals[key], indent=2, default=float) + "\n"
        for name, key in OUTPUTS.items()
    }, seals


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    check = "--check" in argv
    payloads, seals = build_payloads()

    failed = [k for k, s in seals.items() if s.get("status") != "PASS"]
    if failed:
        for k in failed:
            print(f"SEAL FAIL: {k}", file=sys.stderr)
        return 1

    if check:
        stale = []
        for name, text in payloads.items():
            path = OUT_DIR / name
            if not path.exists() or path.read_text() != text:
                stale.append(str(path))
        if stale:
            print("stale seal artifacts:\n  " + "\n  ".join(stale), file=sys.stderr)
            return 1
        print("seal artifacts current")
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, text in payloads.items():
        (OUT_DIR / name).write_text(text)
        print(f"wrote {OUT_DIR / name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
