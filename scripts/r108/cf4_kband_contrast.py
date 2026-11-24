"""R108 lane cf4, A1(ii): the R106 2MRS-excluded contrast with K-band-matched controls (6dFGSv K for every row).

R106 (scripts/r106/cf3_overlap.py) scored the R105 relative held-out marks with the 6dFGSv rows that are CORAS 2MRS
input tracers excluded, against random exclusions stratified by (cz_gal 500 km/s bin x R105 inclusion).  The 2MRS
set is defined by an apparent-magnitude cut, so its kept set had a mark zero point (+0.099 dex member minus
non-member) the controls did not share and the raw blocks were declared not comparable.  K magnitudes were then
known only for the 2MRS tracers.  This module adds a K magnitude for all 8,885 rows (6dFGSv 2MASS photometry,
Campbell et al. 2014 J/MNRAS/443/1231 FPsample column Ktot = 2MASS k_m_ext, joined on the 6dFGS designation;
VizieR VII/259 has no K column) and reruns the same estimator on the same R105 PGC/PGC1 folds:

* replay:   the R106 scorers are rebuilt and their R105 fold replay must pass (R106 tolerances), then the R106
            drop_recentered_czbin block of 2MRS_coras_input (stream [seed, 2]) is recomputed and compared with the
            R106 JSON (reproduction gate);
* K-matched controls: test_only, drop and drop_recentered_czbin for 2MRS_coras_input and its complement with
            random exclusions stratified by (cz_gal 500 km/s bin x inclusion x Ktot bin); bin widths 0.25 mag
            (primary) and 0.5 mag (sensitivity, test_only and czbin only).  New streams: test_only seed+KSEED_OFFSET,
            drop [seed, 4] / [seed, 5];
* magnitude-only analogue: the exclusion set "Ktot <= K*" with K* chosen so that its size equals the 2MRS set, scored
            with the R106 cz x inclusion controls (does a pure apparent-magnitude exclusion reproduce the R106
            non-comparability?);
* zero points: member minus non-member inverse-variance mean delta_d per 2000 km/s cz bin (R106 statistic) and the
            same at matched K (cells cz 2000 km/s x Ktot 0.25 mag with >= 3 rows of each kind), plus a weighted
            linear fit delta_d = a_czbin + b Ktot + c member (c = member effect at fixed K).

Inputs (SHA-256 recorded at run time)
  D03/J_MNRAS_443_1231_FPsample.vot  ac12360640076f9fc153c6b44217f50a9eb5836feda9548640ea9c0ada5f84b7 (11,102 rows)
  R106 CF3_OVERLAP.json.gz (reference numbers), R105 CF4_FIELD_HOLDOUT.json and CF4_CORAS_MARKS.json (fold replay),
  CORAS draw directories (~/Downloads/htt_r105_coras/sixdf8, ~/Downloads/htt_r106_analysis/marks128) with their
  reference JSONs, CORAS donor data (2MRS member catalogue, configuration) at commit 45ab2563.

Units: delta_d in dex (log10 D_z/D_H), K in mag, cz in km/s, scores in nats (natural-log predictive differences).

Usage (repo root, PYTHONPATH=.:htt:htt/src):
  python -B -m scripts.r108.cf4_kband_contrast --jobs 3 --output docs/.../CF4/KBAND_CONTRAST.json

Comparability (review CF4-1).  Every scored block is labelled from the data, not by hand:
* test_only (per fold key) and drop: comparable_to_controls iff |z_raw| < Z_COMPARABLE, z_raw = (kept-set
  inverse-variance mean raw delta_d - control mean)/control sd under the same control masks (R106
  mark_zero_point_confound; R106 used the same 3 sd line in raw_zero_point_outside_control_spread_3sd);
* drop_recentered_czbin: the fit removes the per-2000 km/s bin part of that zero point, so the residual is the
  member-minus-non-member mark difference inside the recentring bins at the matching resolution of the strata
  (R105-selected rows; strata r106: per 2000 km/s bin; k0.25 / k0.5: cells 2000 km/s x Ktot 0.25 / 0.5 mag with
  >= 3 rows of each kind); comparable iff |combined / combined_err_inflated| < Z_COMPARABLE.  A control that keeps
  members where the observed set keeps none carries that split after recentring and the observed set does not.
Degenerate blocks get comparable_to_controls = null.  Each summarised entry carries degenerate,
comparable_to_controls, the comparability record and the exchangeability of its strata: rows in strata that the
exclusion empties are excluded in every control replicate, so every control fraction is conditional on them and
randomises only the effective_n rows in mixed strata (test_only: counted inside each fold's held-out set; drop:
over all rows).  Control fractions of non-comparable blocks are not overlap or leakage evidence.

Claim class: conditional working-model log predictive differences on the R105 folds; control fractions are
finite-replicate tail counts conditional on the fixed strata, not calibrated p-values; no physical attribution.
"""
from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
import multiprocessing as mp
import re
import shlex
import sys
import time
import warnings
from pathlib import Path

import numpy as np

from scripts.r108.common import git_state, sha256_file, write_json

ROOT = Path(__file__).resolve().parents[2]
HOME = Path.home()
DL = HOME / "Downloads/htt_r108/cf4"
R106_JSON_GZ = ROOT / "docs/research_program/observational_publication_20261015/R106_RESEARCH_20261124/CF3/CF3_OVERLAP.json.gz"
R105 = ROOT / "docs/research_program/observational_publication_20261015/R105_RESEARCH_20261124"
OUT_DEFAULT = ROOT / "docs/research_program/observational_publication_20261015/R108_LOS_ATLAS_DATA_20261124/CF4/KBAND_CONTRAST.json"
DEFAULT_CORAS = [f"{HOME}/Downloads/htt_r105_coras/sixdf8={R105}/CF4_CORAS_MARKS.json",
                 f"{HOME}/Downloads/htt_r106_analysis/marks128={HOME}/Downloads/htt_r106_analysis/CF4_MARKS128.json"]
