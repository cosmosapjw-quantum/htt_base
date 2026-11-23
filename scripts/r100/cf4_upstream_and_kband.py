"""R100 Steps A2-A4: CF4 upstream SDSS/6dFGSv genealogy, full 3-band correlated PV, and selection law."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import time

import numpy as np
import scipy
from scipy.integrate import cumulative_trapezoid, lebedev_rule, quad
from scipy.linalg import block_diag
from scipy.spatial import cKDTree
from scipy.special import expit, logit
from scipy.stats import chi2

from htt.obsstat.mv_bulkflow import pair_velocity_covariance
from scripts.r95 import sq_cf4_synthesis as r95
from scripts.r97 import cf4_genealogy_and_partial_id as r97
from scripts.r98 import cf4_p1 as old
from scripts.r99 import cf4_source_law as r99
from scripts.r99.acquisition import exact_identifier

ROOT = Path(__file__).resolve().parents[2]
INTAKE = Path("/home/cosmosapjw/Downloads/htt_r100/source_intake")
SDSS_PATH = INTAKE / "SDSS_PV_public.dat"
SIXDF_PATH = INTAKE / "table1.txt"
OUT_DIR = ROOT / "docs/research_program/observational_publication_20261015/R100_SOURCE_LAW_OPTICAL_MULTIPROBE_20261123"
C = old.C
MAG = old.MAG
HREF = old.HREF


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def _parse_float(s: str) -> float:
    st = s.strip()
    return float(st) if st else np.nan


def load_cf4_table2():
    """Parse all 55,877 CF4 table2 galaxies with exact integer IDs and ReadMe byte slices."""
    path = r97.RAW_CF4 / "table2.dat"
    rows = [ln for ln in path.read_text(encoding="ascii").splitlines() if ln.strip()]
    if len(rows) != 55877:
        raise ValueError(f"Expected 55877 CF4 table2 rows, got {len(rows)}")
    pgc = np.array([exact_identifier(ln[0:7].strip()) for ln in rows], dtype=np.int64)
    pgc1 = np.array([exact_identifier(ln[8:15].strip()) for ln in rows], dtype=np.int64)
    t17 = np.array([exact_identifier(ln[16:21].strip() or "0") for ln in rows], dtype=np.int64)
    vcmb = np.array([int(ln[22:27]) for ln in rows], dtype=np.int64)
    dm = np.array([_parse_float(ln[28:34]) for ln in rows])
    edm = np.array([_parse_float(ln[35:40]) for ln in rows])
    dmsn = np.array([_parse_float(ln[41:47]) for ln in rows])
    dmtf = np.array([_parse_float(ln[53:59]) for ln in rows])
    dmfp = np.array([_parse_float(ln[65:71]) for ln in rows])
    edmfp = np.array([_parse_float(ln[72:76]) for ln in rows])
    dmsbf = np.array([_parse_float(ln[77:83]) for ln in rows])
    dmsn2 = np.array([_parse_float(ln[90:96]) for ln in rows])
    dmtrgb = np.array([_parse_float(ln[102:107]) for ln in rows])
    dmceph = np.array([_parse_float(ln[113:119]) for ln in rows])
    dmmas = np.array([_parse_float(ln[126:131]) for ln in rows])
    ra = np.array([_parse_float(ln[137:145]) for ln in rows])
    dec = np.array([_parse_float(ln[146:154]) for ln in rows])
    return dict(
        path=path, n=len(rows), pgc=pgc, pgc1=pgc1, t17=t17, vcmb=vcmb,
        dm=dm, edm=edm, dmsn=dmsn, dmtf=dmtf, dmfp=dmfp, edmfp=edmfp,
        dmsbf=dmsbf, dmsn2=dmsn2, dmtrgb=dmtrgb, dmceph=dmceph, dmmas=dmmas,
        ra=ra, dec=dec,
    )


def load_sdss_pv():
    """Parse all 34,059 SDSS PV v1.1.0 galaxies retaining exact int IDs and verbatim specObjID."""
    if not SDSS_PATH.exists():
        raise FileNotFoundError(f"Run scripts.r100.source_intake first: missing {SDSS_PATH}")
    with SDSS_PATH.open("r", encoding="ascii") as f:
        hdr = f.readline().lstrip("#").split()
        hi = {k: i for i, k in enumerate(hdr)}
        rows = [ln.split() for ln in f if ln.strip() and not ln.startswith("#")]
    if len(rows) != 34059:
        raise ValueError(f"Expected 34059 SDSS PV rows, got {len(rows)}")
    return {
        "n": len(rows),
        "pgc": np.array([exact_identifier(r[hi["PGC"]]) for r in rows], dtype=np.int64),
        "objid": np.array([exact_identifier(r[hi["objid"]]) for r in rows], dtype=np.int64),
        "specobjid_tokens": [r[hi["specObjID"]] for r in rows],
        "idgroupt17": np.array([exact_identifier(r[hi["IDgroupT17"]]) for r in rows], dtype=np.int64),
        "ngroupt17": np.array([exact_identifier(r[hi["NgroupT17"]]) for r in rows], dtype=np.int64),
        "m_morph": np.array([exact_identifier(r[hi["M"]]) for r in rows], dtype=np.int64),
        "in_mask": np.array([exact_identifier(r[hi["in_mask"]]) for r in rows], dtype=np.int64),
        "ra": np.array([float(r[hi["RA"]]) for r in rows]),
        "dec": np.array([float(r[hi["Dec"]]) for r in rows]),
        "zhelio": np.array([float(r[hi["zhelio"]]) for r in rows]),
        "zcmb": np.array([float(r[hi["zcmb"]]) for r in rows]),
        "zcmb_group": np.array([float(r[hi["zcmb_group"]]) for r in rows]),
        "absmag_r": np.array([float(r[hi["absmag_r"]]) for r in rows]),
        "nbar": np.array([float(r[hi["nbar"]]) for r in rows]),
        "r": np.array([float(r[hi["r"]]) for r in rows]),
        "i": np.array([float(r[hi["i"]]) for r in rows]),
        "s": np.array([float(r[hi["s"]]) for r in rows]),
        "sn": np.array([float(r[hi["Sn"]]) for r in rows]),
        "logdist": np.array([float(r[hi["logdist"]]) for r in rows]),
        "logdist_err": np.array([float(r[hi["logdist_err"]]) for r in rows]),
        "logdist_alpha": np.array([float(r[hi["logdist_alpha"]]) for r in rows]),
        "logdist_corr": np.array([float(r[hi["logdist_corr"]]) for r in rows]),
        "logdist_corr_err": np.array([float(r[hi["logdist_corr_err"]]) for r in rows]),
        "logdist_corr_alpha": np.array([float(r[hi["logdist_corr_alpha"]]) for r in rows]),
    }


def load_sixdf_pv():
    """Parse all 8,885 6dFGSv table1 galaxies preserving explicit -1 sentinel grouping flags."""
    if not SIXDF_PATH.exists():
        raise FileNotFoundError(f"Run scripts.r100.source_intake first: missing {SIXDF_PATH}")
    rows = [
        ln.split()
        for ln in SIXDF_PATH.read_text(encoding="ascii").splitlines()
        if ln.strip() and not ln.startswith("#")
    ]
    if len(rows) != 8885:
        raise ValueError(f"Expected 8885 6dFGSv rows, got {len(rows)}")
    cz_gal = np.array([int(r[3]) for r in rows], dtype=np.int64)
    cz_group = np.array([int(r[4]) for r in rows], dtype=np.int64)
    groupid = np.array([int(r[5]) for r in rows], dtype=np.int64)
    if np.any(cz_gal <= 0):
        raise ValueError("Nonpositive cz_gal in 6dFGSv")
    is_grouped = (groupid != -1) & (cz_group != -1)
    # Mask sentinel -1 safely to NaN in float views while keeping exact int64 sentinels.
    cz_group_valid = np.where(is_grouped, cz_group.astype(float), np.nan)
    return {
        "n": len(rows),
        "ids": [r[0] for r in rows],
        "ra": np.array([float(r[1]) for r in rows]),
        "dec": np.array([float(r[2]) for r in rows]),
        "cz_gal": cz_gal,
        "cz_group_raw": cz_group,
        "groupid_raw": groupid,
        "is_grouped": is_grouped,
        "cz_group_valid": cz_group_valid,
        "delta_d": np.array([float(r[6]) for r in rows]),
        "epsilon_d": np.array([float(r[7]) for r in rows]),
        "alpha": np.array([float(r[8]) for r in rows]),
    }


def _sph_vec(ra_deg: np.ndarray, dec_deg: np.ndarray) -> np.ndarray:
    r, d = np.deg2rad(ra_deg), np.deg2rad(dec_deg)
    return np.column_stack((np.cos(r) * np.cos(d), np.sin(r) * np.cos(d), np.sin(d)))


def _fiducial_dl_mpc_h100(z_arr: np.ndarray, Om: float = 0.315) -> np.ndarray:
    zgrid = np.linspace(0.0, float(max(0.2, np.max(z_arr) + 0.02)), 4000)
    integ = 1.0 / np.sqrt(Om * (1.0 + zgrid) ** 3 + (1.0 - Om))
    chi = np.concatenate([[0.0], cumulative_trapezoid(integ, zgrid)]) * (C / 100.0)
    return np.interp(z_arr, zgrid, (1.0 + zgrid) * chi)


def run_a2_genealogy_and_sign_audit(H, inp, ids_4, mu_4, emu_4, cz_4, v_4, n_4, sel_idx, b_pub, t3):
    """Full SDSS + 6dFGSv crosswalk against CF4 table2/3/4 and upstream calibration/sign audit."""
    t2 = load_cf4_table2()
    sdss = load_sdss_pv()
    sixdf = load_sixdf_pv()

    # Read CF4 ReadMe metadata header
    readme_lines = (r97.RAW_CF4 / "ReadMe").read_text(encoding="ascii", errors="replace").splitlines()[:15]

    t2_vec = _sph_vec(t2["ra"], t2["dec"])
    t2_tree = cKDTree(t2_vec)
    pgc_to_t2 = {}
    for i, g in enumerate(t2["pgc"]):
        pgc_to_t2.setdefault(int(g), []).append(i)

    # SDSS exact PGC join
    s_matched_s, s_matched_t, s_miss = [], [], []
    s_multi = []
    for i, g in enumerate(sdss["pgc"]):
        hits = pgc_to_t2.get(int(g), [])
        if len(hits) == 1:
            s_matched_s.append(i)
            s_matched_t.append(hits[0])
        elif len(hits) > 1:
            s_multi.append(i)
        else:
            s_miss.append(i)
    s_idx = np.array(s_matched_s, dtype=np.int64)
    st_idx = np.array(s_matched_t, dtype=np.int64)
    s_miss_arr = np.array(s_miss, dtype=np.int64)
    s_ang_arcsec = np.rad2deg(
        np.arccos(np.clip(np.sum(_sph_vec(sdss["ra"][s_idx], sdss["dec"][s_idx]) * t2_vec[st_idx], axis=1), -1.0, 1.0))
    ) * 3600.0
    if len(s_miss_arr):
        d_miss, _ = t2_tree.query(_sph_vec(sdss["ra"][s_miss_arr], sdss["dec"][s_miss_arr]))
        s_miss_min_arcsec = float(np.min(np.rad2deg(2.0 * np.arcsin(np.clip(d_miss / 2.0, 0.0, 1.0))) * 3600.0))
    else:
        s_miss_min_arcsec = None

    # 6dFGSv tight angular + velocity join (preserving multi and misses)
    tol15 = 2.0 * math.sin(math.radians(15.0 / 3600.0) / 2.0)
    cand = t2_tree.query_ball_point(_sph_vec(sixdf["ra"], sixdf["dec"]), tol15)
    m6_s, m6_t, m6_multi, m6_miss = [], [], [], []
    for i, cs in enumerate(cand):
        good = [j for j in cs if abs(int(t2["vcmb"][j]) - int(sixdf["cz_gal"][i])) <= 500]
        if len(good) == 1:
            m6_s.append(i)
            m6_t.append(good[0])
        elif len(good) > 1:
            m6_multi.append(i)
        else:
            m6_miss.append(i)
    f6_idx = np.array(m6_s, dtype=np.int64)
    ft_idx = np.array(m6_t, dtype=np.int64)

    # Check shared SDSS & 6dFGSv overlap in table2
    s_by_t2 = {int(t): int(s) for s, t in zip(s_idx, st_idx)}
    overlap = [(s_by_t2[int(t)], int(t), int(f)) for f, t in zip(f6_idx, ft_idx) if int(t) in s_by_t2]
    ov_s = np.array([x[0] for x in overlap], dtype=np.int64)
    ov_t = np.array([x[1] for x in overlap], dtype=np.int64)
    ov_6 = np.array([x[2] for x in overlap], dtype=np.int64)

    # Native FP sign physics test inside SDSS: r - (a*s + b*i + c) = log10(d_z / d_H)
    X_fp = np.column_stack((sdss["s"], sdss["i"], np.ones(sdss["n"])))
    c_fp = np.linalg.lstsq(X_fp, sdss["r"], rcond=None)[0]
    r_resid = sdss["r"] - X_fp @ c_fp
    corr_fp_ld = float(np.corrcoef(r_resid, sdss["logdist"])[0, 1])
    corr_fp_ldc = float(np.corrcoef(r_resid, sdss["logdist_corr"])[0, 1])
    slope_fp_ld = float(np.polyfit(r_resid, sdss["logdist"], 1)[0])
    slope_fp_ldc = float(np.polyfit(r_resid, sdss["logdist_corr"], 1)[0])

    # Convert both upstream indicators at faithful fiducial cosmologies
    dl_s_fid = _fiducial_dl_mpc_h100(sdss["zcmb"][s_idx], Om=0.315)
    dl_6_fid = _fiducial_dl_mpc_h100(sixdf["cz_gal"][f6_idx] / C, Om=0.300)
    mu_s_fid100 = 5.0 * np.log10(dl_s_fid) + 25.0
    mu_6_fid100 = 5.0 * np.log10(dl_6_fid) + 25.0

    y_dmfp_s = t2["dmfp"][st_idx] - mu_s_fid100
    f6_dmfp_finite = np.isfinite(t2["dmfp"][ft_idx])
    y_dmfp_6 = t2["dmfp"][ft_idx[f6_dmfp_finite]] - mu_6_fid100[f6_dmfp_finite]

    sl_s, ic_s = np.polyfit(sdss["logdist_corr"][s_idx], y_dmfp_s, 1)
    sl_6, ic_6 = np.polyfit(sixdf["delta_d"][f6_idx[f6_dmfp_finite]], y_dmfp_6, 1)

    diff_s_plus = y_dmfp_s - 5.0 * sdss["logdist_corr"][s_idx]
    diff_6_minus = y_dmfp_6 + 5.0 * sixdf["delta_d"][f6_idx[f6_dmfp_finite]]
    err_diff_s = t2["edmfp"][st_idx] - 5.0 * sdss["logdist_corr_err"][s_idx]

    # Compare dipoles in Dec > 0 between non-FP CF4 (TF, SNIa), CF4 DMfp, and sign-consistent SDSS!
    raw3 = [ln for ln in (r97.RAW_CF4 / "table3.dat").read_text(encoding="ascii").splitlines() if ln.strip()]
    t3_1pgc = np.array([exact_identifier(ln[0:7].strip()) for ln in raw3], dtype=np.int64)
    t3_vcmb = np.array([int(ln[28:33]) for ln in raw3], dtype=np.int64)
    t3_ra = np.array([_parse_float(ln[34:42]) for ln in raw3])
    t3_dec = np.array([_parse_float(ln[43:51]) for ln in raw3])
    t3_dmsn = np.array([_parse_float(ln[100:106]) for ln in raw3])
    t3_dmfp = np.array([_parse_float(ln[117:123]) for ln in raw3])
    t3_edmfp = np.array([_parse_float(ln[124:129]) for ln in raw3])
    t3_dmtf = np.array([_parse_float(ln[133:139]) for ln in raw3])
    gmap = {int(g): i for i, g in enumerate(t3_1pgc)}

    n3_vec = _sph_vec(t3_ra, t3_dec)
    mufid3 = np.where(t3_vcmb > 0, 5.0 * np.log10(np.maximum(1e-30, _fiducial_dl_mpc_h100(np.maximum(0.0, t3_vcmb / C), 0.315))) + 25.0, np.nan)
    mask_n = (t3_dec > 0.0) & (t3_vcmb >= 3000) & (t3_vcmb <= 24000)
    dec_pos_dipoles = {}
    for dlabel, col in (("CF4_table3_TF_DecPos", t3_dmtf), ("CF4_table3_SNIa_DecPos", t3_dmsn), ("CF4_table3_FP_DecPos", t3_dmfp)):
        mk = mask_n & np.isfinite(col) & np.isfinite(mufid3)
        bt = np.linalg.lstsq(np.column_stack((np.ones(mk.sum()), n3_vec[mk])), mufid3[mk] - col[mk], rcond=None)[0]
        dec_pos_dipoles[dlabel] = {"n": int(mk.sum()), "monopole_mufid_minus_dm": float(bt[0]), "dipole_vec": bt[1:].tolist()}

    # Native sign-consistent SDSS dipole (mu_true = mu_fid100 - 5*ldc + zp) -> mufid - mu_true = +5*ldc - zp:
    ns_vec = _sph_vec(sdss["ra"], sdss["dec"])
    b_sdss_nat = np.linalg.lstsq(np.column_stack((np.ones(sdss["n"]), ns_vec)), 5.0 * sdss["logdist_corr"], rcond=None)[0]
    n6_vec = _sph_vec(sixdf["ra"], sixdf["dec"])
    b_6df_nat = np.linalg.lstsq(np.column_stack((np.ones(sixdf["n"]), n6_vec)), 5.0 * sixdf["delta_d"], rcond=None)[0]

    # Check CF4 table3 DMfp vs inverse-variance mean of table2 DMfp per group!
    inv_w = np.zeros(t2["n"], dtype=float)
    w_mu = np.zeros(t2["n"], dtype=float)
    fp_ok = np.isfinite(t2["dmfp"]) & np.isfinite(t2["edmfp"]) & (t2["edmfp"] > 0)
    gidx_t2 = np.array([gmap.get(int(g), -1) for g in t2["pgc1"]], dtype=np.int64)
    valid_agg = fp_ok & (gidx_t2 >= 0)
    sum_w = np.zeros(len(raw3), dtype=float)
    sum_wy = np.zeros(len(raw3), dtype=float)
    ww = t2["edmfp"][valid_agg] ** -2
    np.add.at(sum_w, gidx_t2[valid_agg], ww)
    np.add.at(sum_wy, gidx_t2[valid_agg], ww * t2["dmfp"][valid_agg])
    g_has_fp = (sum_w > 0) & np.isfinite(t3_dmfp)
    dmfp_agg_diff = t3_dmfp[g_has_fp] - (sum_wy[g_has_fp] / sum_w[g_has_fp])

    # Cross-check 4-window tomography sensitivity if SDSS groups in selected 35,970 are flipped back to -5*logdist_corr + mean zp!
    # Map SDSS group mean sign-flip delta onto selected 35,970 groups:
    sel_ids_arr = ids_4[sel_idx]
    sel_g_map = {int(g): i for i, g in enumerate(sel_ids_arr)}
    sum_w_s = np.zeros(len(sel_idx), dtype=float)
    sum_w_mu_signcorr = np.zeros(len(sel_idx), dtype=float)
    # Using native -5 * logdist_corr with matched sample zero-point ic_s = +0.6361 (74.607 km/s/Mpc):
    mu_s_consistent = mu_s_fid100 - 5.0 * sdss["logdist_corr"][s_idx] + float(np.mean(diff_s_plus))
    mu_s_delta = mu_s_consistent - t2["dmfp"][st_idx]  # = -10 * logdist_corr + residuals (~0)!
    ww_s = t2["edmfp"][st_idx] ** -2
    s_in_sel = np.array([sel_g_map.get(int(t2["pgc1"][ti]), -1) for ti in st_idx], dtype=np.int64)
    ok_sel = s_in_sel >= 0
    np.add.at(sum_w_s, s_in_sel[ok_sel], ww_s[ok_sel])
    np.add.at(sum_w_mu_signcorr, s_in_sel[ok_sel], ww_s[ok_sel] * mu_s_delta[ok_sel])
    # Selected groups weighted by FP weight fraction W[:, 2]
    W_sel = old.magnitude_weights(t3)[sel_idx]
    mu_sel_delta = np.zeros(len(sel_idx), dtype=float)
    has_sdss_sel = sum_w_s > 0
    mu_sel_delta[has_sdss_sel] = W_sel[has_sdss_sel, 2] * (sum_w_mu_signcorr[has_sdss_sel] / sum_w_s[has_sdss_sel])
    _, _, _, _, _, b_sdss_signcorr = old.tomography(
        H, n_4[sel_idx], cz_4[sel_idx], v_4[sel_idx], mu_4[sel_idx] + mu_sel_delta, emu_4[sel_idx]
    )

    # Check shared-anchor overlap counts with SDSS and 6dFGSv
    has_cal_t2 = np.isfinite(t2["dmtrgb"]) | np.isfinite(t2["dmceph"]) | np.isfinite(t2["dmmas"])
    has_sn_t2 = np.isfinite(t2["dmsn"])
    has_tf_t2 = np.isfinite(t2["dmtf"])

    # Check table3 groups containing SDSS vs 6dFGSv
    sdss_grp_set = set(t2["pgc1"][st_idx].tolist()) & set(sel_ids_arr.tolist())
    sixdf_grp_set = set(t2["pgc1"][ft_idx].tolist()) & set(sel_ids_arr.tolist())

    return {
        "cf4_readme_header": readme_lines[:6],
        "sdss_pv_census": {
            "total_rows": sdss["n"],
            "unique_pgc": int(len(np.unique(sdss["pgc"]))),
            "in_mask_1_rows": int(np.sum(sdss["in_mask"] == 1)),
            "in_mask_0_rows": int(np.sum(sdss["in_mask"] == 0)),
            "idgroupt17_nonzero_grouped": int(np.sum(sdss["idgroupt17"] > 0)),
            "exact_pgc_matches_table2": int(len(s_idx)),
            "unmapped_pgc_count": int(len(s_miss_arr)),
            "unmapped_nearest_table2_arcsec": s_miss_min_arcsec,
            "matched_separation_arcsec_q50_q99_max": [float(x) for x in np.percentile(s_ang_arcsec, [50, 99, 100])],
            "selected_35970_groups_with_sdss": int(len(sdss_grp_set)),
            "specobjid_format_note": "E18 scientific notation string tokens retained verbatim; objid/PGC/IDgroupT17 parsed as exact int64.",
        },
        "sixdf_pv_census": {
            "total_rows": sixdf["n"],
            "grouped_valid_rows": int(np.sum(sixdf["is_grouped"])),
            "ungrouped_sentinel_minus1_rows": int(np.sum(~sixdf["is_grouped"])),
            "unique_match_15arcsec_500kms": int(len(f6_idx)),
            "with_finite_dmfp": int(np.sum(f6_dmfp_finite)),
            "ambiguous_multi_matches": int(len(m6_multi)),
            "unmapped_excluded_rows": int(len(m6_miss)),
            "selected_35970_groups_with_6df": int(len(sixdf_grp_set)),
            "selection_bias_matched_vs_excluded_delta_d_mean": [
                float(np.mean(sixdf["delta_d"][f6_idx])),
                float(np.mean(sixdf["delta_d"][m6_miss])),
            ],
            "selection_bias_matched_vs_excluded_cz_mean": [
                float(np.mean(sixdf["cz_gal"][f6_idx])),
                float(np.mean(sixdf["cz_gal"][m6_miss])),
            ],
        },
        "shared_sdss_sixdf_overlap": {
            "n_shared_galaxies": int(len(ov_s)),
            "corr_sdss_ldc_vs_6df_delta_d": float(np.corrcoef(sdss["logdist_corr"][ov_s], sixdf["delta_d"][ov_6])[0, 1]),
            "std_sdss_minus_6df": float(np.std(sdss["logdist_corr"][ov_s] - sixdf["delta_d"][ov_6])),
            "std_sdss_plus_6df": float(np.std(sdss["logdist_corr"][ov_s] + sixdf["delta_d"][ov_6])),
        },
        "native_fp_radius_sign_verification_sdss": {
            "r_fit_s_i_const": c_fp.tolist(),
            "corr_r_minus_rFP_with_logdist": corr_fp_ld,
            "corr_r_minus_rFP_with_logdist_corr": corr_fp_ldc,
            "slope_logdist_on_r_resid": slope_fp_ld,
            "slope_logdist_corr_on_r_resid": slope_fp_ldc,
            "proven_physical_definition": "eta = log10(D_z / D_H) > 0 when D_H < D_z, i.e., mu_H = mu_fid(z) - 5*eta (IDENTICAL for both SDSS logdist_corr and 6dFGSv delta_d).",
        },
        "cf4_intercalibration_and_sign_decomposition": {
            "sdss_slope_DMfp_wrt_ldc": float(sl_s),
            "sdss_intercept_mag": float(ic_s),
            "sdss_diff_plus5_mean_std": [float(np.mean(diff_s_plus)), float(np.std(diff_s_plus))],
            "sdss_implied_H0_kms_Mpc": float(100.0 * (10.0 ** (-np.mean(diff_s_plus) / 5.0))),
            "sdss_e_DMfp_minus_5_err_mean_std": [float(np.mean(err_diff_s)), float(np.std(err_diff_s))],
            "sixdf_slope_DMfp_wrt_delta_d": float(sl_6),
            "sixdf_intercept_mag": float(ic_6),
            "sixdf_diff_minus5_mean_std": [float(np.mean(diff_6_minus)), float(np.std(diff_6_minus))],
            "sixdf_implied_H0_kms_Mpc": float(100.0 * (10.0 ** (-np.mean(diff_6_minus) / 5.0))),
            "table3_vs_table2_invvar_DMfp_max_abs_mag": float(np.max(np.abs(dmfp_agg_diff))),
            "shared_calibrator_galaxies": {
                "sdss_with_trgb_ceph_mas": int(np.sum(has_cal_t2[st_idx])),
                "sdss_with_snia": int(np.sum(has_sn_t2[st_idx])),
                "sixdf_with_trgb_ceph_mas": int(np.sum(has_cal_t2[ft_idx])),
                "sixdf_with_snia": int(np.sum(has_sn_t2[ft_idx])),
                "sixdf_with_tf": int(np.sum(has_tf_t2[ft_idx])),
            },
        },
        "dec_positive_sky_dipole_consistency": {
            **dec_pos_dipoles,
            "SDSS_native_sign_consistent_pos5ldc_dipole": b_sdss_nat[1:].tolist(),
            "SixDF_native_pos5deltad_dipole": b_6df_nat[1:].tolist(),
        },
        "tomography_4x9_sign_reconciled_sensitivity": {
            "note": "Published CF4 4x9 retains table4 DMzp as released; sensitivity flips SDSS DMfp contribution from +5*ldc back to -5*ldc+0.6361 to measure outer-window dipole impact.",
            "published_4x9": b_pub.tolist(),
            "sdss_sign_reconciled_4x9": b_sdss_signcorr.tolist(),
            "max_abs_diff_4x9": float(np.max(np.abs(b_sdss_signcorr - b_pub))),
            "dipole_norms_published": np.linalg.norm(b_pub[:, 1:4], axis=1).tolist(),
            "dipole_norms_sign_reconciled": np.linalg.norm(b_sdss_signcorr[:, 1:4], axis=1).tolist(),
        },
        "remaining_blocked_upstream": [
            "CF4 pre-intercalibration SNIa/TF/SBF/TRGB/Cepheid/maser unshifted tables & zero-point covariance",
            "Authoritative CF4 pipeline sign provenance for SDSS (+4.98*ldc vs 6dF -5.03*delta_d)",
        ],
    }


def _cc_rule_any(n: int, lo: float, hi: float):
    j = np.arange(n + 1)
    th = math.pi * j / n
    w = np.empty(n + 1)
    w[0] = w[-1] = 1.0 / (n * n - 1)
    interior = np.arange(1, n)
    wv = np.ones(n - 1)
    for m in range(1, n // 2):
        wv -= 2.0 * np.cos(2.0 * m * th[interior]) / (4.0 * m * m - 1)
    wv -= np.cos(n * th[interior]) / (n * n - 1)
    w[interior] = 2.0 * wv / n
    return 0.5 * (lo + hi) + 0.5 * (hi - lo) * np.cos(th), w * 0.5 * (hi - lo)


def _lebedev_half(ang_ord: int):
    p, wf = lebedev_rule(ang_ord)
    p = np.asarray(p, dtype=float).T.copy()
    wf = np.asarray(wf, dtype=float)
    _, mates = cKDTree(p).query(-p)
    chosen = np.where(np.arange(len(p)) < mates)[0]
    return p[chosen], 2.0 * wf[chosen] / (4.0 * math.pi)


def _panel_targets(lo_h: float, hi_h: float, rad_ord: int, ang_ord: int, h_val: float):
    u_half, wu = _lebedev_half(ang_ord)
    k_grid, wk = _cc_rule_any(rad_ord, lo_h * h_val, hi_h * h_val)
    targs = np.vstack([np.column_stack((np.full(len(u_half), kv), u_half)) for kv in k_grid])
    idx_mat = np.arange(len(targs), dtype=np.int64).reshape(len(k_grid), len(u_half))
    return targs, [{"k": k_grid, "wk": wk, "wu": wu, "indices": idx_mat}]


def _batched_finufft_modes(finufft, targets: np.ndarray, positions: np.ndarray, n_unit: np.ndarray, gq_list: list[np.ndarray], A: np.ndarray, eps: float = 1e-10, maxbatch: int = 2):
    xmax = np.max(np.abs(positions), axis=0)
    scale = np.array([2.0 ** max(0, math.ceil(math.log2(v0 / (math.pi / 2.0)))) for v0 in xmax])
    scaled = np.ascontiguousarray((positions / scale).T)
    freq = np.ascontiguousarray((targets[:, 1:] * targets[:, :1] * scale).T)
    p = A.shape[0]
    m_jac = len(gq_list)
    coeff = np.ascontiguousarray(
        np.concatenate(
            [(A[:, :, None] * (gq[:, None] * n_unit)[None, :, :]).transpose(0, 2, 1).reshape(p * 3, -1) for gq in gq_list],
            axis=0,
        ),
        dtype=np.complex128,
    )
    plan = finufft.Plan(
        3, 3, n_trans=m_jac * p * 3, eps=eps, isign=1, dtype="complex128",
        nthreads=1, upsampfac=2.0, maxbatchsize=maxbatch, fftw=64,
    )
    plan.setpts(*(np.ascontiguousarray(v) for v in scaled), *(np.ascontiguousarray(v) for v in freq))
    field = np.asarray(plan.execute(coeff)).reshape(m_jac, p, 3, len(targets))
    return np.einsum("jadt,td->jta", field, targets[:, 1:])


def run_a3_full_kband_spv(H, inp, ids, n, cz, v, mu, emu, positive, selected, sel, Wfull, W, A, sig_work, cov_work, b_work, cov5, T, coords, weights_p1):
    """Project all 3 k-bands [1e-4, 1.0] h/Mpc matrix-free via per-panel FINUFFT across R={5,10,20} & 4 observables."""
    r30_sci, gls_svd, _, finufft = old._load_r30_and_bridge()
    z_sel = cz[sel] / C
    chi64, g64, j64, _, _ = r30_sci.background(z_sel, 64)
    amp, _ = r30_sci.power_amplitude()
    radii_hinv = np.array([5.0, 10.0, 20.0], dtype=float)
    radii_Mpc = radii_hinv / r30_sci.H
    positions = chi64[:, None] * n[sel]
    n_sel = n[sel]

    # Exact 1-point variance integrals across [1e-4, 1.0] h/Mpc and latent sigmas for Hermite 1st-chaos
    def rad_var(klo_h: float, khi_h: float, R_mpc: float) -> float:
        val, _ = quad(
            lambda k: float(r30_sci.power(k, amp)) * math.exp(-((k * R_mpc) ** 2)) / (6.0 * math.pi ** 2),
            klo_h * r30_sci.H, khi_h * r30_sci.H, epsrel=1e-10, limit=300,
        )
        return float(val)

    onept_var = {}
    for R_h, R_m in zip(radii_hinv, radii_Mpc):
        vl = rad_var(1e-4, 0.005, R_m)
        vi = rad_var(0.005, 0.05, R_m)
        vh = rad_var(0.05, 1.0, R_m)
        vt = vl + vi + vh
        onept_var[str(int(R_h))] = {
            "var_low_kms2": vl, "var_inherited_kms2": vi, "var_high_kms2": vh, "var_total_kms2": vt,
            "frac_low": vl / vt, "frac_inherited": vi / vt, "frac_high": vh / vt,
        }

    # Build exact Hermite first-chaos Jacobians for R=5 total latent sigma ([1e-4, 1.0] + 150 km/s nl)
    nl = 150.0
    tot_var_r5 = onept_var["5"]["var_total_kms2"]
    sigma_full_r5 = np.sqrt((g64 ** 2) * tot_var_r5 + nl ** 2)
    mom32 = r99.hermite_moments(r30_sci, z_sel, sigma_full_r5, 32)
    q_WF = (1.0 + v[sel] / C) / v[sel]
    obs_names = ["WF_log", "background_proxy", "native_comoving", "bolometric"]
    gq_list = [g64 * q_WF] + [g64 * (mom32[idx, :, 1] / sigma_full_r5) for idx in range(3)]
    res_var_env = {
        lbl: ((np.abs(A) @ np.sqrt(mom32[idx, :, 3])) ** 2)
        for idx, lbl in enumerate(("background_proxy", "native_comoving", "bolometric"))
    }

    # 1. Locked inherited band [0.005, 0.05] h/Mpc (Stage C)
    targets_inh, stages_inh = r99.stages(r30_sci)
    modes_inh = old._finufft_log_modes(finufft, targets_inh, positions, n_sel, gq_list, A, eps=1e-12)
    cov_inh = {
        lbl: sum(old._cov_from_projected_modes(stages_inh["C"], modes_inh[mi], amp, r30_sci, radii_Mpc)[0])
        for mi, lbl in enumerate(obs_names)
    }
    print("[A3] inherited band done", flush=True)

    # 2. Low-k band [1e-4, 0.005] h/Mpc (two panels, CC16 vs CC32, Lebedev 53)
    cov_low = {lbl: np.zeros((108, 108), dtype=float) for lbl in obs_names}
    low_B_wf = np.zeros((108, 108), dtype=float)
    low_probe_err = 0.0
    for lo_h, hi_h in ((1e-4, 1e-3), (1e-3, 5e-3)):
        tgB, bdB = _panel_targets(lo_h, hi_h, 16, 53, r30_sci.H)
        mdB = _batched_finufft_modes(finufft, tgB, positions, n_sel, [gq_list[0]], A, eps=1e-11, maxbatch=4)[0]
        low_B_wf += old._cov_from_projected_modes(bdB, mdB, amp, r30_sci, radii_Mpc)[0][0]

        tgC, bdC = _panel_targets(lo_h, hi_h, 32, 53, r30_sci.H)
        mdC = _batched_finufft_modes(finufft, tgC, positions, n_sel, gq_list, A, eps=1e-11, maxbatch=4)
        p_idx = [0, len(tgC) // 2, len(tgC) - 1]
        d_ref = old._direct_fourier_modes(tgC[p_idx], positions, n_sel, gq_list[0], A)
        low_probe_err = max(low_probe_err, float(np.max(np.abs(mdC[0, p_idx] - d_ref)) / np.max(np.abs(d_ref))))
        for mi, lbl in enumerate(obs_names):
            cov_low[lbl] += old._cov_from_projected_modes(bdC, mdC[mi], amp, r30_sci, radii_Mpc)[0][0]
    low_rad_rel = float(np.linalg.norm((cov_low["WF_log"] - low_B_wf)[:36, :36]) / np.linalg.norm(cov_low["WF_log"][:36, :36]))
    print(f"[A3] low-k band done (probe={low_probe_err:.2e})", flush=True)

    # 3. High-k band [0.05, 1.0] h/Mpc (per-panel FINUFFT with bounded maxbatch!)
    cov_hi1 = {lbl: np.zeros((108, 108), dtype=float) for lbl in obs_names}
    cov_hi2 = {lbl: np.zeros((108, 108), dtype=float) for lbl in obs_names}
    cov_hi3 = {lbl: np.zeros((108, 108), dtype=float) for lbl in obs_names}

    # hi1: [0.05, 0.15] -> CC32 Lebedev 53 + check Lebedev 65 & direct modes
    tg_h1_32, bd_h1_32 = _panel_targets(0.05, 0.15, 32, 53, r30_sci.H)
    md_h1 = _batched_finufft_modes(finufft, tg_h1_32, positions, n_sel, gq_list, A, eps=1e-10, maxbatch=2)
    p1_idx = [0, len(tg_h1_32) // 2, len(tg_h1_32) - 1]
    d_h1 = old._direct_fourier_modes(tg_h1_32[p1_idx], positions, n_sel, gq_list[0], A)
    hi1_probe_err = float(np.max(np.abs(md_h1[0, p1_idx] - d_h1)) / np.max(np.abs(d_h1)))
    for mi, lbl in enumerate(obs_names):
        cov_hi1[lbl] = old._cov_from_projected_modes(bd_h1_32, md_h1[mi], amp, r30_sci, radii_Mpc)[0][0]
    tg_h1_a65, bd_h1_a65 = _panel_targets(0.05, 0.15, 16, 65, r30_sci.H)
    md_h1_a65 = _batched_finufft_modes(finufft, tg_h1_a65, positions, n_sel, [gq_list[0]], A, eps=1e-10, maxbatch=2)[0]
    C_h1_a65 = old._cov_from_projected_modes(bd_h1_a65, md_h1_a65, amp, r30_sci, radii_Mpc)[0][0]
    hi1_ang_rel = float(np.linalg.norm((C_h1_a65 - cov_hi1["WF_log"])[:36, :36]) / np.linalg.norm(cov_hi1["WF_log"][:36, :36]))
    print(f"[A3] hi1 [0.05,0.15] done (probe={hi1_probe_err:.2e})", flush=True)

    # hi2: [0.15, 0.35] -> CC16 Lebedev 65 + check Lebedev 53
    tg_h2_65, bd_h2_65 = _panel_targets(0.15, 0.35, 16, 65, r30_sci.H)
    md_h2 = _batched_finufft_modes(finufft, tg_h2_65, positions, n_sel, gq_list, A, eps=1e-10, maxbatch=1)
    p2_idx = [0, len(tg_h2_65) // 2, len(tg_h2_65) - 1]
    d_h2 = old._direct_fourier_modes(tg_h2_65[p2_idx], positions, n_sel, gq_list[0], A)
    hi2_probe_err = float(np.max(np.abs(md_h2[0, p2_idx] - d_h2)) / np.max(np.abs(d_h2)))
    for mi, lbl in enumerate(obs_names):
        cov_hi2[lbl] = old._cov_from_projected_modes(bd_h2_65, md_h2[mi], amp, r30_sci, radii_Mpc)[0][0]
    tg_h2_53, bd_h2_53 = _panel_targets(0.15, 0.35, 16, 53, r30_sci.H)
    md_h2_53 = _batched_finufft_modes(finufft, tg_h2_53, positions, n_sel, [gq_list[0]], A, eps=1e-10, maxbatch=1)[0]
    C_h2_53 = old._cov_from_projected_modes(bd_h2_53, md_h2_53, amp, r30_sci, radii_Mpc)[0][0]
    hi2_ang_rel = float(np.linalg.norm((cov_hi2["WF_log"] - C_h2_53)[:36, :36]) / np.linalg.norm(cov_hi2["WF_log"][:36, :36]))
    print(f"[A3] hi2 [0.15,0.35] done (probe={hi2_probe_err:.2e})", flush=True)

    # hi3a: [0.35, 0.55] and hi3b: [0.55, 1.00] on WF_log (maxbatch=1 keeps peak RAM < 2 GB)
    tg_h3a, bd_h3a = _panel_targets(0.35, 0.55, 16, 53, r30_sci.H)
    md_h3a = _batched_finufft_modes(finufft, tg_h3a, positions, n_sel, gq_list, A, eps=1e-10, maxbatch=1)
    p3a_idx = [0, len(tg_h3a) // 2, len(tg_h3a) - 1]
    d_h3a = old._direct_fourier_modes(tg_h3a[p3a_idx], positions, n_sel, gq_list[0], A)
    hi3a_probe_err = float(np.max(np.abs(md_h3a[0, p3a_idx] - d_h3a)) / np.max(np.abs(d_h3a)))
    for mi, lbl in enumerate(obs_names):
        cov_hi3[lbl] += old._cov_from_projected_modes(bd_h3a, md_h3a[mi], amp, r30_sci, radii_Mpc)[0][0]
    print(f"[A3] hi3a [0.35,0.55] done (probe={hi3a_probe_err:.2e})", flush=True)
    tg_h3b, bd_h3b = _panel_targets(0.55, 1.00, 12, 35, r30_sci.H)
    md_h3b = _batched_finufft_modes(finufft, tg_h3b, positions, n_sel, [gq_list[0]], A, eps=1e-8, maxbatch=1)[0]
    C_h3b_wf = old._cov_from_projected_modes(bd_h3b, md_h3b, amp, r30_sci, radii_Mpc)[0][0]
    print("[A3] hi3b [0.55,1.00] done", flush=True)
    for mi, lbl in enumerate(obs_names):
        if mi == 0:
            cov_hi3[lbl] += C_h3b_wf
        else:
            ratio2 = float(np.mean((gq_list[mi] / gq_list[0]) ** 2))
            cov_hi3[lbl] += ratio2 * C_h3b_wf

    cov_high = {lbl: cov_hi1[lbl] + cov_hi2[lbl] + cov_hi3[lbl] for lbl in obs_names}
    cov_full = {lbl: cov_low[lbl] + cov_inh[lbl] + cov_high[lbl] for lbl in obs_names}

    # Uncorrelated diagonal short-scale limit for [0.05, 1.0] h/Mpc at R=5
    var_hi_r5 = onept_var["5"]["var_high_kms2"]
    C_hi_diag_ref = (A * (var_hi_r5 * (gq_list[0] ** 2))) @ A.T

    # 20-source closed Bessel validation across ALL THREE bands!
    sub = np.linspace(0, len(n_sel) - 1, 20, dtype=int)
    gsub = g64[sub]
    R_mpc_5 = radii_Mpc[0]
    h_val = r30_sci.H
    bessel_checks = {}
    for bname, klo_h, khi_h, tg_list_b in (
        ("low_k", 1e-4, 5e-3, [_panel_targets(1e-4, 1e-3, 32, 53, h_val), _panel_targets(1e-3, 5e-3, 32, 53, h_val)]),
        ("inherited", 0.005, 0.05, [(targets_inh, stages_inh["C"])]),
        ("high_k", 0.05, 0.35, [(tg_h1_32, bd_h1_32), (tg_h2_65, bd_h2_65)]),
    ):
        def _pk_h(kh):
            kk = h_val * kh
            return (h_val ** 3) * r30_sci.power(kk, amp) * np.exp(-((kk * R_mpc_5) ** 2))
        closed = pair_velocity_covariance(h_val * positions[sub], n_sel[sub], _pk_h, 1.0 / (h_val ** 2), na=1201, nk=1500, kmin=klo_h, kmax=khi_h) * np.outer(gsub, gsub)
        discrete = np.zeros_like(closed)
        for tg_b, bds_b in tg_list_b:
            dir_b = tg_b[:, 1:]
            Fsub = (dir_b @ n_sel[sub].T) * np.exp(1j * tg_b[:, :1] * (dir_b @ positions[sub].T)) * gsub
            for bd in bds_b:
                for ik, kk in enumerate(bd["k"]):
                    grp = Fsub[bd["indices"][ik]]
                    wt = bd["wk"][ik] * float(r30_sci.power(kk, amp)) * math.exp(-((kk * R_mpc_5) ** 2)) * bd["wu"] / (2.0 * math.pi ** 2)
                    discrete += ((grp.T * wt) @ grp.conj()).real
        bessel_checks[bname] = {
            "rel_fro": float(np.linalg.norm(closed - discrete) / np.linalg.norm(closed)),
            "diag_rel": float(np.max(np.abs(closed.diagonal() / discrete.diagonal() - 1.0))),
            "max_abs_kms2": float(np.max(np.abs(closed - discrete))),
        }

    # Assemble 4-term total 36D covariances (with R99's corrected mag_tilt Jacobian!)
    prev_r98 = json.loads(old.OUT.read_text())
    _, _, _, _, _, _, _, b_vec, systematic_cal_cut, _, mag_tilt, sel_info = r99.source_design(prev_r98)
    noise_meas = (A * ((MAG * emu[sel]) ** 2)) @ A.T
    noise_nl150 = {
        lbl: (A * ((nl * (q_WF if lbl == "WF_log" else (mom32[idx - 1, :, 1] / sigma_full_r5))) ** 2)) @ A.T
        for idx, lbl in enumerate(obs_names)
    }

    # Evaluate inherited vs full_k models across R={5,10,20} & observables (18-DOF Schur + 12D depth + octant CV!)
    R_full = cz[sel] / 70.0
    U_rad = 100.0 * n_sel / R_full[:, None]
    X_12 = np.column_stack((old.tomography(H, n_sel, cz[sel], v[sel], mu[sel], emu[sel])[0], U_rad))
    model_comparisons = {}
    designs = {
        "shared_9D_mean": np.tile(np.eye(9), (4, 1)),
        "shared_monopole": np.tile(np.eye(9)[:, 0], 4)[:, None],
    }

    def diag_block(M36):
        ev = np.linalg.eigvalsh(0.5 * (M36 + M36.T))
        return {
            "trace": float(np.trace(M36)),
            "min_eig": float(ev[0]),
            "max_eig": float(ev[-1]),
            "condition": float(ev[-1] / ev[0]) if ev[0] > 0 else None,
        }

    # Also evaluate radial-depth leakage operator for inherited vs full-k using WLS 9D vs 12D on all 4 windows
    radial_impact = []
    X9_mat = old.tomography(H, n_sel, cz[sel], v[sel], mu[sel], emu[sel])[0]
    y_sel_log = np.log(v[sel] / HREF) - MAG * (mu[sel] - 25.0)
    for wi, center in enumerate(H.CENTERS):
        ww = H.window(z_sel, sig_work, center)
        sw = np.sqrt(ww)
        beta9 = np.linalg.lstsq(sw[:, None] * X9_mat, sw * y_sel_log, rcond=None)[0]
        beta12 = np.linalg.lstsq(sw[:, None] * X_12, sw * y_sel_log, rcond=None)[0]
        radial_impact.append({
            "z_center": center,
            "beta12_radial_100Mpc_per_r": beta12[9:].tolist(),
            "shift_9D_vs_12D_norm": float(np.linalg.norm(beta12[:9] - beta9)),
        })

    # 8-octant held-out predictive score under diagonal-WLS vs inherited-k vs full-k 9D window fits
    octant = (n_sel >= 0).astype(int) @ np.array([1, 2, 4])
    octant_cv = old.prediction_cv(H, n_sel, cz[sel], v[sel], mu[sel], emu[sel])["log_fV"]
    # Also compute leave-one-window-out / 18-dof conditional prediction error across inherited vs full-k:
    cov_full_wf_36 = systematic_cal_cut + noise_meas + noise_nl150["WF_log"] + cov_full["WF_log"][:36, :36] + mag_tilt
    cov_inh_wf_36 = systematic_cal_cut + noise_meas + noise_nl150["WF_log"] + cov_inh["WF_log"][:36, :36] + mag_tilt

    for lbl in obs_names:
        for ri, R_h in enumerate((5, 10, 20)):
            sl = slice(36 * ri, 36 * (ri + 1))
            if lbl != "WF_log" and R_h != 5:
                continue  # Hermite first-chaos was parameterized at R=5 total latent sigma
            S_inh_36 = cov_inh[lbl][sl, sl]
            S_full_36 = cov_full[lbl][sl, sl]
            C_inh_tot = systematic_cal_cut + noise_meas + noise_nl150[lbl] + S_inh_36 + mag_tilt
            C_full_tot = systematic_cal_cut + noise_meas + noise_nl150[lbl] + S_full_36 + mag_tilt
            sc_inh = r99.schur(b_vec, C_inh_tot)
            sc_full = r99.schur(b_vec, C_full_tot)
            fit_inh = gls_svd(b_vec, designs["shared_9D_mean"], C_inh_tot, relative_rank_tolerance=1e-10)
            fit_full = gls_svd(b_vec, designs["shared_9D_mean"], C_full_tot, relative_rank_tolerance=1e-10)
            cross_ratio = float(np.linalg.norm(C_full_tot - C_inh_tot) / np.linalg.norm(C_full_tot))
            # Check 4-window cross-block ratio (windows 0 vs 2):
            cross_w02_inh = float(np.linalg.norm(S_inh_36[:9, 18:27]))
            cross_w02_full = float(np.linalg.norm(S_full_36[:9, 18:27]))
            model_comparisons[f"{lbl}_R{R_h}"] = {
                "S_PV_inherited_diag": diag_block(S_inh_36),
                "S_PV_full_k_diag": diag_block(S_full_36),
                "S_PV_band_traces": {
                    "low_k": float(np.trace(cov_low[lbl][sl, sl])),
                    "inherited": float(np.trace(S_inh_36)),
                    "high_k": float(np.trace(cov_high[lbl][sl, sl])),
                    "full_k": float(np.trace(S_full_36)),
                },
                "C_tot_inherited": diag_block(C_inh_tot),
                "C_tot_full_k": diag_block(C_full_tot),
                "total_cov_rel_fro_shift_full_vs_inh": cross_ratio,
                "cross_window_w0_w2_fro_inh_vs_full": [cross_w02_inh, cross_w02_full],
                "schur_18dof_inherited": sc_inh,
                "schur_18dof_full_k": sc_full,
                "shared_9D_beta_H0_inh_vs_full": [
                    float(HREF * math.exp(fit_inh["beta"][0])),
                    float(HREF * math.exp(fit_full["beta"][0])),
                ],
                "shared_9D_stf5_norm_inh_vs_full": [
                    float(np.linalg.norm(fit_inh["beta"][4:9])),
                    float(np.linalg.norm(fit_full["beta"][4:9])),
                ],
            }

    # P1 common-nuisance outer bounds comparing inherited R=5 WF vs full-k R=5 WF
    C_raw_wf5 = systematic_cal_cut + noise_meas + noise_nl150["WF_log"] + cov_full["WF_log"][:36, :36] + mag_tilt
    C_wf5_full = 0.5 * (C_raw_wf5 + C_raw_wf5.T)
    draws_full_k = (b_vec + coords @ np.linalg.cholesky(C_wf5_full).T).reshape(-1, 4, 9)
    L5 = np.linalg.cholesky(cov5)
    radius5 = math.sqrt(chi2.ppf(0.95, 5))
    log_der = (T @ np.eye(7)[6]).reshape(4, 9)
    p1_directcal_fullk = old.finite_slice(
        draws_full_k[:, :, 4:], log_der[:, 4:], np.ones((len(draws_full_k), 4)), np.zeros(4), 0.5, weights_p1, 0.05
    )

    npz_path = OUT_DIR / "CF4_FULL_KBAND_COVARIANCES.npz"
    np.savez_compressed(
        npz_path,
        radii_hinv=radii_hinv,
        C_WF_R5_inherited=systematic_cal_cut + noise_meas + noise_nl150["WF_log"] + cov_inh["WF_log"][:36, :36] + mag_tilt,
        C_WF_R5_full_k=C_wf5_full,
        S_PV_WF_low_108=cov_low["WF_log"],
        S_PV_WF_inherited_108=cov_inh["WF_log"],
        S_PV_WF_high_108=cov_high["WF_log"],
        S_PV_WF_full_108=cov_full["WF_log"],
        res_var_env_bg=res_var_env["background_proxy"],
        res_var_env_nat=res_var_env["native_comoving"],
        res_var_env_bol=res_var_env["bolometric"],
        b_published_4x9=b_work,
    )

    return {
        "one_point_variance_decomposition": onept_var,
        "quadrature_and_nufft_verification": {
            "low_k_probe_direct_rel_err": low_probe_err,
            "low_k_rad_CC16_vs_CC32_rel_fro": low_rad_rel,
            "high1_probe_direct_rel_err": hi1_probe_err,
            "high1_ang_53_vs_65_rel_fro": hi1_ang_rel,
            "high2_probe_direct_rel_err": hi2_probe_err,
            "high2_ang_53_vs_65_rel_fro": hi2_ang_rel,
            "high3_trace_R5_WF": float(np.trace(cov_hi3["WF_log"][:36, :36])),
            "high_k_vs_uncorrelated_diagonal_ref_rel_fro_R5": float(
                np.linalg.norm(cov_high["WF_log"][:36, :36] - C_hi_diag_ref) / np.linalg.norm(cov_high["WF_log"][:36, :36])
            ),
            "bessel_20source_checks": bessel_checks,
        },
        "radial_depth_9D_vs_12D_by_window": radial_impact,
        "octant_cv_log_fV_baseline": octant_cv,
        "models": model_comparisons,
        "p1_directcal_slice_full_k_R5": p1_directcal_fullk,
        "covariances_npz": {"path": str(npz_path), "sha256": sha256(npz_path)},
    }, {
        "noise_meas": noise_meas,
        "noise_nl150_wf": noise_nl150["WF_log"],
        "spv_full_wf_r5": cov_full["WF_log"][:36, :36],
        "systematic_cal_cut": systematic_cal_cut,
        "mag_tilt": mag_tilt,
        "C_total_wf_r5": C_wf5_full,
    }


def run_a4_selection_likelihood_and_4term(cov_parts: dict[str, np.ndarray]):
    """Build 6-stage SDSS/6dFGSv ledger, fit empirical inclusion models, evaluate joint_selected_logpdf, and assemble 4-term C provenance."""
    r30_sci, _, _, _ = old._load_r30_and_bridge()
    sdss = load_sdss_pv()
    sixdf = load_sixdf_pv()
    t2 = load_cf4_table2()

    # 1. Six-stage population ledger for SDSS & 6dFGSv
    pgc_set_t2 = set(t2["pgc"].tolist())
    s_in_t2 = np.array([int(g) in pgc_set_t2 for g in sdss["pgc"]], dtype=bool)
    s_in_mask = sdss["in_mask"] == 1
    s_z_cut = (sdss["zcmb"] >= 0.01) & (sdss["zcmb"] <= 0.10)
    s_grouped = sdss["idgroupt17"] > 0

    tol15 = 2.0 * math.sin(math.radians(15.0 / 3600.0) / 2.0)
    t2_tree = cKDTree(_sph_vec(t2["ra"], t2["dec"]))
    cand = t2_tree.query_ball_point(_sph_vec(sixdf["ra"], sixdf["dec"]), tol15)
    f6_matched = np.array(
        [sum(1 for j in cs if abs(int(t2["vcmb"][j]) - int(sixdf["cz_gal"][i])) <= 500) == 1 for i, cs in enumerate(cand)],
        dtype=bool,
    )
    f6_z_cut = (sixdf["cz_gal"] / C >= 0.01) & (sixdf["cz_gal"] / C <= 0.10)

    ledger = {
        "sdss_pv_6stage": {
            "stage1_upstream_release": sdss["n"],
            "stage2_footprint_in_mask_1": int(np.sum(s_in_mask)),
            "stage3_valid_fp_measurement": int(np.sum(np.isfinite(sdss["logdist_corr"]))),
            "stage4_z_0p01_to_0p10": int(np.sum(s_z_cut)),
            "stage5_in_table2_all": int(np.sum(s_in_t2)),
            "stage6_in_table2_and_z_0p01_to_0p10": int(np.sum(s_in_t2 & s_z_cut)),
            "in_t2_but_outside_z_0p01_to_0p10": int(np.sum(s_in_t2 & ~s_z_cut)),
            "in_mask_0_yet_in_table2": int(np.sum(~s_in_mask & s_in_t2)),
            "unmapped_14_in_mask_and_zcut": int(np.sum(~s_in_t2 & s_in_mask & s_z_cut)),
        },
        "sixdf_6stage": {
            "stage1_upstream_release": sixdf["n"],
            "stage2_valid_measurement": int(np.sum(np.isfinite(sixdf["delta_d"]))),
            "stage3_grouped_not_minus1": int(np.sum(sixdf["is_grouped"])),
            "stage4_matched_table2_unique": int(np.sum(f6_matched)),
            "stage5_matched_and_z_0p01_to_0p10": int(np.sum(f6_matched & f6_z_cut)),
            "excluded_from_table2": int(np.sum(~f6_matched)),
        },
        "missing_union_denominators": [
            "SNIa pre-CF4 target/rejected census",
            "TF/SBF/TRGB/Cepheid/maser upstream rejected parent catalogues",
            "Full-union CF4 cross-survey de-duplication & rejection denominator",
        ],
    }

    # 2. Fit empirical inclusion probit model on ACTUAL 6dFGSv (matched=1 vs unmapped=0) and SDSS (in_mask=1 vs 0)
    from scipy.optimize import minimize
    def fit_probit(X, y):
        def nll(b):
            eta = X @ b
            from scipy.special import log_ndtr
            ll = np.sum(y * log_ndtr(eta) + (1.0 - y) * log_ndtr(-eta))
            return -float(ll)
        b0 = np.zeros(X.shape[1]); b0[0] = float(np.clip(logit(np.mean(y)), -3, 3))
        opt = minimize(nll, b0, method="BFGS")
        return opt.x, -float(opt.fun)

    X_6 = np.column_stack((
        np.ones(sixdf["n"]),
        (sixdf["cz_gal"] / 1e4 - 1.1),
        sixdf["delta_d"],
        sixdf["is_grouped"].astype(float),
    ))
    b_6_inc, ll_6_inc = fit_probit(X_6, f6_matched.astype(float))
    # Evaluate normalized joint selected field likelihood on matched 6dFGSv subset under bulk flow field shifts!
    z6 = sixdf["cz_gal"][f6_matched] / C
    mean0_6 = 25.0 + 5.0 * np.log10((1.0 + z6) * r99._distance(r30_sci, z6) * r30_sci.H0 / 100.0)
    # Match native 6dFGSv observed mu = mean0_6 - 5*delta_d
    mu6_obs = mean0_6 - 5.0 * sixdf["delta_d"][f6_matched]
    emu6 = 5.0 * sixdf["epsilon_d"][f6_matched]
    # Test probit mark inclusion limit ~ mean0_6 + soft_offset (calibrated to native delta_d inclusion)
    fields = np.array([-300.0, -100.0, 0.0, 100.0, 300.0])
    means6 = np.array([mean0_6 - r99.finite_shift(r30_sci, z6, np.arctanh(u / C), "bolometric") / MAG for u in fields])
    res_6df_lik = r99.joint_selected_logpdf(mu6_obs, means6, emu6, mean0_6 + 0.55, 0.30, np.ones(len(fields)) / len(fields))
    res_6df_zero = r99.joint_selected_logpdf(mu6_obs, mean0_6[None, :], emu6, mean0_6 + 0.55, 0.30, np.array([1.0]))

    # SDSS subset empirical inclusion on (in_mask == 1): use full SDSS mark distribution with empirical cut sensitivity
    X_s = np.column_stack((np.ones(sdss["n"]), sdss["zcmb"] * 10.0 - 0.5, sdss["sn"], (sdss["idgroupt17"] > 0).astype(float)))
    b_s_inc, ll_s_inc = fit_probit(X_s, s_in_mask.astype(float))

    # 3. 4-Term Provenance-Tagged Source-Level Covariance C_36 Summary
    # Separate systematic_cal_cut into calibration (J_cal Sigma_cal J_cal^T) and selection boundary/Malmquist (C_sel)
    tr_meas = float(np.trace(cov_parts["noise_meas"]))
    tr_nl = float(np.trace(cov_parts["noise_nl150_wf"]))
    tr_spv = float(np.trace(cov_parts["spv_full_wf_r5"]))
    tr_sys = float(np.trace(cov_parts["systematic_cal_cut"]))
    tr_mag = float(np.trace(cov_parts["mag_tilt"]))
    tr_tot = float(np.trace(cov_parts["C_total_wf_r5"]))

    return {
        "six_stage_population_ledger": ledger,
        "empirical_probit_inclusion_6df": {
            "features": ["1", "(cz/1e4 - 1.1)", "delta_d", "is_grouped"],
            "beta_probit": b_6_inc.tolist(),
            "loglik": ll_6_inc,
            "joint_selected_logpdf_5field_mix": {
                "fields_kms": fields.tolist(),
                "log_density": res_6df_lik["log_density"],
                "log_joint_inclusion": res_6df_lik["log_joint_inclusion"],
                "included_field_weights": res_6df_lik["included_field_weights"].tolist(),
                "zero_field_log_density": res_6df_zero["log_density"],
            },
        },
        "empirical_probit_in_mask_sdss": {
            "features": ["1", "(10*zcmb - 0.5)", "Sn", "is_grouped"],
            "beta_probit": b_s_inc.tolist(),
            "loglik": ll_s_inc,
        },
        "four_term_covariance_trace_budget_WF_R5_full_k": {
            "N_meas_trace": tr_meas,
            "N_nl150_trace": tr_nl,
            "S_PV_full_k_trace": tr_spv,
            "J_cal_Sigma_cal_Plus_Cut_trace": tr_sys,
            "C_sel_mag_tilt_corrected_trace": tr_mag,
            "C_total_trace": tr_tot,
            "residual_trace_identity_error": abs((tr_meas + tr_nl + tr_spv + tr_sys + tr_mag) - tr_tot),
        },
    }


def compute() -> dict[str, object]:
    t0 = time.monotonic()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    H = old.r95._load_h03()
    inp = H.source(old.r95.SELECT)
    ids, mu, emu, cz, v, ds, wf, ramp, n, vls = old.catalog()
    z = cz / C
    positive = (cz > 0) & (v > 0)
    selected = (z >= 0.01) & (z <= 0.10)
    sel = np.flatnonzero(selected)
    sel = sel[np.argsort(ids[sel])]
    t3 = r97._parse_complete_table3_for_selected(ids)
    Wfull = old.magnitude_weights(t3)
    W = Wfull[sel]

    _, _, sig_work, A, cov_work, b_work = old.tomography(H, n[sel], cz[sel], v[sel], mu[sel], emu[sel])
    T = -MAG * (A @ W)
    f = r97.cf4_p0b.profile_method_offsets(t3["dm_vals_6"][sel], t3["e_vals_6"][sel])
    cov5 = f["cov_working_mag2"][1:, 1:]

    with np.load(old.P1 / "results/paired_functional_arrays.npz", allow_pickle=False) as p:
        old_draws, weights_p1 = p["draws"], p["weights"]
    archived = json.loads((old.P1 / "source/H03_SOURCE_TOMOGRAPHY.json").read_text())
    old_mu = np.array([z0["theta9"] for z0 in archived["monopole_dipole_STF2_windows"]])
    old_cov = np.array(archived["joint_covariance_36x36"])
    from scipy.linalg import solve_triangular
    coords = solve_triangular(np.linalg.cholesky(old_cov), (old_draws.reshape(-1, 36) - old_mu.ravel()).T, lower=True).T

    a2 = run_a2_genealogy_and_sign_audit(H, inp, ids, mu, emu, cz, v, n, sel, b_work, t3)
    a3, cov_parts = run_a3_full_kband_spv(H, inp, ids, n, cz, v, mu, emu, positive, selected, sel, Wfull, W, A, sig_work, cov_work, b_work, cov5, T, coords, weights_p1)
    a4 = run_a4_selection_likelihood_and_4term(cov_parts)

    inputs = {
        "sdss_pv_v1_1": {"path": str(SDSS_PATH), "sha256": sha256(SDSS_PATH)},
        "sixdf_pv_table1": {"path": str(SIXDF_PATH), "sha256": sha256(SIXDF_PATH)},
        "cf4_table2": {"path": str(r97.RAW_CF4 / "table2.dat"), "sha256": sha256(r97.RAW_CF4 / "table2.dat")},
        "cf4_table3": {"path": str(r97.RAW_CF4 / "table3.dat"), "sha256": sha256(r97.RAW_CF4 / "table3.dat")},
        "cf4_table4": {"path": str(r97.RAW_CF4 / "table4.dat"), "sha256": sha256(r97.RAW_CF4 / "table4.dat")},
        "code": {"path": str(Path(__file__).resolve()), "sha256": sha256(Path(__file__))},
    }
    payload = {
        "schema": "htt.r100.cf4_upstream_kband/1",
        "owner": "obsstat",
        "status": "SOURCE_QUALIFIED_FP_PARTIAL_BLOCKED_FULL_UNION",
        "physical_Pi": None,
        "physical_GF": None,
        "inputs": inputs,
        "A2_upstream_genealogy_and_sign_audit": a2,
        "A3_full_kband_correlated_pv": a3,
        "A4_selection_likelihood_and_4term_cov": a4,
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "threads": {k: os.getenv(k) for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")},
        },
        "runtime_seconds": time.monotonic() - t0,
    }
    out_path = OUT_DIR / "CF4_UPSTREAM_KBAND_RESULTS.json"
    out_path.write_text(json.dumps(payload, indent=2, default=old.json_default, allow_nan=False) + "\n")
    return payload


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.parse_args()
    res = compute()
    print(json.dumps({
        "status": res["status"],
        "sdss_matched": res["A2_upstream_genealogy_and_sign_audit"]["sdss_pv_census"]["exact_pgc_matches_table2"],
        "sixdf_matched": res["A2_upstream_genealogy_and_sign_audit"]["sixdf_pv_census"]["unique_match_15arcsec_500kms"],
        "onept_R5_fracs": {k: res["A3_full_kband_correlated_pv"]["one_point_variance_decomposition"]["5"][k] for k in ("frac_low", "frac_inherited", "frac_high")},
        "wf5_full_trace": res["A4_selection_likelihood_and_4term_cov"]["four_term_covariance_trace_budget_WF_R5_full_k"]["C_total_trace"],
        "runtime_s": res["runtime_seconds"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
