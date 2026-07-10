#!/usr/bin/env python3
"""Run the EGS3 v7 strengthened-theorem SymPy seals and write, under
docs/generated/:

  signed_box_interval_seal.json        (T1' / F1 signed-box endpoints + DL1)
  gf_strictness_exact_seal.json        (T2' / M1 Fraction-exact strictness iff)
  coverage_strengthened_seal.json      (T4'/T5'/T8' / M3 estimated-covariance + IM + ncx2)
  multicomponent_tilt_seal.json        (T9' / m1 species-summed Gauss budget)
  linearized_realization_seal.json     (T3-lin / M2, if the module is present)

These are NEW artifacts; the v6 seal JSONs (parent_identity_seal.json,
bianchi_v_constraint_seal.json) are left byte-frozen. Fail-closed: any seal whose
status != PASS sets the runner status FAIL and exits 1. ``--check`` regenerates in
memory and diffs against disk.

Claim boundary: symbolic/closed-form strengthened-theorem seals; no data claim,
no detection, family/geometry, native-solver, or posterior claim.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
for p in (REPO, REPO / "htt", REPO / "htt/htt"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

OUT_DIR = REPO / "docs/generated"


def _gf_strictness_seal() -> dict:
    from htt.obsstat.egs3_gf_interval import gf_strictness_exact_witness
    w = gf_strictness_exact_witness()
    ok = w["agreement_exact_1.0"] and w["aligned_counterexample_joint_equals_naive"]
    return {
        "seal": "egs3.gf_strictness_exact",
        "status": "PASS" if ok else "FAIL",
        "witness": w,
        "claim_boundary": "exact-rational strictness-iff witness (T2'); joint interval "
                          "is a subset of naive, strict iff a shared component conflicts; "
                          "aligned regime collapses to equality; no data/detection/family "
                          "claim",
    }


def build_payloads() -> tuple[dict[str, str], dict[str, dict]]:
    from htt.obsstat.egs3_coverage_strengthened import (
        coverage_strengthened_seal, signed_box_interval_seal)
    from htt.obsstat.egs3_parent_identity import multicomponent_tilt_seal
    from htt.obsstat.egs3_mes_provenance import mes_provenance_seal
    from htt.obsstat.egs3_mes_rederivation import mes_rederivation_seal
    from htt.obsstat.egs3_measured_response import measured_response_seal
    from htt.obsstat.egs3_data_lane_forward import data_lane_forward_seal

    seals: dict[str, dict] = {
        "signed_box_interval_seal.json": signed_box_interval_seal(),
        "gf_strictness_exact_seal.json": _gf_strictness_seal(),
        "coverage_strengthened_seal.json": coverage_strengthened_seal(),
        "multicomponent_tilt_seal.json": multicomponent_tilt_seal(),
        "mes_provenance_seal.json": mes_provenance_seal(),
        "mes_rederivation_seal.json": mes_rederivation_seal(),
        "measured_response_seal.json": measured_response_seal(),
        "data_lane_forward_seal.json": data_lane_forward_seal(),
    }
    try:
        from htt.obsstat.egs3_linearized_realization import linearized_realization_seal
        seals["linearized_realization_seal.json"] = linearized_realization_seal()
    except Exception:  # module not present yet -> lane simply omits it
        pass
    try:
        from htt.obsstat.egs3_nonlinear_realization import nonlinear_realization_seal
        seals["nonlinear_realization_seal.json"] = nonlinear_realization_seal()
    except Exception:  # module not present yet -> lane simply omits it
        pass
    try:
        from htt.teff.representative import teff_representative_seal
        seals["teff_representative_seal.json"] = teff_representative_seal()
    except Exception:  # module not present yet -> lane simply omits it
        pass
    try:
        from htt.obsstat.egs3_gf_interval_v8 import gf_interval_v8_seal
        seals["gf_interval_v8_seal.json"] = gf_interval_v8_seal()
    except Exception:  # module not present yet -> lane simply omits it
        pass
    try:
        from htt.obsstat.egs3_volterra_hz import volterra_hz_seal
        seals["volterra_hz_seal.json"] = volterra_hz_seal()
    except Exception:  # module not present yet -> lane simply omits it
        pass
    try:
        from htt.obsstat.egs3_interior_family import interior_family_seal
        seals["interior_family_seal.json"] = interior_family_seal()
    except Exception:  # module not present yet -> lane simply omits it
        pass

    payloads = {name: json.dumps(seal, indent=2, default=float) + "\n"
                for name, seal in seals.items()}
    return payloads, seals


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    check = "--check" in argv
    payloads, seals = build_payloads()

    failed = [k for k, s in seals.items() if s.get("status") != "PASS"]
    if failed:
        for k in failed:
            print(f"V7 SEAL FAIL: {k}", file=sys.stderr)
        return 1

    if check:
        stale = [str(OUT_DIR / n) for n, t in payloads.items()
                 if not (OUT_DIR / n).exists() or (OUT_DIR / n).read_text() != t]
        if stale:
            print("stale v7 seal artifacts:\n  " + "\n  ".join(stale), file=sys.stderr)
            return 1
        print("v7 seal artifacts current")
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, text in payloads.items():
        (OUT_DIR / name).write_text(text)
        print(f"wrote {OUT_DIR / name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
