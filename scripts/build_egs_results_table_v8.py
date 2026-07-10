#!/usr/bin/env python3
"""v8-update successor results table (NEW artifact pair).

The v7-era ``docs/generated/egs_results_table.json`` is byte-frozen (its SHA is
embedded in the frozen v7 report MANIFEST), so the v8-update rows land in the
successor pair ``egs_results_table_v8.{json,md}``: the frozen table's rows are
inherited VERBATIM by importing ``_rows()`` from the untouched v7-era builder,
and the v8-update rows are appended. Same status vocabulary; no detection /
Bianchi-class / geometry / native-solver claim is made or implied.

FORCED DEVIATION (documented): the house rule "append rows in
build_egs_results_table.py" cannot be followed without breaking the v7
byte-freeze; the successor-artifact pattern is the freeze-preserving
execution of that rule.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
GEN = REPO_ROOT / "docs/generated"
OUT_JSON = GEN / "egs_results_table_v8.json"
OUT_MD = GEN / "egs_results_table_v8.md"

MATH, GR, DATA = "math_stat", "gr_boltzmann", "data_interpretation"


def _v7_builder():
    spec = importlib.util.spec_from_file_location(
        "build_egs_results_table", REPO_ROOT / "scripts/build_egs_results_table.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["build_egs_results_table"] = mod
    spec.loader.exec_module(mod)
    return mod


def _r(tid, axis, statement, key, status, evidence):
    return {"theorem_id": tid, "axis": axis, "statement": statement,
            "key_result": key, "status": status, "evidence": evidence}


def _v8_rows() -> list[dict]:
    return [
        _r("EGS3-E4b", MATH,
           "T2'' signed-numerator exact quotient successor: v7 latent sign defect fixed by full corner enumeration; domain documented; negative-numerator path exercised",
           "frozen [-3/5,-19/39] vs true [-3/4,-19/49]; 200/200 bit-exact on the documented domain; containment 400/400",
           "proven_symbolic", "gf_interval_v8_seal.json"),
        _r("EGS3-B2b", GR,
           "Volterra depth-memory closed under real H(z): kernel exactly (a_s/a_t)^3 for ANY expansion history (e-fold clock)",
           "EdS limit (s/t)^2 symbolic; LambdaCDM Volterra==RK4 to 1.6e-7; e-fold Gronwall envelope",
           "proven_symbolic", "volterra_hz_seal.json"),
        _r("EGS3-PSDb", MATH,
           "PSD-cone dual independent review: claim side clean; math P1 (linear-vs-squared shear bracket units) + 3 P2 repaired and re-verified",
           "SIGN_OFF x2; discriminating shell gate; Wolfram seal schema v2 (Omega_k free)",
           "proven_gate", "psd_cone_review_signoff.json + egs3_psd_cone_proof.json"),
        _r("EGS2-B1b", GR,
           "semi-native shear transfer cross-checked against the REAL CAMB recombination visibility (exit gate discharged)",
           "super-horizon floor 0.632456 identical; finite-k floors 0.0957 vs 0.0959 (0.2%); band peak tracks k*chi_star",
           "proven_gate", "seminative_camb_crosscheck_seal.json"),
        _r("EGS3-G11", GR,
           "T3-int: connected two-segment exact family realizes EVERY interior x_C of [11/100,17/100]; Bianchi V group-invariant curl derived; four sectors simultaneously nonzero witness",
           "junction exact at 3/20; slaving |curl v|^2 = a^2 v_perp^2 (derived obstruction to free box dial-in)",
           "proven_symbolic", "interior_family_seal.json + egs3_v8_interior_family_proof.json"),
        _r("EGS3-U1", MATH,
           "beta-channel correspondence: s = tanh(beta) exact under the antipodal two-point reduction; R3-1 = -(3/4) t + O(t^2) on the comparator tilt coordinate (antipodal-specific)",
           "exact closed forms R3(t), R5(t); R4 == 1 identically; single-species pin -(3/2)",
           "proven_symbolic", "teff_unification_seal.json + egs3_v8_unification_proof.json"),
        _r("EGS3-U2", MATH,
           "MES-registry ceilings on the Teff fingerprints: proved envelopes (3/2)s^2, (5/2)s^2; exact rational ceilings at eps1; MES ordering carried by the ceiling map",
           "|R3-1| <= 2.283e-6, |R5-1| <= 3.804e-6; CF4 rapidity contained in both channels (1.94e-6)",
           "proven_symbolic", "teff_unification_seal.json"),
        _r("EGS3-U3", MATH,
           "rank-deficiency schema correspondence: comparator channel response and Teff retained-moment response are two exact instances of one linear-response schema",
           "rank 2 both sides; null kinds carried; p=4 selector annihilates both enrichment directions exactly",
           "proven_symbolic", "unification_schema_seal.json"),
        _r("EGS3-U4", MATH,
           "statistical closure over the Teff fingerprints: IM coverage on the identified interval of the nonidentified mixing + Hotelling calibration of the estimated-covariance joint",
           "coverage 0.936-0.956 (floor 0.927); naive chi^2 size 0.153 vs Hotelling 0.064 (display mixings, disclosed)",
           "measured_synth", "teff_statistical_seal.json"),
        _r("TEFF-T1", GR,
           "transport application: BGK multigroup reference vs the closed-form representative; retained moments machine-conserved; insertion-resolved residual monitored",
           "honest answer: residual == unretained error BY CONSTRUCTION in the single-mode toy; NOT Boltzmann-closure evidence",
           "measured_synth", "teff_transport_application_seal.json"),
        _r("TEFF-P1", MATH,
           "Rust twin parity: 3 a_BE = pi^4/15, 3 a_FD = 7 pi^4/120 exact vs spectral.rs; Gram closed forms zeta(3)/(3 zeta(4)), zeta(2)/(2 zeta(3)); cargo lane live",
           "cargo test --lib teff: 153 passed / 0 failed (CARGO_LIVE)",
           "proven_gate", "teff_rust_parity_seal.json"),
        _r("K5-V8", DATA,
           "K5 card v8 extension: deterministic Teff fingerprint row from the SAME CF4 rapidity as Omega_tilt; registered-external model-conditional vorticity/shear cross-checks; Omega_k documented external null",
           "fingerprint 1.94e-6 < MES ceiling 2.28e-6; observational_claim_allowed stays False",
           "blocked", "k5_cf4_identified_interval_card_v8.json (plugin firewall intact)"),
    ]


def _payload() -> dict:
    v7 = _v7_builder()
    rows = v7._rows() + _v8_rows()
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    base = v7._payload()
    return {
        "schema": "htt.egs.results_table.v8",
        "based_on_frozen_v7_table": "docs/generated/egs_results_table.json "
                                    "(byte-frozen; rows inherited verbatim via "
                                    "the untouched v7-era builder)",
        "claim_tier": base["claim_tier"],
        "family_identification": False,
        "native_solver_result": False,
        "axes": base["axes"],
        "status_counts": counts,
        "rows": rows,
        "claim_boundary": base["claim_boundary"],
        "blockers_open": base["blockers_open"],
        "v8_update_note": "v8-update rows (EGS3-E4b/B2b/PSDb, EGS2-B1b, "
                          "EGS3-G11, EGS3-U1..U4, TEFF-T1/P1, K5-V8) appended; "
                          "the unification lane couples the MES registry, the "
                          "graded comparator and the active Teff lane into one "
                          "sealed system; no claim-envelope change",
    }


_AXIS_LABEL = {MATH: "Math/Stat", GR: "GR/Boltzmann", DATA: "Data"}


def _markdown(payload: dict) -> str:
    lines = [
        "# Consolidated EGS-type results table (v8-update successor)",
        "",
        "Auto-generated by `scripts/build_egs_results_table_v8.py`; inherits the",
        "byte-frozen v7 table rows verbatim and appends the v8-update rows.",
        "Conditional theorems + synthetic mechanics only; no detection,",
        "Bianchi-class/geometry, or native-solver claim.",
        "",
        f"Status counts: {payload['status_counts']}",
        "",
        "| Theorem | Axis | Statement | Key result | Status | Evidence |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append("| {tid} | {axis} | {st} | {key} | `{status}` | {ev} |".format(
            tid=row["theorem_id"], axis=_AXIS_LABEL[row["axis"]],
            st=row["statement"], key=row["key_result"], status=row["status"],
            ev=row["evidence"]))
    lines += ["", "Open blockers: " + ", ".join(f"`{b}`" for b in payload["blockers_open"]), ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    payload = _payload()
    exp_json = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    exp_md = _markdown(payload) + "\n"
    if args.check:
        stale = []
        for path, content in ((OUT_JSON, exp_json), (OUT_MD, exp_md)):
            if (path.read_text() if path.exists() else None) != content:
                stale.append(path.relative_to(REPO_ROOT).as_posix())
        if stale:
            print("stale v8 results table:", *stale, sep="\n  - ")
            return 1
        print("v8 results table up to date")
        return 0
    OUT_JSON.write_text(exp_json)
    OUT_MD.write_text(exp_md)
    print(f"wrote {OUT_JSON.relative_to(REPO_ROOT)} + {OUT_MD.relative_to(REPO_ROOT)} ({len(payload['rows'])} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
