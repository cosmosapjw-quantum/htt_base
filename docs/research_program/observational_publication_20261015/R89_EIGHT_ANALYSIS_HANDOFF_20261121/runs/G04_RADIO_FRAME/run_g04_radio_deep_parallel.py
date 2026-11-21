#!/usr/bin/env python3
"""R89 Phase-3 Track 3 (G04_RADIO_FRAME): 5-Survey Multi-Frequency Flux-Ladder & NHI Mask (create-only).

Executes chunked/streaming NSIDE=16 WLS count-dipole comparisons across 5 radio surveys:
- NVSS (1.4 GHz, nvss.dat.gz)
- RACS-low DR1 (887.5 MHz, RACS_DR1_galcut.dat.gz, raw + RMS-uniform cut)
- SPICE-RACS DR2 / RACS-low3 (943.5 MHz, sources.dat.gz, -90<dec<+49)
- SUMSS v2.1 (843 MHz, sumss212.dat.gz)
- LoTSS DR3 (144 MHz, LoTSS_DR3_v1.0.srl.fits, 13.67M sources)
masked by Galactic latitude |b|>15 deg and HI4PI column density NHI < 1e21 cm^-2.
Preserves SQ-RADIO = DIAGNOSTIC_COMPLETED_SCOPED and V04-V06 = BLOCKED_DEPENDENCY.
"""
from __future__ import annotations

import gzip
import hashlib
import math
import json
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

OUT_DIR = Path(__file__).resolve().parent
OUT_JSON = OUT_DIR / "DEEP_FIVE_SURVEY_RESULT.json"

WORKDIR = Path("/mnt/extdrive/workdir")
NHI_FITS = WORKDIR / "raw/observational_bundles/ZoA_crosscheck/NHI_HPX.fits"
NVSS_GZ = WORKDIR / "raw/new_acquisitions/radio_hi/NVSS/nvss.dat.gz"
RACS_GZ = WORKDIR / "raw/observational_bundles/RACS_low_DR1_compact/RACS_DR1_galcut.dat.gz"
SPICE_GZ = WORKDIR / "raw/new_acquisitions/radio_hi/SPICE_RACS_DR2_CDS/sources.dat.gz"
SUMSS_GZ = WORKDIR / "raw/new_acquisitions/radio_hi/SUMSS/sumss212.dat.gz"
LOTSS_FITS = WORKDIR / "raw/new_acquisitions/radio_hi/LoTSS_DR3/LoTSS_DR3_v1.0.srl.fits"

NSIDE = 16
NPIX = hp.nside2npix(NSIDE)
THETA_P, PHI_P = hp.pix2ang(NSIDE, np.arange(NPIX))
PIX_N = np.column_stack([np.sin(THETA_P) * np.cos(PHI_P), np.sin(THETA_P) * np.sin(PHI_P), np.cos(THETA_P)])
PIX_SC_ICRS = SkyCoord(ra=np.rad2deg(PHI_P) * u.deg, dec=(90.0 - np.rad2deg(THETA_P)) * u.deg, frame="icrs")
PIX_B_DEG = PIX_SC_ICRS.galactic.b.deg
PIX_DEC_DEG = 90.0 - np.rad2deg(THETA_P)
CMB_SC = SkyCoord(l=264.021 * u.deg, b=48.253 * u.deg, frame="galactic").icrs


