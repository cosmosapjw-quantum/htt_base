#!/usr/bin/env python3
"""R89 G04_RADIO_FRAME Solver-Free Research Completion (create-only).

Covers Section 5 across NVSS, RACS DR1, SPICE-RACS DR2, SUMSS, and LoTSS DR3 (interior):
A. Empirical cumulative number-count slope x(S) & exact Ellis-Baldwin (1984)
   kinematic prediction d_kin = [2 + x(1 + alpha)] * beta_CMB vs excess ratio.
B. Pairwise common-sky overlap dipoles (NVSS ∩ RACS, NVSS ∩ SPICE-RACS, NVSS ∩ LoTSS,
   RACS ∩ SUMSS), joint 9p (monopole+dipole+STF quad) vs 4p leakage, Galactic-cut
   sensitivity (|b|>15,20,30), and RACS_DR1_RMS_Footprints.tsv declination check.
C. Masked C_ell (l=1..15) shot-noise subtraction & 48-patch (NSIDE=2) spatial
   Jackknife 3x3 dipole covariance vs Poisson/overdispersion uncertainty.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import platform
import resource
import sys
import time
from pathlib import Path

import healpy as hp
import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits

ROOT = Path(__file__).resolve().parents[6]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from docs.research_program.observational_publication_20261015.H03_20261016.src.h03_tomography import stf_features

OUT_DIR = Path(__file__).resolve().parent
OUT_JSON = OUT_DIR / "SOLVER_FREE_RESEARCH_RESULT.json"

WORKDIR = Path("/mnt/extdrive/workdir")
NHI_FITS = WORKDIR / "raw/observational_bundles/ZoA_crosscheck/NHI_HPX.fits"
NVSS_GZ = WORKDIR / "raw/new_acquisitions/radio_hi/NVSS/nvss.dat.gz"
RACS_GZ = WORKDIR / "raw/observational_bundles/RACS_low_DR1_compact/RACS_DR1_galcut.dat.gz"
RACS_RMS_TSV = WORKDIR / "raw/observational_bundles/RACS_low_DR1_RMS_footprint/RACS_DR1_RMS_Footprints.tsv"
SPICE_GZ = WORKDIR / "raw/new_acquisitions/radio_hi/SPICE_RACS_DR2_CDS/sources.dat.gz"
SUMSS_GZ = WORKDIR / "raw/new_acquisitions/radio_hi/SUMSS/sumss212.dat.gz"
LOTSS_FITS = WORKDIR / "raw/new_acquisitions/radio_hi/LoTSS_DR3/LoTSS_DR3_v1.0.srl.fits"

NSIDE = 16
NPIX = hp.nside2npix(NSIDE)
THETA_P, PHI_P = hp.pix2ang(NSIDE, np.arange(NPIX))
PIX_N = np.column_stack([np.sin(THETA_P) * np.cos(PHI_P), np.sin(THETA_P) * np.sin(PHI_P), np.cos(THETA_P)])
PIX_SC = SkyCoord(ra=np.rad2deg(PHI_P) * u.deg, dec=(90.0 - np.rad2deg(THETA_P)) * u.deg, frame="icrs")
PIX_B_DEG = PIX_SC.galactic.b.deg
PIX_DEC_DEG = 90.0 - np.rad2deg(THETA_P)
PIX_PATCH = hp.ang2pix(2, THETA_P, PHI_P)

BETA_CMB = 369.82 / 299792.458  # Planck 2018 CMB dipole beta = 1.23359e-3
CMB_VEC_ICRS = np.array([
    math.cos(math.radians(-6.94)) * math.cos(math.radians(167.94)),
    math.cos(math.radians(-6.94)) * math.sin(math.radians(167.94)),
    math.sin(math.radians(-6.94)),
])
# Exact Galactic (264.021, 48.253) -> ICRS unit vector
_cmb_icrs = SkyCoord(l=264.021 * u.deg, b=48.253 * u.deg, frame="galactic").icrs
CMB_U_ICRS = np.array([
    math.cos(math.radians(float(_cmb_icrs.dec.deg))) * math.cos(math.radians(float(_cmb_icrs.ra.deg))),
    math.cos(math.radians(float(_cmb_icrs.dec.deg))) * math.sin(math.radians(float(_cmb_icrs.ra.deg))),
    math.sin(math.radians(float(_cmb_icrs.dec.deg))),
])


def _sha256_head_only_fast(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def _build_nhi_ns16_icrs() -> np.ndarray:
    with fits.open(NHI_FITS, memmap=True) as hd:
        order = str(hd[1].header.get("ORDERING", "RING")).upper()
        nest = order == "NESTED"
        nside_in = int(hd[1].header.get("NSIDE", 1024))
        nhi = np.asarray(hd[1].data["NHI"], dtype=np.float64).ravel()
        hpx = np.asarray(hd[1].data["HPXINDEX"], dtype=np.int64).ravel()
    vx, vy, vz = hp.pix2vec(nside_in, hpx, nest=nest)
    sc_basis = SkyCoord(l=[0.0, 90.0, 0.0] * u.deg, b=[0.0, 0.0, 90.0] * u.deg, frame="galactic").icrs
    R_gi = np.column_stack([
        [
            math.cos(math.radians(float(pt.dec.deg))) * math.cos(math.radians(float(pt.ra.deg))),
            math.cos(math.radians(float(pt.dec.deg))) * math.sin(math.radians(float(pt.ra.deg))),
            math.sin(math.radians(float(pt.dec.deg))),
        ]
        for pt in sc_basis
    ])
    ix = R_gi[0, 0] * vx + R_gi[0, 1] * vy + R_gi[0, 2] * vz
    iy = R_gi[1, 0] * vx + R_gi[1, 1] * vy + R_gi[1, 2] * vz
    iz = R_gi[2, 0] * vx + R_gi[2, 1] * vy + R_gi[2, 2] * vz
    icrs_pix = hp.vec2pix(NSIDE, ix, iy, iz, nest=False)
    ok = np.isfinite(nhi) & (nhi > 0.0)
    return np.divide(np.bincount(icrs_pix[ok], weights=nhi[ok], minlength=NPIX), np.maximum(np.bincount(icrs_pix[ok], minlength=NPIX), 1.0))


def _fit_4p_and_9p(cts: np.ndarray, fp_mask: np.ndarray) -> dict:
    m = fp_mask & np.isfinite(cts)
    n_pix = int(np.sum(m))
    if n_pix < 30:
        return {"masked_pixels": n_pix, "status": "INSUFFICIENT_PIXELS"}
    yc = cts[m]
    mean_c = float(np.mean(yc))
    if mean_c <= 0.0:
        return {"masked_pixels": n_pix, "status": "ZERO_MEAN_COUNTS"}
    n_src = int(np.sum(yc))
    y = (yc - mean_c) / mean_c
    w = np.full(n_pix, mean_c, dtype=np.float64)
    nm = PIX_N[m]

    # 4p dipole+monopole
    X4 = np.column_stack([nm, np.ones(n_pix)])
    F4 = X4.T @ (w[:, None] * X4)
    b4 = np.linalg.solve(F4, X4.T @ (w * y))
    cov4_p = np.linalg.inv(F4)[:3, :3]
    res4 = y - X4 @ b4
    od4 = float(np.sum(w * res4 * res4) / max(n_pix - 4, 1))
    d4 = b4[:3]
    amp4 = float(np.linalg.norm(d4))
    sc4 = SkyCoord(ra=(math.degrees(math.atan2(d4[1], d4[0])) % 360.0) * u.deg, dec=math.degrees(math.asin(max(-1.0, min(1.0, d4[2] / max(amp4, 1e-30))))) * u.deg, frame="icrs").galactic
    sep_cmb4 = math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(d4, CMB_U_ICRS) / max(amp4, 1e-30))))))
    sd_poiss = float(math.sqrt((d4 @ cov4_p @ d4) / max(amp4 * amp4, 1e-30))) if amp4 > 0 else float(math.sqrt(np.trace(cov4_p) / 3.0))

    # 9p monopole+dipole+STF quadrupole (leakage check)
    X9 = np.column_stack([nm, np.ones(n_pix), stf_features(nm)])
    F9 = X9.T @ (w[:, None] * X9)
    eig9 = np.linalg.eigvalsh(F9)
    b9 = np.linalg.solve(F9, X9.T @ (w * y))
    d9 = b9[:3]
    amp9 = float(np.linalg.norm(d9))
    angle_4_vs_9 = math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(d4, d9) / max(amp4 * amp9, 1e-30))))))

    # 48-patch (NSIDE=2) spatial jackknife covariance of 4p dipole
    patches = PIX_PATCH[m]
    uniq_p = [int(p) for p in np.unique(patches) if np.sum(patches != p) >= 15]
    jk_vecs = []
    for p in uniq_p:
        keep = patches != p
        y_p = (yc[keep] - float(np.mean(yc[keep]))) / max(float(np.mean(yc[keep])), 1e-12)
        Xp = np.column_stack([nm[keep], np.ones(int(np.sum(keep)))])
        wp = np.full(int(np.sum(keep)), float(np.mean(yc[keep])), dtype=np.float64)
        Fp = Xp.T @ (wp[:, None] * Xp)
        bp = np.linalg.solve(Fp, Xp.T @ (wp * y_p))
        jk_vecs.append(bp[:3])
    jk_arr = np.asarray(jk_vecs, dtype=np.float64)
    M_jk = len(jk_arr)
    jk_diff = jk_arr - jk_arr.mean(axis=0)[None, :]
    cov_jk = ((M_jk - 1.0) / max(M_jk, 1)) * (jk_diff.T @ jk_diff)
    sd_jk = float(math.sqrt(max(float((d4 @ cov_jk @ d4) / max(amp4 * amp4, 1e-30)), 0.0))) if amp4 > 0 else float(math.sqrt(np.trace(cov_jk) / 3.0))

    # Masked pseudo-C_ell (l=1..15) divided by f_sky vs Poisson shot noise 4*pi*f_sky / N_src
    f_sky = float(n_pix / NPIX)
    od_map = np.zeros(NPIX, dtype=np.float64)
    od_map[m] = y
    cl_pseudo = hp.anafast(od_map, lmax=15) / max(f_sky, 1e-12)
    shot_floor = (4.0 * math.pi * f_sky) / max(n_src, 1)

    return {
        "n_sources": n_src,
        "masked_pixels": n_pix,
        "sky_fraction": f_sky,
        "mean_count_per_pixel": mean_c,
        "dipole_4p_icrs_vec": d4.tolist(),
        "dipole_4p_amp": amp4,
        "dipole_4p_gal_lb_deg": [float(sc4.l.deg), float(sc4.b.deg)],
        "dipole_4p_sep_cmb_deg": float(sep_cmb4),
        "sd_poisson": sd_poiss,
        "sd_overdisp": float(sd_poiss * math.sqrt(max(od4, 1.0))),
        "sd_jackknife_48p": sd_jk,
        "jackknife_n_patches": int(M_jk),
        "jackknife_over_poisson_ratio": float(sd_jk / max(sd_poiss, 1e-30)),
        "poisson_overdispersion": od4,
        "dipole_9p_amp": amp9,
        "dipole_4p_vs_9p_shift_deg": float(angle_4_vs_9),
        "quad_9p_frob_norm": float(np.linalg.norm(b9[4:9])),
        "F9_condition": float(eig9.max() / max(eig9.min(), 1e-30)),
        "cl_pseudo_over_fsky_ell1_to_10": [float(x) for x in cl_pseudo[1:11]],
        "poisson_shot_noise_floor": float(shot_floor),
        "cl_excess_ell2_to_5": [float(cl_pseudo[l] - shot_floor) for l in range(2, 6)],
    }


def _scan_all_five(base_mask: np.ndarray) -> tuple[dict, dict]:
    maps = {}
    masks = {}

    # 1. NVSS (verified fixed-width format matching run_g04_radio_deep_parallel.py)
    nv_cuts = (15.0, 20.0, 30.0, 50.0)
    nv_cts = {c: np.zeros(NPIX, dtype=np.float64) for c in nv_cuts}
    with gzip.open(NVSS_GZ, "rt", encoding="ascii", errors="ignore") as f:
        for ln in f:
            if len(ln) < 83:
                continue
            try:
                rah = float(ln[40:42]); ram = float(ln[43:45]); ras = float(ln[46:51])
                sgn = -1.0 if ln[52:53] == "-" else 1.0
                ded = float(ln[53:55]); dem = float(ln[56:58]); des = float(ln[59:63])
                flux = float(ln[75:83])
            except ValueError:
                continue
            if flux < 15.0:
                continue
            ra = 15.0 * (rah + ram / 60.0 + ras / 3600.0)
            dec = sgn * (ded + dem / 60.0 + des / 3600.0)
            if dec <= -37.0:
                continue
            pix = hp.ang2pix(NSIDE, math.radians(90.0 - dec), math.radians(ra))
            for c in nv_cuts:
                if flux >= c:
                    nv_cts[c][pix] += 1.0
    maps["NVSS"] = nv_cts
    masks["NVSS"] = base_mask & (PIX_DEC_DEG > -36.5)

    # 2. RACS DR1 (cts_raw on fp_raw & fp_unif; cts_unif ONLY for contrast, fixed per F3)
    rc_cuts = (15.0, 20.0, 30.0, 50.0, 100.0)
    rc_cts = {c: np.zeros(NPIX, dtype=np.float64) for c in rc_cuts}
    rms_sum = np.zeros(NPIX, dtype=np.float64)
    rms_cnt = np.zeros(NPIX, dtype=np.float64)
    with gzip.open(RACS_GZ, "rt", encoding="ascii", errors="ignore") as f:
        for ln in f:
            parts = ln.split("|")
            if len(parts) <= 31:
                continue
            try:
                ra = float(parts[6]); dec = float(parts[7]); sv = float(parts[10]); rms = float(parts[14])
            except ValueError:
                continue
            pix = hp.ang2pix(NSIDE, math.radians(90.0 - dec), math.radians(ra))
            rms_sum[pix] += rms; rms_cnt[pix] += 1.0
            if sv >= 15.0:
                for c in rc_cuts:
                    if sv >= c:
                        rc_cts[c][pix] += 1.0
    mean_rms = np.divide(rms_sum, np.maximum(rms_cnt, 1.0))
    maps["RACS_DR1"] = rc_cts
    masks["RACS_DR1_raw"] = base_mask & (PIX_DEC_DEG >= -79.5) & (PIX_DEC_DEG <= 29.5)
    masks["RACS_DR1_unif"] = base_mask & (PIX_DEC_DEG >= -75.0) & (PIX_DEC_DEG <= 25.0) & (rms_cnt >= 50) & (mean_rms <= 0.45)

    # 3. SPICE-RACS DR2
    sp_cuts = (20.0, 30.0, 50.0)
    sp_cts = {c: np.zeros(NPIX, dtype=np.float64) for c in sp_cuts}
    with gzip.open(SPICE_GZ, "rt", encoding="ascii", errors="ignore") as f:
        for ln in f:
            if len(ln) < 166:
                continue
            try:
                ra = float(ln[56:71]); dec = float(ln[88:103]); ftot = float(ln[152:166])
            except ValueError:
                continue
            if ftot < 20.0:
                continue
            pix = hp.ang2pix(NSIDE, math.radians(90.0 - dec), math.radians(ra))
            for c in sp_cuts:
                if ftot >= c:
                    sp_cts[c][pix] += 1.0
    maps["SPICE_RACS"] = sp_cts
    masks["SPICE_RACS"] = base_mask & (PIX_DEC_DEG >= -79.5) & (PIX_DEC_DEG <= 49.5)

    # 4. SUMSS (verified fixed-width format matching run_g04_radio_deep_parallel.py)
    su_cuts = (15.0, 20.0, 30.0, 50.0)
    su_cts = {c: np.zeros(NPIX, dtype=np.float64) for c in su_cuts}
    with gzip.open(SUMSS_GZ, "rt", encoding="ascii", errors="ignore") as f:
        for ln in f:
            if len(ln) < 62:
                continue
            try:
                rah, ram, ras = float(ln[0:2]), float(ln[3:5]), float(ln[6:11])
                sign = -1.0 if ln[13:14] == "-" else 1.0
                ded, dem, des = float(ln[14:16]), float(ln[17:19]), float(ln[20:25])
                ftot = float(ln[54:62])
            except ValueError:
                continue
            if ftot < 15.0:
                continue
            ra = 15.0 * (rah + ram / 60.0 + ras / 3600.0)
            dec = sign * (ded + dem / 60.0 + des / 3600.0)
            pix = hp.ang2pix(NSIDE, math.radians(90.0 - dec), math.radians(ra))
            for c in su_cuts:
                if ftot >= c:
                    su_cts[c][pix] += 1.0
    maps["SUMSS"] = su_cts
    masks["SUMSS"] = base_mask & (PIX_DEC_DEG <= -30.5)

    # 5. LoTSS DR3 interior >= 1500
    lo_cuts = (20.0, 50.0, 100.0)
    lo_cts = {c: np.zeros(NPIX, dtype=np.float64) for c in lo_cuts}
    lo_all = np.zeros(NPIX, dtype=np.float64)
    with fits.open(LOTSS_FITS, memmap=True) as hd:
        data = hd[1].data
        nrows = len(data)
        chunk = 1000000
        for i in range(0, nrows, chunk):
            j = min(i + chunk, nrows)
            ra = np.asarray(data["RA"][i:j], dtype=np.float64)
            dec = np.asarray(data["DEC"][i:j], dtype=np.float64)
            ft = np.asarray(data["Total_flux"][i:j], dtype=np.float64)
            ok = np.isfinite(ra) & np.isfinite(dec) & np.isfinite(ft)
            if not np.any(ok):
                continue
            pix = hp.ang2pix(NSIDE, np.deg2rad(90.0 - dec[ok]), np.deg2rad(ra[ok]))
            lo_all += np.bincount(pix, minlength=NPIX)
            fok = ft[ok]
            for c in lo_cuts:
                mc = fok >= c
                if np.any(mc):
                    lo_cts[c] += np.bincount(pix[mc], minlength=NPIX)
    maps["LoTSS_DR3"] = lo_cts
    masks["LoTSS_DR3_int1500"] = base_mask & (lo_all >= 1500.0) & (np.abs(PIX_B_DEG) > 20.0)
    return maps, masks


def _ellis_baldwin_analysis(maps: dict, masks: dict) -> dict:
    # Compute cumulative count slope x = -d ln N(>S) / d ln S between adjacent flux cuts on fixed footprint
    survey_map = {
        "NVSS": ("NVSS", (15.0, 20.0, 30.0, 50.0)),
        "RACS_DR1_unif": ("RACS_DR1", (15.0, 20.0, 30.0, 50.0, 100.0)),
        "SPICE_RACS": ("SPICE_RACS", (20.0, 30.0, 50.0)),
        "SUMSS": ("SUMSS", (15.0, 20.0, 30.0, 50.0)),
        "LoTSS_DR3_int1500": ("LoTSS_DR3", (20.0, 50.0, 100.0)),
    }
    alpha_fid = 0.75
    out = {}
    for label, (skey, cuts) in survey_map.items():
        fp = masks[label]
        Ns = {c: int(np.sum(maps[skey][c][fp])) for c in cuts}
        ladder = {str(int(c)): _fit_4p_and_9p(maps[skey][c], fp) for c in cuts}
        slopes = []
        for c1, c2 in zip(cuts[:-1], cuts[1:]):
            x_eff = -math.log(max(Ns[c2], 1) / max(Ns[c1], 1)) / math.log(c2 / c1)
            d_kin = (2.0 + x_eff * (1.0 + alpha_fid)) * BETA_CMB
            d_kin_lo = (2.0 + x_eff * (1.0 + 0.65)) * BETA_CMB
            d_kin_hi = (2.0 + x_eff * (1.0 + 0.85)) * BETA_CMB
            obs_c2 = ladder[str(int(c2))]["dipole_4p_amp"]
            slopes.append({
                "flux_interval_mJy": [int(c1), int(c2)],
                "N_c1": Ns[c1],
                "N_c2": Ns[c2],
                "x_slope_measured": x_eff,
                "d_kin_alpha0p75": d_kin,
                "d_kin_alpha_0p65_to_0p85": [d_kin_lo, d_kin_hi],
                "d_obs_at_c2": obs_c2,
                "excess_ratio_d_obs_over_d_kin": float(obs_c2 / max(d_kin, 1e-12)),
            })
        out[label] = {"ladder": ladder, "ellis_baldwin_segments": slopes}
    return out


def _pairwise_common_sky_overlaps(maps: dict, masks: dict) -> dict:
    pairs = [
        ("NVSS_vs_RACS_DR1_unif_S20", "NVSS", "NVSS", 20.0, "RACS_DR1", "RACS_DR1_unif", 20.0),
        ("NVSS_vs_SPICE_RACS_S20", "NVSS", "NVSS", 20.0, "SPICE_RACS", "SPICE_RACS", 20.0),
        ("NVSS_vs_SPICE_RACS_S50", "NVSS", "NVSS", 50.0, "SPICE_RACS", "SPICE_RACS", 50.0),
        ("NVSS_vs_LoTSS_int1500_S50", "NVSS", "NVSS", 50.0, "LoTSS_DR3", "LoTSS_DR3_int1500", 50.0),
        ("RACS_DR1_unif_vs_SUMSS_S20", "RACS_DR1", "RACS_DR1_unif", 20.0, "SUMSS", "SUMSS", 20.0),
    ]
    out = {}
    for pname, s1, m1, c1, s2, m2, c2 in pairs:
        inter = masks[m1] & masks[m2]
        f1 = _fit_4p_and_9p(maps[s1][c1], inter)
        f2 = _fit_4p_and_9p(maps[s2][c2], inter)
        v1 = np.asarray(f1["dipole_4p_icrs_vec"], dtype=np.float64)
        v2 = np.asarray(f2["dipole_4p_icrs_vec"], dtype=np.float64)
        ang = math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(v1, v2) / max(np.linalg.norm(v1) * np.linalg.norm(v2), 1e-30))))))
        out[pname] = {
            "common_pixels": int(np.sum(inter)),
            "sky_fraction": float(np.mean(inter)),
            "fit_a": f1,
            "fit_b": f2,
            "dipole_a_vs_b_angle_deg": float(ang),
            "amp_ratio_a_over_b": float(f1["dipole_4p_amp"] / max(f2["dipole_4p_amp"], 1e-12)),
        }
    return out


def _galactic_cut_sensitivity(maps: dict, masks: dict) -> dict:
    out = {}
    for bcut in (15.0, 20.0, 30.0):
        gm = np.abs(PIX_B_DEG) > bcut
        out[f"abs_b_gt_{int(bcut)}"] = {
            "NVSS_S20": _fit_4p_and_9p(maps["NVSS"][20.0], masks["NVSS"] & gm),
            "RACS_DR1_unif_S20": _fit_4p_and_9p(maps["RACS_DR1"][20.0], masks["RACS_DR1_unif"] & gm),
            "SPICE_RACS_S20": _fit_4p_and_9p(maps["SPICE_RACS"][20.0], masks["SPICE_RACS"] & gm),
        }
    return out


def _racs_tile_tsv_summary() -> dict:
    decs = []
    with RACS_RMS_TSV.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            try:
                decs.append(float(row["s_dec"]))
            except (KeyError, ValueError):
                continue
    d_arr = np.asarray(decs, dtype=np.float64)
    return {
        "n_tiles": int(len(d_arr)),
        "dec_min_max": [float(d_arr.min()), float(d_arr.max())] if len(d_arr) else None,
        "dec_band_counts": {
            "south_le_minus30": int(np.sum(d_arr <= -30.0)),
            "mid_minus30_to_0": int(np.sum((d_arr > -30.0) & (d_arr <= 0.0))),
            "north_gt_0": int(np.sum(d_arr > 0.0)),
        },
    }


def main() -> int:
    if OUT_JSON.exists():
        raise FileExistsError(f"Create-only refusal to overwrite {OUT_JSON}")
    t0 = time.perf_counter()

    nhi_icrs = _build_nhi_ns16_icrs()
    base_mask = (np.abs(PIX_B_DEG) > 15.0) & (nhi_icrs < 1e21)

    maps, masks = _scan_all_five(base_mask)
    eb_res = _ellis_baldwin_analysis(maps, masks)
    pair_res = _pairwise_common_sky_overlaps(maps, masks)
    gal_res = _galactic_cut_sensitivity(maps, masks)
    tile_res = _racs_tile_tsv_summary()

    dt = time.perf_counter() - t0
    rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    payload = {
        "artifact_id": "R89_G04_RADIO_SOLVER_FREE_RESEARCH_V1",
        "group_id": "G04_RADIO_FRAME",
        "create_only": True,
        "epistemic_status": "conditional",
        "runtime_sec": round(dt, 3),
        "max_rss_mb": round(rss_mb, 2),
        "platform": platform.platform(),
        "node_verdicts_preserved": {
            "V01": "REUSED_SCOPED",
            "V02": "REUSED_SCOPED",
            "V03": "REUSED_SCOPED",
            "SQ-FRAME": "DIAGNOSTIC_COMPLETED_SCOPED",
            "SQ-RADIO": "DIAGNOSTIC_COMPLETED_SCOPED",
            "V04": "BLOCKED_DEPENDENCY",
            "V05": "BLOCKED_DEPENDENCY",
            "V06": "BLOCKED_DEPENDENCY",
        },
        "part_a_ellis_baldwin_and_ladders": eb_res,
        "part_b_pairwise_overlaps_and_galcuts": {
            "pairwise_common_sky": pair_res,
            "galactic_cut_sensitivity": gal_res,
            "racs_rms_tile_footprints": tile_res,
        },
        "claim_hygiene": {
            "physical_Pi": None,
            "physical_GF": None,
            "bianchi_family_identified": False,
            "cosmological_radio_dipole_significance_approved": False,
            "note": "Survey-matched LSS/selection null absent; V04-V06 remain BLOCKED_DEPENDENCY.",
        },
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"group_id": "G04_RESEARCH", "runtime_sec": round(dt, 2), "max_rss_mb": round(rss_mb, 1)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
