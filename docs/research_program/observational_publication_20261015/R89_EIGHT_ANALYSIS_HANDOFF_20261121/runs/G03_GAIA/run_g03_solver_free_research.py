#!/usr/bin/env python3
"""R89 G03_GAIA Solver-Free Research Completion (create-only).

Covers Section 4:
A. Joint 20-parameter VSH (16 modes) + Gaia Scanning-Law nuisance templates
   (scalar hit-density gradient, curl gradient, spin-2 Q/U_COSMO modes) over all
   1,203,489 clean Gaia CRF3 QSOs.
B. Quaia-CRF3 692,154 QSO 4-bin redshift tomography (unweighted & selection_relative),
   plus Gaia magnitude (G), color (bp_rp), ICRF3 cross-match, and frame-rotator splits.
C. Empirical 48-patch (NSIDE=2) Jackknife & cluster-robust Sandwich covariance
   + Gaia-vs-VLBA (exact Dec bytes) difference & normal-frame identifiable subspace.
"""
from __future__ import annotations

import gzip
import hashlib
import io
import json
import math
import os
import platform
import resource
import sys
import time
import zipfile
from pathlib import Path

import healpy as hp
import numpy as np
from astropy.io import fits
from scipy.stats import chi2

ROOT = Path(__file__).resolve().parents[6]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from htt.obsstat import pre_dag_fast
from scripts.r69.gaia_e2_b2 import fit_case, prepare, templates

OUT_DIR = Path(__file__).resolve().parent
OUT_JSON = OUT_DIR / "SOLVER_FREE_RESEARCH_RESULT.json"

WORKDIR = Path("/mnt/extdrive/workdir")
SCANLAW_ZIP = WORKDIR / "raw/gaia_scanning_law_20261110/FullGaiaMissionScanningLaw.zip"
SCANLAW_MEMBER = "FullGaiaMissionScanningLaw/commanded_scan_law.csv.gz"
GAIA_FULL_FITS = WORKDIR / "raw/observational_bundles/Gaia_CRF3_astrometry/gaia_crf3_astrometry_full.fits"
XM_FLAGS_FITS = WORKDIR / "raw/new_acquisitions/optical/Gaia_CRF3_flags/gaia_crf3_xm_icrf_flags.fits"
FRAME_ROT_FITS = WORKDIR / "raw/new_acquisitions/optical/Gaia_CRF3_flags/frame_rotator_source.fits"
QUAIA_JOIN_NPZ = WORKDIR / "htt_open_data/a22_20261023/quaia_join/quaia_crf3_join.npz"
VLBA_T6 = WORKDIR / "htt_open_data/vlba/233_3/table6.dat"

NSIDE_SCAN = 32
NPIX_SCAN = hp.nside2npix(NSIDE_SCAN)
NSIDE_PATCH = 2
NPATCH = hp.nside2npix(NSIDE_PATCH)
THREADS = int(os.environ.get("OMP_NUM_THREADS", "4"))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def _build_scanlaw_templates() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    hits = np.zeros(NPIX_SCAN, dtype=np.float64)
    c2_sum = np.zeros(NPIX_SCAN, dtype=np.float64)
    s2_sum = np.zeros(NPIX_SCAN, dtype=np.float64)

    with zipfile.ZipFile(SCANLAW_ZIP, "r") as zf:
        with zf.open(SCANLAW_MEMBER, "r") as raw_f:
            with gzip.GzipFile(fileobj=raw_f) as gz:
                import pandas as pd

                reader = pd.read_csv(
                    gz,
                    comment="#",
                    usecols=["ra_fov1", "dec_fov1", "scan_angle_fov1", "ra_fov2", "dec_fov2", "scan_angle_fov2"],
                    chunksize=500000,
                    dtype=np.float64,
                )
                for df in reader:
                    for suff in ("fov1", "fov2"):
                        ra = df[f"ra_{suff}"].to_numpy()
                        dec = df[f"dec_{suff}"].to_numpy()
                        psi = np.deg2rad(df[f"scan_angle_{suff}"].to_numpy())
                        pix = hp.ang2pix(NSIDE_SCAN, np.deg2rad(90.0 - dec), np.deg2rad(ra))
                        np.add.at(hits, pix, 1.0)
                        np.add.at(c2_sum, pix, np.cos(2.0 * psi))
                        np.add.at(s2_sum, pix, np.sin(2.0 * psi))

    delta_n = (hits / max(float(np.mean(hits)), 1.0)) - 1.0
    q_scan = np.divide(c2_sum, np.maximum(hits, 1.0))
    u_scan_cosmo = -np.divide(s2_sum, np.maximum(hits, 1.0))
    alms = hp.map2alm([delta_n, q_scan, u_scan_cosmo], lmax=8, pol=True)
    _, d_th, d_ph = hp.alm2map_der1(alms[0], NSIDE_SCAN, lmax=8)
    # e_ra = +e_phi, e_dec = -e_theta
    grad_ra = d_ph
    grad_dec = -d_th
    return grad_ra, grad_dec, q_scan, u_scan_cosmo, delta_n


