"""R95 Step 3D (G05_PLANCK / P2): Full-resolution (NSIDE=2048, lmax=48) FFP10 SMICA T/E/B & PR3 SMICA vs Commander analysis.

Reuses:
  - /home/cosmosapjw/Downloads/htt_r94_fullres_stream/{full_stream_manifest_r95.json,
    noise_300_TEB_alm.npz, observed_smica_commander_TEB_alm.npz, full_TEB_*.npz}
  - /home/cosmosapjw/Downloads/htt_r93_ffp999_alm_biposh/SMICA_999_NSIDE64_MASKED_ALM_L48.npz
  - scripts/r94/gaunt_fast.py (C++17/OpenMP Gaunt L=2 projector + exact O(N d) LOO)
  - scripts/r93/smica_ffp999_biposh.py (iso_theory_cl)
  - /mnt/extdrive/workdir/raw/planck_data/COM_Mask_CMB-common-Mask-{Int,Pol}_2048_R3.00.fits

Strict scientific separation:
  - Primary MC null = 300 unique-noise realizations (cmb_ids < 300); 999 recycled-noise reported separately.
  - Observed PR3 SMICA vs PR3 Commander strictly separated; commander_null_qualified = False.
  - Conditional T/E/B template checks do NOT promote SQ-NATIVE or B02-B05 publication acceptance.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import time
from pathlib import Path

import healpy as hp
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
STREAM_DIR = Path.home() / "Downloads/htt_r94_fullres_stream"
R93_NPZ = Path.home() / "Downloads/htt_r93_ffp999_alm_biposh/SMICA_999_NSIDE64_MASKED_ALM_L48.npz"
MASK_I_FITS = Path("/mnt/extdrive/workdir/raw/planck_data/COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits")
MASK_P_FITS = Path("/mnt/extdrive/workdir/raw/planck_data/COM_Mask_CMB-common-Mask-Pol_2048_R3.00.fits")
R95_DIR = ROOT / "docs/research_program/observational_publication_20261015/R95_LOCAL_EXECUTION_20261122"
OUT_JSON = R95_DIR / "G05_PLANCK_FULLRES_TEB_RESULT.json"
LMAX = 48


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def _load_mod(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _vectorized_alm2cl_batch(a: np.ndarray, b: np.ndarray, lmax: int = LMAX) -> np.ndarray:
    """Exact HEALPix pseudo-C_ell(l=0..lmax) for 2D arrays a, b shape (N, nalm)."""
    N = a.shape[0]
    ell_vals = np.arange(lmax + 1)
    cl = np.zeros((N, lmax + 1), dtype=np.float64)
    # Accumulate m=0 (weight 1) and m>0 (weight 2 Re[a conj(b)])
    for m in range(0, lmax + 1):
        ls = np.arange(m, lmax + 1)
        idx = hp.Alm.getidx(lmax, ls, m)
        prod = np.real(a[:, idx] * np.conj(b[:, idx]))
        w = 1.0 if m == 0 else 2.0
        cl[:, ls] += w * prod
    cl /= (2 * ell_vals + 1)[None, :]
    return cl


def _all_six_spectra(teb: np.ndarray, lmax: int = LMAX) -> dict[str, np.ndarray]:
    """Compute TT, EE, BB, TE, TB, EB for batch teb of shape (N, 3, nalm)."""
    aT, aE, aB = teb[:, 0, :], teb[:, 1, :], teb[:, 2, :]
    return {
        "TT": _vectorized_alm2cl_batch(aT, aT, lmax),
        "EE": _vectorized_alm2cl_batch(aE, aE, lmax),
        "BB": _vectorized_alm2cl_batch(aB, aB, lmax),
        "TE": _vectorized_alm2cl_batch(aT, aE, lmax),
        "TB": _vectorized_alm2cl_batch(aT, aB, lmax),
        "EB": _vectorized_alm2cl_batch(aE, aB, lmax),
    }


def _rank_summary(mc_vals: np.ndarray, obs_val: np.ndarray) -> dict:
    """Vectorized standardized chi2 distance on diagonal covariance across LOO isn't overfit."""
    # Exact rank-p using gaunt_fast.loo_diagonal_fast
    mu = mc_vals.mean(axis=0)
    sd = mc_vals.std(axis=0, ddof=1)
    z_obs = (obs_val - mu) / np.maximum(sd, 1e-30)
    return {
        "mc_n": int(mc_vals.shape[0]),
        "mean": mu.tolist(),
        "std": sd.tolist(),
        "obs": obs_val.tolist(),
        "z_scores": z_obs.tolist(),
        "max_abs_z": float(np.max(np.abs(z_obs))),
    }


