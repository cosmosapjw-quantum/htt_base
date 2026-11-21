#!/usr/bin/env python3
"""R89 G02_CF4 Solver-Free Research Completion (create-only).

Covers Section 3 (A/B/C):
A. CF4 35,970 groups + CF4++ HMC velocity grid subtraction & variance propagation,
   plus sharp L1/corner partial-identification bounds under bounded uncalibrated
   inter-method zero-point nuisance across the 4 depth windows.
B. DES-Dovekie whitened SVD rank/nullspace & reduced well-conditioned sky estimand,
   plus Pantheon+ redshift-shell and N/S Galactic hemisphere GLS stability.
C. Independent DESI EDR Fuji FP (4,191 galaxies) 4p/9p/SVD analysis + 63 SDSS
   HAMHOD mocks empirical 3x3 dipole covariance and bias/noise decomposition.
"""
from __future__ import annotations

import hashlib
import itertools
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
from scipy.linalg import cho_factor, cho_solve, solve_triangular
from scipy.ndimage import map_coordinates
from scipy.stats import chi2

ROOT = Path(__file__).resolve().parents[6]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from docs.research_program.observational_publication_20261015.H03_20261016.src.h03_tomography import (
    CENTERS,
    C_KM_S,
    METHODS,
    WIDTH,
    fit as h03_fit,
    proxy_distance,
    stf_features,
    velocity_design,
    window as h03_window,
    working_sigma,
)
from htt.obsstat import p2p3_fast
from scripts.r88.run_p0c import build_packet as r88_build_packet

OUT_DIR = Path(__file__).resolve().parent
OUT_JSON = OUT_DIR / "SOLVER_FREE_RESEARCH_RESULT.json"

WORKDIR = Path("/mnt/extdrive/workdir")
CF4_SEL = ROOT / "docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz"
CF4PP_NPZ = WORKDIR / "htt_open_data/cf4/d06_flow_20261018/new_CF4pp_mean_std_grids.npz"
DES_DIR = WORKDIR / "raw/observational_bundles/DES_SN5YR_Dovekie"
PP_DIR = WORKDIR / "raw/pantheonplus_release_c447f0f_20261110"
DESI_FP = WORKDIR / "raw/new_acquisitions/optical/DESI_PV_Fuji_FP/DESI_FP_logdists_fiducial.csv"
SDSS_MOCK_DIR = WORKDIR / "htt_open_data/sdss_source_null_20261018/analysis_selected"


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


def _vec_to_gal(vec: np.ndarray) -> dict:
    norm = float(np.linalg.norm(vec))
    if norm <= 0.0:
        return {"amp": 0.0, "l_deg": None, "b_deg": None}
    u_v = vec / norm
    dec_d = math.degrees(math.asin(max(-1.0, min(1.0, float(u_v[2])))))
    ra_d = math.degrees(math.atan2(float(u_v[1]), float(u_v[0]))) % 360.0
    sc = SkyCoord(ra=ra_d * u.deg, dec=dec_d * u.deg, frame="icrs").galactic
    return {"amp": norm, "l_deg": float(sc.l.deg), "b_deg": float(sc.b.deg)}


def _flat_lcdm_mu(z: np.ndarray, h0: float = 70.0, om0: float = 0.3) -> np.ndarray:
    z = np.asarray(z, dtype=np.float64)
    z_max = float(np.max(z)) * 1.05
    zg = np.linspace(0.0, z_max, 20000)
    inv_ez = 1.0 / np.sqrt(om0 * (1.0 + zg) ** 3 + (1.0 - om0))
    cum = np.zeros_like(zg)
    cum[1:] = np.cumsum(0.5 * (inv_ez[:-1] + inv_ez[1:]) * (zg[1] - zg[0]))
    dl = (1.0 + z) * np.interp(z, zg, cum) * (C_KM_S / h0)
    return 5.0 * np.log10(dl) + 25.0