def _accum_general_gaussian(B: np.ndarray, y: np.ndarray, e1: np.ndarray, e2: np.ndarray, rho: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    inv_1m = 1.0 / (1.0 - rho * rho)
    r1 = (y[:, 0] * inv_1m) / (e1 * e1) - (rho * y[:, 1] * inv_1m) / (e1 * e2)
    r2 = (y[:, 1] * inv_1m) / (e2 * e2) - (rho * y[:, 0] * inv_1m) / (e1 * e2)
    B0 = B[:, 0, :]
    B1 = B[:, 1, :]
    C0 = (B0 * (inv_1m / (e1 * e1))[:, None]) - (B1 * (rho * inv_1m / (e1 * e2))[:, None])
    C1 = (B1 * (inv_1m / (e2 * e2))[:, None]) - (B0 * (rho * inv_1m / (e1 * e2))[:, None])
    F = B0.T @ C0 + B1.T @ C1
    F = 0.5 * (F + F.T)
    score = B0.T @ r1 + B1.T @ r2
    chisq = float(np.sum(y[:, 0] * r1 + y[:, 1] * r2))
    return F, score, chisq


def _finalize_16(acc: dict) -> dict:
    fit = fit_case(acc)
    cov = np.asarray(fit["formal_cov_microasyr2"], dtype=np.float64)
    return {
        "n_sources": fit["n_sources"],
        "rank": fit["rank"],
        "F_condition": fit["F_condition"],
        "coefs_microasyr": fit["coefs_microasyr"],
        "formal_errors_microasyr": fit["formal_errors_microasyr"],
        "E1_amp_microasyr": fit["groups_amplitude_microasyr"]["E1"],
        "B1_amp_microasyr": fit["groups_amplitude_microasyr"]["B1"],
        "E2_amp_microasyr": fit["groups_amplitude_microasyr"]["E2"],
        "B2_amp_microasyr": fit["groups_amplitude_microasyr"]["B2"],
        "chi2_per_dof_working": fit["chi2_per_dof_working"],
        "_cov_16": cov.tolist(),
    }


def _strip_cov(d: dict) -> dict:
    return {k: v for k, v in d.items() if not k.startswith("_")}


def _wald_subspaces(delta_uasyr: np.ndarray, cov_uasyr2: np.ndarray) -> dict:
    out = {}
    for name, sl in [("all_16D", slice(0, 16)), ("E1_3D", slice(0, 3)), ("B1_3D", slice(3, 6)), ("E2_5D", slice(6, 11)), ("B2_5D", slice(11, 16))]:
        d = delta_uasyr[sl]
        c = 0.5 * (cov_uasyr2[sl, sl] + cov_uasyr2[sl, sl].T)
        w = float(d @ np.linalg.solve(c, d))
        out[name] = {
            "norm_microasyr": float(np.linalg.norm(d)),
            "wald_chi2": w,
            "dof": len(d),
            "p_nominal": float(chi2.sf(w, len(d))),
        }
    return out


def _part_a_and_c_gaia_scan_and_jackknife(grad_ra: np.ndarray, grad_dec: np.ndarray, q_scan: np.ndarray, u_scan: np.ndarray) -> tuple[dict, dict, dict]:
    split_names = [
        "quality_all",
        "g_lt_19",
        "g_19_to_20",
        "g_ge_20",
        "bprp_lt_0p6",
        "bprp_ge_0p6",
        "icrf3_matched",
        "non_icrf3",
        "frame_rotator_spin",
        "non_frame_rotator_spin",
    ]
    accum = {k: {"F": np.zeros((16, 16)), "score": np.zeros(16), "chisq": 0.0, "N": 0} for k in split_names}
    F20 = np.zeros((20, 20), dtype=np.float64)
    sc20 = np.zeros(20, dtype=np.float64)
    c20 = 0.0
    n_qall = 0

    F_patch = np.zeros((NPATCH, 16, 16), dtype=np.float64)
    s_patch = np.zeros((NPATCH, 16), dtype=np.float64)
    n_patch = np.zeros(NPATCH, dtype=np.int64)

    with fits.open(FRAME_ROT_FITS, memmap=True) as fh:
        fd = fh[1].data
        spin_ids = np.asarray(fd["source_id"][np.asarray(fd["used_for_reference_frame_spin"], dtype=bool)], dtype=np.int64)
    spin_ids.sort()

    with fits.open(XM_FLAGS_FITS, memmap=True) as fx:
        xd = fx[1].data
        xm_mask = (
            np.asarray(xd["icrf3sx"], dtype=bool)
            | np.asarray(xd["icrf3k"], dtype=bool)
            | np.asarray(xd["icrf3xka"], dtype=bool)
        )
        icrf3_ids = np.asarray(xd["source_id"][xm_mask], dtype=np.int64)
    icrf3_ids.sort()

    with fits.open(GAIA_FULL_FITS, memmap=True) as fg:
        gtab = fg[1].data
        nrows = len(gtab)
        chunk = 100000
        for i in range(0, nrows, chunk):
            j = min(i + chunk, nrows)
            z = gtab[i:j]

            ra_r, dec_r, y1, y2, e1, e2, rho, valid, qual = prepare(z)
            solved = np.asarray(z["astrometric_params_solved"], dtype=np.int64)
            keep = valid & qual & (solved == 31) & (np.abs(y1) < 100.0) & (np.abs(y2) < 100.0)
            if not np.any(keep):
                continue

            ra_k, dec_k = ra_r[keep], dec_r[keep]
            yy = np.column_stack([y1[keep], y2[keep]])
            e1k, e2k, rhok = e1[keep], e2[keep], rho[keep]
            sid_k = np.asarray(z["source_id"][keep], dtype=np.int64)
            gmag_k = np.asarray(z["phot_g_mean_mag"][keep], dtype=np.float64)
            bprp_k = np.asarray(z["bp_rp"][keep], dtype=np.float64)
            pos_ic = np.searchsorted(icrf3_ids, sid_k)
            icrf_k = (pos_ic < len(icrf3_ids)) & (icrf3_ids[np.minimum(pos_ic, max(len(icrf3_ids) - 1, 0))] == sid_k)
            pos = np.searchsorted(spin_ids, sid_k)
            is_spin = (pos < len(spin_ids)) & (spin_ids[np.minimum(pos, max(len(spin_ids) - 1, 0))] == sid_k)

            _, B16 = templates(ra_k, dec_k)
            pix_scan = hp.ang2pix(NSIDE_SCAN, 0.5 * np.pi - dec_k, ra_k)
            n_k = len(ra_k)
            n_qall += n_k

            # 20-param joint VSH + Scanning-Law nuisance templates
            B20 = np.empty((n_k, 2, 20), dtype=np.float64)
            B20[:, :, :16] = B16
            B20[:, 0, 16] = grad_ra[pix_scan];  B20[:, 1, 16] = grad_dec[pix_scan]
            B20[:, 0, 17] = -grad_dec[pix_scan]; B20[:, 1, 17] = grad_ra[pix_scan]
            B20[:, 0, 18] = q_scan[pix_scan];   B20[:, 1, 18] = u_scan[pix_scan]
            B20[:, 0, 19] = -u_scan[pix_scan];  B20[:, 1, 19] = q_scan[pix_scan]
            FF20, sc_20, chi_20 = _accum_general_gaussian(B20, yy, e1k, e2k, rhok)
            F20 += FF20
            sc20 += sc_20
            c20 += chi_20

            # 48-patch accumulation for jackknife & sandwich covariance
            pix_p = hp.ang2pix(NSIDE_PATCH, 0.5 * np.pi - dec_k, ra_k)
            for pid in np.unique(pix_p):
                mp = pix_p == pid
                FFp, scp, _ = pre_dag_fast.accumulate_gaia(B16[mp], yy[mp], e1k[mp], e2k[mp], rhok[mp], threads=THREADS)
                F_patch[pid] += FFp
                s_patch[pid] += scp
                n_patch[pid] += int(np.count_nonzero(mp))

            masks = {
                "quality_all": np.ones(n_k, dtype=bool),
                "g_lt_19": np.isfinite(gmag_k) & (gmag_k < 19.0),
                "g_19_to_20": np.isfinite(gmag_k) & (gmag_k >= 19.0) & (gmag_k < 20.0),
                "g_ge_20": np.isfinite(gmag_k) & (gmag_k >= 20.0),
                "bprp_lt_0p6": np.isfinite(bprp_k) & (bprp_k < 0.6),
                "bprp_ge_0p6": np.isfinite(bprp_k) & (bprp_k >= 0.6),
                "icrf3_matched": icrf_k,
                "non_icrf3": ~icrf_k,
                "frame_rotator_spin": is_spin,
                "non_frame_rotator_spin": ~is_spin,
            }
            for sk, mk in masks.items():
                if not np.any(mk):
                    continue
                FFs, scs, c2s = pre_dag_fast.accumulate_gaia(B16[mk], yy[mk], e1k[mk], e2k[mk], rhok[mk], threads=THREADS)
                accum[sk]["F"] += FFs
                accum[sk]["score"] += scs
                accum[sk]["chisq"] += c2s
                accum[sk]["N"] += int(np.count_nonzero(mk))

    # Finalize 20-param joint scanlaw fit
    beta20_uas = np.linalg.solve(F20, sc20) * 1000.0
    cov20_uas2 = np.linalg.inv(F20) * 1e6
    beta16_uas = np.linalg.solve(accum["quality_all"]["F"], accum["quality_all"]["score"]) * 1000.0
    cov16_uas2 = np.linalg.inv(accum["quality_all"]["F"]) * 1e6
    eig20 = np.linalg.eigvalsh(F20)
    err20 = np.sqrt(np.diag(cov20_uas2))
    nuisance_z = beta20_uas[16:] / err20[16:]
    # Correlations between VSH modes and 4 scanlaw parameters from inverse Fisher
    sd20 = np.sqrt(np.diag(cov20_uas2))
    corr_20 = cov20_uas2 / np.outer(sd20, sd20)
    part_a = {
        "epistemic_status": "conditional",
        "n_quality_all": n_qall,
        "joint_20p_F_condition": float(eig20.max() / max(eig20.min(), 1e-30)),
        "joint_20p_chi2_per_dof": float((c20 - (beta20_uas / 1000.0) @ sc20) / (2 * n_qall - 20)),
        "vsh_16_without_scanlaw_uasyr": beta16_uas.tolist(),
        "vsh_16_with_scanlaw_deproj_uasyr": beta20_uas[:16].tolist(),
        "delta_vsh_shift_norm_E1_B1_E2_B2_uasyr": {
            "E1": float(np.linalg.norm(beta20_uas[0:3] - beta16_uas[0:3])),
            "B1": float(np.linalg.norm(beta20_uas[3:6] - beta16_uas[3:6])),
            "E2": float(np.linalg.norm(beta20_uas[6:11] - beta16_uas[6:11])),
            "B2": float(np.linalg.norm(beta20_uas[11:16] - beta16_uas[11:16])),
        },
        "scanlaw_4_nuisance_params_uasyr": {
            "names": ["grad_deltaN", "curl_grad_deltaN", "spin2_Q_scan", "spin2_U_cosmo_scan"],
            "estimates": beta20_uas[16:].tolist(),
            "formal_errors": err20[16:].tolist(),
            "formal_z_scores": nuisance_z.tolist(),
            "max_abs_corr_with_E2_modes": float(np.max(np.abs(corr_20[6:11, 16:20]))),
            "max_abs_corr_with_B2_modes": float(np.max(np.abs(corr_20[11:16, 16:20]))),
        },
    }

    # Finalize Gaia population splits + contrasts
    sub_fits = {k: _finalize_16(accum[k]) for k in split_names}
    contrasts = {
        "g_lt19_vs_ge20": _wald_subspaces(
            np.asarray(sub_fits["g_lt_19"]["coefs_microasyr"]) - np.asarray(sub_fits["g_ge_20"]["coefs_microasyr"]),
            np.asarray(sub_fits["g_lt_19"]["_cov_16"]) + np.asarray(sub_fits["g_ge_20"]["_cov_16"]),
        ),
        "bprp_blue_vs_red": _wald_subspaces(
            np.asarray(sub_fits["bprp_lt_0p6"]["coefs_microasyr"]) - np.asarray(sub_fits["bprp_ge_0p6"]["coefs_microasyr"]),
            np.asarray(sub_fits["bprp_lt_0p6"]["_cov_16"]) + np.asarray(sub_fits["bprp_ge_0p6"]["_cov_16"]),
        ),
        "icrf3_vs_non_icrf3": _wald_subspaces(
            np.asarray(sub_fits["icrf3_matched"]["coefs_microasyr"]) - np.asarray(sub_fits["non_icrf3"]["coefs_microasyr"]),
            np.asarray(sub_fits["icrf3_matched"]["_cov_16"]) + np.asarray(sub_fits["non_icrf3"]["_cov_16"]),
        ),
        "frame_rotator_spin_vs_non_rotator": _wald_subspaces(
            np.asarray(sub_fits["frame_rotator_spin"]["coefs_microasyr"]) - np.asarray(sub_fits["non_frame_rotator_spin"]["coefs_microasyr"]),
            np.asarray(sub_fits["frame_rotator_spin"]["_cov_16"]) + np.asarray(sub_fits["non_frame_rotator_spin"]["_cov_16"]),
        ),
    }
    part_splits = {
        "epistemic_status": "conditional",
        "subsets": {k: _strip_cov(v) for k, v in sub_fits.items()},
        "disjoint_contrasts": contrasts,
    }

    # Empirical 48-patch Sandwich + Leave-One-Patch-Out Jackknife
    active_p = np.flatnonzero(n_patch > 0)
    F_tot = accum["quality_all"]["F"]
    s_tot = accum["quality_all"]["score"]
    beta_hat_mas = np.linalg.solve(F_tot, s_tot)
    meat = np.zeros((16, 16), dtype=np.float64)
    jk_betas = []
    for p in active_p:
        gp = s_patch[p] - F_patch[p] @ beta_hat_mas
        meat += np.outer(gp, gp)
        Fp_m = F_tot - F_patch[p]
        sp_m = s_tot - s_patch[p]
        jk_betas.append(np.linalg.solve(Fp_m, sp_m) * 1000.0)
    C_inv = np.linalg.inv(F_tot)
    M_p = len(active_p)
    # Cluster-robust sandwich covariance (scale M/(M-1) finite-cluster correction)
    cov_sand_uas2 = (M_p / max(M_p - 1, 1)) * (C_inv @ meat @ C_inv) * 1e6
    jk_arr = np.asarray(jk_betas, dtype=np.float64)
    jk_mean = jk_arr.mean(axis=0)
    jk_diff = jk_arr - jk_mean[None, :]
    cov_jk_uas2 = ((M_p - 1.0) / M_p) * (jk_diff.T @ jk_diff)

    part_robust = {
        "epistemic_status": "numerically_checked",
        "n_active_nside2_patches": int(M_p),
        "nominal_diag_std_uasyr": np.sqrt(np.diag(cov16_uas2)).tolist(),
        "sandwich_std_uasyr": np.sqrt(np.diag(cov_sand_uas2)).tolist(),
        "jackknife_std_uasyr": np.sqrt(np.diag(cov_jk_uas2)).tolist(),
        "inflation_ratio_sandwich_over_nominal": (np.sqrt(np.diag(cov_sand_uas2)) / np.sqrt(np.diag(cov16_uas2))).tolist(),
        "inflation_ratio_jackknife_over_nominal": (np.sqrt(np.diag(cov_jk_uas2)) / np.sqrt(np.diag(cov16_uas2))).tolist(),
        "nominal_wald_subspaces": _wald_subspaces(beta16_uas, cov16_uas2),
        "sandwich_robust_wald_subspaces": _wald_subspaces(beta16_uas, cov_sand_uas2),
        "jackknife_robust_wald_subspaces": _wald_subspaces(beta16_uas, cov_jk_uas2),
        "_gaia_qall": sub_fits["quality_all"],
        "_cov_jk": cov_jk_uas2.tolist(),
    }
    return part_a, part_splits, part_robust


def _part_b_quaia_z_tomography() -> dict:
    with np.load(QUAIA_JOIN_NPZ, allow_pickle=False) as z:
        ra = np.asarray(z["ra"], dtype=np.float64)
        dec = np.asarray(z["dec"], dtype=np.float64)
        zq = np.asarray(z["redshift_quaia"], dtype=np.float64)
        pmra = np.asarray(z["gaia_pmra"], dtype=np.float64)
        pmdec = np.asarray(z["gaia_pmdec"], dtype=np.float64)
        epmra = np.asarray(z["gaia_pmra_error"], dtype=np.float64)
        epmdec = np.asarray(z["gaia_pmdec_error"], dtype=np.float64)
        rho = np.asarray(z["gaia_pmra_pmdec_corr"], dtype=np.float64)
        ruwe = np.asarray(z["gaia_ruwe"], dtype=np.float64)
        solved = np.asarray(z["gaia_astrometric_params_solved"], dtype=np.float64)
        sel_rel = np.asarray(z["selection_relative"], dtype=np.float64)

    clean = (
        np.isfinite(ra) & np.isfinite(dec) & np.isfinite(zq)
        & np.isfinite(pmra) & np.isfinite(pmdec) & np.isfinite(epmra) & np.isfinite(epmdec) & np.isfinite(rho)
        & (epmra > 0) & (epmdec > 0) & (np.abs(rho) < 0.999)
        & (ruwe < 1.4) & (solved == 31) & (np.abs(pmra) < 100.0) & (np.abs(pmdec) < 100.0)
    )
    bins = [
        ("z_lt_0p8", clean & (zq < 0.8)),
        ("z_0p8_1p4", clean & (zq >= 0.8) & (zq < 1.4)),
        ("z_1p4_2p1", clean & (zq >= 1.4) & (zq < 2.1)),
        ("z_ge_2p1", clean & (zq >= 2.1)),
    ]
    z_results = {}
    raw_fits = {}
    for bname, bm in bins:
        idx = np.flatnonzero(bm)
        F_u = np.zeros((16, 16)); s_u = np.zeros(16); c_u = 0.0
        F_w = np.zeros((16, 16)); s_w = np.zeros(16); c_w = 0.0
        chunk = 65536
        for start in range(0, len(idx), chunk):
            ii = idx[start : min(start + chunk, len(idx))]
            _, B = templates(np.deg2rad(ra[ii]), np.deg2rad(dec[ii]))
            yy = np.column_stack([pmra[ii], pmdec[ii]])
            FF, sc, cc = pre_dag_fast.accumulate_gaia(B, yy, epmra[ii], epmdec[ii], rho[ii], threads=THREADS)
            F_u += FF; s_u += sc; c_u += cc
            inv_s = 1.0 / np.sqrt(np.clip(sel_rel[ii], 1e-4, 1.0))
            FFw, scw, ccw = pre_dag_fast.accumulate_gaia(B, yy, epmra[ii] * inv_s, epmdec[ii] * inv_s, rho[ii], threads=THREADS)
            F_w += FFw; s_w += scw; c_w += ccw
        fu = _finalize_16({"F": F_u, "score": s_u, "chisq": c_u, "N": int(len(idx))})
        fw = _finalize_16({"F": F_w, "score": s_w, "chisq": c_w, "N": int(len(idx))})
        raw_fits[bname] = fu
        z_results[bname] = {
            "median_z": float(np.median(zq[idx])),
            "unweighted": _strip_cov(fu),
            "selection_weighted": _strip_cov(fw),
        }

    # Test redshift constancy between low-z (z<0.8) and high-z (z>=2.1)
    c_lo_hi = _wald_subspaces(
        np.asarray(raw_fits["z_lt_0p8"]["coefs_microasyr"]) - np.asarray(raw_fits["z_ge_2p1"]["coefs_microasyr"]),
        np.asarray(raw_fits["z_lt_0p8"]["_cov_16"]) + np.asarray(raw_fits["z_ge_2p1"]["_cov_16"]),
    )
    return {
        "epistemic_status": "conditional",
        "quaia_join_sha256": _sha256(QUAIA_JOIN_NPZ),
        "n_clean": int(np.count_nonzero(clean)),
        "redshift_bins": z_results,
        "z_lt_0p8_vs_ge_2p1_disjoint_contrast": c_lo_hi,
    }


def _part_c_vlba_comparison(gaia_qall: dict, cov_jk_gaia: np.ndarray) -> dict:
    ra_l, dec_l, pmra_l, pmdec_l, e1_l, e2_l = [], [], [], [], [], []
    with VLBA_T6.open("r", encoding="ascii", errors="ignore") as f:
        for ln in f:
            if not ln.strip():
                continue
            try:
                rah, ram, ras = float(ln[9:11]), float(ln[12:14]), float(ln[15:24])
                sign = -1.0 if ln[32] == "-" else 1.0
                ded, dem, des = float(ln[33:35]), float(ln[36:38]), float(ln[39:48])
                pmra = float(ln[56:64]) * 1e-3
                epmra = float(ln[65:72]) * 1e-3
                pmdec = float(ln[84:91]) * 1e-3
                epmdec = float(ln[92:99]) * 1e-3
            except (ValueError, IndexError):
                continue
            if epmra > 0 and epmdec > 0 and math.isfinite(pmra) and math.isfinite(pmdec):
                ra_l.append(15.0 * (rah + ram / 60.0 + ras / 3600.0))
                dec_l.append(sign * (ded + dem / 60.0 + des / 3600.0))
                pmra_l.append(pmra); pmdec_l.append(pmdec); e1_l.append(epmra); e2_l.append(epmdec)
    ra = np.array(ra_l); dec = np.array(dec_l); pmra = np.array(pmra_l); pmdec = np.array(pmdec_l); e1 = np.array(e1_l); e2 = np.array(e2_l)
    m = np.maximum(np.abs(pmra) / e1, np.abs(pmdec) / e2) < 5.0
    _, B = templates(np.deg2rad(ra[m]), np.deg2rad(dec[m]))
    yy = np.column_stack([pmra[m], pmdec[m]])
    F, sc, c2 = pre_dag_fast.accumulate_gaia(B, yy, e1[m], e2[m], np.zeros_like(ra[m]), threads=THREADS)
    vlba_fit = _finalize_16({"F": F, "score": sc, "chisq": c2, "N": int(np.count_nonzero(m))})

    diff = np.asarray(gaia_qall["coefs_microasyr"]) - np.asarray(vlba_fit["coefs_microasyr"])
    cov_nom_comb = np.asarray(gaia_qall["_cov_16"]) + np.asarray(vlba_fit["_cov_16"])
    # Inflate VLBA variance by empirical chi2/dof ~ 2.30 vs Gaia 48-patch jackknife covariance
    cov_robust_comb = cov_jk_gaia + vlba_fit["chi2_per_dof_working"] * np.asarray(vlba_fit["_cov_16"])
    return {
        "epistemic_status": "conditional",
        "vlba_clean_5sigma": _strip_cov(vlba_fit),
        "gaia_vs_vlba_nominal_cov": _wald_subspaces(diff, cov_nom_comb),
        "gaia_jk_vs_vlba_chi2dof_scaled_cov": _wald_subspaces(diff, cov_robust_comb),
        "normal_frame_identifiability_note": (
            "In 1+3 kinematics, radial-free VSH alone identifies pure-E2 shear up to isotropic/selection "
            "systematics (B2=0 falsifier for homogeneous local shear), whereas B1 = Omega_frame - omega_cosmic "
            "carries an irreducible spin-vorticity degeneracy; E1 measures Galactocentric aberration + boost."
        ),
    }


def main() -> int:
    if OUT_JSON.exists():
        raise FileExistsError(f"Create-only refusal to overwrite {OUT_JSON}")
    t0 = time.perf_counter()

    grad_ra, grad_dec, q_scan, u_scan, _ = _build_scanlaw_templates()
    part_a, part_splits, part_robust = _part_a_and_c_gaia_scan_and_jackknife(grad_ra, grad_dec, q_scan, u_scan)
    part_b = _part_b_quaia_z_tomography()
    gaia_qall = part_robust.pop("_gaia_qall")
    cov_jk = np.asarray(part_robust.pop("_cov_jk"), dtype=np.float64)
    part_c_vlba = _part_c_vlba_comparison(gaia_qall, cov_jk)

    dt = time.perf_counter() - t0
    rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    payload = {
        "artifact_id": "R89_G03_GAIA_SOLVER_FREE_RESEARCH_V1",
        "group_id": "G03_GAIA",
        "create_only": True,
        "sq_gaia_status": "DIAGNOSTIC_COMPLETED_SCOPED",
        "runtime_sec": round(dt, 3),
        "max_rss_mb": round(rss_mb, 2),
        "platform": platform.platform(),
        "part_a_joint_scanlaw_deprojection": part_a,
        "part_b_population_and_quaia_tomography": {
            "gaia_population_splits": part_splits,
            "quaia_4bin_z_tomography": part_b,
        },
        "part_c_robust_covariance_and_vlba": {
            "nside2_48patch_sandwich_jackknife": part_robust,
            "vlba_and_normal_frame_projection": part_c_vlba,
        },
        "claim_hygiene": {
            "physical_Pi": None,
            "physical_GF": None,
            "bianchi_family_identified": False,
            "cosmological_shear_or_vorticity_detection_claimed": False,
        },
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"group_id": "G03_RESEARCH", "runtime_sec": round(dt, 2), "max_rss_mb": round(rss_mb, 1)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