K_EDGES_FROM, K_EDGES_TO = 6.0, 13.5
KSEED_OFFSET = 4
SETS = ("2MRS_coras_input", "complement_keep_only_2MRS_coras_input")
Z_COMPARABLE = 3.0     # |z| line for comparable_to_controls (R106 raw_zero_point_outside_control_spread_3sd)
RESIDUAL_K_WIDTH = {"r106": None, "k0.25": .25, "k0.5": .5}   # matching resolution of each strata label
MEMBER_LABEL = {"2MRS_coras_input": "2MRS CORAS input member",
                "complement_keep_only_2MRS_coras_input": "not a 2MRS CORAS input member",
                "Ktot_le_Kstar_same_size": "Ktot <= K*"}


def load_ktot(path, names):
    from astropy.io.votable import parse_single_table
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        t = parse_single_table(str(path)).to_table(use_names_over_ids=True)
    if len(t) != 11102:
        raise ValueError(f"FPsample rows {len(t)} != 11102 (VizieR catalogue page)")
    nm = np.asarray(t["6dFGS"]).astype(str)
    if len(set(nm)) != len(nm):
        raise ValueError("FPsample 6dFGS designations not unique")
    k = np.asarray(np.ma.filled(np.ma.asarray(t["Ktot"]).astype(float), np.nan))
    look = dict(zip(nm, k))
    K = np.array([look.get(str(n), np.nan) for n in names])
    return K, dict(n_fpsample=int(len(t)), n_sixdfv_with_ktot=int(np.isfinite(K).sum()),
                   column="Ktot = 2MASS k_m_ext (Campbell et al. 2014 table4 via VizieR J/MNRAS/443/1231/FPsample)")


A_K_OVER_A_V = 0.114   # Cardelli, Clayton & Mathis 1989 (R_V = 3.1), Table 3


def load_dr3(path, names):
    """VII/259 6dfgs (6dFGS DR3): AV, heliocentric cz and redshift quality joined on the 6dFGS designation."""
    from astropy.io.votable import parse_single_table
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        t = parse_single_table(str(path)).to_table(use_names_over_ids=True)
    if len(t) != 124647:
        raise ValueError(f"VII/259 6dfgs rows {len(t)} != 124647 (VizieR catalogue page)")
    nm = np.asarray(t["6dFGS"]).astype(str)
    idx = {n: i for i, n in enumerate(nm)}
    j = np.array([idx.get(str(n), -1) for n in names])
    av = np.where(j >= 0, np.ma.filled(np.ma.asarray(t["AV"]).astype(float), np.nan)[np.maximum(j, 0)], np.nan)
    q = np.where(j >= 0, np.asarray(t["q_cz"], int)[np.maximum(j, 0)], -1)
    return av, dict(n_dr3=int(len(t)), n_sixdfv_joined=int((j >= 0).sum()),
                    q_cz_histogram={int(a): int(b) for a, b in zip(*np.unique(q, return_counts=True))},
                    AV_min_median_max=[float(np.nanmin(av)), float(np.nanmedian(av)), float(np.nanmax(av))],
                    A_K_over_A_V=A_K_OVER_A_V)


def kbins(K, width):
    edges = np.arange(K_EDGES_FROM, K_EDGES_TO + 1e-9, width)
    if np.nanmin(K) < edges[0] or np.nanmax(K) >= edges[-1]:
        raise ValueError("K outside the bin range")
    return np.digitize(K, edges) - 1, edges


def k_strata(base_strata, kb):
    nk = int(kb.max()) + 1
    return np.asarray(base_strata, np.int64) * nk + kb


def exchangeability(strata, excluded, selected=None, groups=None):
    """How many excluded rows sit in strata where a random control can differ from the observed set.

    groups: None (drop: one global draw over all rows) or a list of row-index arrays (test_only: masks are drawn
    inside each fold's held-out set, so strata are counted per group and summed).  selected: R105 inclusion; the
    selected counts are the rows that carry a mark."""
    strata, excluded = np.asarray(strata), np.asarray(excluded, bool)
    selected = np.ones(len(strata), bool) if selected is None else np.asarray(selected, bool)
    groups = [np.arange(len(strata))] if groups is None else groups
    mixed_rows = pure_rows = n_mixed = n_with = mixed_sel = pure_sel = 0
    for g in groups:
        st, ex, se = strata[g], excluded[g], selected[g]
        for s in np.unique(st):
            idx = st == s
            k, n = int(np.sum(ex & idx)), int(idx.sum())
            if k == 0:
                continue
            n_with += 1
            ksel = int(np.sum(ex & idx & se))
            if k == n:
                pure_rows += k
                pure_sel += ksel
            else:
                mixed_rows += k
                mixed_sel += ksel
                n_mixed += 1
    n_ex = mixed_rows + pure_rows
    return dict(n_excluded=n_ex, n_excluded_in_mixed_strata=mixed_rows,
                n_excluded_in_strata_fully_excluded=pure_rows, n_mixed_strata=n_mixed,
                n_strata_with_exclusion=n_with,
                fraction_excluded_in_strata_fully_excluded=pure_rows / n_ex if n_ex else None,
                effective_n_randomised=mixed_rows,
                n_excluded_selected=mixed_sel + pure_sel, n_excluded_selected_in_mixed_strata=mixed_sel,
                n_excluded_selected_in_strata_fully_excluded=pure_sel,
                fraction_selected_excluded_in_strata_fully_excluded=pure_sel / (mixed_sel + pure_sel)
                if mixed_sel + pure_sel else None,
                counted=("per fold held-out set, summed over folds" if len(groups) > 1 else "over all rows"),
                note="rows in fully excluded strata are excluded in every control replicate; control fractions are "
                     "conditional on them and randomise only the effective_n_randomised mixed-strata rows")


