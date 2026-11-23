"""R102 Step 3: SQ-CF4 selection/calibration uncertainty, group-blocked holdout & SDSS randoms.

Reuses R101's full 8,885-row 6dFGSv match-pattern likelihood and training-only 36D
CF4 predictive contrasts, extends them with:
1. 6dFGSv 8,885-row exact R101 replay + observed probit Fisher covariance + pairs
   cluster bootstrap + 5-fold group-blocked cross-validation (no intra-group leakage)
   + Laplace/delta-method uncertainty propagation + 4-row multi-match ambiguity policies.
2. Streaming intake of 4,000,000-row SDSS_randoms_public.dat (v1.1.0), NSIDE=32 HEALPix
   footprint/multipole comparison & radial N(z) selection audit vs 34,059-row SDSS_PV,
   plus 5-fold group-blocked CV on SDSS in_mask probit (idgroupt17 > 0 grouped, 0 singleton).
3. CF4 36D training-only component-wise predictive tangents (diag_meas_nl150, cal_plus_cut,
   sel_mag, S_PV low/inherited/high) with Euler homogeneity & finite-difference checks,
   plus sky-quadrant & Table-3 calibrator overlap audit.

All outputs remain source-conditional diagnostics on already released catalogs:
source_qualification="BLOCKED_INPUT", physical_Pi=None, physical_GF=None,
calibrated_p=None, Bianchi_family_attribution=None.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import time

import healpy as hp
import numpy as np

from htt.infer.cf4_group_holdout import (
    build_group_clusters,
    cluster_bootstrap_probit,
    component_covariance_tangents,
    fit_probit_with_hessian,
    group_kfold_indices,
    selected_probit_uncertainty_propagation,
    sixdf_match_ambiguity_policies,
)
from htt.infer.cf4_predictive_response import (
    predictive_contrasts,
    predictive_covariance_response,
    selected_probit_field_response,
)
from scripts.r97 import cf4_genealogy_and_partial_id as r97
from scripts.r98 import cf4_p1 as old
from scripts.r99 import cf4_source_law as r99
from scripts.r100 import cf4_upstream_and_kband as r100
from scripts.r101 import cf4_predictive_response as r101_cf4

ROOT = Path(__file__).resolve().parents[2]
R98_DIR = ROOT / "docs/research_program/observational_publication_20261015/R98_FOURTH_RESEARCH_CYCLE_20261123"
R100_DIR = ROOT / "docs/research_program/observational_publication_20261015/R100_SOURCE_LAW_OPTICAL_MULTIPROBE_20261123"
SDSS_RANDOMS_PATH = Path("/home/cosmosapjw/Downloads/htt_r101/SDSS_randoms_public.dat")
DEFAULT_OUT = (
    ROOT
    / "docs/research_program/observational_publication_20261015"
    / "R102_CF4_HOLDOUT_NATIVE_SOLVER_20261123"
    / "CF4_SELECTION_HOLDOUT_RESULTS.json"
)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _sixdf_part(r100_ref: dict[str, object]) -> dict[str, object]:
    # Exact R101 replay check
    r101_marks = r101_cf4.source_marks(r100_ref)
    target_diff = float(r101_marks["fitted_with_all_parent_match_indicators"]["log_density_mix_minus_zero"])
    if abs(target_diff - 27.341020201440188) > 1e-8:
        raise ArithmeticError(f"R101 8,885-row 6dFGSv replay drifted: {target_diff}")

    t2 = r100.load_cf4_table2()
    six = r100.load_sixdf_pv()
    amb = sixdf_match_ambiguity_policies(t2, six, arcsec=15.0, dv_kms=500.0)
    unique_inc = amb["policies"]["unique_only_r101"]["included"]
    closest_idx = amb["closest_table2_indices"]
    matched_t2_pgc = np.where(closest_idx >= 0, t2["pgc"][np.maximum(closest_idx, 0)], -1)
    matched_t2_pgc1 = np.where(closest_idx >= 0, t2["pgc1"][np.maximum(closest_idx, 0)], -1)

    cz = np.asarray(six["cz_gal"], dtype=np.float64)
    delta_d = np.asarray(six["delta_d"], dtype=np.float64)
    sigma = np.asarray(six["epsilon_d"], dtype=np.float64)
    is_grp = np.asarray(six["is_grouped"], dtype=np.float64)
    X_full = np.column_stack((np.ones(len(cz)), cz / 1e4 - 1.1, delta_d, is_grp))

    fit_full = fit_probit_with_hessian(X_full, unique_inc)
    beta_ref = np.asarray(
        r100_ref["A4_selection_likelihood_and_4term_cov"]["empirical_probit_inclusion_6df"]["beta_probit"],
        dtype=np.float64,
    )
    beta_replay_err = float(np.max(np.abs(fit_full.beta_hat - beta_ref)))
    if beta_replay_err > 1e-6:
        raise ArithmeticError(f"6dF probit MLE mismatch vs R100: {beta_replay_err}")

    # Group clusters preserving ungrouped sentinel (-1) as singletons and linking Table-2 PGC duplicates
    clusters = build_group_clusters(
        six["groupid_raw"], ungrouped_sentinel=(-1, 0), secondary_keys=matched_t2_pgc
    )
    boot = cluster_bootstrap_probit(X_full, unique_inc, clusters, n_boot=40, seed=202611)

    # Bolometric field means at 5 fields across all 8,885 parent rows
    fields = np.asarray([-300.0, -100.0, 0.0, 100.0, 300.0], dtype=np.float64)
    probs = np.full(len(fields), 0.2, dtype=np.float64)
    sci, *_ = old._load_r30_and_bridge()
    z_parent = cz / r100.C
    parent_means = np.stack(
        [r99.finite_shift(sci, z_parent, np.arctanh(v / r100.C), "bolometric") / (5.0 * r100.MAG) for v in fields]
    )
    input_mark = np.where(unique_inc, delta_d, np.nan)

    # Full-cohort selection uncertainty propagation (Laplace Hessian + cluster bootstrap)
    unc_laplace = selected_probit_uncertainty_propagation(
        input_mark,
        parent_means,
        sigma,
        X_full,
        fit_full.beta_hat,
        fit_full.cov_laplace,
        probs,
        included=unique_inc,
        mark_col=2,
        n_mc=128,
        seed=12345,
    )
    unc_boot = selected_probit_uncertainty_propagation(
        input_mark,
        parent_means,
        sigma,
        X_full,
        fit_full.beta_hat,
        boot["cov_cluster_bootstrap"],
        probs,
        included=unique_inc,
        mark_col=2,
        n_mc=128,
        seed=54321,
    )

    # 5-fold group-blocked CV: fit probit ONLY on training clusters, evaluate held-out inclusion & field response
    folds = group_kfold_indices(clusters, n_splits=5, seed=42)
    fold_rows = []
    from scipy.special import log_ndtr

    sum_cv_mix_minus_zero_plugin = 0.0
    sum_cv_mix_minus_zero_marg = 0.0
    for f_id, (tr_idx, te_idx) in enumerate(folds):
        if len(np.intersect1d(clusters[tr_idx], clusters[te_idx])) != 0:
            raise AssertionError("group leakage")
        fit_tr = fit_probit_with_hessian(X_full[tr_idx], unique_inc[tr_idx])
        sign_te = np.where(unique_inc[te_idx], 1.0, -1.0)
        te_probit_ll = float(np.sum(log_ndtr(sign_te * (X_full[te_idx] @ fit_tr.beta_hat))))
        te_prop = selected_probit_uncertainty_propagation(
            input_mark[te_idx],
            parent_means[:, te_idx],
            sigma[te_idx],
            X_full[te_idx],
            fit_tr.beta_hat,
            fit_tr.cov_laplace,
            probs,
            included=unique_inc[te_idx],
            mark_col=2,
            n_mc=64,
            seed=7000 + f_id,
        )
        sum_cv_mix_minus_zero_plugin += float(te_prop["plugin_log_density_mix_minus_zero"])
        sum_cv_mix_minus_zero_marg += float(te_prop["marginalized_log_density_mix_minus_zero"])
        fold_rows.append(
            {
                "fold": f_id,
                "n_train": int(len(tr_idx)),
                "n_test": int(len(te_idx)),
                "n_test_matched": int(np.count_nonzero(unique_inc[te_idx])),
                "n_test_rejected": int(np.count_nonzero(~unique_inc[te_idx])),
                "beta_train": fit_tr.beta_hat.tolist(),
                "heldout_probit_loglik": te_probit_ll,
                "heldout_plugin_mix_minus_zero": float(te_prop["plugin_log_density_mix_minus_zero"]),
                "heldout_delta_method_std": float(te_prop["delta_method_std_mix_minus_zero"]),
                "heldout_marginalized_mix_minus_zero": float(te_prop["marginalized_log_density_mix_minus_zero"]),
            }
        )

    # 4-row multi-match ambiguity sensitivity policies
    ambiguity_sensitivity = {}
    for pname, pspec in amb["policies"].items():
        keep = pspec["keep"]
        inc = pspec["included"][keep]
        fit_p = fit_probit_with_hessian(X_full[keep], inc)
        mk_p = np.where(inc, delta_d[keep], np.nan)
        a_p = fit_p.beta_hat[0] + fit_p.beta_hat[1] * (cz[keep] / 1e4 - 1.1) + fit_p.beta_hat[3] * is_grp[keep]
        mix_p = selected_probit_field_response(mk_p, parent_means[:, keep], sigma[keep], a_p, float(fit_p.beta_hat[2]), probs, included=inc)
        zer_p = selected_probit_field_response(mk_p, np.zeros((1, int(np.count_nonzero(keep)))), sigma[keep], a_p, float(fit_p.beta_hat[2]), [1.0], included=inc)
        ambiguity_sensitivity[pname] = {
            "rows_evaluated": int(np.count_nonzero(keep)),
            "matched_count": int(np.count_nonzero(inc)),
            "rejected_count": int(np.count_nonzero(~inc)),
            "beta_probit": fit_p.beta_hat.tolist(),
            "probit_loglik": float(fit_p.loglik),
            "log_density_mix_minus_zero": float(mix_p["log_density"] - zer_p["log_density"]),
        }

    # Sensitivity: link CF4 Table-2 group identifier pgc1 alongside 6dF groupid_raw
    clusters_pgc1 = build_group_clusters(
        six["groupid_raw"], ungrouped_sentinel=(-1, 0), secondary_keys=matched_t2_pgc1
    )
    folds_pgc1 = group_kfold_indices(clusters_pgc1, n_splits=5, seed=42)
    pgc1_probit_ll = 0.0
    pgc1_plugin = 0.0
    pgc1_marg = 0.0
    for f_id, (tr_idx, te_idx) in enumerate(folds_pgc1):
        if len(np.intersect1d(clusters_pgc1[tr_idx], clusters_pgc1[te_idx])) != 0:
            raise AssertionError("pgc1 group leakage")
        fit_tr = fit_probit_with_hessian(X_full[tr_idx], unique_inc[tr_idx])
        sign_te = np.where(unique_inc[te_idx], 1.0, -1.0)
        pgc1_probit_ll += float(np.sum(log_ndtr(sign_te * (X_full[te_idx] @ fit_tr.beta_hat))))
        te_prop = selected_probit_uncertainty_propagation(
            input_mark[te_idx],
            parent_means[:, te_idx],
            sigma[te_idx],
            X_full[te_idx],
            fit_tr.beta_hat,
            fit_tr.cov_laplace,
            probs,
            included=unique_inc[te_idx],
            mark_col=2,
            n_mc=64,
            seed=7100 + f_id,
        )
        pgc1_plugin += float(te_prop["plugin_log_density_mix_minus_zero"])
        pgc1_marg += float(te_prop["marginalized_log_density_mix_minus_zero"])

    return {
        "r101_replay_mix_minus_zero": target_diff,
        "r100_probit_beta_replay_max_abs_err": beta_replay_err,
        "parent_rows": int(len(cz)),
        "unique_group_clusters": int(len(np.unique(clusters))),
        "pgc1_linked_group_cv": {
            "unique_group_clusters_pgc1": int(len(np.unique(clusters_pgc1))),
            "n_splits": 5,
            "zero_cluster_leakage_verified": True,
            "sum_heldout_probit_loglik": pgc1_probit_ll,
            "sum_heldout_plugin_mix_minus_zero": pgc1_plugin,
            "sum_heldout_marginalized_mix_minus_zero": pgc1_marg,
        },
        "probit_full_fit": {
            "features": ["1", "(cz/1e4 - 1.1)", "delta_d", "is_grouped"],
            "beta_hat": fit_full.beta_hat.tolist(),
            "loglik": fit_full.loglik,
            "grad_norm": fit_full.grad_norm,
            "laplace_std": np.sqrt(np.diag(fit_full.cov_laplace)).tolist(),
            "laplace_cov": fit_full.cov_laplace.tolist(),
            "cluster_bootstrap_n": int(boot["n_boot"]),
            "cluster_bootstrap_std": boot["std_beta"].tolist(),
            "cluster_bootstrap_cov": boot["cov_cluster_bootstrap"].tolist(),
        },
        "selection_uncertainty_full_cohort": {
            "plugin_mix_minus_zero": float(unc_laplace["plugin_log_density_mix_minus_zero"]),
            "grad_beta_mix_minus_zero": unc_laplace["grad_beta_mix_minus_zero"].tolist(),
            "laplace_delta_method_std": float(unc_laplace["delta_method_std_mix_minus_zero"]),
            "laplace_marginalized_mix_minus_zero": float(unc_laplace["marginalized_log_density_mix_minus_zero"]),
            "cluster_boot_delta_method_std": float(unc_boot["delta_method_std_mix_minus_zero"]),
            "cluster_boot_marginalized_mix_minus_zero": float(unc_boot["marginalized_log_density_mix_minus_zero"]),
        },
        "five_fold_group_cv": {
            "n_splits": 5,
            "zero_cluster_leakage_verified": True,
            "sum_heldout_probit_loglik": float(sum(r["heldout_probit_loglik"] for r in fold_rows)),
            "sum_heldout_plugin_mix_minus_zero": sum_cv_mix_minus_zero_plugin,
            "sum_heldout_marginalized_mix_minus_zero": sum_cv_mix_minus_zero_marg,
            "folds": fold_rows,
        },
        "match_ambiguity_policies": {
            "multiplicity_histogram": amb["multiplicity_histogram"],
            "ambiguous_4_rows": amb["ambiguous_rows"],
            "policies": ambiguity_sensitivity,
        },
    }


def _sdss_randoms_and_holdout_part(r100_ref: dict[str, object]) -> dict[str, object]:
    if not SDSS_RANDOMS_PATH.is_file():
        raise FileNotFoundError(f"missing downloaded SDSS_randoms_public.dat at {SDSS_RANDOMS_PATH}")

    nside = 32
    npix = hp.nside2npix(nside)
    rand_pix_counts = np.zeros(npix, dtype=np.int64)
    rand_pix_nbar_sum = np.zeros(npix, dtype=np.float64)
    z_edges = np.linspace(0.0, 0.12, 25, dtype=np.float64)
    rand_z_hist = np.zeros(len(z_edges) - 1, dtype=np.int64)

    n_rand = 0
    ra_min, ra_max = math.inf, -math.inf
    dec_min, dec_max = math.inf, -math.inf
    z_min, z_max, z_sum = math.inf, -math.inf, 0.0
    nb_min, nb_max, nb_sum = math.inf, -math.inf, 0.0

    # Chunked streaming intake over all 4,000,000 rows without full-array memory blowup
    from itertools import islice

    chunk_size = 250_000
    with SDSS_RANDOMS_PATH.open("r", encoding="ascii") as f:
        header = f.readline().strip()
        while True:
            lines = list(islice(f, chunk_size))
            if not lines:
                break
            chunk = np.loadtxt(lines, dtype=np.float64)
            if chunk.ndim == 1:
                chunk = chunk[None, :]
            ra_c, dec_c, z_c, nb_c = chunk[:, 0], chunk[:, 1], chunk[:, 2], chunk[:, 3]
            n_c = len(ra_c)
            n_rand += n_c
            ra_min = min(ra_min, float(np.min(ra_c)))
            ra_max = max(ra_max, float(np.max(ra_c)))
            dec_min = min(dec_min, float(np.min(dec_c)))
            dec_max = max(dec_max, float(np.max(dec_c)))
            z_min = min(z_min, float(np.min(z_c)))
            z_max = max(z_max, float(np.max(z_c)))
            z_sum += float(np.sum(z_c))
            nb_min = min(nb_min, float(np.min(nb_c)))
            nb_max = max(nb_max, float(np.max(nb_c)))
            nb_sum += float(np.sum(nb_c))

            th = np.deg2rad(90.0 - dec_c)
            ph = np.deg2rad(ra_c)
            pix = hp.ang2pix(nside, th, ph, nest=False)
            rand_pix_counts += np.bincount(pix, minlength=npix)
            rand_pix_nbar_sum += np.bincount(pix, weights=nb_c, minlength=npix)
            zh, _ = np.histogram(z_c, bins=z_edges)
            rand_z_hist += zh

    sdss = r100.load_sdss_pv()
    in_mask = np.asarray(sdss["in_mask"], dtype=bool)
    sdss_pix_all = hp.ang2pix(nside, np.deg2rad(90.0 - sdss["dec"]), np.deg2rad(sdss["ra"]), nest=False)
    sdss_all_counts = np.bincount(sdss_pix_all, minlength=npix)
    sdss_inmask_counts = np.bincount(sdss_pix_all[in_mask], minlength=npix)

    rand_occ = rand_pix_counts > 0
    sdss_occ_all = sdss_all_counts > 0
    sdss_occ_mask = sdss_inmask_counts > 0
    corr_inmask = float(np.corrcoef(rand_pix_counts[rand_occ], sdss_inmask_counts[rand_occ])[0, 1])

    # Low-ell normalized footprint spherical harmonic spectrum comparison (l=1..6)
    f_rand = rand_pix_counts / max(float(np.mean(rand_pix_counts)), 1.0)
    f_sdss = sdss_inmask_counts / max(float(np.mean(sdss_inmask_counts)), 1.0)
    cl_rand = hp.anafast(f_rand, lmax=6)
    cl_sdss = hp.anafast(f_sdss, lmax=6)
    cl_cross = hp.anafast(f_rand, f_sdss, lmax=6)
    rho_l = cl_cross[1:7] / np.sqrt(np.maximum(1e-300, cl_rand[1:7] * cl_sdss[1:7]))

    # Radial N(z) distribution comparison
    sdss_z_hist_all, _ = np.histogram(sdss["zcmb"], bins=z_edges)
    sdss_z_hist_mask, _ = np.histogram(sdss["zcmb"][in_mask], bins=z_edges)
    p_rand = rand_z_hist / max(int(rand_z_hist.sum()), 1)
    p_sdss_mask = sdss_z_hist_mask / max(int(sdss_z_hist_mask.sum()), 1)
    radial_tvd = 0.5 * float(np.sum(np.abs(p_rand - p_sdss_mask)))

    # SDSS in_mask probit 5-fold group-blocked CV (sentinel 0 -> ungrouped singletons!)
    is_grp_sdss = (np.asarray(sdss["idgroupt17"], dtype=np.int64) > 0).astype(np.float64)
    X_sdss = np.column_stack(
        (
            np.ones(sdss["n"]),
            10.0 * np.asarray(sdss["zcmb"], dtype=np.float64) - 0.5,
            np.asarray(sdss["sn"], dtype=np.float64),
            is_grp_sdss,
        )
    )
    fit_sdss = fit_probit_with_hessian(X_sdss, in_mask)
    ref_sdss_beta = np.asarray(
        r100_ref["A4_selection_likelihood_and_4term_cov"]["empirical_probit_in_mask_sdss"]["beta_probit"],
        dtype=np.float64,
    )
    sdss_beta_err = float(np.max(np.abs(fit_sdss.beta_hat - ref_sdss_beta)))

    clusters_sdss = build_group_clusters(sdss["idgroupt17"], ungrouped_sentinel=(0, -1), secondary_keys=sdss["pgc"])
    folds_sdss = group_kfold_indices(clusters_sdss, n_splits=5, seed=42)
    from scipy.special import log_ndtr

    sdss_folds = []
    for f_id, (tr_idx, te_idx) in enumerate(folds_sdss):
        if len(np.intersect1d(clusters_sdss[tr_idx], clusters_sdss[te_idx])) != 0:
            raise AssertionError("SDSS group leakage")
        fit_tr = fit_probit_with_hessian(X_sdss[tr_idx], in_mask[tr_idx])
        sign_te = np.where(in_mask[te_idx], 1.0, -1.0)
        te_ll = float(np.sum(log_ndtr(sign_te * (X_sdss[te_idx] @ fit_tr.beta_hat))))
        sdss_folds.append(
            {
                "fold": f_id,
                "n_train": int(len(tr_idx)),
                "n_test": int(len(te_idx)),
                "n_test_out_of_mask": int(np.count_nonzero(~in_mask[te_idx])),
                "beta_train": fit_tr.beta_hat.tolist(),
                "heldout_probit_loglik": te_ll,
            }
        )

    return {
        "sdss_randoms_file": {
            "path": str(SDSS_RANDOMS_PATH),
            "header": header,
            "sha256": _sha256_file(SDSS_RANDOMS_PATH),
            "row_count": int(n_rand),
            "ra_range_deg": [ra_min, ra_max],
            "dec_range_deg": [dec_min, dec_max],
            "zcmb_range": [z_min, z_max],
            "zcmb_mean": z_sum / max(n_rand, 1),
            "nbar_range": [nb_min, nb_max],
            "nbar_mean": nb_sum / max(n_rand, 1),
        },
        "healpix_nside32_footprint_comparison": {
            "nside": nside,
            "npix_total": npix,
            "randoms_occupied_pixels": int(np.count_nonzero(rand_occ)),
            "sdss_all_occupied_pixels": int(np.count_nonzero(sdss_occ_all)),
            "sdss_in_mask_occupied_pixels": int(np.count_nonzero(sdss_occ_mask)),
            "in_mask_containment_in_randoms_frac": float(np.count_nonzero(sdss_occ_mask & rand_occ)) / max(int(np.count_nonzero(sdss_occ_mask)), 1),
            "all_containment_in_randoms_frac": float(np.count_nonzero(sdss_occ_all & rand_occ)) / max(int(np.count_nonzero(sdss_occ_all)), 1),
            "pixel_count_corr_on_randoms_footprint": corr_inmask,
            "footprint_cl_cross_corr_ell_1_to_6": [float(x) for x in rho_l],
        },
        "radial_selection_comparison": {
            "z_edges": [float(x) for x in z_edges],
            "randoms_counts_by_bin": [int(x) for x in rand_z_hist],
            "sdss_all_counts_by_bin": [int(x) for x in sdss_z_hist_all],
            "sdss_in_mask_counts_by_bin": [int(x) for x in sdss_z_hist_mask],
            "radial_total_variation_distance_in_mask": radial_tvd,
        },
        "sdss_in_mask_group_blocked_cv": {
            "n_rows": int(sdss["n"]),
            "unique_group_clusters": int(len(np.unique(clusters_sdss))),
            "r100_beta_replay_max_abs_err": sdss_beta_err,
            "beta_hat": fit_sdss.beta_hat.tolist(),
            "laplace_std": np.sqrt(np.diag(fit_sdss.cov_laplace)).tolist(),
            "full_probit_loglik": fit_sdss.loglik,
            "zero_cluster_leakage_verified": True,
            "sum_heldout_probit_loglik": float(sum(r["heldout_probit_loglik"] for r in sdss_folds)),
            "folds": sdss_folds,
        },
    }


def _cf4_36d_and_quadrant_part(r100_ref: dict[str, object]) -> dict[str, object]:
    npz_path = R100_DIR / "CF4_FULL_KBAND_COVARIANCES.npz"
    r98_j = json.loads((R98_DIR / "CF4_P1_RESULTS.json").read_text())
    sd = r99.source_design(r98_j)

    with np.load(npz_path, allow_pickle=False) as f:
        y = f["b_published_4x9"].reshape(36)
        C_tot = np.asarray(f["C_WF_R5_full_k"], dtype=np.float64)
        S_low = np.asarray(f["S_PV_WF_low_108"][:36, :36], dtype=np.float64)
        S_inh = np.asarray(f["S_PV_WF_inherited_108"][:36, :36], dtype=np.float64)
        S_high = np.asarray(f["S_PV_WF_high_108"][:36, :36], dtype=np.float64)

    C_cal_cut = np.asarray(sd[8], dtype=np.float64)
    C_sel_mag = np.asarray(sd[10], dtype=np.float64)
    C_diag_nl = C_tot - C_cal_cut - C_sel_mag - S_low - S_inh - S_high
    C_diag_nl = 0.5 * (C_diag_nl + C_diag_nl.T)

    # Verify exact 4-term + band decomposition trace identity
    budget = r100_ref["A4_selection_likelihood_and_4term_cov"]["four_term_covariance_trace_budget_WF_R5_full_k"]
    expected_diag_tr = float(budget["N_meas_trace"]) + float(budget["N_nl150_trace"])
    diag_trace_err = abs(float(np.trace(C_diag_nl)) - expected_diag_tr)
    if diag_trace_err > 1e-11:
        raise ArithmeticError(f"CF4 36D component decomposition trace error: {diag_trace_err}")

    components = {
        "diag_meas_plus_nl150": C_diag_nl,
        "cal_plus_cut": C_cal_cut,
        "sel_mag_tilt": C_sel_mag,
        "spv_low_k": S_low,
        "spv_inherited_k": S_inh,
        "spv_high_k": S_high,
    }
    x = np.tile(np.eye(9, dtype=np.float64), (2, 1))
    contrasts = predictive_contrasts(x, x)
    comp_res = component_covariance_tangents(y, components, contrasts)
    if comp_res["euler_homogeneity_errors"]["max"] > 1e-11:
        raise ArithmeticError(f"Euler homogeneity violated: {comp_res['euler_homogeneity_errors']}")

    # Independent FD verification on one selected covariance component (cal_plus_cut)
    eps = 1e-5
    plus = predictive_covariance_response(y, C_tot + eps * C_cal_cut, C_cal_cut, contrasts)
    minus = predictive_covariance_response(y, C_tot - eps * C_cal_cut, C_cal_cut, contrasts)
    fd_chi2 = (float(plus["chi2"]) - float(minus["chi2"])) / (2.0 * eps)
    fd_logd = (float(plus["log_density"]) - float(minus["log_density"])) / (2.0 * eps)
    cal_rep = comp_res["components"]["cal_plus_cut"]
    fd_err = max(abs(fd_chi2 - float(cal_rep["chi2_tangent"])), abs(fd_logd - float(cal_rep["log_density_tangent"])))

    # Selected 35,970-group sky-quadrant & Table-3 calibrator overlap census
    ids, mu, emu, cz, v, ds, wf, ramp, n_vec, vls = old.catalog()
    sel_ids = np.asarray(sd[0], dtype=np.int64)
    idx_sel = np.searchsorted(ids, sel_ids)
    if not np.array_equal(ids[idx_sel], sel_ids):
        raise ValueError("Selected 35,970 group ID lookup failed")

    t3 = r97._parse_complete_table3_for_selected(ids)
    cal_finite = np.isfinite(t3["cal_vals"])[idx_sel]
    e6_sel = t3["e_vals_6"][idx_sel]
    ra_deg = np.rad2deg(np.arctan2(n_vec[idx_sel, 1], n_vec[idx_sel, 0])) % 360.0
    ra_quads = np.floor(ra_deg / 90.0).astype(np.int64)
    quad_rows = []
    for q in range(4):
        m = ra_quads == q
        quad_rows.append(
            {
                "ra_quadrant": q,
                "ra_deg_interval": [90 * q, 90 * (q + 1)],
                "n_groups": int(np.count_nonzero(m)),
                "calibrator_overlap_count": int(np.count_nonzero(m & cal_finite)),
                "method_counts": {
                    "SNIa": int(np.count_nonzero(m & np.isfinite(e6_sel[:, 0]))),
                    "TF": int(np.count_nonzero(m & np.isfinite(e6_sel[:, 1]))),
                    "FP": int(np.count_nonzero(m & np.isfinite(e6_sel[:, 2]))),
                },
                "mean_zcmb": float(np.mean(cz[idx_sel][m] / r100.C)),
            }
        )

    return {
        "input_npz_sha256": _sha256_file(npz_path),
        "diag_trace_identity_error": diag_trace_err,
        "cal_plus_cut_fd_max_abs_err": float(fd_err),
        "predictive_36d_component_tangents": comp_res,
        "selected_35970_calibrator_and_quadrant_audit": {
            "selected_groups": int(len(idx_sel)),
            "selected_with_finite_calibrator": int(np.count_nonzero(cal_finite)),
            "quadrants": quad_rows,
        },
    }


def run_all() -> dict[str, object]:
    t0 = time.monotonic()
    r100_ref = json.loads((R100_DIR / "CF4_UPSTREAM_KBAND_RESULTS.json").read_text())
    return {
        "schema": "htt.r102.cf4_selection_holdout/1",
        "scope": (
            "SQ-CF4 source-conditional selection uncertainty propagation, 5-fold group-blocked "
            "holdout (zero cluster overlap), 4-row multi-match sensitivity, SDSS_randoms_public.dat "
            "(4M rows) selection geometry audit, and 36D CF4 component-wise predictive tangents."
        ),
        "source_qualification": "BLOCKED_INPUT",
        "physical_Pi": None,
        "physical_GF": None,
        "calibrated_p": None,
        "Bianchi_family_attribution": None,
        "part1_sixdf_holdout_and_selection_uncertainty": _sixdf_part(r100_ref),
        "part2_sdss_randoms_and_holdout": _sdss_randoms_and_holdout_part(r100_ref),
        "part3_cf4_36d_component_tangents_and_quadrants": _cf4_36d_and_quadrant_part(r100_ref),
        "runtime_seconds": time.monotonic() - t0,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args(argv)
    out = run_all()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")
    print(
        json.dumps(
            {
                "source_qualification": out["source_qualification"],
                "sixdf_r101_mix_minus_zero": out["part1_sixdf_holdout_and_selection_uncertainty"]["r101_replay_mix_minus_zero"],
                "sixdf_cv_sum_plugin": out["part1_sixdf_holdout_and_selection_uncertainty"]["five_fold_group_cv"]["sum_heldout_plugin_mix_minus_zero"],
                "sixdf_cv_sum_marginalized": out["part1_sixdf_holdout_and_selection_uncertainty"]["five_fold_group_cv"]["sum_heldout_marginalized_mix_minus_zero"],
                "sixdf_laplace_delta_std": out["part1_sixdf_holdout_and_selection_uncertainty"]["selection_uncertainty_full_cohort"]["laplace_delta_method_std"],
                "sdss_randoms_rows": out["part2_sdss_randoms_and_holdout"]["sdss_randoms_file"]["row_count"],
                "sdss_footprint_containment": out["part2_sdss_randoms_and_holdout"]["healpix_nside32_footprint_comparison"]["in_mask_containment_in_randoms_frac"],
                "cf4_euler_max_err": out["part3_cf4_36d_component_tangents_and_quadrants"]["predictive_36d_component_tangents"]["euler_homogeneity_errors"]["max"],
                "runtime_s": out["runtime_seconds"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
