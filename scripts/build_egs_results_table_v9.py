#!/usr/bin/env python3
"""v9 (Seventh Revision) successor results table (NEW artifact pair).

The v7 table and the v8 successor are both hash-frozen in shipped packages,
so the v9 rows land in ``egs_results_table_v9.{json,md}``. The active v8
gateway reads its authenticated frozen JSON without executing legacy Python;
v9 then applies the quarantine overlay and appends this cycle's rows. Same
status vocabulary; no detection / Bianchi-class / geometry / native-solver
claim.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
GEN = REPO_ROOT / "docs/generated"
OUT_JSON = GEN / "egs_results_table_v9.json"
OUT_MD = GEN / "egs_results_table_v9.md"

MATH, GR, DATA = "math_stat", "gr_boltzmann", "data_interpretation"


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


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


def _cf4_quarantined_row(tid: str, evidence: str, *finding_ids: str) -> dict:
    findings = ", ".join(finding_ids)
    return _r(
        tid,
        DATA,
        "CF4 numerical consumer quarantined by PR-120; independent estimator "
        "or symbolic mechanics may remain method substrate, but this active row "
        "cannot carry an observational or global-tilt interpretation.",
        f"blocked source record; findings {findings} remain OPEN; no replacement value",
        "quarantined_open_p0",
        "cf4_p0_quarantine_block.json; legacy reproduction only: "
        f"legacy/cf4_p0/cards/{evidence}",
    )


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
        _cf4_quarantined_row(
            "K5-V9", "k5_cf4_identified_interval_card_v9.json",
            "C1-K5-MV-F1", "N-DATA-CF4-DOWNSTREAM"),
        _cf4_quarantined_row(
            "K5-LCDMCV", "cf4_bulkflow_lcdm_card.json",
            "C1-K5-MV-F1", "N-DATA-CF4-DOWNSTREAM"),
        _cf4_quarantined_row(
            "K5-MV", "cf4_mv_bulkflow_card.json", "C1-K5-MV-F1"),
        _cf4_quarantined_row(
            "K5-RECON", "cf4_reconstruction_dependence_card.json",
            "C1-K5-MV-F1"),
        _cf4_quarantined_row(
            "K5-MOCKSIG", "cf4_mock_significance_card.json", "C1-K5-MV-F1"),
        _cf4_quarantined_row(
            "K5-VCORR", "cf4_velocity_correlation_card.json",
            "C3-K5-VCORR-ML-F1", "N-DATA-CF4-DOWNSTREAM"),
        _cf4_quarantined_row(
            "K5-VCORR-ML", "cf4_velocity_correlation_ml_card.json",
            "C3-K5-VCORR-ML-F1"),
        _r("K6-CURL", DATA,
           "K6 vorticity on the REAL CF4++ 3-D WF field (rev-r127 no-go was "
           "abstract): the WF mean-field curl/div ratio quantifies the potential-"
           "flow suppression, and a correlated-residual constrained-realization "
           "vorticity distribution (scaled to the per-cell WF std) upgrades the "
           "per-cell-independent toy",
           "the WF mean field is strongly curl-suppressed (RMS|curl|/RMS|div| = "
           "0.009, potential flow) -- the no-go CONFIRMED on the real 3-D field; "
           "the CR vorticity RMS|curl| = 14-48 (km/s)/Mpc is residual-dominated "
           "and correlation-length-dependent, so a DEFINITIVE ensemble still "
           "needs the full WF operator (BLOCKED_MISSING_FIELD_REALIZATIONS "
           "PARTIAL)",
           "measured",
           "cf4pp_vorticity_card.json"),
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
        _r("EXT-DESI-MOCK", DATA,
           "mock-calibrated significance of the DESI BGS number-count dipole "
           "(the rev-r197 in-house-mock pattern applied to the dipole): the "
           "analytic shot-noise floor + an in-house LambdaCDM clustering mock "
           "(exact ell=1 projection of the observed dN/dz -> GRF sky maps masked "
           "to the footprint + Poisson shot, IDENTICAL estimator)",
           "the observed dipole D=9.49e-3 is CLUSTERING-dominated (13.5 sigma "
           "above the shot-noise floor) and CONSISTENT with LambdaCDM clustering "
           "cosmic variance (mock |D|=0.021+/-0.009, p=0.90 at bias 1.5; robust "
           "across bias 1.2-2.0) -- NOT an excess/anomaly; the kinematic dipole "
           "is sub-dominant to the clustering cosmic variance at BGS depths",
           "measured",
           "desi_dipole_mock_card.json"),
        _r("EXT-ACT", DATA,
           "ACT DR6 CMB-lensing low-multipole isotropy cross-check "
           "(independent-instrument): 400 baseline sims give the mean field "
           "MF=<kappa_alm_sim> and the N0+N1-inclusive isotropic null; the "
           "ell=2..10 debiased band power is tested for consistency AND a 95% "
           "CL model-independent upper limit is set on excess low-multipole "
           "power (a flat-in-ell signal injected into the sims)",
           "p = 0.35 CONSISTENT with the isotropic LambdaCDM sims; 95% CL "
           "upper limit on excess ell=2..10 kappa band power < 3.28e-6 "
           "(0.47x the null band power); NOT a detection, NOT a family claim; "
           "the reconstruction dipole ell=1 is not measurable (NaN)",
           "measured",
           "external_lanes_seal.json; act_kappa_card.json"),
        _r("EXT-JWST", DATA,
           "JWST/CF4 cross-match catalogue mechanics remain available, but "
           "the downstream Omega_tilt survey-design forecast is quarantined "
           "by PR-120",
           "catalogue linkage only; no global-tilt precision gain or "
           "observational interpretation while N-DATA-CF4-DOWNSTREAM is OPEN",
           "quarantined_open_p0",
           "jwst_cf4_anchors.json; cf4_p0_quarantine_block.json"),
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

_CF4_P0_INHERITED_ROWS = {
    "EGS3-D1": "bass_extended_joint_forecast.json",
    "EGS3-K5card": "k5_cf4_identified_interval_card.json",
    "K5": "k5_cf4_release_coverage.json",
    "K5-V8": "k5_cf4_identified_interval_card_v8.json",
}


def _apply_overlay(rows: list[dict]) -> list[dict]:
    out = []
    for row in rows:
        if row["theorem_id"] == "EGS3-A1":
            row = dict(row)
            row["statement"] = (
                "Graded-comparator identifiability within the registered "
                "leading-channel response map: from {low-l CMB-T, radial "
                "velocity} the reachable subspace of g has rank 2."
            )
            row["key_result"] = (
                "rank 2; reachable ['Sigma2', 'Omega_tilt']; V2/W2 is a "
                "structural zero column only in the registered response map "
                "and may re-open under transverse velocities or a separately "
                "derived full vorticity transfer; Omega_k is a leading-order "
                "no-channel that re-opens beyond leading order"
            )
            row["status"] = "proven_gate"
            out.append(row)
            continue
        if row["theorem_id"] == "EGS3-D2":
            out.append(
                _r(
                    "EGS3-D2",
                    MATH,
                    "Generic coupled-Fisher sensitivity to a synthetic tilt-information "
                    "weight; this is method substrate and not a PV/JWST prior or "
                    "observational forecast.",
                    "monotone covariance-inflation sensitivity on a declared synthetic "
                    "grid; observational interpretation absent",
                    "synthetic_method_only",
                    "egs3-gates D4; fig_egs3_d_joint_forecast; "
                    "cf4_p0_quarantine_block.json",
                )
            )
            continue
        if row["theorem_id"] == "EGS3-U2":
            row = dict(row)
            row["statement"] = (
                "MES-registry ceilings on the Teff fingerprints: proved "
                "symbolic envelopes and exact rational ceilings at eps1; "
                "observational numeric instantiation excluded"
            )
            row["key_result"] = (
                "symbolic ceiling map retained; former CF4 point quarantined "
                "while C1-K5-MV-F1 remains OPEN; no replacement value"
            )
            row["evidence"] = (
                "teff_unification_seal.json; cf4_p0_quarantine_block.json"
            )
            out.append(row)
            continue
        if row["theorem_id"] in _CF4_P0_INHERITED_ROWS:
            out.append(
                _cf4_quarantined_row(
                    row["theorem_id"],
                    _CF4_P0_INHERITED_ROWS[row["theorem_id"]],
                    "C1-K5-MV-F1",
                    "N-DATA-CF4-DOWNSTREAM",
                )
            )
            continue
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
    blockers_open = [
        (
            "CF4 P0 findings C1-K5-MV-F1, C3-K5-VCORR-ML-F1, and "
            "N-DATA-CF4-DOWNSTREAM remain OPEN; replacement_value=null and "
            "scientific_effect=none"
            if "BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP" in blocker
            else blocker
        )
        for blocker in base["blockers_open"]
    ]
    config = {
        "schema": "htt.egs.results_table.v9",
        "supersession_overlay": sorted(_SUPERSESSION_OVERLAY),
        "claim_scope_overlay": ["EGS3-A1"],
        "cf4_quarantined_rows": sorted(_CF4_P0_INHERITED_ROWS),
        "v9_row_ids": [row["theorem_id"] for row in _v9_rows()],
    }
    return {
        "schema": "htt.egs.results_table.v9",
        "artifact_id": "common.egs.results_table.v9",
        "artifact_path": "docs/generated/egs_results_table_v9.json",
        "owner": "COMMON",
        "implementation_scope": "common",
        "based_on_frozen_tables": "egs_results_table.json (v7, byte-frozen) "
                                  "+ egs_results_table_v8.json (v8, "
                                  "hash-frozen); rows inherited with a "
                                  "supersession overlay on EGS3-E1/E2/E4/G2 "
                                  "and a PR-169 claim-scope overlay on EGS3-A1",
        "claim_tier": base["claim_tier"],
        "transfer_source": "mixed_none_registered_external_and_proxy_by_row",
        "config_hash": "sha256:" + hashlib.sha256(
            json.dumps(config, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
        ).hexdigest(),
        "input_hashes": [
            f"legacy/cf4_p0/tables/egs_results_table_v8.json:"
            f"{_sha256(REPO_ROOT / 'legacy/cf4_p0/tables/egs_results_table_v8.json')}",
            f"scripts/build_egs_results_table_v9.py:"
            f"{_sha256(REPO_ROOT / 'scripts/build_egs_results_table_v9.py')}",
        ],
        "sky_support_status": "mixed_by_row",
        "null_mock_status": "mixed_by_row",
        "caveats": [
            "Table rows retain their individual theorem, synthetic, and data-interpretation scopes.",
            "All CF4 P0-fed rows are blocked records with no replacement value.",
            "No row identifies a Bianchi family or represents native low-ell solver output.",
        ],
        "generating_command": "python scripts/build_egs_results_table_v9.py",
        "git_commit_or_worktree_state": "content-addressed-inputs",
        "family_identification": False,
        "native_solver_result": False,
        "axes": base["axes"],
        "status_counts": counts,
        "rows": rows,
        "claim_boundary": base["claim_boundary"],
        "blockers_open": blockers_open,
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
             f"owner: {payload['owner']}",
             f"implementation_scope: {payload['implementation_scope']}",
             f"claim_tier: {payload['claim_tier']}",
             f"transfer_source: {payload['transfer_source']}",
             f"config_hash: `{payload['config_hash']}`",
             "input_hashes:",
             *[f"- {item}" for item in payload["input_hashes"]],
             f"sky_support_status: {payload['sky_support_status']}",
             f"null_mock_status: {payload['null_mock_status']}",
             "caveats:",
             *[f"- {item}" for item in payload["caveats"]],
             f"generating_command: `{payload['generating_command']}`",
             f"git_commit_or_worktree_state: {payload['git_commit_or_worktree_state']}",
             "",
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