def member_split(cz, dd, eps, member, keep, K=None, kwidth=None, min_rows=None):
    """Member-minus-non-member inverse-variance mean delta_d per 2000 km/s cz bin (kwidth None, >= 5 rows of each
    kind, R106 statistic) or per cell 2000 km/s x K kwidth mag (>= 3 rows of each kind), with the R106
    heterogeneity combination (None when no cell qualifies)."""
    from scripts.r106.cf3_overlap import heterogeneity
    min_rows = (5 if kwidth is None else 3) if min_rows is None else min_rows

    def ivmean(m):
        w = 1. / eps[m] ** 2
        return float(np.sum(w * dd[m]) / w.sum()), float(w.sum() ** -.5)

    cells = {}
    kb = None if kwidth is None else np.floor((K - K_EDGES_FROM) / kwidth).astype(int)
    for a in range(0, 18000, 2000):
        zsel = keep & (cz >= a) & (cz < a + 2000)
        for q in ([None] if kb is None else np.unique(kb)):
            c = zsel if q is None else zsel & (kb == q)
            if np.sum(c & member) < min_rows or np.sum(c & ~member) < min_rows:
                continue
            (m1, e1), (m0, e0) = ivmean(c & member), ivmean(c & ~member)
            lab = f"{a}-{a + 2000}" if q is None else f"cz{a}-{a + 2000}|K{K_EDGES_FROM + kwidth * q:.2f}"
            cells[lab] = dict(diff=m1 - m0, err=float(np.hypot(e1, e0)), n_member=int(np.sum(c & member)),
                              n_nonmember=int(np.sum(c & ~member)))
    het = heterogeneity([r["diff"] for r in cells.values()], [r["err"] for r in cells.values()]) if cells else None
    return cells, het


def residual_record(cz, dd, eps, member, K, inc, kwidth):
    """Data-driven residual for a czbin-recentred block (see module docstring, review CF4-1)."""
    cells, het = member_split(cz, dd, eps, member, inc.astype(bool), K, kwidth)
    z = het["combined"] / het["combined_err_inflated"] if het and het["combined_err_inflated"] > 0 else None
    return dict(statistic=("member-minus-non-member mean delta_d of R105-selected rows per 2000 km/s cz bin" if kwidth is None
                           else f"member-minus-non-member mean delta_d of R105-selected rows in cells 2000 km/s x Ktot "
                                f"{kwidth:g} mag (>= 3 rows of each kind)"),
                n_cells=len(cells), n_rows=int(sum(r["n_member"] + r["n_nonmember"] for r in cells.values())),
                combined_dex=het["combined"] if het else None, combined_err_inflated_dex=het["combined_err_inflated"] if het else None,
                chi2_per_dof=het["chi2_per_dof"] if het else None, z=z)


def _verdict(z, what, differs):
    if z is None or not np.isfinite(z):
        return None, f"{what} undefined, comparability not established"
    if abs(z) < Z_COMPARABLE:
        return True, f"|{what}| = {abs(z):.2f} < {Z_COMPARABLE:g}"
    return False, (f"|{what}| = {abs(z):.2f} >= {Z_COMPARABLE:g}: {differs}; control fractions are not overlap or "
                   "leakage evidence")


def comparability(rec, blk, residual):
    """Data-driven comparability of one block record (drop) or one fold-key record (test_only)."""
    zp = rec.get("mark_zero_point_confound")
    zraw = zp["z_observed_minus_control_mean_over_sd"] if zp else None
    base = dict(rule_threshold_abs_z=Z_COMPARABLE, raw_mark_zero_point_z=zraw)
    if rec.get("degenerate"):
        return dict(base, comparable_to_controls=None, statistic=None, z=None,
                    reason="degenerate block: no selected kept row, fractions undefined")
    if blk == "drop_recentered_czbin":
        ok, why = _verdict(residual["z"] if residual else None, "residual member split z",
                           "inside the 2000 km/s recentring bins the excluded rows differ from the rows a control "
                           "excludes in their mark (member-minus-non-member split at the strata's matching "
                           "resolution), which czbin recentring does not remove")
        return dict(base, comparable_to_controls=ok, statistic="residual_member_split_after_czbin_recentring",
                    z=residual["z"] if residual else None, residual=residual, reason=why)
    if blk == "drop" and rec.get("control_replicates_used", 0) <= 1:
        zraw = None
    ok, why = _verdict(zraw, "raw mark zero-point z", "the kept set's raw mark zero point lies outside the spread "
                                                       "of the control kept sets")
    return dict(base, comparable_to_controls=ok, statistic="raw_mark_zero_point_z", z=zraw, reason=why)


def apply_comparability(r, blk, residual):
    """Overwrite the R106 label fields of a scored block with the data-driven verdicts; returns them."""
    if blk == "test_only":
        out = {}
        for key, rec in r.items():
            c = comparability(rec, blk, residual)
            rec["comparable_to_controls"] = c["comparable_to_controls"]
            rec.pop("not_comparable_reason", None)
            if c["comparable_to_controls"] is False:
                rec["not_comparable_reason"] = c["reason"]
            out[key] = c
        return out
    c = comparability(r, blk, residual)
    r["comparable_to_controls"] = c["comparable_to_controls"]
    r.pop("not_comparable_reason", None)
    if c["comparable_to_controls"] is False:
        r["not_comparable_reason"] = c["reason"]
    return c


def zero_point_diagnostics(cz, dd, eps, member, K, inc, k_label="Ktot", member_label="2MRS CORAS input member"):
    """R106 member-minus-nonmember split per 2000 km/s bin, the same at matched K, and a weighted linear fit.

    k_label / member_label name the K regressor and the member indicator in the fit's model string (review CF4-4)."""
    sel = inc.astype(bool)
    out = {}
    rows, het = member_split(cz, dd, eps, member, np.ones(len(cz), bool))
    out["all_rows_by_cz"] = dict(bins=rows, **het,
                                 note=f"R106 statistic (zero_points.sixdf_delta_d_2mrs_member_minus_nonmember) with "
                                      f"member = [{member_label}], all {len(cz):,} rows")
    for label, keep in (("all_rows", np.ones(len(cz), bool)), ("r105_selected_rows", sel)):
        cells, _ = member_split(cz, dd, eps, member, keep, K, .25)
        het = None
        if len(cells) > 1:
            from scripts.r106.cf3_overlap import heterogeneity
            het = heterogeneity([r["diff"] for r in cells.values()], [r["err"] for r in cells.values()])
        out[f"matched_K_cells_{label}"] = dict(cells=cells, n_cells=len(cells),
                                               n_rows=int(sum(r["n_member"] + r["n_nonmember"] for r in cells.values())),
                                               combined=het, K_variable=k_label)
        # weighted linear model delta_d = a_czbin + b K + c member on rows of `keep`
        zb = np.floor(cz / 2000.).astype(int)
        ub = np.unique(zb[keep])
        X = np.column_stack([(zb[keep] == u).astype(float) for u in ub] + [K[keep], member[keep].astype(float)])
        w = 1. / eps[keep] ** 2
        A = X.T @ (X * w[:, None])
        beta = np.linalg.solve(A, X.T @ (w * dd[keep]))
        cov = np.linalg.inv(A)
        res = dd[keep] - X @ beta
        chi2 = float(np.sum(w * res ** 2))
        dof = int(keep.sum() - X.shape[1])
        out[f"linear_fit_{label}"] = dict(
            model=f"delta_d = a(2000 km/s cz bin) + b*{k_label} + c*[{member_label}]; weights 1/epsilon_d^2",
            b_per_mag=float(beta[-2]), b_err=float(np.sqrt(cov[-2, -2])), c_member_dex=float(beta[-1]),
            c_err=float(np.sqrt(cov[-1, -1])), chi2=chi2, dof=dof,
            c_err_inflated=float(np.sqrt(cov[-1, -1] * max(1., chi2 / dof))))
    return out