def _part_a_cf4_flow_and_partial_id() -> dict:
    with np.load(CF4_SEL, allow_pickle=False) as zf:
        z = np.asarray(zf["z_CMB"], dtype=np.float64)
        mu = np.asarray(zf["dmzp"], dtype=np.float64)
        e_mu = np.asarray(zf["e_dmzp"], dtype=np.float64)
        n = np.asarray(zf["n_J2000"], dtype=np.float64)
        method = np.asarray(zf["method_family"])

    d_mpc = proxy_distance(mu)
    sig_work = working_sigma(d_mpc, e_mu)
    X = velocity_design(d_mpc, n)
    y_raw = C_KM_S * z

    weights = np.column_stack([h03_window(z, sig_work, c, bandwidth=WIDTH) for c in CENTERS])
    raw_res = p2p3_fast.four_window_working_gls(X, y_raw, weights, sig_work, native_lib="auto", threads=int(os.environ.get("OMP_NUM_THREADS", "4")))

    # Map CF4 positions to Supergalactic Cartesian (Mpc/h) per retrieve_CF4pp_grid_values.py
    r_mpch = (C_KM_S * z) / 100.0
    sc_sg = SkyCoord(
        x=n[:, 0] * r_mpch * u.Mpc,
        y=n[:, 1] * r_mpch * u.Mpc,
        z=n[:, 2] * r_mpch * u.Mpc,
        representation_type="cartesian",
        frame="icrs",
    ).supergalactic
    sgx = sc_sg.cartesian.x.value
    sgy = sc_sg.cartesian.y.value
    sgz = sc_sg.cartesian.z.value

    delta = 1000.0 / 128.0
    fx = np.clip((sgx + 500.0) / delta - 0.5, 0.0, 127.0)
    fy = np.clip((sgy + 500.0) / delta - 0.5, 0.0, 127.0)
    fz = np.clip((sgz + 500.0) / delta - 0.5, 0.0, 127.0)
    with np.load(CF4PP_NPZ, allow_pickle=False) as g:
        vr_mean_key = "vr_mean" if "vr_mean" in g.files else "vr_mean_CF4pp"
        vr_std_key = "vr_std" if "vr_std" in g.files else "vr_std_CF4pp"
        vr_mean_grid = np.asarray(g[vr_mean_key], dtype=np.float64)
        vr_std_grid = np.asarray(g[vr_std_key], dtype=np.float64)
    vr_trilin = map_coordinates(vr_mean_grid, [fx, fy, fz], order=1, mode="nearest")
    vr_std = map_coordinates(vr_std_grid, [fx, fy, fz], order=1, mode="nearest")

    # Flow-subtracted conditional apparent velocity: cz_cosmo_cond = cz_CMB - vr_CF4pp
    y_flow = y_raw - vr_trilin
    sig_flow = np.hypot(sig_work, vr_std)
    w_flow = np.column_stack([h03_window(z, sig_flow, c, bandwidth=WIDTH) for c in CENTERS])
    flow_res = p2p3_fast.four_window_working_gls(X, y_flow, w_flow, sig_flow, native_lib="auto", threads=int(os.environ.get("OMP_NUM_THREADS", "4")))

    # Sharp partial-identification bounds under bounded uncalibrated inter-method zero-point nuisance
    # Distance shift d_i -> d_i * 10^(delta_mu_m / 5): linearize fixed-weight influence A_w on residual delta_X * theta
    ln10_over_5 = math.log(10.0) / 5.0
    meth_masks = {m: (method == m) for m in METHODS}
    partial_id = {}
    max_fd_err = 0.0
    for wi, c in enumerate(CENTERS):
        fit_w = h03_fit(X, y_raw, weights[:, wi], influence=True)
        A_w = fit_w["A"]  # (9, N)
        theta_w = fit_w["theta"]
        yhat_w = X @ theta_w  # equals d_i * (X_row / d_i . theta_w)
        # Sensitivity G[alpha, m] = d(theta_alpha) / d(delta_mu_m) at fixed weights
        G = np.zeros((9, len(METHODS)), dtype=np.float64)
        for mi, mname in enumerate(METHODS):
            mm = meth_masks[mname]
            # Exact fixed-weight WLS total derivative wrt delta_mu_m:
            # d(theta)/d(eps) = F_w^{-1} (dX^T W r_w) - A_w (dX theta_w) = A_w @ ((y_raw - 2*yhat_w) * dX/X)
            G[:, mi] = A_w[:, mm] @ ((y_raw[mm] - 2.0 * yhat_w[mm]) * ln10_over_5)

        # Verify against direct nonlinear central finite difference (h = 1e-5 mag on SN) at fixed weights
        h_fd = 1e-5
        d_plus = proxy_distance(mu + np.where(meth_masks["SN"], h_fd, 0.0))
        d_minus = proxy_distance(mu - np.where(meth_masks["SN"], h_fd, 0.0))
        th_plus = h03_fit(velocity_design(d_plus, n), y_raw, weights[:, wi], influence=False)["theta"]
        th_minus = h03_fit(velocity_design(d_minus, n), y_raw, weights[:, wi], influence=False)["theta"]
        fd_slope = (th_plus - th_minus) / (2.0 * h_fd)
        rel_fd_diff = float(np.max(np.abs(fd_slope - G[:, METHODS.index("SN")])))
        max_fd_err = max(max_fd_err, rel_fd_diff)

        bounds_by_delta = {}
        corners_sign = np.array(list(itertools.product([-1.0, 1.0], repeat=len(METHODS))), dtype=np.float64)
        for d0 in (0.02, 0.05):
            # Exact sharp componentwise L1 intervals: theta_a +- d0 * sum_m |G[a, m]|
            l1_half = d0 * np.sum(np.abs(G), axis=1)
            # 16 extreme corners in [-d0, d0]^4 for dipole & quad norms
            dip_vecs = theta_w[1:4][None, :] + d0 * (corners_sign @ G[1:4, :].T)
            dip_norms = np.linalg.norm(dip_vecs, axis=1)
            quad_vecs = theta_w[4:9][None, :] + d0 * (corners_sign @ G[4:9, :].T)
            quad_norms = np.linalg.norm(quad_vecs, axis=1)
            bounds_by_delta[f"delta_mu_{d0:.2f}_mag"] = {
                "H_shift_interval": [float(theta_w[0] - l1_half[0]), float(theta_w[0] + l1_half[0])],
                "dipole_l1_box_components": [[float(theta_w[j] - l1_half[j]), float(theta_w[j] + l1_half[j])] for j in range(1, 4)],
                "dipole_norm_corner_min_max_km_s_per_mpc": [float(dip_norms.min()), float(dip_norms.max())],
                "quad_norm_corner_min_max_km_s_per_mpc": [float(quad_norms.min()), float(quad_norms.max())],
            }

        partial_id[f"z_{c:.3f}"] = {
            "theta_raw_9p": theta_w.tolist(),
            "theta_flow_corr_9p": flow_res["theta"][wi].tolist(),
            "dipole_raw": _vec_to_gal(theta_w[1:4]),
            "dipole_flow_corr": _vec_to_gal(flow_res["theta"][wi, 1:4]),
            "quad_norm_raw": float(np.linalg.norm(theta_w[4:9])),
            "quad_norm_flow_corr": float(np.linalg.norm(flow_res["theta"][wi, 4:9])),
            "sensitivity_G_9x4_per_mag": G.tolist(),
            "zero_point_bounds": bounds_by_delta,
        }

    return {
        "epistemic_status": "conditional",
        "sources": {
            "selected_cf4_sha256": _sha256(CF4_SEL),
            "cf4pp_grid_sha256": _sha256(CF4PP_NPZ),
        },
        "n_groups": int(len(z)),
        "cf4pp_vr_trilinear_stats_km_s": {
            "mean": float(np.mean(vr_trilin)),
            "std": float(np.std(vr_trilin)),
            "median_vr_std_uncert": float(np.median(vr_std)),
        },
        "fixed_weight_G_vs_nonlinear_SN_fd_max_diff": max_fd_err,
        "windows": partial_id,
        "joint_36d_raw_vs_flow": {
            "raw_theta_4x9": raw_res["theta"].tolist(),
            "flow_theta_4x9": flow_res["theta"].tolist(),
            "raw_receipt": p2p3_fast.last_p2p3_receipt(),
        },
        "blocked_physical_terms": ["S_PV", "J_cal Sigma_cal J_cal^T", "C_selection", "upstream_independent_CF4_heldout"],
    }