def _pack_loo(gaunt, x_mc: np.ndarray, obs: np.ndarray) -> dict:
    r = gaunt.loo_diagonal_fast(x_mc, obs)
    return {
        "observed_score": float(r["observed_score"]),
        "MC_N": int(r["MC_N"]),
        "null_tail_count": int(r["null_tail_count"]),
        "rank_p": float(r["rank_p"]),
        "MC_median_score": float(r["MC_median_score"]),
        "MC_p95_score": float(r["MC_p95_score"]),
    }


def run_planck_fullres_analysis() -> dict:
    t0 = time.perf_counter()
    manifest_path = STREAM_DIR / "full_stream_manifest_r95.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Stream manifest missing: {manifest_path}")
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("cmb_count") != 999 or manifest.get("noise_count") != 300:
        raise RuntimeError(f"Incomplete fullres stream manifest: {manifest.get('cmb_count')}/999")

    # 1. Load all 40 sorted full_TEB chunks -> 999 paired + 999 cmb_only
    chunk_files = sorted(STREAM_DIR.glob("full_TEB_*.npz"))
    ids_list, paired_list, cmb_only_list = [], [], []
    for cf in chunk_files:
        with np.load(cf, allow_pickle=False) as d:
            ids_list.append(np.asarray(d["cmb_ids"], dtype=np.int32))
            paired_list.append(np.asarray(d["TEB_alm"], dtype=np.complex128))
            cmb_only_list.append(np.asarray(d["cmb_only_TEB_alm"], dtype=np.complex128))
    cmb_ids = np.concatenate(ids_list)
    paired_teb = np.concatenate(paired_list, axis=0)
    cmb_only_teb = np.concatenate(cmb_only_list, axis=0)
    if len(cmb_ids) != 999 or set(cmb_ids.tolist()) != (set(range(1000)) - {970}):
        raise RuntimeError(f"Expected 999 CMB realizations excluding 970, got len={len(cmb_ids)}")

    # Sort monotonically by cmb_id to align 1:1 with R93 NPZ
    order = np.argsort(cmb_ids)
    cmb_ids = cmb_ids[order]
    paired_teb = paired_teb[order]
    cmb_only_teb = cmb_only_teb[order]

    with np.load(STREAM_DIR / "noise_300_TEB_alm.npz", allow_pickle=False) as d:
        noise_ids = np.asarray(d["noise_ids"], dtype=np.int32)
        noise_teb = np.asarray(d["TEB_alm"], dtype=np.complex128)
        if len(noise_ids) != 300:
            raise RuntimeError("Expected 300 noise realizations")

    with np.load(STREAM_DIR / "observed_smica_commander_TEB_alm.npz", allow_pickle=False) as d:
        obs_smica_n64 = np.asarray(d["smica_TEB_n64sub"], dtype=np.complex128)
        obs_smica_n2048 = np.asarray(d["smica_TEB_n2048sub"], dtype=np.complex128)
        obs_cmd_n2048 = np.asarray(d["commander_TEB_n2048sub"], dtype=np.complex128)
        obs_meta = {
            "smica_sha256": str(d["smica_sha256"]),
            "commander_sha256": str(d["commander_sha256"]),
            "smica_beta_n64_uK": d["smica_beta_n64_uK"].tolist(),
            "smica_beta_n2048_uK": d["smica_beta_n2048_uK"].tolist(),
            "commander_beta_n2048_uK": d["commander_beta_n2048_uK"].tolist(),
        }

    # 2. Parity check against R93 NSIDE64 T-alm across ALL 999 pairs + observed SMICA
    with np.load(R93_NPZ, allow_pickle=False) as d64:
        ids64 = np.asarray(d64["cmb_ids"], dtype=np.int32)
        if not np.array_equal(ids64, cmb_ids):
            raise RuntimeError("CMB ID order mismatch between fullres stream and R93 NSIDE64 NPZ")
        alm64_paired_T = np.asarray(d64["paired_masked_alm_lmax48"], dtype=np.complex128)
        alm64_obs_T = np.asarray(d64["observed_masked_alm_lmax48"], dtype=np.complex128)

    idx_l2_start = 2  # l >= 2 coefficients (m=0 starts at l=0,1,2...; mask/dip subtraction uses l>=2)
    cl_t_2048 = _vectorized_alm2cl_batch(paired_teb[:, 0, :], paired_teb[:, 0, :], LMAX)
    cl_t_64 = _vectorized_alm2cl_batch(alm64_paired_T, alm64_paired_T, LMAX)
    # Verify vectorized_alm2cl against healpy.alm2cl on sample 0
    cl0_hp = hp.alm2cl(paired_teb[0, 0, :])
    cl0_vec_err = float(np.max(np.abs(cl_t_2048[0] - cl0_hp)))
    if cl0_vec_err > 1e-10:
        raise RuntimeError(f"alm2cl vectorization parity failed: err={cl0_vec_err}")

    ratio_2048_over_64_mean = (cl_t_2048[:, 2:].mean(axis=0) / cl_t_64[:, 2:].mean(axis=0))
    l2_rel_999 = np.linalg.norm(paired_teb[:, 0, :] - alm64_paired_T, axis=1) / np.linalg.norm(alm64_paired_T, axis=1)
    obs_T_rel_diff = float(np.linalg.norm(obs_smica_n64[0] - alm64_obs_T) / np.linalg.norm(alm64_obs_T))

    # 3. Compute all 6 pseudo-C_ell spectra cleanly separated by ensemble
    distinct300 = cmb_ids < 300
    spec_paired = _all_six_spectra(paired_teb, LMAX)
    spec_cmb_only = _all_six_spectra(cmb_only_teb, LMAX)
    spec_noise_only = _all_six_spectra(noise_teb, LMAX)
    spec_obs_smica = _all_six_spectra(obs_smica_n2048[None, :, :], LMAX)
    spec_obs_cmd = _all_six_spectra(obs_cmd_n2048[None, :, :], LMAX)

    spectra_summary = {}
    for ch in ("TT", "EE", "BB", "TE", "TB", "EB"):
        arr300 = spec_paired[ch][distinct300, 2:]
        arr999 = spec_paired[ch][:, 2:]
        arr_sig = spec_cmb_only[ch][:, 2:]
        arr_noi = spec_noise_only[ch][:, 2:]
        obs_s = spec_obs_smica[ch][0, 2:]
        obs_c = spec_obs_cmd[ch][0, 2:]
        mu300 = arr300.mean(axis=0)
        sd300 = arr300.std(axis=0, ddof=1)
        z300_s = (obs_s - mu300) / np.maximum(sd300, 1e-30)
        # Inspect low-ell quadrupole (ell=2 -> idx 0), ell=10 (idx 8), ell=30 (idx 28), ell=48 (idx 46)
        spectra_summary[ch] = {
            "ell_2_obs_smica": float(obs_s[0]),
            "ell_2_obs_commander_exploratory": float(obs_c[0]),
            "ell_2_mc300_mean": float(mu300[0]),
            "ell_2_mc300_sd": float(sd300[0]),
            "ell_2_noise300_mean": float(arr_noi[:, 0].mean()),
            "ell_2_signal999_mean": float(arr_sig[:, 0].mean()),
            "ell_2_smica_z300": float(z300_s[0]),
            "ell_2_to_48_max_abs_z_smica_vs_300": float(np.max(np.abs(z300_s))),
            "ell_2_to_48_mc300_mean": mu300.tolist(),
            "ell_2_to_48_mc300_sd": sd300.tolist(),
            "ell_2_to_48_mc999_recycled_mean": arr999.mean(axis=0).tolist(),
            "ell_2_to_48_smica_obs": obs_s.tolist(),
            "ell_2_to_48_commander_obs_unqualified": obs_c.tolist(),
        }

    # 4. Signed L=2 BiPoSH on T, E, B via C++17 Gaunt kernel + exact C++/NumPy parity check
    gaunt = _load_mod("r95_gaunt_fast", ROOT / "scripts/r94/gaunt_fast.py")
    r93 = _load_mod("r95_r93_biposh", ROOT / "scripts/r93/smica_ffp999_biposh.py")

    cl_T_weight = r93.iso_theory_cl()
    cl_E_weight = np.zeros(LMAX + 1, dtype=np.float64)
    cl_B_weight = np.zeros(LMAX + 1, dtype=np.float64)
    cl_E_weight[2:] = np.maximum(spec_paired["EE"][distinct300, 2:].mean(axis=0), 1e-12)
    cl_B_weight[2:] = np.maximum(spec_paired["BB"][distinct300, 2:].mean(axis=0), 1e-12)

    terms = {
        "T": gaunt.build_terms(cl_T_weight, LMAX),
        "E": gaunt.build_terms(cl_E_weight, LMAX),
        "B": gaunt.build_terms(cl_B_weight, LMAX),
    }

    # Verify C++ native vs NumPy reference on first 25 paired T/E/B maps
    gaunt_parity = {}
    biposh_mc999 = {}
    biposh_sig999 = {}
    biposh_noi300 = {}
    biposh_obs_smica2048 = {}
    biposh_obs_smica64 = {}
    biposh_obs_cmd2048 = {}
    for ch_idx, ch in enumerate(("T", "E", "B")):
        t_ch = terms[ch]
        ref25 = gaunt.project(paired_teb[:25, ch_idx, :], t_ch, backend="numpy")
        nat25 = gaunt.project(paired_teb[:25, ch_idx, :], t_ch, backend="native")
        par_err = float(np.max(np.abs(nat25 - ref25)))
        if par_err > 1e-11 * max(1.0, float(np.max(np.abs(ref25)))):
            raise RuntimeError(f"Gaunt C++/NumPy parity failed on {ch}: {par_err}")
        gaunt_parity[ch] = par_err

        biposh_mc999[ch] = gaunt.project(paired_teb[:, ch_idx, :], t_ch, backend="native").reshape(999, 20)
        biposh_sig999[ch] = gaunt.project(cmb_only_teb[:, ch_idx, :], t_ch, backend="native").reshape(999, 20)
        biposh_noi300[ch] = gaunt.project(noise_teb[:, ch_idx, :], t_ch, backend="native").reshape(300, 20)
        biposh_obs_smica2048[ch] = gaunt.project(obs_smica_n2048[None, ch_idx, :], t_ch, backend="native")[0].reshape(20)
        biposh_obs_smica64[ch] = gaunt.project(obs_smica_n64[None, ch_idx, :], t_ch, backend="native")[0].reshape(20)
        biposh_obs_cmd2048[ch] = gaunt.project(obs_cmd_n2048[None, ch_idx, :], t_ch, backend="native")[0].reshape(20)

    biposh_summary = {}
    for ch in ("T", "E", "B"):
        x_mc = biposh_mc999[ch]
        x300 = x_mc[distinct300]
        obs_s = biposh_obs_smica2048[ch]
        obs_c = biposh_obs_cmd2048[ch]
        band_out = {}
        for bi, (l_lo, l_hi) in enumerate(gaunt.L2_BANDS):
            sl = slice(bi * 5, (bi + 1) * 5)
            band_out[f"{l_lo}-{l_hi}"] = {
                "smica_n2048_signed5": obs_s[sl].tolist(),
                "commander_n2048_signed5_unqualified": obs_c[sl].tolist(),
                "unique_noise_300": _pack_loo(gaunt, x300[:, sl], obs_s[sl]),
                "recycled_noise_999": _pack_loo(gaunt, x_mc[:, sl], obs_s[sl]),
            }
        biposh_summary[ch] = {
            "global_20D_smica_n2048_unique_noise_300": _pack_loo(gaunt, x300, obs_s),
            "global_20D_smica_n2048_recycled_noise_999": _pack_loo(gaunt, x_mc, obs_s),
            "global_20D_smica_n64sub_unique_noise_300": _pack_loo(gaunt, x300, biposh_obs_smica64[ch]),
            "global_20D_commander_exploratory_against_smica_300_NOT_NULL_QUALIFIED": _pack_loo(gaunt, x300, obs_c),
            "bands": band_out,
        }

    # Joint 60D (T+E+B) score across unique 300 noise primary vs 999 recycled
    x300_60 = np.column_stack([biposh_mc999[c][distinct300] for c in ("T", "E", "B")])
    x999_60 = np.column_stack([biposh_mc999[c] for c in ("T", "E", "B")])
    obs_s60 = np.concatenate([biposh_obs_smica2048[c] for c in ("T", "E", "B")])
    obs_c60 = np.concatenate([biposh_obs_cmd2048[c] for c in ("T", "E", "B")])
    joint_teb_60d = {
        "smica_n2048_unique_noise_300": _pack_loo(gaunt, x300_60, obs_s60),
        "smica_n2048_recycled_noise_999": _pack_loo(gaunt, x999_60, obs_s60),
        "commander_exploratory_vs_smica300_NOT_NULL_QUALIFIED": _pack_loo(gaunt, x300_60, obs_c60),
    }

    # 5. Beam smoothing (SMICA 5 arcmin FWHM) + Mask f_sky + 10-realization pure-E -> B mask leakage check
    fwhm_rad = math.radians(5.0 / 60.0)
    sigma_b = fwhm_rad / math.sqrt(8.0 * math.log(2.0))
    beam_sq = {str(ell): math.exp(-ell * (ell + 1) * sigma_b * sigma_b) for ell in (2, 16, 32, 48)}
    maskI = hp.read_map(str(MASK_I_FITS), dtype=np.float64)
    maskP = hp.read_map(str(MASK_P_FITS), dtype=np.float64)
    fsky_I = float(np.mean(maskI))
    fsky_P = float(np.mean(maskP))
    # Pure-E synthetic mock skies masked with exact PR3 Mask-Pol (zero input T, zero input B, 10 draws)
    rng = np.random.default_rng(9505)
    nalm = hp.Alm.getsize(LMAX)
    leak_ell2_list, leak_mean_list = [], []
    for _ in range(10):
        alm_E_pure = np.zeros(nalm, dtype=np.complex128)
        for ell in range(2, LMAX + 1):
            sig = math.sqrt(float(cl_E_weight[ell]))
            idx0 = hp.Alm.getidx(LMAX, ell, 0)
            alm_E_pure[idx0] = rng.normal(scale=sig)
            for m in range(1, ell + 1):
                idxm = hp.Alm.getidx(LMAX, ell, m)
                alm_E_pure[idxm] = (rng.normal(scale=sig) + 1j * rng.normal(scale=sig)) / math.sqrt(2.0)
        alm_zero = np.zeros_like(alm_E_pure)
        _, q_pure, u_pure = hp.alm2map([alm_zero, alm_E_pure, alm_zero], nside=2048, lmax=LMAX, pol=True)
        aE_leak, aB_leak = hp.map2alm_spin([q_pure * maskP, u_pure * maskP], spin=2, lmax=LMAX)
        cl_E_leak = hp.alm2cl(aE_leak)[2:]
        cl_B_leak = hp.alm2cl(aB_leak)[2:]
        leak_ell2_list.append(float(cl_B_leak[0] / max(cl_E_leak[0], 1e-30)))
        leak_mean_list.append(float(np.mean(cl_B_leak) / np.mean(cl_E_leak)))
    del maskI, maskP, q_pure, u_pure

    # 6. Conditional Bianchi L=2 quadrupole comparison (observed SMICA/Commander vs MC & R95 Step 3C)
    # Extract L=2 (m=0,1,2) quadrupole total power C_2^{TT,EE,BB} and check against Step 3C prototype
    hier_path = R95_DIR / "G07_BIANCHI_POLARIZED_HIERARCHY.json"
    bianchi_overlap_note = None
    if hier_path.is_file():
        hd = json.loads(hier_path.read_text())
        ang = hd.get("angular_grid_models", {})
        bianchi_overlap_note = {
            fname: {
                "cl_TT_l2": float(rec["cl_TT"][2]),
                "cl_EE_l2": float(rec["cl_EE"][2]),
                "cl_BB_l2": float(rec["cl_BB"][2]),
            }
            for fname, rec in ang.items() if fname != "FLRW"
        }

    out = {
        "schema": "htt.r95.planck_fullres_teb_999_analysis/1",
        "elapsed_seconds": time.perf_counter() - t0,
        "stream_manifest_sha256": _sha(manifest_path),
        "r93_nside64_npz_sha256": _sha(R93_NPZ),
        "observed_meta": obs_meta,
        "sample_counts": {
            "cmb_ids": int(len(cmb_ids)),
            "missing_cmb_id": 970,
            "unique_noise_primary_N": int(np.sum(distinct300)),
            "recycled_noise_secondary_N": 999,
            "cmb_00818_warning_preserved": manifest.get("warnings_log", {}).get("818", []),
        },
        "nside2048_vs_nside64_T_parity": {
            "alm2cl_vectorized_max_abs_err": cl0_vec_err,
            "observed_smica_n64sub_T_rel_l2_diff": obs_T_rel_diff,
            "mc999_T_rel_l2_diff_min_median_max": [
                float(np.min(l2_rel_999)),
                float(np.median(l2_rel_999)),
                float(np.max(l2_rel_999)),
            ],
            "mean_cl_ratio_2048_over_64_at_ell_2_10_20_30_48": {
                "2": float(ratio_2048_over_64_mean[0]),
                "10": float(ratio_2048_over_64_mean[8]),
                "20": float(ratio_2048_over_64_mean[18]),
                "30": float(ratio_2048_over_64_mean[28]),
                "48": float(ratio_2048_over_64_mean[46]),
            },
        },
        "mask_and_beam_checks": {
            "f_sky_I": fsky_I,
            "f_sky_P": fsky_P,
            "smica_5arcmin_beam_sq_b_ell2": beam_sq,
            "pure_E_synthetic_n_draws": 10,
            "pure_E_synthetic_mask_leakage_clBB_over_clEE_ell2": float(np.mean(leak_ell2_list)),
            "pure_E_synthetic_mask_leakage_clBB_over_clEE_mean_2_48": float(np.mean(leak_mean_list)),
            "pure_E_synthetic_mask_leakage_clBB_over_clEE_std_2_48": float(np.std(leak_mean_list, ddof=1)),
            "eb_weight_source_note": "TT BiPoSH uses external Planck theory Cl; EE/BB Gaunt weights use distinct300 paired pseudo-Cl mean (noise+signal).",
        },
        "pseudo_cl_spectra_ell2_to_48": spectra_summary,
        "gaunt_cpp_vs_numpy_parity_max_abs": gaunt_parity,
        "biposh_L2_summary": biposh_summary,
        "biposh_joint_60D_TEB": joint_teb_60d,
        "bianchi_step3c_quadrupole_reference": bianchi_overlap_note,
        "physics_gates": {
            "smica_unique_noise_primary_N": 300,
            "commander_null_qualified": False,
            "bianchi_family_identified": False,
            "native_boltzmann_likelihood_completed": False,
            "physical_Pi": None,
            "physical_GF": None,
            "scope_note": "Full-resolution NSIDE=2048 masked T/E/B pseudo-Cl & L=2 signed BiPoSH across all 999 FFP10 SMICA signal + 300 unique noise realizations; SMICA vs Commander separated; NOT a release-matched Commander MC null or inhomogeneous Bianchi all-m likelihood.",
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2) + "\n")
    return out


if __name__ == "__main__":
    res = run_planck_fullres_analysis()
    print(json.dumps({
        "cmb_ids": res["sample_counts"]["cmb_ids"],
        "unique_noise": res["sample_counts"]["unique_noise_primary_N"],
        "obs_T_diff_n64_n2048": res["nside2048_vs_nside64_T_parity"]["observed_smica_n64sub_T_rel_l2_diff"],
        "T_biposh_p300": res["biposh_L2_summary"]["T"]["global_20D_smica_n2048_unique_noise_300"]["rank_p"],
        "E_biposh_p300": res["biposh_L2_summary"]["E"]["global_20D_smica_n2048_unique_noise_300"]["rank_p"],
        "B_biposh_p300": res["biposh_L2_summary"]["B"]["global_20D_smica_n2048_unique_noise_300"]["rank_p"],
        "TEB_60D_p300": res["biposh_joint_60D_TEB"]["smica_n2048_unique_noise_300"]["rank_p"],
        "eb_leak_mean": res["mask_and_beam_checks"]["pure_E_synthetic_mask_leakage_clBB_over_clEE_mean_2_48"],
        "elapsed_s": res["elapsed_seconds"],
    }))