# --------------------------------------------------------------------------- R106 context (mirrors r106 build())

def build_context(args):
    from scripts.r105 import cf4_field_holdout as mark
    from scripts.r105 import cf4_coras_marks as cmarks
    from scripts.r105 import coras_reduce
    from scripts.r104 import cf4_2mrs_field as field
    from scripts.r106 import cf3_overlap as r106

    import os
    if os.popen(f"git -C '{r106.DONOR}' rev-parse HEAD").read().strip() != r106.DONOR_COMMIT:
        raise ValueError("CORAS donor commit changed")
    const = r106.coras_constants()
    old, s, inc, x, nn_mu, links, alpha, u, models, field_sha = mark.source_sample()
    mrs = r106.load_2mrs()
    N = s["n"]
    names = np.asarray(s["ids"])
    cz6 = s["cz_gal"].astype(float)
    n6 = field.to_galactic(field.hp.ang2vec(s["ra"], s["dec"], lonlat=True))
    nm = r106.unit_gal(mrs["lat"], mrs["lon"])
    czm_cmb = mrs["cz"] + r106.frame_shift(mrs["lat"], mrs["lon"], const["frames"]["CMB"])
    mm = r106.sky_match(n6, cz6, nm, czm_cmb)
    keep_cmb, _ = r106.coras_2mrs_input(mrs, const, "CMB")
    mrs_row = mm["best"]
    in_2mrs = mrs_row >= 0
    in_coras = in_2mrs & keep_cmb[np.maximum(mrs_row, 0)]
    ks_2mrs = np.where(in_2mrs, mrs["ks"][np.maximum(mrs_row, 0)], np.nan)

    ref = json.loads((r106.R105 / "CF4_FIELD_HOLDOUT.json").read_text())
    folds = {}
    for key, clusters in links.items():
        folds[key] = []
        for f, (tr, te) in enumerate(old.group_kfold_indices(clusters, n_splits=5, seed=42)):
            if hashlib.sha256(("\n".join(sorted(names[te])) + "\n").encode()).hexdigest() != \
                    ref["folds"][key]["folds"][f]["sorted_test_id_sha256"]:
                raise ValueError("R105 fold identity mismatch")
            folds[key].append((tr, te))

    y = np.where(inc, s["delta_d"], np.nan)
    sig = s["epsilon_d"]
    zbin = np.floor(cz6 / r106.CZ_BIN).astype(int)
    strata = 2 * zbin + inc.astype(int)
    rb = np.floor(cz6 / r106.CZ_RECENTER_BIN).astype(int)
    rbins = np.unique(rb)
    zp_acc = dict(wy=np.where(inc, s["delta_d"] / sig ** 2, 0.), w=np.where(inc, 1. / sig ** 2, 0.),
                  eps_sel=np.where(inc, sig, 0.), sel=inc.astype(float),
                  binm=(rb[:, None] == rbins[None, :]).astype(float),
                  bin_labels=[f"{int(k * r106.CZ_RECENTER_BIN)}-{int((k + 1) * r106.CZ_RECENTER_BIN)}" for k in rbins])
    base = dict(old=old, mark=mark, x=x, inc=inc, y=y, sig=sig, folds=folds, strata=strata, cz=cz6, zp=zp_acc)
    field_ref = {key: [r["scores_shared_minus_zero"] for r in ref["folds"][key]["folds"]] for key in folds}
    scorers = [r106.Scorer("R105_field_holdout", nn_mu, models, base, field_ref, 1e-9,
                           contrasts={"fixed_2mrs_offset_minus_offset_only": ("fixed_2mrs_offset", "offset_only"),
                                      "trained_scale_offset_minus_offset_only": ("trained_scale_offset", "offset_only")})]
    geom, growth, sci, z = cmarks.site_geometry()
    coras_inputs = {}
    for spec in args.coras:
        directory, reference = (Path(t) for t in spec.split("="))
        rec, *_ = coras_reduce.metadata(directory, geom)
        if rec.get("catalogue") != geom["catalogue"] or rec.get("nodes") != ["SQ-CF4"]:
            raise ValueError("6dFGSv catalogue binding mismatch")
        seeds = list(range(rec["first"], rec["last"] + 1))
        residuals = [f"residual_{i}.tsv" for i in seeds]
        if set(rec["output_sha256"]) != set(residuals) | {"mean.tsv"}:
            raise ValueError("partial CORAS draw set")

        def read(name, directory=directory, rec=rec):
            p = directory / name
            if coras_reduce._sha(p) != rec["output_sha256"][name]:
                raise ValueError(f"field hash mismatch: {p}")
            return coras_reduce.read_radial(p, geom["ids"])

        mean = read("mean.tsv")
        offsets = np.array([-300., -100., 0., 100., 300.])
        mus = [np.zeros(N), nn_mu[models["fixed_2mrs"]][0]]
        tags = [("zero", 0.), ("nn", 0.)]
        for off in offsets:
            mus.append(old.r99.finite_shift(sci, z, np.arctanh(off / old.r100.C), "bolometric") / (5 * old.r100.MAG))
            tags.append(("offset", off))
        for nm_ in ["mean.tsv", *residuals]:
            v = mean if nm_ == "mean.tsv" else mean + read(nm_)
            for off in offsets:
                mus.append(old.r99.finite_shift(sci, z, np.arctanh((off + growth * v) / old.r100.C), "bolometric") /
                           (5 * old.r100.MAG))
                tags.append((nm_, off))
        mus = np.array(mus)
        tn, tu = np.array([t[0] for t in tags]), np.array([t[1] for t in tags])
        draw = np.isin(tn, residuals)
        choices = dict(zero=tn == "zero", nn=tn == "nn", offset_only=tn == "offset", coras_mean=(tn == "mean.tsv") & (tu == 0),
                       coras_mean_offset=tn == "mean.tsv", coras_draws=draw & (tu == 0), coras_draws_offset=draw)
        if len(seeds) >= 4:
            for half, subset in enumerate(np.array_split(residuals, 2)):
                choices[f"coras_half{half + 1}_offset"] = np.isin(tn, subset)
        cref = json.loads(reference.read_text())
        cfolds = {key: [r["shared_minus_zero"] for r in cref["folds"][key]] for key in folds}
        label = f"CORAS_{len(seeds)}draws_r{rec['config']['radial']}_l{rec['config']['ell']}_fft{rec['config']['fft']}"
        if np.max(abs(mus[tn == "offset"] - nn_mu[models["offset_only"]])) > 1e-12:
            raise ValueError("offset-only components differ from R105 field-holdout offsets")
        scorers.append(r106.Scorer(label, mus, choices, base, cfolds, 1e-7, contrasts={
            "coras_mean_offset_minus_offset_only": ("coras_mean_offset", "offset_only"),
            "coras_draws_offset_minus_offset_only": ("coras_draws_offset", "offset_only")}))
        coras_inputs[label] = dict(directory=str(directory), reference=str(reference),
                                   run_json_sha256=sha256_file(directory / "run.json"),
                                   reference_sha256=sha256_file(reference), mean_sha256=rec["output_sha256"]["mean.tsv"],
                                   n_components=int(len(mus)), seeds=[seeds[0], seeds[-1]])
    replays = {}
    for sc in scorers:
        t = time.time()
        rep = sc.replay()
        replays[sc.name] = dict(max_abs_fold_replay_error=rep["max_abs_fold_replay_error"], tolerance=sc.tol,
                                seconds=time.time() - t, sum_full=rep["sum_full"])
    return dict(scorers=scorers, names=names, cz=cz6, inc=inc, s=s, in_coras=in_coras, in_2mrs=in_2mrs,
                ks_2mrs=ks_2mrs, base=base, replays=replays, coras_inputs=coras_inputs, field_sha=field_sha)


