"""R108 radio lane: R106 closed-form / semi-analytic p(C_1) of the NVSS integrated-minus-peak contrast at theory C_1 values.

Purpose
    Feed the TF7 theory C_1 bracket (THEORY_C1.json from scripts/r108/radio_theory_c1.py) into the R106 p(C_1) machinery for
    the EMPIRICAL_DIFF_SELECTION RED / MID / FLAT null families, with the identical estimator (R65 Wald t_self, p = 2
    "dipole" and p = 6 "dipole_stf"), identical mocks (R106 C_1 = 0 common-random-number ensembles, 1000 per family) and
    the identical first-order l = 1 injection delta_i(C_1) = delta0_i + df sqrt(C_1) u_i, using the R106 helper functions
    imported unchanged from scripts/r106/radio_null_mocks.py. Before any new C_1 is evaluated the script reproduces the R106
    p-versus-C_1 grid (integer exceedance counts and Gaussian p) and the 0.05/0.01 crossings exactly.
Inputs (SHA-256 verified at run time)
    ~/Downloads/htt_r106_analysis/nvss/review_followup/C1ZERO_DRAWS.npz      cf288192ba5bb953c4905b91285b870dcaeb9b2addd9c151949a0b5470e310f0
    docs/.../R106_RESEARCH_20261124/NVSS/NVSS_REVIEW_CORRECTIONS.json         (sha recorded; observed delta, t_self, df, R106 curve)
    docs/.../R108_LOS_ATLAS_DATA_20261124/RADIO/THEORY_C1.json                (sha recorded)
Units: C_1 dimensionless (l = 1 power of the log-density of the resolved/migrating classes, R106 convention).
Usage (repo root, venv python):
    .venv/bin/python -m scripts.r108.radio_p_of_c1 --theory docs/.../RADIO/THEORY_C1.json --out docs/.../RADIO/P_OF_C1_THEORY.json
Claim class: every p in the output is CONDITIONAL on the R106 EMPIRICAL_DIFF_SELECTION family shape and on C_1 (claim_class,
    classification, per-row claim_class); RACS empirical points are a scale only (other survey's class definition).
    THEORY_C1 envelope points are fed both as computed and x the V3 low-l systematic factor (RADIO-1 review).
Deterministic (no new random numbers; the R106 mocks are reused).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

from scripts.r106 import radio_null_mocks as R

C1ZERO_NPZ = Path.home() / "Downloads/htt_r106_analysis/nvss/review_followup/C1ZERO_DRAWS.npz"
C1ZERO_SHA = "cf288192ba5bb953c4905b91285b870dcaeb9b2addd9c151949a0b5470e310f0"
REVIEW = Path("docs/research_program/observational_publication_20261015/R106_RESEARCH_20261124/NVSS/NVSS_REVIEW_CORRECTIONS.json")
FAMS = ("LSS_DIFF_RED", "LSS_DIFF_MID", "LSS_DIFF_FLAT")
MODELS = ("dipole", "dipole_stf")
CLAIM_CLASS = {
    "label": "CONDITIONAL",
    "calibrated_p": None,
    "scope": "p conditional on the R106 EMPIRICAL_DIFF_SELECTION null families (RED / MID / FLAT) and on C1",
    "statement": ("every p here (p_mc, p_mc_display, gaussian_p, p_conditional) is conditional on the empirical DIFF family "
                  "shape and on the C1 value fed in; the R106 C1 = 0 CRN mocks do not reproduce the observed overdispersion "
                  "(overdispersion-reproducing mocks are open); not a calibrated significance; no physical attribution "
                  "(R106 NVSS_REVIEW_CORRECTIONS.json claim_classes.conditional_prediction / physical_attribution)"),
    "empirical_points": ("RACS points use RACS's own resolved/migrating class definition (25 arcsec beam, 887.5 MHz, edges "
                         "scaled by an assumed alpha = 0.75) and include RACS tile/PSF systematics: they set a scale only and "
                         "are not an independent estimate of the NVSS g_diff C1; the NVSS point is circular"),
    "not_claimed": "no calibrated p, no physical attribution, no family identification"}
CLASSIFICATION = {"label": "CONDITIONAL", "calibrated_p": None,
                  "scope": "p conditional on R106 EMPIRICAL_DIFF_SELECTION null families"}
RACS_FORM = "empirical_other_survey_class_definition (scale only)"


def sha256(path):
    with open(path, "rb") as fh:
        return hashlib.file_digest(fh, "sha256").hexdigest()


def git_head():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return None


def family_state(z0, review, fam, model):
    """Coefficients exactly as R106 c1_analysis builds them."""
    d0, u = z0[f"c1zero_{fam}__{model}_delta"], z0[f"c1zero_{fam}__u_l1"]
    prec = np.linalg.inv(z0[f"c1zero_{fam}__{model}_cov"])
    prec = 0.5 * (prec + np.transpose(prec, (0, 2, 1)))
    df = review["df_offdiag_fraction"]["observed_counts"]["df"]
    coeffs = R.tself_coefficients(d0, prec, u, df)
    md = review["f1_c1_dependence"]["per_family"][fam]["models"][model]
    return dict(coeffs=coeffs, cov0=np.cov(d0.T), dob=np.asarray(md["observed_delta"], float),
                tob=float(md["observed_t_self"]), df=df, n=len(d0), r106=md)


def p_at(st, c1):
    n = st["n"]
    k = int(R.exceed_counts(st["coeffs"], st["tob"], [c1])[0])
    w = R.wald(st["dob"], R.closed_form_cov(st["cov0"], st["df"], c1))
    p = (k + 1) / (n + 1)
    return dict(C1=c1, k_ge_observed=k, n_mocks=n, p_mc=p, p_mc_display=R.p_display(k, n),
                p_mc_binomial_se=math.sqrt(p * (1 - p) / (n + 1)), gaussian_wald=w, gaussian_p=math.exp(-w / 2),
                claim_class="CONDITIONAL")


def reproduce(st):
    """Exact replay of the R106 p-versus-C_1 grid and crossings."""
    worst_k, worst_g, rows = 0, 0.0, 0
    for row in st["r106"]["p_versus_C1"]:
        mine = p_at(st, row["C1"])
        worst_k = max(worst_k, abs(mine["k_ge_observed"] - row["t_self_semi_analytic_k"]))
        worst_g = max(worst_g, abs(mine["gaussian_p"] - row["gaussian_p"]) / max(row["gaussian_p"], 1e-300))
        rows += 1
    cross = {}
    for alpha in R.ALPHAS:
        cm, _ = R.c1_crossing_mc(st["coeffs"], st["tob"], alpha, 0.1)
        cg = R.c1_crossing_gaussian(st["dob"], st["cov0"], st["df"], alpha, 0.1)
        ref = st["r106"]["crossings"][str(alpha)]
        cross[str(alpha)] = dict(semi_analytic_C1=cm, r106_semi_analytic_C1=ref["t_self_semi_analytic_C1"],
                                 gaussian_C1=cg, r106_gaussian_C1=ref["gaussian_closed_form_C1"],
                                 exact_match=bool(cm == ref["t_self_semi_analytic_C1"] and
                                                  (cg == ref["gaussian_closed_form_C1"] or
                                                   (cg is not None and ref["gaussian_closed_form_C1"] is not None and
                                                    abs(cg / ref["gaussian_closed_form_C1"] - 1) < 1e-12))))
    return dict(grid_points=rows, max_abs_k_difference=worst_k, max_rel_gaussian_p_difference=worst_g, crossings=cross,
                passed=bool(worst_k == 0 and worst_g < 1e-10 and all(c["exact_match"] for c in cross.values())))


def theory_points(th):
    """Named C_1 values from THEORY_C1.json (shot-noise-free unless labelled)."""
    pts = [("zero (identical resolved/compact classes)", 0.0, "shot_noise_free")]
    for pv in ("linear", "hmcode2020"):
        e = th["envelope"][pv]
        pts += [(f"{pv}: count-field C1 primary min ({e['primary_argmin']})", e["primary_min"], "shot_noise_free"),
                (f"{pv}: count-field C1 primary max ({e['primary_argmax']})", e["primary_max"], "shot_noise_free"),
                (f"{pv}: count-field C1 extended max ({e['extended_argmax']})", e["extended_max"], "shot_noise_free"),
                (f"{pv}: differential C1 max over bracket pairs ({' - '.join(e['differential_pair_max']['pair'])})",
                 e["differential_pair_max"]["C1"], "shot_noise_free"),
                (f"{pv}: differential Minkowski bound 4 max C1", e["differential_triangle_bound_4max"], "shot_noise_free")]
        f = th["C1_forms_for_R106"][pv]["g_diff"]
        pts += [(f"{pv}: g_diff with shot noise, {lab} (double counts Poisson; sensitivity only)", v, "with_shot_noise")
                for lab, v in zip(f["labels"], f["with_shot_noise"])]
        v3 = e["with_V3_low_l_systematic"]
        fu = v3["factor_up"]
        pts += [(f"{pv}: count-field C1 extended max x V3 low-l systematic {fu:.4f}", v3["extended_max"], "shot_noise_free_x_V3_factor_up"),
                (f"{pv}: differential C1 max over bracket pairs x V3 low-l systematic {fu:.4f}", v3["differential_pair_max"],
                 "shot_noise_free_x_V3_factor_up"),
                (f"{pv}: differential Minkowski bound 4 max C1 x V3 low-l systematic {fu:.4f}",
                 v3["differential_triangle_bound_4max"], "shot_noise_free_x_V3_factor_up")]
    return pts


def empirical_points(racs):
    """Transverse differential (resolved/migrating fraction) dipole powers from RACS_DIPOLE.json (empirical, CONDITIONAL).

    RACS uses its own resolved/migrating class definition and carries its own tile/PSF systematics, so its points are a
    scale only, not an independent estimate of the NVSS g_diff C1; the NVSS point is circular."""
    pts = []
    for blk, tag, form in (("racs_full_mask_alpha0p75", "RACS full mask", RACS_FORM),
                           ("racs_overlap_with_R65_NVSS_mask", "RACS on NVSS overlap", RACS_FORM),
                           ("racs_full_mask_alpha0p75_cut_x1p5", "RACS full mask, edges x1.5", RACS_FORM),
                           ("nvss_full_R65_mask", "NVSS itself (circular: same data as the tested contrast; scale only)",
                            "empirical_circular")):
        r = racs[blk]["differential_offdiag_dipole"]["mono_dipole"]
        lab = tag if form == "empirical_circular" else f"{tag} (RACS class definition; scale only, not an NVSS estimate)"
        for key in ("C1_transverse_debiased_pearson", "C1_transverse_raw"):
            pts.append((f"empirical {lab}: {key}", max(float(r[key]), 0.0), form))
    return pts


def summary_rows(p_rows):
    """Compact table rows (dipole model, all forms except with_shot_noise); every p is labelled CONDITIONAL."""
    return [dict(label=r["label"], form=r["form"], C1=r["C1"], p_conditional=r["p_mc_display"], gaussian_p_conditional=r["gaussian_p"],
                 claim_class="CONDITIONAL") for r in p_rows if r["form"] != "with_shot_noise"]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--theory", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--racs", default=None, help="RACS_DIPOLE.json for empirical differential C1 points")
    a = ap.parse_args(argv)
    if sha256(C1ZERO_NPZ) != C1ZERO_SHA:
        raise ValueError("C1ZERO_DRAWS.npz SHA-256 mismatch")
    review = json.loads(REVIEW.read_text())
    th = json.loads(Path(a.theory).read_text())
    with np.load(C1ZERO_NPZ, allow_pickle=False) as z:
        z0 = {k: z[k] for k in z.files}
    out = dict(schema="htt.r108.radio.p_of_c1/1", node="SQ-RADIO",
               command=" ".join([sys.executable, "-m", "scripts.r108.radio_p_of_c1", *(argv or sys.argv[1:])]),
               git_head=git_head(), started_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
               script_sha256=sha256(Path(__file__)), r106_script_sha256=sha256(Path(R.__file__)),
               input_sha256={"C1ZERO_DRAWS.npz": C1ZERO_SHA, "NVSS_REVIEW_CORRECTIONS.json": sha256(REVIEW),
                             "THEORY_C1.json": sha256(a.theory)},
               statistic="R65 wald_self (t_self) of delta = integrated - peak; p_mc = (k+1)/(n+1) over the R106 C_1=0 CRN mocks "
                         "with the first-order l=1 injection; gaussian_p = exp(-W/2) with Cov = Cov_{C1=0} + df^2 (3 C1/4pi) I_2",
               families={f: R.FAMILY_LABELS[f] for f in FAMS}, claim_class=CLAIM_CLASS, classification=CLASSIFICATION,
               reproduction={}, p_at_theory_C1={})
    states = {(f, m): family_state(z0, review, f, m) for f in FAMS for m in MODELS}
    for (f, m), st in states.items():
        out["reproduction"][f"{f}|{m}"] = reproduce(st)
    if not all(r["passed"] for r in out["reproduction"].values()):
        out["status"] = "REPRODUCTION_FAILED"
        Path(a.out).write_text(json.dumps(out, indent=1, default=float) + "\n")
        print("reproduction failed", json.dumps(out["reproduction"], indent=1, default=float))
        return 2
    pts = theory_points(th)
    if a.racs:
        out["input_sha256"]["RACS_DIPOLE.json"] = sha256(a.racs)
        pts += empirical_points(json.loads(Path(a.racs).read_text()))
    for (f, m), st in states.items():
        out["p_at_theory_C1"][f"{f}|{m}"] = [dict(label=lab, form=form, **p_at(st, c1)) for lab, c1, form in pts]
    # compact table: dipole model, shot-noise-free points
    out["summary_dipole_t_self"] = {R.FAMILY_LABELS[f]: summary_rows(out["p_at_theory_C1"][f"{f}|dipole"]) for f in FAMS}
    out["crossings_r106_0p05"] = {R.FAMILY_LABELS[f]: states[(f, "dipole")]["r106"]["crossings"]["0.05"]["t_self_semi_analytic_C1"]
                                  for f in FAMS}
    out["status"] = "OK"
    out["status_meaning"] = "execution status (R106 reproduction passed); not a claim class: see claim_class"
    Path(a.out).write_text(json.dumps(out, indent=1, default=float) + "\n")
    for fam, rows in out["summary_dipole_t_self"].items():
        print(fam)
        for r in rows:
            print("   %-95s C1=%.3e p_conditional=%s gauss=%.4f" % (r["label"][:95], r["C1"], r["p_conditional"],
                                                                     r["gaussian_p_conditional"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