def _gls_fit(y: np.ndarray, X: np.ndarray, cov: np.ndarray) -> dict:
    c_sym = 0.5 * (cov + cov.T)
    cf = cho_factor(c_sym, lower=True, check_finite=False)
    cinv_X = cho_solve(cf, X, check_finite=False)
    cinv_y = cho_solve(cf, y, check_finite=False)
    F = 0.5 * (X.T @ cinv_X + (X.T @ cinv_X).T)
    beta = np.linalg.solve(F, X.T @ cinv_y)
    pcov = np.linalg.inv(F)
    res = y - X @ beta
    chi2_val = float(res @ cho_solve(cf, res, check_finite=False))
    eig = np.linalg.eigvalsh(F)
    dip = beta[1:4]
    c_dip = pcov[1:4, 1:4]
    w_dip = float(dip @ np.linalg.solve(c_dip, dip))
    out = {
        "n_obs": int(len(y)),
        "n_params": int(X.shape[1]),
        "F_condition": float(eig.max() / max(eig.min(), 1e-30)),
        "chi2_working": chi2_val,
        "chi2_per_dof": float(chi2_val / max(len(y) - X.shape[1], 1)),
        "monopole_offset": float(beta[0]),
        "dipole_dir": _vec_to_gal(dip),
        "dipole_wald_nominal": w_dip,
        "dipole_p_nominal": float(chi2.sf(w_dip, 3)),
    }
    if X.shape[1] == 9:
        q = beta[4:9]
        w_q = float(q @ np.linalg.solve(pcov[4:9, 4:9], q))
        out["quad_norm"] = float(np.linalg.norm(q))
        out["quad_wald_nominal"] = w_q
        out["quad_p_nominal"] = float(chi2.sf(w_q, 5))
    return out