_POOL: dict = {}


def _run(task):
    """task = (scorer index, set label, block, strata label, stream)."""
    si, ename, blk, slabel, stream = task
    t = time.time()
    sc = _POOL["scorers"][si]
    a = _POOL["args"]
    X = _POOL["sets"][ename]
    st = _POOL["strata"][slabel]
    if blk == "test_only":
        sc2 = copy.copy(sc)
        sc2.b = dict(sc.b, strata=st)
        seed = a.seed if slabel == "r106" else a.seed + KSEED_OFFSET + (0 if slabel == "k0.25" else 1)
        # comparable= only sets R106 label fields and changes no number; build() overwrites those fields with the
        # data-driven verdict (apply_comparability) before anything is summarised or written
        r = sc2.test_only(X, a.replicates, seed, comparable=True)
    elif blk == "drop":
        r = sc.drop(X, a.drop_replicates, a.seed, strata=st, strata_label=_POOL["labels"][slabel], stream=stream)
    elif blk == "drop_recentered_czbin":
        r = sc.drop(X, a.drop_replicates, a.seed, recenter="czbin", strata=st, strata_label=_POOL["labels"][slabel],
                    stream=stream)
    else:
        raise ValueError(blk)
    return r, time.time() - t


def _entry_labels(degenerate, comp, exch):
    """Compact labels copied into every score entry of a summarised block."""
    return dict(degenerate=bool(degenerate), comparable_to_controls=comp["comparable_to_controls"] if comp else None,
                fraction_excluded_rows_fixed_in_every_control=exch["fraction_excluded_in_strata_fully_excluded"] if exch else None,
                effective_n_randomised=exch["effective_n_randomised"] if exch else None)


def _block_labels(degenerate, comp, exch, recorded=None):
    out = dict(degenerate=bool(degenerate), comparable_to_controls=comp["comparable_to_controls"] if comp else None,
               comparability=comp, exchangeability=exch,
               control_fractions_conditional_on=(
                   None if not exch else
                   f"{exch['n_excluded_in_strata_fully_excluded']} of {exch['n_excluded']} excluded rows "
                   f"({100 * (exch['fraction_excluded_in_strata_fully_excluded'] or 0.):.1f}%) sit in strata the exclusion "
                   f"empties and are excluded in every control replicate; the fractions randomise only the "
                   f"{exch['effective_n_randomised']} mixed-strata rows ({exch['counted']})"))
    if recorded is not None:
        out.update(recorded)
    return out


