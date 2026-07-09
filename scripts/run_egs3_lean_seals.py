#!/usr/bin/env python3
"""EGS3 v7 Lean-core seal lane.

Builds the pure-Lean-4 ``formal/`` project (no mathlib) and runs the ``egs3v7``
executable, whose successful elaboration IS the proof: every seal proposition is
closed by ``decide``/``native_decide`` at compile time. The executable re-checks
the load-bearing propositions at runtime and emits one JSON line, which this
runner parses and verifies fail-closed.

Missing ``lake``/``lean`` is a *registered blocker* (exit 2), never silently
replaced by a Python assertion. Any failing check sets status FAIL (exit 1).
``--check`` regenerates in memory and diffs against disk.

Claim boundary: machine-checked rational/Bool-lattice seals only (gate-promotion
lattice + signed-box identified-interval endpoint certificates + registered
convention constants); no data, detection, family/geometry, native-solver, or
posterior claim.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess

REPO = Path(__file__).resolve().parents[1]
FORMAL_DIR = REPO / "formal"
OUT = REPO / "docs/generated/egs3_lean_seal.json"


def _lean_version() -> str:
    exe = shutil.which("lean")
    if not exe:
        return "unavailable"
    try:
        out = subprocess.run([exe, "--version"], text=True, capture_output=True, check=True)
        return out.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def build_payload() -> tuple[dict, int]:
    """Return (payload, exit_code). exit_code 2 == registered blocker."""
    lake = shutil.which("lake")
    if not lake or not (FORMAL_DIR / "lakefile.toml").exists():
        return {
            "status": "BLOCKED_LEAN_UNAVAILABLE",
            "detail": "lake not on PATH or formal/ project missing",
            "lean_version": _lean_version(),
        }, 2
    try:
        subprocess.run([lake, "build"], cwd=FORMAL_DIR, text=True,
                       capture_output=True, check=True, timeout=900)
        run = subprocess.run([lake, "exe", "egs3v7"], cwd=FORMAL_DIR, text=True,
                             capture_output=True, check=True, timeout=300)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        detail = getattr(exc, "stderr", "") or repr(exc)
        return {
            "status": "BLOCKED_LEAN_BUILD_FAILED",
            "detail": str(detail)[-2000:],
            "lean_version": _lean_version(),
        }, 2
    lines = [ln for ln in run.stdout.splitlines() if ln.strip().startswith("{")]
    if not lines:
        return {"status": "BLOCKED_LEAN_NO_OUTPUT", "stdout": run.stdout[-1000:]}, 2
    seal = json.loads(lines[-1])
    checks = seal.get("checks", {})
    all_true = bool(checks) and all(v is True for v in checks.values())
    payload = {
        "seal": "egs3.lean_core",
        "status": "PASS" if (all_true and seal.get("status") == "PASS") else "FAIL",
        "lean_version": _lean_version(),
        "lean_schema": seal.get("schema"),
        "checks": checks,
        "claim_boundary": "machine-checked rational/Bool-lattice seals only; "
                          "gate-promotion lattice + signed-box endpoint certificates "
                          "+ convention constants; no data/detection/family/native "
                          "claim",
    }
    return payload, (0 if payload["status"] == "PASS" else 1)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)

    payload, code = build_payload()
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"

    if code == 2:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        print(json.dumps(payload, indent=2))
        return 2

    if args.check:
        if not OUT.exists() or OUT.read_text() != text:
            print(f"stale lean seal artifact: {OUT}")
            return 1
        print("lean seal artifact current")
        return code

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print(f"wrote {OUT}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
