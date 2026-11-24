"""R108 lane cf4, A1(i): 6dFGSv membership in the real Cosmicflows-3 table3, CF3 method attribution and the CORAS
CF3 calibration window, replacing the R106 proxies.

R106 (scripts/r106/cf3_overlap.py) matched the 8,885 6dFGSv rows to the CF3 member file distributed with CORAS and
attributed CF3 methods through CF4 table2 because VizieR J/AJ/152/50 table3 was not local.  This module matches the
same 8,885 rows (R100 intake table1.txt, the R105/R106 positions) to table3 by three independent routes

* name route:     6dFGS designation gHHMMSSs+DDMMSS decoded to ICRS, <= NAME_ARCSEC to table3 GLON/GLAT, |dcz| <= 500 km/s;
* PGC route:      R103 rule (15 arcsec, 500 km/s, closest) 6dFGSv -> CF4 table2 PGC, then table3 PGC;
* position route: table1 RA/Dec -> table3 GLON/GLAT (1e-4 deg precision), R103 metric 15 arcsec and 500 km/s
                  (6dFGSv cz_gal is CMB frame; table3 Vcmb is CMB frame, Fixsen et al. 1996 apex);

and classifies each row as matched (all routes with a hit name one table3 row), ambiguous (routes disagree, or the
position or name window holds several rows) or unmatched.  "Routes agree" counts (n_DM_P_counterpart_routes_agree)
include the ambiguous_window_multiple rows, whose routes name one row but whose window held several; the
matched-status count is reported beside it (review CF4-3).  For matched rows it reports the CF3 source letters (r_Dist),
the DM-P (6dFGS FP with CF3 zero point) presence, DM-P minus the 6dFGSv modulus, the CORAS calibration-window
membership recomputed from the table3 nest columns (<HV> + CORAS CMB/LG frame shift at GGLON/GGLAT, window
[2000, 16000] km/s as read by r106.coras_constants) and the 6dF share of the window's distance information at
galaxy level (R106 style) and at source level ((e_DM/e_DM-P)^2 per galaxy).  Every per-row result is compared
with the R106 crosstable.

Inputs (SHA-256 recorded at run time; the values at writing are)
  D01/J_AJ_152_50_table3.vot   8ff91a41f05458892be2c5dd8a3855b99079c1362c17defba6ca8a2f58b9ffc4 (17,669 rows)
  D01/J_AJ_152_50_table2.vot   17124d39f6a09ba86e5506969a22963c278db7d786ebdeec07d6eea6e20b7e90 (11,508 rows)
  D02/J_MNRAS_445_2677_table1.vot 3a9fa69ffba01dc32720dcc034b0bfbb8c600a9604ee7fa89ed8fbf8e7371ef4 (8,885 rows)
  R100 table1.txt              08f3d4b264e28efcb574bea4efa370d66e4f299f8254e21bd04979fb8301a14d
  R106 SIXDF_CF3_2MRS_CROSSTABLE.tsv 38283acb2d4a2504908c68699b4862501f4871cf68b749e1ae59bd2ff6b881de
  CF3 ReadMe (R9 CDS copy)     74ebe9ea1431f0612c350624fd64ed70089ff0a28ecc7d5fd02eb13ab7694f0f
  CORAS donor configuration (commit 45ab2563...) through r106.coras_constants

Units: cz and velocities km/s (CMB frame unless stated), moduli mag, separations arcsec, shares dimensionless.

Usage (repo root, PYTHONPATH=.:htt:htt/src):
  python -B -m scripts.r108.cf4_cf3_table3_overlap --output docs/.../R108_LOS_ATLAS_DATA_20261124/CF4/CF3_TABLE3_OVERLAP.json

Deterministic (no random numbers).  Claim class: catalogue lineage bookkeeping; no physical attribution.
"""
from __future__ import annotations

import argparse
import csv
import json
import shlex
import sys
import time
import warnings
from pathlib import Path

import numpy as np

from scripts.r108.common import git_state, sha256_file, write_json

ROOT = Path(__file__).resolve().parents[2]
DL = Path.home() / "Downloads/htt_r108/cf4"
OUT_DEFAULT = ROOT / "docs/research_program/observational_publication_20261015/R108_LOS_ATLAS_DATA_20261124/CF4/CF3_TABLE3_OVERLAP.json"
R106_CROSSTAB = Path.home() / "Downloads/htt_r106_analysis/cf3/SIXDF_CF3_2MRS_CROSSTABLE.tsv"
R106_JSON_GZ = ROOT / "docs/research_program/observational_publication_20261015/R106_RESEARCH_20261124/CF3/CF3_OVERLAP.json.gz"
CF3_README = ROOT / ".agent-harness/runs/R9-SELECTED-LAW-20260913/artifacts/calibration_candidate/sources/CF3_ReadMe.txt"
C = 299792.458
ARCSEC, DV = 15., 500.
TIGHT_ARCSEC = 2.
NAME_ARCSEC = 2.5
CZ_BINS = ((0, 6000), (6000, 10000), (10000, 14000), (14000, 20000))


