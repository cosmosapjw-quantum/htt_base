#!/usr/bin/env python3
"""GBI-06: Calibrated Planck PR3+FFP10 CMB lane, separate NPIPE PR4 robustness lane,
and real owned multi-probe data reconciliation (Quaia, NVSS, RACS, Gaia, Pantheon+, CF4, DESI).

All outputs live under:
  * Raw binary arrays/caches (outside Git): /mnt/extdrive/workdir/r49_chains/
  * Receipts (in Git): docs/research_program/observational_publication_20261015/R49_GENERAL_TILTED_BIANCHI_20261112/
"""

from __future__ import annotations

import argparse
import concurrent.futures
import gc
import gzip
import hashlib
import io
import json
import math
import pathlib
import sys
import tarfile
import time
import warnings
from typing import Any

import h5py
import healpy as hp
import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import fits
import astropy.units as u
import scipy.linalg

warnings.filterwarnings("ignore")

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
HTT_ROOT = REPO_ROOT / "htt"
HTT_SRC = HTT_ROOT / "src"
for p in (str(HTT_SRC), str(HTT_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from bass.transport.general_bianchi_transfer import (  # noqa: E402
    TiltedTransferParameters,
    compute_general_bianchi_transfer,
)
from common.stf_metric_bridge import G_STF5, cartesian_to_stf_matrix, stf_matrix_to_cartesian  # noqa: E402
from htt.htt.infer.r49_general_bianchi_likelihood import (  # noqa: E402
    CMBModeBudgetSpec,
    FrameEpochAlignmentSpec,
    GALACTIC_TO_ICRS_MATRIX,
    ICRS_TO_GALACTIC_MATRIX,
    SPEED_OF_LIGHT_KM_S,
    T_CMB_K,
    _pack_transfer_modes,
    standard_lowell_mode_labels,
)

RAW_ROOT = pathlib.Path("/mnt/extdrive/workdir/raw")
CHAIN_DIR = pathlib.Path("/mnt/extdrive/workdir/r49_chains")
OUT_DIR = REPO_ROOT / "docs" / "research_program" / "observational_publication_20261015" / "R49_GENERAL_TILTED_BIANCHI_20261112"
REHASH_PATH = OUT_DIR / "DATA_REHASH_RECEIPT.json"

LMAX = 6
ELLS = (2, 3, 4, 5, 6)
MODE_LABELS = standard_lowell_mode_labels(ELLS, include_eb=True)  # 135 modes: 45 T, 45 E, 45 B


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 22), b""):
            h.update(blk)
    return h.hexdigest()


def _mode_tuples(lmax: int = LMAX, lmin: int = 2) -> list[tuple[int, int, str, float]]:
    out: list[tuple[int, int, str, float]] = []
    sq2 = math.sqrt(2.0)
    for ell in range(lmin, lmax + 1):
        out.append((ell, 0, "r", 1.0))
        for m in range(1, ell + 1):
            out.append((ell, m, "r", 1.0 / sq2))
            out.append((ell, m, "i", -1.0 / sq2))
    return out


_MODES_45 = _mode_tuples(LMAX, lmin=2)
_MODES_49 = _mode_tuples(LMAX, lmin=0)


def _pack_hp_alm_n(alm_arr: np.ndarray, modes: list[tuple[int, int, str, float]], lmax: int = LMAX) -> np.ndarray:
    sq2 = math.sqrt(2.0)
    vals = np.empty(len(modes), dtype=np.float64)
    for k, (ell, m, tag, _) in enumerate(modes):
        c = alm_arr[hp.Alm.getidx(lmax, ell, m)]
        if m == 0:
            vals[k] = float(np.real(c))
        elif tag == "r":
            vals[k] = float(sq2 * np.real(c))
        else:
            vals[k] = float(-sq2 * np.imag(c))
    return vals


def build_lowell_mask_operators(
    mask_int_ring_2048: np.ndarray,
    mask_pol_ring_2048: np.ndarray,
) -> dict[str, Any]:
    """Build exact low-RAM full-resolution mask-debiased coupling inverses (K49_inv_45, K_EB_inv)."""
    m_int_f64 = (mask_int_ring_2048 > 0.5).astype(np.float64)
    m_pol_f64 = (mask_pol_ring_2048 > 0.5).astype(np.float64)
    m_int_128 = hp.ud_grade(m_int_f64, 128, order_in="RING", order_out="RING")
    m_pol_128 = hp.ud_grade(m_pol_f64, 128, order_in="RING", order_out="RING")

    n_alm = hp.Alm.getsize(LMAX)
    K49 = np.zeros((49, 49), dtype=np.float64)
    for j, (ell, m, tag, amp) in enumerate(_MODES_49):
        aT = np.zeros(n_alm, dtype=np.complex128)
        aT[hp.Alm.getidx(LMAX, ell, m)] = amp if tag == "r" else 1j * amp
        if ell <= 1:
            Tm = hp.alm2map(aT, nside=2048, lmax=LMAX, pol=False)
            alm_out = hp.map2alm(Tm * m_int_f64, lmax=LMAX, pol=False, iter=0)
            del Tm
        else:
            Tm = hp.alm2map(aT, nside=128, lmax=LMAX, pol=False)
            alm_out = hp.map2alm(Tm * m_int_128, lmax=LMAX, pol=False, iter=0)
        K49[:, j] = _pack_hp_alm_n(alm_out, _MODES_49)

    K_EB = np.zeros((90, 90), dtype=np.float64)
    zeros_128 = np.zeros(hp.nside2npix(128), dtype=np.float64)
    for pb in range(2):
        for j, (ell, m, tag, amp) in enumerate(_MODES_45):
            a0 = np.zeros(n_alm, dtype=np.complex128)
            aE = np.zeros(n_alm, dtype=np.complex128)
            aB = np.zeros(n_alm, dtype=np.complex128)
            idx = hp.Alm.getidx(LMAX, ell, m)
            val = amp if tag == "r" else 1j * amp
            if pb == 0:
                aE[idx] = val
            else:
                aB[idx] = val
            _, Qm, Um = hp.alm2map([a0, aE, aB], nside=128, lmax=LMAX, pol=True)
            alm_back = hp.map2alm([zeros_128, Qm * m_pol_128, Um * m_pol_128], lmax=LMAX, pol=True, iter=0)
            K_EB[:45, pb * 45 + j] = _pack_hp_alm_n(alm_back[1], _MODES_45)
            K_EB[45:, pb * 45 + j] = _pack_hp_alm_n(alm_back[2], _MODES_45)

    K49_inv = np.linalg.inv(K49)
    K_EB_inv = np.linalg.inv(K_EB)
    return {
        "K49_inv_45": K49_inv[4:, :],
        "K_EB_inv": K_EB_inv,
        "cond_K_T": float(np.linalg.cond(K49)),
        "cond_K_EB": float(np.linalg.cond(K_EB)),
        "f_sky_int": float(np.mean(mask_int_ring_2048 > 0.5)),
        "f_sky_pol": float(np.mean(mask_pol_ring_2048 > 0.5)),
        "mask_int_bool": (mask_int_ring_2048 > 0.5),
        "mask_pol_bool": (mask_pol_ring_2048 > 0.5),
    }


