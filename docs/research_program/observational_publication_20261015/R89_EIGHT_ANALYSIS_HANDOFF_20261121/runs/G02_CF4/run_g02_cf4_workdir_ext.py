#!/usr/bin/env python3
"""R89 G02_CF4 extended workdir + Downloads integration (create-only).

Connects previously unreferenced /mnt/extdrive/workdir CF4-upstream & grid assets
and /home/cosmosapjw/Downloads/htt_r89_downloads/Measuring_bulkflows to G02_CF4
diagnostics without overwriting RESULT.json or weakening P0-B / P0-C / H02 gates.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import os
import platform
import resource
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
from astropy.io import fits

ROOT = Path(__file__).resolve().parents[6]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from htt.obsstat import cf4_p0b
from htt.obsstat.affine_flow import curl_injection_recovery, fit_affine_flow
from scripts.r88.run_p0c import build_packet as r88_build_packet

OUT_DIR = Path(__file__).resolve().parent
OUT_JSON = OUT_DIR / "WORKDIR_EXT_RESULT.json"

WORKDIR = Path("/mnt/extdrive/workdir")
DL_DIR = Path("/home/cosmosapjw/Downloads/htt_r89_downloads/Measuring_bulkflows/Measuring_bulkflows-main")

T2_PATH = WORKDIR / "raw/cf4_full/table2.dat"
T2_PIN_SHA = "8e908928e68352b59292cf67020a4d70aaa6d30f278dfa6aa3e41a9df808332f"
CF4PP_NPZ = WORKDIR / "raw/cf4/CF4pp_mean_std_grids.npz"
CF4GP_FITS = WORKDIR / "htt_open_data/cf4/d06_flow_20261018/CF4gp_new_64-z008_velocity.fits"
CF4_D03_CSV = WORKDIR / "htt_open_data/cf4/d06_flow_20261018/D03_HOST_FLOW_QUERIES.csv"
SDSS_PV_DAT = WORKDIR / "raw/sdss_pv_zenodo_6824749/SDSS_PV_public.dat"
SDSS_MOCK_DIR = WORKDIR / "htt_open_data/sdss_source_null_20261018/analysis_selected"
SIXDF_FP_GZ = WORKDIR / "htt_open_data/a22_20261023/6df/FP_table8.dat.gz"
SIXDF_PV_GZ = WORKDIR / "htt_open_data/a22_20261023/6df/PV_table1.dat.gz"
DESI_FP_CSV = WORKDIR / "raw/new_acquisitions/optical/DESI_PV_Fuji_FP/DESI_FP_logdists_fiducial.csv"
PANTHEON_DIR = WORKDIR / "raw/pantheonplus_release_c447f0f_20261110"
SHOES_COV_FITS = WORKDIR / "raw/shoes2022_calibration_reference_20261015/allc_shoes_ceph_topantheonwt6.0_112221.fits"
R27_FAC_RES = WORKDIR / "htt_open_data/r27_cf4_exact_calibration_factor_numeric/metadata_repair_run/actual_run/products/RESULT.json"
R27_M7_RES = WORKDIR / "htt_open_data/r27_cf4_m7_covariance_application/actual_run/products/RESULT.json"
R26_FP_RES = WORKDIR / "htt_open_data/r26_cf4_fp_pooling_closure/RESULT.json"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _parse_cf4_table2(selected_gids: set[int]) -> dict:
    # 1-based CDS ReadMe -> 0-based Python slices for table2.dat
    method_slices = {
        "SNIa": (41, 47),
        "TF": (53, 59),
        "FP": (65, 71),
        "SBF": (77, 83),
        "SNII": (90, 96),
        "TRGB": (102, 107),
        "Ceph": (113, 119),
        "MASER": (126, 131),
    }
    n_rows = 0
    in_sel = 0
    meth_counts_all = Counter()
    meth_counts_sel = Counter()
    g_gal_counts = Counter()
    g_dms: dict[int, list[float]] = {}

    with T2_PATH.open("r", encoding="ascii") as f:
        for line in f:
            if not line.strip():
                continue
            n_rows += 1
            gid = int(line[8:15].strip())
            dm = float(line[28:34].strip())
            in_group = gid in selected_gids
            if in_group:
                in_sel += 1
                g_gal_counts[gid] += 1
                g_dms.setdefault(gid, []).append(dm)
            for mname, (a, b) in method_slices.items():
                if line[a:b].strip():
                    meth_counts_all[mname] += 1
                    if in_group:
                        meth_counts_sel[mname] += 1

    mult_vals = np.array(list(g_gal_counts.values()), dtype=int)
    within_rms = [float(np.std(vals, ddof=1)) for vals in g_dms.values() if len(vals) >= 2]
    return {
        "table2_rows": n_rows,
        "rows_in_selected_35970_groups": in_sel,
        "selected_groups_matched_in_table2": len(g_gal_counts),
        "multiplicity_distribution_in_selected_groups": {
            "singleton_1_gal": int(np.sum(mult_vals == 1)),
            "pairs_to_4_gal": int(np.sum((mult_vals >= 2) & (mult_vals <= 4))),
            "rich_ge5_gal": int(np.sum(mult_vals >= 5)),
            "max_galaxies_in_group": int(mult_vals.max()),
            "multi_galaxy_group_count": len(within_rms),
            "median_within_group_dm_std_mag": float(np.median(within_rms)) if within_rms else None,
            "p90_within_group_dm_std_mag": float(np.percentile(within_rms, 90)) if within_rms else None,
        },
        "method_galaxy_counts_all_55877": dict(meth_counts_all),
        "method_galaxy_counts_selected_35970_groups": dict(meth_counts_sel),
    }


def _analyze_cf4pp_and_gp() -> dict:
    with np.load(CF4PP_NPZ, allow_pickle=False) as z:
        v_mean = np.asarray(z["v_mean_CF4pp"], dtype=np.float64)
        v_std = np.asarray(z["v_std_CF4pp"], dtype=np.float64)
        vr_mean = np.asarray(z["vr_mean_CF4pp"], dtype=np.float64)
        vr_std = np.asarray(z["vr_std_CF4pp"], dtype=np.float64)

    n = v_mean.shape[1]
    box = 1000.0
    delta = box / n
    axis = (np.arange(n) + 0.5) * delta - box / 2.0
    gx, gy, gz = np.meshgrid(axis, axis, axis, indexing="ij")
    r2 = gx * gx + gy * gy + gz * gz

    shells = {}
    r_safe = np.maximum(np.sqrt(r2), 1e-12)
    rx, ry, rz = gx / r_safe, gy / r_safe, gz / r_safe
    vr_from_vmean = v_mean[0] * rx + v_mean[1] * ry + v_mean[2] * rz
    vr_std_radial = np.sqrt((v_std[0] * rx) ** 2 + (v_std[1] * ry) ** 2 + (v_std[2] * rz) ** 2)
    for rad in (75.0, 100.0, 150.0, 200.0):
        sel = r2 <= rad * rad
        pos = np.column_stack([gx[sel], gy[sel], gz[sel]])
        vm = np.column_stack([v_mean[0][sel], v_mean[1][sel], v_mean[2][sel]])
        fit = fit_affine_flow(pos, vm)
        inj = curl_injection_recovery(
            pos, vm, radius=rad + 1.0, omega_inject=np.array([2.0, -2.0, 2.0])
        )
        vr_rms_mean = float(np.sqrt(np.mean(vr_std_radial[sel] ** 2)))
        vr_abs_mean = float(np.sqrt(np.mean(vr_from_vmean[sel] ** 2)))
        shells[f"R_{int(rad)}_Mpc_h"] = {
            "n_cells": int(pos.shape[0]),
            "bulk_velocity_sg_kms": fit.bulk.tolist(),
            "bulk_amplitude_kms": float(fit.bulk_amplitude),
            "affine_expansion_h_kms_Mpc": float(fit.expansion),
            "affine_shear_amplitude_h_kms_Mpc": float(fit.shear_amplitude),
            "wf_mean_vorticity_amplitude_h_kms_Mpc": float(fit.vorticity_amplitude),
            "curl_injection_recovery_rel_err": float(inj["rel_error"]),
            "grid_vr_from_vmean_rms_kms": vr_abs_mean,
            "grid_vr_std_from_vstd_rms_kms": vr_rms_mean,
        }

    with fits.open(CF4GP_FITS, memmap=True) as hd:
        gp_shape = list(hd[0].data.shape)
    with CF4_D03_CSV.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        d03_rows = list(r)
    valid_vr = [float(row["vr_rms_kms"]) for row in d03_rows if row.get("vr_rms_kms")]
    h_ratios = [
        float(row["CF4_Vcmb_kms"]) / float(np.hypot(np.hypot(float(row["SGX"]), float(row["SGY"])), float(row["SGZ"])))
        for row in d03_rows
        if row.get("SGX") and float(row["CF4_Vcmb_kms"]) > 0
    ]
    return {
        "cf4pp_box_Mpc_h": box,
        "cf4pp_grid_shape": list(v_mean.shape),
        "supergalactic_affine_shells": shells,
        "cf4gp_velocity_shape": gp_shape,
        "d03_host_flow_queries": {
            "row_count": len(d03_rows),
            "median_vr_rms_kms": float(np.median(valid_vr)),
            "p90_vr_rms_kms": float(np.percentile(valid_vr, 90)),
            "verified_H0_grid_ratio_Vcmb_over_r_h": float(np.median(h_ratios)) if h_ratios else None,
        },
        "structural_note": "Box and cell coordinates are in Mpc/h (D03 Vcmb/r = 100.0 km/s/(Mpc/h)). Wiener-filter CF4++ velocity field is curl-suppressed by potential-flow prior; provides scale comparison (~150-220 km/s cell std vs R87 constant sigma_v), NOT upstream group-level S_PV.",
    }


def _analyze_upstream_surveys_and_mocks() -> dict:
    # 1. SDSS PV observed
    ra_s, dec_s, z_s, eta_s, eeta_s = [], [], [], [], []
    with SDSS_PV_DAT.open("r", encoding="utf-8") as f:
        hdr = f.readline().lstrip("#").split()
        idx_ra = hdr.index("RA")
        idx_dec = hdr.index("Dec")
        idx_z = hdr.index("zcmb")
        idx_eta = hdr.index("logdist")
        idx_eeta = hdr.index("logdist_err")
        for line in f:
            if not line.strip() or line.startswith("#"):
                continue
            p = line.split()
            ra_s.append(float(p[idx_ra]))
            dec_s.append(float(p[idx_dec]))
            z_s.append(float(p[idx_z]))
            eta_s.append(float(p[idx_eta]))
            eeta_s.append(float(p[idx_eeta]))
    ra_sa, dec_sa = np.deg2rad(ra_s), np.deg2rad(dec_s)
    eta_sa, eeta_sa = np.asarray(eta_s), np.asarray(eeta_s)
    w_s = 1.0 / (eeta_sa ** 2 + 1e-8)
    n_s = np.column_stack([np.cos(dec_sa) * np.cos(ra_sa), np.cos(dec_sa) * np.sin(ra_sa), np.sin(dec_sa)])
    X_s = np.column_stack([np.ones(len(n_s)), n_s])
    beta_sdss = np.linalg.solve((X_s.T * w_s) @ X_s, X_s.T @ (w_s * eta_sa))

    # 2. SDSS 24 HAM/HOD mocks (subset of 166 or R19001..R19024)
    mock_files = sorted(SDSS_MOCK_DIR.glob("MOCK_HAMHOD_SDSS_v5_R190*.0_err_corr"))
    mock_betas = []
    mock_counts = []
    for mf in mock_files[:24]:
        with mf.open("r", encoding="utf-8") as f:
            r = csv.DictReader(f)
            mra, mdec, meta, meeta = [], [], [], []
            for row in r:
                mra.append(float(row["RA"]))
                mdec.append(float(row["Dec"]))
                meta.append(float(row["logdist"]))
                meeta.append(float(row["logdist_err"]))
        mra_a, mdec_a = np.deg2rad(mra), np.deg2rad(mdec)
        meta_a, meeta_a = np.asarray(meta), np.asarray(meeta)
        wm = 1.0 / (meeta_a ** 2 + 1e-8)
        nm = np.column_stack([np.cos(mdec_a) * np.cos(mra_a), np.cos(mdec_a) * np.sin(mra_a), np.sin(mdec_a)])
        Xm = np.column_stack([np.ones(len(nm)), nm])
        bm = np.linalg.solve((Xm.T * wm) @ Xm, Xm.T @ (wm * meta_a))
        mock_betas.append(bm)
        mock_counts.append(len(nm))
    mock_betas_a = np.asarray(mock_betas)
    mock_cov = np.cov(mock_betas_a, rowvar=False) if len(mock_betas_a) > 1 else None

    # 3. 6dFGS + DESI Fuji FP
    with gzip.open(SIXDF_FP_GZ, "rt", encoding="ascii") as f:
        n_6df_fp = sum(1 for ln in f if ln.strip())
    with gzip.open(SIXDF_PV_GZ, "rt", encoding="ascii") as f:
        n_6df_pv = sum(1 for ln in f if ln.strip())
    desi_z, desi_eta = [], []
    with DESI_FP_CSV.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            desi_z.append(float(row["zcmb"]))
            desi_eta.append(float(row["logdist"]))

    return {
        "sdss_pv": {
            "n_galaxies": len(eta_sa),
            "zcmb_range": [float(min(z_s)), float(max(z_s))],
            "weighted_logdist_monopole_and_icrs_dipole": beta_sdss.tolist(),
            "dipole_amp_logdist": float(np.linalg.norm(beta_sdss[1:])),
        },
        "sdss_hamhod_mocks_sample24": {
            "total_mock_files_in_dir": len(list(SDSS_MOCK_DIR.glob("MOCK_HAMHOD_SDSS_v5_*"))),
            "evaluated_mock_count": len(mock_betas_a),
            "n_galaxies_range": [int(min(mock_counts)), int(max(mock_counts))],
            "mean_monopole_dipole": np.mean(mock_betas_a, axis=0).tolist(),
            "std_monopole_dipole": np.std(mock_betas_a, axis=0, ddof=1).tolist(),
            "cov_diag": np.diag(mock_cov).tolist() if mock_cov is not None else None,
        },
        "sixdf_gs": {"fp_table8_rows": n_6df_fp, "pv_table1_rows": n_6df_pv},
        "desi_fuji_fp": {
            "n_galaxies": len(desi_eta),
            "zcmb_range": [float(min(desi_z)), float(max(desi_z))],
            "median_logdist": float(np.median(desi_eta)),
        },
    }


def _read_pantheon_cov(path: Path) -> np.ndarray:
    with path.open("r", encoding="utf-8") as f:
        n = int(f.readline().strip())
        vals = np.fromfile(f, sep=" ", dtype=np.float64)
    return vals.reshape((n, n))


def _analyze_pantheon_shoes_and_r27() -> dict:
    with (PANTHEON_DIR / "Pantheon+SH0ES.dat").open("r", encoding="utf-8") as f:
        hdr = f.readline().split()
        rows = [ln.split() for ln in f if ln.strip()]
    n_sn = len(rows)
    cov_full = _read_pantheon_cov(PANTHEON_DIR / "Pantheon+SH0ES_STAT+SYS.cov")
    cov_stat = _read_pantheon_cov(PANTHEON_DIR / "Pantheon+SH0ES_STATONLY.cov")
    cov_vpec_file = _read_pantheon_cov(PANTHEON_DIR / "sytematic_groupings/Pantheon+SH0ES_122221_VPEC.cov")
    cov_calib_file = _read_pantheon_cov(PANTHEON_DIR / "sytematic_groupings/Pantheon+SH0ES_122221_CALIB.cov")
    cov_mwebv_file = _read_pantheon_cov(PANTHEON_DIR / "sytematic_groupings/Pantheon+SH0ES_122221_MWEBV.cov")

    cov_sys = cov_full - cov_stat
    # In Pantheon+ release, 122221_*.cov files include only that systematic group on the 122221 stat baseline,
    # whereas STATONLY.cov differs at 1,409 diagonal entries. Compare leave-one-out against STAT+SYS directly.
    diff_ss_minus_vpec = cov_full - cov_vpec_file
    diff_ss_minus_calib = cov_full - cov_calib_file
    tr_full = float(np.trace(cov_full))
    tr_stat = float(np.trace(cov_stat))
    tr_sys = float(np.trace(cov_sys))
    tr_vpec_file = float(np.trace(cov_vpec_file))
    tr_calib_file = float(np.trace(cov_calib_file))
    tr_mwebv_file = float(np.trace(cov_mwebv_file))
    # Estimate clean within-122221 VPEC and CALIB systematic excess above MWEBV near-stat baseline
    tr_vpec_above_mwebv = float(tr_vpec_file - tr_mwebv_file)
    tr_calib_above_mwebv = float(tr_calib_file - tr_mwebv_file)

    with fits.open(SHOES_COV_FITS, memmap=True) as hd:
        shoes_shape = list(hd[0].data.shape)
        shoes_diag_min = float(np.min(np.diag(hd[0].data)))
        shoes_diag_max = float(np.max(np.diag(hd[0].data)))

    r27_fac = json.loads(R27_FAC_RES.read_text(encoding="utf-8"))
    r27_m7 = json.loads(R27_M7_RES.read_text(encoding="utf-8"))
    r26_fp = json.loads(R26_FP_RES.read_text(encoding="utf-8"))

    # Measuring_bulkflows downloaded reference mock & results
    mock_rows = np.loadtxt(DL_DIR / "example_surveymock.dat")
    mle_txt = [line.split() for line in (DL_DIR / "BF_MLE_result.txt").read_text().strip().splitlines()]
    mve_txt = [line.split() for line in (DL_DIR / "BF_MVE_result.txt").read_text().strip().splitlines()]

    return {
        "pantheon_plus": {
            "n_rows": n_sn,
            "n_columns": len(hdr),
            "trace_stat_sys": tr_full,
            "trace_stat_only": tr_stat,
            "trace_sys_diff_raw": tr_sys,
            "trace_stat_plus_vpec_file": tr_vpec_file,
            "trace_stat_plus_calib_file": tr_calib_file,
            "trace_stat_plus_mwebv_file": tr_mwebv_file,
            "trace_stat_sys_minus_vpec": float(np.trace(diff_ss_minus_vpec)),
            "trace_stat_sys_minus_calib": float(np.trace(diff_ss_minus_calib)),
            "min_diag_stat_sys_minus_vpec": float(np.min(np.diag(diff_ss_minus_vpec))),
            "min_diag_stat_sys_minus_calib": float(np.min(np.diag(diff_ss_minus_calib))),
            "vpec_excess_over_mwebv_trace": tr_vpec_above_mwebv,
            "calib_excess_over_mwebv_trace": tr_calib_above_mwebv,
            "vpec_excess_fraction_of_mwebv_gap": float(tr_vpec_above_mwebv / (tr_full - tr_mwebv_file)),
            "calib_excess_fraction_of_mwebv_gap": float(tr_calib_above_mwebv / (tr_full - tr_mwebv_file)),
            "baseline_caveat": "122221_*.cov files share the 122221 statistical baseline while STATONLY.cov differs at 1,409 diagonals; differences against STAT+SYS have strictly positive diagonals whereas differences against STATONLY are indefinite.",
        },
        "shoes_2022": {
            "allc_shape": shoes_shape,
            "diag_min_mag2": shoes_diag_min,
            "diag_max_mag2": shoes_diag_max,
        },
        "r27_cf4_calibration_factor": {
            "status": r27_fac.get("status"),
            "factor_product_sha256": r27_fac.get("factor_product_sha256"),
            "channel_row_counts": r27_fac.get("channel_row_counts"),
        },
        "r27_cf4_m7_covariance_profiles": {
            "status": r27_m7.get("status"),
            "physical_confidence_status": r27_m7.get("physical_confidence_status"),
            "selected_rows": r27_m7.get("selected_rows"),
        },
        "r26_cf4_fp_pooling_closure": {
            "scientific_admission": r26_fp.get("scientific_admission"),
            "simultaneous_modulus_error_feasibility": r26_fp.get("simultaneous_modulus_error_feasibility"),
        },
        "downloaded_measuring_bulkflows_reference": {
            "example_surveymock_shape": list(mock_rows.shape),
            "example_mock_ra_range_deg": [float(mock_rows[:, 0].min()), float(mock_rows[:, 0].max())],
            "example_mock_z_range": [float(mock_rows[:, 2].min()), float(mock_rows[:, 2].max())],
            "bf_mle_vector_kms": [float(x) for x in mle_txt[0]],
            "bf_mve_vector_kms": [float(x) for x in mve_txt[0]],
        },
    }


def main() -> int:
    if OUT_JSON.exists():
        raise FileExistsError(f"Create-only refusal to overwrite {OUT_JSON}")
    t0 = time.perf_counter()
    s = cf4_p0b.load_cf4_method_source()
    assert cf4_p0b.validate_source_identity(s)
    assert _sha256(T2_PATH) == T2_PIN_SHA
    p0c_packet = r88_build_packet("SQ-CF4")
    assert p0c_packet["status"] == "BLOCKED_INPUT"

    sel_gids = set(s.group_id.tolist())
    t2_diag = _parse_cf4_table2(sel_gids)
    grid_diag = _analyze_cf4pp_and_gp()
    survey_diag = _analyze_upstream_surveys_and_mocks()
    cov_diag = _analyze_pantheon_shoes_and_r27()
    elapsed = time.perf_counter() - t0

    input_paths = (
        T2_PATH,
        CF4PP_NPZ,
        CF4GP_FITS,
        CF4_D03_CSV,
        SDSS_PV_DAT,
        SIXDF_FP_GZ,
        SIXDF_PV_GZ,
        DESI_FP_CSV,
        PANTHEON_DIR / "Pantheon+SH0ES.dat",
        PANTHEON_DIR / "Pantheon+SH0ES_STAT+SYS.cov",
        SHOES_COV_FITS,
        DL_DIR / "example_surveymock.dat",
    )
    out = {
        "schema": "htt.r89.g02_cf4_workdir_ext/1",
        "group_id": "G02_CF4",
        "node_ids": ["H01", "H03", "SQ-CF4", "H02", "H04", "H05", "H06"],
        "source_sha256": {str(p): _sha256(p) for p in input_paths if p.stat().st_size < 250_000_000},
        "source_bytes": {str(p): p.stat().st_size for p in input_paths},
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "elapsed_seconds": float(elapsed),
            "maxrss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        },
        "cf4_table2_galaxy_to_selected_group": t2_diag,
        "cf4pp_and_gp_velocity_fields": grid_diag,
        "upstream_survey_and_sdss_mock_diagnostics": survey_diag,
        "pantheon_shoes_r27_and_bulkflow_reference": cov_diag,
        "p0c_fail_closed_gate": {"node": "SQ-CF4", "status": p0c_packet["status"]},
        "sq_cf4_r87_diagnostic_status": "DIAGNOSTIC_COMPLETED_SCOPED",
        "sq_cf4_r78_physical_gate": "BLOCKED_INPUT",
        "node_verdicts": {
            "H01": "REUSED_SCOPED",
            "H03": "REUSED_SCOPED",
            "SQ-CF4": "BLOCKED_INPUT",
            "H02": "BLOCKED_INPUT",
            "H04": "BLOCKED_DEPENDENCY",
            "H05": "BLOCKED_DEPENDENCY",
            "H06": "BLOCKED_DEPENDENCY",
        },
        "physical_gate_note": "Adding workdir constituent tables/grids/mocks and Measuring_bulkflows confirms constituent heterogeneity and scale (~150-220 km/s cell std), while preserving BLOCKED_INPUT on SQ-CF4/H02 until full unpooled 35,970-group S_PV + J_cal Sigma_cal J_cal^T + C_selection are supplied.",
    }
    OUT_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "group_id": "G02_CF4",
        "elapsed_s": round(elapsed, 3),
        "table2_rows": t2_diag["table2_rows"],
        "t2_selected_matched_groups": t2_diag["selected_groups_matched_in_table2"],
        "cf4pp_R100_bulk_kms": round(grid_diag["supergalactic_affine_shells"]["R_100_Mpc_h"]["bulk_amplitude_kms"], 2),
        "sdss_mocks_evaluated": survey_diag["sdss_hamhod_mocks_sample24"]["evaluated_mock_count"],
        "pantheon_vpec_excess_frac": round(cov_diag["pantheon_plus"]["vpec_excess_fraction_of_mwebv_gap"], 4),
        "sq_cf4_gate": p0c_packet["status"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
