#!/usr/bin/env python3
"""EGS3 v7 SageMath exact-rational seal lane.

Runs ``sage/egs3_v7_polyhedra.sage`` (SageMath + Singular), which emits one JSON
line of exact-rational polyhedron and ideal-membership checks, and verifies it
fail-closed into ``docs/generated/egs3_sage_seal.json``.

Missing ``sage`` is a *registered blocker* (exit 2), never silently replaced by a
Python computation. Any failing check sets status FAIL (exit 1). ``--check``
regenerates in memory and diffs against disk. Sage cold-start compiles its library
(~90 s once); warm runs are ~2 s.

Claim boundary: exact-rational polyhedron + ideal-membership seals only
(signed-box identified-interval endpoints + DL1 monotonicity + Bianchi V
constraint algebra); no data, detection, family/geometry, native-solver, or
posterior claim.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess

REPO = Path(__file__).resolve().parents[1]
SAGE_SCRIPT = REPO / "sage/egs3_v7_polyhedra.sage"
OUT = REPO / "docs/generated/egs3_sage_seal.json"


def build_payload() -> tuple[dict, int]:
    """Return (payload, exit_code). exit_code 2 == registered blocker."""
    sage = shutil.which("sage")
    if not sage or not SAGE_SCRIPT.exists():
        return {
            "status": "BLOCKED_SAGE_UNAVAILABLE",
            "detail": "sage not on PATH or sage/egs3_v7_polyhedra.sage missing",
        }, 2
    try:
        run = subprocess.run([sage, str(SAGE_SCRIPT)], text=True,
                             capture_output=True, check=True, timeout=1200)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        detail = getattr(exc, "stderr", "") or repr(exc)
        return {"status": "BLOCKED_SAGE_RUN_FAILED", "detail": str(detail)[-2000:]}, 2
    lines = [ln for ln in run.stdout.splitlines() if ln.strip().startswith("{")]
    if not lines:
        return {"status": "BLOCKED_SAGE_NO_OUTPUT", "stdout": run.stdout[-1000:]}, 2
    seal = json.loads(lines[-1])
    checks = seal.get("checks", {})
    all_true = bool(checks) and all(v is True for v in checks.values())
    seal["status"] = "PASS" if (all_true and seal.get("status") == "PASS") else "FAIL"
    return seal, (0 if seal["status"] == "PASS" else 1)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)

    payload, code = build_payload()
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"

    if code == 2:
        print(json.dumps(payload, indent=2))
        return 2

    if args.check:
        if not OUT.exists() or OUT.read_text() != text:
            print(f"stale sage seal artifact: {OUT}")
            return 1
        print("sage seal artifact current")
        return code

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print(f"wrote {OUT}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
