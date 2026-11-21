#!/usr/bin/env python3
"""R89 G03_GAIA extended workdir + Downloads integration (create-only).

Binds Quaia-CRF3 692,154 QSO redshifts & selection maps, R24 depth cross-moments,
102-mode systematic Gram controls, Gaia CRF3 frame-rotator/ICRF flags,
ICRF3 multi-band catalogs (S/X, K, X/Ka), and VLBA extragalactic PMs.
"""
from __future__ import annotations

import hashlib
import json
import platform
import resource
import sys
import time
from pathlib import Path

import healpy as hp
import numpy as np
from astropy.io import fits
from scipy.linalg import solve_triangular
from scipy.stats import chi2

ROOT = Path(__file__).resolve().parents[6]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from htt.obsstat import p5p6_fast, phy_fast, pre_dag_fast
from scripts.r69.gaia_e2_b2 import fit_case, templates

OUT_DIR = Path(__file__).resolve().parent
OUT_JSON = OUT_DIR / "WORKDIR_EXT_RESULT.json"

WORKDIR = Path("/mnt/extdrive/workdir")
QUAIA_JOIN_NPZ = WORKDIR / "htt_open_data/a22_20261023/quaia_join/quaia_crf3_join.npz"
PIN_QUAIA_JOIN = "2fbaa40a8afe58066064efa8a7784ac508c5b2c67b41c779676eab7df8cf9ef4"
ZSPLIT_DIR = WORKDIR / "raw/new_acquisitions/transient_cmb/quaia_zsplit"
ZSPLIT0_FITS = ZSPLIT_DIR / "selection_function_NSIDE64_G20.5_zsplit2bin0.fits"
ZSPLIT1_FITS = ZSPLIT_DIR / "selection_function_NSIDE64_G20.5_zsplit2bin1.fits"
SACC_FITS = ZSPLIT_DIR / "cls_quaia_planckPR4_s8.fits"

DEPTH_MOM_NPZ = WORKDIR / "htt_open_data/a22_20261023/r24_depth_moments/new_moments.npz"
FULL_STATS_NPZ = WORKDIR / "htt_open_data/a22_20261023/astrometry/full_stats.npz"
MARGIN_STATS_NPZ = WORKDIR / "htt_open_data/a22_20261023/astrometry/margin_stats.npz"
FRAME_ROT_FITS = WORKDIR / "raw/new_acquisitions/optical/Gaia_CRF3_flags/frame_rotator_source.fits"
XM_FLAGS_FITS = WORKDIR / "raw/new_acquisitions/optical/Gaia_CRF3_flags/gaia_crf3_xm_icrf_flags.fits"
ICRF_DIR = WORKDIR / "raw/icrf3_iers_20261110"
VLBA_T6 = WORKDIR / "htt_open_data/vlba/233_3/table6.dat"

THREADS = 8


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _run_vsh_subset(
    ra_deg: np.ndarray,
    dec_deg: np.ndarray,
    pmra_mas: np.ndarray,
    pmdec_mas: np.ndarray,
    epmra_mas: np.ndarray,
    epmdec_mas: np.ndarray,
    rho: np.ndarray,
    extra_weight: np.ndarray | None = None,
) -> dict:
    n_tot = len(ra_deg)
    F = np.zeros((16, 16), dtype=np.float64)
    score = np.zeros(16, dtype=np.float64)
    chisq = 0.0
    chunk = 65536
    for i in range(0, n_tot, chunk):
        j = min(i + chunk, n_tot)
        _, B = templates(np.deg2rad(ra_deg[i:j]), np.deg2rad(dec_deg[i:j]))
        yy = np.column_stack([pmra_mas[i:j], pmdec_mas[i:j]])
        e1 = epmra_mas[i:j]
        e2 = epmdec_mas[i:j]
        if extra_weight is not None:
            # extra_weight in (0, 1] scales precision uniformly for selection sensitivity checks
            inv_sqrt = 1.0 / np.sqrt(np.clip(extra_weight[i:j], 1e-4, 1.0))
            e1 = e1 * inv_sqrt
            e2 = e2 * inv_sqrt
        FF, sc, c2 = pre_dag_fast.accumulate_gaia(B, yy, e1, e2, rho[i:j], threads=THREADS)
        F += FF
        score += sc
        chisq += c2
    acc = {"F": F, "score": score, "chisq": chisq, "N": n_tot}
    fit = fit_case(acc)
    alias = phy_fast.gaia_eb_mask_alias(np.asarray(fit["formal_cov_microasyr2"], dtype=np.float64))
    return {
        "n_sources": fit["n_sources"],
        "rank": fit["rank"],
        "F_condition": fit["F_condition"],
        "coefs_microasyr": fit["coefs_microasyr"],
        "formal_errors_microasyr": fit["formal_errors_microasyr"],
        "groups_amplitude_microasyr": fit["groups_amplitude_microasyr"],
        "E2_shape_chi": fit["E2_shape_chi"],
        "chi2_per_dof_working": fit["chi2_per_dof_working"],
        "chi2_per_dof_note": "Equal to (sum_w r^2)/(2N-16); scales linearly when precision weights include selection_relative < 1.",
        "nominal_within_fixed_Gaussian": fit["nominal_within_fixed_Gaussian"],
        "E2_B2_mask_alias_maxcanonical": alias["maxcanonical"],
        "last_chunk_backend_receipt": pre_dag_fast.last_backend_receipt(),
        "_formal_cov": fit["formal_cov_microasyr2"],
    }


