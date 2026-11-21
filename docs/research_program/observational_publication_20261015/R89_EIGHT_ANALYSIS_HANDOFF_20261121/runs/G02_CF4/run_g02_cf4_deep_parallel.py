#!/usr/bin/env python3
"""R89 G02_CF4 Phase-3 deep multi-survey SN & mock analysis (create-only).

Analyzes DES-Dovekie 5YR SN (STAT+SYS inverted precision unpack -> full cov subset),
Pantheon+SH0ES under STAT+SYS, STATONLY, and all 14 systematic-grouping covariances,
63 SDSS HAMHOD mock realizations (sky-footprint cosmic-variance baseline), and
Measuring_bulkflows reference outputs, while preserving R87/R88 SQ-CF4 BLOCKED_INPUT.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import resource
import sys
import time
from pathlib import Path

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from scipy.linalg import cho_factor, cho_solve
from scipy.stats import chi2

ROOT = Path(__file__).resolve().parents[6]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from docs.research_program.observational_publication_20261015.H03_20261016.src.h03_tomography import (
    CENTERS,
    C_KM_S,
    STF,
    WIDTH,
    quadrupole_matrix,
)
from scripts.r68.fiveview_geometry import stf_shape
from scripts.r88.run_p0c import build_packet as r88_build_packet

OUT_DIR = Path(__file__).resolve().parent
OUT_JSON = OUT_DIR / "DEEP_MULTISURVEY_RESULT.json"

WORKDIR = Path("/mnt/extdrive/workdir")
DES_DIR = WORKDIR / "raw/observational_bundles/DES_SN5YR_Dovekie"
PP_DIR = WORKDIR / "raw/pantheonplus_release_c447f0f_20261110"
SDSS_MOCK_DIR = WORKDIR / "htt_open_data/sdss_source_null_20261018/analysis_selected"
DL_BF_DIR = Path("/home/cosmosapjw/Downloads/htt_r89_downloads/Measuring_bulkflows/Measuring_bulkflows-main")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def _icrs_unit(ra_deg: np.ndarray, dec_deg: np.ndarray) -> np.ndarray:
    ra = np.deg2rad(ra_deg)
    dec = np.deg2rad(dec_deg)
    cd = np.cos(dec)
    return np.column_stack([cd * np.cos(ra), cd * np.sin(ra), np.sin(dec)])


def _vec_to_gal_icrs(vec: np.ndarray) -> dict:
    norm = float(np.linalg.norm(vec))
    if norm <= 0.0 or not np.isfinite(norm):
        return {"amp": 0.0, "ra_deg": None, "dec_deg": None, "l_deg": None, "b_deg": None}
    uvec = vec / norm
    dec_deg = float(np.rad2deg(np.arcsin(np.clip(uvec[2], -1.0, 1.0))))
    ra_deg = float(np.rad2deg(np.arctan2(uvec[1], uvec[0])) % 360.0)
    sc = SkyCoord(ra=ra_deg * u.deg, dec=dec_deg * u.deg, frame="icrs").galactic
    return {
        "amp": norm,
        "ra_deg": ra_deg,
        "dec_deg": dec_deg,
        "l_deg": float(sc.l.deg),
        "b_deg": float(sc.b.deg),
    }


def _flat_lcdm_mu(z: np.ndarray, h0: float = 70.0, om0: float = 0.3) -> np.ndarray:
    z = np.asarray(z, dtype=np.float64)
    z_max = float(np.max(z)) * 1.05
    n_grid = 20000
    zg = np.linspace(0.0, z_max, n_grid)
    ez = np.sqrt(om0 * (1.0 + zg) ** 3 + (1.0 - om0))
    dz = zg[1] - zg[0]
    inv_ez = 1.0 / ez
    cum = np.zeros_like(zg)
    cum[1:] = np.cumsum(0.5 * (inv_ez[:-1] + inv_ez[1:]) * dz)
    chi = np.interp(z, zg, cum) * (C_KM_S / h0)
    dl_mpc = (1.0 + z) * chi
    return 5.0 * np.log10(dl_mpc) + 25.0


def _stf_basis(n: np.ndarray) -> np.ndarray:
    return np.einsum("ni,aij,nj->na", n, STF, n, optimize=True)


def _gls_fit(y: np.ndarray, X: np.ndarray, cov: np.ndarray, mode: str = "9p") -> dict:
    c_sym = 0.5 * (cov + cov.T)
    cf = cho_factor(c_sym, lower=True, check_finite=False)
    # Solve C^{-1} X and C^{-1} y via Cholesky
    cinv_X = cho_solve(cf, X, check_finite=False)
    cinv_y = cho_solve(cf, y, check_finite=False)
    F = X.T @ cinv_X
    F = 0.5 * (F + F.T)
    b = X.T @ cinv_y
    beta = np.linalg.solve(F, b)
    param_cov = np.linalg.inv(F)
    res = y - X @ beta
    cinv_res = cho_solve(cf, res, check_finite=False)
    chi2_val = float(res @ cinv_res)
    eig = np.linalg.eigvalsh(F)
    cond = float(eig.max() / max(eig.min(), 1e-30))

    dip = beta[1:4]
    c_dip = param_cov[1:4, 1:4]
    dip_wald = float(dip @ np.linalg.solve(c_dip, dip))
    out = {
        "n_obs": int(len(y)),
        "n_params": int(X.shape[1]),
        "F_condition": cond,
        "chi2_working": chi2_val,
        "dof": int(len(y) - X.shape[1]),
        "chi2_per_dof": float(chi2_val / max(len(y) - X.shape[1], 1)),
        "monopole_offset": float(beta[0]),
        "monopole_err": float(math.sqrt(max(param_cov[0, 0], 0.0))),
        "dipole_vec": dip.tolist(),
        "dipole_err_vec": np.sqrt(np.maximum(np.diag(c_dip), 0.0)).tolist(),
        "dipole_dir": _vec_to_gal_icrs(dip),
        "dipole_wald_chi2_nominal": dip_wald,
        "dipole_p_nominal": float(chi2.sf(dip_wald, 3)),
    }
    if mode == "9p" and X.shape[1] == 9:
        q = beta[4:9]
        c_q = param_cov[4:9, 4:9]
        q_wald = float(q @ np.linalg.solve(c_q, q))
        qmat = quadrupole_matrix(q)
        shape = stf_shape(qmat)
        out["quad_vec"] = q.tolist()
        out["quad_frobenius_norm"] = float(np.linalg.norm(q))
        out["quad_shape_chi"] = float(shape["signed_chi"])
        out["quad_wald_chi2_nominal"] = q_wald
        out["quad_p_nominal"] = float(chi2.sf(q_wald, 5))
    return out


def _analyze_des_dovekie() -> dict:
    hd_path = DES_DIR / "DES-Dovekie_HD.csv"
    meta_path = DES_DIR / "DES-Dovekie_Metadata.csv"
    npz_path = DES_DIR / "STAT+SYS.npz"

    hd_rows = []
    with hd_path.open("r", encoding="utf-8") as f:
        for ln in f:
            if ln.startswith("VARNAMES:"):
                hcols = ln.split()[1:]
            elif ln.startswith("SN:"):
                p = ln.split()[1:]
                hd_rows.append(
                    (
                        p[hcols.index("CID")],
                        int(p[hcols.index("IDSURVEY")]),
                        float(p[hcols.index("zHD")]),
                        float(p[hcols.index("MU")]),
                        float(p[hcols.index("MUERR")]),
                    )
                )

    meta_map = {}
    with meta_path.open("r", encoding="utf-8") as f:
        for ln in f:
            if ln.startswith("VARNAMES:"):
                mcols = ln.split()[1:]
            elif ln.startswith("SN:"):
                p = ln.split()[1:]
                cid = p[mcols.index("CID")]
                surv = int(p[mcols.index("IDSURVEY")])
                hra = float(p[mcols.index("HOST_RA")])
                hdec = float(p[mcols.index("HOST_DEC")])
                meta_map[(cid, surv)] = (hra, hdec)

    z_hd = np.array([r[2] for r in hd_rows], dtype=np.float64)
    mu = np.array([r[3] for r in hd_rows], dtype=np.float64)
    muerr = np.array([r[4] for r in hd_rows], dtype=np.float64)
    hra = np.array([meta_map[(r[0], r[1])][0] for r in hd_rows], dtype=np.float64)
    hdec = np.array([meta_map[(r[0], r[1])][1] for r in hd_rows], dtype=np.float64)

    with np.load(npz_path, allow_pickle=False) as d:
        n = int(d["nsn"][0])
        if n != len(hd_rows):
            raise ValueError(f"DES nsn mismatch: {n} vs {len(hd_rows)}")
        inv_cov = np.zeros((n, n), dtype=np.float64)
        inv_cov[np.triu_indices(n)] = np.asarray(d["cov"], dtype=np.float64)
        il = np.tril_indices(n, -1)
        inv_cov[il] = inv_cov.T[il]
    # Exact match to DES-Dovekie-SN_Likelihood.py: invert precision before subsetting
    c_full = np.linalg.inv(inv_cov)
    c_full = 0.5 * (c_full + c_full.T)

    valid_sky = np.isfinite(mu) & np.isfinite(z_hd) & (z_hd > 0.01) & (hra > -900.0) & (hdec > -900.0)
    lowz_sky = valid_sky & (z_hd < 0.15)
    highz_sky = valid_sky & (z_hd >= 0.15)

    dmu_all = mu - _flat_lcdm_mu(z_hd, h0=70.0, om0=0.3)
    n_icrs = _icrs_unit(np.where(valid_sky, hra, 0.0), np.where(valid_sky, hdec, 0.0))
    X9_all = np.column_stack([np.ones(n), n_icrs, _stf_basis(n_icrs)])
    X4_all = np.column_stack([np.ones(n), n_icrs])

    c_diag_full = np.diag(np.diag(c_full))
    results = {}
    for label, sel in [("valid_sky_all_z", valid_sky), ("valid_sky_z_lt_0p15", lowz_sky), ("valid_sky_z_ge_0p15", highz_sky)]:
        idx = np.flatnonzero(sel)
        if len(idx) < 20:
            continue
        c_sub = c_full[np.ix_(idx, idx)]
        results[f"{label}_9p_stat_sys"] = _gls_fit(dmu_all[idx], X9_all[idx], c_sub, mode="9p")
        results[f"{label}_4p_stat_sys"] = _gls_fit(dmu_all[idx], X4_all[idx], c_sub, mode="4p")
        if label == "valid_sky_all_z":
            results[f"{label}_9p_diag_only"] = _gls_fit(dmu_all[idx], X9_all[idx], c_diag_full[np.ix_(idx, idx)], mode="9p")

    return {
        "sources": {
            "hd_csv_sha256": _sha256(hd_path),
            "meta_csv_sha256": _sha256(meta_path),
            "stat_sys_npz_sha256": _sha256(npz_path),
        },
        "n_total": n,
        "n_valid_host_coords_z_gt_0p01": int(np.count_nonzero(valid_sky)),
        "n_lowz_lt_0p15": int(np.count_nonzero(lowz_sky)),
        "n_highz_ge_0p15": int(np.count_nonzero(highz_sky)),
        "sqrt_diag_cov_over_muerr_median": float(np.median(np.sqrt(np.diag(c_full)) / muerr)),
        "fits_mag": results,
    }


def _load_snana_cov(path: Path) -> np.ndarray:
    arr = np.fromfile(path, dtype=np.float64, sep=" ")
    n = int(round(arr[0]))
    if len(arr) != 1 + n * n:
        raise ValueError(f"Unexpected covariance size in {path}: {len(arr)} vs {1 + n*n}")
    mat = arr[1:].reshape((n, n))
    return 0.5 * (mat + mat.T)


def _analyze_pantheon_plus() -> dict:
    dat_path = PP_DIR / "Pantheon+SH0ES.dat"
    cov_tot_path = PP_DIR / "Pantheon+SH0ES_STAT+SYS.cov"
    cov_stat_path = PP_DIR / "Pantheon+SH0ES_STATONLY.cov"

    with dat_path.open("r", encoding="utf-8") as f:
        cols = f.readline().split()
        rows = [ln.split() for ln in f if ln.strip()]

    iz = cols.index("zHD")
    imu = cols.index("MU_SH0ES")
    ira = cols.index("RA")
    idec = cols.index("DEC")
    ical = cols.index("IS_CALIBRATOR")

    z_hd = np.array([float(r[iz]) for r in rows], dtype=np.float64)
    mu = np.array([float(r[imu]) for r in rows], dtype=np.float64)
    ra = np.array([float(r[ira]) for r in rows], dtype=np.float64)
    dec = np.array([float(r[idec]) for r in rows], dtype=np.float64)
    is_cal = np.array([int(r[ical]) for r in rows], dtype=np.int64)

    c_stat_sys = _load_snana_cov(cov_tot_path)
    c_statonly = _load_snana_cov(cov_stat_path)

    sel_all = np.isfinite(z_hd) & np.isfinite(mu) & (z_hd > 0.01) & (ra >= 0.0) & (ra <= 360.0) & (np.abs(dec) <= 90.0) & (is_cal == 0)
    sel_lowz = sel_all & (z_hd < 0.15)
    dmu = mu - _flat_lcdm_mu(z_hd, h0=70.0, om0=0.3)
    n_icrs = _icrs_unit(ra, dec)
    X9 = np.column_stack([np.ones(len(rows)), n_icrs, _stf_basis(n_icrs)])

    idx_all = np.flatnonzero(sel_all)
    idx_lowz = np.flatnonzero(sel_lowz)

    base_fits = {
        "all_sky_z_gt_0p01_stat_sys": _gls_fit(dmu[idx_all], X9[idx_all], c_stat_sys[np.ix_(idx_all, idx_all)], mode="9p"),
        "all_sky_z_gt_0p01_statonly": _gls_fit(dmu[idx_all], X9[idx_all], c_statonly[np.ix_(idx_all, idx_all)], mode="9p"),
        "lowz_0p01_0p15_stat_sys": _gls_fit(dmu[idx_lowz], X9[idx_lowz], c_stat_sys[np.ix_(idx_lowz, idx_lowz)], mode="9p"),
        "lowz_0p01_0p15_statonly": _gls_fit(dmu[idx_lowz], X9[idx_lowz], c_statonly[np.ix_(idx_lowz, idx_lowz)], mode="9p"),
    }

    grp_dir = PP_DIR / "sytematic_groupings"
    grp_results = {}
    ref_dip = np.array(base_fits["all_sky_z_gt_0p01_stat_sys"]["dipole_vec"], dtype=np.float64)
    for p in sorted(grp_dir.glob("Pantheon+SH0ES_122221_*.cov")):
        name = p.stem.replace("Pantheon+SH0ES_122221_", "")
        cg = _load_snana_cov(p)
        cg_sub = cg[np.ix_(idx_all, idx_all)]
        eigmin_raw = float(np.linalg.eigvalsh(cg_sub).min())
        if eigmin_raw > 1e-8:
            mode_used = "direct_pd_grouping_matrix"
            c_use = cg_sub
        else:
            mode_used = "added_to_statonly"
            c_use = c_statonly[np.ix_(idx_all, idx_all)] + cg_sub
        fit_g = _gls_fit(dmu[idx_all], X9[idx_all], c_use, mode="9p")
        dip_g = np.array(fit_g["dipole_vec"], dtype=np.float64)
        grp_results[name] = {
            "matrix_mode": mode_used,
            "raw_eigmin": eigmin_raw,
            "dipole_amp_mag": fit_g["dipole_dir"]["amp"],
            "dipole_l_deg": fit_g["dipole_dir"]["l_deg"],
            "dipole_b_deg": fit_g["dipole_dir"]["b_deg"],
            "delta_dipole_vs_full_stat_sys_mag": float(np.linalg.norm(dip_g - ref_dip)),
            "quad_frobenius_norm_mag": fit_g["quad_frobenius_norm"],
            "chi2_working": fit_g["chi2_working"],
            "dipole_wald_chi2_nominal": fit_g["dipole_wald_chi2_nominal"],
            "quad_wald_chi2_nominal": fit_g["quad_wald_chi2_nominal"],
        }

    return {
        "sources": {
            "dat_sha256": _sha256(dat_path),
            "stat_sys_cov_sha256": _sha256(cov_tot_path),
            "statonly_cov_sha256": _sha256(cov_stat_path),
        },
        "n_total": len(rows),
        "n_all_sky_z_gt_0p01_noncal": int(len(idx_all)),
        "n_lowz_0p01_0p15_noncal": int(len(idx_lowz)),
        "base_fits_mag": base_fits,
        "systematic_grouping_ablations": grp_results,
    }


def _fit_weighted_9p(X: np.ndarray, y: np.ndarray, w: np.ndarray) -> dict | None:
    if len(y) < 15:
        return None
    s = np.sqrt(w)
    Xw = s[:, None] * X
    yw = s * y
    F = Xw.T @ Xw
    eig = np.linalg.eigvalsh(F)
    if eig.min() <= 0:
        return None
    cond = float(eig.max() / eig.min())
    if not np.isfinite(cond) or cond > 1e10:
        return None
    beta = np.linalg.solve(F, Xw.T @ yw)
    res = y - X @ beta
    cov = np.linalg.inv(F)
    dip = beta[1:4]
    c_dip = cov[1:4, 1:4]
    return {
        "beta": beta,
        "cov": cov,
        "dip_amp": float(np.linalg.norm(dip)),
        "dip_vec": dip,
        "dip_wald_diag_noise": float(dip @ np.linalg.solve(c_dip, dip)),
        "quad_norm": float(np.linalg.norm(beta[4:9])),
        "chi2_diag": float(np.sum(w * res * res)),
        "cond": cond,
    }


def _analyze_sdss_63_mocks() -> dict:
    mock_paths = sorted(SDSS_MOCK_DIR.glob("MOCK_HAMHOD_SDSS_v5_R19*.0_err_corr"))
    ln10 = math.log(10.0)
    full_obs_vecs = []
    full_true_vecs = []
    full_obs_quad = []
    full_true_quad = []
    full_obs_wald = []
    shell_amps = {c: [] for c in CENTERS}
    n_rows_list = []

    for mp in mock_paths:
        data = np.genfromtxt(mp, delimiter=",", names=True, usecols=("RA", "Dec", "z_obs", "logdist_true", "logdist", "logdist_err"))
        n_rows_list.append(int(len(data)))
        ra = data["RA"]
        dec = data["Dec"]
        z_obs = data["z_obs"]
        eta_obs = data["logdist"]
        eta_true = data["logdist_true"]
        e_eta = data["logdist_err"]
        ok = np.isfinite(ra) & np.isfinite(dec) & np.isfinite(z_obs) & np.isfinite(eta_obs) & np.isfinite(eta_true) & np.isfinite(e_eta) & (z_obs > 0.01) & (e_eta > 0.0)
        ra, dec, z_obs, eta_obs, eta_true, e_eta = ra[ok], dec[ok], z_obs[ok], eta_obs[ok], eta_true[ok], e_eta[ok]

        d_est = (C_KM_S * z_obs) / 70.0
        v_obs = C_KM_S * z_obs * ln10 * eta_obs
        v_true = C_KM_S * z_obs * ln10 * eta_true
        sig_v = np.hypot(250.0, C_KM_S * z_obs * ln10 * e_eta)
        w = 1.0 / (sig_v * sig_v)
        nvec = _icrs_unit(ra, dec)
        X = np.column_stack([d_est, d_est[:, None] * nvec, d_est[:, None] * _stf_basis(nvec)])

        fo = _fit_weighted_9p(X, v_obs, w)
        ft = _fit_weighted_9p(X, v_true, w)
        if fo is None or ft is None:
            continue
        full_obs_vecs.append(fo["dip_vec"])
        full_true_vecs.append(ft["dip_vec"])
        full_obs_quad.append(fo["quad_norm"])
        full_true_quad.append(ft["quad_norm"])
        full_obs_wald.append(fo["dip_wald_diag_noise"])

        for c in CENTERS:
            wc = w * np.exp(-0.5 * ((z_obs - c) / WIDTH) ** 2)
            active = wc > (1e-6 * np.max(wc))
            fs = _fit_weighted_9p(X[active], v_obs[active], wc[active])
            if fs is not None:
                shell_amps[c].append(fs["dip_amp"])

    obs_arr = np.array(full_obs_vecs, dtype=np.float64)
    true_arr = np.array(full_true_vecs, dtype=np.float64)
    obs_amp = np.linalg.norm(obs_arr, axis=1)
    true_amp = np.linalg.norm(true_arr, axis=1)
    diff_arr = obs_arr - true_arr
    cos_align = np.sum(obs_arr * true_arr, axis=1) / (obs_amp * true_amp)

    shell_summary = {}
    for c in CENTERS:
        arr = np.array(shell_amps[c], dtype=np.float64)
        shell_summary[f"z_{c:.3f}"] = {
            "n_valid_mocks": int(len(arr)),
            "median_dipole_km_s_per_mpc": float(np.median(arr)) if len(arr) else None,
            "mean_dipole_km_s_per_mpc": float(np.mean(arr)) if len(arr) else None,
            "std_dipole_km_s_per_mpc": float(np.std(arr)) if len(arr) else None,
            "p05_p95": [float(np.percentile(arr, 5)), float(np.percentile(arr, 95))] if len(arr) else None,
        }

    return {
        "n_mock_files": len(mock_paths),
        "n_fitted_mocks": len(obs_arr),
        "mean_rows_per_mock": float(np.mean(n_rows_list)) if n_rows_list else 0.0,
        "first_mock_sha256": _sha256(mock_paths[0]) if mock_paths else None,
        "apparent_expansion_dipole_km_s_per_mpc": {
            "obs_mean_vec": obs_arr.mean(axis=0).tolist(),
            "obs_std_vec": obs_arr.std(axis=0).tolist(),
            "obs_amp_mean": float(obs_amp.mean()),
            "obs_amp_median": float(np.median(obs_amp)),
            "obs_amp_p05_p95": [float(np.percentile(obs_amp, 5)), float(np.percentile(obs_amp, 95))],
            "true_amp_mean": float(true_amp.mean()),
            "obs_minus_true_rms_per_axis": np.sqrt(np.mean(diff_arr * diff_arr, axis=0)).tolist(),
            "obs_true_cosine_median": float(np.median(cos_align)),
            "obs_quad_norm_median": float(np.median(full_obs_quad)),
            "true_quad_norm_median": float(np.median(full_true_quad)),
            "nominal_diag_wald_chi2_median": float(np.median(full_obs_wald)),
            "nominal_diag_wald_chi2_p95": float(np.percentile(full_obs_wald, 95)),
        },
        "z_shell_summary": shell_summary,
        "note": "SDSS HAMHOD mock cosmic-variance ensemble on SDSS footprint only; NOT a matched CF4 empirical selection/method covariance.",
    }


def _parse_measuring_bulkflows_refs() -> dict:
    files = {
        "BF_MVE_result.txt": DL_BF_DIR / "BF_MVE_result.txt",
        "BF_MLE_result.txt": DL_BF_DIR / "BF_MLE_result.txt",
        "BF_MVE_cov.txt": DL_BF_DIR / "BF_MVE_cov.txt",
        "BF_MLE_cov.txt": DL_BF_DIR / "BF_MLE_cov.txt",
        "MVE_result_peery_MLE_result_nusser.txt": DL_BF_DIR / "MVE_result_peery_MLE_result_nusser.txt",
        "powerspectrum.csv": DL_BF_DIR / "powerspectrum.csv",
    }
    hashes = {k: _sha256(p) for k, p in files.items() if p.exists()}

    def read_vec_err(p: Path):
        lines = [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
        vec = [float(x) for x in lines[0].split()]
        err = [float(x) for x in lines[1].split()]
        return {"vec_kms": vec, "err_kms": err, "amp_kms": float(np.linalg.norm(vec))}

    mve = read_vec_err(files["BF_MVE_result.txt"]) if files["BF_MVE_result.txt"].exists() else None
    mle = read_vec_err(files["BF_MLE_result.txt"]) if files["BF_MLE_result.txt"].exists() else None
    cov_mve = np.loadtxt(files["BF_MVE_cov.txt"]) if files["BF_MVE_cov.txt"].exists() else None
    cov_mle = np.loadtxt(files["BF_MLE_cov.txt"]) if files["BF_MLE_cov.txt"].exists() else None
    out = {
        "file_sha256": hashes,
        "BF_MVE": mve,
        "BF_MLE": mle,
        "MVE_cov_diag_sqrt": np.sqrt(np.diag(cov_mve)).tolist() if cov_mve is not None else None,
        "MLE_cov_diag_sqrt": np.sqrt(np.diag(cov_mle)).tolist() if cov_mle is not None else None,
    }
    return out


def main() -> int:
    if OUT_JSON.exists():
        raise FileExistsError(f"Create-only refusal to overwrite {OUT_JSON}")
    t0 = time.perf_counter()

    r88_pkt = r88_build_packet("SQ-CF4")
    des_res = _analyze_des_dovekie()
    pp_res = _analyze_pantheon_plus()
    sdss_res = _analyze_sdss_63_mocks()
    dl_res = _parse_measuring_bulkflows_refs()

    dt = time.perf_counter() - t0
    rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    payload = {
        "artifact_id": "R89_G02_CF4_DEEP_MULTISURVEY_V1",
        "group_id": "G02_CF4",
        "create_only": True,
        "runtime_sec": round(dt, 3),
        "max_rss_mb": round(rss_mb, 2),
        "platform": platform.platform(),
        "env": {
            "OMP_NUM_THREADS": os.environ.get("OMP_NUM_THREADS"),
            "OPENBLAS_NUM_THREADS": os.environ.get("OPENBLAS_NUM_THREADS"),
        },
        "sq_cf4_status": r88_pkt["status"],
        "r88_p0c_packet_sha_status": {
            "node_id": r88_pkt["node_id"],
            "status": r88_pkt["status"],
            "reason": r88_pkt.get("reason"),
        },
        "des_dovekie_5yr": des_res,
        "pantheon_plus_shoes": pp_res,
        "sdss_hamhod_63_mocks": sdss_res,
        "measuring_bulkflows_ref": dl_res,
        "claim_hygiene": {
            "physical_Pi": None,
            "physical_GF": None,
            "cf4_raw_cal_posterior_absent": True,
            "bianchi_family_identified": False,
            "statement": (
                "Working-frame Hubble-diagram multipole & SDSS-mock cosmic-variance diagnostics only; "
                "DES/Pantheon+ SN systematic ablations and SDSS mocks do not supply CF4-matched "
                "physical S_PV, J_cal Sigma_cal J_cal^T, selection covariance, or upstream-independent CF4 heldout."
            ),
        },
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_JSON} in {dt:.2f}s (max RSS {rss_mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
