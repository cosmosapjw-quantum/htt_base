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
# insertion order matters: REPO must end up FIRST so `htt` resolves to the
# repo-root package (which carries htt.teff); htt/htt would shadow it.
for p in (REPO / "htt/htt", REPO / "htt", REPO):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

OUT_DIR = REPO / "docs/generated"
SAGE_SCRIPT = REPO / "sage/egs3_v9_fractional.sage"
KE_WOLFRAM_SCRIPT = REPO / "wolfram/ke_rotating_congruence.wls"


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


def wolfram_ke_frame_seal(sympy_anchors: dict | None) -> tuple[dict, int]:
    """Second-engine lane for the KE frame seal: run the independent Wolfram
    computation and enforce cross-engine equality of the exact rational
    anchors against the SymPy seal. Missing wolframscript is a registered
    blocker (exit 2), never silently substituted."""
    exe = shutil.which("wolframscript")
    if not exe or not KE_WOLFRAM_SCRIPT.exists():
        return {"status": "BLOCKED_WOLFRAM_UNAVAILABLE",
                "detail": "wolframscript not on PATH or "
                          "wolfram/ke_rotating_congruence.wls missing"}, 2
    code = (f'Print[ExportString[Get["{KE_WOLFRAM_SCRIPT}"], "RawJSON", '
            f'"Compact"->True]]')
    try:
        run = subprocess.run([exe, "-code", code], text=True,
                             capture_output=True, check=True, timeout=1200)
    except (OSError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired) as exc:
        detail = getattr(exc, "stderr", "") or repr(exc)
        return {"status": "BLOCKED_WOLFRAM_RUN_FAILED",
                "detail": str(detail)[-2000:]}, 2
    raw = run.stdout
    span = raw[raw.find("{"):raw.rfind("}") + 1]
    if not span:
        return {"status": "BLOCKED_WOLFRAM_NO_OUTPUT",
                "stdout": raw[-1000:]}, 2
    seal = json.loads(span)
    checks = dict(seal.get("checks", {}))
    cross = bool(sympy_anchors) and seal.get("anchors") == sympy_anchors
    checks["cross_engine_anchor_match_sympy"] = cross
    seal["checks"] = checks
    ok = checks and all(v is True for v in checks.values())
    seal["status"] = "PASS" if ok else "FAIL"
    return seal, (0 if ok else 1)


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
        from htt.obsstat.egs3_bianchi_v_dynamics import bianchi_v_dynamics_seal
        seal = bianchi_v_dynamics_seal()
        payloads["bianchi_v_dynamics_seal.json"] = seal
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
    # --- REV-R181: King-Ellis frame (items 1-7) + Wolfram second engine ---
    sympy_anchors = None
    try:
        from htt.obsstat.egs3_king_ellis_frame import king_ellis_frame_seal
        seal = king_ellis_frame_seal()
        payloads["king_ellis_frame_seal.json"] = seal
        sympy_anchors = seal["rational_point_anchor"]["values"]
        if seal.get("status") != "PASS":
            worst = max(worst, 1)
    except ImportError:
        pass
    if sympy_anchors is not None:
        wseal, code = wolfram_ke_frame_seal(sympy_anchors)
        payloads["king_ellis_frame_wolfram_seal.json"] = wseal
        worst = max(worst, code if code != 2 else 0)
        if code == 2:
            print(f"REGISTERED BLOCKER: {wseal.get('status')}",
                  file=sys.stderr)

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