def _build_nhi_ns16_icrs() -> np.ndarray:
    with fits.open(NHI_FITS, memmap=True) as hd:
        order = str(hd[1].header.get("ORDERING", "RING")).upper()
        nest = order == "NESTED"
        coords = str(hd[1].header.get("COORDSYS", "GALACTIC")).upper()
        col_names = {c.name for c in hd[1].columns}
        if "NHI" in col_names and "HPXINDEX" in col_names and coords.startswith("G"):
            nside_in = int(hd[1].header.get("NSIDE", 1024))
            nhi = np.asarray(hd[1].data["NHI"], dtype=np.float64).ravel()
            hpx = np.asarray(hd[1].data["HPXINDEX"], dtype=np.int64).ravel()
            # Bin native NSIDE=1024 Galactic pixel centers directly into ICRS NSIDE=16 pixels
            vx, vy, vz = hp.pix2vec(nside_in, hpx, nest=nest)
            sc_basis = SkyCoord(l=[0.0, 90.0, 0.0] * u.deg, b=[0.0, 0.0, 90.0] * u.deg, frame="galactic").icrs
            R_gi = np.column_stack(
                [
                    [
                        math.cos(math.radians(float(pt.dec.deg))) * math.cos(math.radians(float(pt.ra.deg))),
                        math.cos(math.radians(float(pt.dec.deg))) * math.sin(math.radians(float(pt.ra.deg))),
                        math.sin(math.radians(float(pt.dec.deg))),
                    ]
                    for pt in sc_basis
                ]
            )
            ix = R_gi[0, 0] * vx + R_gi[0, 1] * vy + R_gi[0, 2] * vz
            iy = R_gi[1, 0] * vx + R_gi[1, 1] * vy + R_gi[1, 2] * vz
            iz = R_gi[2, 0] * vx + R_gi[2, 1] * vy + R_gi[2, 2] * vz
            icrs_pix = hp.vec2pix(NSIDE, ix, iy, iz, nest=False)
            ok = np.isfinite(nhi) & (nhi > 0.0)
            s_nhi = np.bincount(icrs_pix[ok], weights=nhi[ok], minlength=NPIX)
            c_nhi = np.bincount(icrs_pix[ok], minlength=NPIX)
            return np.divide(s_nhi, np.maximum(c_nhi, 1.0))
        if "NHI" in col_names:
            nhi = np.asarray(hd[1].data["NHI"], dtype=np.float64).ravel()
            if "HPXINDEX" in col_names:
                nside_in = int(hd[1].header.get("NSIDE", 1024))
                hpx = np.asarray(hd[1].data["HPXINDEX"], dtype=np.int64).ravel()
                arr = np.full(hp.nside2npix(nside_in), hp.UNSEEN, dtype=np.float64)
                arr[hpx] = nhi
            else:
                arr = nhi
        else:
            col_name = hd[1].columns[0].name
            arr = np.asarray(hd[1].data[col_name], dtype=np.float64).ravel()
    nhi_gal_ring = hp.ud_grade(arr, nside_out=NSIDE, order_in="NESTED" if nest else "RING", order_out="RING")
    del arr
    if coords.startswith("G"):
        l_deg = PIX_SC_ICRS.galactic.l.deg
        b_deg = PIX_SC_ICRS.galactic.b.deg
        gal_pix = hp.ang2pix(NSIDE, np.deg2rad(90.0 - b_deg), np.deg2rad(l_deg), nest=False)
        return nhi_gal_ring[gal_pix]
    return nhi_gal_ring


def _fit_wls_dipole(cts: np.ndarray, footprint_mask: np.ndarray) -> dict:
    m = footprint_mask & np.isfinite(cts)
    n_pix = int(np.sum(m))
    if n_pix < 20:
        return {"masked_pixels": n_pix, "status": "INSUFFICIENT_PIXELS"}
    y_c = cts[m]
    mean_c = float(np.mean(y_c))
    if mean_c <= 0:
        return {"masked_pixels": n_pix, "status": "ZERO_MEAN_COUNTS"}
    y = (y_c - mean_c) / mean_c
    w = np.full(n_pix, mean_c, dtype=np.float64)
    X = np.column_stack([PIX_N[m], np.ones(n_pix)])
    XtWX = (X.T * w) @ X
    XtWy = X.T @ (w * y)
    cov = np.linalg.inv(XtWX)
    beta = cov @ XtWy
    resid = y - X @ beta
    chi2_val = float(np.sum(w * resid * resid))
    overdisp = max(1.0, chi2_val / max(n_pix - 4, 1))
    cov_s = cov[:3, :3] * overdisp
    d_vec = beta[:3]
    amp = float(np.linalg.norm(d_vec))
    sc = SkyCoord(x=d_vec[0], y=d_vec[1], z=d_vec[2], representation_type="cartesian").spherical
    sc_icrs = SkyCoord(ra=sc.lon, dec=sc.lat, frame="icrs")
    return {
        "n_sources": int(np.sum(cts[m])),
        "masked_pixels": n_pix,
        "sky_fraction": float(n_pix / NPIX),
        "mean_count_per_pixel": mean_c,
        "dipole_icrs_vec": d_vec.tolist(),
        "dipole_amplitude": amp,
        "dipole_amp_sd_cond": float(np.sqrt((d_vec @ cov_s @ d_vec) / max(amp * amp, 1e-18))),
        "dipole_ra_dec_deg": [float(sc_icrs.ra.deg), float(sc_icrs.dec.deg)],
        "dipole_gal_lb_deg": [float(sc_icrs.galactic.l.deg), float(sc_icrs.galactic.b.deg)],
        "angle_to_cmb_deg": float(sc_icrs.separation(CMB_SC).deg),
        "poisson_overdispersion": float(overdisp),
    }


