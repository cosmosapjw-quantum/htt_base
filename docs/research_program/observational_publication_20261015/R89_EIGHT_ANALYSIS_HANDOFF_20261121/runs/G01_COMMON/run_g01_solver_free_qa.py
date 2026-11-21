#!/usr/bin/env python3
"""R89 G01_COMMON Solver-Free Independent Numerical & Statistical QA (create-only).

Verifies all eight Section-2 Phase-3 computation paths cleanly without touching
R78/R86/R87/R88/R89 authorities or claiming 60/60 science pass:
1. GLS Cholesky whitening & projection identity on DES-Dovekie & Pantheon+SH0ES.
2. Rank-deficient design whitened SVD stability on DES-Dovekie 9p vs 4p.
3. Orthonormal STF basis equivalence (h03.STF vs fiveview.E & sphere-average 2/15 I_5).
4. VSH E1/B1/E2/B2 full-sky orthogonality, ICRS->Galactic SO(3), COSMO U=-U_IAU pure-E.
5. HEALPix masked pseudo-C_l & exact Wigner-3j Master coupling unity on f_sky=1.
6. Radio WLS dipole unbiased injection-recovery on NVSS-like and LoTSS-like NSIDE=16 masks.
7. SDSS 63 HAMHOD mocks distinctness (63 unique SHA256s, zero duplicates, sampling units).
8. Cross-probe matched-null & claim-hygiene verification across Phase-3 JSONs.
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
from astropy import units as u
from astropy.coordinates import SkyCoord
from scipy.linalg import cho_factor, cho_solve, solve_triangular
from scipy.special import roots_legendre
from sympy.physics.wigner import wigner_3j

ROOT = Path(__file__).resolve().parents[6]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from docs.research_program.observational_publication_20261015.H03_20261016.src.h03_tomography import (
    C_KM_S,
    STF,
    stf_features,
)
from scripts.r68.fiveview_geometry import E as FIVEVIEW_E
from scripts.r69.gaia_e2_b2 import templates as vsh_templates

OUT_DIR = Path(__file__).resolve().parent
OUT_JSON = OUT_DIR / "SOLVER_FREE_QA_RESULT.json"

RUNS_DIR = ROOT / "docs/research_program/observational_publication_20261015/R89_EIGHT_ANALYSIS_HANDOFF_20261121/runs"
WORKDIR = Path("/mnt/extdrive/workdir")
DES_DIR = WORKDIR / "raw/observational_bundles/DES_SN5YR_Dovekie"
PP_DIR = WORKDIR / "raw/pantheonplus_release_c447f0f_20261110"
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


def _qa_gls_and_svd() -> tuple[dict, dict]:
    # --- DES-Dovekie invert-then-subset + whitened SVD ---
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
                meta_map[(p[mcols.index("CID")], int(p[mcols.index("IDSURVEY")]))] = (
                    float(p[mcols.index("HOST_RA")]),
                    float(p[mcols.index("HOST_DEC")]),
                )
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
    c_full = np.linalg.inv(inv_cov)
    c_full = 0.5 * (c_full + c_full.T)

    sel = np.isfinite(mu) & np.isfinite(z_hd) & (z_hd > 0.01) & (hra > -900.0) & (hdec > -900.0)
    idx = np.flatnonzero(sel)
    c_des = c_full[np.ix_(idx, idx)]
    c_des = 0.5 * (c_des + c_des.T)
    n_des = _icrs_unit(hra[idx], hdec[idx])
    X9_des = np.column_stack([np.ones(len(idx)), n_des, stf_features(n_des)])
    X4_des = X9_des[:, :4]

    L_des = np.linalg.cholesky(c_des)
    Linv_C_LinvT = solve_triangular(L_des, solve_triangular(L_des, c_des, lower=True).T, lower=True)
    des_whiten_err = float(np.max(np.abs(Linv_C_LinvT - np.eye(len(idx)))))

    WX9 = solve_triangular(L_des, X9_des, lower=True)
    WX4 = solve_triangular(L_des, X4_des, lower=True)
    s9 = np.linalg.svd(WX9, compute_uv=False)
    s4 = np.linalg.svd(WX4, compute_uv=False)
    cf = cho_factor(c_des, lower=True)
    cinv_X4 = cho_solve(cf, X4_des)
    F4 = X4_des.T @ cinv_X4
    A4 = np.linalg.solve(F4, cinv_X4.T)
    des_proj_err = float(np.max(np.abs(A4 @ X4_des - np.eye(4))))

    # --- Pantheon+ whitening check ---
    with (PP_DIR / "Pantheon+SH0ES.dat").open("r", encoding="utf-8") as f:
        cols = f.readline().split()
        rows = [ln.split() for ln in f if ln.strip()]
    iz, ira, idec, ical = cols.index("zHD"), cols.index("RA"), cols.index("DEC"), cols.index("IS_CALIBRATOR")
    z_pp = np.array([float(r[iz]) for r in rows])
    ra_pp = np.array([float(r[ira]) for r in rows])
    dec_pp = np.array([float(r[idec]) for r in rows])
    cal_pp = np.array([int(r[ical]) for r in rows])
    sel_pp = (z_pp > 0.01) & (ra_pp >= 0) & (ra_pp <= 360) & (np.abs(dec_pp) <= 90) & (cal_pp == 0)
    idx_pp = np.flatnonzero(sel_pp)
    arr_cov = np.fromfile(PP_DIR / "Pantheon+SH0ES_STAT+SYS.cov", dtype=np.float64, sep=" ")
    n_pp = int(round(arr_cov[0]))
    c_pp = arr_cov[1:].reshape((n_pp, n_pp))[np.ix_(idx_pp, idx_pp)]
    c_pp = 0.5 * (c_pp + c_pp.T)
    L_pp = np.linalg.cholesky(c_pp)
    pp_whiten_err = float(np.max(np.abs(solve_triangular(L_pp, solve_triangular(L_pp, c_pp, lower=True).T, lower=True) - np.eye(len(idx_pp)))))
    n_pp_u = _icrs_unit(ra_pp[idx_pp], dec_pp[idx_pp])
    X9_pp = np.column_stack([np.ones(len(idx_pp)), n_pp_u, stf_features(n_pp_u)])
    s9_pp = np.linalg.svd(solve_triangular(L_pp, X9_pp, lower=True), compute_uv=False)

    gls_qa = {
        "pass": des_whiten_err < 1e-10 and des_proj_err < 1e-10 and pp_whiten_err < 1e-11,
        "des_n": int(len(idx)),
        "des_whitening_max_abs_err": des_whiten_err,
        "des_4p_projection_identity_err": des_proj_err,
        "pantheon_n": int(len(idx_pp)),
        "pantheon_whitening_max_abs_err": pp_whiten_err,
    }
    svd_qa = {
        "pass": bool((s9[0] / s9[-1]) ** 2 > 1e8 and (s9_pp[0] / s9_pp[-1]) < 20.0),
        "des_9p_singular_values": s9.tolist(),
        "des_9p_F_cond_from_svd": float((s9[0] / s9[-1]) ** 2),
        "des_4p_singular_values": s4.tolist(),
        "des_4p_F_cond_from_svd": float((s4[0] / s4[-1]) ** 2),
        "pantheon_9p_singular_values": s9_pp.tolist(),
        "pantheon_9p_F_cond_from_svd": float((s9_pp[0] / s9_pp[-1]) ** 2),
    }
    return gls_qa, svd_qa


def _qa_stf_basis() -> dict:
    parity_diff = float(np.max(np.abs(STF - FIVEVIEW_E)))
    frob_gram = np.einsum("aij,bij->ab", STF, STF)
    frob_err = float(np.max(np.abs(frob_gram - np.eye(5))))

    mu, wt = roots_legendre(48)
    phi = np.arange(96) * (2.0 * np.pi / 96.0)
    mm, pp = np.meshgrid(mu, phi, indexing="ij")
    th = np.arccos(mm.ravel())
    ph = pp.ravel()
    n = np.column_stack([np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)])
    w = np.repeat(wt / (2.0 * 96.0), 96)
    feats = stf_features(n)
    sph_gram = (feats * w[:, None]).T @ feats
    sph_err = float(np.max(np.abs(sph_gram - (2.0 / 15.0) * np.eye(5))))
    return {
        "pass": parity_diff == 0.0 and frob_err < 1e-14 and sph_err < 1e-13,
        "max_abs_h03_minus_fiveview_E": parity_diff,
        "frobenius_gram_max_err": frob_err,
        "sphere_integral_2_over_15_I5_max_err": sph_err,
    }


def _qa_vsh_frames_and_cosmo() -> dict:
    # Full-sky orthogonality of 16 VSH modes via exact spherical Gauss-Legendre quadrature
    mu, wt = roots_legendre(48)
    phi = np.arange(96) * (2.0 * np.pi / 96.0)
    mm, pp = np.meshgrid(mu, phi, indexing="ij")
    dec = np.arcsin(mm.ravel())
    ra = pp.ravel()
    w = np.repeat(wt / (2.0 * 96.0), 96)
    _, B = vsh_templates(ra, dec)
    G = np.einsum("pda,p,pdb->ab", B, w, B)
    expected_diag = np.array([2.0 / 3.0] * 6 + [1.0 / 5.0] * 10)
    vsh_err = float(np.max(np.abs(G - np.diag(expected_diag))))

    # ICRS->Galactic SO(3)
    sc = SkyCoord(ra=[0.0, 90.0, 0.0] * u.deg, dec=[0.0, 0.0, 90.0] * u.deg, frame="icrs").galactic
    R = np.column_stack([
        [
            math.cos(math.radians(float(p.b.deg))) * math.cos(math.radians(float(p.l.deg))),
            math.cos(math.radians(float(p.b.deg))) * math.sin(math.radians(float(p.l.deg))),
            math.sin(math.radians(float(p.b.deg))),
        ]
        for p in sc
    ])
    ortho_err = float(np.max(np.abs(R.T @ R - np.eye(3))))
    det_err = float(abs(np.linalg.det(R) - 1.0))

    # Pure E-mode synthetic COSMO Stokes U convention vs IAU convention
    ns = 32
    lmax = 6
    alm_true = np.zeros((3, hp.Alm.getsize(lmax)), dtype=np.complex128)
    alm_true[1, hp.Alm.getidx(lmax, 2, 0)] = 1.0 + 0.0j
    alm_true[1, hp.Alm.getidx(lmax, 4, 2)] = 0.4 + 0.3j
    _, q_cosmo, u_cosmo = hp.alm2map(alm_true, nside=ns, lmax=lmax, pol=True)
    # Interpret synthetic (q, -u_cosmo) as IAU Stokes U -> must negate U_IAU back to U_COSMO
    alms_cosmo = hp.map2alm([np.zeros_like(q_cosmo), q_cosmo, u_cosmo], lmax=lmax, pol=True)
    alms_iau_unflipped = hp.map2alm([np.zeros_like(q_cosmo), q_cosmo, -u_cosmo], lmax=lmax, pol=True)
    cl_b_cosmo = float(np.max(hp.alm2cl(alms_cosmo[2])))
    cl_b_wrong = float(np.max(hp.alm2cl(alms_iau_unflipped[2])))

    return {
        "pass": vsh_err < 1e-12 and ortho_err < 1e-14 and det_err < 1e-14 and cl_b_cosmo < 1e-10 and cl_b_wrong > 1e-2,
        "vsh_16mode_fullsky_gram_max_err": vsh_err,
        "icrs_to_gal_orthogonality_err": ortho_err,
        "icrs_to_gal_det_minus_1": det_err,
        "cosmo_pure_E_residual_max_cl_B": cl_b_cosmo,
        "unflipped_iau_spurious_max_cl_B": cl_b_wrong,
    }


def _master_scalar_coupling(w_ell: np.ndarray, lmax_out: int) -> np.ndarray:
    lmax_w = len(w_ell) - 1
    M = np.zeros((lmax_out + 1, lmax_out + 1), dtype=np.float64)
    fac = (2.0 * np.arange(lmax_w + 1) + 1.0) * w_ell / (4.0 * np.pi)
    for l1 in range(lmax_out + 1):
        for l2 in range(lmax_out + 1):
            s = 0.0
            for l3 in range(abs(l1 - l2), min(l1 + l2, lmax_w) + 1):
                if (l1 + l2 + l3) % 2 == 0 and fac[l3] != 0.0:
                    w0 = float(wigner_3j(l1, l2, l3, 0, 0, 0))
                    s += fac[l3] * (w0 * w0)
            M[l1, l2] = (2.0 * l2 + 1.0) * s
    return M


def _qa_healpix_master() -> dict:
    # Exact unity at full sky f_sky = 1 (iter=3 removes pixel ring quadrature residual)
    ones = np.ones(hp.nside2npix(32), dtype=np.float64)
    w_full = hp.anafast(ones, lmax=16, iter=3)
    M_full = _master_scalar_coupling(w_full, lmax_out=8)
    id_err = float(np.max(np.abs(M_full - np.eye(9))))

    # Real Planck common T mask condition check on NSIDE=64
    tmask = hp.ud_grade(hp.read_map(str(WORKDIR / "raw/planck_data/COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits"), field=0, nest=True), 64, order_in="NESTED", order_out="RING") >= 0.9
    w_planck = hp.anafast(tmask.astype(np.float64), lmax=20)
    M_p = _master_scalar_coupling(w_planck, lmax_out=8)[2:9, 2:9]
    cond_p = float(np.linalg.cond(M_p))
    return {
        "pass": id_err < 1e-10 and cond_p < 5.0,
        "fullsky_master_TT_identity_err": id_err,
        "planck_common_mask_fsky": float(np.mean(tmask)),
        "planck_master_TT_2_to_8_cond": cond_p,
    }


def _qa_radio_dipole_recovery() -> dict:
    nside = 16
    npix = hp.nside2npix(nside)
    th, ph = hp.pix2ang(nside, np.arange(npix))
    pix_n = np.column_stack([np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)])
    pix_dec = 90.0 - np.rad2deg(th)
    sc_g = SkyCoord(ra=np.rad2deg(ph) * u.deg, dec=pix_dec * u.deg, frame="icrs").galactic
    pix_b = sc_g.b.deg
    d_true = np.array([-0.022, 0.008, 0.014], dtype=np.float64)

    errs = {}
    for name, m in [("nvss_like", (pix_dec >= -40.0) & (np.abs(pix_b) > 15.0)), ("lotss_like", (pix_dec >= 25.0) & (np.abs(pix_b) > 20.0))]:
        y = pix_n[m] @ d_true + 0.05  # inject nonzero monopole offset + exact dipole
        X = np.column_stack([pix_n[m], np.ones(int(np.sum(m)))])
        w = np.linspace(50.0, 200.0, int(np.sum(m)))
        s = np.sqrt(w)
        beta, *_ = np.linalg.lstsq(s[:, None] * X, s * y, rcond=None)
        errs[name] = {
            "n_pix": int(np.sum(m)),
            "dipole_recovery_max_abs_err": float(np.max(np.abs(beta[:3] - d_true))),
            "monopole_recovery_err": float(abs(beta[3] - 0.05)),
        }
    return {
        "pass": all(v["dipole_recovery_max_abs_err"] < 1e-12 for v in errs.values()),
        "masks": errs,
    }


def _qa_sdss_mock_uniqueness() -> dict:
    mocks = sorted(SDSS_MOCK_DIR.glob("MOCK_HAMHOD_SDSS_v5_R19*.0_err_corr"))
    shas = [_sha256(p) for p in mocks]
    row_counts = []
    for p in mocks:
        with p.open("r", encoding="ascii") as f:
            row_counts.append(sum(1 for _ in f) - 1)
    return {
        "pass": len(mocks) == 63 and len(set(shas)) == 63,
        "n_mock_files": len(mocks),
        "n_unique_sha256": len(set(shas)),
        "min_rows": min(row_counts),
        "median_rows": int(np.median(row_counts)),
        "max_rows": max(row_counts),
        "sampling_unit": "Independent SDSS-footprint HAMHOD mock realization per file; does NOT match CF4 35,970-group sky/selection",
    }


def _qa_claim_hygiene_and_crossprobe() -> dict:
    g8 = json.loads((RUNS_DIR / "G08_OPTICAL_PHY/CROSSPROBE_SYNTHESIS_RESULT.json").read_text(encoding="utf-8"))
    g2 = json.loads((RUNS_DIR / "G02_CF4/DEEP_MULTISURVEY_RESULT.json").read_text(encoding="utf-8"))
    g3 = json.loads((RUNS_DIR / "G03_GAIA/DEEP_SCANLAW_VLBA_RESULT.json").read_text(encoding="utf-8"))
    g4 = json.loads((RUNS_DIR / "G04_RADIO_FRAME/DEEP_FIVE_SURVEY_RESULT.json").read_text(encoding="utf-8"))
    g5 = json.loads((RUNS_DIR / "G05_PLANCK/DEEP_MULTIPIPELINE_CMB_RESULT.json").read_text(encoding="utf-8"))

    checks = {
        "g2_sq_cf4_blocked": g2["sq_cf4_status"] == "BLOCKED_INPUT",
        "g5_sq_cmb_null_blocked": g5["node_verdicts"]["SQ-CMB-NULL"] == "BLOCKED_INPUT",
        "g8_60_nodes_unique": g8["r78_r89_60_node_accounting"]["total_unique_nodes_covered"] == 60,
        "g8_next_action_is_sq_cf4": g8["r78_r89_60_node_accounting"]["r78_next_action_id"] == "SQ-CF4",
        "g8_not_60_pass": g8["r78_r89_60_node_accounting"]["sixty_of_sixty_science_pass"] is False,
        "all_physical_Pi_null": all(x["claim_hygiene"]["physical_Pi"] is None for x in (g2, g3, g4, g5, g8)),
        "all_physical_GF_null": all(x["claim_hygiene"]["physical_GF"] is None for x in (g2, g3, g4, g5, g8)),
    }
    return {"pass": all(checks.values()), "checks": checks}


def main() -> int:
    if OUT_JSON.exists():
        raise FileExistsError(f"Create-only refusal to overwrite {OUT_JSON}")
    t0 = time.perf_counter()

    gls_qa, svd_qa = _qa_gls_and_svd()
    stf_qa = _qa_stf_basis()
    vsh_qa = _qa_vsh_frames_and_cosmo()
    master_qa = _qa_healpix_master()
    radio_qa = _qa_radio_dipole_recovery()
    mock_qa = _qa_sdss_mock_uniqueness()
    hygiene_qa = _qa_claim_hygiene_and_crossprobe()

    all_pass = all(x["pass"] for x in (gls_qa, svd_qa, stf_qa, vsh_qa, master_qa, radio_qa, mock_qa, hygiene_qa))
    if not all_pass:
        raise RuntimeError("One or more G01 solver-free QA checks failed")

    dt = time.perf_counter() - t0
    rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    payload = {
        "artifact_id": "R89_G01_COMMON_SOLVER_FREE_QA_V1",
        "group_id": "G01_COMMON",
        "create_only": True,
        "runtime_sec": round(dt, 3),
        "max_rss_mb": round(rss_mb, 2),
        "platform": platform.platform(),
        "epistemic_status": "numerically_checked",
        "qa_checks": {
            "1_gls_whitening": gls_qa,
            "2_rank_deficient_svd": svd_qa,
            "3_stf_basis_convention": stf_qa,
            "4_vsh_frames_and_cosmo_stokes": vsh_qa,
            "5_healpix_master_coupling": master_qa,
            "6_radio_wls_recovery": radio_qa,
            "7_sdss_63_mocks_uniqueness": mock_qa,
            "8_crossprobe_claim_hygiene": hygiene_qa,
        },
        "claim_hygiene": {
            "physical_Pi": None,
            "physical_GF": None,
            "bianchi_family_identified": False,
            "sixty_of_sixty_science_pass": False,
        },
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"group_id": "G01_QA", "all_pass": all_pass, "runtime_sec": round(dt, 2), "max_rss_mb": round(rss_mb, 1)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
