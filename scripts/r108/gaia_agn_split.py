"""R108 gaia lane: AGN-identification and centroid-quality splits of the R106 Quaia sample.

Purpose
  The R106 Gaia/Quaia statistic uses 634,233 qualified Quaia rows. This script (1) records their
  membership in Gaia-CRF3 (gaiadr3.gaia_crf3_xm flags, D10S) and in gaiadr3.agn_cross_id (D10), which
  decides whether an AGN-only versus non-AGN comparison exists inside the R106 sample, and (2) runs
  the identical R106 estimator on full-sky splits of that sample that probe AGN-centroid systematics:
    ruwe        RUWE below / at-or-above the Quaia median (centroid-quality proxy),
    ident       identified in an optical-spectroscopic or radio/VLBI/blazar catalogue (dr14q, lamost5,
                cat2qz, lqrf, icrf3sx/k/xka, ocars, alma19, bzcat5, cat2whspj) versus identified only by
                photometric / mid-IR selections (aw15, r90, c75, guw, b19, m65, lqac5 only).
  For each split: R106 statistics of both halves (all 48 patches and the per-draw rule-selected
  exclusion), a within-half 'patch' permutation null (redshift labels permuted inside each NSIDE-2
  patch, R106 null kind 'patch'), and a difference test: d = curvature(A) - curvature(B) with the
  shared-patch delete-one jackknife covariance of d, against a null that relabels A/B membership at
  random inside each shell x patch cell (keeps footprint, redshift and half sizes per cell).
  A split whose halves leave any shell x patch cell empty is reported BLOCKED (the R106 jackknife needs
  every patch).
Inputs: D10F gaia_crf3_xm flags FITS, optional D10 agn_cross_id FITS (SHA-256 recorded), R106 pinned inputs
  through scripts.r108.gaia_estimator (Quaia join, CRF3 FITS for RUWE, R98 cache).
Units: curvature microarcsec/yr per z^2; Q dimensionless.
Usage: python -m scripts.r108.gaia_agn_split --flags F [--agn A] --out J [--draws 200 --seed 108400]
Seeds: seed (half nulls: seed+1.., difference null: seed+100..), deterministic.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import numpy as np

from scripts.r103 import gaia_frame_curvature as g
from scripts.r106 import gaia_null_refit as r106
from scripts.r108 import gaia_estimator as est
from scripts.r108.common import maxrss_mb, sha256_file, write_json

SPEC_RADIO = ("dr14q", "lamost5", "cat2qz", "lqrf", "icrf3sx", "icrf3k", "icrf3xka", "ocars", "alma19", "bzcat5",
              "cat2whspj")
PHOT_IR = ("aw15", "r90", "c75", "guw", "b19", "m65", "lqac5")
STATS = ("spin6", "magnetic16", "joint32")
SPIN6 = r106.STAT_SETS["spin6"]


def half_stats(X, Y, shell, patch, w):
    f, s = r106.group_normal(X, Y, shell, patch)
    counts = np.zeros((4, est.NPATCH), int)
    np.add.at(counts, (shell, patch), 1)
    if counts.min() == 0:
        return None, counts, f, s
    return est.stats(f, s, w), counts, f, s


def diff_q(fA, sA, fB, sB, w, keep):
    """spin6 / magnetic16 / joint32 forms of curvature(A) - curvature(B), shared-patch delete-one jackknife."""
    fullA, oneA, _, _ = g.shared_patch_refits(fA[:, keep], sA[:, keep])
    fullB, oneB, _, _ = g.shared_patch_refits(fB[:, keep], sB[:, keep])
    d = (w @ (fullA - fullB)).reshape(-1)
    c1 = g.delete_covariance(w @ (oneA - oneB), len(keep), 1)
    return r106.qforms(d, c1), d


def run_split(name, maskA, ctx, Y, draws, seed):
    q, w, X = ctx["q"], ctx["w"], ctx["X"]
    allp = np.arange(est.NPATCH)
    keep_ex = np.setdiff1d(allp, r106.EXCLUDE)
    out = {"name": name, "n_A": int(maskA.sum()), "n_B": int((~maskA).sum())}
    halves = {}
    for lab, m in (("A", maskA), ("B", ~maskA)):
        st, counts, f, s = half_stats(X[m], Y[m], q["shell"][m], q["patch"][m], w)
        rec = {"n": int(m.sum()), "min_sources_per_shell_patch": int(counts.min()),
               "empty_shell_patch_cells": int((counts == 0).sum())}
        if st is None:
            rec["status"] = "BLOCKED"
            out[lab] = rec
            out["status"] = "BLOCKED"
            out["reason"] = f"half {lab} leaves {rec['empty_shell_patch_cells']} shell x patch cells empty"
            return out
        rec.update({cfg: {jk: {k: st[cfg][jk][k] for k in STATS} for jk in ("jk1", "jk2")} for cfg in st})
        rec["selected_pair"] = st[f"excl_selected__{est.RULE}"]["pair"]
        rec["spin6_curvature_all48"] = st["all48"]["vec"][SPIN6].tolist()
        rng = np.random.default_rng(seed + (1 if lab == "A" else 2))
        null = {cfg: {k: np.empty(draws) for k in STATS} for cfg in ("all48", "excl")}
        sh, pa, Xm, Ym = q["shell"][m], q["patch"][m], X[m], Y[m]
        for t in range(draws):
            lab_perm = r106.permute_within(sh, pa.astype(np.int64), rng)
            fp, sp = r106.group_normal(Xm, Ym, lab_perm, pa)
            stp = est.stats(fp, sp, w)
            for k in STATS:
                null["all48"][k][t] = stp["all48"]["jk1"][k]
                null["excl"][k][t] = stp[f"excl_selected__{est.RULE}"]["jk1"][k]
        rec["patch_permutation_null_jk1"] = {
            cfg: {k: {"observed": rec["all48" if cfg == "all48" else f"excl_selected__{est.RULE}"]["jk1"][k],
                      "null_q50": float(np.median(null[cfg][k])), "null_q99": float(np.quantile(null[cfg][k], .99)),
                      "null_max": float(null[cfg][k].max()),
                      "draws_ge_observed": int((null[cfg][k] >= rec["all48" if cfg == "all48" else f"excl_selected__{est.RULE}"]["jk1"][k]).sum()),
                      "draws": draws,
                      "exact_conditional_permutation_p": float(((null[cfg][k] >= rec["all48" if cfg == "all48" else f"excl_selected__{est.RULE}"]["jk1"][k]).sum() + 1) / (draws + 1))}
                  for k in STATS} for cfg in null}
        halves[lab] = (f, s)
        out[lab] = rec
    # Difference test.
    obs_diff = {}
    for cfg, keep in (("all48", allp), ("excl_8_47", keep_ex)):
        qd, d = diff_q(*halves["A"], *halves["B"], w, keep)
        obs_diff[cfg] = {"Q": {k: qd[k] for k in STATS}, "spin6_difference": d[SPIN6].tolist()}
    rng = np.random.default_rng(seed + 100)
    cell = q["shell"].astype(np.int64) * est.NPATCH + q["patch"]
    nulld = {cfg: {k: np.empty(draws) for k in STATS} for cfg in ("all48", "excl_8_47")}
    for t in range(draws):
        mA = r106.permute_within(maskA, cell, rng)
        fA, sA = r106.group_normal(X[mA], Y[mA], q["shell"][mA], q["patch"][mA])
        fB, sB = r106.group_normal(X[~mA], Y[~mA], q["shell"][~mA], q["patch"][~mA])
        for cfg, keep in (("all48", allp), ("excl_8_47", keep_ex)):
            qd, _ = diff_q(fA, sA, fB, sB, w, keep)
            for k in STATS:
                nulld[cfg][k][t] = qd[k]
    out["difference_test"] = {cfg: {k: {"observed": obs_diff[cfg]["Q"][k], "null_q50": float(np.median(nulld[cfg][k])),
                                         "null_q95": float(np.quantile(nulld[cfg][k], .95)),
                                         "null_q99": float(np.quantile(nulld[cfg][k], .99)),
                                         "draws_ge_observed": int((nulld[cfg][k] >= obs_diff[cfg]["Q"][k]).sum()),
                                         "draws": draws,
                                         "exact_conditional_permutation_p": float(((nulld[cfg][k] >= obs_diff[cfg]["Q"][k]).sum() + 1) / (draws + 1))}
                                     for k in STATS} | {"spin6_difference": obs_diff[cfg]["spin6_difference"]}
                              for cfg in obs_diff}
    out["status"] = "RUN"
    return out


def run(a):
    t0 = time.monotonic()
    ctx = est.load_context(with_colour=True)
    q, crf3 = ctx["q"], ctx["crf3"]
    Y = est.whiten_field(ctx["L"], q["y"])
    from astropy.table import Table

    fl = Table.read(a.flags)
    fid = np.asarray(fl["source_id"], np.int64)
    order = np.argsort(fid)
    pos = np.clip(np.searchsorted(fid[order], q["source_id"]), 0, len(fid) - 1)
    in_xm = fid[order][pos] == q["source_id"]
    if a.agn is not None:
        agn = Table.read(a.agn, include_names=["source_id", "catalogue_name"])
        in_agn = np.isin(q["source_id"], np.asarray(agn["source_id"], np.int64))
    else:  # D10 BLOCKED this round; membership is decided by gaia_crf3_xm (D10F) alone
        in_agn = np.zeros(len(q["source_id"]), bool)
    flags = {k: np.zeros(len(q["source_id"]), bool) for k in SPEC_RADIO + PHOT_IR}
    for k in flags:
        col = np.asarray(fl[k])
        col = np.asarray(col.filled(False) if hasattr(col, "filled") else col).astype(bool)
        flags[k][in_xm] = col[order][pos[in_xm]]
    membership = {"quaia_qualified": int(len(q["source_id"])), "in_gaia_crf3_xm": int(in_xm.sum()),
                  "in_agn_cross_id": int(in_agn.sum()) if a.agn is not None else "D10 not acquired (BLOCKED)",
                  "non_agn_in_r106_sample": int((~(in_xm | in_agn)).sum()),
                  "gaia_crf3_xm_rows": int(len(fid)),
                  "flag_counts": {k: int(v.sum()) for k, v in flags.items()}}
    ident = np.zeros(len(q["source_id"]), bool)
    for k in SPEC_RADIO:
        ident |= flags[k]
    rows = {"membership": membership}
    rorder = np.argsort(crf3["source_id"])
    ruwe, hit = r106.lookup(crf3["source_id"][rorder], crf3["ruwe"][rorder], q["source_id"])
    if not hit.all():
        raise RuntimeError("Quaia rows without CRF3 RUWE")
    ruwe_med = float(np.median(ruwe))
    splits = {"ruwe": (ruwe < ruwe_med, f"A: RUWE < {ruwe_med:.6f} (Quaia median), B: RUWE >= median"),
              "ident": (ident, "A: in an optical-spectroscopic or radio/VLBI/blazar catalogue; B: photometric/mid-IR only")}
    res = {"schema": "htt.r108.gaia_agn_split/1", "units": "curvature microarcsec/yr per z^2; Q dimensionless",
           "calibrated_p": None, "physical_Pi": None, "physical_GF": None,
           "input_sha256": {**ctx["inputs"], "crf3_flags_fits": sha256_file(a.flags),
                            **({"agn_cross_id_fits": sha256_file(a.agn)} if a.agn is not None else {})},
           "estimator_replay": ctx["replay"], **rows, "draws": a.draws, "seed": a.seed,
           "agn_vs_non_agn": agn_vs_non_agn_statement(membership, a.agn is not None),
           "splits": {}}
    for i, (name, (mask, desc)) in enumerate(splits.items()):
        r = run_split(name, mask, ctx, Y, a.draws, a.seed + 1000 * i)
        r["definition"] = desc
        res["splits"][name] = r
        print(json.dumps({"split": name, "status": r["status"], "elapsed_s": round(time.monotonic() - t0, 1)}), flush=True)
    res["scope"] = ("Half-sample permutation p-values are exact conditional permutation p-values for within-patch redshift "
                    "exchangeability of that half; the difference-test p is exact for random A/B relabelling inside shell x "
                    "patch cells. Neither is a calibrated significance of a physical signal.")
    res["runtime_s"] = time.monotonic() - t0
    res["maxrss_mb"] = maxrss_mb()
    res["provenance"] = est.provenance()
    write_json(a.out, res)
    print(json.dumps({"out": str(a.out), "runtime_s": res["runtime_s"]}))


def agn_vs_non_agn_statement(membership, agn_checked):
    """Wording of the AGN versus non-AGN comparison status.

    The R106 sample is built by joining Quaia to the Gaia-CRF3 FITS (load_context raises if any row lacks a CRF3 BP-RP
    match), so membership in gaia_crf3_xm is a consequence of the sample construction, not a measured property of Quaia;
    agn_cross_id membership is stated only when D10 was read."""
    if membership["non_agn_in_r106_sample"] != 0:
        return "non-AGN rows exist; see splits"
    agn = ("agn_cross_id membership checked against D10" if agn_checked else
           "agn_cross_id membership not checked (D10 blocked)")
    return ("BLOCKED: every qualified R106 row is in gaiadr3.gaia_crf3_xm by construction of the R106 sample (CRF3 BP-RP join "
            f"required), so no non-CRF3 subset exists inside it; {agn}. An empty non-AGN subset is a property of the sample "
            "construction, not a measured property of Quaia.")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--flags", type=Path, required=True)
    ap.add_argument("--agn", type=Path, default=None, help="D10 FITS (optional; BLOCKED this round)")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--draws", type=int, default=200)
    ap.add_argument("--seed", type=int, default=108400)
    a = ap.parse_args(argv)
    a.flags = a.flags.expanduser()
    a.agn = a.agn.expanduser() if a.agn is not None else None
    run(a)


if __name__ == "__main__":
    main()