def _scan_nvss(base_mask: np.ndarray) -> dict:
    cuts = (15.0, 20.0, 30.0, 50.0)
    cts = {c: np.zeros(NPIX, dtype=np.float64) for c in cuts}
    total_rows = 0
    with gzip.open(NVSS_GZ, "rt", encoding="ascii", errors="ignore") as f:
        for ln in f:
            if len(ln) < 83:
                continue
            try:
                rah = float(ln[40:42]); ram = float(ln[43:45]); ras = float(ln[46:51])
                sgn = -1.0 if ln[52:53] == "-" else 1.0
                ded = float(ln[53:55]); dem = float(ln[56:58]); des = float(ln[59:63])
                s14 = float(ln[75:83])
            except ValueError:
                continue
            total_rows += 1
            if s14 < 15.0:
                continue
            ra = 15.0 * (rah + ram / 60.0 + ras / 3600.0)
            dec = sgn * (ded + dem / 60.0 + des / 3600.0)
            if dec <= -37.0:
                continue
            pix = hp.ang2pix(NSIDE, math.radians(90.0 - dec), math.radians(ra))
            for c in cuts:
                if s14 >= c:
                    cts[c][pix] += 1.0
    fp = base_mask & (PIX_DEC_DEG > -36.5)
    return {
        "total_parsed_rows": total_rows,
        "flux_ladder_mJy": {str(int(c)): _fit_wls_dipole(cts[c], fp) for c in cuts},
    }


def _scan_racs_dr1(base_mask: np.ndarray) -> dict:
    cuts = (15.0, 20.0, 30.0, 50.0, 100.0)
    cts_raw = {c: np.zeros(NPIX, dtype=np.float64) for c in cuts}
    cts_unif = {c: np.zeros(NPIX, dtype=np.float64) for c in cuts}
    rms_sum = np.zeros(NPIX, dtype=np.float64)
    rms_cnt = np.zeros(NPIX, dtype=np.float64)
    total_rows = 0
    with gzip.open(RACS_GZ, "rt", encoding="ascii", errors="ignore") as f:
        for ln in f:
            parts = ln.split("|")
            if len(parts) <= 31:
                continue
            try:
                ra = float(parts[6]); dec = float(parts[7]); sv = float(parts[10]); rms = float(parts[14])
            except ValueError:
                continue
            total_rows += 1
            pix = hp.ang2pix(NSIDE, math.radians(90.0 - dec), math.radians(ra))
            rms_sum[pix] += rms
            rms_cnt[pix] += 1.0
            if sv >= 15.0:
                for c in cuts:
                    if sv >= c:
                        cts_raw[c][pix] += 1.0
                        if rms <= 0.45:
                            cts_unif[c][pix] += 1.0
    mean_rms = np.divide(rms_sum, np.maximum(rms_cnt, 1.0))
    fp_raw = base_mask & (PIX_DEC_DEG >= -79.5) & (PIX_DEC_DEG <= 29.5)
    fp_unif = base_mask & (PIX_DEC_DEG >= -75.0) & (PIX_DEC_DEG <= 25.0) & (rms_cnt >= 50) & (mean_rms <= 0.45)
    fp_nvss_ov = fp_unif & (PIX_DEC_DEG >= -36.5)
    return {
        "total_parsed_rows": total_rows,
        "raw_footprint_ladder_mJy": {str(int(c)): _fit_wls_dipole(cts_raw[c], fp_raw) for c in cuts},
        # Use cts_raw[c] on uniform-RMS pixels so individual-source rms<=0.45 cuts do not induce partial-cell completeness bias
        "rms_uniform_footprint_ladder_mJy": {str(int(c)): _fit_wls_dipole(cts_raw[c], fp_unif) for c in cuts},
        "rms_uniform_nvss_overlap_S20_S30": {
            "20": _fit_wls_dipole(cts_raw[20.0], fp_nvss_ov),
            "30": _fit_wls_dipole(cts_raw[30.0], fp_nvss_ov),
        },
        "source_level_rms_cut_0p45_biased_selection_contrast_S20": _fit_wls_dipole(cts_unif[20.0], fp_unif),
    }