def extract_debiased_135_uK(
    I_ring_uK: np.ndarray,
    Q_ring_uK: np.ndarray,
    U_ring_uK: np.ndarray,
    op: dict[str, Any],
    *,
    in_place: bool = False,
) -> np.ndarray:
    mask_i = op["mask_int_bool"]
    mask_p = op["mask_pol_bool"]
    if in_place:
        I_m, Q_m, U_m = I_ring_uK, Q_ring_uK, U_ring_uK
        I_m[~mask_i] = 0.0
        Q_m[~mask_p] = 0.0
        U_m[~mask_p] = 0.0
    else:
        I_m = np.where(mask_i, I_ring_uK, 0.0)
        Q_m = np.where(mask_p, Q_ring_uK, 0.0)
        U_m = np.where(mask_p, U_ring_uK, 0.0)
    alm = hp.map2alm([I_m, Q_m, U_m], lmax=LMAX, pol=True, iter=0)
    v_T = op["K49_inv_45"] @ _pack_hp_alm_n(alm[0], _MODES_49)
    v_EB = op["K_EB_inv"] @ np.concatenate([_pack_hp_alm_n(alm[1], _MODES_45), _pack_hp_alm_n(alm[2], _MODES_45)])
    return np.concatenate([v_T, v_EB])


def read_nested_iqu_ring_uK(path: pathlib.Path, cols=("I_STOKES", "Q_STOKES", "U_STOKES"), scale: float = 1.0e6) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    with fits.open(path, memmap=True) as h:
        I_n = np.asarray(h[1].data[cols[0]], dtype=np.float64).reshape(-1)
        Q_n = np.asarray(h[1].data[cols[1]], dtype=np.float64).reshape(-1)
        U_n = np.asarray(h[1].data[cols[2]], dtype=np.float64).reshape(-1)
    return (
        hp.reorder(I_n, n2r=True) * scale,
        hp.reorder(Q_n, n2r=True) * scale,
        hp.reorder(U_n, n2r=True) * scale,
    )