def load_vot(path):
    from astropy.io.votable import parse_single_table
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return parse_single_table(str(path)).to_table(use_names_over_ids=True)


def _f(col, fill=np.nan):
    return np.asarray(np.ma.filled(np.ma.asarray(col).astype(float), fill), float)


def read_table3(path):
    t = load_vot(path)
    if len(t) != 17669:
        raise ValueError(f"CF3 table3 rows {len(t)} != 17669 (ReadMe)")
    pgc = np.asarray(t["PGC"], np.int64)
    if len(np.unique(pgc)) != len(pgc):
        raise ValueError("table3 PGC not unique")
    nest = np.ma.filled(np.ma.asarray(t["Nest"]).astype(np.int64), 0)
    return dict(n=len(t), pgc=pgc, glon=_f(t["GLON"]), glat=_f(t["GLAT"]), hv=_f(t["HV"]), vcmb=_f(t["Vcmb"]),
                dm=_f(t["DM"]), edm=_f(t["e_DM"]), dmp=_f(t["DM-P"]), edmp=_f(t["e_DM-P"]),
                rdist=np.asarray(t["r_Dist"]).astype(str), odist=np.asarray(t["o_Dist"], np.int64), nest=nest,
                ghv=_f(t["<HV>"]), gvcmb=_f(t["<Vcmb>"]), gglon=_f(t["GGLON"]), gglat=_f(t["GGLAT"]),
                gdm=_f(t["<DM>"]), gedm=_f(t["e_<DM>"]), s14=np.asarray(t["S14"], np.int64))


def group_keys(t3):
    """Nest identifier, or a unique negative key for galaxies without a nest (singletons)."""
    return np.where(t3["nest"] > 0, t3["nest"], -(np.arange(t3["n"]) + 1))


def route_candidates(best, counts):
    """Per row: (table3 indices named by the routes, window_multiple).  best: per-route arrays of the chosen table3
    index (-1 none); counts: per-route window multiplicities (sky_match 'count') of the routes that have a window
    (position, name).  window_multiple is true when any of those windows held more than one row (review CF4-3)."""
    best = [np.asarray(b) for b in best]
    counts = [np.asarray(c) for c in counts]
    return [([int(b[i]) for b in best], bool(any(c[i] > 1 for c in counts))) for i in range(len(best[0]))]


def classify(candidates):
    """candidates: list (per row) of lists of table3 indices found by the routes (duplicates allowed) plus a flag
    'window_multiple' when a route window (position or name) held > 1 row.  Returns status array and the chosen
    index."""
    status = np.empty(len(candidates), dtype=object)
    chosen = np.full(len(candidates), -1, np.int64)
    for i, (cands, multi) in enumerate(candidates):
        u = sorted(set(c for c in cands if c >= 0))
        if not u:
            status[i] = "unmatched"
        elif len(u) > 1:
            status[i] = "ambiguous_routes_disagree"
        elif multi:
            status[i] = "ambiguous_window_multiple"
            chosen[i] = u[0]
        else:
            status[i] = "matched"
            chosen[i] = u[0]
    return status, chosen


def window_flags(ghv, gglat, gglon, frames, lo, hi):
    from scripts.r106 import cf3_overlap as r106
    out = {}
    for fr in ("CMB", "LG"):
        v = ghv + r106.frame_shift(gglat, gglon, frames[fr])
        out[fr] = (v >= lo) & (v <= hi)
    return out


