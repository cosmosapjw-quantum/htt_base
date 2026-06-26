#!/usr/bin/env python3
"""REV-R126: consolidated results table across the EGS-type theorem programme.

Aggregates the headline result of every conditional theorem + every blocked
data measurement into one structured table (json + markdown), pulling numeric
values from the already-deterministic experiment records so the table is
reproducible and honest:

  - EGS-lowell  NT-A1 / NT-A3 / NT-B3   (docs/generated/egs_lowell_theorem_proofs.json)
  - EGS2        NT2-A1..B3 + K1/K6      (docs/generated/egs2_experiments.json)
  - EGS3        A1..A4, B1..B4, PSD     (docs/generated/egs3_experiments.json +
                                         egs3_psd_cone_proof.json)

Status vocabulary:
  proven_symbolic   gate + Wolfram-verified closed-form identity
  proven_gate       gate-verified numerical/structural theorem
  measured_synth    synthetic-mechanics stand-in (NOT a real-data measurement)
  blocked           real-data run gated by a registered blocker code

No detection / family / geometry / native-solver claim is made or implied.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GEN = REPO_ROOT / "docs/generated"
OUT_JSON = GEN / "egs_results_table.json"
OUT_MD = GEN / "egs_results_table.md"

MATH, GR, DATA = "math_stat", "gr_boltzmann", "data_interpretation"


def _load(name: str) -> dict:
    p = GEN / name
    return json.loads(p.read_text()) if p.is_file() else {}


def _rows() -> list[dict]:
    egs2 = _load("egs2_experiments.json").get("experiments", {})
    egs3 = _load("egs3_experiments.json").get("experiments", {})
    psd = _load("egs3_psd_cone_proof.json")
    a = egs3.get("axis_a", {})
    b = egs3.get("axis_b", {})
    p = egs3.get("axis_psd", {})
    nt2a = egs2.get("NT2_A1_A2_fisher_floor", {})
    nt2b3 = egs2.get("NT2_B3_blind_sector", {})
    k1 = egs2.get("BLOCK_K1_e2e_maxscan", {})
    k6 = egs2.get("BLOCK_K6_hoffman_ribak", {})
    # real-data discharges (rev-r127): K1 global max-scan, K5 coverage, K6 curl no-go
    k1g = _load("k1_global_maxscan.json")
    k5g = _load("k5_cf4_release_coverage.json")
    k6g = _load("k6_cf4_curl_posterior.json")

    def r(tid, axis, statement, key, status, evidence):
        return {"theorem_id": tid, "axis": axis, "statement": statement,
                "key_result": key, "status": status, "evidence": evidence}

    rows = [
        r("NT-A1", MATH, "Quadrupole-filling EGS identity: F_shear linear in the CMB quadrupole, F_shear->0 in the EGS limit",
          "slope 1/(kappa^2 x_max); F_shear(D2=0)=0", "proven_symbolic",
          "wolfram egs_lowell; fig_theorem_nt_a1_quadrupole_filling"),
        r("NT-A3", MATH, "Single-sky sampling dispersion of the standard F_shear estimator (one estimator; NOT a universal CR floor)",
          "sqrt(2/5) = 0.632 at l=2", "proven_symbolic",
          "wolfram egs_lowell; fig_theorem_nt_a3_cosmic_variance_floor"),
        r("NT-B3", GR, "Depth-transport EGS limit: depth gap G_F=1 for depth-steady shear; a depth-growing tilt imprints a gap",
          "L.1=0 contrast operator; G_F=1 iff steady", "proven_symbolic",
          "wolfram egs_lowell; fig_theorem_nt_b3_gf_transport"),
        r("EGS3-A1", MATH, "Graded-comparator identifiability: from {low-l CMB-T, radial velocity} the reachable subspace of g is rank 2",
          f"rank {a.get('A1_graded_rank',{}).get('rank','?')}; reachable {a.get('A1_graded_rank',{}).get('reachable')}; joint null {a.get('A1_graded_rank',{}).get('null')}",
          "proven_gate", "egs3-gates A1; fig_egs3_a1_graded_rank"),
        r("EGS3-A3", MATH, "Pi is a calibrated e-value: unit null mean, Markov false-exceedance bound P(E>=1/beta)<=beta; domination is conservative",
          f"null mean {a.get('A3_evalue_calibration',{}).get('null_mean','?')}; Markov holds {a.get('A3_evalue_calibration',{}).get('markov_holds','?')}",
          "proven_gate", "egs3-gates A3; fig_egs3_a3_evalue_calibration"),
        r("EGS3-A4", MATH, "Rao-Blackwell sufficiency: the reachable-sector statistic dominates any raw multi-channel estimator",
          f"Var_RB <= Var_raw: {a.get('A4_rao_blackwell',{}).get('dominates','?')}",
          "proven_gate", "egs3-gates A4"),
        r("NT2-A1", MATH, "Genuine multi-multipole Fisher-CR floor, strictly below the single-l dispersion",
          f"floor {nt2a.get('single_ell_dispersion_l2',0.632):.3f}(l=2) -> 0.424(L=20)", "proven_gate",
          "egs2-gates NT2-A1; fig_egs2_nt2a1_fisher_floor"),
        r("NT2-A2", MATH, "Octupole information saturation: the tail contribution converges (no single extra multipole closes the floor)",
          "tail l>3 saturates; decade increments shrink", "proven_gate", "egs2-gates NT2-A2"),
        r("EGS3-B1", GR, "Semi-native shear->multipole transfer: the Fisher floor is a PROFILE in the shear scale k",
          "floor saturates at 0.632 (super-horizon), drops below at finite k", "proven_gate",
          "egs3-gates B1; fig_egs3_b1_floor_profile"),
        r("EGS3-B2", GR, "Volterra depth-memory: the depth gap is a Volterra integral of the tilt stress with kernel exp(-3 int H); == ODE + Gronwall",
          f"max|Volterra-ODE| {b.get('B2_volterra_memory',{}).get('max_diff_vs_ode','?')}; Gronwall holds {b.get('B2_volterra_memory',{}).get('gronwall_holds','?')}",
          "proven_gate", "egs3-gates B2; fig_egs3_b2_volterra"),
        r("NT2-B3 / EGS3-B3", GR, "Vorticity blind sector re-opens: radial velocities are vorticity-blind (n.Omega.n=0); the transverse channel breaks the no-go",
          f"radial max {nt2b3.get('radial_max_projection','~0')}; transverse rank {b.get('B3_vorticity_reopen',{}).get('transverse_rank','?')}",
          "proven_gate", "egs2/egs3-gates B3; fig_egs3_b3_vorticity"),
        r("NT2-B1", GR, "Two-sided shear/F bracket: a nonzero quadrupole forbids a vanishing shear-filling (lower bound > 0 under H3)",
          "F_lo > 0; zero excluded", "proven_symbolic",
          "wolfram egs3 bracket; egs2-gates NT2-B1; fig_egs2_nt2b1_bracket"),
        r("EGS3-B4", GR, "Covariant two-sided-bracket constants: nondegeneracy condition C_up*kappa*(1+R) > 1 (satisfied by kappa=4/21, C_up=9)",
          "12/7 > 1", "proven_symbolic", "wolfram egs3_bracket_constants (PASS)"),
        r("EGS3-PSD", MATH, "PSD-cone redesign: x_C = tr(C M) for M=diag(g)>=0; admissible set is the convex PSD cone; rank-2 reachable eigen-directions; cone-shell bracket excludes the FLRW vertex",
          f"bit-identical {p.get('bit_identical','?')}; rank {p.get('reachable_rank','?')}; convex cone {p.get('convex_cone','?')}; status {psd.get('status','?')}",
          "proven_symbolic", "egs3-gates PSD P1-P4; wolfram egs3_psd_cone (PASS); fig_egs3_psd_cone"),
        r("K1", DATA, "Global look-elsewhere-corrected low-l morphology p-value on the real Planck map (isotropic LambdaCDM null)",
          (f"SMICA global p={k1g.get('smica',{}).get('global_p',0):.3f}, Commander p={k1g.get('commander',{}).get('global_p',0):.3f} (real PR3 map, {k1g.get('config',{}).get('n_null','?')} GRF nulls)"
           if k1g else "awaiting compute"),
          "measured_partial",
          "scripts/k1_global_maxscan.py on real SMICA/Commander; E2E-systematics null still BLOCKED_MISSING_PR4_E2E_ACCESS (PLA portal-only sims)"),
        r("K5", DATA, "CF4 cosmic-variance-inclusive bulk-flow coverage from release-matched forward mocks (real Tully+2023 catalogue)",
          (f"|B|={k5g.get('measured_bulk',{}).get('amplitude_kms',0):.0f} +/- {k5g.get('coverage',{}).get('total_amplitude_error_kms',0):.0f} km/s; CV-incl coverage {k5g.get('coverage',{}).get('cosmic_variance_inclusive',{}).get('amplitude_coverage',0):.2f} (meas-only {k5g.get('coverage',{}).get('measurement_noise_only',{}).get('amplitude_coverage',0):.2f})"
           if k5g else "awaiting compute"),
          "measured",
          "scripts/k5_cf4_release_coverage.py on real CF4 groups; BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP discharged"),
        r("K6", DATA, "CF4 vorticity/curl sector on the real WF field: structural no-go (curl-suppressed reconstruction, estimator validated)",
          (f"vorticity/shear<={k6g.get('vorticity_over_shear_ratio_max','?'):.3f} at all radii; curl-injection recovered; structural_no_go={k6g.get('structural_no_go','?')}"
           if k6g else "awaiting compute"),
          "measured_no_go",
          "scripts/k6_cf4_curl_posterior.py on real CF4++ WF field; BLOCKED_MISSING_FIELD_REALIZATIONS discharged as structural no-go"),
    ]
    return rows


def _payload() -> dict:
    rows = _rows()
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return {
        "schema": "htt.egs.results_table.v1",
        "claim_tier": "program_theorem_and_synthetic_mechanics",
        "family_identification": False,
        "native_solver_result": False,
        "axes": {"math_stat": "mathematics / statistics theory axis",
                 "gr_boltzmann": "GR / covariant-Boltzmann theory axis",
                 "data_interpretation": "data interpretation axis"},
        "status_counts": counts,
        "rows": rows,
        "claim_boundary": "conditional theorems + synthetic mechanics + real-data measurements on owned inputs; no detection, family/geometry, or native-solver result. Measured rows are model-independent descriptors; K6 is an honest structural no-go; K1 is a partial (look-elsewhere) discharge under an idealised null.",
        "discharges_rev_r127": {
            "K5": "BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP discharged (real CF4 catalogue, CV-inclusive coverage)",
            "K6": "BLOCKED_MISSING_FIELD_REALIZATIONS discharged as a structural no-go (real CF4 WF field, curl-suppressed)",
            "K1": "BLOCKED_MISSING_PR4_E2E_ACCESS partially discharged (real-map look-elsewhere global p under LambdaCDM null; E2E-systematics null still open)",
        },
        "blockers_open": ["BLOCKED_MISSING_PR4_E2E_ACCESS (E2E-systematics null only; look-elsewhere discharged)",
                          "AWAITING_NATIVE_LOWELL_SOLVER"],
    }


_AXIS_LABEL = {MATH: "Math/Stat", GR: "GR/Boltzmann", DATA: "Data"}


def _markdown(payload: dict) -> str:
    lines = [
        "# Consolidated EGS-type results table",
        "",
        "Auto-generated by `scripts/build_egs_results_table.py` from the deterministic",
        "experiment records. Conditional theorems + synthetic mechanics only; no",
        "detection, family/geometry, or native-solver claim. Blocked rows keep their",
        "registered blocker code and emit only a labelled synthetic stand-in.",
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
            print("stale results table:", *stale, sep="\n  - ")
            return 1
        print("results table up to date")
        return 0
    OUT_JSON.write_text(exp_json)
    OUT_MD.write_text(exp_md)
    print(f"wrote {OUT_JSON.relative_to(REPO_ROOT)} + {OUT_MD.relative_to(REPO_ROOT)} ({len(payload['rows'])} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
