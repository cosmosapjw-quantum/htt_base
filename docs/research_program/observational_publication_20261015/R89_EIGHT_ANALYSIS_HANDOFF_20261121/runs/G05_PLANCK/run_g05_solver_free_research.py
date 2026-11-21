#!/usr/bin/env python3
"""R89 G05_PLANCK Solver-Free Research Completion (create-only).

Covers Section 6:
A. Exact analytic Hivon+2002 Master / Wigner-3j pseudo-C_l mode-coupling
   deconvolution (scalar TT & spin-2 EE/BB) with 200-sky unbiasedness validation,
   applied across all 8 CMB maps (PR3 x4, PR4_T, Cosmoglobe, BeyondPlanck, WMAP9)
   plus point-parity asymmetry R_T(lmax=7,8).
B. Real Planck PR3 SMICA half-mission (hm1, hm2) & odd-even (oe1, oe2)
   noise-debiased cross-spectra vs split_noise pilot MC map.
C. Strictly SMICA-only 25 NEW raw FFP10 CMB+Noise MC pairs (00050..00074, disjoint
   from Phase-3 00000..00049) evaluated identically on NSIDE=64 Master masks,
   while preserving SQ-CMB-NULL = BLOCKED_INPUT (Commander FFP10 only 2 complete).
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

import healpy as hp
import numpy as np
from sympy.physics.wigner import wigner_3j

ROOT = Path(__file__).resolve().parents[6]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from htt.obsstat import p2p3_fast

OUT_DIR = Path(__file__).resolve().parent
OUT_JSON = OUT_DIR / "SOLVER_FREE_RESEARCH_RESULT.json"

WORKDIR = Path("/mnt/extdrive/workdir")
MASK_INT_FITS = WORKDIR / "raw/planck_data/COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits"
MASK_POL_FITS = WORKDIR / "raw/planck_data/COM_Mask_CMB-common-Mask-Pol_2048_R3.00.fits"
SMICA_CMB_MC = WORKDIR / "raw/planck_ffp10/smica/cmb_mc"
SMICA_NOISE_MC = WORKDIR / "raw/planck_ffp10/smica/noise_mc"
PR3_CMB_DIR = WORKDIR / "htt_open_data/planck/PR3/cmb"
PR3_SPLIT_NOISE = WORKDIR / "htt_open_data/planck/PR3/split_noise"
CMD_CMB_MC = WORKDIR / "raw/planck_ffp10/commander/cmb_mc"
PHASE3_CMB_JSON = OUT_DIR / "DEEP_MULTIPIPELINE_CMB_RESULT.json"

OBSERVED_MAPS = [
    ("PR3_SMICA", WORKDIR / "raw/planck_data/COM_CMB_IQU-smica_2048_R3.00_full.fits", True, 1.0, True),
    ("PR3_Commander", WORKDIR / "raw/planck_data/COM_CMB_IQU-commander_2048_R3.00_full.fits", True, 1.0, True),
    ("PR3_NILC", WORKDIR / "raw/planck_pr3_component_controls/COM_CMB_IQU-nilc_2048_R3.00_full.fits", True, 1.0, True),
    ("PR3_SEVEM", WORKDIR / "raw/planck_pr3_component_controls/COM_CMB_IQU-sevem_2048_R3.01_full.fits", True, 1.0, True),
    ("PR4_Commander_T", WORKDIR / "htt_open_data/r36_pr4_actual/COM_CMB_IQU-commander_4096_R4.00_full.fits", True, 1.0, False),
    ("Cosmoglobe_DR1", WORKDIR / "raw/cosmoglobe_dr1/CG_cmb_IQU_n1024_v1.fits", False, 1e-6, True),
    ("BeyondPlanck_v2", WORKDIR / "raw/beyondplanck_v2/BP_cmb_IQU_n1024_v2.fits", False, 1e-6, True),
    ("WMAP9_ILC_T", WORKDIR / "raw/wmap_9yr/core/wmap_ilc_9yr_v5.fits", True, 1e-3, False),
]

NSIDE = 64
LMAX_MAP = 16
LMAX_MASTER = 12


def _downgrade(path: Path, *, nest: bool, scale: float, pol: bool) -> list[np.ndarray]:
    fields = (0, 1, 2) if pol else (0,)
    raw = hp.read_map(str(path), field=fields, nest=nest)
    if not pol:
        raw = [raw]
    out = []
    order_in = "NESTED" if nest else "RING"
    for arr in raw:
        a = np.asarray(arr, dtype=np.float64)
        bad = ~np.isfinite(a) | (np.abs(a) > 1e20)
        if np.any(bad):
            a = np.where(bad, hp.UNSEEN, a)
        dg = hp.ud_grade(a, nside_out=NSIDE, order_in=order_in, order_out="RING")
        dg = np.where(dg == hp.UNSEEN, 0.0, dg * scale)
        out.append(dg)
    return out


def _master_matrices(tmask: np.ndarray, pmask: np.ndarray, lmax_out: int = LMAX_MASTER) -> dict:
    w_t = hp.anafast(tmask.astype(np.float64), lmax=2 * lmax_out + 4, iter=3)
    w_p = hp.anafast(pmask.astype(np.float64), lmax=2 * lmax_out + 4, iter=3)
    M_TT = np.zeros((lmax_out + 1, lmax_out + 1), dtype=np.float64)
    M_pp = np.zeros((lmax_out + 1, lmax_out + 1), dtype=np.float64)
    M_mm = np.zeros((lmax_out + 1, lmax_out + 1), dtype=np.float64)

    for l1 in range(2, lmax_out + 1):
        for l2 in range(2, lmax_out + 1):
            st = 0.0
            spp = 0.0
            smm = 0.0
            for l3 in range(abs(l1 - l2), l1 + l2 + 1):
                if (l1 + l2 + l3) % 2 == 0:
                    w0 = float(wigner_3j(l1, l2, l3, 0, 0, 0))
                    st += (2 * l3 + 1) * w_t[l3] * (w0 * w0)
                w2 = float(wigner_3j(l1, l2, l3, 2, -2, 0))
                tpol = (2 * l3 + 1) * w_p[l3] * (w2 * w2)
                if (l1 + l2 + l3) % 2 == 0:
                    spp += tpol
                else:
                    smm += tpol
            fac = (2 * l2 + 1) / (4.0 * math.pi)
            M_TT[l1, l2] = fac * st
            M_pp[l1, l2] = fac * spp
            M_mm[l1, l2] = fac * smm

    M_TT_sub = M_TT[2:, 2:]
    M_EB_sub = np.block([[M_pp[2:, 2:], M_mm[2:, 2:]], [M_mm[2:, 2:], M_pp[2:, 2:]]])
    return {
        "M_TT": M_TT_sub,
        "M_TT_inv": np.linalg.inv(M_TT_sub),
        "M_EB": M_EB_sub,
        "M_EB_inv": np.linalg.inv(M_EB_sub),
        "M_TT_cond": float(np.linalg.cond(M_TT_sub)),
        "M_EB_cond": float(np.linalg.cond(M_EB_sub)),
    }


def _validate_master_mc(master: dict, tmask: np.ndarray, pmask: np.ndarray, n_sim: int = 200) -> dict:
    # Known smooth input spectrum l=0..LMAX_MASTER
    ells = np.arange(LMAX_MASTER + 1, dtype=np.float64)
    cl_true_tt = np.zeros_like(ells); cl_true_tt[2:] = 1e-9 / (ells[2:] * (ells[2:] + 1.0))
    cl_true_ee = np.zeros_like(ells); cl_true_ee[2:] = 5e-14 / (ells[2:] + 1.0)
    cl_true_bb = np.zeros_like(ells); cl_true_bb[2:] = 1e-14 / (ells[2:] + 1.0)
    cl_true_te = np.zeros_like(ells)

    rng = np.random.default_rng(20261121)
    tt_hats, ee_hats, bb_hats = [], [], []
    # Generate without pixel window so Master exact identity is isolated
    for _ in range(n_sim):
        np.random.seed(int(rng.integers(1, 2**31 - 1)))
        m_full = hp.synfast([cl_true_tt, cl_true_ee, cl_true_bb, cl_true_te], nside=NSIDE, lmax=LMAX_MASTER, pixwin=False, new=True)
        alm_t = hp.map2alm(m_full[0] * tmask, lmax=LMAX_MASTER)
        cl_pt = hp.alm2cl(alm_t)[2 : LMAX_MASTER + 1]
        tt_hats.append(master["M_TT_inv"] @ cl_pt)

        alms_p = hp.map2alm([m_full[0] * tmask, m_full[1] * pmask, m_full[2] * pmask], lmax=LMAX_MASTER, pol=True)
        cl_pe = hp.alm2cl(alms_p[1])[2 : LMAX_MASTER + 1]
        cl_pb = hp.alm2cl(alms_p[2])[2 : LMAX_MASTER + 1]
        deconv = master["M_EB_inv"] @ np.concatenate([cl_pe, cl_pb])
        n_l = LMAX_MASTER - 1
        ee_hats.append(deconv[:n_l])
        bb_hats.append(deconv[n_l:])

    tt_mean = np.mean(tt_hats, axis=0)
    ee_mean = np.mean(ee_hats, axis=0)
    bb_mean = np.mean(bb_hats, axis=0)
    tt_ratio = tt_mean / cl_true_tt[2:]
    ee_ratio = ee_mean / cl_true_ee[2:]
    bb_ratio = bb_mean / cl_true_bb[2:]
    return {
        "n_sim": n_sim,
        "tt_mean_over_true_l2_to_12": tt_ratio.tolist(),
        "ee_mean_over_true_l2_to_12": ee_ratio.tolist(),
        "bb_mean_over_true_l2_to_12": bb_ratio.tolist(),
        "max_abs_tt_rel_bias": float(np.max(np.abs(tt_ratio - 1.0))),
        "max_abs_ee_rel_bias": float(np.max(np.abs(ee_ratio - 1.0))),
        "max_abs_bb_rel_bias": float(np.max(np.abs(bb_ratio - 1.0))),
        "c2_tt_mc_se_rel": float(np.std(np.array(tt_hats)[:, 0]) / math.sqrt(n_sim) / cl_true_tt[2]),
    }


def _clean_md_t(t_map: np.ndarray, tmask: np.ndarray) -> np.ndarray:
    t = t_map.copy()
    npix = len(t)
    th, ph = hp.pix2ang(NSIDE, np.arange(npix))
    n = np.column_stack([np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)])
    X = np.column_stack([np.ones(int(tmask.sum())), n[tmask]])
    coef, *_ = np.linalg.lstsq(X, t[tmask], rcond=None)
    t[tmask] -= X @ coef
    t[~tmask] = 0.0
    return t


def _parity_ratio(cl_2_to_N: np.ndarray, lmax: int) -> float:
    # D_l = l(l+1)/(2pi) C_l; sum even / sum odd for l in [2..lmax]
    ells = np.arange(2, lmax + 1, dtype=np.float64)
    dl = ells * (ells + 1.0) * cl_2_to_N[: len(ells)]
    even_m = (ells.astype(int) % 2) == 0
    return float(np.sum(dl[even_m]) / max(float(np.sum(dl[~even_m])), 1e-30))


def _land_magueijo_axes(alm_t: np.ndarray, lmax_in: int = LMAX_MASTER) -> dict:
    # l=2 STF & l=3 exact 3x3 J_i J_j
    alm2 = np.zeros_like(alm_t)
    for m in range(3):
        alm2[hp.Alm.getidx(lmax_in, 2, m)] = alm_t[hp.Alm.getidx(lmax_in, 2, m)]
    m2 = hp.alm2map(alm2, 32, lmax=lmax_in)
    npix32 = len(m2)
    th, ph = hp.pix2ang(32, np.arange(npix32))
    n = np.column_stack([np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)])
    Q = (7.5 / npix32) * np.einsum("ni,nj,n->ij", n, n, m2)
    Q = 0.5 * (Q + Q.T) - np.eye(3) * (np.trace(Q) / 3.0)
    ev2, evec2 = np.linalg.eigh(Q)
    n2 = evec2[:, int(np.argmax(np.abs(ev2)))].copy()
    if n2[2] < 0.0:
        n2 = -n2

    ms = np.arange(-3, 4, dtype=np.float64)
    Jz = np.diag(ms).astype(np.complex128)
    Jp = np.zeros((7, 7), dtype=np.complex128)
    for ii in range(6):
        mv = ms[ii]
        Jp[ii + 1, ii] = np.sqrt(12.0 - mv * (mv + 1.0))
    Jm = Jp.T
    J_ops = [0.5 * (Jp + Jm), -0.5j * (Jp - Jm), Jz]
    v3 = np.zeros(7, dtype=np.complex128)
    v3[3] = alm_t[hp.Alm.getidx(lmax_in, 3, 0)]
    for mv in range(1, 4):
        c3 = alm_t[hp.Alm.getidx(lmax_in, 3, mv)]
        v3[3 + mv] = c3
        v3[3 - mv] = ((-1) ** mv) * np.conj(c3)
    norm3 = float(np.real(np.vdot(v3, v3)))
    M3 = np.zeros((3, 3), dtype=np.float64)
    for ii in range(3):
        for jj in range(3):
            M3[ii, jj] = float(np.real(np.vdot(v3, 0.5 * (J_ops[ii] @ J_ops[jj] + J_ops[jj] @ J_ops[ii]) @ v3))) / max(norm3, 1e-30)
    ev3, evec3 = np.linalg.eigh(0.5 * (M3 + M3.T))
    n3 = evec3[:, 2].copy()
    if n3[2] < 0.0:
        n3 = -n3
    return {
        "n2_gal_axis": n2.tolist(),
        "n3_gal_axis": n3.tolist(),
        "n2_n3_align_cos": float(abs(np.dot(n2, n3))),
        "l3_m2_over_9": float(ev3[2] / 9.0),
    }


def _eval_map(maps_k: list[np.ndarray], tmask: np.ndarray, pmask: np.ndarray, pol: bool, master: dict) -> dict:
    t_c = _clean_md_t(maps_k[0], tmask)
    alm_t = hp.map2alm(t_c, lmax=LMAX_MASTER)
    cl_pt = hp.alm2cl(alm_t)[2 : LMAX_MASTER + 1]
    cl_mt = master["M_TT_inv"] @ cl_pt
    lm = _land_magueijo_axes(alm_t)
    res = {
        "cl_pseudo_TT_ell2_to_12": cl_pt.tolist(),
        "cl_master_TT_ell2_to_12": cl_mt.tolist(),
        "parity_R_pseudo_lmax7": _parity_ratio(cl_pt, 7),
        "parity_R_master_lmax7": _parity_ratio(cl_mt, 7),
        "parity_R_master_lmax8": _parity_ratio(cl_mt, 8),
        **lm,
    }
    if pol:
        qm = np.where(pmask, maps_k[1], 0.0)
        um = np.where(pmask, maps_k[2], 0.0)
        alms = hp.map2alm([t_c, qm, um], lmax=LMAX_MASTER, pol=True)
        cl_pe = hp.alm2cl(alms[1])[2 : LMAX_MASTER + 1]
        cl_pb = hp.alm2cl(alms[2])[2 : LMAX_MASTER + 1]
        deconv = master["M_EB_inv"] @ np.concatenate([cl_pe, cl_pb])
        n_l = LMAX_MASTER - 1
        res["cl_master_EE_ell2_to_12"] = deconv[:n_l].tolist()
        res["cl_master_BB_ell2_to_12"] = deconv[n_l:].tolist()
    return res


def _part_b_smica_splits(tmask: np.ndarray, pmask: np.ndarray, master: dict) -> dict:
    hm1 = _downgrade(PR3_CMB_DIR / "COM_CMB_IQU-smica_2048_R3.00_hm1.fits", nest=True, scale=1.0, pol=True)
    hm2 = _downgrade(PR3_CMB_DIR / "COM_CMB_IQU-smica_2048_R3.00_hm2.fits", nest=True, scale=1.0, pol=True)
    oe1 = _downgrade(PR3_CMB_DIR / "COM_CMB_IQU-smica_2048_R3.00_oe1.fits", nest=True, scale=1.0, pol=True)
    oe2 = _downgrade(PR3_CMB_DIR / "COM_CMB_IQU-smica_2048_R3.00_oe2.fits", nest=True, scale=1.0, pol=True)

    # Half-difference noise proxy (hm1 - hm2)/2 and (oe1 - oe2)/2
    hm_diff = [0.5 * (hm1[i] - hm2[i]) for i in range(3)]
    oe_diff = [0.5 * (oe1[i] - oe2[i]) for i in range(3)]

    def cross(a, b):
        ta = _clean_md_t(a[0], tmask); tb = _clean_md_t(b[0], tmask)
        aa = hp.map2alm([ta, np.where(pmask, a[1], 0.0), np.where(pmask, a[2], 0.0)], lmax=LMAX_MASTER, pol=True)
        ab = hp.map2alm([tb, np.where(pmask, b[1], 0.0), np.where(pmask, b[2], 0.0)], lmax=LMAX_MASTER, pol=True)
        ct = master["M_TT_inv"] @ hp.alm2cl(aa[0], ab[0])[2 : LMAX_MASTER + 1]
        ce_p = hp.alm2cl(aa[1], ab[1])[2 : LMAX_MASTER + 1]
        cb_p = hp.alm2cl(aa[2], ab[2])[2 : LMAX_MASTER + 1]
        deb = master["M_EB_inv"] @ np.concatenate([ce_p, cb_p])
        nl = LMAX_MASTER - 1
        return {"master_TT_2_to_6": ct[:5].tolist(), "master_EE_2_to_6": deb[:nl][:5].tolist(), "master_BB_2_to_6": deb[nl:][:5].tolist()}

    # Pilot split noise FFP10 mc_00000
    n_hm1 = _downgrade(PR3_SPLIT_NOISE / "dx12_v3_smica_noise_hm1_mc_00000_raw.fits", nest=False, scale=1.0, pol=True)
    n_hm2 = _downgrade(PR3_SPLIT_NOISE / "dx12_v3_smica_noise_hm2_mc_00000_raw.fits", nest=False, scale=1.0, pol=True)
    n_hm_diff = [0.5 * (n_hm1[i] - n_hm2[i]) for i in range(3)]

    return {
        "epistemic_status": "conditional",
        "hm1_x_hm2_debiased": cross(hm1, hm2),
        "oe1_x_oe2_debiased": cross(oe1, oe2),
        "hm_halfdiff_obs_noise": _eval_map(hm_diff, tmask, pmask, True, master),
        "oe_halfdiff_obs_noise": _eval_map(oe_diff, tmask, pmask, True, master),
        "ffp10_mc00000_hm_halfdiff_noise": _eval_map(n_hm_diff, tmask, pmask, True, master),
    }


def main() -> int:
    if OUT_JSON.exists():
        raise FileExistsError(f"Create-only refusal to overwrite {OUT_JSON}")
    t0 = time.perf_counter()

    tmask = _downgrade(MASK_INT_FITS, nest=True, scale=1.0, pol=False)[0] >= 0.9
    pmask = _downgrade(MASK_POL_FITS, nest=True, scale=1.0, pol=False)[0] >= 0.9
    master = _master_matrices(tmask, pmask, LMAX_MASTER)
    mc_val = _validate_master_mc(master, tmask, pmask, n_sim=200)

    obs_res = {}
    sm_mk = None
    for name, path, nest, scale, pol in OBSERVED_MAPS:
        mk = _downgrade(path, nest=nest, scale=scale, pol=pol)
        obs_res[name] = _eval_map(mk, tmask, pmask, pol, master)
        if name == "PR3_SMICA":
            sm_mk = mk

    split_res = _part_b_smica_splits(tmask, pmask, master)

    # Verify exact Phase-3 lmax=8 + 1/f_sky estimator consistency on PR3_SMICA before combining 75 pairs
    f_sky_t = float(np.mean(tmask))
    f_sky_p = float(np.mean(pmask))
    assert sm_mk is not None
    sm_tc = _clean_md_t(sm_mk[0], tmask)
    sm_almt8 = hp.map2alm(sm_tc, lmax=8)
    sm_alms8 = hp.map2alm([sm_tc, np.where(pmask, sm_mk[1], 0.0), np.where(pmask, sm_mk[2], 0.0)], lmax=8, pol=True)
    sm_p3_tt2 = float(hp.alm2cl(sm_almt8)[2] / f_sky_t)
    sm_p3_ee2 = float(hp.alm2cl(sm_alms8[1])[2] / f_sky_p)
    sm_p3_bb2 = float(hp.alm2cl(sm_alms8[2])[2] / f_sky_p)
    sm_p3_al8 = float(_land_magueijo_axes(sm_almt8, lmax_in=8)["n2_n3_align_cos"])

    # Evaluate 25 NEW raw FFP10 SMICA MC pairs (00050..00074, strictly non-overlapping with Phase-3 00000..00049)
    new_ids = [f"FFP10_SMICA_RAW_{k:05d}" for k in range(50, 75)]
    new_tt2, new_ee2, new_bb2, new_par7, new_align = [], [], [], [], []
    # Compute exact Phase-3 lmax=8 + 1/f_sky statistics on 00050..00074 for exact 75-pair combination
    p_tt2, p_ee2, p_bb2, p_al8 = [], [], [], []
    for k in range(50, 75):
        mc = _downgrade(SMICA_CMB_MC / f"dx12_v3_smica_cmb_mc_{k:05d}_raw.fits", nest=False, scale=1.0, pol=True)
        mn = _downgrade(SMICA_NOISE_MC / f"dx12_v3_smica_noise_mc_{k:05d}_raw.fits", nest=False, scale=1.0, pol=True)
        mtot = [mc[i] + mn[i] for i in range(3)]
        ev = _eval_map(mtot, tmask, pmask, True, master)
        new_tt2.append(ev["cl_master_TT_ell2_to_12"][0])
        new_ee2.append(ev["cl_master_EE_ell2_to_12"][0])
        new_bb2.append(ev["cl_master_BB_ell2_to_12"][0])
        new_par7.append(ev["parity_R_master_lmax7"])
        new_align.append(ev["n2_n3_align_cos"])
        # Exact Phase-3 lmax=8 pseudo-Cl / f_sky and alignment match
        tc = _clean_md_t(mtot[0], tmask)
        almt8 = hp.map2alm(tc, lmax=8)
        p_tt2.append(float(hp.alm2cl(almt8)[2] / f_sky_t))
        p_al8.append(float(_land_magueijo_axes(almt8, lmax_in=8)["n2_n3_align_cos"]))
        qm = np.where(pmask, mtot[1], 0.0); um = np.where(pmask, mtot[2], 0.0)
        alms = hp.map2alm([tc, qm, um], lmax=8, pol=True)
        p_ee2.append(float(hp.alm2cl(alms[1])[2] / f_sky_p))
        p_bb2.append(float(hp.alm2cl(alms[2])[2] / f_sky_p))

    obs_sm = obs_res["PR3_SMICA"]
    phase3 = json.loads(PHASE3_CMB_JSON.read_text(encoding="utf-8"))
    # Pseudo observation from Phase-3 for 75-pair count consistency
    p3_sm = phase3["eight_map_common_mask_lowell"]["PR3_SMICA"]
    p3_mc = phase3["raw_ffp10_smica_50mc_common_mask"]
    p3_match_err = max(
        abs(sm_p3_tt2 - p3_sm["cl_TT_ell2_to_8_K2"][0]),
        abs(sm_p3_ee2 - p3_sm["cl_EE_ell2_to_8_K2"][0]),
        abs(sm_p3_bb2 - p3_sm["cl_BB_ell2_to_8_K2"][0]),
        abs(sm_p3_al8 - p3_sm["n2_n3_alignment_abs_cos"]),
    )
    assert p3_match_err < 1e-12, f"Phase-3 estimator mismatch: {p3_match_err}"

    r25_c2_tt = p2p3_fast.working_rank_interval(obs_sm["cl_master_TT_ell2_to_12"][0], np.array(new_tt2), simulation_ids=new_ids, null_qualified=False)
    r25_c2_ee = p2p3_fast.working_rank_interval(obs_sm["cl_master_EE_ell2_to_12"][0], np.array(new_ee2), simulation_ids=new_ids, null_qualified=False)
    r25_c2_bb = p2p3_fast.working_rank_interval(obs_sm["cl_master_BB_ell2_to_12"][0], np.array(new_bb2), simulation_ids=new_ids, null_qualified=False)
    r25_par7 = p2p3_fast.working_rank_interval(obs_sm["parity_R_master_lmax7"], np.array(new_par7), simulation_ids=new_ids, null_qualified=False)
    r25_align = p2p3_fast.working_rank_interval(obs_sm["n2_n3_align_cos"], np.array(new_align), simulation_ids=new_ids, null_qualified=False)

    # Combined 75-pair lmax=8 1/f_sky pseudo rank (50 from Phase-3 + 25 new): exact higher counts summed
    hi75_tt = int(p3_mc["smica_c2_TT_rank"]["higher_than_observed"]) + int(np.sum(np.array(p_tt2) > p3_sm["cl_TT_ell2_to_8_K2"][0]))
    hi75_ee = int(p3_mc["smica_c2_EE_rank"]["higher_than_observed"]) + int(np.sum(np.array(p_ee2) > p3_sm["cl_EE_ell2_to_8_K2"][0]))
    hi75_bb = int(p3_mc["smica_c2_BB_rank"]["higher_than_observed"]) + int(np.sum(np.array(p_bb2) > p3_sm["cl_BB_ell2_to_8_K2"][0]))
    hi75_al = int(p3_mc["smica_l2_l3_alignment_rank"]["higher_than_observed"]) + int(np.sum(np.array(p_al8) > p3_sm["n2_n3_alignment_abs_cos"]))

    dt = time.perf_counter() - t0
    rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    payload = {
        "artifact_id": "R89_G05_PLANCK_SOLVER_FREE_RESEARCH_V1",
        "group_id": "G05_PLANCK",
        "create_only": True,
        "epistemic_status": "conditional",
        "runtime_sec": round(dt, 3),
        "max_rss_mb": round(rss_mb, 2),
        "platform": platform.platform(),
        "part_a_master_deconvolution": {
            "f_sky_T": float(np.mean(tmask)),
            "f_sky_P": float(np.mean(pmask)),
            "M_TT_cond": master["M_TT_cond"],
            "M_EB_cond": master["M_EB_cond"],
            "synthetic_200mc_validation": mc_val,
            "eight_observed_maps_master": obs_res,
        },
        "part_b_pr3_smica_splits": split_res,
        "part_c_smica_only_ffp10_mc": {
            "new_25_mc_00050_00074_master_ranks": {
                "c2_TT": r25_c2_tt,
                "c2_EE": r25_c2_ee,
                "c2_BB": r25_c2_bb,
                "parity_R_lmax7": r25_par7,
                "l2_l3_align": r25_align,
            },
            "combined_75_mc_pseudo_ranks": {
                "n_pairs": 75,
                "phase3_lmax8_obs_max_abs_diff": float(p3_match_err),
                "c2_TT_higher_of_75": hi75_tt,
                "c2_TT_rank_frac": float((hi75_tt + 1) / 76.0),
                "c2_EE_higher_of_75": hi75_ee,
                "c2_EE_rank_frac": float((hi75_ee + 1) / 76.0),
                "c2_BB_higher_of_75": hi75_bb,
                "c2_BB_rank_frac": float((hi75_bb + 1) / 76.0),
                "l2_l3_align_higher_of_75": hi75_al,
                "l2_l3_align_rank_frac": float((hi75_al + 1) / 76.0),
                "physical_p_value": None,
                "null_qualified": False,
            },
            "commander_ffp10_complete_fits": len(list(CMD_CMB_MC.glob("*.fits"))),
            "sq_cmb_null_status": "BLOCKED_INPUT",
        },
        "claim_hygiene": {
            "physical_Pi": None,
            "physical_GF": None,
            "bianchi_family_identified": False,
            "release_matched_null_pass": False,
            "note": "Master deconvolution validated on 200 synthetic Gaussian skies; Commander FFP10 remains incomplete (2 files), keeping SQ-CMB-NULL BLOCKED_INPUT.",
        },
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"group_id": "G05_RESEARCH", "runtime_sec": round(dt, 2), "max_rss_mb": round(rss_mb, 1), "mc_tt_bias_max": round(mc_val["max_abs_tt_rel_bias"], 4)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