def _scan_spice_racs(base_mask: np.ndarray) -> dict:
    cuts = (20.0, 30.0, 50.0)
    cts = {c: np.zeros(NPIX, dtype=np.float64) for c in cuts}
    total_rows = 0
    with gzip.open(SPICE_GZ, "rt", encoding="ascii", errors="ignore") as f:
        for ln in f:
            if len(ln) < 166:
                continue
            try:
                ra = float(ln[56:71])
                dec = float(ln[88:103])
                ftot = float(ln[152:166])
            except ValueError:
                continue
            total_rows += 1
            if ftot < 20.0:
                continue
            pix = hp.ang2pix(NSIDE, math.radians(90.0 - dec), math.radians(ra))
            for c in cuts:
                if ftot >= c:
                    cts[c][pix] += 1.0
    fp_all = base_mask & (PIX_DEC_DEG >= -88.0) & (PIX_DEC_DEG <= 48.0)
    fp_ov = base_mask & (PIX_DEC_DEG >= -36.5) & (PIX_DEC_DEG <= 48.0)
    return {
        "total_parsed_rows": total_rows,
        "full_footprint_ladder_mJy": {str(int(c)): _fit_wls_dipole(cts[c], fp_all) for c in cuts},
        "nvss_overlap_band_S20_S30": {
            "20": _fit_wls_dipole(cts[20.0], fp_ov),
            "30": _fit_wls_dipole(cts[30.0], fp_ov),
        },
    }


def _scan_sumss(base_mask: np.ndarray) -> dict:
    cuts = (15.0, 20.0, 30.0, 50.0)
    cts = {c: np.zeros(NPIX, dtype=np.float64) for c in cuts}
    total_rows = 0
    with gzip.open(SUMSS_GZ, "rt", encoding="ascii", errors="ignore") as f:
        for ln in f:
            if len(ln) < 62:
                continue
            try:
                rah = float(ln[0:2]); ram = float(ln[3:5]); ras = float(ln[6:11])
                sgn = -1.0 if ln[13:14] == "-" else 1.0
                ded = float(ln[14:16]); dem = float(ln[17:19]); des = float(ln[20:25])
                st = float(ln[54:62])
            except ValueError:
                continue
            total_rows += 1
            if st < 15.0:
                continue
            ra = 15.0 * (rah + ram / 60.0 + ras / 3600.0)
            dec = sgn * (ded + dem / 60.0 + des / 3600.0)
            if dec > -30.0:
                continue
            pix = hp.ang2pix(NSIDE, math.radians(90.0 - dec), math.radians(ra))
            for c in cuts:
                if st >= c:
                    cts[c][pix] += 1.0
    fp = base_mask & (PIX_DEC_DEG <= -30.5)
    return {
        "total_parsed_rows": total_rows,
        "flux_ladder_mJy": {str(int(c)): _fit_wls_dipole(cts[c], fp) for c in cuts},
    }


def _scan_lotss(base_mask: np.ndarray) -> dict:
    cuts = (20.0, 50.0, 100.0)
    cts_all = np.zeros(NPIX, dtype=np.float64)
    cts = {c: np.zeros(NPIX, dtype=np.float64) for c in cuts}
    with fits.open(LOTSS_FITS, memmap=True) as hd:
        nrows = int(hd[1].header["NAXIS2"])
        data = hd[1].data
        chunk = 500_000
        for i in range(0, nrows, chunk):
            j = min(i + chunk, nrows)
            ra = np.asarray(data["RA"][i:j], dtype=np.float64)
            dec = np.asarray(data["DEC"][i:j], dtype=np.float64)
            ft = np.asarray(data["Total_flux"][i:j], dtype=np.float64)
            ok = np.isfinite(ra) & np.isfinite(dec) & np.isfinite(ft)
            if not np.any(ok):
                continue
            pix = hp.ang2pix(NSIDE, np.deg2rad(90.0 - dec[ok]), np.deg2rad(ra[ok]))
            cts_all += np.bincount(pix, minlength=NPIX)
            fok = ft[ok]
            for c in cuts:
                m = fok >= c
                if np.any(m):
                    cts[c] += np.bincount(pix[m], minlength=NPIX)
    # LoTSS covers northern footprint with partial edge pixels (cts_all in [500, 1500)); restrict interior to cts_all >= 1500
    fp_edge500 = base_mask & (cts_all >= 500.0) & (np.abs(PIX_B_DEG) > 20.0)
    fp = base_mask & (cts_all >= 1500.0) & (np.abs(PIX_B_DEG) > 20.0)
    return {
        "total_rows": nrows,
        "interior_cut_min_raw_per_pix": 1500,
        "flux_ladder_mJy": {str(int(c)): _fit_wls_dipole(cts[c], fp) for c in cuts},
        "edge500_sensitivity_S50": _fit_wls_dipole(cts[50.0], fp_edge500),
    }


