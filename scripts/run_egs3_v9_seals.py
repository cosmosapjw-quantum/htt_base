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
KE_DYN_WOLFRAM_SCRIPT = REPO / "wolfram/ke_dynamics.wls"
OMK_WOLFRAM_SCRIPT = REPO / "wolfram/omega_k_reopening.wls"


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


def _run_wolfram(script: Path) -> tuple[dict | None, dict]:
    """Run a .wls returning an Association; missing engine is a registered
    blocker (exit-2 semantics), never silently substituted."""
    exe = shutil.which("wolframscript")
    if not exe or not script.exists():
        return None, {"status": "BLOCKED_WOLFRAM_UNAVAILABLE",
                      "detail": f"wolframscript not on PATH or {script} "
                                "missing"}
    code = (f'Print[ExportString[Get["{script}"], "RawJSON", '
            f'"Compact"->True]]')
    try:
        run = subprocess.run([exe, "-code", code], text=True,
                             capture_output=True, check=True, timeout=1200)
    except (OSError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired) as exc:
        detail = getattr(exc, "stderr", "") or repr(exc)
        return None, {"status": "BLOCKED_WOLFRAM_RUN_FAILED",
                      "detail": str(detail)[-2000:]}
    raw = run.stdout
    span = raw[raw.find("{"):raw.rfind("}") + 1]
    if not span:
        return None, {"status": "BLOCKED_WOLFRAM_NO_OUTPUT",
                      "stdout": raw[-1000:]}
    return json.loads(span), {}


def wolfram_ke_frame_seal(sympy_anchors: dict | None) -> tuple[dict, int]:
    """Second-engine lane for the KE frame seal: independent Wolfram
    computation + exact rational cross-engine anchor equality."""
    seal, blocked = _run_wolfram(KE_WOLFRAM_SCRIPT)
    if seal is None:
        return blocked, 2
    checks = dict(seal.get("checks", {}))
    checks["cross_engine_anchor_match_sympy"] = (
        bool(sympy_anchors) and seal.get("anchors") == sympy_anchors)
    seal["checks"] = checks
    ok = checks and all(v is True for v in checks.values())
    seal["status"] = "PASS" if ok else "FAIL"
    return seal, (0 if ok else 1)


def wolfram_ke_dynamics_seal(sympy_seal: dict | None) -> tuple[dict, int]:
    """Second-engine lane for KE-DYN: Wolfram derives the SAME rotating
    system independently and NDSolve-integrates it in one script; the
    runner cross-checks the development summaries against the SymPy
    seal (tolerances, not bit-equality: two independent integrators)."""
    seal, blocked = _run_wolfram(KE_DYN_WOLFRAM_SCRIPT)
    if seal is None:
        return blocked, 2
    checks = dict(seal.get("checks", {}))
    cross = False
    if sympy_seal is not None:
        sv = sympy_seal["rotating_development_bianchi_v_dust"]
        wv = seal.get("type_v_development", {})
        try:
            rel = abs(wv["omega2_final"] - sv["omega2_final"]) \
                / abs(sv["omega2_final"])
            tilt_rel = max(
                abs(wv["tilt_final"][i] - sv["tilt_final"][i])
                / max(abs(sv["tilt_final"][i]), 1e-12) for i in range(2))
            cross = rel < 1e-4 and tilt_rel < 1e-4
            checks["cross_engine_omega2_rel"] = float(rel) < 1e-4
            checks["cross_engine_tilt_rel"] = float(tilt_rel) < 1e-4
        except (KeyError, TypeError, ZeroDivisionError):
            cross = False
    checks["cross_engine_development_match_sympy"] = bool(cross)
    seal["checks"] = checks
    ok = checks and all(v is True for v in checks.values())
    seal["status"] = "PASS" if ok else "FAIL"
    return seal, (0 if ok else 1)


def wolfram_omk_seal(sympy_seal: dict | None) -> tuple[dict, int]:
    """Second-engine lane for OMK-REOPEN: independent Wolfram derivation +
    NDSolve; the runner cross-checks the slaving plateau and the deep-run
    vacuum-anchor approach against the SymPy seal (tolerances: two
    independent integrators)."""
    seal, blocked = _run_wolfram(OMK_WOLFRAM_SCRIPT)
    if seal is None:
        return blocked, 2
    checks = dict(seal.get("checks", {}))
    cross = False
    if sympy_seal is not None:
        try:
            dyn = sympy_seal["dynamical_verification"]
            sp_plateau = dyn["lrs3_dust"]["plateau_ratio_mean"]
            wl_plateau = seal["metric_lane"]["plateau_ratio_mean"]
            sp_anchor = dyn["reduced_lane"]["late_time_vacuum_anchor"]
            wl_deep = seal["deep_lane"]
            cross = (abs(wl_plateau - sp_plateau) / abs(sp_plateau) < 1e-3
                     and abs(wl_deep["sigma_final"]
                             - sp_anchor["sigma_final"]) < 1e-6
                     and abs(wl_deep["k_final"]
                             - sp_anchor["k_final"]) < 1e-6)
        except (KeyError, TypeError, ZeroDivisionError):
            cross = False
    checks["cross_engine_match_sympy"] = bool(cross)
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
    # --- REV-R182: King-Ellis dynamics (items 8-10) + Wolfram NDSolve ---
    dyn_seal = None
    try:
        from htt.obsstat.egs3_king_ellis_dynamics import (
            king_ellis_dynamics_seal)
        dyn_seal = king_ellis_dynamics_seal()
        payloads["king_ellis_dynamics_seal.json"] = dyn_seal
        if dyn_seal.get("status") != "PASS":
            worst = max(worst, 1)
    except ImportError:
        pass
    if dyn_seal is not None:
        wseal, code = wolfram_ke_dynamics_seal(dyn_seal)
        payloads["king_ellis_dynamics_wolfram_seal.json"] = wseal
        worst = max(worst, code if code != 2 else 0)
        if code == 2:
            print(f"REGISTERED BLOCKER: {wseal.get('status')}",
                  file=sys.stderr)
    # --- REV-R184: Omega_k higher-order re-opening transfer + ceiling ---
    omk_seal = None
    try:
        from htt.obsstat.egs3_omega_k_reopening import (
            omega_k_reopening_seal)
        omk_seal = omega_k_reopening_seal()
        payloads["omega_k_reopening_seal.json"] = omk_seal
        if omk_seal.get("status") != "PASS":
            worst = max(worst, 1)
    except ImportError:
        pass
    if omk_seal is not None:
        wseal, code = wolfram_omk_seal(omk_seal)
        payloads["omega_k_reopening_wolfram_seal.json"] = wseal
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