def _part_b_des_svd_and_pantheon_splits() -> dict:
    # --- DES whitened SVD & reduced estimand ---
    hd_rows = []
    with (DES_DIR / "DES-Dovekie_HD.csv").open("r", encoding="utf-8") as f:
        for ln in f:
            if ln.startswith("VARNAMES:"):
                hcols = ln.split()[1:]
            elif ln.startswith("SN:"):
                p = ln.split()[1:]
                hd_rows.append((p[hcols.index("CID")], int(p[hcols.index("IDSURVEY")]), float(p[hcols.index("zHD")]), float(p[hcols.index("MU")])))
    meta_map = {}
    with (DES_DIR / "DES-Dovekie_Metadata.csv").open("r", encoding="utf-8") as f:
        for ln in f:
            if ln.startswith("VARNAMES:"):
                mcols = ln.split()[1:]
            elif ln.startswith("SN:"):
                p = ln.split()[1:]
                meta_map[(p[mcols.index("CID")], int(p[mcols.index("IDSURVEY")]))] = (float(p[mcols.index("HOST_RA")]), float(p[mcols.index("HOST_DEC")]))

    z_hd = np.array([r[2] for r in hd_rows], dtype=np.float64)
    mu = np.array([r[3] for r in hd_rows], dtype=np.float64)
    hra = np.array([meta_map[(r[0], r[1])][0] for r in hd_rows], dtype=np.float64)
    hdec = np.array([meta_map[(r[0], r[1])][1] for r in hd_rows], dtype=np.float64)
    with np.load(DES_DIR / "STAT+SYS.npz", allow_pickle=False) as d:
        n = int(d["nsn"][0])
        inv_cov = np.zeros((n, n), dtype=np.float64)
        inv_cov[np.triu_indices(n)] = np.asarray(d["cov"], dtype=np.float64)
        il = np.tril_indices(n, -1)
        inv_cov[il] = inv_cov.T[il]
    c_full = 0.5 * (np.linalg.inv(inv_cov) + np.linalg.inv(inv_cov).T)
    sel = np.isfinite(mu) & np.isfinite(z_hd) & (z_hd > 0.01) & (hra > -900.0) & (hdec > -900.0)
    idx = np.flatnonzero(sel)
    c_sub = 0.5 * (c_full[np.ix_(idx, idx)] + c_full[np.ix_(idx, idx)].T)
    y_des = (mu - _flat_lcdm_mu(z_hd))[idx]
    n_des = _icrs_unit(hra[idx], hdec[idx])
    X9_des = np.column_stack([np.ones(len(idx)), n_des, stf_features(n_des)])

    L_des = np.linalg.cholesky(c_sub)
    wy = solve_triangular(L_des, y_des, lower=True)
    WX9 = solve_triangular(L_des, X9_des, lower=True)
    U, svals, Vt = np.linalg.svd(WX9, full_matrices=False)
    # Orthogonal principal mode amplitudes u_k^T (L^{-1} y) / sigma_k with exact std error 1/sigma_k
    z_scores = (U.T @ wy)
    mode_estimates = z_scores / svals
    mode_errs = 1.0 / svals

    reduced_truncations = {}
    for k in (1, 2, 3, 4, 6, 9):
        # Minimum-norm truncated-SVD 9p representative + reduced chi2 on retained k-subspace
        V_k = Vt[:k, :]
        beta_k = V_k.T @ (z_scores[:k] / svals[:k])
        cov_k = V_k.T @ np.diag(1.0 / (svals[:k] ** 2)) @ V_k
        res_k = wy - WX9 @ beta_k
        reduced_truncations[f"rank_{k}"] = {
            "k": k,
            "retained_cond_F": float((svals[0] / svals[k - 1]) ** 2),
            "chi2_working": float(res_k @ res_k),
            "subspace_wald_chi2": float(np.sum(z_scores[:k] ** 2)),
            "subspace_p_nominal": float(chi2.sf(float(np.sum(z_scores[:k] ** 2)), k)),
            "min_norm_dipole_amp_mag": float(np.linalg.norm(beta_k[1:4])),
            "min_norm_dipole_std_rms": float(np.sqrt(np.mean(np.diag(cov_k[1:4, 1:4])))),
        }

    # --- Pantheon+ redshift-shell and N/S hemisphere stability ---
    with (PP_DIR / "Pantheon+SH0ES.dat").open("r", encoding="utf-8") as f:
        cols = f.readline().split()
        rows = [ln.split() for ln in f if ln.strip()]
    iz, imu, ira, idec, ical = cols.index("zHD"), cols.index("MU_SH0ES"), cols.index("RA"), cols.index("DEC"), cols.index("IS_CALIBRATOR")
    z_pp = np.array([float(r[iz]) for r in rows])
    mu_pp = np.array([float(r[imu]) for r in rows])
    ra_pp = np.array([float(r[ira]) for r in rows])
    dec_pp = np.array([float(r[idec]) for r in rows])
    cal_pp = np.array([int(r[ical]) for r in rows])
    arr_tot = np.fromfile(PP_DIR / "Pantheon+SH0ES_STAT+SYS.cov", dtype=np.float64, sep=" ")
    n_pp = int(round(arr_tot[0]))
    c_pp_tot = arr_tot[1:].reshape((n_pp, n_pp))
    arr_st = np.fromfile(PP_DIR / "Pantheon+SH0ES_STATONLY.cov", dtype=np.float64, sep=" ")
    c_pp_st = arr_st[1:].reshape((n_pp, n_pp))

    base_pp = np.isfinite(z_pp) & np.isfinite(mu_pp) & (z_pp > 0.01) & (ra_pp >= 0) & (ra_pp <= 360) & (np.abs(dec_pp) <= 90) & (cal_pp == 0)
    dmu_pp = mu_pp - _flat_lcdm_mu(z_pp)
    n_pp_u = _icrs_unit(ra_pp, dec_pp)
    X9_pp = np.column_stack([np.ones(len(rows)), n_pp_u, stf_features(n_pp_u)])
    X4_pp = X9_pp[:, :4]
    sc_pp = SkyCoord(ra=ra_pp * u.deg, dec=dec_pp * u.deg, frame="icrs").galactic
    gal_b_pp = sc_pp.b.deg

    pp_splits = {}
    shells = [
        ("z_0p01_0p05", base_pp & (z_pp < 0.05)),
        ("z_0p05_0p15", base_pp & (z_pp >= 0.05) & (z_pp < 0.15)),
        ("z_0p15_0p40", base_pp & (z_pp >= 0.15) & (z_pp < 0.40)),
        ("z_ge_0p40", base_pp & (z_pp >= 0.40)),
        ("gal_north_b_gt_0", base_pp & (gal_b_pp > 0.0)),
        ("gal_south_b_lt_0", base_pp & (gal_b_pp < 0.0)),
    ]
    for sname, m in shells:
        ix = np.flatnonzero(m)
        pp_splits[sname] = {
            "4p_stat_sys": _gls_fit(dmu_pp[ix], X4_pp[ix], c_pp_tot[np.ix_(ix, ix)]),
            "9p_stat_sys": _gls_fit(dmu_pp[ix], X9_pp[ix], c_pp_tot[np.ix_(ix, ix)]),
            "4p_statonly": _gls_fit(dmu_pp[ix], X4_pp[ix], c_pp_st[np.ix_(ix, ix)]),
        }

    return {
        "epistemic_status": "conditional",
        "des_dovekie_whitened_svd": {
            "n_obs": int(len(idx)),
            "singular_values_9": svals.tolist(),
            "mode_amplitudes": mode_estimates.tolist(),
            "mode_std_errors": mode_errs.tolist(),
            "mode_z_scores": z_scores.tolist(),
            "near_null_right_singular_vectors_v7_to_v9": Vt[6:, :].tolist(),
            "reduced_rank_estimands": reduced_truncations,
        },
        "pantheon_plus_stability": pp_splits,
    }


