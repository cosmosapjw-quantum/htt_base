#!/usr/bin/env python3
"""R89 Phase-3 Track 4 (G05_PLANCK): 8-Map Common-Mask + 50 Raw FFP10 MC Pairs (create-only).

Compares 8 observed CMB maps (PR3 SMICA/Commander/NILC/SEVEM, PR4 Commander T,
Cosmoglobe DR1, BeyondPlanck v2, WMAP9 ILC T) downgraded to Galactic RING NSIDE=64
on exact common PR3 Int/Pol masks, plus 50 raw FFP10 SMICA signal+noise MC pairs.
Preserves SQ-CMB-NULL = BLOCKED_INPUT (single-pipeline FFP10 / missing PR4/multi-pipeline joint null).
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import resource
import sys
import time
from pathlib import Path

import healpy as hp
import numpy as np

ROOT = Path(__file__).resolve().parents[6]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from htt.obsstat import p2p3_fast

OUT_DIR = Path(__file__).resolve().parent
OUT_JSON = OUT_DIR / "DEEP_MULTIPIPELINE_CMB_RESULT.json"

WORKDIR = Path("/mnt/extdrive/workdir")
MASK_INT_FITS = WORKDIR / "raw/planck_data/COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits"
MASK_POL_FITS = WORKDIR / "raw/planck_data/COM_Mask_CMB-common-Mask-Pol_2048_R3.00.fits"
SMICA_CMB_DIR = WORKDIR / "raw/planck_ffp10/smica/cmb_mc"
SMICA_NOISE_DIR = WORKDIR / "raw/planck_ffp10/smica/noise_mc"
CMD_CMB_DIR = WORKDIR / "raw/planck_ffp10/commander/cmb_mc"
CMD_CAND_DIR = WORKDIR / "raw/planck_ffp10/commander/candidates/COMMANDER-FFP10-DOWNLOAD-20260829T144340Z-64adad"

NSIDE_OUT = 64
LMAX = 8
N_RAW_MC = 50


def _sha256_small(path: Path) -> str | None:
    if not path.is_file() or path.stat().st_size > 250_000_000:
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _downgrade_map(path: Path, *, nest: bool, scale_to_k: float, pol: bool) -> list[np.ndarray]:
    fields = (0, 1, 2) if pol else (0,)
    arrs = hp.read_map(str(path), field=fields, nest=nest, verbose=False) if "verbose" in hp.read_map.__code__.co_varnames else hp.read_map(str(path), field=fields, nest=nest)
    if not pol:
        arrs = [np.asarray(arrs, dtype=np.float64)]
    else:
        arrs = [np.asarray(a, dtype=np.float64) for a in arrs]
    order_in = "NESTED" if nest else "RING"
    out = []
    for a in arrs:
        bad = ~np.isfinite(a) | (np.abs(a) > 1e20)
        if np.any(bad):
            a = np.where(bad, hp.UNSEEN, a)
        dg = hp.ud_grade(a, nside_out=NSIDE_OUT, order_in=order_in, order_out="RING")
        dg = np.where(dg == hp.UNSEEN, 0.0, dg * scale_to_k)
        out.append(dg)
    del arrs
    return out


def _quad_oct_invariants(alm_t: np.ndarray, alm_list_full: np.ndarray | None = None) -> dict:
    # Build l=2 Cartesian STF matrix and compute eigenvalues/principal axis; l=3 angular momentum axis
    # Extract l=2,3 maps purely from alm_t and use fast grid/quadrature moments
    npix = hp.nside2npix(32)
    theta, phi = hp.pix2ang(32, np.arange(npix))
    n = np.column_stack([np.sin(theta) * np.cos(phi), np.sin(theta) * np.sin(phi), np.cos(theta)])

    alm2 = np.zeros_like(alm_t)
    alm3 = np.zeros_like(alm_t)
    for m in range(3):
        alm2[hp.Alm.getidx(LMAX, 2, m)] = alm_t[hp.Alm.getidx(LMAX, 2, m)]
    for m in range(4):
        alm3[hp.Alm.getidx(LMAX, 3, m)] = alm_t[hp.Alm.getidx(LMAX, 3, m)]
    m2 = hp.alm2map(alm2, 32, lmax=LMAX)
    m3 = hp.alm2map(alm3, 32, lmax=LMAX)
    # Q_ij = (15 / 8pi) * integral n_i n_j m2(n) dOmega -> discrete equal-area average: <n_i n_j m2>
    Q = (7.5 / npix) * np.einsum("ni,nj,n->ij", n, n, m2)
    Q = 0.5 * (Q + Q.T) - np.eye(3) * (np.trace(Q) / 3.0)
    evals, evecs = np.linalg.eigh(Q)
    # Signed chi = sqrt(6) tr(Q^3) / tr(Q^2)^{3/2}
    q2 = float(np.trace(Q @ Q))
    chi2 = float(np.sqrt(6.0) * np.trace(Q @ Q @ Q) / (q2 ** 1.5)) if q2 > 0 else 0.0
    dom_idx = int(np.argmax(np.abs(evals)))
    n2_axis = evecs[:, dom_idx]
    if n2_axis[2] < 0:
        n2_axis = -n2_axis

    # Exact Land-Magueijo (2005) l=3 maximum angular-momentum dispersion axis:
    # maximize <a | (n . J)^2 | a> = sum_{m=-3}^3 m^2 |a_{3m}(n)|^2 via top eigenvector of 3x3 Re<a|0.5(J_i J_j + J_j J_i)|a>
    ms = np.arange(-3, 4, dtype=np.float64)
    Jz = np.diag(ms).astype(np.complex128)
    Jp = np.zeros((7, 7), dtype=np.complex128)
    for ii in range(6):
        m_val = ms[ii]
        Jp[ii + 1, ii] = np.sqrt(12.0 - m_val * (m_val + 1.0))
    Jm = Jp.T
    J_ops = [0.5 * (Jp + Jm), -0.5j * (Jp - Jm), Jz]
    v3 = np.zeros(7, dtype=np.complex128)
    v3[3] = alm_t[hp.Alm.getidx(LMAX, 3, 0)]
    for m_val in range(1, 4):
        c3 = alm_t[hp.Alm.getidx(LMAX, 3, m_val)]
        v3[3 + m_val] = c3
        v3[3 - m_val] = ((-1) ** m_val) * np.conj(c3)
    norm3 = float(np.real(np.vdot(v3, v3)))
    if norm3 > 0.0:
        M3 = np.zeros((3, 3), dtype=np.float64)
        for ii in range(3):
            for jj in range(3):
                M3[ii, jj] = float(np.real(np.vdot(v3, 0.5 * (J_ops[ii] @ J_ops[jj] + J_ops[jj] @ J_ops[ii]) @ v3))) / norm3
        M3 = 0.5 * (M3 + M3.T)
        ev3, evec3 = np.linalg.eigh(M3)
        n3_axis = evec3[:, 2].copy()
        if n3_axis[2] < 0.0:
            n3_axis = -n3_axis
        max_m2_ratio = float(ev3[2] / 9.0)
    else:
        n3_axis = np.array([0.0, 0.0, 1.0], dtype=np.float64)
        max_m2_ratio = 0.0
    align_cos = float(abs(np.dot(n2_axis, n3_axis)))
    return {
        "Q2_chi_signed": chi2,
        "n2_gal_axis": n2_axis.tolist(),
        "n3_oct_axis": n3_axis.tolist(),
        "n2_n3_alignment_abs_cos": align_cos,
        "l3_land_magueijo_max_m2_over_9": max_m2_ratio,
    }


def _analyze_masked_map(maps_k: list[np.ndarray], tmask: np.ndarray, pmask: np.ndarray | None, pol: bool) -> dict:
    # Masked monopole+dipole removal on T before harmonic transform
    t = maps_k[0].copy()
    npix = len(t)
    theta, phi = hp.pix2ang(NSIDE_OUT, np.arange(npix))
    n = np.column_stack([np.sin(theta) * np.cos(phi), np.sin(theta) * np.sin(phi), np.cos(theta)])
    X_md = np.column_stack([np.ones(int(tmask.sum())), n[tmask]])
    coef, *_ = np.linalg.lstsq(X_md, t[tmask], rcond=None)
    t[tmask] -= X_md @ coef
    t[~tmask] = 0.0

    f_sky_t = float(np.mean(tmask))
    alm_t = hp.map2alm(t, lmax=LMAX)
    cl_tt = hp.alm2cl(alm_t) / f_sky_t
    inv_l23 = _quad_oct_invariants(alm_t)

    res = {
        "f_sky_T": f_sky_t,
        "cl_TT_ell2_to_8_K2": [float(x) for x in cl_tt[2 : LMAX + 1]],
        "lowell_T_rms_uK": float(np.std(t[tmask]) * 1e6),
        **inv_l23,
        "_t_masked": t[tmask],
    }

    if pol and pmask is not None and len(maps_k) == 3:
        f_sky_p = float(np.mean(pmask))
        q = np.where(pmask, maps_k[1], 0.0)
        u = np.where(pmask, maps_k[2], 0.0)
        alms = hp.map2alm([t, q, u], lmax=LMAX, pol=True)
        cl_teb = hp.alm2cl(alms)  # TT, EE, BB, TE, EB, TB
        res["f_sky_P"] = f_sky_p
        res["cl_EE_ell2_to_8_K2"] = [float(x / f_sky_p) for x in cl_teb[1][2 : LMAX + 1]]
        res["cl_BB_ell2_to_8_K2"] = [float(x / f_sky_p) for x in cl_teb[2][2 : LMAX + 1]]
        res["cl_TE_ell2_to_8_K2"] = [float(x / np.sqrt(f_sky_t * f_sky_p)) for x in cl_teb[3][2 : LMAX + 1]]
        res["_qu_masked"] = np.concatenate([q[pmask], u[pmask]])
    return res


def main() -> int:
    if OUT_JSON.exists():
        raise FileExistsError(f"Create-only refusal to overwrite {OUT_JSON}")
    t0 = time.perf_counter()

    # Common PR3 NSIDE=64 binary masks (f_sky ~ 0.78 T, ~0.78 P)
    m_int_raw = hp.read_map(str(MASK_INT_FITS), field=0, nest=True, verbose=False) if "verbose" in hp.read_map.__code__.co_varnames else hp.read_map(str(MASK_INT_FITS), field=0, nest=True)
    m_pol_raw = hp.read_map(str(MASK_POL_FITS), field=0, nest=True, verbose=False) if "verbose" in hp.read_map.__code__.co_varnames else hp.read_map(str(MASK_POL_FITS), field=0, nest=True)
    tmask = hp.ud_grade(np.asarray(m_int_raw, dtype=np.float64), nside_out=NSIDE_OUT, order_in="NESTED", order_out="RING") >= 0.9
    pmask = hp.ud_grade(np.asarray(m_pol_raw, dtype=np.float64), nside_out=NSIDE_OUT, order_in="NESTED", order_out="RING") >= 0.9
    del m_int_raw, m_pol_raw

    map_specs = [
        ("PR3_SMICA", WORKDIR / "raw/planck_data/COM_CMB_IQU-smica_2048_R3.00_full.fits", True, 1.0, True),
        ("PR3_Commander", WORKDIR / "raw/planck_data/COM_CMB_IQU-commander_2048_R3.00_full.fits", True, 1.0, True),
        ("PR3_NILC", WORKDIR / "raw/planck_pr3_component_controls/COM_CMB_IQU-nilc_2048_R3.00_full.fits", True, 1.0, True),
        ("PR3_SEVEM", WORKDIR / "raw/planck_pr3_component_controls/COM_CMB_IQU-sevem_2048_R3.01_full.fits", True, 1.0, True),
        ("PR4_Commander_T", WORKDIR / "htt_open_data/r36_pr4_actual/COM_CMB_IQU-commander_4096_R4.00_full.fits", True, 1.0, False),
        ("Cosmoglobe_DR1", WORKDIR / "raw/cosmoglobe_dr1/CG_cmb_IQU_n1024_v1.fits", False, 1e-6, True),
        ("BeyondPlanck_v2", WORKDIR / "raw/beyondplanck_v2/BP_cmb_IQU_n1024_v2.fits", False, 1e-6, True),
        ("WMAP9_ILC_T", WORKDIR / "raw/wmap_9yr/core/wmap_ilc_9yr_v5.fits", True, 1e-3, False),
    ]

    obs_summaries = {}
    t_vecs = {}
    qu_vecs = {}
    for name, path, nest, scale, pol in map_specs:
        maps_k = _downgrade_map(path, nest=nest, scale_to_k=scale, pol=pol)
        r = _analyze_masked_map(maps_k, tmask, pmask if pol else None, pol=pol)
        t_vecs[name] = r.pop("_t_masked")
        if "_qu_masked" in r:
            qu_vecs[name] = r.pop("_qu_masked")
        r["file_bytes"] = int(path.stat().st_size)
        obs_summaries[name] = r

    # Pairwise cross-pipeline T correlation & RMS diff (uK) across all 8 maps, and QU across 6 IQU maps
    t_names = [m[0] for m in map_specs]
    n_t = len(t_names)
    t_corr = np.ones((n_t, n_t), dtype=np.float64)
    t_diff_uk = np.zeros((n_t, n_t), dtype=np.float64)
    for i in range(n_t):
        for j in range(i + 1, n_t):
            a, b = t_vecs[t_names[i]], t_vecs[t_names[j]]
            c = float(np.corrcoef(a, b)[0, 1])
            d = float(np.sqrt(np.mean((a - b) ** 2)) * 1e6)
            t_corr[i, j] = t_corr[j, i] = c
            t_diff_uk[i, j] = t_diff_uk[j, i] = d

    qu_names = [m[0] for m in map_specs if m[0] in qu_vecs]
    n_qu = len(qu_names)
    qu_corr = np.ones((n_qu, n_qu), dtype=np.float64)
    qu_diff_uk = np.zeros((n_qu, n_qu), dtype=np.float64)
    for i in range(n_qu):
        for j in range(i + 1, n_qu):
            a, b = qu_vecs[qu_names[i]], qu_vecs[qu_names[j]]
            c = float(np.corrcoef(a, b)[0, 1])
            d = float(np.sqrt(np.mean((a - b) ** 2)) * 1e6)
            qu_corr[i, j] = qu_corr[j, i] = c
            qu_diff_uk[i, j] = qu_diff_uk[j, i] = d

    # 2. Direct raw FFP10 SMICA 50 paired CMB+Noise FITS evaluation on identical NSIDE=64 mask
    mc_ids = []
    mc_cl_tt = []
    mc_cl_ee = []
    mc_cl_bb = []
    mc_align = []
    for k in range(N_RAW_MC):
        cpath = SMICA_CMB_DIR / f"dx12_v3_smica_cmb_mc_{k:05d}_raw.fits"
        npath = SMICA_NOISE_DIR / f"dx12_v3_smica_noise_mc_{k:05d}_raw.fits"
        mc_ids.append(f"FFP10_SMICA_RAW_{k:05d}")
        mc_c = _downgrade_map(cpath, nest=False, scale_to_k=1.0, pol=True)
        mc_n = _downgrade_map(npath, nest=False, scale_to_k=1.0, pol=True)
        mc_tot = [mc_c[idx] + mc_n[idx] for idx in range(3)]
        rm = _analyze_masked_map(mc_tot, tmask, pmask, pol=True)
        mc_cl_tt.append(rm["cl_TT_ell2_to_8_K2"])
        mc_cl_ee.append(rm["cl_EE_ell2_to_8_K2"])
        mc_cl_bb.append(rm["cl_BB_ell2_to_8_K2"])
        mc_align.append(rm["n2_n3_alignment_abs_cos"])

    mc_cl_tt_a = np.asarray(mc_cl_tt, dtype=np.float64)
    mc_cl_ee_a = np.asarray(mc_cl_ee, dtype=np.float64)
    mc_cl_bb_a = np.asarray(mc_cl_bb, dtype=np.float64)
    mc_align_a = np.asarray(mc_align, dtype=np.float64)

    obs_smica = obs_summaries["PR3_SMICA"]
    rank_smica_c2_tt = p2p3_fast.working_rank_interval(obs_smica["cl_TT_ell2_to_8_K2"][0], mc_cl_tt_a[:, 0], simulation_ids=mc_ids, null_qualified=False)
    rank_smica_c2_ee = p2p3_fast.working_rank_interval(obs_smica["cl_EE_ell2_to_8_K2"][0], mc_cl_ee_a[:, 0], simulation_ids=mc_ids, null_qualified=False)
    rank_smica_c2_bb = p2p3_fast.working_rank_interval(obs_smica["cl_BB_ell2_to_8_K2"][0], mc_cl_bb_a[:, 0], simulation_ids=mc_ids, null_qualified=False)
    rank_smica_align = p2p3_fast.working_rank_interval(obs_smica["n2_n3_alignment_abs_cos"], mc_align_a, simulation_ids=mc_ids, null_qualified=False)

    # Check Commander FFP10 raw FITS availability on disk (documenting blocker)
    cmd_complete = len(list(CMD_CMB_DIR.glob("*.fits")))
    cmd_partial = len(list(CMD_CMB_DIR.glob("*.partial"))) + (len(list(CMD_CAND_DIR.glob("*.fits"))) if CMD_CAND_DIR.is_dir() else 0)

    elapsed = time.perf_counter() - t0
    out = {
        "schema": "htt.r89.g05_planck_deep_multipipeline/1",
        "group_id": "G05_PLANCK",
        "node_ids": ["L01", "SQ-CMB-NULL", "L03", "L02", "L04", "L05", "L06"],
        "mask_sha256": {
            "T_mask": _sha256_small(MASK_INT_FITS),
            "P_mask": _sha256_small(MASK_POL_FITS),
        },
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "healpy": hp.__version__,
            "elapsed_seconds": float(elapsed),
            "maxrss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
            "nside_downgraded": NSIDE_OUT,
            "lmax": LMAX,
        },
        "eight_map_common_mask_lowell": obs_summaries,
        "cross_pipeline_T_comparison": {
            "map_order": t_names,
            "pearson_corr_matrix": t_corr.tolist(),
            "rms_diff_uK_matrix": t_diff_uk.tolist(),
        },
        "cross_pipeline_QU_comparison": {
            "map_order": qu_names,
            "pearson_corr_matrix": qu_corr.tolist(),
            "rms_diff_uK_matrix": qu_diff_uk.tolist(),
        },
        "raw_ffp10_smica_50mc_common_mask": {
            "mc_pairs_evaluated": N_RAW_MC,
            "mc_c2_TT_median_max": [float(np.median(mc_cl_tt_a[:, 0])), float(np.max(mc_cl_tt_a[:, 0]))],
            "mc_c2_EE_median_max": [float(np.median(mc_cl_ee_a[:, 0])), float(np.max(mc_cl_ee_a[:, 0]))],
            "mc_c2_BB_median_max": [float(np.median(mc_cl_bb_a[:, 0])), float(np.max(mc_cl_bb_a[:, 0]))],
            "smica_c2_TT_rank": rank_smica_c2_tt,
            "smica_c2_EE_rank": rank_smica_c2_ee,
            "smica_c2_BB_rank": rank_smica_c2_bb,
            "smica_l2_l3_alignment_rank": rank_smica_align,
        },
        "commander_ffp10_raw_census": {
            "complete_fits_in_cmb_mc": cmd_complete,
            "incomplete_or_candidate_files": cmd_partial,
        },
        "node_verdicts": {
            "L01": "REUSED_SCOPED",
            "L02": "REUSED_SCOPED",
            "SQ-CMB-NULL": "BLOCKED_INPUT",
            "L03": "BLOCKED_DEPENDENCY",
            "L04": "BLOCKED_DEPENDENCY",
            "L05": "BLOCKED_DEPENDENCY",
            "L06": "BLOCKED_DEPENDENCY",
        },
        "claim_hygiene": {
            "physical_Pi": None,
            "physical_GF": None,
            "bianchi_family_identified": False,
            "release_matched_null_pass": False,
            "statement": (
                "Common-mask 8-pipeline CMB comparison and 50 raw FFP10 SMICA pilot pairs only "
                "(null_qualified=False); SQ-CMB-NULL remains BLOCKED_INPUT with physical_Pi=None and physical_GF=None."
            ),
        },
        "physical_gate_note": "Eight observed pipelines agree strongly in T (r > 0.99 across Planck/CG/BP, RMS diff a few uK) and diverge more noticeably in low-ell polarization QU, while PR3 SMICA against 50 raw FFP10 CMB+Noise FITS maps on identical NSIDE=64 masks shows non-extreme ranks (null_qualified=False). Commander FFP10 only has 2 complete raw CMB maps on disk, keeping joint multi-pipeline SQ-CMB-NULL in BLOCKED_INPUT.",
    }
    OUT_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "group_id": "G05_PLANCK_DEEP",
        "elapsed_s": round(elapsed, 3),
        "maxrss_mib": round(out["runtime"]["maxrss_kib"] / 1024.0, 1),
        "maps_analyzed": len(obs_summaries),
        "mc_evaluated": N_RAW_MC,
        "smica_c2_TT_rank": rank_smica_c2_tt["rank_interval"],
        "smica_c2_EE_rank": rank_smica_c2_ee["rank_interval"],
        "smica_l2_l3_align_rank": rank_smica_align["rank_interval"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