def summarize(block, keys, comp=None, exch=None, recorded=None):
    """Compact view: observed, control mean/sd and tail counts for each key/score, with the comparability verdict,
    the degenerate flag and the exchangeability of the strata carried into every entry (review CF4-1).

    drop blocks: comp/exch/recorded are block-level dicts; test_only: dicts keyed by fold key (pgc, pgc1)."""
    out = {}
    if block is None:
        return None
    if "per_key" in block:   # drop
        lab = _entry_labels(block.get("degenerate"), comp, exch)
        for key, r in block["per_key"].items():
            out[key] = {k: dict(observed=r["sum_kept_minus_zero"][k], control_mean=c["mean"], control_sd=c["sd"],
                                k_le=c.get("k_control_le_observed"), k_ge=c.get("k_control_ge_observed"),
                                p_le_plus_one=c.get("p_le_plus_one"), p_ge_plus_one=c.get("p_ge_plus_one"),
                                replicates=c.get("replicates"), **lab)
                        for k, c in r["control"].items() if k in keys}
        zp = block.get("mark_zero_point_confound")
        out["raw_zero_point_z"] = zp["z_observed_minus_control_mean_over_sd"] if zp else None
        out["raw_zero_point_observed_dex"] = zp["observed"] if zp else None
        out["raw_zero_point_control_mean_dex"] = zp["control"]["mean"] if zp else None
        out["control_replicates_used"] = block["control_replicates_used"]
        out.update(_block_labels(block.get("degenerate"), comp, exch, recorded))
        return out
    for key, r in block.items():   # test_only
        c = r["control"]
        ck, ek = (comp or {}).get(key), (exch or {}).get(key)
        lab = _entry_labels(r.get("degenerate"), ck, ek)
        out[key] = {k: dict(observed=r["sum_kept_minus_zero"][k], control_mean=c[k]["mean"], control_sd=c[k]["sd"],
                            k_le=c[k].get("k_control_le_observed"), k_ge=c[k].get("k_control_ge_observed"),
                            p_le_plus_one=c[k].get("p_le_plus_one"), p_ge_plus_one=c[k].get("p_ge_plus_one"),
                            replicates=c[k].get("replicates"), **lab)
                    for k in keys if k in c and isinstance(c[k], dict) and "mean" in c[k]}
        zp = r.get("mark_zero_point_confound")
        out[key]["raw_zero_point_z"] = zp["z_observed_minus_control_mean_over_sd"] if zp else None
        out[key]["raw_zero_point_observed_dex"] = zp["observed"] if zp else None
        out[key]["raw_zero_point_control_mean_dex"] = zp["control"]["mean"] if zp else None
        out[key].update(_block_labels(r.get("degenerate"), ck, ek, (recorded or {}).get(key)))
    return out


def recorded_r106_labels(block, blk):
    """The labels R106 itself recorded for a reference block (kept beside the R108 data-driven verdict)."""
    if blk == "test_only":
        return {key: dict(comparable_to_controls_as_recorded_r106=r.get("comparable_to_controls"),
                          not_comparable_reason_as_recorded_r106=r.get("not_comparable_reason"))
                for key, r in block.items()}
    return dict(comparable_to_controls_as_recorded_r106=block.get("comparable_to_controls"),
                not_comparable_reason_as_recorded_r106=block.get("not_comparable_reason"))