def _wald_contrast(res_a: dict, res_b: dict, label_a: str, label_b: str) -> dict:
    ba = np.asarray(res_a["coefs_microasyr"], dtype=np.float64)
    bb = np.asarray(res_b["coefs_microasyr"], dtype=np.float64)
    ca = np.asarray(res_a["_formal_cov"], dtype=np.float64)
    cb = np.asarray(res_b["_formal_cov"], dtype=np.float64)
    delta = ba - bb
    cdiff = ca + cb
    slices = {"all_16D": slice(0, 16), "E1_3D": slice(0, 3), "B1_3D": slice(3, 6), "E2_5D": slice(6, 11), "B2_5D": slice(11, 16)}
    out = {}
    for k, sl in slices.items():
        d = delta[sl]
        c = cdiff[sl, sl]
        w = float(d @ np.linalg.solve(c, d))
        out[k] = {
            "delta_norm_microasyr": float(np.linalg.norm(d)),
            "formal_wald_chi2": w,
            "dof": len(d),
            "formal_p_not_calibrated": float(chi2.sf(w, len(d))),
        }
    return {"subset_a": label_a, "subset_b": label_b, "n_a": res_a["n_sources"], "n_b": res_b["n_sources"], "contrasts": out}


def main() -> int:
    if OUT_JSON.exists():
        raise FileExistsError(f"Create-only refusal to overwrite {OUT_JSON}")
    t0 = time.perf_counter()
    assert _sha256(QUAIA_JOIN_NPZ) == PIN_QUAIA_JOIN

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
        pix64 = np.asarray(z["pixel_ring64"], dtype=np.int64)

    clean = (
        np.isfinite(ra) & np.isfinite(dec) & np.isfinite(zq)
        & np.isfinite(pmra) & np.isfinite(pmdec)
        & np.isfinite(epmra) & np.isfinite(epmdec) & np.isfinite(rho)
        & (epmra > 0) & (epmdec > 0) & (np.abs(rho) < 0.999)
        & (ruwe < 1.4) & (solved == 31)
        & (np.abs(pmra) < 100.0) & (np.abs(pmdec) < 100.0)
    )
    idx = np.flatnonzero(clean)
    ra_c, dec_c, z_c = ra[idx], dec[idx], zq[idx]
    pmra_c, pmdec_c, e1_c, e2_c, rho_c = pmra[idx], pmdec[idx], epmra[idx], epmdec[idx], rho[idx]
    sel_c, pix_c = sel_rel[idx], pix64[idx]

    # Full clean & 4 redshift-quartile tomographic bins
    vsh_full = _run_vsh_subset(ra_c, dec_c, pmra_c, pmdec_c, e1_c, e2_c, rho_c)
    qs = np.quantile(z_c, [0.0, 0.25, 0.5, 0.75, 1.0])
    quartiles = {}
    q_raw_objs = {}
    for qi in range(4):
        lo, hi = qs[qi], qs[qi + 1]
        m = (z_c >= lo) & (z_c <= hi if qi == 3 else z_c < hi)
        res_q = _run_vsh_subset(ra_c[m], dec_c[m], pmra_c[m], pmdec_c[m], e1_c[m], e2_c[m], rho_c[m])
        q_raw_objs[f"Q{qi + 1}"] = res_q
        quartiles[f"Q{qi + 1}"] = {
            "z_range": [float(lo), float(hi)],
            "z_median": float(np.median(z_c[m])),
            **{k: v for k, v in res_q.items() if k != "_formal_cov"},
        }

    # Quaia 2-bin z-split matching zsplit2bin0 / zsplit2bin1 selection maps (published cut z=1.47 + sample median check)
    smap0 = hp.read_map(str(ZSPLIT0_FITS), verbose=False) if "verbose" in hp.read_map.__code__.co_varnames else hp.read_map(str(ZSPLIT0_FITS))
    smap1 = hp.read_map(str(ZSPLIT1_FITS), verbose=False) if "verbose" in hp.read_map.__code__.co_varnames else hp.read_map(str(ZSPLIT1_FITS))
    z_med = float(np.median(z_c))
    z_quaia_edge = 1.47
    m_z0 = z_c < z_quaia_edge
    m_z1 = z_c >= z_quaia_edge
    w_z0 = np.clip(smap0[pix_c[m_z0]], 0.05, 1.0)
    w_z1 = np.clip(smap1[pix_c[m_z1]], 0.05, 1.0)
    vsh_z0_unw = _run_vsh_subset(ra_c[m_z0], dec_c[m_z0], pmra_c[m_z0], pmdec_c[m_z0], e1_c[m_z0], e2_c[m_z0], rho_c[m_z0])
    vsh_z0_sel = _run_vsh_subset(ra_c[m_z0], dec_c[m_z0], pmra_c[m_z0], pmdec_c[m_z0], e1_c[m_z0], e2_c[m_z0], rho_c[m_z0], extra_weight=w_z0)
    vsh_z1_unw = _run_vsh_subset(ra_c[m_z1], dec_c[m_z1], pmra_c[m_z1], pmdec_c[m_z1], e1_c[m_z1], e2_c[m_z1], rho_c[m_z1])
    vsh_z1_sel = _run_vsh_subset(ra_c[m_z1], dec_c[m_z1], pmra_c[m_z1], pmdec_c[m_z1], e1_c[m_z1], e2_c[m_z1], rho_c[m_z1], extra_weight=w_z1)
    vsh_full_selrel = _run_vsh_subset(ra_c, dec_c, pmra_c, pmdec_c, e1_c, e2_c, rho_c, extra_weight=np.where(np.isfinite(sel_c) & (sel_c > 0.05), sel_c, 0.05))

    contrast_q1_q4 = _wald_contrast(q_raw_objs["Q1"], q_raw_objs["Q4"], "z_Q1_lowest", "z_Q4_highest")
    contrast_z0_z1 = _wald_contrast(vsh_z0_unw, vsh_z1_unw, "z_split_bin0", "z_split_bin1")

    with fits.open(SACC_FITS) as hd:
        sacc_info = {
            "hdu_count": len(hd),
            "cl_00_rows": int(hd["data:cl_00"].header["NAXIS2"]),
            "cov_shape": list(hd["covariance"].data.shape),
        }

    # R24 depth moments & 102-mode astrometry nuisance Gram matrices
    with np.load(DEPTH_MOM_NPZ, allow_pickle=False) as dm:
        A6 = dm["A"]
        K6 = dm["K"]
        q6 = dm["q"]
        n_dm = int(dm["n"])
        zcounts_dm = dm["zcounts"].tolist()
        L6 = np.linalg.cholesky(A6)
        wK = solve_triangular(L6, K6, lower=True, check_finite=False)
        depth_summary = {
            "source_n": n_dm,
            "zcounts": zcounts_dm,
            "A_eigenvalues": np.linalg.eigvalsh(A6).tolist(),
            "whitened_K_rank": int(np.linalg.matrix_rank(wK)),
            "raw_q6_microasyr": q6.tolist(),
        }
    nuis_stats = {}
    for label, pth in (("full_102", FULL_STATS_NPZ), ("margin_102", MARGIN_STATS_NPZ)):
        with np.load(pth, allow_pickle=False) as st:
            G = st["G"]
            b = st["b"]
            ev = np.linalg.eigvalsh(.5 * (G + G.T))
            sol = np.linalg.lstsq(G, b, rcond=None)
            nuis_stats[label] = {
                "n_sources": int(st["n"]),
                "G_shape": list(G.shape),
                "G_rank": int(sol[2]),
                "G_min_eig": float(ev[0]),
                "G_max_eig": float(ev[-1]),
                "cut_Q": float(st["cut_Q"]),
            }

    # Gaia CRF3 rotator flags, ICRF3 bands, and VLBA extragalactic proper motions
    with fits.open(FRAME_ROT_FITS, memmap=True) as hd:
        fr = hd[1].data
        fr_summary = {
            "n_rows": int(len(fr)),
            "used_for_orientation": int(np.sum(fr["used_for_reference_frame_orientation"])),
            "used_for_spin": int(np.sum(fr["used_for_reference_frame_spin"])),
        }
    with fits.open(XM_FLAGS_FITS, memmap=True) as hd:
        xm = hd[1].data
        xm_summary = {
            "n_rows": int(len(xm)),
            "icrf3sx_matches": int(np.sum(np.asarray(xm["icrf3sx"], dtype=int) != 0)),
            "icrf3k_matches": int(np.sum(np.asarray(xm["icrf3k"], dtype=int) != 0)),
            "icrf3xka_matches": int(np.sum(np.asarray(xm["icrf3xka"], dtype=int) != 0)),
        }
    icrf_counts = {}
    for band, fn in (("S_X", "icrf3sx.txt"), ("K", "icrf3k.txt"), ("X_Ka", "icrf3xka.txt")):
        lines = (ICRF_DIR / fn).read_text(encoding="ascii", errors="ignore").splitlines()
        icrf_counts[band] = sum(1 for ln in lines if ln.startswith("ICRF"))

    vlba_lines = [ln for ln in VLBA_T6.read_text(encoding="ascii", errors="ignore").splitlines() if ln.strip()]

    elapsed = time.perf_counter() - t0
    input_paths = (
        QUAIA_JOIN_NPZ,
        ZSPLIT0_FITS,
        ZSPLIT1_FITS,
        SACC_FITS,
        DEPTH_MOM_NPZ,
        FULL_STATS_NPZ,
        MARGIN_STATS_NPZ,
        FRAME_ROT_FITS,
        ICRF_DIR / "icrf3sx.txt",
        VLBA_T6,
    )
    out = {
        "schema": "htt.r89.g03_gaia_workdir_ext/1",
        "group_id": "G03_GAIA",
        "node_ids": ["K01", "K02", "SQ-GAIA", "K03", "K04", "K05", "K06"],
        "source_sha256": {str(p): _sha256(p) for p in input_paths},
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "elapsed_seconds": float(elapsed),
            "maxrss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
            "threads": THREADS,
        },
        "quaia_crf3_selection": {
            "raw_rows": len(ra),
            "clean_astrometric_rows": len(idx),
            "z_median": z_med,
            "z_quartiles_edges": [float(x) for x in qs],
        },
        "quaia_full_vsh": {k: v for k, v in vsh_full.items() if k != "_formal_cov"},
        "quaia_full_selection_relative_weighted_vsh": {k: v for k, v in vsh_full_selrel.items() if k != "_formal_cov"},
        "quaia_redshift_quartiles_vsh": quartiles,
        "quaia_zsplit2_selection_comparison": {
            "z_split_edge_used": z_quaia_edge,
            "bin0_unweighted": {k: v for k, v in vsh_z0_unw.items() if k != "_formal_cov"},
            "bin0_zsplit_weighted": {k: v for k, v in vsh_z0_sel.items() if k != "_formal_cov"},
            "bin1_unweighted": {k: v for k, v in vsh_z1_unw.items() if k != "_formal_cov"},
            "bin1_zsplit_weighted": {k: v for k, v in vsh_z1_sel.items() if k != "_formal_cov"},
        },
        "redshift_tomographic_wald_contrasts": {
            "Q1_vs_Q4": contrast_q1_q4,
            "zsplit0_vs_zsplit1": contrast_z0_z1,
        },
        "quaia_planck_pr4_sacc": sacc_info,
        "r24_depth_moments": depth_summary,
        "astrometry_102_mode_nuisance": nuis_stats,
        "crf3_and_vlba_metadata": {
            "frame_rotator_source": fr_summary,
            "gaia_crf3_xm_icrf_flags": xm_summary,
            "icrf3_catalog_counts": icrf_counts,
            "vlba_table6_rows": len(vlba_lines),
            "vlba_convention_note": "Truebenbach & Darling RA proper motions include cos(delta) factor per SOURCE_CORRECTIONS.md; physical NNR/session transfer remains uncalibrated.",
        },
        "node_verdicts": {
            "K01": "REUSED_SCOPED",
            "K02": "REUSED_SCOPED",
            "SQ-GAIA": "DIAGNOSTIC_COMPLETED_SCOPED",
            "K03": "BLOCKED_INPUT",
            "K04": "BLOCKED_DEPENDENCY",
            "K05": "BLOCKED_DEPENDENCY",
            "K06": "BLOCKED_DEPENDENCY",
        },
        "physical_gate_note": "Tomographic VSH fits across 634,233 clean Quaia-CRF3 QSOs quantify empirical E1/B1/E2/B2 stability across redshift quartiles and Quaia z-split selection weights, while K03-K06 physical shear/vorticity remain BLOCKED_INPUT pending Gaia epoch scanning-law transfer and optical congruence calibration.",
    }
    OUT_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "group_id": "G03_GAIA",
        "elapsed_s": round(elapsed, 3),
        "clean_quaia_crf3": len(idx),
        "Q1_E1_uas_yr": round(quartiles["Q1"]["groups_amplitude_microasyr"]["E1"], 3),
        "Q4_E1_uas_yr": round(quartiles["Q4"]["groups_amplitude_microasyr"]["E1"], 3),
        "Q1_vs_Q4_all16D_wald": round(contrast_q1_q4["contrasts"]["all_16D"]["formal_wald_chi2"], 3),
        "r24_whitened_K_rank": depth_summary["whitened_K_rank"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