def _part_c_desi_fp_and_sdss_cov() -> dict:
    # 1. DESI EDR Fuji FP 4,191 galaxies
    ra_l, dec_l, z_l, eta_l, err_l = [], [], [], [], []
    with DESI_FP.open("r", encoding="utf-8") as f:
        hdr = f.readline().lstrip("#").strip().split(",")
        ira, idec, iz, ieta, ierr = hdr.index("ra_1"), hdr.index("dec_1"), hdr.index("zcmb"), hdr.index("logdist"), hdr.index("logdist_err")
        for ln in f:
            p = ln.strip().split(",")
            if len(p) <= max(ira, idec, iz, ieta, ierr):
                continue
            try:
                ra_v, dec_v, zv, ev, erv = float(p[ira]), float(p[idec]), float(p[iz]), float(p[ieta]), float(p[ierr])
            except ValueError:
                continue
            if zv > 0.01 and erv > 0.0 and math.isfinite(ra_v) and math.isfinite(dec_v) and math.isfinite(ev):
                ra_l.append(ra_v); dec_l.append(dec_v); z_l.append(zv); eta_l.append(ev); err_l.append(erv)

    ra = np.array(ra_l); dec = np.array(dec_l); zc = np.array(z_l); eta = np.array(eta_l); e_eta = np.array(err_l)
    ln10 = math.log(10.0)
    d_est = (C_KM_S * zc) / 70.0
    v_app = C_KM_S * zc * ln10 * eta
    sig_v = np.hypot(250.0, C_KM_S * zc * ln10 * e_eta)
    n_u = _icrs_unit(ra, dec)
    X9 = np.column_stack([d_est, d_est[:, None] * n_u, d_est[:, None] * stf_features(n_u)])
    X4 = X9[:, :4]
    c_diag = np.diag(sig_v * sig_v)

    w = 1.0 / (sig_v * sig_v)
    s = np.sqrt(w)
    svals_9 = np.linalg.svd(s[:, None] * X9, compute_uv=False)
    svals_4 = np.linalg.svd(s[:, None] * X4, compute_uv=False)
    fit4 = _gls_fit(v_app, X4, c_diag)
    fit9 = _gls_fit(v_app, X9, c_diag)

    # 2. 63 SDSS HAMHOD mocks empirical 3x3 dipole covariance & bias decomposition
    mocks = sorted(SDSS_MOCK_DIR.glob("MOCK_HAMHOD_SDSS_v5_R19*.0_err_corr"))
    obs_vecs, true_vecs, formal_covs = [], [], []
    for mp in mocks:
        dat = np.genfromtxt(mp, delimiter=",", names=True, usecols=("RA", "Dec", "z_obs", "logdist_true", "logdist", "logdist_err"))
        ok = np.isfinite(dat["RA"]) & np.isfinite(dat["Dec"]) & (dat["z_obs"] > 0.01) & (dat["logdist_err"] > 0.0)
        d_m = (C_KM_S * dat["z_obs"][ok]) / 70.0
        n_m = _icrs_unit(dat["RA"][ok], dat["Dec"][ok])
        Xm = np.column_stack([d_m, d_m[:, None] * n_m, d_m[:, None] * stf_features(n_m)])
        sig_m = np.hypot(250.0, C_KM_S * dat["z_obs"][ok] * ln10 * dat["logdist_err"][ok])
        wm = 1.0 / (sig_m * sig_m)
        vo = C_KM_S * dat["z_obs"][ok] * ln10 * dat["logdist"][ok]
        vt = C_KM_S * dat["z_obs"][ok] * ln10 * dat["logdist_true"][ok]
        Xw = np.sqrt(wm)[:, None] * Xm
        F = Xw.T @ Xw
        cov_m = np.linalg.inv(F)
        bo = np.linalg.solve(F, Xw.T @ (np.sqrt(wm) * vo))
        bt = np.linalg.solve(F, Xw.T @ (np.sqrt(wm) * vt))
        obs_vecs.append(bo[1:4])
        true_vecs.append(bt[1:4])
        formal_covs.append(cov_m[1:4, 1:4])

    obs_a = np.array(obs_vecs)
    true_a = np.array(true_vecs)
    emp_cov_obs = np.cov(obs_a.T, ddof=1)
    emp_cov_diff = np.cov((obs_a - true_a).T, ddof=1)
    mean_formal_cov = np.mean(formal_covs, axis=0)
    eig_ratio = np.linalg.eigvalsh(emp_cov_obs) / np.linalg.eigvalsh(mean_formal_cov)

    return {
        "epistemic_status": "conditional",
        "desi_fuji_fp": {
            "source_sha256": _sha256(DESI_FP),
            "n_galaxies": int(len(zc)),
            "zcmb_min_med_max": [float(np.min(zc)), float(np.median(zc)), float(np.max(zc))],
            "whitened_9p_singular_values": svals_9.tolist(),
            "whitened_4p_singular_values": svals_4.tolist(),
            "fit_4p_km_s_per_mpc": fit4,
            "fit_9p_km_s_per_mpc": fit9,
            "note": "DESI Fuji northern FP footprint has high 9p sky collinearity; 4p is better conditioned.",
        },
        "sdss_63_mocks_covariance": {
            "n_mocks": len(mocks),
            "obs_mean_vec_km_s_per_mpc": obs_a.mean(axis=0).tolist(),
            "true_mean_vec_km_s_per_mpc": true_a.mean(axis=0).tolist(),
            "bias_obs_minus_true_vec": (obs_a - true_a).mean(axis=0).tolist(),
            "empirical_3x3_obs_cov": emp_cov_obs.tolist(),
            "empirical_3x3_obs_minus_true_cov": emp_cov_diff.tolist(),
            "mean_formal_diag_noise_3x3_cov": mean_formal_cov.tolist(),
            "emp_obs_to_formal_noise_eig_ratios": eig_ratio.tolist(),
        },
    }