def build(args):
    t0 = time.time()
    ctx = build_context(args)
    if args.scorer_names:
        missing = set(args.scorer_names) - {sc.name for sc in ctx["scorers"]}
        if missing:
            raise ValueError(f"unknown scorer names {missing}")
        ctx["scorers"] = [sc for sc in ctx["scorers"] if sc.name in args.scorer_names]
    names, cz, inc, s = ctx["names"], ctx["cz"], ctx["inc"], ctx["s"]
    fp_path = args.directory / "D03/J_MNRAS_443_1231_FPsample.vot"
    K, kinfo = load_ktot(fp_path, names)
    if not np.all(np.isfinite(K)):
        raise ValueError("Ktot missing for some 6dFGSv rows")
    member = ctx["in_coras"]
    dr3_path = args.directory / "D03/VII_259_6dfgs.vot"
    AV, dr3info = load_dr3(dr3_path, names)
    Kc = K - A_K_OVER_A_V * AV
    # cross-check with the R106 crosstable flag
    with gzip.open(R106_JSON_GZ, "rt") as fh:
        r106j = json.load(fh)
    n_r106 = r106j["sixdf"]["twomrs"]["n_in_coras_input_cmb"]
    if int(member.sum()) != int(n_r106):
        raise ValueError("2MRS CORAS-input membership differs from R106")
    ks = ctx["ks_2mrs"]
    dk = K[member] - ks[member]
    dkc = Kc[member] - ks[member]
    kcomp = dict(n=int(member.sum()), median_Ktot_minus_2MRS_Ks=float(np.median(dk)),
                 p5_p50_p95=np.percentile(dk, [5, 50, 95]).tolist(),
                 extinction_corrected_minus_2MRS_Ks_p5_p50_p95=np.percentile(dkc, [5, 50, 95]).tolist(),
                 note="2MRS Ks (CORAS 2MRS member file) is extinction corrected; Ktot is 2MASS k_m_ext")

    # strata
    base_strata = ctx["base"]["strata"]
    kb25, e25 = kbins(K, .25)
    kb50, e50 = kbins(K, .5)
    strata = {"r106": base_strata, "k0.25": k_strata(base_strata, kb25), "k0.5": k_strata(base_strata, kb50)}
    labels = {"r106": "global random exclusion with the same cz_gal 500 km/s bin x inclusion counts (R106)",
              "k0.25": "cz_gal 500 km/s bin x inclusion x Ktot 0.25 mag bin counts",
              "k0.5": "cz_gal 500 km/s bin x inclusion x Ktot 0.5 mag bin counts"}
    # magnitude-only analogue of the 2MRS set
    order = np.argsort(K, kind="stable")
    nset = int(member.sum())
    kstar = float(K[order[nset - 1]])
    kset = K <= kstar
    sets = {"2MRS_coras_input": member, "complement_keep_only_2MRS_coras_input": ~member,
            "Ktot_le_Kstar_same_size": kset}
    exch = {f"{e}|{sl}": exchangeability(strata[sl], X, inc) for e, X in sets.items() for sl in ("k0.25", "k0.5")
            if e != "Ktot_le_Kstar_same_size"}
    folds = ctx["base"]["folds"]
    _exch_cache: dict = {}

    def exch_of(ename, blk, slabel):
        """Exchangeability of one scored block: per fold key inside the held-out sets (test_only) or global (drop)."""
        kind = "test_only" if blk == "test_only" else "drop"
        if (ename, kind, slabel) not in _exch_cache:
            X, st = sets[ename], strata[slabel]
            _exch_cache[ename, kind, slabel] = (
                {key: exchangeability(st, X, inc, groups=[te for _, te in folds[key]]) for key in folds}
                if kind == "test_only" else exchangeability(st, X, inc))
        return _exch_cache[ename, kind, slabel]

    # data-driven residual for the czbin-recentred blocks, per exclusion set and strata (review CF4-1)
    residuals = {f"{e}|{sl}": residual_record(cz, s["delta_d"], s["epsilon_d"], X, K, inc, RESIDUAL_K_WIDTH[sl])
                 for e, X in sets.items() for sl in RESIDUAL_K_WIDTH}

    # task list
    tasks = []
    for si in range(len(ctx["scorers"])):
        tasks.append((si, "2MRS_coras_input", "drop_recentered_czbin", "r106", 2))   # reproduction gate
        for e in SETS:
            tasks.append((si, e, "test_only", "k0.25", None))
            tasks.append((si, e, "test_only", "k0.5", None))
            if not (args.reduced and e != "2MRS_coras_input"):
                tasks.append((si, e, "drop", "k0.25", 4))
            tasks.append((si, e, "drop_recentered_czbin", "k0.25", 4))
            if e == "2MRS_coras_input" and not args.reduced:   # 0.5 mag sensitivity, headline set only
                tasks.append((si, e, "drop_recentered_czbin", "k0.5", 5))
        tasks.append((si, "Ktot_le_Kstar_same_size", "test_only", "r106", None))
        tasks.append((si, "Ktot_le_Kstar_same_size", "drop", "r106", 2))
        tasks.append((si, "Ktot_le_Kstar_same_size", "drop_recentered_czbin", "r106", 2))
    if args.only_gate:
        tasks = [t for t in tasks if t[3] == "r106" and t[1] == "2MRS_coras_input"]
    _POOL.update(scorers=ctx["scorers"], args=args, sets=sets, strata=strata, labels=labels)

    def cost(t):
        n = len(ctx["scorers"][t[0]].mus)
        return n * (1 if t[2] == "test_only" else 33)

    tasks.sort(key=lambda t: -cost(t))
    if args.jobs > 1:
        with mp.get_context("fork").Pool(args.jobs) as pool:
            done = dict(zip(tasks, pool.map(_run, tasks, chunksize=1)))
    else:
        done = {t: _run(t) for t in tasks}

    # reproduction gate against R106
    gate = {}
    for si, sc in enumerate(ctx["scorers"]):
        t = (si, "2MRS_coras_input", "drop_recentered_czbin", "r106", 2)
        r, _ = done[t]
        ref = r106j["scoring"][sc.name]["exclusions"]["2MRS_coras_input"]["drop_recentered_czbin"]
        worst = 0.
        for key in r["per_key"]:
            for k in sc.keys:
                if k == "zero":
                    continue
                a_, b_ = r["per_key"][key]["sum_kept_minus_zero"][k], ref["per_key"][key]["sum_kept_minus_zero"][k]
                worst = max(worst, abs(a_ - b_))
                ca, cb = r["per_key"][key]["control"][k]["mean"], ref["per_key"][key]["control"][k]["mean"]
                worst = max(worst, abs(ca - cb))
        gate[sc.name] = dict(max_abs_difference_observed_and_control_mean=worst, tolerance=1e-6, passed=worst <= 1e-6)
    if not all(g["passed"] for g in gate.values()):
        raise ValueError(f"R106 reproduction gate failed: {gate}")

    keys_of = {sc.name: [k for k in sc.keys if k != "zero"] for sc in ctx["scorers"]}
    scoring, overview = {}, {}

    def overview_row(comp, ex):
        return dict(comparable_to_controls=comp["comparable_to_controls"], statistic=comp["statistic"], z=comp["z"],
                    raw_mark_zero_point_z=comp["raw_mark_zero_point_z"],
                    fraction_excluded_rows_fixed_in_every_control=ex["fraction_excluded_in_strata_fully_excluded"],
                    effective_n_randomised=ex["effective_n_randomised"])

    for si, sc in enumerate(ctx["scorers"]):
        res, ov = {}, {}
        for t, (r, sec) in sorted(done.items(), key=lambda kv: kv[0][1:4]):
            if t[0] != si:
                continue
            _, ename, blk, slabel, _ = t
            name = f"{ename}|{blk}|{slabel}"
            comp = apply_comparability(r, blk, residuals[f"{ename}|{slabel}"])
            ex = exch_of(ename, blk, slabel)
            res[name] = dict(summary=summarize(r, keys_of[sc.name], comp, ex), seconds=sec, stream=t[4],
                             strata=labels[slabel])
            ov[name] = ({key: overview_row(comp[key], ex[key]) for key in comp} if blk == "test_only"
                        else overview_row(comp, ex))
        scoring[sc.name], overview[sc.name] = res, ov
    # R106 references per set and block (same summary layout); R106's own labels are kept beside the R108 verdict
    r106_ref = {}
    for sc in ctx["scorers"]:
        r106_ref[sc.name] = {}
        for e in SETS:
            for blk in ("test_only", "drop", "drop_recentered_czbin"):
                src = r106j["scoring"][sc.name]["exclusions"][e].get(blk)
                if not isinstance(src, dict):
                    continue
                rec = recorded_r106_labels(src, blk)
                blk_copy = copy.deepcopy(src)
                comp = apply_comparability(blk_copy, blk, residuals[f"{e}|r106"])
                r106_ref[sc.name][f"{e}|{blk}|r106"] = summarize(blk_copy, keys_of[sc.name], comp, exch_of(e, blk, "r106"),
                                                                 rec)

    zp = zero_point_diagnostics(cz, s["delta_d"], s["epsilon_d"], member, K, inc)
    zp["r106_reference_combined_dex"] = r106j["zero_points"]["sixdf_delta_d_2mrs_member_minus_nonmember"]["combined_difference_dex"]
    zpc = zero_point_diagnostics(cz, s["delta_d"], s["epsilon_d"], member, Kc, inc, k_label="Kc")
    zp["extinction_corrected_K"] = {k: v for k, v in zpc.items() if k != "all_rows_by_cz"}
    zp["extinction_corrected_K"]["definition"] = "Kc = Ktot - 0.114 AV (VII/259 AV); same cells and fit as above"
    zp["Ktot_le_Kstar_minus_rest_by_cz"] = zero_point_diagnostics(cz, s["delta_d"], s["epsilon_d"], kset, K, inc,
                                                                  member_label=MEMBER_LABEL["Ktot_le_Kstar_same_size"])["all_rows_by_cz"]

    inputs = {"fpsample": fp_path, "dr3_6dfgs": dr3_path, "code": Path(__file__), "r106_json_gz": R106_JSON_GZ, "r105_field_holdout": R105 / "CF4_FIELD_HOLDOUT.json",
              "r105_coras_marks": R105 / "CF4_CORAS_MARKS.json"}
    for lab, rec in ctx["coras_inputs"].items():
        inputs[f"coras_reference_{lab}"] = Path(rec["reference"])
        inputs[f"coras_run_json_{lab}"] = Path(rec["directory"]) / "run.json"
    from scripts.r106 import cf3_overlap as r106
    for nm_ in ("data/2MRS_group_member_catalog.dat", "configuration.hpp", "src/transformations.cpp"):
        inputs[f"coras_donor_{nm_}"] = r106.DONOR / nm_
    payload = dict(
        schema="htt.r108.cf4.kband_contrast/1",
        classification=dict(label="CONDITIONAL", depends_on="R105 working mark model, CF3-calibrated CORAS fsigma8 and "
                            "bulk, and the K-matching variable (2MASS k_m_ext, not the 2MRS extinction-corrected Ks)",
                            scope="relative held-out log predictive differences and finite-replicate control fractions; "
                                  "no calibrated p, no physical attribution",
                            control_fractions="K-matched control fractions are conditional on the excluded rows in strata "
                                              "the exclusion empties (excluded in every replicate; fraction and "
                                              "effective_n_randomised in every summarised entry); fractions of blocks "
                                              "with comparable_to_controls != true are not overlap or leakage evidence"),
        comparability_rule=dict(
            threshold_abs_z=Z_COMPARABLE,
            raw_blocks="test_only (per fold key) and drop: comparable iff |raw mark zero-point z| < threshold, z = (kept-set "
                       "inverse-variance mean raw delta_d - control mean)/control sd under the same masks",
            drop_recentered_czbin="comparable iff |residual member-minus-non-member split z| < threshold at the strata's "
                                  "matching resolution inside the 2000 km/s recentring bins (comparability_residuals)",
            degenerate="comparable_to_controls = null",
            replaces="R108 first pass passed comparable=True for every block; R106 recorded false for its magnitude-defined "
                     "test_only/drop blocks and true for drop_recentered_czbin (kept as *_as_recorded_r106 in "
                     "r106_reference)"),
        comparability_residuals=residuals, comparability_overview=overview,
        git=git_state(),
        script=dict(path=str(Path(__file__).resolve().relative_to(ROOT)), sha256=sha256_file(Path(__file__))), command=" ".join(shlex.quote(a) for a in [sys.executable, "-B", "-m",
                                                                     "scripts.r108.cf4_kband_contrast", *sys.argv[1:]]),
        input_paths={k: str(p) for k, p in inputs.items()},
        input_sha256={k: sha256_file(p) for k, p in inputs.items()},
        field_sha256=ctx["field_sha"], coras_inputs=ctx["coras_inputs"],
        ktot=kinfo, dr3=dr3info, ktot_vs_2mrs_ks=kcomp, k_bin_edges={"0.25": e25.tolist(), "0.5": e50.tolist()},
        magnitude_only_set=dict(Kstar_mag=kstar, n=int(kset.sum()), n_overlap_with_2mrs=int(np.sum(kset & member)),
                                n_2mrs_not_in_set=int(np.sum(member & ~kset)), n_set_not_2mrs=int(np.sum(kset & ~member))),
        exchangeability=exch,
        exchangeability_note="keys set|strata: global counts over all rows (drop-type draws); per-block counts (test_only "
                             "inside each fold's held-out set) are in each summarised entry",
        r106_fold_replay=ctx["replays"], r106_reproduction_gate=gate,
        scoring=scoring, r106_reference=r106_ref, zero_points=zp,
        seeds=dict(seed=args.seed, test_only_k0p25=[args.seed + KSEED_OFFSET, "0|1"],
                   test_only_k0p5=[args.seed + KSEED_OFFSET + 1, "0|1"], drop_k0p25=[args.seed, 4],
                   drop_czbin_k0p5=[args.seed, 5], r106_streams=[args.seed, 2],
                   replicates=args.replicates, drop_replicates=args.drop_replicates),
        task_list=[list(map(str, t)) for t in tasks], reduced=bool(args.reduced),
        wall_seconds=time.time() - t0)
    write_json(args.output, payload)
    return payload


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--directory", type=Path, default=DL)
    p.add_argument("--output", type=Path, default=OUT_DEFAULT)
    p.add_argument("--coras", nargs="*", default=DEFAULT_CORAS)
    p.add_argument("--replicates", type=int, default=2000)
    p.add_argument("--drop-replicates", type=int, default=64)
    p.add_argument("--seed", type=int, default=20261124)
    p.add_argument("--jobs", type=int, default=1)
    p.add_argument("--only-gate", action="store_true", help="run only the R106 reproduction gate blocks")
    p.add_argument("--reduced", action="store_true",
                   help="omit the complement drop (K 0.25) and the K 0.5 czbin blocks (runtime budget for 128-draw CORAS)")
    p.add_argument("--scorer-names", nargs="*", default=None,
                   help="restrict scoring to these scorers (all are still rebuilt and fold-replayed)")
    p.add_argument("--trace-opens", type=Path, default=None,
                   help="record every file opened by the run (JSON lines) for the pre-existing-input receipts")
    a = p.parse_args(argv)
    if a.trace_opens:
        from scripts.r108.cf4_receipts import install_open_trace
        install_open_trace(a.trace_opens, "scripts.r108.cf4_kband_contrast")
    res = build(a)
    print(json.dumps(dict(output=str(a.output), gate=res["r106_reproduction_gate"], wall_seconds=res["wall_seconds"]),
                     indent=1))


if __name__ == "__main__":
    main()