def information_shares(t3, keys, is6df, window):
    """Window-level 6dF share of distance information: galaxy flag (R106 style) and source level (e_DM/e_DM-P)^2."""
    w = 1. / t3["edm"] ** 2
    f_src = np.where(is6df & np.isfinite(t3["edmp"]), np.minimum(1., (t3["edm"] / t3["edmp"]) ** 2), 0.)
    uk, inv = np.unique(keys, return_inverse=True)
    G = len(uk)
    wden = np.bincount(inv, weights=w, minlength=G)
    share_gal = np.bincount(inv, weights=w * is6df, minlength=G) / wden
    share_src = np.bincount(inv, weights=w * f_src, minlength=G) / wden
    first = np.zeros(G, np.int64)
    first[inv[::-1]] = np.arange(len(inv))[::-1]
    gedm = t3["gedm"][first]
    v = np.maximum(t3["gvcmb"][first], 1.)
    wm = 1. / gedm ** 2
    wv = 1. / (np.log(10.) / 5. * v * gedm) ** 2
    out = {}
    for fr, W in window.items():
        Wg = W[first]
        out[fr] = dict(n_nests_in_window=int(Wg.sum()), n_nests_total=int(G),
                       n_window_nests_with_6df_member=int(np.sum(Wg & (share_gal > 0))),
                       mu_share_galaxy_flag=float((share_gal * wm)[Wg].sum() / wm[Wg].sum()),
                       mu_share_source_level=float((share_src * wm)[Wg].sum() / wm[Wg].sum()),
                       velocity_share_galaxy_flag=float((share_gal * wv)[Wg].sum() / wv[Wg].sum()),
                       velocity_share_source_level=float((share_src * wv)[Wg].sum() / wv[Wg].sum()))
    out["definition"] = ("nest weights 1/e_<DM>^2 (mu) or 1/(ln10/5 v e_<DM>)^2 with v=<Vcmb> (velocity); within a nest, "
                         "galaxy weights 1/e_DM^2; galaxy_flag counts a DM-P galaxy fully, source_level counts "
                         "(e_DM/e_DM-P)^2 (the DM-P inverse-variance fraction of the galaxy average, capped at 1)")
    return out


def position_pairing_record(rows, tight_arcsec, name_arcsec, dv_gate):
    """Data-driven description of the position-only pairings (review CF4-2): the rule tests position only, so the
    record states the cz differences it leaves and whether the designation-decoded position (name route, no cz gate)
    names the same table3 row; identity is never asserted."""
    dcz = np.array([r["sixdfv_cz_minus_cf3_vcmb_kms"] for r in rows], float)
    same = [r["name_route_no_cz_gate_pgc"] is not None and r["name_route_no_cz_gate_pgc"] == r["pgc"] for r in rows]
    for r, ok in zip(rows, same):
        r["name_route_no_cz_gate_same_row"] = bool(ok)
        r["exceeds_cz_gate"] = bool(abs(r["sixdfv_cz_minus_cf3_vcmb_kms"]) > dv_gate)
    n = len(rows)
    if n:
        note = (f"nearest DM-P row within {tight_arcsec:g} arcsec with no cz gate; 6dFGSv cz_gal minus CF3 Vcmb ranges "
                f"from {dcz.min():+.0f} to {dcz.max():+.0f} km/s (|dcz| median {np.median(abs(dcz)):.0f}, max "
                f"{abs(dcz).max():.0f} km/s; {int(np.sum(abs(dcz) > dv_gate))} of {n} exceed the {dv_gate:g} km/s gate); "
                f"{sum(same)} of {n} are named by the designation-decoded position within {name_arcsec:g} arcsec "
                f"(also positional, no cz gate). Same-galaxy identity is not verified.")
    else:
        note = "no 6dFGSv row was paired by position only"
    return dict(rule=f"nearest DM-P row within {tight_arcsec:g} arcsec, no cz gate, not claimed by another 6dFGSv row",
                n_resolved=n, resolved_rows=rows, identity_verified=False,
                n_name_route_no_cz_gate_same_row=int(sum(same)),
                sixdfv_cz_minus_cf3_vcmb_kms_min_max=[float(dcz.min()), float(dcz.max())] if n else None,
                abs_dcz_kms_median=float(np.median(abs(dcz))) if n else None,
                n_exceeding_cz_gate=int(np.sum(abs(dcz) > dv_gate)), note=note)


def robust(d):
    d = np.asarray(d, float)
    d = d[np.isfinite(d)]
    if not len(d):
        return dict(n=0)
    med = float(np.median(d))
    return dict(n=int(len(d)), median=med, robust_sd_1p4826mad=float(1.4826 * np.median(abs(d - med))),
                mean=float(d.mean()), rms_about_mean=float(d.std()),
                percentiles_1_16_50_84_99=np.percentile(d, [1, 16, 50, 84, 99]).tolist(),
                max_abs_minus_median=float(np.max(abs(d - med))))


def read_crosstab(path):
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    if len(rows) != 8885:
        raise ValueError("R106 crosstable rows changed")
    return rows