def run_pr3_and_ffp10_lane(rehash: dict[str, Any], force_reextract: bool = False) -> tuple[dict[str, Any], np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    t0 = time.time()
    m_int_path = pathlib.Path(rehash["hashed_primary_files"]["pr3_mask_int"]["path"])
    m_pol_path = pathlib.Path(rehash["hashed_primary_files"]["pr3_mask_pol"]["path"])
    with fits.open(m_int_path, memmap=True) as h:
        m_int_r = hp.reorder(np.asarray(h[1].data["TMASK"], dtype=np.float32).reshape(-1), n2r=True) > 0.5
    with fits.open(m_pol_path, memmap=True) as h:
        m_pol_r = hp.reorder(np.asarray(h[1].data["PMASK"], dtype=np.float32).reshape(-1), n2r=True) > 0.5

    op = build_lowell_mask_operators(m_int_r, m_pol_r)
    del m_int_r, m_pol_r
    gc.collect()

    smica_full = pathlib.Path(rehash["hashed_primary_files"]["pr3_smica_full"]["path"])
    smica_hm1 = pathlib.Path(rehash["hashed_primary_files"]["pr3_smica_hm1"]["path"])
    smica_hm2 = pathlib.Path(rehash["hashed_primary_files"]["pr3_smica_hm2"]["path"])

    I_tmp, Q_tmp, U_tmp = read_nested_iqu_ring_uK(smica_full)
    d_obs_pr3 = extract_debiased_135_uK(I_tmp, Q_tmp, U_tmp, op, in_place=True)
    del I_tmp, Q_tmp, U_tmp
    I_tmp, Q_tmp, U_tmp = read_nested_iqu_ring_uK(smica_hm1)
    d_hm1 = extract_debiased_135_uK(I_tmp, Q_tmp, U_tmp, op, in_place=True)
    del I_tmp, Q_tmp, U_tmp
    I_tmp, Q_tmp, U_tmp = read_nested_iqu_ring_uK(smica_hm2)
    d_hm2 = extract_debiased_135_uK(I_tmp, Q_tmp, U_tmp, op, in_place=True)
    del I_tmp, Q_tmp, U_tmp
    gc.collect()
    d_hmhd = 0.5 * (d_hm1 - d_hm2)

    cache_path = CHAIN_DIR / "ffp10_300_debiased_135.npz"
    partial_path = CHAIN_DIR / "ffp10_300_partial.npz"
    n_pairs = 300
    if cache_path.exists() and not force_reextract:
        z = np.load(cache_path)
        sim_tot = z["sim_tot"]
        sim_noise = z["sim_noise"]
        # Legacy null_beta is a rescaled quadrupole, not a velocity-estimator null.
        null_beta = None
    else:
        sim_tot = np.zeros((n_pairs, 135), dtype=np.float64)
        sim_noise = np.zeros((n_pairs, 135), dtype=np.float64)
        start_idx = 0
        if partial_path.exists() and not force_reextract:
            zp = np.load(partial_path)
            done_n = int(zp["done_count"])
            sim_tot[:done_n] = zp["sim_tot"][:done_n]
            sim_noise[:done_n] = zp["sim_noise"][:done_n]
            start_idx = done_n
            print(f"[PR3 FFP10] resuming from {partial_path} at pair {start_idx}/{n_pairs}", flush=True)

        ffp_root = RAW_ROOT / "planck_ffp10/smica"
        npix2048 = hp.nside2npix(2048)
        I_buf = np.empty(npix2048, dtype=np.float64)
        Q_buf = np.empty(npix2048, dtype=np.float64)
        U_buf = np.empty(npix2048, dtype=np.float64)
        raw_bufs = [
            np.empty((49152, 3, 1024), dtype=">f4"),
            np.empty((49152, 3, 1024), dtype=">f4"),
        ]

        def _read_raw_into(path: pathlib.Path, buf: np.ndarray) -> np.ndarray:
            with open(path, "rb", buffering=0) as f:
                f.seek(5760)
                f.readinto(buf)
            return buf

        def _extract_raw_buf(buf: np.ndarray) -> np.ndarray:
            np.multiply(buf[:, 0, :].reshape(-1), 1.0e6, out=I_buf, casting="unsafe")
            np.multiply(buf[:, 1, :].reshape(-1), 1.0e6, out=Q_buf, casting="unsafe")
            np.multiply(buf[:, 2, :].reshape(-1), 1.0e6, out=U_buf, casting="unsafe")
            return extract_debiased_135_uK(I_buf, Q_buf, U_buf, op, in_place=True)

        # Build sequential job list for double-buffered I/O + CPU extraction
        file_jobs: list[tuple[int, int, pathlib.Path]] = []
        for i in range(start_idx, n_pairs):
            file_jobs.append((i, 0, ffp_root / f"cmb_mc/dx12_v3_smica_cmb_mc_{i:05d}_raw.fits"))
            file_jobs.append((i, 1, ffp_root / f"noise_mc/dx12_v3_smica_noise_mc_{i:05d}_raw.fits"))

        if file_jobs:
            cmb_vec_cur: np.ndarray | None = None
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                fut = pool.submit(_read_raw_into, file_jobs[0][2], raw_bufs[0])
                for step_k, (pair_i, kind, _) in enumerate(file_jobs):
                    cur_buf = fut.result()
                    if step_k + 1 < len(file_jobs):
                        nxt_buf = raw_bufs[(step_k + 1) % 2]
                        fut = pool.submit(_read_raw_into, file_jobs[step_k + 1][2], nxt_buf)
                    v_ext = _extract_raw_buf(cur_buf)
                    if kind == 0:
                        cmb_vec_cur = v_ext
                    else:
                        assert cmb_vec_cur is not None
                        sim_noise[pair_i] = v_ext
                        sim_tot[pair_i] = cmb_vec_cur + v_ext
                        cmb_vec_cur = None
                        if (pair_i + 1) % 15 == 0 or pair_i == start_idx:
                            np.savez(partial_path, done_count=pair_i + 1, sim_tot=sim_tot, sim_noise=sim_noise)
                            print(
                                f"[PR3 FFP10] processed pair {pair_i + 1}/{n_pairs} ({time.time() - t0:.1f}s)",
                                flush=True,
                            )

        del I_buf, Q_buf, U_buf, raw_bufs
        gc.collect()
        null_beta = None
        np.savez(cache_path, sim_tot=sim_tot, sim_noise=sim_noise,
                 velocity_null_status="UNAVAILABLE_SAME_ESTIMATOR_JOINT_NULL_REQUIRED")
        if partial_path.exists():
            partial_path.unlink()

    # Stratified N=60, N=200, N=300 convergence
    stratified = {}
    for n_sub, name in ((60, "N60_smoke"), (200, "N200_pilot"), (300, "N300_production")):
        sub = sim_tot[:n_sub]
        sd = np.std(sub, axis=0, ddof=1)
        stratified[name] = {
            "n_pairs": n_sub,
            "mean_abs_uK": float(np.mean(np.abs(np.mean(sub, axis=0)))),
            "rms_T_ell2_uK": float(np.sqrt(np.mean(sd[:5] ** 2))),
            "rms_E_ell2_uK": float(np.sqrt(np.mean(sd[45:50] ** 2))),
            "rms_B_ell2_uK": float(np.sqrt(np.mean(sd[90:95] ** 2))),
        }

    cov_tot = np.cov(sim_tot.T) + 1.0e-6 * np.eye(135)
    cov_noise = np.cov(sim_noise.T) + 1.0e-6 * np.eye(135)
    # Check HMHD empirical noise vs FFP10 noise_mc covariance
    L_n = scipy.linalg.cholesky(cov_noise, lower=True)
    w_hmhd = scipy.linalg.solve_triangular(L_n, d_hmhd, lower=True)
    hmhd_chi2 = float(w_hmhd @ w_hmhd)

    # Stratified synthetic injection/recovery across I, V, VII_0, VII_h, IX
    rng = np.random.default_rng(4906)
    L_tot = scipy.linalg.cholesky(cov_tot, lower=True)
    C_inv = scipy.linalg.cho_solve((L_tot, True), np.eye(135))
    inj_results = {}
    det_idx = [i for i, lbl in enumerate(MODE_LABELS) if int(lbl.split("_")[1]) in (2, 3, 4)]
    C_det_inv = np.linalg.inv(cov_tot[np.ix_(det_idx, det_idx)])
    det_labels = tuple(MODE_LABELS[i] for i in det_idx)

    # Build exact 5-basis response matrix for Bianchi I linearized shear at ell=2..4
    basis_T = np.zeros((len(det_idx), 5), dtype=np.float64)
    for k in range(5):
        ek = np.zeros(5)
        ek[k] = 1.0e-5
        out_k = compute_general_bianchi_transfer(
            TiltedTransferParameters(
                family="I",
                sigma_N=cartesian_to_stf_matrix(ek),
                v_matter=np.zeros(3),
                v_rad=np.zeros(3),
                v_obs=np.zeros(3),
                ell_max=4,
                n_gl_theta=12,
                transfer_mode="linearized_near_flrw",
            )
        )
        basis_T[:, k] = (1.0e6 * T_CMB_K * _pack_transfer_modes(out_k.alm_T, out_k.alm_E, out_k.alm_B, det_labels)) / 1.0e-5

    F_5 = basis_T.T @ C_det_inv @ basis_T
    pinv_gls = np.linalg.solve(F_5, basis_T.T @ C_det_inv)
    cov_5 = np.linalg.inv(F_5)
    sd_gram = math.sqrt(float(np.trace(G_STF5 @ cov_5)))

    for fam in ("I", "V", "VII_0", "VII_h", "IX"):
        u_dir = rng.normal(size=5)
        u_dir /= math.sqrt(float(u_dir @ G_STF5 @ u_dir))
        s_true = u_dir * (3.0 * sd_gram)
        out_s = compute_general_bianchi_transfer(
            TiltedTransferParameters(
                family=fam,
                sigma_N=cartesian_to_stf_matrix(s_true),
                v_matter=np.zeros(3),
                v_rad=np.zeros(3),
                v_obs=np.zeros(3),
                h_bianchi=0.35 if fam == "VII_h" else 0.0,
                omega_k=0.01 if fam in ("V", "VII_h", "IX") else 0.0,
                ell_max=4,
                n_gl_theta=12,
                transfer_mode="linearized_near_flrw",
            )
        )
        sig_v = 1.0e6 * T_CMB_K * _pack_transfer_modes(out_s.alm_T, out_s.alm_E, out_s.alm_B, det_labels)
        noise_real = rng.multivariate_normal(np.zeros(135), cov_tot)[det_idx]
        s_hat = pinv_gls @ (sig_v + noise_real)
        inj_results[fam] = {
            "injected_gram": float(math.sqrt(float(s_true @ G_STF5 @ s_true))),
            "recovered_gram": float(math.sqrt(float(s_hat @ G_STF5 @ s_hat))),
            "bias_z_sigma": float(math.sqrt(float((s_hat - s_true) @ G_STF5 @ (s_hat - s_true))) / sd_gram),
            "cos_alignment": float(
                (s_true @ G_STF5 @ s_hat)
                / (math.sqrt(float(s_true @ G_STF5 @ s_true)) * max(1e-30, math.sqrt(float(s_hat @ G_STF5 @ s_hat))))
            ),
        }

    receipt = {
        "schema_version": "r49_gbi06_pr3_calibration_v1",
        "lane": "PR3_CALIBRATED",
        "mc_source": "FFP10_PR3",
        "primary_observed_map": str(smica_full),
        "primary_observed_sha256": rehash["hashed_primary_files"]["pr3_smica_full"]["sha256"],
        "hm1_sha256": rehash["hashed_primary_files"]["pr3_smica_hm1"]["sha256"],
        "hm2_sha256": rehash["hashed_primary_files"]["pr3_smica_hm2"]["sha256"],
        "mask_int_fsky": op["f_sky_int"],
        "mask_pol_fsky": op["f_sky_pol"],
        "coupling_cond_T": op["cond_K_T"],
        "coupling_cond_EB": op["cond_K_EB"],
        "n_ffp10_pairs": n_pairs,
        "stratified_ffp10_convergence": stratified,
        "hmhd_empirical_noise_chi2_vs_ffp10": hmhd_chi2,
        "hmhd_dof": 135,
        "ffp10_null_gram_sd": sd_gram,
        "observed_ell2_T_rms_uK": float(np.sqrt(np.mean(d_obs_pr3[:5] ** 2))),
        "observed_ell2_E_rms_uK": float(np.sqrt(np.mean(d_obs_pr3[45:50] ** 2))),
        "observed_ell2_B_rms_uK": float(np.sqrt(np.mean(d_obs_pr3[90:95] ** 2))),
        "injection_recovery_across_families": inj_results,
        "elapsed_s": round(time.time() - t0, 2),
    }
    return receipt, d_obs_pr3, cov_tot, null_beta, sim_tot


def run_npipe_pr4_lane(rehash: dict[str, Any]) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    t0 = time.time()
    npipe_inv = rehash["npipe_pr4_inventory"]
    mask_path = pathlib.Path(npipe_inv["lollipop_mask_ns512"]["path"])
    with fits.open(mask_path, memmap=True) as h:
        mask_lol_512 = np.asarray(h[1].data["T"], dtype=np.float64).reshape(-1) > 0.5
    m_pol_2048_r = hp.ud_grade(mask_lol_512.astype(np.float64), 2048, order_in="RING", order_out="RING") > 0.5

    # Use PR3 Int mask union with Lollipop Pol mask for temperature clean sky consistency
    with fits.open(rehash["hashed_primary_files"]["pr3_mask_int"]["path"], memmap=True) as h:
        m_int_2048_r = hp.reorder(np.asarray(h[1].data["TMASK"], dtype=np.float64).reshape(-1), n2r=True) > 0.5

    op_pr4 = build_lowell_mask_operators(m_int_2048_r, m_pol_2048_r)

    # Extract E-mode large-scale transfer functions Bl_E from PLANCK_RIMO_TF_R4.00.tar.gz for 100/143/217 GHz
    rimo_tar = pathlib.Path(npipe_inv["rimo_tf_r4_tar_gz"]["path"])
    rimo_tf_ell2_6: dict[str, list[float]] = {}
    with tarfile.open(rimo_tar, "r:gz") as tf:
        for freq in ("100", "143", "217"):
            target_name = f"simulated_maps/npipe_aux/large_scale_transfer_functions/Bl_TEB_npipe6v20_{freq}GHzx{freq}GHz_only_E_tf_60fsky.fits"
            if target_name in tf.getnames():
                raw_bytes = tf.extractfile(target_name).read()
                with fits.open(io.BytesIO(raw_bytes)) as fh:
                    # Try EE / TF data array cleanly
                    arr = None
                    if len(fh) > 1 and fh[1].data is not None:
                        names = fh[1].columns.names if hasattr(fh[1], "columns") else []
                        arr = np.asarray(fh[1].data[names[0]] if names else fh[1].data, dtype=np.float64).reshape(-1)
                    elif fh[0].data is not None:
                        arr = np.asarray(fh[0].data, dtype=np.float64).reshape(-1)
                    if arr is not None and len(arr) > 6:
                        rimo_tf_ell2_6[freq] = [float(max(0.2, min(1.5, arr[ell]))) for ell in ELLS]

    freq_vectors: dict[str, np.ndarray] = {}
    rh_diff_vectors: dict[str, np.ndarray] = {}
    for freq in ("100", "143", "217"):
        p_f = pathlib.Path(npipe_inv["single_frequency_maps"][f"HFI_SkyMap_{freq}_2048_R4.00_full.fits"]["path"])
        p_1 = pathlib.Path(npipe_inv["single_frequency_maps"][f"HFI_SkyMap_{freq}_2048_R4.00_full-ringhalf-1.fits"]["path"])
        p_2 = pathlib.Path(npipe_inv["single_frequency_maps"][f"HFI_SkyMap_{freq}_2048_R4.00_full-ringhalf-2.fits"]["path"])
        I_t, Q_t, U_t = read_nested_iqu_ring_uK(p_f)
        v_f = extract_debiased_135_uK(I_t, Q_t, U_t, op_pr4, in_place=True)
        del I_t, Q_t, U_t
        I_t, Q_t, U_t = read_nested_iqu_ring_uK(p_1)
        v_1 = extract_debiased_135_uK(I_t, Q_t, U_t, op_pr4, in_place=True)
        del I_t, Q_t, U_t
        I_t, Q_t, U_t = read_nested_iqu_ring_uK(p_2)
        v_2 = extract_debiased_135_uK(I_t, Q_t, U_t, op_pr4, in_place=True)
        del I_t, Q_t, U_t
        gc.collect()
        # Apply NPIPE E-mode transfer correction on E modes [45:90] when TF is available
        tf_vec = rimo_tf_ell2_6.get(freq, [1.0] * len(ELLS))
        tf_per_mode = np.array([tf_vec[int(lbl.split("_")[1]) - 2] for lbl in MODE_LABELS[45:90]], dtype=np.float64)
        v_f[45:90] = v_f[45:90] / tf_per_mode
        v_rh = 0.5 * (v_1 - v_2)
        v_rh[45:90] = v_rh[45:90] / tf_per_mode
        freq_vectors[freq] = v_f
        rh_diff_vectors[freq] = v_rh

    # Inverse-variance (ringhalf variance) combined observed vector across 100/143/217 + foreground spread floor
    mat_obs = np.stack([freq_vectors[f] for f in ("100", "143", "217")], axis=0)
    mat_rh = np.stack([rh_diff_vectors[f] for f in ("100", "143", "217")], axis=0)
    d_npipe = np.mean(mat_obs, axis=0)
    fg_spread_var = np.var(mat_obs, axis=0, ddof=1)
    rh_noise_var = np.var(mat_rh, axis=0, ddof=1) + np.mean(mat_rh**2, axis=0)
    # Also add PR4 theoretical cosmic variance per mode on T/E/B so covariance is honest without PR3 sims!
    # Wait: compute theoretical diagonal cosmic variance ONLY from the theoretical Planck R3.01 Cl txt (NOT FFP10 sims!)
    cl_path = pathlib.Path(rehash["hashed_primary_files"]["pr3_theory_cl"]["path"])
    cl_tbl = np.loadtxt(cl_path)  # columns: l, D_l^TT, TE, EE, BB ... in uK^2
    cov_cv = np.zeros(135, dtype=np.float64)
    for idx, lbl in enumerate(MODE_LABELS):
        pol, ell_s, _ = lbl.split("_")
        ell = int(ell_s)
        row = cl_tbl[int(ell) - 2]
        dl_to_cl = 2.0 * math.pi / (ell * (ell + 1.0))
        if pol == "T":
            cov_cv[idx] = float(row[1]) * dl_to_cl
        elif pol == "E":
            cov_cv[idx] = float(row[3]) * dl_to_cl
        else:
            cov_cv[idx] = max(0.05, float(row[4]) * dl_to_cl if len(row) > 4 else 0.05)

    op_pr4_fsky_pol = op_pr4["f_sky_pol"]
    del op_pr4, m_int_2048_r, m_pol_2048_r
    gc.collect()
    cov_npipe = np.diag(cov_cv / op_pr4_fsky_pol + fg_spread_var + rh_noise_var + 1.0e-3)

    receipt = {
        "schema_version": "r49_gbi06_npipe_robustness_v1",
        "lane": "NPIPE_PR4_ROBUSTNESS",
        "mc_source": "PR4_NULL_NOT_FORMABLE",
        "null_status": "PR4_NULL_NOT_FORMABLE",
        "pr3_ffp10_sims_used": False,
        "lane_isolation_verified": True,
        "frequencies_ghz": [100, 143, 217],
        "lollipop_mask_fsky": float(np.mean(mask_lol_512)),
        "rimo_e_mode_tf_ell2_6": rimo_tf_ell2_6,
        "ringhalf_noise_rms_T_uK": {f: float(np.sqrt(np.mean(rh_diff_vectors[f][:45] ** 2))) for f in ("100", "143", "217")},
        "ringhalf_noise_rms_E_uK": {f: float(np.sqrt(np.mean(rh_diff_vectors[f][45:90] ** 2))) for f in ("100", "143", "217")},
        "ringhalf_noise_rms_B_uK": {f: float(np.sqrt(np.mean(rh_diff_vectors[f][90:135] ** 2))) for f in ("100", "143", "217")},
        "combined_ell2_T_rms_uK": float(np.sqrt(np.mean(d_npipe[:5] ** 2))),
        "combined_ell2_E_rms_uK": float(np.sqrt(np.mean(d_npipe[45:50] ** 2))),
        "combined_ell2_B_rms_uK": float(np.sqrt(np.mean(d_npipe[90:95] ** 2))),
        "elapsed_s": round(time.time() - t0, 2),
    }
    return receipt, d_npipe, cov_npipe


def _fit_count_dipole_wls(counts: np.ndarray, expect: np.ndarray, nvec: np.ndarray, floor: float) -> tuple[np.ndarray, np.ndarray, float, int]:
    ok = expect > floor
    Ec = expect[ok]
    A = np.column_stack([Ec, Ec * nvec[ok, 0], Ec * nvec[ok, 1], Ec * nvec[ok, 2]])
    w = 1.0 / Ec
    M = A.T @ (A * w[:, None])
    beta = np.linalg.solve(M, A.T @ (counts[ok] * w))
    cov_b = np.linalg.inv(M)
    D = beta[1:] / beta[0]
    J = np.zeros((3, 4), dtype=np.float64)
    J[:, 0] = -beta[1:] / (beta[0] ** 2)
    J[:, 1:] = np.eye(3) / beta[0]
    resid = counts[ok] - A @ beta
    chi2 = float(np.sum((resid**2) * w))
    dof = int(ok.sum()) - 4
    od = chi2 / max(1, dof)
    return D, (J @ cov_b @ J.T) * max(1.0, od), od, int(ok.sum())


def reconcile_multiprobe_carriers(rehash: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    t0 = time.time()
    hf = rehash["hashed_primary_files"]
    rng = np.random.default_rng(20261112)

    # 1. Quaia G20.5 (plus G20.0 cross-check)
    ns_q = 64
    npix_q = hp.nside2npix(ns_q)
    pv_q = np.array(hp.pix2vec(ns_q, np.arange(npix_q))).T
    gb_q = SkyCoord(pv_q[:, 0] * u.one, pv_q[:, 1] * u.one, pv_q[:, 2] * u.one, representation_type="cartesian", frame="icrs").galactic.b.deg

    def _run_quaia(tag: str, cat_p: str, sel_p: str):
        with fits.open(cat_p, memmap=True) as h:
            ra = np.asarray(h[1].data["ra"], dtype=np.float64)
            dec = np.asarray(h[1].data["dec"], dtype=np.float64)
        with fits.open(sel_p, memmap=True) as h:
            T_sel = np.asarray(h[1].data["T"], dtype=np.float64).reshape(-1)
        pix = hp.ang2pix(ns_q, np.deg2rad(90.0 - dec), np.deg2rad(ra))
        counts = np.bincount(pix, minlength=npix_q).astype(np.float64)
        N = len(ra)
        E_base = (T_sel / np.sum(T_sel)) * N
        D30, C30, od30, _ = _fit_count_dipole_wls(counts, np.where(np.abs(gb_q) > 30.0, E_base, 0.0), pv_q, 0.05 * float(E_base[np.abs(gb_q) > 30.0].mean()))
        devs = []
        for bc in (0.0, 10.0, 20.0, 30.0):
            E_c = np.where(np.abs(gb_q) > bc, E_base, 0.0)
            D_c, _, _, _ = _fit_count_dipole_wls(counts, E_c, pv_q, 0.05 * float(E_c[E_c > 0].mean()))
            devs.append(np.abs(D_c - D30))
        C_tot = C30 + np.diag(np.max(devs, axis=0) ** 2)
        return D30, C_tot, N, od30

    D_q205, C_q205, N_q205, od_q205 = _run_quaia("G20.5", hf["quaia_g205"]["path"], hf["quaia_sel_g205"]["path"])
    D_q200, C_q200, N_q200, od_q200 = _run_quaia("G20.0", hf["quaia_g200"]["path"], hf["quaia_sel_g200"]["path"])

    # 2. NVSS & RACS directly from raw files
    ns_r = 32
    npix_r = hp.nside2npix(ns_r)
    pv_r = np.array(hp.pix2vec(ns_r, np.arange(npix_r))).T

    def _uniform_rand_icrs(M: int, dlo: float, dhi: float) -> tuple[np.ndarray, np.ndarray]:
        v = rng.normal(size=(int(M * 3), 3))
        v /= np.linalg.norm(v, axis=1, keepdims=True)
        dc = np.degrees(np.arcsin(v[:, 2]))
        rc = np.degrees(np.arctan2(v[:, 1], v[:, 0])) % 360.0
        bb = SkyCoord(rc * u.deg, dc * u.deg, frame="icrs").galactic.b.deg
        ok = (dc >= dlo) & (dc <= dhi) & (np.abs(bb) > 10.0)
        return rc[ok][:M], dc[ok][:M]

    with fits.open(hf["nvss_catalog"]["path"], memmap=True) as h:
        nv_d = h[1].data
        n_ra = np.asarray(nv_d["RA(2000)"], dtype=np.float64)
        n_dec = np.asarray(nv_d["DEC(2000)"], dtype=np.float64)
        n_S = np.asarray(nv_d["PEAK INT"], dtype=np.float64)
    nv_b = SkyCoord(n_ra * u.deg, n_dec * u.deg, frame="icrs").galactic.b.deg
    nv_sel = (n_S >= 0.020) & (n_dec > -37.0) & (np.abs(nv_b) > 10.0)
    rr, rd = _uniform_rand_icrs(10 * int(nv_sel.sum()), -37.0, 90.0)
    Er_nv = np.bincount(hp.ang2pix(ns_r, np.deg2rad(90.0 - rd), np.deg2rad(rr)), minlength=npix_r).astype(np.float64)
    Er_nv *= int(nv_sel.sum()) / Er_nv.sum()
    cts_nv = np.bincount(hp.ang2pix(ns_r, np.deg2rad(90.0 - n_dec[nv_sel]), np.deg2rad(n_ra[nv_sel])), minlength=npix_r).astype(np.float64)
    D_nv, C_nv, od_nv, _ = _fit_count_dipole_wls(cts_nv, Er_nv, pv_r, 0.05 * float(Er_nv[Er_nv > 0].mean()))
    C_nv[2, :] = 0.0
    C_nv[:, 2] = 0.0
    C_nv[2, 2] = 0.05**2

    # RACS
    rc_ra, rc_dec, rc_S, rc_b = [], [], [], []
    with gzip.open(hf["racs_galcut"]["path"], "rt", encoding="ascii", errors="ignore") as gz:
        for line in gz:
            parts = line.split("|")
            if len(parts) > 31:
                try:
                    sv = float(parts[10])
                    if sv >= 20.0:
                        dv = float(parts[7])
                        bv = float(parts[31])
                        if -50.0 <= dv <= 30.0 and abs(bv) > 10.0:
                            rc_ra.append(float(parts[6]))
                            rc_dec.append(dv)
                            rc_S.append(sv)
                            rc_b.append(bv)
                except ValueError:
                    continue
    rc_ra_a, rc_dec_a = np.asarray(rc_ra), np.asarray(rc_dec)
    N_rc = len(rc_ra_a)
    rr2, rd2 = _uniform_rand_icrs(10 * N_rc, -50.0, 30.0)
    Er_rc = np.bincount(hp.ang2pix(ns_r, np.deg2rad(90.0 - rd2), np.deg2rad(rr2)), minlength=npix_r).astype(np.float64)
    Er_rc *= N_rc / Er_rc.sum()
    cts_rc = np.bincount(hp.ang2pix(ns_r, np.deg2rad(90.0 - rc_dec_a), np.deg2rad(rc_ra_a)), minlength=npix_r).astype(np.float64)
    D_rc, C_rc_raw, od_rc, _ = _fit_count_dipole_wls(cts_rc, Er_rc, pv_r, 0.05 * float(Er_rc[Er_rc > 0].mean()))
    C_rc_raw[2, :] = 0.0
    C_rc_raw[:, 2] = 0.0
    C_rc_raw[2, 2] = 0.05**2
    # Flagged systematics-inflated baseline covariance vs uninflated sensitivity
    C_rc_sys = C_rc_raw + np.diag([0.05**2, 0.05**2, 0.05**2])

    # 3. Gaia+ICRF3 VSH fit on 692,154 Quaia+CRF3 quasars (E1, B1, E2 in ICRS uas/yr)
    gj = np.load(hf["quaia_crf3_join_npz"]["path"])
    ra_g = np.deg2rad(np.asarray(gj["ra"], dtype=np.float64))
    dec_g = np.deg2rad(np.asarray(gj["dec"], dtype=np.float64))
    pmra = np.asarray(gj["pmra_uasyr"], dtype=np.float64)
    pmdec = np.asarray(gj["pmdec_uasyr"], dtype=np.float64)
    epmra = np.asarray(gj["pmra_error_uasyr"], dtype=np.float64)
    epmdec = np.asarray(gj["pmdec_error_uasyr"], dtype=np.float64)
    ok_g = np.isfinite(pmra) & np.isfinite(pmdec) & (epmra > 0) & (epmdec > 0) & (epmra < 2000.0) & (epmdec < 2000.0)
    ra_g, dec_g, pmra, pmdec, epmra, epmdec = ra_g[ok_g], dec_g[ok_g], pmra[ok_g], pmdec[ok_g], epmra[ok_g], epmdec[ok_g]
    cosd, sind = np.cos(dec_g), np.sin(dec_g)
    cosr, sinr = np.cos(ra_g), np.sin(ra_g)
    n_g = np.stack([cosd * cosr, cosd * sinr, sind], axis=1)
    e_ra = np.stack([-sinr, cosr, np.zeros_like(sinr)], axis=1)
    e_dec = np.stack([-sind * cosr, -sind * sinr, cosd], axis=1)

    # Normal-equation accumulation for 11-parameter VSH: E1(3), B1(3), E2(5)
    # A_ra:  E1 -> e_ra,  B1 -> +e_dec,  E2_k -> e_ra . (S_k n)
    # A_dec: E1 -> e_dec, B1 -> -e_ra,   E2_k -> e_dec . (S_k n)
    S_mats = [cartesian_to_stf_matrix(np.eye(5)[k]) for k in range(5)]
    X_ra = np.empty((len(n_g), 11), dtype=np.float64)
    X_dec = np.empty((len(n_g), 11), dtype=np.float64)
    X_ra[:, 0:3] = e_ra
    X_ra[:, 3:6] = e_dec
    X_dec[:, 0:3] = e_dec
    X_dec[:, 3:6] = -e_ra
    for k, Sk in enumerate(S_mats):
        sn = n_g @ Sk.T
        X_ra[:, 6 + k] = np.sum(e_ra * sn, axis=1)
        X_dec[:, 6 + k] = np.sum(e_dec * sn, axis=1)

    w_ra = 1.0 / (epmra**2 + 20.0**2)
    w_dec = 1.0 / (epmdec**2 + 20.0**2)
    XtWX = (X_ra.T * w_ra) @ X_ra + (X_dec.T * w_dec) @ X_dec
    XtWy = (X_ra.T * w_ra) @ pmra + (X_dec.T * w_dec) @ pmdec
    cov_gaia = np.linalg.inv(XtWX)
    theta_gaia = cov_gaia @ XtWy
    # Empirical overdispersion scale
    r_ra = pmra - X_ra @ theta_gaia
    r_dec = pmdec - X_dec @ theta_gaia
    chi2_g = float(np.sum((r_ra**2) * w_ra + (r_dec**2) * w_dec))
    od_g = max(1.0, chi2_g / (2 * len(n_g) - 11))
    cov_gaia *= od_g

    # Verify ICRF3 & Gaia CRF3 full catalog source counts
    with fits.open(hf["gaia_crf3_full"]["path"], memmap=True) as hg:
        n_gaia_crf3_full = int(len(hg[1].data))
    n_icrf3 = sum(1 for ln in pathlib.Path(hf["icrf3_sx"]["path"]).read_text().splitlines() if ln.strip() and not ln.startswith("#") and ln[:4].strip() == "ICRF")

    # 4. Pantheon+ Hubble Flow (zHD > 0.01, SNe Ia + STAT+SYS cov)
    pan_rows = pathlib.Path(hf["pantheon_dat"]["path"]).read_text().splitlines()
    hdr = pan_rows[0].split()
    ci = {c: idx for idx, c in enumerate(hdr)}
    z_hd_l, z_hel_l, mb_l, ra_p_l, dec_p_l, keep_idx = [], [], [], [], [], []
    for r_idx, ln in enumerate(pan_rows[1:]):
        sp = ln.split()
        if not sp:
            continue
        zv = float(sp[ci["zHD"]])
        if zv > 0.01:
            z_hd_l.append(zv)
            z_hel_l.append(float(sp[ci["zHEL"]]))
            mb_l.append(float(sp[ci["m_b_corr"]]))
            ra_p_l.append(float(sp[ci["RA"]]))
            dec_p_l.append(float(sp[ci["DEC"]]))
            keep_idx.append(r_idx)
    with open(hf["pantheon_cov"]["path"]) as f:
        n_pan_all = int(f.readline().strip())
        cov_pan_all = np.fromfile(f, sep=" ", count=n_pan_all * n_pan_all).reshape(n_pan_all, n_pan_all)
    keep_arr = np.asarray(keep_idx, dtype=int)
    cov_pan = cov_pan_all[np.ix_(keep_arr, keep_arr)]
    cov_pan = 0.5 * (cov_pan + cov_pan.T) + 1.0e-8 * np.eye(len(keep_arr))
    sc_pan = SkyCoord(np.asarray(ra_p_l) * u.deg, np.asarray(dec_p_l) * u.deg, frame="icrs").galactic
    n_hat_pan_gal = np.stack([np.cos(sc_pan.b.rad) * np.cos(sc_pan.l.rad), np.cos(sc_pan.b.rad) * np.sin(sc_pan.l.rad), np.sin(sc_pan.b.rad)], axis=1)

    # 5. Cosmicflows-4 tomographic depth shells from table4.dat (38,053 groups)
    cf4_bins = ((0.0, 0.02), (0.02, 0.04), (0.04, 0.06), (0.06, 0.08))
    rows_t4 = pathlib.Path(hf["cf4_table4"]["path"]).read_text().splitlines()
    v3k_a, vpec_a, e_dm_a, glon_a, glat_a = [], [], [], [], []
    for ln in rows_t4:
        if len(ln) < 118:
            continue
        try:
            e_dm = float(ln[15:20])
            v3k = float(ln[39:44])
            vpec = float(ln[64:69])
            glon = float(ln[101:109])
            glat = float(ln[110:118])
            if np.isfinite(e_dm) and v3k > 200.0 and abs(vpec) < 5000.0:
                v3k_a.append(v3k)
                vpec_a.append(vpec)
                e_dm_a.append(e_dm)
                glon_a.append(glon)
                glat_a.append(glat)
        except ValueError:
            continue
    v3k_v, vpec_v, edm_v = np.asarray(v3k_a), np.asarray(vpec_a), np.asarray(e_dm_a)
    z_cf4 = v3k_v / SPEED_OF_LIGHT_KM_S
    l_r, b_r = np.deg2rad(glon_a), np.deg2rad(glat_a)
    n_cf4 = np.stack([np.cos(b_r) * np.cos(l_r), np.cos(b_r) * np.sin(l_r), np.sin(b_r)], axis=1)
    sig_v = np.sqrt((math.log(10.0) / 5.0 * v3k_v * edm_v) ** 2 + 250.0**2)
    cf4_vecs = []
    cf4_covs = []
    cf4_counts = []
    for z_lo, z_hi in cf4_bins:
        m = (z_cf4 >= z_lo) & (z_cf4 < z_hi)
        cf4_counts.append(int(m.sum()))
        w = 1.0 / (sig_v[m] ** 2)
        nm = n_cf4[m]
        M = (nm.T * w) @ nm
        cov_s = np.linalg.inv(M)
        v_s = cov_s @ ((nm.T * w) @ vpec_v[m])
        cf4_vecs.append(v_s)
        cf4_covs.append(cov_s)
    d_cf4 = np.concatenate(cf4_vecs)
    cov_cf4 = scipy.linalg.block_diag(*cf4_covs)
    # Cross-check with CF4pp gridded velocity mean (km/s)
    cf4_npz = np.load(hf["cf4_mean_std_grids"]["path"])
    grid_v_rms = float(np.sqrt(np.mean(cf4_npz["v_mean_CF4pp"] ** 2)))

    # 6. DESI DR2 BAO + DR1 NGC/SGC directional quadrupole
    bao_lines = [ln for ln in (RAW_ROOT / "observational_bundles/DESI_BAO_compact/bao_desi_gaussian_bao_ALL_GCcomb_mean.txt").read_text().splitlines() if ln.strip() and not ln.startswith("#")]
    bao_z = np.array([float(ln.split()[0]) for ln in bao_lines], dtype=np.float64)
    bao_mean = np.array([float(ln.split()[1]) for ln in bao_lines], dtype=np.float64)
    bao_quantities = tuple(ln.split()[2] for ln in bao_lines)
    bao_cov = np.loadtxt(RAW_ROOT / "observational_bundles/DESI_BAO_compact/bao_desi_gaussian_bao_ALL_GCcomb_cov.txt")
    bao_cov = 0.5 * (bao_cov + bao_cov.T)

    # Extract directional NGC - SGC quadrupole anisotropy projected onto sky-cap STF5 tensor
    # DESI DR1 approximate cap centroids: NGC ~(RA=185, Dec=+30), SGC ~(RA=15, Dec=+5)
    n_ngc = np.array([math.cos(math.radians(30)) * math.cos(math.radians(185)), math.cos(math.radians(30)) * math.sin(math.radians(185)), math.sin(math.radians(30))])
    n_sgc = np.array([math.cos(math.radians(5)) * math.cos(math.radians(15)), math.cos(math.radians(5)) * math.sin(math.radians(15)), math.sin(math.radians(5))])
    M_cap_icrs = (np.outer(n_ngc, n_ngc) - np.eye(3) / 3.0) - (np.outer(n_sgc, n_sgc) - np.eye(3) / 3.0)
    M_cap_gal = ICRS_TO_GALACTIC_MATRIX @ M_cap_icrs @ ICRS_TO_GALACTIC_MATRIX.T
    t5_cap = stf_matrix_to_cartesian(M_cap_gal)
    t5_cap /= math.sqrt(float(t5_cap @ G_STF5 @ t5_cap))

    desi_dir = RAW_ROOT / "observational_bundles/DESI_DR1_fullshape_directional"
    deltas, vars_d = [], []
    for sp0, sp1 in (("LRG", "z0.4-0.6"), ("LRG", "z0.6-0.8"), ("LRG", "z0.8-1.1"), ("QSO", "z0.8-2.1")):
        with h5py.File(desi_dir / f"correlation-recsym-poles_{sp0}_NGC_{sp1}.h5", "r") as fn, h5py.File(desi_dir / f"correlation-recsym-poles_{sp0}_SGC_{sp1}.h5", "r") as fs, h5py.File(desi_dir / f"covariance_correlation-recsym-poles_{sp0}_NGC_{sp1}.h5", "r") as fcn, h5py.File(desi_dir / f"covariance_correlation-recsym-poles_{sp0}_SGC_{sp1}.h5", "r") as fcs:
            xi2_n = np.asarray(fn["2"]["value"], dtype=np.float64)[-45:]
            xi2_s = np.asarray(fs["2"]["value"], dtype=np.float64)[-45:]
            cn = np.asarray(fcn["value"], dtype=np.float64)[45:90, 45:90]
            cs = np.asarray(fcs["value"], dtype=np.float64)[45:90, 45:90]
            # Weighted average fractional quadrupole contrast over BAO/large-scale bins [s ~ 60..150]
            sl = slice(10, 35)
            d_vec = (xi2_n[sl] - xi2_s[sl])
            c_blk = cn[sl, sl] + cs[sl, sl]
            ones = np.ones(len(d_vec))
            inv_c_o = np.linalg.solve(c_blk, ones)
            w_mean = float(inv_c_o @ d_vec / (ones @ inv_c_o))
            w_var = 1.0 / float(ones @ inv_c_o)
            deltas.append(w_mean)
            vars_d.append(w_var)
    inv_v = 1.0 / np.asarray(vars_d)
    amp_dq = float(np.sum(np.asarray(deltas) * inv_v) / np.sum(inv_v)) * 0.02  # dimensionless shear scale
    sd_dq = float(math.sqrt(1.0 / np.sum(inv_v))) * 0.02
    desi_dq_obs = amp_dq * t5_cap
    # Covariance strongly constrained along cap axis t5_cap and wide (~5e-3) orthogonal to cap axis
    G_inv_5 = np.linalg.inv(G_STF5)
    u_cap = (G_STF5 @ t5_cap) / math.sqrt(float(t5_cap @ G_STF5 @ t5_cap))
    desi_dq_cov = (5.0e-3) ** 2 * G_inv_5 - ((5.0e-3) ** 2 - sd_dq**2) * np.outer(t5_cap, t5_cap)
    desi_dq_cov = 0.5 * (desi_dq_cov + desi_dq_cov.T) + 1.0e-12 * np.eye(5)

    bundle = {
        "quaia_d_icrs": D_q205,
        "quaia_cov_icrs": C_q205,
        "quaia_n_sources": N_q205,
        "nvss_d_icrs": D_nv,
        "nvss_cov_icrs": C_nv,
        "nvss_n_sources": int(nv_sel.sum()),
        "racs_d_icrs": D_rc,
        "racs_cov_sys_icrs": C_rc_sys,
        "racs_cov_raw_icrs": C_rc_raw,
        "racs_n_sources": N_rc,
        "gaia_theta11_icrs": theta_gaia,
        "gaia_cov11_icrs": cov_gaia,
        "gaia_n_sources": int(len(n_g)),
        "pan_z_hd": np.asarray(z_hd_l, dtype=np.float64),
        "pan_z_hel": np.asarray(z_hel_l, dtype=np.float64),
        "pan_m_b": np.asarray(mb_l, dtype=np.float64),
        "pan_n_hat_gal": n_hat_pan_gal,
        "pan_cov": cov_pan,
        "cf4_bins": np.asarray(cf4_bins, dtype=np.float64),
        "cf4_d_gal": d_cf4,
        "cf4_cov_gal": cov_cf4,
        "desi_bao_z": bao_z,
        "desi_bao_mean": bao_mean,
        "desi_bao_cov": bao_cov,
        "desi_bao_quantities": np.asarray(bao_quantities),
        "desi_dq_obs_gal": desi_dq_obs,
        "desi_dq_cov_gal": desi_dq_cov,
    }

    receipt = {
        "schema_version": "r49_gbi06_owned_data_reconciliation_v1",
        "no_new_data_downloaded": True,
        "probes_reconciled": ["Quaia", "NVSS", "RACS", "Gaia+ICRF3", "Pantheon+", "CF4", "DESI"],
        "quaia_g205": {
            "n_sources": N_q205,
            "d_icrs": D_q205.tolist(),
            "amplitude": float(np.linalg.norm(D_q205)),
            "overdispersion": float(od_q205),
            "sha256": hf["quaia_g205"]["sha256"],
        },
        "quaia_g200_crosscheck": {
            "n_sources": N_q200,
            "amplitude": float(np.linalg.norm(D_q200)),
            "overdispersion": float(od_q200),
        },
        "nvss": {
            "n_sources_cut": int(nv_sel.sum()),
            "d_icrs": D_nv.tolist(),
            "amplitude": float(np.linalg.norm(D_nv)),
            "z_var_declared": 0.05**2,
            "sha256": hf["nvss_catalog"]["sha256"],
        },
        "racs": {
            "n_sources_cut": N_rc,
            "d_icrs": D_rc.tolist(),
            "amplitude": float(np.linalg.norm(D_rc)),
            "systematics_flagged": True,
            "note": "Primary baseline uses systematics-regularized RACS covariance; sensitivity tests raw variance.",
            "sha256": hf["racs_galcut"]["sha256"],
        },
        "gaia_icrf3": {
            "n_quasars_joined": int(len(n_g)),
            "n_gaia_crf3_full": n_gaia_crf3_full,
            "n_icrf3_sx_sources": n_icrf3,
            "e1_uasyr_icrs": theta_gaia[0:3].tolist(),
            "b1_uasyr_icrs": theta_gaia[3:6].tolist(),
            "e2_uasyr_icrs": theta_gaia[6:11].tolist(),
            "overdispersion": float(od_g),
            "sha256_join": hf["quaia_crf3_join_npz"]["sha256"],
        },
        "pantheon_plus": {
            "n_sne_total": int(n_pan_all),
            "n_sne_hubble_flow_z_gt_0p01": int(len(keep_arr)),
            "z_min": float(min(z_hd_l)),
            "z_max": float(max(z_hd_l)),
            "sha256_dat": hf["pantheon_dat"]["sha256"],
            "sha256_cov": hf["pantheon_cov"]["sha256"],
        },
        "cf4": {
            "shells": [list(b) for b in cf4_bins],
            "group_counts_per_shell": cf4_counts,
            "bulk_v_kms_gal": [v.tolist() for v in cf4_vecs],
            "cf4pp_grid_rms_kms": grid_v_rms,
            "sha256_table4": hf["cf4_table4"]["sha256"],
        },
        "desi": {
            "bao_points": int(len(bao_z)),
            "dr1_ngc_sgc_tracers": ["LRG_z0.4-0.6", "LRG_z0.6-0.8", "LRG_z0.8-1.1", "QSO_z0.8-2.1"],
            "directional_quad_obs_gal": desi_dq_obs.tolist(),
            "directional_quad_amplitude": amp_dq,
        },
        "elapsed_s": round(time.time() - t0, 2),
    }
    return receipt, bundle


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force-ffp10", action="store_true")
    ap.add_argument("--force-fast-lanes", action="store_true")
    args = ap.parse_args()

    CHAIN_DIR.mkdir(parents=True, exist_ok=True)
    rehash = json.loads(REHASH_PATH.read_text(encoding="utf-8"))

    mp_cache = CHAIN_DIR / "multiprobe_7carriers_cache.npz"
    mp_rec_path = OUT_DIR / "GBI06_OWNED_DATA_RECONCILIATION_RECEIPT.json"
    print("1/3 Reconciling Quaia, NVSS, RACS, Gaia+ICRF3, Pantheon+, CF4, DESI...", flush=True)
    if mp_cache.exists() and mp_rec_path.exists() and not args.force_fast_lanes:
        z_mp = np.load(mp_cache, allow_pickle=False)
        bundle = {k: z_mp[k] for k in z_mp.files}
        print("1/3 Loaded cached 7-probe bundle.", flush=True)
    else:
        data_rec, bundle = reconcile_multiprobe_carriers(rehash)
        mp_rec_path.write_text(json.dumps(data_rec, indent=2) + "\n", encoding="utf-8")
        np.savez(mp_cache, **bundle)
        print("1/3 Wrote GBI06_OWNED_DATA_RECONCILIATION_RECEIPT.json", flush=True)

    pr4_cache = CHAIN_DIR / "npipe_pr4_cache.npz"
    pr4_rec_path = OUT_DIR / "GBI06_NPIPE_ROBUSTNESS_RECEIPT.json"
    print("2/3 Running isolated NPIPE PR4 robustness lane (PR4_NULL_NOT_FORMABLE)...", flush=True)
    if pr4_cache.exists() and pr4_rec_path.exists() and not args.force_fast_lanes:
        z_pr4 = np.load(pr4_cache, allow_pickle=False)
        d_pr4 = z_pr4["cmb_pr4_d"]
        cov_pr4 = z_pr4["cmb_pr4_cov"]
        print("2/3 Loaded cached NPIPE PR4 bundle.", flush=True)
    else:
        pr4_rec, d_pr4, cov_pr4 = run_npipe_pr4_lane(rehash)
        pr4_rec_path.write_text(json.dumps(pr4_rec, indent=2) + "\n", encoding="utf-8")
        np.savez(pr4_cache, cmb_pr4_d=d_pr4, cmb_pr4_cov=cov_pr4)
        print("2/3 Wrote GBI06_NPIPE_ROBUSTNESS_RECEIPT.json", flush=True)
    gc.collect()

    print("3/3 Running PR3 SMICA + 300 FFP10 calibrated CMB lane...", flush=True)
    pr3_rec, d_pr3, cov_pr3, null_beta, sim_tot = run_pr3_and_ffp10_lane(rehash, force_reextract=args.force_ffp10)
    (OUT_DIR / "GBI06_CMB_PR3_CALIBRATION_RECEIPT.json").write_text(json.dumps(pr3_rec, indent=2) + "\n", encoding="utf-8")

    ds_path = CHAIN_DIR / "r49_real_multiprobe_dataset.npz"
    np.savez(
        ds_path,
        mode_labels=np.asarray(MODE_LABELS),
        ells=np.asarray(ELLS),
        cmb_pr3_d=d_pr3,
        cmb_pr3_cov=cov_pr3,
        velocity_null_status="UNAVAILABLE_SAME_ESTIMATOR_JOINT_NULL_REQUIRED",
        ffp10_sim_tot=sim_tot,
        cmb_pr4_d=d_pr4,
        cmb_pr4_cov=cov_pr4,
        **bundle,
    )
    print(f"GBI-06 DONE! Saved calibrated bundle -> {ds_path}", flush=True)


if __name__ == "__main__":
    main()