def main() -> int:
    if OUT_JSON.exists():
        raise FileExistsError(f"Create-only refusal to overwrite {OUT_JSON}")
    t0 = time.perf_counter()

    r88_pkt = r88_build_packet("SQ-CF4")
    part_a = _part_a_cf4_flow_and_partial_id()
    part_b = _part_b_des_svd_and_pantheon_splits()
    part_c = _part_c_desi_fp_and_sdss_cov()

    dt = time.perf_counter() - t0
    rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    payload = {
        "artifact_id": "R89_G02_CF4_SOLVER_FREE_RESEARCH_V1",
        "group_id": "G02_CF4",
        "create_only": True,
        "runtime_sec": round(dt, 3),
        "max_rss_mb": round(rss_mb, 2),
        "platform": platform.platform(),
        "sq_cf4_status": r88_pkt["status"],
        "part_a_cf4_flow_and_partial_id": part_a,
        "part_b_des_svd_and_pantheon_splits": part_b,
        "part_c_desi_fp_and_sdss_cov": part_c,
        "claim_hygiene": {
            "physical_Pi": None,
            "physical_GF": None,
            "bianchi_family_identified": False,
            "sixty_of_sixty_science_pass": False,
        },
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"group_id": "G02_RESEARCH", "sq_cf4_status": r88_pkt["status"], "runtime_sec": round(dt, 2), "max_rss_mb": round(rss_mb, 1)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