def build(args):
    t0 = time.time()
    from scripts.r100 import cf4_upstream_and_kband as r100
    from scripts.r103 import cf4_shared_field_holdout as h
    from scripts.r104 import cf4_2mrs_field as r104
    from scripts.r106 import cf3_overlap as r106

    d = args.directory
    paths = dict(table3=d / "D01/J_AJ_152_50_table3.vot", table2=d / "D01/J_AJ_152_50_table2.vot",
                 sixdfv_vizier=d / "D02/J_MNRAS_445_2677_table1.vot", sixdfv_local=r100.SIXDF_PATH,
                 cf4_table2=r100.r97.RAW_CF4 / "table2.dat", r106_crosstab=R106_CROSSTAB, r106_json_gz=R106_JSON_GZ,
                 cf3_readme=CF3_README, vizier_meta_D01=d / "D01/vizier_J_AJ_152_50_meta.html",
                 vizier_meta_D02=d / "D02/vizier_J_MNRAS_445_2677_meta.html",
                 coras_configuration=r106.DONOR / "configuration.hpp",
                 coras_transformations=r106.DONOR / "src/transformations.cpp")
    sha = {k: sha256_file(p) for k, p in paths.items()}

    # -- row counts against the ReadMe and the VizieR catalogue page
    readme = r106.cf3_readme_counts(CF3_README.read_text())
    t3 = read_table3(paths["table3"])
    t2v = load_vot(paths["table2"])
    meta1 = paths["vizier_meta_D01"].read_text(errors="replace")
    meta2 = paths["vizier_meta_D02"].read_text(errors="replace")
    import re
    vc = {m.group(1): int(m.group(2)) for m in re.finditer(r"(J/[A-Za-z]+/[0-9]+/[0-9]+/\w+)\s*</A>.*?\((\d+) rows\)",
                                                            meta1 + meta2, re.S)}
    if not vc:
        vc = {m.group(1): int(m.group(2)) for m in re.finditer(r"(J/[A-Za-z]+/[0-9]+/[0-9]+/\w+)[^()]*?\((\d+) rows\)",
                                                                re.sub(r"<[^>]+>", " ", meta1 + meta2))}
    sixv = load_vot(paths["sixdfv_vizier"])
    rowcheck = dict(readme=readme, vizier_catalogue_page_rows=vc,
                    table3_rows=int(t3["n"]), table2_rows=int(len(t2v)), sixdfv_vizier_rows=int(len(sixv)),
                    table3_rows_with_DM_P=int(np.isfinite(t3["dmp"]).sum()),
                    table3_rows_r_Dist_contains_P=int(sum("P" in s for s in t3["rdist"])),
                    table3_e_DM_P_values=sorted(set(np.round(t3["edmp"][np.isfinite(t3["edmp"])], 3).tolist())),
                    pass_table3=int(t3["n"]) == readme["table3_galaxies"],
                    pass_table2=int(len(t2v)) == readme["table2_nests"],
                    pass_sixdf_fp_count=int(np.isfinite(t3["dmp"]).sum()) == readme["sixdfgs_fp_distances"])

    # -- 6dFGSv: R100 intake (R105/R106 positions) vs VizieR J/MNRAS/445/2677 table1
    s = r100.load_sixdf_pv()
    names = np.asarray(s["ids"])
    vn = np.asarray(sixv["6dFGS"]).astype(str)
    same_order = bool(np.array_equal(vn, names))
    ident = dict(same_names_same_order=same_order,
                 max_abs_ra_deg=float(np.max(abs(_f(sixv["RAJ2000"]) - s["ra"]))) if same_order else None,
                 max_abs_dec_deg=float(np.max(abs(_f(sixv["DEJ2000"]) - s["dec"]))) if same_order else None,
                 n_czgal_differ=int(np.sum(_f(sixv["czgal"]) != s["cz_gal"])) if same_order else None,
                 max_abs_delta_d=float(np.max(abs(_f(sixv["log(Dz/DH)"]) - s["delta_d"]))) if same_order else None,
                 max_abs_epsilon_d=float(np.max(abs(_f(sixv["e_log(Dz/DH)"]) - s["epsilon_d"]))) if same_order else None)

    cz6 = s["cz_gal"].astype(float)
    n6 = r104.to_galactic(r104.hp.ang2vec(s["ra"], s["dec"], lonlat=True))
    n3 = r106.unit_gal(t3["glat"], t3["glon"])
    has_p = np.isfinite(t3["dmp"])

    # routes
    mpos = r106.sky_match(n6, cz6, n3, t3["vcmb"], arcsec=ARCSEC, dv=DV)
    mtight = r106.sky_match(n6, cz6, n3, t3["vcmb"], arcsec=TIGHT_ARCSEC, dv=np.inf)
    dn = r106.designation_radec(names, "6df")
    nname = r104.to_galactic(r106.icrs_unit(dn[:, 0], dn[:, 1]))
    mname = r106.sky_match(nname, cz6, n3, t3["vcmb"], arcsec=NAME_ARCSEC, dv=DV)
    t2 = r100.load_cf4_table2()
    m4 = h.sixdf_match_ambiguity_policies(t2, s, arcsec=ARCSEC, dv_kms=DV)
    cl = m4["closest_table2_indices"]
    pgc4 = np.where(cl >= 0, t2["pgc"][np.maximum(cl, 0)], -1)
    idx3 = {int(p): i for i, p in enumerate(t3["pgc"])}
    mpgc = np.array([idx3.get(int(p), -1) for p in pgc4])
    cands = route_candidates([mpos["best"], mname["best"], mpgc], [mpos["count"], mname["count"]])
    status, chosen = classify(cands)
    ok = chosen >= 0
    chosen_p = ok & has_p[np.maximum(chosen, 0)]
    used, counts = np.unique(chosen[ok], return_counts=True)
    dup_rows = used[counts > 1]

    def per_route(m):
        return dict(n_hit=int((m >= 0).sum()), n_hit_with_DM_P=int(np.sum((m >= 0) & has_p[np.maximum(m, 0)])))

    route_agreement = dict(
        position=dict(per_route(mpos["best"]), **r106.match_summary(mpos)),
        name=dict(per_route(mname["best"]), **r106.match_summary(mname)),
        pgc=dict(per_route(mpgc), n_sixdfv_with_cf4_pgc=int((pgc4 >= 0).sum())),
        tight_position_no_cz_gate=dict(per_route(mtight["best"]), **r106.match_summary(mtight)),
        position_and_name_agree=int(np.sum((mpos["best"] >= 0) & (mpos["best"] == mname["best"]))),
        position_and_pgc_agree=int(np.sum((mpos["best"] >= 0) & (mpos["best"] == mpgc))),
        pgc_and_name_agree=int(np.sum((mpgc >= 0) & (mpgc == mname["best"]))),
        all_three_agree=int(np.sum((mpos["best"] >= 0) & (mpos["best"] == mname["best"]) & (mpos["best"] == mpgc))))
    st_counts = {k: int(np.sum(status == k)) for k in ("matched", "ambiguous_window_multiple",
                                                       "ambiguous_routes_disagree", "unmatched")}
    # explicit remainder: 6dFGSv rows without a unique DM-P counterpart, and DM-P rows not claimed by any 6dFGSv row
    claimed = np.zeros(t3["n"], bool)
    claimed[chosen[ok]] = True
    unclaimed_p = np.flatnonzero(has_p & ~claimed)
    near = r106.sky_match(n6, cz6, n3[has_p], t3["vcmb"][has_p], arcsec=600., dv=np.inf)
    pidx = np.flatnonzero(has_p)

    def row_rec(i):
        j = near["best"][i]
        return dict(row=int(i + 1), sixdf_id=str(names[i]), cz_gal=int(cz6[i]), status=str(status[i]),
                    position_pgc=int(t3["pgc"][mpos["best"][i]]) if mpos["best"][i] >= 0 else None,
                    name_pgc=int(t3["pgc"][mname["best"][i]]) if mname["best"][i] >= 0 else None,
                    cf4_pgc_route_pgc=int(pgc4[i]) if pgc4[i] >= 0 else None,
                    pgc_route_in_table3=bool(mpgc[i] >= 0),
                    nearest_DM_P_row_pgc=int(t3["pgc"][pidx[j]]) if j >= 0 else None,
                    nearest_DM_P_sep_arcsec=float(near["sep_arcsec"][i]) if j >= 0 else None,
                    nearest_DM_P_dcz_kms=float(near["dv_kms"][i]) if j >= 0 else None,
                    chosen_has_DM_P=bool(chosen_p[i]))
    remainder_rows = np.flatnonzero(~chosen_p)
    # position-only pairing of the remainder: nearest DM-P row within TIGHT_ARCSEC that no other row claimed
    near_j = np.where(near["best"] >= 0, pidx[np.maximum(near["best"], 0)], -1)
    resolved = [int(i) for i in remainder_rows
                if near_j[i] >= 0 and near["sep_arcsec"][i] <= TIGHT_ARCSEC and not claimed[near_j[i]]]
    res_targets = near_j[resolved] if resolved else np.array([], np.int64)
    claimed_after = claimed.copy()
    claimed_after[res_targets] = True
    # independent positional check of those pairings: the designation-decoded position (name route) with no cz gate
    mname_nogate = r106.sky_match(nname, cz6, n3, t3["vcmb"], arcsec=NAME_ARCSEC, dv=np.inf)
    pairing = position_pairing_record(
        [dict(sixdf_id=str(names[i]), pgc=int(t3["pgc"][near_j[i]]), sep_arcsec=float(near["sep_arcsec"][i]),
              sixdfv_cz_minus_cf3_vcmb_kms=float(-near["dv_kms"][i]),
              name_route_no_cz_gate_pgc=int(t3["pgc"][mname_nogate["best"][i]]) if mname_nogate["best"][i] >= 0 else None,
              name_route_no_cz_gate_window_count=int(mname_nogate["count"][i]))
         for i in resolved], TIGHT_ARCSEC, NAME_ARCSEC, DV)
    remainder = dict(
        n_sixdfv_without_DM_P_counterpart_routes_agree=int(len(remainder_rows)),
        sixdfv_rows=[row_rec(i) for i in remainder_rows],
        n_DM_P_rows_not_claimed=int(len(unclaimed_p)),
        DM_P_rows_not_claimed=[dict(pgc=int(t3["pgc"][j]), glon=float(t3["glon"][j]), glat=float(t3["glat"][j]),
                                    vcmb=float(t3["vcmb"][j]), r_Dist=str(t3["rdist"][j])) for j in unclaimed_p],
        table3_rows_claimed_by_more_than_one_sixdfv_row=[int(t3["pgc"][j]) for j in dup_rows],
        position_only_resolution=dict(
            pairing,
            n_distinct_targets=int(len(set(res_targets.tolist()))),
            n_DM_P_rows_still_unclaimed=int(np.sum(has_p & ~claimed_after)),
            n_sixdfv_rows_still_without_DM_P=int(len(remainder_rows) - len(resolved)),
            counts_after_pairing_note="the two counts above treat the position-only pairings as counterparts; "
                                      "identity is not verified (identity_verified=false)"))

    # -- method attribution of the matched DM-P rows
    j = chosen[chosen_p]
    letters, lc = np.unique(t3["rdist"][j], return_counts=True)
    method = dict(r_Dist_composition={str(a): int(b) for a, b in zip(letters, lc)},
                  o_Dist_histogram={int(a): int(b) for a, b in zip(*np.unique(t3["odist"][j], return_counts=True))},
                  n_single_source_P=int(np.sum(t3["rdist"][j] == "P")),
                  n_with_other_sources=int(np.sum(t3["rdist"][j] != "P")),
                  other_source_letter_counts={L: int(sum(L in r for r in t3["rdist"][j])) for L in "CTLMSNHIF"},
                  n_vizier_S14_link_flag=int(np.sum(t3["s14"][j] == 1)),
                  note="r_Dist letters per CF3 ReadMe note 3 (P=6dFGS FP; F=ENEAR/EFAR/SMAC FP; H,I=TF; N=SNIa; S=SBF)")

    # -- zero points: DM-P (6dF FP, CF3 zero point) vs the 6dFGSv modulus; DM (CF3 average) vs DM-P
    mu6 = r106.mu_from_delta(cz6, s["delta_d"])
    dmp = np.where(chosen_p, t3["dmp"][np.maximum(chosen, 0)], np.nan)
    dm = np.where(chosen_p, t3["dm"][np.maximum(chosen, 0)], np.nan)
    multi = chosen_p & (t3["rdist"][np.maximum(chosen, 0)] != "P")
    zp = dict(convention="mu_6dF = 5 log10[(1+z) D_C(z_CMB; Om=0.3, H0=75) 10^-delta_d] + 25 (r106.mu_from_delta)",
              DM_P_minus_mu6dF=robust(dmp - mu6),
              DM_P_minus_mu6dF_by_cz={f"{a}-{b}": robust((dmp - mu6)[(cz6 >= a) & (cz6 < b)]) for a, b in CZ_BINS},
              DM_minus_DM_P_multi_source=robust((dm - dmp)[multi]),
              DM_minus_DM_P_single_source=robust((dm - dmp)[chosen_p & ~multi]))

    # -- CORAS calibration window from the table3 nest columns
    const = r106.coras_constants()
    lo, hi = const["calibration_cz_window_kms"]
    win3 = window_flags(t3["ghv"], t3["gglat"], t3["gglon"], const["frames"], lo, hi)
    win_fixsen = (t3["gvcmb"] >= lo) & (t3["gvcmb"] <= hi)
    g = np.maximum(chosen, 0)
    cal_cmb, cal_lg = ok & win3["CMB"][g], ok & win3["LG"][g]
    cal_any = cal_cmb | cal_lg
    keys = group_keys(t3)
    shares = information_shares(t3, keys, has_p, win3)

    # -- comparison with R106 (CORAS member file route and window)
    ct = read_crosstab(R106_CROSSTAB)
    if [r["sixdf_id"] for r in ct] != names.tolist():
        raise ValueError("R106 crosstable row order differs")
    r106_pgc = np.array([int(r["cf3_pgc"]) for r in ct])
    r106_cmb = np.array([int(r["cf3_group_in_window_cmb"]) for r in ct])
    r106_lg = np.array([int(r["cf3_group_in_window_lg"]) for r in ct])
    r106_cf4pgc = np.array([int(r["cf4_pgc"]) for r in ct])
    r106_any = (r106_cmb == 1) | (r106_lg == 1)
    my_pgc = np.where(ok, t3["pgc"][g], -1)
    comp = dict(
        cf4_pgc_route_identical_to_r106=bool(np.array_equal(r106_cf4pgc, pgc4)),
        r106_cf3_member_any_route=int((r106_pgc >= 0).sum()),
        table3_DM_P_counterpart_routes_agree=int(chosen_p.sum()),
        same_pgc_as_r106=int(np.sum((r106_pgc >= 0) & (r106_pgc == my_pgc))),
        different_pgc_from_r106=int(np.sum((r106_pgc >= 0) & ok & (r106_pgc != my_pgc))),
        r106_member_table3_none=int(np.sum((r106_pgc >= 0) & ~ok)),
        table3_member_r106_none=int(np.sum((r106_pgc < 0) & ok)),
        window_either=dict(r106=int(r106_any.sum()), table3=int(cal_any.sum()),
                           both=int(np.sum(r106_any & cal_any)), r106_only=int(np.sum(r106_any & ~cal_any)),
                           table3_only=int(np.sum(~r106_any & cal_any))),
        window_cmb=dict(r106=int((r106_cmb == 1).sum()), table3=int(cal_cmb.sum()),
                        agree_on_rows_with_both_defined=int(np.sum((r106_cmb >= 0) & ok & ((r106_cmb == 1) == cal_cmb))),
                        n_rows_both_defined=int(np.sum((r106_cmb >= 0) & ok))),
        window_lg=dict(r106=int((r106_lg == 1).sum()), table3=int(cal_lg.sum()),
                       agree_on_rows_with_both_defined=int(np.sum((r106_lg >= 0) & ok & ((r106_lg == 1) == cal_lg))),
                       n_rows_both_defined=int(np.sum((r106_lg >= 0) & ok))))
    with __import__("gzip").open(R106_JSON_GZ, "rt") as fh:
        r106j = json.load(fh)
    r106_window = r106j["cf3_calibration_window"]
    r106_six = r106j["sixdf"]["cf3"]

    window = dict(
        definition=f"nest <HV> + CORAS heliocentric->frame shift at (GGLAT, GGLON); {lo:g} <= v <= {hi:g} km/s "
                   "(CORAS PARAMETER_ESTIMATE window, czMin=2000, DISTANCE_CATALOG_MAX_REDSHIFT_VELOCITY); 5-sigma "
                   "clip of CORAS not reproduced, so window membership is a superset of calibration membership",
        n_sixdfv_matched_in_window_CMB=int(cal_cmb.sum()), n_sixdfv_matched_in_window_LG=int(cal_lg.sum()),
        n_sixdfv_matched_in_window_either=int(cal_any.sum()), n_sixdfv_matched_in_window_both=int((cal_cmb & cal_lg).sum()),
        n_sixdfv_matched_DM_P_in_window_either=int((cal_any & chosen_p).sum()),
        fraction_of_8885_in_window_either=float(cal_any.sum() / len(names)),
        n_sixdfv_matched_outside_window_both=int(np.sum(ok & ~cal_any)),
        alternative_fixsen_Vcmb_window=int(np.sum(ok & win_fixsen[g])),
        table3_nests_in_window={fr: int(np.unique(keys[W]).size) for fr, W in win3.items()},
        information_share=shares,
        r106_values=dict(n_in_calibration_window_either=r106_six["n_in_calibration_window_either"],
                         n_in_calibration_window_CMB=r106_six["n_in_calibration_window_CMB"],
                         n_in_calibration_window_LG=r106_six["n_in_calibration_window_LG"],
                         n_member_any_route=r106_six["n_member_any_route"],
                         velocity_share_CMB=r106_window["CMB"]["velocity_inverse_variance_share_attributable_to_6dfgsv"],
                         mu_share_CMB=r106_window["CMB"]["mu_inverse_variance_share_attributable_to_6dfgsv"]))

    # -- per-row table (large output, kept outside the repository with its SHA-256)
    out_rows = args.rows_tsv
    out_rows.parent.mkdir(parents=True, exist_ok=True)
    if out_rows.exists():
        raise FileExistsError(f"refusing to overwrite {out_rows}")
    cols = ["row", "sixdf_id", "cz_gal", "status", "t3_pgc", "t3_has_DM_P", "t3_r_Dist", "t3_DM", "t3_e_DM", "t3_DM_P",
            "mu6dF_h75", "pos_pgc", "pos_sep_arcsec", "pos_dcz", "name_pgc", "cf4_pgc", "tight_pgc", "nest",
            "window_cmb", "window_lg", "r106_cf3_pgc", "r106_window_cmb", "r106_window_lg"]
    with open(out_rows, "w") as fh:
        fh.write("\t".join(cols) + "\n")
        for i in range(len(names)):
            k = chosen[i]
            fh.write("\t".join(str(v) for v in (
                i + 1, names[i], int(cz6[i]), status[i], int(t3["pgc"][k]) if k >= 0 else -1, int(chosen_p[i]),
                t3["rdist"][k] if k >= 0 else "-", f"{t3['dm'][k]:.2f}" if k >= 0 else "nan",
                f"{t3['edm'][k]:.2f}" if k >= 0 else "nan", f"{dmp[i]:.2f}", f"{mu6[i]:.4f}",
                int(t3["pgc"][mpos["best"][i]]) if mpos["best"][i] >= 0 else -1, f"{mpos['sep_arcsec'][i]:.3f}",
                f"{mpos['dv_kms'][i]:.1f}", int(t3["pgc"][mname["best"][i]]) if mname["best"][i] >= 0 else -1,
                int(pgc4[i]), int(t3["pgc"][mtight["best"][i]]) if mtight["best"][i] >= 0 else -1,
                int(t3["nest"][k]) if k >= 0 else -1, int(cal_cmb[i]), int(cal_lg[i]), int(r106_pgc[i]),
                int(r106_cmb[i]), int(r106_lg[i]))) + "\n")

    payload = dict(
        schema="htt.r108.cf4.cf3_table3_overlap/2",
        script=dict(path=str(Path(__file__).resolve().relative_to(ROOT)), sha256=sha256_file(Path(__file__))),
        classification=dict(label="NUMERICAL", scope="catalogue cross-identification, CF3 method attribution and "
                            "calibration-window bookkeeping with the real CF3 table3; no flow, Pi/G_F or Bianchi "
                            "attribution, no p-value"),
        git=git_state(), command=" ".join(shlex.quote(a) for a in [sys.executable, "-B", "-m",
                                                                     "scripts.r108.cf4_cf3_table3_overlap", *sys.argv[1:]]),
        input_paths={k: str(p) for k, p in paths.items()}, input_sha256=sha,
        row_checks=rowcheck, sixdfv_vizier_vs_r100_intake=ident,
        match_parameters=dict(position=dict(arcsec=ARCSEC, dv_kms=DV, cz="6dFGSv cz_gal (CMB) vs table3 Vcmb",
                                             positions="table3 GLON/GLAT (F8.4 deg)"),
                              name=dict(arcsec=NAME_ARCSEC, dv_kms=DV, decoding="r106.designation_radec('6df')"),
                              pgc="R103 rule 6dFGSv->CF4 table2 (15 arcsec, 500 km/s, closest) then exact table3 PGC",
                              tight=dict(arcsec=TIGHT_ARCSEC, dv_kms=None)),
        status_counts=st_counts, route_agreement=route_agreement,
        n_DM_P_counterpart_routes_agree=int(chosen_p.sum()),
        n_DM_P_counterpart_matched_status=int(np.sum(chosen_p & (status == "matched"))),
        n_DM_P_counterpart_ambiguous_window_multiple=int(np.sum(chosen_p & (status == "ambiguous_window_multiple"))),
        counterpart_count_definitions=dict(
            n_DM_P_counterpart_routes_agree="rows whose routes with a hit name one table3 row that has DM-P (status "
                                            "matched or ambiguous_window_multiple); renamed from n_unique_DM_P_counterpart",
            n_DM_P_counterpart_matched_status="the same restricted to status matched (no route window held > 1 row)",
            window_multiple="position (15 arcsec, 500 km/s) or name (2.5 arcsec, 500 km/s) window held > 1 table3 row"),
        n_matched_counterpart_without_DM_P=int(np.sum(ok & ~chosen_p)),
        remainder=remainder, cf3_method_attribution=method, zero_points=zp,
        calibration_window=window, comparison_with_r106=comp,
        rows_tsv=dict(path=str(out_rows), sha256=sha256_file(out_rows), columns=cols),
        wall_seconds=time.time() - t0)
    write_json(args.output, payload)
    return payload


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--directory", type=Path, default=DL)
    p.add_argument("--output", type=Path, default=OUT_DEFAULT)
    p.add_argument("--rows-tsv", type=Path, default=DL / "results/CF3_TABLE3_SIXDFV_ROWS.tsv")
    p.add_argument("--trace-opens", type=Path, default=None,
                   help="record every file opened by the run (JSON lines) for the pre-existing-input receipts")
    a = p.parse_args(argv)
    if a.trace_opens:
        from scripts.r108.cf4_receipts import install_open_trace
        install_open_trace(a.trace_opens, "scripts.r108.cf4_cf3_table3_overlap")
    res = build(a)
    print(json.dumps(dict(output=str(a.output), status_counts=res["status_counts"],
                          n_DM_P_counterpart_routes_agree=res["n_DM_P_counterpart_routes_agree"],
                          n_DM_P_counterpart_matched_status=res["n_DM_P_counterpart_matched_status"],
                          window_either=res["calibration_window"]["n_sixdfv_matched_in_window_either"],
                          wall_seconds=res["wall_seconds"]), indent=1))


if __name__ == "__main__":
    main()
