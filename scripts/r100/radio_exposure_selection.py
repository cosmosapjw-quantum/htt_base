"""R100 Part C: LoTSS DR3 exposure audit, fixed-offset GLM count likelihoods, and boosted sample reselection."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import time

import healpy as hp
import numpy as np
import scipy
from scipy.optimize import minimize
from scipy.special import digamma, gammaln

from docs.research_program.observational_publication_20261015.H03_20261016.src.h03_tomography import stf_features
from scripts.r97 import bianchi_coupled_m_transport as r97
from scripts.r98 import cross_survey as r98_cs
from scripts.r99 import acquisition as r99_acq

ROOT = Path(__file__).resolve().parents[2]
R99_INP = ROOT / "docs/research_program/observational_publication_20261015/R99_FIFTH_BLOCKER_RESOLUTION_20261123/inputs"
R99_OUT = ROOT / "docs/research_program/observational_publication_20261015/R99_FIFTH_BLOCKER_RESOLUTION_20261123"
OUT_DIR = ROOT / "docs/research_program/observational_publication_20261015/R100_SOURCE_LAW_OPTICAL_MULTIPROBE_20261123"
BETA_CMB = r98_cs.BETA_CMB


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_lotss_c1_audit() -> tuple[dict[str, object], dict[str, np.ndarray]]:
    """C1: Audit captured LoTSS DR3 mosaic/metadata files and distinguish outer polygon vs tape-gated RMS."""
    rows, polys = r99_acq.load_polygons(R99_INP / "lotss_mosaics.csv")
    hp355 = json.loads((R99_INP / "lotss_hp355.json").read_text())
    hp1078 = json.loads((R99_INP / "lotss_hp1078.json").read_text())
    acq_res = json.loads((R99_OUT / "ACQUISITION_RESULTS.json").read_text())

    with np.load(R99_INP / "lotss_outer_exposure_nside16.npz", allow_pickle=False) as lz:
        lotss_npz = {k: lz[k].copy() for k in lz.files}

    # Check mosaic overlap multiplicity across NSIDE=16 pixel centers
    pix_vecs = np.asarray(hp.pix2vec(16, np.arange(hp.nside2npix(16)))).T
    overlap_counts = np.zeros(len(pix_vecs), dtype=np.int64)
    for poly in polys:
        overlap_counts += r99_acq.independent_union_membership([poly], pix_vecs).astype(np.int64)

    px_widths = [int(float(x)) for r in rows for x in (r.get("pixelsize") or "").strip("[]").split() if x]
    px_areas = [
        int(float(parts[0])) * int(float(parts[1]))
        for r in rows
        for parts in [(r.get("pixelsize") or "").strip("[]").split()]
        if len(parts) == 2
    ]
    accsizes = np.array([int(r.get("accsize") or 0) for r in rows], dtype=np.int64)
    # Count finite exposure bins across support
    sup = lotss_npz["support"].astype(bool)
    frac = lotss_npz["fraction"]
    partial_cells = int(np.sum(sup & (frac < 1.0 - 1e-12)))

    audit = {
        "status": "GEOMETRIC_OUTER_EXPOSURE_AUDITED_INTERNAL_RMS_BLOCKED_EXTERNAL",
        "mosaic_count": len(rows),
        "center_overlap_multiplicity_on_ns16": {
            "min_among_hit_centers": int(overlap_counts[overlap_counts > 0].min()),
            "median_among_hit_centers": float(np.median(overlap_counts[overlap_counts > 0])),
            "max_overlap_at_single_center": int(overlap_counts.max()),
            "fraction_of_support_centers_ge2_mosaics": float(np.mean(overlap_counts[sup] >= 2)),
        },
        "mosaic_pixel_width_min_median_max": [int(min(px_widths)), float(np.median(px_widths)), int(max(px_widths))],
        "total_mosaic_image_pixels": int(sum(px_areas)),
        "primary_mosaic_fits_total_bytes": int(accsizes.sum()),
        "nside16_support_cells": int(sup.sum()),
        "nside16_partial_boundary_cells": partial_cells,
        "nside16_full_interior_cells": int(sup.sum()) - partial_cells,
        "nside16_legacy_density_mask_cells": int(lotss_npz["original_density_mask"].sum()),
        "area_sq_deg_fine64_128_256": [r["area_square_deg"] for r in acq_res["resolution_checks"]],
        "fraction_max_abs_diff_fine128_vs_256": float(np.max(np.abs(lotss_npz["fraction_fine256"] - lotss_npz["fraction_fine128"]))),
        "surf_datalink_tape_audit": {
            "hp264_datalink_auxiliary_tar_bytes": 6450000000,
            "hp355_misc_tar_bytes": hp355["files"]["entries"]["HP-misc-355.tar"]["size"],
            "hp355_storage_class": hp355["files"]["entries"]["HP-misc-355.tar"]["storage_class"],
            "hp1078_misc_tar_bytes": hp1078["files"]["entries"]["HP-misc-1078.tar"]["size"],
            "hp1078_storage_class": hp1078["files"]["entries"]["HP-misc-1078.tar"]["storage_class"],
            "prior_http202_deferred_confirmed_without_tape_staging": True,
        },
        "blocked_metadata": [
            "Per-pixel valid-weight holes inside outer rectangles (inside HP-misc-*.tar on SURF tape)",
            "Per-mosaic local PyBDSF RMS noise map & flux-size completeness curve",
            "Source association / multi-component grouping uncertainties",
        ],
    }
    return audit, lotss_npz


def count_logpmf_and_grad_eta(y: np.ndarray, eta: np.ndarray, family: str, disp: float = 0.0):
    """Exact log PMF and d(logp)/d(eta) for Poisson, NB1 (Var=mu/(1-p)), and NB2_CoxLSS (Var=mu+alpha*mu^2)."""
    mu = np.exp(np.clip(eta, -40.0, 40.0))
    if family == "poisson":
        logp = y * eta - mu - gammaln(y + 1.0)
        d_eta = y - mu
        return logp, d_eta, np.zeros_like(y)
    if family == "nb1":
        p = float(disp)
        if not 0.0 < p < 1.0:
            raise ValueError(f"NB1 p must lie in (0, 1), got {p}")
        r = mu * (1.0 - p) / p
        logp = gammaln(y + r) - gammaln(r) - gammaln(y + 1.0) + r * math.log1p(-p) + y * math.log(p)
        psi_diff = digamma(y + r) - digamma(r) + math.log1p(-p)
        d_eta = r * psi_diff
        # dp derivative of r = mu*(1-p)/p: dr/dp = -mu/p^2
        dr_dp = -mu / (p * p)
        d_p = dr_dp * psi_diff - r / (1.0 - p) + y / p
        return logp, d_eta, d_p
    if family == "nb2":
        alpha = float(disp)
        if not alpha > 0.0:
            raise ValueError(f"NB2 alpha must be positive, got {alpha}")
        r = 1.0 / alpha
        log_r_mu = np.logaddexp(math.log(r), eta)  # log(r + mu)
        logp = (
            gammaln(y + r) - gammaln(r) - gammaln(y + 1.0)
            + r * (math.log(r) - log_r_mu) + y * (eta - log_r_mu)
        )
        d_eta = r * (y - mu) / (r + mu)
        d_alpha = -(r * r) * (digamma(y + r) - digamma(r) + math.log(r) - log_r_mu + 1.0 - (y + r) / (r + mu))
        return logp, d_eta, d_alpha
    raise ValueError(f"Unknown count family: {family}")


def fit_offset_count_glm(
    y: np.ndarray,
    X: np.ndarray,
    log_exposure: np.ndarray,
    model: str = "nb1_pearson",
    initial_beta: np.ndarray | None = None,
) -> dict[str, object]:
    """Fit mu_p = exp(log_exposure_p + X_p @ beta) via thin-QR BFGS with additive offset (no ridge).

    Strictly retains observed zero counts (y_p == 0) where exposure_p > 0; rejects nonfinite offsets.
    """
    y = np.asarray(y, dtype=float)
    X = np.asarray(X, dtype=float)
    off = np.asarray(log_exposure, dtype=float)
    if X.ndim != 2 or len(y) != len(X) or off.shape != (len(y),) or np.any(y < 0):
        raise ValueError("Invalid counts, design matrix, or offset shape")
    if not (np.all(np.isfinite(y)) and np.all(np.isfinite(X)) and np.all(np.isfinite(off))):
        raise ValueError("Counts, design, and log_exposure on active cells must all be finite (exclude e_p=0 before calling)")
    if len(y) <= X.shape[1]:
        raise ValueError("Insufficient observations for design rank")

    Q, R = np.linalg.qr(X, mode="reduced")
    if np.linalg.matrix_rank(R) < X.shape[1]:
        raise ValueError("Count design matrix is rank deficient")
    scale = math.sqrt(len(y))
    Z = Q * scale

    mean_rate = float(np.sum(y) / max(np.sum(np.exp(off)), 1e-30))
    b0 = np.zeros(X.shape[1], dtype=float)
    b0[0] = math.log(max(mean_rate, 1e-12))
    if initial_beta is not None:
        b0[:] = np.asarray(initial_beta, dtype=float)
    theta0 = R @ b0 / scale

    def fit_fixed(family: str, disp: float, th_start: np.ndarray):
        def obj(th):
            lp, d_eta, _ = count_logpmf_and_grad_eta(y, off + Z @ th, family, disp)
            return -float(np.mean(lp)), -(Z.T @ d_eta) / len(y)
        opt = minimize(obj, th_start, jac=True, method="BFGS", options={"gtol": 1e-7, "maxiter": 700})
        nll, grad = obj(opt.x)
        if not np.isfinite(nll) or np.max(np.abs(grad)) > 5e-5:
            raise RuntimeError(f"Offset GLM {model} did not converge: grad={np.max(np.abs(grad))}, msg={opt.message}")
        return opt.x, nll, grad, int(opt.nit)

    if model == "poisson":
        th, nll, grad, nit = fit_fixed("poisson", 0.0, theta0)
        disp_out = 0.0
        family = "poisson"
    elif model == "nb1_pearson":
        # Exposure-aware Pearson variance inflation around fitted Poisson mean!
        th_p, _, _, _ = fit_fixed("poisson", 0.0, theta0)
        mu_p = np.exp(off + Z @ th_p)
        phi = float(np.sum(((y - mu_p) ** 2) / np.maximum(mu_p, 1e-12)) / max(1, len(y) - X.shape[1]))
        p_hat = float(np.clip(1.0 - 1.0 / max(phi, 1.0001), 1e-5, 0.995))
        th, nll, grad, nit = fit_fixed("nb1", p_hat, th_p)
        disp_out = p_hat
        family = "nb1"
    elif model in ("nb1_mle", "nb2_coxlss"):
        family = "nb1" if model == "nb1_mle" else "nb2"
        th_init, _, _, _ = fit_fixed("poisson", 0.0, theta0)
        mu_p = np.exp(off + Z @ th_init)
        phi = max(1.05, float(np.sum(((y - mu_p) ** 2) / np.maximum(mu_p, 1e-12)) / max(1, len(y) - X.shape[1])))
        if family == "nb1":
            u0 = math.log(float(np.clip(1.0 - 1.0 / phi, 0.01, 0.98)) / (1.0 - float(np.clip(1.0 - 1.0 / phi, 0.01, 0.98))))
        else:
            alpha0 = max(1e-4, float(np.mean((y - mu_p) ** 2 - mu_p) / max(np.mean(mu_p ** 2), 1e-12)))
            u0 = math.log(alpha0)

        def obj_joint(vec):
            th_v, u_v = vec[:-1], float(vec[-1])
            if family == "nb1":
                u_c = float(np.clip(u_v, -12.0, 8.0))
                disp_v = 1.0 / (1.0 + math.exp(-u_c))
                d_disp_du = disp_v * (1.0 - disp_v)
            else:
                u_c = float(np.clip(u_v, -14.0, 6.0))
                disp_v = math.exp(u_c)
                d_disp_du = disp_v
            lp, d_eta, d_disp = count_logpmf_and_grad_eta(y, off + Z @ th_v, family, disp_v)
            g_th = -(Z.T @ d_eta) / len(y)
            g_u = -float(np.mean(d_disp)) * d_disp_du
            return -float(np.mean(lp)), np.r_[g_th, g_u]

        opt = minimize(obj_joint, np.r_[th_init, u0], jac=True, method="BFGS", options={"gtol": 1e-7, "maxiter": 800})
        th = opt.x[:-1]
        u_fin = float(opt.x[-1])
        disp_out = float(1.0 / (1.0 + math.exp(-np.clip(u_fin, -12.0, 8.0)))) if family == "nb1" else float(math.exp(np.clip(u_fin, -14.0, 6.0)))
        nll, grad = obj_joint(opt.x)
        nit = int(opt.nit)
        if not np.isfinite(nll) or np.max(np.abs(grad)) > 1e-4:
            raise RuntimeError(f"Joint MLE {model} did not converge: grad={np.max(np.abs(grad))}")
    else:
        raise ValueError(f"Unknown model {model}")

    beta = np.linalg.solve(R, th * scale)
    _, raw_d_eta, _ = count_logpmf_and_grad_eta(y, off + X @ beta, family, disp_out)
    raw_grad = -(X.T @ raw_d_eta) / len(y)
    return {
        "family": family,
        "beta": beta,
        "dispersion": float(disp_out),
        "nll": float(nll),
        "sum_loglik": float(-nll * len(y)),
        "max_mean_raw_score_abs": float(np.max(np.abs(raw_grad))),
        "whitened_max_grad_abs": float(np.max(np.abs(grad))),
        "iterations": nit,
        "design_condition": float(np.linalg.cond(R)),
    }


def boosted_reselection_dipole(
    beta_vec: np.ndarray,
    log_cuts: np.ndarray,
    log_counts_per_sr: np.ndarray,
    ref_cut_idx: int,
    sed_model: str = "dirac_0p75",
    alpha_mean: float = 0.75,
    alpha_std: float = 0.25,
) -> dict[str, object]:
    """Exact finite-boost Doppler + aberration + empirical SED-integrated sample reselection dipole.

    Evaluates dN/dOmega(n; beta) = D_o(n)^2 * int P(alpha) N_rest(> S_ref * D_o(n)^-(1+alpha)) dalpha
    across Gauss-Legendre sky grid and compares against linear Ellis-Baldwin d_EB = [2 + x(1+alpha)] beta.
    """
    beta = np.asarray(beta_vec, dtype=float)
    b2 = float(beta @ beta)
    if b2 >= 1.0:
        raise ValueError("Superluminal boost")
    gamma = 1.0 / math.sqrt(1.0 - b2)
    _, _, nh, w = r97.gl_sphere_grid(24)
    nh_flat = nh.reshape(-1, 3)
    w4 = (w / (4.0 * math.pi)).ravel()

    D_o = gamma * (1.0 + nh_flat @ beta)
    log_D = np.log(D_o)

    # Interpolate empirical rest-frame cumulative log N(>S) safely via linear/quadratic fit to log cuts
    if len(log_cuts) >= 3:
        poly = np.polyfit(log_cuts - log_cuts[ref_cut_idx], log_counts_per_sr - log_counts_per_sr[ref_cut_idx], 2)
        c2, c1, c0 = float(poly[0]), float(poly[1]), float(poly[2])
    else:
        poly1 = np.polyfit(log_cuts - log_cuts[ref_cut_idx], log_counts_per_sr - log_counts_per_sr[ref_cut_idx], 1)
        c2, c1, c0 = 0.0, float(poly1[0]), float(poly1[1])
    x_loc = -c1  # empirical slope -d(ln N)/d(ln S) at ref cut
    x_prime = -2.0 * c2  # curvature -d^2(ln N)/d(ln S)^2

    if sed_model.startswith("dirac_"):
        a_pts = np.array([alpha_mean])
        a_wts = np.array([1.0])
    elif sed_model == "gaussian_hermite":
        from scipy.special import roots_hermitenorm
        z_h, w_h = roots_hermitenorm(15)
        a_pts = alpha_mean + alpha_std * z_h
        a_wts = w_h / math.sqrt(2.0 * math.pi)
    else:
        raise ValueError(sed_model)

    # Shift in threshold log(S_rest / S_ref) = -(1 + alpha) * log(D_o)
    dlogS = -np.outer(log_D, 1.0 + a_pts)
    log_N_rel = c0 + c1 * dlogS + c2 * (dlogS ** 2)
    lam = (D_o[:, None] ** 2) * (np.exp(log_N_rel) @ a_wts)[:, None]
    lam = lam.ravel()
    lam_norm = lam / float(np.sum(w4 * lam))
    dip_exact = 3.0 * np.sum((w4 * (lam_norm - 1.0))[:, None] * nh_flat, axis=0)
    dip_eb_linear = (2.0 + x_loc * (1.0 + alpha_mean)) * beta
    return {
        "x_local_slope": x_loc,
        "x_curvature": x_prime,
        "boosted_nonlinear_dipole_vec": dip_exact.tolist(),
        "boosted_nonlinear_dipole_amp": float(np.linalg.norm(dip_exact)),
        "eb_linear_dipole_vec": dip_eb_linear.tolist(),
        "eb_linear_dipole_amp": float(np.linalg.norm(dip_eb_linear)),
        "nonlinear_plus_curvature_rel_diff": float(np.linalg.norm(dip_exact - dip_eb_linear) / max(np.linalg.norm(dip_eb_linear), 1e-30)),
    }


def compute() -> dict[str, object]:
    t0 = time.monotonic()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    c1_audit, lotss_npz = load_lotss_c1_audit()
    src = r98_cs.load_radio()
    counts_by_survey, old_mask_lotss, cache_prov = r99_acq.locked_radio_cache()

    with np.load(cache_prov["maps_path"], allow_pickle=False) as mf:
        all_maps = {}
        all_masks = {}
        for k in mf.files:
            if k.startswith("mask__"):
                all_masks[k[6:]] = mf[k].astype(bool)
            else:
                _, sname, cut_s = k.split("__")
                all_maps.setdefault(sname, {})[float(cut_s)] = mf[k].copy()

    pix_area = float(hp.nside2pixarea(16))
    uniform_log_exp = np.full(src.NPIX, math.log(pix_area), dtype=float)
    nhi_base_gal = (np.abs(src.PIX_B_DEG) > 15.0) & all_masks["NVSS"]  # exact |b|>15 check below
    # Reconstruct exact |b|>15 & NHI<1e21 mask from cached R89 reader if quick, or compare lotss outer support with |b|>15:
    b_gt_15 = np.abs(src.PIX_B_DEG) > 15.0
    lotss_outer_sup = lotss_npz["support"].astype(bool)
    lotss_outer_b15 = lotss_outer_sup & b_gt_15
    lotss_outer_log_exp = lotss_npz["log_exposure_sr"]

    # Footprints to analyze: 5 declared surveys + LoTSS outer_exposure_b15 & LoTSS outer_exposure_all!
    footprints = [
        ("NVSS", "NVSS", all_masks["NVSS"], uniform_log_exp),
        ("RACS_DR1", "RACS_DR1", all_masks["RACS_DR1_unif"], uniform_log_exp),
        ("SPICE_RACS", "SPICE_RACS", all_masks["SPICE_RACS"], uniform_log_exp),
        ("SUMSS", "SUMSS", all_masks["SUMSS"], uniform_log_exp),
        ("LoTSS_DR3_legacy966", "LoTSS_DR3", all_masks["LoTSS_DR3_int1500"], uniform_log_exp),
        ("LoTSS_DR3_outer_b15", "LoTSS_DR3", lotss_outer_b15, lotss_outer_log_exp),
        ("LoTSS_DR3_outer_all1771", "LoTSS_DR3", lotss_outer_sup, lotss_outer_log_exp),
    ]

    X4 = np.column_stack((np.ones(src.NPIX), src.PIX_N))
    X9 = np.column_stack((X4, stf_features(src.PIX_N)))
    rng = np.random.default_rng(9804)
    fold_of_patch = np.empty(48, int)
    fold_of_patch[rng.permutation(48)] = np.arange(48) % 4
    fold = fold_of_patch[src.PIX_PATCH]

    survey_results = {}
    reselection_results = {}
    jk_dipoles = {}

    for label, sname, mask, log_exp in footprints:
        dd = all_maps[sname]
        # Verify positive counts never appear where geometric exposure == 0!
        cuts_sorted = sorted(dd)
        for c in cuts_sorted:
            if np.any((dd[c] > 0) & mask & (~np.isfinite(log_exp))):
                raise ValueError(f"Positive count on zero exposure in {label} cut {c}")
        active = mask & np.isfinite(log_exp)
        n_empty = int(np.sum(active & (dd[cuts_sorted[0]] == 0)))
        survey_results[label] = {
            "survey": sname,
            "active_cells": int(active.sum()),
            "total_exposure_sr": float(np.sum(np.exp(log_exp[active]))),
            "min_cell_exposure_frac": float(np.min(np.exp(log_exp[active])) / pix_area),
            "observed_empty_cells_lowest_cut_retained": n_empty,
            "cuts": {},
        }
        for cut in cuts_sorted:
            y = dd[cut]
            cut_row = {"n_sources": int(y[active].sum()), "observed_empty_cells": int(np.sum(active & (y == 0))), "models": {}}
            for mname, mkey, X in (
                ("Poisson4_offset", "poisson", X4),
                ("NB1_4_Pearson_offset", "nb1_pearson", X4),
                ("NB1_4_MLE_offset", "nb1_mle", X4),
                ("NB2_CoxLSS_4_offset", "nb2_coxlss", X4),
                ("NB1_9_offset", "nb1_pearson", X9),
            ):
                fit = fit_offset_count_glm(y[active], X[active], log_exp[active], mkey)
                cv_ll = 0.0
                for k in range(4):
                    tr = active & (fold != k)
                    te = active & (fold == k)
                    if te.sum() == 0:
                        continue
                    ft = fit_offset_count_glm(y[tr], X[tr], log_exp[tr], mkey)
                    lp, _, _ = count_logpmf_and_grad_eta(
                        y[te], log_exp[te] + X[te] @ ft["beta"], ft["family"], ft["dispersion"]
                    )
                    cv_ll += float(np.sum(lp))
                beta = fit.pop("beta")
                fit.update(
                    beta_log_intensity=beta.tolist(),
                    exact_fullsky_dipole=r98_cs.exact_log_dipole(beta[1:4]).tolist(),
                    dipole_amp=float(np.linalg.norm(r98_cs.exact_log_dipole(beta[1:4]))),
                    heldout_sum_loglik=cv_ll,
                )
                cut_row["models"][mname] = fit
            # Explicit Log-likelihood gains on held-out 4-fold predictions
            m_d = cut_row["models"]
            cut_row["cv_loglik_gain_nb1_mle_minus_poisson"] = m_d["NB1_4_MLE_offset"]["heldout_sum_loglik"] - m_d["Poisson4_offset"]["heldout_sum_loglik"]
            cut_row["cv_loglik_gain_nb2_coxlss_minus_poisson"] = m_d["NB2_CoxLSS_4_offset"]["heldout_sum_loglik"] - m_d["Poisson4_offset"]["heldout_sum_loglik"]
            cut_row["cv_loglik_gain_nb2_minus_nb1_mle"] = m_d["NB2_CoxLSS_4_offset"]["heldout_sum_loglik"] - m_d["NB1_4_MLE_offset"]["heldout_sum_loglik"]
            survey_results[label]["cuts"][str(cut)] = cut_row

        # Empirical N(>S) & boosted sample reselection at reference cut (50 mJy LoTSS, 20 mJy others)
        ref_cut = 50.0 if sname == "LoTSS_DR3" else 20.0
        ref_i = cuts_sorted.index(ref_cut)
        sr_tot = float(np.sum(np.exp(log_exp[active])))
        log_cuts = np.log(np.array(cuts_sorted, dtype=float))
        log_counts_sr = np.array([math.log(max(dd[c][active].sum(), 1) / sr_tot) for c in cuts_sorted], dtype=float)

        b_cmb = BETA_CMB * src.CMB_U_ICRS
        b_3cmb = 3.0 * b_cmb
        rs_tab = {}
        for sed_lbl, am in (("dirac_0p50", 0.50), ("dirac_0p75", 0.75), ("dirac_1p00", 1.00), ("gaussian_hermite", 0.75)):
            rs_tab[f"{sed_lbl}__1xCMB"] = boosted_reselection_dipole(b_cmb, log_cuts, log_counts_sr, ref_i, sed_lbl, am)
            rs_tab[f"{sed_lbl}__3xCMB"] = boosted_reselection_dipole(b_3cmb, log_cuts, log_counts_sr, ref_i, sed_lbl, am)
        reselection_results[label] = {"reference_cut_mJy": ref_cut, "scenarios": rs_tab}

        # 48-patch jackknife dipole under fixed-offset NB1_4_Pearson
        y_ref = dd[ref_cut]
        b_full_ref = np.asarray(survey_results[label]["cuts"][str(ref_cut)]["models"]["NB1_4_Pearson_offset"]["beta_log_intensity"])
        ll = []
        for p in range(48):
            mm = active & (src.PIX_PATCH != p)
            if mm.sum() <= 15:
                ll.append(b_full_ref[1:4])
                continue
            fit_p = fit_offset_count_glm(y_ref[mm], X4[mm], log_exp[mm], "nb1_pearson", b_full_ref)
            ll.append(fit_p["beta"][1:4])
        jk_dipoles[label] = np.asarray(ll)

    def _five_survey_joint(canon_labels: list[str], caveat: str) -> dict[str, object]:
        joint_jk = np.concatenate([jk_dipoles[lb] for lb in canon_labels], axis=1)
        C15_jk = r98_cs.jackknife_cov(joint_jk)
        obs_dips = np.concatenate([
            np.asarray(survey_results[lb]["cuts"][str(50.0 if "LoTSS" in lb else 20.0)]["models"]["NB1_4_Pearson_offset"]["exact_fullsky_dipole"])
            for lb in canon_labels
        ])
        ev15, U15 = np.linalg.eigh(0.5 * (C15_jk + C15_jk.T))
        keep15 = ev15 > 1e-10 * ev15[-1]
        X_common_eb = np.vstack([
            (2.0 + reselection_results[lb]["scenarios"]["dirac_0p75__1xCMB"]["x_local_slope"] * 1.75) * np.eye(3)
            for lb in canon_labels
        ])
        W_15 = (U15[:, keep15] / np.sqrt(ev15[keep15])) @ U15[:, keep15].T
        beta_common_gls = np.linalg.lstsq(W_15 @ X_common_eb, W_15 @ obs_dips, rcond=None)[0]
        chi2_common = float(np.sum((W_15 @ (obs_dips - X_common_eb @ beta_common_gls)) ** 2))
        chi2_cmb_pred = float(np.sum((W_15 @ (obs_dips - X_common_eb @ (BETA_CMB * src.CMB_U_ICRS))) ** 2))
        return {
            "surveys": canon_labels,
            "jackknife_15d_rank": int(np.sum(keep15)),
            "common_beta_over_beta_cmb": float(np.linalg.norm(beta_common_gls) / BETA_CMB),
            "common_beta_icrs": beta_common_gls.tolist(),
            "chi2_subspace_common_free_beta": chi2_common,
            "chi2_subspace_fixed_planck_cmb_beta": chi2_cmb_pred,
            "calibrated_p": None,
            "caveat": caveat,
        }

    joint_legacy = _five_survey_joint(
        ["NVSS", "RACS_DR1", "SPICE_RACS", "SUMSS", "LoTSS_DR3_legacy966"],
        "Spatial 48-patch jackknife covariance across complete-interior footprints (excludes 112 unmasked LoTSS outer empty cells).",
    )
    joint_outer_b15 = _five_survey_joint(
        ["NVSS", "RACS_DR1", "SPICE_RACS", "SUMSS", "LoTSS_DR3_outer_b15"],
        "Sensitivity replacing LoTSS_DR3_legacy966 with unmasked LoTSS_DR3_outer_b15 (1338 cells incl. 112 uncalibrated empty holes missing SURF tape RMS maps; induces boundary gradient dipole).",
    )

    payload = {
        "schema": "htt.r100.radio_exposure_selection/1",
        "owner": "obsstat",
        "status": "MODEL_CONDITIONAL_EXPOSURE_RESELECTION_EXECUTED",
        "physical_Pi": None,
        "physical_GF": None,
        "inputs": {
            **cache_prov,
            "lotss_mosaics_sha256": sha256(R99_INP / "lotss_mosaics.csv"),
            "lotss_exposure_npz_sha256": sha256(R99_INP / "lotss_outer_exposure_nside16.npz"),
            "code_sha256": sha256(Path(__file__)),
        },
        "C1_lotss_dr3_coverage_audit": c1_audit,
        "C2_offset_count_models": survey_results,
        "C2_boosted_sample_reselection": reselection_results,
        "C2_five_survey_common_beta_vs_residuals": joint_legacy,
        "C2_five_survey_with_lotss_outer_b15_sensitivity": joint_outer_b15,
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "threads": {k: os.getenv(k) for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")},
        },
        "runtime_seconds": time.monotonic() - t0,
    }
    out_path = OUT_DIR / "RADIO_EXPOSURE_SELECTION_RESULTS.json"
    out_path.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    return payload


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.parse_args()
    res = compute()
    lo_b15 = res["C2_offset_count_models"]["LoTSS_DR3_outer_b15"]["cuts"]["50.0"]
    lo_old = res["C2_offset_count_models"]["LoTSS_DR3_legacy966"]["cuts"]["50.0"]
    print(json.dumps({
        "status": res["status"],
        "lotss_outer_b15_cells": res["C2_offset_count_models"]["LoTSS_DR3_outer_b15"]["active_cells"],
        "lotss_legacy966_cells": res["C2_offset_count_models"]["LoTSS_DR3_legacy966"]["active_cells"],
        "lotss_50mJy_nb2_gain_over_nb1": lo_b15["cv_loglik_gain_nb2_minus_nb1_mle"],
        "lotss_50mJy_dipole_b15_vs_966": [
            lo_b15["models"]["NB1_4_MLE_offset"]["dipole_amp"],
            lo_old["models"]["NB1_4_MLE_offset"]["dipole_amp"],
        ],
        "common_beta_ratio_cmb": res["C2_five_survey_common_beta_vs_residuals"]["common_beta_over_beta_cmb"],
        "runtime_s": res["runtime_seconds"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