def main() -> int:
    if OUT_JSON.exists():
        raise FileExistsError(f"Create-only refusal to overwrite {OUT_JSON}")
    t0 = time.perf_counter()

    nhi_icrs = _build_nhi_ns16_icrs()
    nhi_thresh = 1e21  # 10^21 cm^-2 HI4PI clean extragalactic threshold
    base_mask = (np.abs(PIX_B_DEG) > 15.0) & (nhi_icrs < nhi_thresh)

    nvss_res = _scan_nvss(base_mask)
    racs_res = _scan_racs_dr1(base_mask)
    spice_res = _scan_spice_racs(base_mask)
    sumss_res = _scan_sumss(base_mask)
    lotss_res = _scan_lotss(base_mask)

    elapsed = time.perf_counter() - t0
    out = {
        "schema": "htt.r89.g04_radio_five_survey_deep/1",
        "group_id": "G04_RADIO_FRAME",
        "node_ids": ["V01", "V02", "V03", "SQ-FRAME", "SQ-RADIO", "V04", "V05", "V06"],
        "mask_policy": {
            "nside": NSIDE,
            "abs_b_min_deg": 15.0,
            "nhi_max_cm2": nhi_thresh,
            "base_valid_pixels": int(np.sum(base_mask)),
        },
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "elapsed_seconds": float(elapsed),
            "maxrss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        },
        "surveys": {
            "NVSS_1400MHz": nvss_res,
            "RACS_low_DR1_888MHz": racs_res,
            "SPICE_RACS_DR2_944MHz": spice_res,
            "SUMSS_v21_843MHz": sumss_res,
            "LoTSS_DR3_144MHz": lotss_res,
        },
        "node_verdicts": {
            "V01": "REUSED_SCOPED",
            "V02": "REUSED_SCOPED",
            "V03": "REUSED_SCOPED",
            "SQ-FRAME": "DIAGNOSTIC_COMPLETED_SCOPED",
            "SQ-RADIO": "DIAGNOSTIC_COMPLETED_SCOPED",
            "V04": "BLOCKED_DEPENDENCY",
            "V05": "BLOCKED_DEPENDENCY",
            "V06": "BLOCKED_DEPENDENCY",
        },
        "claim_hygiene": {
            "physical_Pi": None,
            "physical_GF": None,
            "bianchi_family_identified": False,
            "statement": (
                "Empirical radio number-count dipole flux-ladder and pixel-RMS uniformity diagnostics only; "
                "not a tile/beam-calibrated physical velocity measurement or Bianchi family claim."
            ),
        },
        "physical_gate_note": "Uniform RMS cuts on RACS-low DR1 and 5-frequency flux ladders quantify empirical survey selection/noise sensitivity; V04-V06 remain BLOCKED_DEPENDENCY pending tile/beam completeness transfer and common-congruence anchor.",
    }
    OUT_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "group_id": "G04_RADIO_DEEP",
        "elapsed_s": round(elapsed, 3),
        "nvss_S20_amp": round(nvss_res["flux_ladder_mJy"]["20"]["dipole_amplitude"], 5),
        "racs_raw_S20_amp": round(racs_res["raw_footprint_ladder_mJy"]["20"]["dipole_amplitude"], 5),
        "racs_unif_S20_amp": round(racs_res["rms_uniform_footprint_ladder_mJy"]["20"]["dipole_amplitude"], 5),
        "spice_S20_amp": round(spice_res["full_footprint_ladder_mJy"]["20"]["dipole_amplitude"], 5),
        "sumss_S20_amp": round(sumss_res["flux_ladder_mJy"]["20"]["dipole_amplitude"], 5),
        "lotss_S50_amp": round(lotss_res["flux_ladder_mJy"]["50"]["dipole_amplitude"], 5),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
