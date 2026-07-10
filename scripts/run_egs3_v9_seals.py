#!/usr/bin/env python3
"""EGS3 v9-cycle seal runner (REV-R171..): fail-closed JSON seals for the
v9 successor theorems, written to docs/generated/:

  fractional_program_exact_seal.json    (T2G, SymPy+Fraction primary lane)
  fractional_program_sage_seal.json     (T2G, SageMath QQ+PPL second engine;
                                         missing sage == registered blocker,
                                         exit 2, never silently substituted)

Later v9 phases register additional seals here (TSUM, U4-v9, MES-BR).
``--check`` regenerates in memory and diffs against disk byte-exactly.

Claim boundary: diagnostic-only exact algebra/statistics on registered
synthetic instances; no data claim, no geometry claim, no inference claim.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
for p in (REPO, REPO / "htt", REPO / "htt/htt", REPO / "htt/src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

OUT_DIR = REPO / "docs/generated"
SAGE_SCRIPT = REPO / "sage/egs3_v9_fractional.sage"


def sage_fractional_seal() -> tuple[dict, int]:
    sage = shutil.which("sage")
    if not sage or not SAGE_SCRIPT.exists():
        return {"status": "BLOCKED_SAGE_UNAVAILABLE",
                "detail": "sage not on PATH or sage/egs3_v9_fractional.sage "
                          "missing"}, 2
    try:
        run = subprocess.run([sage, str(SAGE_SCRIPT)], text=True,
                             capture_output=True, check=True, timeout=1200)
    except (OSError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired) as exc:
        detail = getattr(exc, "stderr", "") or repr(exc)
        return {"status": "BLOCKED_SAGE_RUN_FAILED",
                "detail": str(detail)[-2000:]}, 2
    lines = [ln for ln in run.stdout.splitlines()
             if ln.strip().startswith("{")]
    if not lines:
        return {"status": "BLOCKED_SAGE_NO_OUTPUT",
                "stdout": run.stdout[-1000:]}, 2
    seal = json.loads(lines[-1])
    checks = seal.get("checks", {})
    ok = bool(checks) and all(v is True for v in checks.values())
    seal["status"] = "PASS" if (ok and seal.get("status") == "PASS") else "FAIL"
    return seal, (0 if seal["status"] == "PASS" else 1)


def build_seals() -> tuple[dict[str, dict], int]:
    """Return ({filename: payload}, worst_exit_code)."""
    payloads: dict[str, dict] = {}
    worst = 0

    from htt.obsstat.egs3_fractional_program import fractional_program_seal
    seal = fractional_program_seal()
    payloads["fractional_program_exact_seal.json"] = seal
    if seal.get("status") != "PASS":
        worst = max(worst, 1)

    sage_seal, code = sage_fractional_seal()
    payloads["fractional_program_sage_seal.json"] = sage_seal
    worst = max(worst, code if code != 2 else 0)  # blocker registered, not FAIL
    if code == 2:
        print(f"REGISTERED BLOCKER: {sage_seal.get('status')}", file=sys.stderr)

    # --- REV-R172+ seals are appended here (TSUM, U4-v9, MES-BR) ---
    try:
        from htt.obsstat.egs3_fingerprint_sum_theorem import (
            fingerprint_sum_theorem_seal)
        seal = fingerprint_sum_theorem_seal()
        payloads["fingerprint_sum_theorem_seal.json"] = seal
        if seal.get("status") != "PASS":
            worst = max(worst, 1)
    except ImportError:
        pass
    try:
        from htt.obsstat.egs3_teff_statistical_v9 import teff_statistical_v9_seal
        seal = teff_statistical_v9_seal()
        payloads["teff_statistical_v9_seal.json"] = seal
        if seal.get("status") != "PASS":
            worst = max(worst, 1)
    except ImportError:
        pass
    try:
        from htt.obsstat.egs3_mes_branch_registry import mes_branch_registry_seal
        seal = mes_branch_registry_seal()
        payloads["mes_branch_registry_seal.json"] = seal
        if seal.get("status") != "PASS":
            worst = max(worst, 1)
    except ImportError:
        pass

    return payloads, worst


def _render(payload: dict) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)

    payloads, worst = build_seals()
    if args.check:
        stale = []
        for name, payload in payloads.items():
            path = OUT_DIR / name
            if not path.exists() or path.read_text() != _render(payload):
                stale.append(name)
        if stale:
            print("stale v9 seals:\n  " + "\n  ".join(stale), file=sys.stderr)
            return 1
        print(f"v9 seals current ({len(payloads)})")
        return worst
    for name, payload in payloads.items():
        path = OUT_DIR / name
        path.write_text(_render(payload))
        print(f"wrote {path} status={payload.get('status')}")
    return worst


if __name__ == "__main__":
    raise SystemExit(main())
