#!/usr/bin/env python3
"""EGS3 v8 mathlib-backed Lean seal lane.

Builds the separate ``formal_mathlib/`` package (mathlib dependency) whose successful
elaboration IS the proof: the forall-parameter T1'/DL1/T2' generalizations
(``Egs3V8Mathlib/Basic.lean``) are closed by mathlib order/field lemmas at compile
time. This lane is kept OUT of ``formal/`` so the core ``native_decide`` lane stays
offline and fast.

Missing ``lake``/mathlib cache (network) is a *registered blocker* (exit 2), never
silently replaced by a Python assertion. A build failure is also exit 2. ``--check``
diffs the recorded seal against disk.

Claim boundary: machine-checked forall-parameter rational-order seals only; no data,
detection, family/geometry, native-solver, or posterior claim.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess

REPO = Path(__file__).resolve().parents[1]
PKG_DIR = REPO / "formal_mathlib"
OUT = REPO / "docs/generated/egs3_v8_mathlib_seal.json"

# The forall-parameter theorems this lane certifies (must exist in Basic.lean).
THEOREMS = [
    "nullLo_of_nonneg", "nullHi_of_nonneg", "dl1_lower_gap",
    "joint_subset_naive", "w2_mismatch_factor", "mes_three_halves",
    "bianchi_v_four_thirds",
]


def _lean_version() -> str:
    exe = shutil.which("lean")
    if not exe:
        return "unavailable"
    try:
        out = subprocess.run([exe, "--version"], text=True, capture_output=True, check=True)
        return out.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def _theorems_present() -> bool:
    src = (PKG_DIR / "Egs3V8Mathlib" / "Basic.lean")
    if not src.exists():
        return False
    text = src.read_text(encoding="utf-8")
    return all(f"theorem {name}" in text for name in THEOREMS)


def build_payload() -> tuple[dict, int]:
    """Return (payload, exit_code). exit_code 2 == registered blocker."""
    lake = shutil.which("lake")
    if not lake or not (PKG_DIR / "lakefile.toml").exists():
        return {
            "status": "BLOCKED_LEAN_UNAVAILABLE",
            "detail": "lake not on PATH or formal_mathlib/ package missing",
            "lean_version": _lean_version(),
        }, 2
    if not _theorems_present():
        return {"status": "BLOCKED_THEOREMS_MISSING",
                "detail": "expected theorems not all present in Basic.lean"}, 2
    # fetch the prebuilt mathlib cache (network) if not already present, then build.
    try:
        subprocess.run([lake, "exe", "cache", "get"], cwd=PKG_DIR, text=True,
                       capture_output=True, timeout=1800)  # best-effort; build is the gate
        subprocess.run([lake, "build"], cwd=PKG_DIR, text=True,
                       capture_output=True, check=True, timeout=3600)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        detail = getattr(exc, "stderr", "") or repr(exc)
        return {
            "status": "BLOCKED_MATHLIB_BUILD_FAILED",
            "detail": str(detail)[-2000:],
            "lean_version": _lean_version(),
        }, 2
    payload = {
        "seal": "egs3.mathlib_general",
        "status": "PASS",
        "lean_version": _lean_version(),
        "theorems": THEOREMS,
        "note": "forall-parameter generalizations of the concrete native_decide lane: "
                "T1' signed-box endpoint formulas, DL1 branch gap = c*U, T2' interval "
                "subset, all proved for arbitrary rationals via mathlib order/field lemmas",
        "claim_boundary": "machine-checked forall-parameter rational-order seals; no data, "
                          "detection, family/geometry, native-solver, or posterior claim",
    }
    return payload, 0


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
            print(f"stale mathlib seal artifact: {OUT}")
            return 1
        print("mathlib seal artifact current")
        return code

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print(f"wrote {OUT}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
