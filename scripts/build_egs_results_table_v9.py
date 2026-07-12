#!/usr/bin/env python3
"""v9 (Seventh Revision) successor results table (NEW artifact pair).

The v7 table and the v8 successor are both hash-frozen in shipped packages,
so the v9 rows land in ``egs_results_table_v9.{json,md}``: the v8 successor's
rows are inherited VERBATIM by importing its builders (which themselves
inherit the frozen v7 rows), and the v9-cycle rows are appended. Same status
vocabulary; no detection / Bianchi-class / geometry / native-solver claim.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
GEN = REPO_ROOT / "docs/generated"
OUT_JSON = GEN / "egs_results_table_v9.json"
OUT_MD = GEN / "egs_results_table_v9.md"

MATH, GR, DATA = "math_stat", "gr_boltzmann", "data_interpretation"


def _v8_builder():
    spec = importlib.util.spec_from_file_location(
        "build_egs_results_table_v8",
        REPO_ROOT / "scripts/build_egs_results_table_v8.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["build_egs_results_table_v8"] = mod
    spec.loader.exec_module(mod)
    return mod


def _r(tid, axis, statement, key, status, evidence):
    return {"theorem_id": tid, "axis": axis, "statement": statement,
            "key_result": key, "status": status, "evidence": evidence}


def _v9_rows() -> list[dict]:
    return [
        _r("EGS3-T2G", MATH,
           "General fractional-program interval theorem: containment, vertex "
           "attainment, per-endpoint diagonal-attainment criterion, "
           "argmin/argmax corollary on the N>0 domain; P36 and the T2' "
           "per-endpoint iff RETRACTED (refuting instance inside the stated "
           "hypotheses)",
           "counterexample joint [0,1/2] vs product [0,1]; 400-draw exact "
           "survey with forced N_min=0 third; sign test defeated 81x there; "
           "Sage QQ+PPL Charnes-Cooper 15/15",
           "proven",
           "fractional_program_exact_seal.json; fractional_program_sage_seal.json"),
        _r("EGS3-TSUM", MATH,
           "Two-temperature fingerprint sum bound R3+R5 >= 2 with equality "
           "iff s=0 (promotion of the v8 numeric certificate)",
           "exact factorization mu3*mu5 - mu4^2 = s^2 (1-s^2)^3 + AM-GM",
           "proven",
           "fingerprint_sum_theorem_seal.json"),
        _r("EGS3-U4v9", MATH,
           "Fingerprint statistics rerun with pre-registered acceptance, "
           "disclosed seeds, Wilson CIs, and exact-regime witnesses; "
           "finite-sample deviations reported, not claimed away",
           "boundary coverage deviation -0.0054 (band 0.01); fingerprint "
           "Hotelling size 0.0678 (reported); Gaussian/Wishart exact witness "
           "size 0.05025 (CI contains alpha); known-se IM exact",
           "measured",
           "teff_statistical_v9_seal.json"),
        _r("EGS3-MESBR", MATH,
           "MES coefficient branch registry (MES-G verified geodesic / "
           "MES-NG unverified / accel WITHHELD) + eps1 attribution triple; "
           "registered values unchanged",
           "eps1 = solar kinematic dipole (rel diff 1.1e-5); ceilings "
           "1.3087e-6 / 2.5369e-5 (hybrid, disclosed) / 3.379e-13 "
           "(SAG-consistent); eps1 term carries 99.05%/99.99% of B_omega",
           "registered_external",
           "mes_branch_registry_seal.json"),
        _r("K5-V9", DATA,
           "K5/CF4 identified-interval card v9: three attribution-conditional "
           "W^2 ceilings x two signed-curvature branches; no branch promoted",
           "6 labeled intervals; lower endpoint keyed to -U_W; "
           "observational_claim_allowed False",
           "diagnostic_only",
           "k5_cf4_identified_interval_card_v9.json"),
        _r("EXT-DESI", DATA,
           "DESI DR1 BGS number-count dipole lane (Omega_tilt-sector cross-"
           "check): randoms downloaded; window-corrected overdensity dipole "
           "delta=(D-alpha R)/(alpha R), linear D=3<delta n_hat>_R on NGC+SGC "
           "(fsky 0.28) = 9.49e-3 -- a 224x suppression of the raw footprint "
           "value (2.13) down to the kinematic scale ~7e-3",
           "window-corrected D=9.49e-3, dir (l,b)=(172.5,-44.7); mixes local "
           "BGS clustering with the kinematic dipole; mask-coupling amplitude "
           "bias + significance need release-matched mocks (residual gate)",
           "measured_diagnostic",
           "external_lanes_seal.json; desi_dipole_card.json"),
        _r("EXT-ACT", DATA,
           "ACT DR6 CMB-lensing auto-bandpower lane (independent-instrument "
           "isotropy cross-check): the released kappa a_lm (lmax=4000) + N_L "
           "load with a raw masked auto-power readout; a low-multipole kappa "
           "isotropy statistic is reconstruction-mean-field dominated",
           "auto-bandpower computed; low-ell isotropy null needs the ACT "
           "lensing simulation ensemble (mean field + N0/N1)",
           "blocked",
           "external_lanes_seal.json (BLOCKED_MISSING_ACT_LENSING_SIMS)"),
        _r("EXT-JWST", DATA,
           "JWST distance anchors (14 Cepheid/TRGB/maser, CF4-matched) feed "
           "the Omega_tilt survey-design forecast",
           "connected via jwst_cf4_crossmatch -> joint_pv_cmb_forecast "
           "(labelled forecast, not a measurement)",
           "diagnostic_only",
           "external_lanes_seal.json; jwst_cf4_anchors.json"),
        _r("KE-FRAME", GR,
           "King-Ellis items 1-7: exact tilted-frame kinematics + "
           "constraint algebra, dual engine (SymPy + independent Wolfram, "
           "exact rational cross-engine anchors); contracted Gauss "
           "identity DERIVED (R3 = 2 G_uu - (2/3)Theta^2 + sigma^2 + "
           "omega^2, stated projection definition)",
           "Frobenius omega[n]=0 and aligned omega[u]=0 exact; identity "
           "verified on five configurations incl. two rotating; standard "
           "3-curvature reproduced in integrable limits",
           "proven",
           "king_ellis_frame_seal.json; king_ellis_frame_wolfram_seal.json"),
        _r("KE-OBS", GR,
           "Exact vorticity classification of group-invariant tilted "
           "congruences: omega_ab omega^ab = (S^2 sin^2 phi/2)"
           "[S cos phi (H1-H2) - cosh(b) c/a1]^2; CORRECTS the blanket "
           "'irrotational at Omega_k=0' reading (oblique tilt carries "
           "O(v^2) kinematic vorticity; slaving relation reproduced at "
           "leading order)",
           "type-I oblique form (S^4/2) sin^2 phi cos^2 phi (H1-H2)^2; "
           "type-V codimension-1 cancellation surface; n-frame Frobenius "
           "and the W^2 withdrawal untouched",
           "proven",
           "king_ellis_frame_seal.json"),
        _r("KE-DYN", GR,
           "King-Ellis items 8-10: exact u-frame conservation; "
           "Raychaudhuri derived by undetermined coefficients; GENUINE "
           "rotating perfect-fluid development at Omega_k>0 (type V, "
           "constraints monitored, omega^2[u]>0, dust+radiation, SymPy "
           "RK45 + Wolfram NDSolve); Omega_k=0 DOUBLY obstructed (single "
           "stream: G_ti=0 momentum constraint; antipodal pair: dynamical "
           "irrotationality, Killing+Euler conserve the tilt-covector "
           "direction)",
           "lower-endpoint W^2 withdrawal upgraded from constraint-level "
           "to DYNAMICAL within the group-invariant perfect-fluid class; "
           "radiation drift = gamma=4/3 center-manifold law +(2/3)beta^2",
           "proven",
           "king_ellis_dynamics_seal.json; "
           "king_ellis_dynamics_wolfram_seal.json"),
        _r("OMK-REOPEN", GR,
           "Higher-order anisotropic-Omega_k re-opening transfer: exact "
           "curvature->shear slaving on the LRS Bianchi III / "
           "Kantowski-Sachs class (source coefficient exactly -1; "
           "Sigma = kappa Delta Omega_k with kappa = -1/(2+q) exact, "
           "dual engine SymPy + Wolfram NDSolve ~5e-12); finite "
           "|Delta Omega_k| ceilings on a NEW labeled card",
           "kappa: dust -2/5, radiation -1/3, vacuum anchor -2/3 "
           "(two-sided via KS mirror); ceilings: MES registered "
           "6.4e-3/7.7e-3, MES cosmological 4.1e-5/4.9e-5, Saadeh "
           "model-conditional 1.5e-6/1.8e-6; instantaneous structural "
           "null UNTOUCHED; frozen U_k plugin NOT modified; "
           "attribution+class-conditional, nothing promoted",
           "proven",
           "omega_k_reopening_seal.json; "
           "omega_k_reopening_wolfram_seal.json; "
           "k5_omega_k_ceiling_card.json"),
        _r("MES-REFREEZE", GR,
           "MES vorticity-ceiling re-freeze: the "
           "primary-source raw MESa bounds reduce (C1/C2, SymPy + Wolfram) "
           "to geodesic sigma (5/3,3,3/7) + omega (10/3,2/15,0) + no accel; "
           "the previously-registered non-geodesic omega/accel are MESb "
           "print-only (no accessible source); e1 = 0 is the SAG "
           "observer-motion convention, admissibility-checked by the "
           "hierarchy-preservation theorem",
           "e1_crit = 43 e2/25 + 9 e3/35 = 7.68e-6 (observed dipole "
           "1.23e-3 exceeds it, so the full-dipole geodesic ceiling is "
           "excluded); e1 = 0 is the SAG convention; re-frozen W2_max = 3.3789e-13 (from 1.3087e-6, "
           "6.59-OOM tightening) = branch-registry sag_consistent; frozen "
           "anchor byte-identical (successor pattern); x_C untouched",
           "re_frozen",
           "mes_geodesic_refreeze_seal.json; "
           "mes_geodesic_refreeze_wolfram_seal.json"),
        _r("MES-MESB-TRACE", GR,
           "MESb (print-only) web-traced via three archived accessible "
           "primary sources; the in-house non-geodesic omega (3/4,2,2/7) / "
           "accel (3/4,1,3/14) REFUTED (in-house numbering, no accessible "
           "source; exceed the companion's own reduced bound under its "
           "assumption alpha x 10^-5 = max(eps2,eps3)); geodesic omega "
           "(10/3,2/15,0) triply primary-sourced and re-adopted",
           "five refute-prompted adversarial lanes: geodesic anchor "
           "3.3789e-13 SURVIVES (exact, MESa eq 60 + SAG eq 4 + C1/C2), "
           "companion non-geodesic envelope PLAUSIBLE order-of-magnitude "
           "(faithful (3/2)eps3^2 = 5.52e-11; COBE alpha~1 -> 1.50e-10); "
           "manuscript ch04 corrected to the geodesic result + conditional "
           "ordering (B_sigma > B_omega iff e1 < e1_crit)",
           "web_traced_refuted_readopted",
           "mesb_web_trace_seal.json; mesb_web_trace_wolfram_seal.json; "
           "PROVENANCE_M4b.md"),
        _r("EGS3-G12", GR,
           "T3 family re-scoped onto the three-level sharpness taxonomy; "
           "lower-endpoint W^2 withdrawn to constraint-unverified "
           "(Frobenius: hypersurface-orthogonal slice normal; antipodal pair "
           "cancels energy flux only); upper endpoint keeps level 2",
           "constraint-surface endpoint witnesses, not exact cosmologies; "
           "level 3 (dynamics) unreached; ten-step rotating-congruence "
           "program registered",
           "reclassified",
           "THEOREM_REGISTRY.yaml; t3_king_ellis.yaml"),
    ]


# status/annotation overlay for inherited rows whose claims the v9 registry
# retracted or superseded (adversarial-audit finding, REV-R179): the frozen
# v7/v8 table ARTIFACTS keep their bytes; this successor table must not
# assert retracted content as live.
_SUPERSESSION_OVERLAY = {
    "EGS3-E4": ("retracted_superseded",
                " [RETRACTED by T2G: refuting instance inside the stated"
                " hypotheses; see THEOREM_REGISTRY.yaml P36]"),
    "EGS3-G2": ("retracted_superseded",
                " [RETRACTED by T2G: the per-endpoint iff fails on"
                " N_min=0/signed-numerator domains; the seal survives as"
                " the existence-level lemma L-T2-EXIST on the strictly"
                " positive-numerator domain]"),
    "EGS3-E1": (None, " [SUPERSEDED by T1'/T3-full per"
                      " THEOREM_REGISTRY.yaml (P26/P31); content subsumed]"),
    "EGS3-E2": (None, " [SUPERSEDED by T4'/T5' per THEOREM_REGISTRY.yaml"
                      " (P35); content subsumed]"),
}


def _apply_overlay(rows: list[dict]) -> list[dict]:
    out = []
    for row in rows:
        row = dict(row)
        status, badge = _SUPERSESSION_OVERLAY.get(row["theorem_id"],
                                                  (None, None))
        if badge:
            row["statement"] = row["statement"] + badge
        if status:
            row["status"] = status
        out.append(row)
    return out


def _payload() -> dict:
    v8 = _v8_builder()
    rows = _apply_overlay(v8._payload()["rows"]) + _v9_rows()
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    base = v8._payload()
    return {
        "schema": "htt.egs.results_table.v9",
        "based_on_frozen_tables": "egs_results_table.json (v7, byte-frozen) "
                                  "+ egs_results_table_v8.json (v8, "
                                  "hash-frozen); rows inherited with a "
                                  "supersession overlay on EGS3-E1/E2/E4/G2 "
                                  "(registry-retracted or superseded content "
                                  "must not print as live; REV-R179)",
        "claim_tier": base["claim_tier"],
        "family_identification": False,
        "native_solver_result": False,
        "axes": base["axes"],
        "status_counts": counts,
        "rows": rows,
        "claim_boundary": base["claim_boundary"],
        "blockers_open": base["blockers_open"],
        "v9_note": "v9 rows (EGS3-T2G/TSUM/U4v9/MESBR, K5-V9, EGS3-G12) "
                   "appended per the 2026-07-10 review-response cycle; "
                   "KE-FRAME/KE-OBS/KE-DYN rows added by the executed "
                   "ten-item rotating-congruence program (REV-R181/R182); "
                   "P36/T2' retractions and the P26/P31/P35 supersessions "
                   "are carried by THEOREM_REGISTRY.yaml; no claim-envelope "
                   "change",
    }


_AXIS_LABEL = {MATH: "Math/Stat", GR: "GR/Boltzmann", DATA: "Data"}


def _markdown(payload: dict) -> str:
    lines = ["# EGS consolidated results table (v9 successor)", "",
             f"Rows: {len(payload['rows'])}; status counts: "
             + ", ".join(f"{k}={v}" for k, v in
                         sorted(payload["status_counts"].items())), "",
             "| ID | Axis | Statement | Key result | Status | Evidence |",
             "|---|---|---|---|---|---|"]
    for row in payload["rows"]:
        lines.append(
            f"| {row['theorem_id']} | {_AXIS_LABEL.get(row['axis'], row['axis'])} "
            f"| {row['statement']} | {row['key_result']} | {row['status']} "
            f"| {row['evidence']} |")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    payload = _payload()
    exp_json = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    exp_md = _markdown(payload)
    if args.check:
        stale = [str(p) for p, c in ((OUT_JSON, exp_json), (OUT_MD, exp_md))
                 if not p.exists() or p.read_text() != c]
        if stale:
            print("stale v9 results table:\n  " + "\n  ".join(stale),
                  file=sys.stderr)
            return 1
        print("v9 results table current")
        return 0
    OUT_JSON.write_text(exp_json)
    OUT_MD.write_text(exp_md)
    print(f"wrote {OUT_JSON} ({len(payload['rows'])} rows)\nwrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
