#!/usr/bin/env python3
"""R54-L02: PR4 bypass. Covariance triangulation without NPIPE simulations.

Steps follow LOCAL_AGENT_CONTRACT.json:nodes[R54-L02]; deviations are in DEVIATIONS.json (DV-L02-*):
 1. analytic T covariance C_th = R diag(C_ell b^2 p^2) R^T + FFP10 noise, R = response of the R51 masked T estimator
 2. LRT of C_th against the FFP10 sample covariance S_T45 and the diagonal ratios
 3. adopt C_th for the T lane only if p >= 0.01 and every diagonal ratio is within 0.25 of 1
 4. cross-experiment T (WMAP9 ILC, Cosmoglobe DR1, BeyondPlanck v2; union mask): Sigma_T shifts from SMICA in T sd
 5. E lane: Cosmoglobe/BeyondPlanck with their uncertainty products, WMAP9 V band with its noise matrix, PR4 split difference
 6. adopted E covariance floor
 7. B ell=2 null with the adopted covariance per pipeline / experiment and the E-lane status
No PR4 simulation is used. Claim tier C0.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import platform
import sys
import tarfile
import tempfile
import time
from pathlib import Path

import healpy as hp
import numpy as np
import scipy
from astropy.io import fits
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT / "htt", ROOT / "htt/src", ROOT):
    sys.path.insert(0, str(_p))

from htt.htt.infer import r54_calibration as cal  # noqa: E402
from htt.htt.infer import r54_pr4_bypass as pb  # noqa: E402
from htt.htt.infer import r54_tensor_five_view as fv  # noqa: E402

PUB = ROOT / "docs/research_program/observational_publication_20261015"
R54 = PUB / "R54_TENSOR_FRAME_TOMOGRAPHY_20261116"
NPZ = PUB / "R50_OBSERVED_CONVERGENCE_20261115/R51/observed_carrier.npz"
OUT = R54 / "RESULTS/R54_L02_RESULT.json"
CAMB = ROOT / "data/camb_ref_planck2018.npz"
SIMS = Path("/mnt/extdrive/workdir/r49_chains/ffp10_300_debiased_135.npz")
PR4_CACHE = Path("/mnt/extdrive/workdir/r49_chains/npipe_pr4_cache.npz")
RAW = Path("/mnt/extdrive/workdir/raw")
WMAP_ILC = RAW / "wmap_9yr/core/wmap_ilc_9yr_v5.fits"
WMAP_MASKS = RAW / "wmap_9yr/core/wmap_analysis_masks_9yr_v5.tar.gz"
WMAP_BANDS = RAW / "wmap_9yr/core/wmap_band_forered_iqumap_r9_nineyear_v5.tar.gz"
WMAP_NINV = RAW / "wmap_9yr/morphology_subset/wmap_band_forered_quninv_r4_nineyear_v5.tar.gz"
CG_CMB = RAW / "cosmoglobe_dr1/CG_cmb_IQU_n1024_v1.fits"
BP_CMB = RAW / "beyondplanck_v2/BP_cmb_IQU_n1024_v2.fits"
BP_MASK_I = RAW / "beyondplanck_v2/BP_CMB_I_analysis_mask_n1024_v2.fits"
BP_MASK_P = RAW / "beyondplanck_v2/BP_CMB_IQU_analysis_mask_n8_v2.fits"
BP_CHAINS = [RAW / f"beyondplanck_v2/BP_c000{i}_Presamp_v2.h5" for i in (1, 2, 3, 4)]
ELL_CUT, ELL_CHECK, NSIDE_K = 30, 20, 128
SEED = 20261116
N_CG_MC, N_WMAP_MC, BP_THIN = 100, 500, 100
ALPHA = 0.01


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def load_script(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def gauss_beam(fwhm_arcmin: float, lmax: int) -> np.ndarray:
    return hp.gauss_beam(math.radians(fwhm_arcmin / 60.0), lmax=lmax)


def ring_map(path: Path, col: str, nside_out: int | None = None, scale: float = 1.0) -> np.ndarray:
    with fits.open(path, memmap=True) as h:
        hd = h[1].header
        m = np.asarray(h[1].data[col], np.float64).reshape(-1)
        if str(hd.get("ORDERING", "RING")).upper().startswith("NEST"):
            m = hp.reorder(m, n2r=True)
    m = m * scale
    return m if nside_out is None or hp.npix2nside(m.size) == nside_out else hp.ud_grade(m, nside_out, order_in="RING", order_out="RING")


def ell_rows(labels: list[str], field: str) -> dict[int, list[int]]:
    out: dict[int, list[int]] = {}
    for i, s in enumerate(labels):
        f, ell = s.split("_")[0], int(s.split("_")[1])
        if f == field:
            out.setdefault(ell, []).append(i)
    return out


def gls(d: np.ndarray, cov: np.ndarray, j: np.ndarray) -> dict:
    ci = np.linalg.inv(cov)
    f = j.T @ ci @ j
    c = np.linalg.inv(f)
    est = c @ j.T @ ci @ d
    return {"est": est, "cov": c, "sd": np.sqrt(np.diag(c)), "wald": float(est @ f @ est)}


def floor_null(vec_obs: np.ndarray, null_vecs: np.ndarray, cov: np.ndarray, floor: float, rng: np.random.Generator, law: str) -> dict:
    """Upper tail of q = b^T (C + f I)^-1 b with null realisations b_i + sqrt(f) z_i (adopted covariance)."""
    c = cov + floor * np.eye(cov.shape[0])
    q_obs = pb.quadratic_form(vec_obs, c)
    draws = null_vecs + math.sqrt(floor) * rng.standard_normal(null_vecs.shape)
    q = np.array([pb.quadratic_form(x, c) for x in draws])
    out = cal.EmpiricalNull(q, law).upper_tail(q_obs)
    out["pass"] = bool(out["p_value"] >= ALPHA)
    return out


def compute() -> dict:
    t0 = time.monotonic()
    missing = [str(p) for p in (SIMS, CAMB, WMAP_ILC, WMAP_MASKS, WMAP_BANDS, WMAP_NINV, CG_CMB, BP_CMB, BP_MASK_I, BP_MASK_P, PR4_CACHE, *BP_CHAINS)
               if not p.is_file()]
    if missing:
        return {"status": "BLOCKED_MISSING_INPUT", "reason": "missing: " + ", ".join(missing)}
    r51 = load_script("r51_lowell", "scripts/r51/run_r51_pr3_lowell.py")
    lanes = r51.lane_module()
    cmb = load_script("r54_cmb", "scripts/r54/run_r54_cmb_type1.py")
    l01 = json.loads((R54 / "RESULTS/R54_L01_RESULT.json").read_text())
    l1 = json.loads((R54 / "RESULTS/R54_L1_TYPE1_TE.json").read_text())
    with np.load(NPZ, allow_pickle=False) as z:
        labels = [str(x) for x in z["mode_labels"]]
        s_ref, j_t, j_ideal = z["S_ffp10_300_135x135_uK2"], z["response_J_135x5_uK"], z["response_J_ideal_135x5_uK"]
        d_s, d_c = z["d_smica_135_uK"], z["d_commander_135_uK"]
    with np.load(SIMS, allow_pickle=False) as z:
        sims, sims_noise = z["sim_tot"].copy(), z["sim_noise"].copy()
    t45 = cmb.rows(labels, "T", (2, 3, 4, 5, 6))
    t2, e2, b2 = cmb.rows(labels, "T", (2,)), cmb.rows(labels, "E", (2,)), cmb.rows(labels, "B", (2,))
    tl = ell_rows(labels, "T")
    with fits.open(r51.SMICA, memmap=True) as h:
        int_beam = np.asarray(h[2].data["INT_BEAM"], float).reshape(-1)[:ELL_CUT + 1]
    bl_smica = int_beam * hp.pixwin(2048)[:ELL_CUT + 1]
    mask_i, mask_p = r51.read_mask(r51.MASK_I, "TMASK"), r51.read_mask(r51.MASK_P, "PMASK")
    op = lanes.build_lowell_mask_operators(mask_i, mask_p)

    # ---- steps 1-3: analytic T covariance
    m128 = hp.ud_grade(mask_i.astype(float), NSIDE_K, order_in="RING", order_out="RING")
    r_mat, ells = pb.t_response_matrix(m128, NSIDE_K, ELL_CUT, op["K49_inv_45"], pb.mode_tuples(6, 0))
    with np.load(CAMB, allow_pickle=False) as z:
        cl_tab = dict(zip(z["ell"].astype(int).tolist(), z["C_TT"].tolist()))
    if any(ell not in cl_tab for ell in range(2, ELL_CUT + 1)):
        raise SystemExit("camb_ref_planck2018.npz does not cover 2 <= ell <= ELL_CUT")

    def power(e: np.ndarray) -> np.ndarray:
        return np.array([cl_tab[int(x)] * bl_smica[int(x)] ** 2 for x in e])

    noise_t = np.cov(sims_noise[:, t45].T, ddof=1)
    c_th = pb.analytic_covariance(r_mat, ells, power, noise_t)
    keep = ells <= ELL_CHECK
    c_check = pb.analytic_covariance(r_mat[:, keep], ells[keep], power, noise_t)
    s_t = s_ref[np.ix_(t45, t45)]
    lrt = pb.wishart_lrt(c_th, s_t, 299)
    adopt = bool(lrt["p_value"] >= ALPHA and lrt["max_abs_diag_ratio_minus_1"] <= 0.25)
    jt = j_t[t45]
    fit_th, fit_mc = gls(d_s[t45], c_th, jt), gls(d_s[t45], s_t, jt)
    infl = fv.finite_mc_sd_inflation(300, 45, 5)
    t_cov_adopted = c_th if adopt else s_t
    t_sd_factor = 1.0 if adopt else infl
    t_test = {"ell_cut": ELL_CUT, "nside_coupling": NSIDE_K, "n_modes": int(r_mat.shape[1]), "lrt": lrt,
              "truncation_check_ell_le_20_max_rel_diff": float(np.max(np.abs(c_check - c_th)) / np.max(np.abs(c_th))),
              "noise": "FFP10 noise-only sample covariance (sim_noise, 300)", "beam": "SMICA INT_BEAM x pixwin(2048)",
              "adopt_rule": "p >= 0.01 and max |diag(S)/diag(C_th) - 1| <= 0.25", "adopted": adopt,
              "reason": "C_th adopted (no finite-MC inflation)" if adopt else "FFP10 kept with the calibrated inflation: the analytic covariance fails the rule",
              "Sigma_T_with_C_th": {"est": fit_th["est"], "sd": fit_th["sd"], "wald": fit_th["wald"],
                                    "wald_tail": fv.chi2_null_tail(fit_th["wald"], 5, "gaussian with the analytic covariance")},
              "Sigma_T_with_FFP10": {"est": fit_mc["est"], "sd_inflated": fit_mc["sd"] * infl, "inflation": infl}}
    print(f"[L02] T covariance done {time.monotonic() - t0:.0f}s adopt={adopt}", flush=True)

    # ---- step 4: cross-experiment T on the union mask
    tmpdir = Path(tempfile.mkdtemp(prefix="r54_l02_", dir="/tmp"))
    with tarfile.open(WMAP_MASKS) as tf:
        tf.extract("wmap_temperature_kq85_analysis_mask_r9_9yr_v5.fits", tmpdir)
        tf.extract("wmap_polarization_analysis_mask_r4_9yr_v5.fits", tmpdir)
    kq85 = ring_map(tmpdir / "wmap_temperature_kq85_analysis_mask_r9_9yr_v5.fits", "TEMPERATURE", 2048) > 0.5
    with fits.open(BP_MASK_I, memmap=True) as h:
        col_i = h[1].columns.names[0]
    bp_i = ring_map(BP_MASK_I, col_i, 2048) > 0.5
    with fits.open(BP_MASK_P, memmap=True) as h:
        cols_p = h[1].columns.names
    bp_p = ring_map(BP_MASK_P, cols_p[1] if len(cols_p) > 1 else cols_p[0], 2048) > 0.5
    union_i, union_p = mask_i & kq85 & bp_i, mask_p & bp_p
    op_u = lanes.build_lowell_mask_operators(union_i, union_p)
    f_sky = {"union_T": float(union_i.mean()), "union_P": float(union_p.mean()), "R51_T": float(mask_i.mean()), "R51_P": float(mask_p.mean()),
             "bp_pol_mask_column": cols_p[1] if len(cols_p) > 1 else cols_p[0]}

    def t_vector(i_map: np.ndarray, beam_ratio: np.ndarray) -> np.ndarray:
        v = lanes.extract_debiased_135_uK(i_map, np.zeros_like(i_map), np.zeros_like(i_map), op_u, in_place=True)[t45]
        for ell, rows in tl.items():
            v[[t45.index(r) for r in rows]] *= beam_ratio[ell]
        return v

    vec_t = {"SMICA": t_vector(lanes.read_nested_iqu_ring_uK(r51.SMICA)[0], np.ones(ELL_CUT + 1))}
    vec_t["WMAP9_ILC"] = t_vector(ring_map(WMAP_ILC, "TEMPERATURE", 2048, 1.0e3), bl_smica / (gauss_beam(60.0, ELL_CUT) * hp.pixwin(512)[:ELL_CUT + 1]))
    fwhm = {}
    for name, path in (("Cosmoglobe_DR1", CG_CMB), ("BeyondPlanck_v2", BP_CMB)):
        with fits.open(path, memmap=True) as h:
            fwhm[name] = float(h[1].header["FWHM"])
        vec_t[name] = t_vector(ring_map(path, "I_MEAN", 2048), bl_smica / (gauss_beam(fwhm[name], ELL_CUT) * hp.pixwin(1024)[:ELL_CUT + 1]))
    ref = gls(vec_t["SMICA"], t_cov_adopted, jt)
    sd_t, base = ref["sd"] * t_sd_factor, ref["est"]
    cross = {}
    for name, v in vec_t.items():
        est = gls(v, t_cov_adopted, jt)["est"]
        cross[name] = {"Sigma_T": est, "shift_from_SMICA_in_sd": (est - base) / sd_t, "max_abs_shift_sd": float(np.max(np.abs((est - base) / sd_t)))}
    env = max(v["max_abs_shift_sd"] for k, v in cross.items() if k != "SMICA")
    stack = np.array([v["Sigma_T"] for v in cross.values()])
    cross_t = {"mask": "R51 TMASK x WMAP9 KQ85 x BeyondPlanck intensity analysis mask", "f_sky": f_sky, "beam_fwhm_arcmin": {"WMAP9_ILC": 60.0, **fwhm},
               "experiments": cross, "sd_used": sd_t, "max_abs_shift_sd": env, "rule": "max |shift| <= 0.5 sd",
               "status": "PIPELINE_STABLE" if env <= 0.5 else "PIPELINE_DEPENDENT",
               "envelope_Sigma_T": {"min": stack.min(axis=0), "max": stack.max(axis=0)}}
    print(f"[L02] cross-experiment T done {time.monotonic() - t0:.0f}s", flush=True)

    # ---- step 5: E-lane alternatives
    e_table = {}
    norm_col = float(np.linalg.norm(j_ideal[t2, 0]))                 # norm of one STF5 column of the ideal ell = 2 response
    mask_p_1024 = (hp.ud_grade(union_p.astype(float), 1024, order_in="RING", order_out="RING") > 0.5).astype(float)
    k_1024 = pb.eb_operator(mask_p_1024, 1024)
    rng_cg = np.random.default_rng([SEED, 22])
    null_store = {}
    for name, path in (("Cosmoglobe_DR1", CG_CMB), ("BeyondPlanck_v2_mean", BP_CMB)):
        q, u = ring_map(path, "Q_MEAN"), ring_map(path, "U_MEAN")
        sq, su = ring_map(path, "Q_STDDEV"), ring_map(path, "U_STDDEV")
        obs = pb.extract_eb(q, u, mask_p_1024, k_1024)
        null = np.array([pb.extract_eb(sq * rng_cg.standard_normal(sq.size), su * rng_cg.standard_normal(su.size), mask_p_1024, k_1024)
                         for _ in range(N_CG_MC)])
        null_store[name] = null
        e_table[name] = {"vector_E2": obs[0:5], "vector_B2": obs[45:50],
                         "law": f"white-noise Monte Carlo from the Q/U STDDEV maps (N={N_CG_MC}; pixel correlations not modelled)",
                         "E2_rms_uK": float(np.sqrt(np.mean(obs[0:5] ** 2))), "B2_rms_uK": float(np.sqrt(np.mean(obs[45:50] ** 2))),
                         "noise_B2_rms_uK": float(np.sqrt(np.mean(null[:, 45:50] ** 2))),
                         "Sigma_E_frobenius": float(np.linalg.norm(obs[0:5]) / norm_col)}
        print(f"[L02] {name} done {time.monotonic() - t0:.0f}s", flush=True)
    import h5py
    samples_e, samples_b = [], []
    for path in BP_CHAINS:
        with h5py.File(path, "r") as f:
            keys = sorted(k for k in f.keys() if k.isdigit())
            for k in keys[::BP_THIN]:
                a = f[k]["cmb_lowl"]["amp_alm"][()]
                samples_e.append(a[1, 4:9])
                samples_b.append(a[2, 4:9])
    samples_e, samples_b = np.array(samples_e, float), np.array(samples_b, float)
    e_table["BeyondPlanck_v2_posterior"] = {"n_samples": int(samples_b.shape[0]), "thin": BP_THIN, "B2_zero_tail": pb.posterior_zero_tail(samples_b),
                                            "E2_zero_tail": pb.posterior_zero_tail(samples_e),
                                            "E2_rms_uK_posterior_mean": float(np.sqrt(np.mean(samples_e.mean(axis=0) ** 2))),
                                            "B2_rms_uK_posterior_mean": float(np.sqrt(np.mean(samples_b.mean(axis=0) ** 2))),
                                            "Sigma_E_frobenius_posterior_mean": float(np.linalg.norm(samples_e.mean(axis=0)) / norm_col),
                                            "Sigma_E_frobenius_posterior_16_84": np.quantile(np.linalg.norm(samples_e, axis=1) / norm_col, [0.16, 0.84]),
                                            "index_convention": "l^2 + l + m (Commander real a_lm); the B null statistic is invariant to the real basis"}
    print(f"[L02] BeyondPlanck posterior done {time.monotonic() - t0:.0f}s", flush=True)
    with tarfile.open(WMAP_BANDS) as tf:
        tf.extract("wmap_band_forered_iqumap_r9_9yr_V_v5.fits", tmpdir)
    with tarfile.open(WMAP_NINV) as tf:
        tf.extract("wmap_band_forered_quninv_r4_9yr_V_v5.fits", tmpdir)
    with fits.open(tmpdir / "wmap_band_forered_iqumap_r9_9yr_V_v5.fits", memmap=True) as h:
        qn, un, nobs = (np.asarray(h[1].data[c], float).reshape(-1) for c in ("Q_POLARISATION", "U_POLARISATION", "N_OBS"))
    fac = (512 // 16) ** 2
    w = nobs.reshape(-1, fac)
    q16 = (qn.reshape(-1, fac) * w).sum(axis=1) / w.sum(axis=1) * 1.0e3            # NESTED degrade, mK -> uK
    u16 = (un.reshape(-1, fac) * w).sum(axis=1) / w.sum(axis=1) * 1.0e3
    with fits.open(tmpdir / "wmap_band_forered_quninv_r4_9yr_V_v5.fits", memmap=True) as h:
        ninv = np.asarray(h[0].data, float) * 1.0e-6                                   # mK^-2 -> uK^-2
    with fits.open(tmpdir / "wmap_polarization_analysis_mask_r4_9yr_v5.fits", memmap=True) as h:
        p06_nest = np.asarray(h[1].data["TEMPERATURE"], float).reshape(-1) > 0.5
    p06 = hp.reorder(p06_nest.astype(float), n2r=True)
    good = np.concatenate([p06_nest, p06_nest])
    sub = ninv[np.ix_(good, good)]
    lch = np.linalg.cholesky(0.5 * (sub + sub.T))
    k16 = pb.eb_operator(p06, 16)
    rng_w = np.random.default_rng([SEED, 23])

    def wmap_eb(qnest: np.ndarray, unest: np.ndarray) -> np.ndarray:
        return pb.extract_eb(hp.reorder(qnest, n2r=True), hp.reorder(unest, n2r=True), p06, k16)

    obs_w = wmap_eb(q16, u16)
    npx = q16.size
    from scipy.linalg import solve_triangular
    draws = solve_triangular(lch.T, rng_w.standard_normal((int(good.sum()), N_WMAP_MC)), lower=False)   # covariance (L L^T)^-1 = N
    null_w = []
    for j in range(N_WMAP_MC):
        x = np.zeros(2 * npx)
        x[good] = draws[:, j]
        null_w.append(wmap_eb(x[:npx], x[npx:]))
    null_w = np.array(null_w)
    e_table["WMAP9_V"] = {"vector_E2": obs_w[0:5], "vector_B2": obs_w[45:50],
                          "law": f"WMAP9 V-band inverse-noise-matrix draws (N={N_WMAP_MC}) through the NSIDE 16 P06 estimator",
                          "E2_rms_uK": float(np.sqrt(np.mean(obs_w[0:5] ** 2))), "B2_rms_uK": float(np.sqrt(np.mean(obs_w[45:50] ** 2))),
                          "noise_B2_rms_uK": float(np.sqrt(np.mean(null_w[:, 45:50] ** 2))),
                          "Sigma_E_frobenius": float(np.linalg.norm(obs_w[0:5]) / norm_col), "f_sky_P06": float(p06.mean())}
    print(f"[L02] WMAP9 done {time.monotonic() - t0:.0f}s", flush=True)
    with np.load(PR4_CACHE, allow_pickle=False) as z:
        d_pr4, c_pr4 = z["cmb_pr4_d"].copy(), z["cmb_pr4_cov"].copy()
    rows2 = e2 + b2
    diff = d_pr4[rows2] - d_s[rows2]
    c_diff = c_pr4[np.ix_(rows2, rows2)] + np.cov(sims_noise[:, rows2].T, ddof=1)
    e_table["PR4_frequency_cache"] = {"role": "difference test against SMICA only (one split difference is not a null law)",
                                      "difference_test": fv.chi2_null_tail(pb.quadratic_form(diff, c_diff), 10,
                                                                           "gaussian difference test: PR4 ring-half split covariance + FFP10 SMICA noise"),
                                      "E2_rms_uK": float(np.sqrt(np.mean(d_pr4[e2] ** 2))), "B2_rms_uK": float(np.sqrt(np.mean(d_pr4[b2] ** 2)))}

    # ---- step 6: adopted E covariance floor (ell = 2 E and B rows)
    floor_l1 = float(l1["data"]["systematics_floor_uK2_per_ell"]["2"])
    hm = l01["optional_legs"]["half_mission"]
    floor_hm = max(hm["E2_variance_uK2"], hm["B2_variance_uK2"]) if hm["status"] == "DONE_SCOPED_C0" else 0.0
    pdl = l01["optional_legs"]["pipeline_dispersion"]
    floor_pd = max(pdl["E2_dispersion_variance_uK2"], pdl["B2_dispersion_variance_uK2"]) if pdl["status"] == "DONE_SCOPED_C0" else 0.0
    xs = np.array([np.concatenate([d_s[e2], d_s[b2]]),
                   np.concatenate([e_table["Cosmoglobe_DR1"]["vector_E2"], e_table["Cosmoglobe_DR1"]["vector_B2"]]),
                   np.concatenate([samples_e.mean(axis=0), samples_b.mean(axis=0)]), np.concatenate([obs_w[0:5], obs_w[45:50]])])
    floor_x = float(np.mean(xs.var(axis=0, ddof=1)))
    floors = {"R54-L1_B_null_floor_ell2": floor_l1, "half_mission": floor_hm, "pipeline_dispersion": floor_pd, "cross_experiment_dispersion": floor_x}
    floor = max(floors.values())
    adopted_e = {"floor_uK2": floor, "components_uK2": floors, "rows": "E and B, ell = 2", "definition": "S_FFP10 + diag(floor) on the ell = 2 E and B rows",
                 "cross_experiment_members": ["SMICA", "Cosmoglobe_DR1", "BeyondPlanck_v2_posterior_mean", "WMAP9_V"]}

    # ---- step 7: B ell=2 null with the adopted covariance
    rng_f = np.random.default_rng([SEED, 21])
    s_b2 = s_ref[np.ix_(b2, b2)]
    tests = {}
    pl = {"SMICA": d_s, "Commander": d_c}
    for k, v in pdl.get("vectors_135_uK", {}).items():
        pl[k] = np.asarray(v, float)
    for name, vec in pl.items():
        tests[f"PR3_{name}"] = {"family": "Planck_PR3", **floor_null(vec[b2], sims[:, b2], s_b2, floor, rng_f,
                                                                     "FFP10 B ell=2 realisations + Gaussian floor draws (N=300)")}
    for name in ("Cosmoglobe_DR1", "BeyondPlanck_v2_mean"):
        nb = null_store[name][:, 45:50]
        tests[name] = {"family": "Cosmoglobe_BeyondPlanck", **floor_null(e_table[name]["vector_B2"], nb, np.cov(nb.T, ddof=1), floor, rng_f,
                                                                          e_table[name]["law"] + " + Gaussian floor draws")}
    zt = pb.posterior_zero_tail(samples_b + math.sqrt(floor) * rng_f.standard_normal(samples_b.shape))
    tests["BeyondPlanck_v2_posterior"] = {"family": "Cosmoglobe_BeyondPlanck", **zt, "pass": bool(zt["p_value"] >= ALPHA)}
    nw = null_w[:, 45:50]
    tests["WMAP9_V"] = {"family": "WMAP9", **floor_null(obs_w[45:50], nw, np.cov(nw.T, ddof=1), floor, rng_f,
                                                        e_table["WMAP9_V"]["law"] + " + Gaussian floor draws")}
    families = sorted({t["family"] for t in tests.values() if t["pass"]})
    literal = sorted(k for k, t in tests.items() if t["pass"])
    status = "CLAIMABLE" if len(families) >= 2 else "DIAGNOSTIC"
    return {
        "status": "DONE_SCOPED_C0",
        "t_analytic_covariance_test": t_test, "cross_experiment_T": cross_t, "e_lane_table": e_table, "adopted_e_covariance": adopted_e,
        "b_null_adopted": tests, "e_lane_status": status,
        "e_lane_rule": "CLAIMABLE if the B ell=2 null passes (p >= 0.01) with the adopted covariance in at least two data families (DV-L02-9)",
        "passing_families": families, "passing_pipelines_or_experiments_contract_literal": literal,
        "decision": {"T_covariance": t_test["reason"], "T_lane": cross_t["status"], "E_lane": status},
        "pr4_simulations_used": False,
        "acceptance": {"e_lane_status": {"value": status, "op": "in", "threshold": ["CLAIMABLE", "DIAGNOSTIC"], "pass": status in ("CLAIMABLE", "DIAGNOSTIC")},
                       "pr4_simulations_used": {"value": False, "op": "==", "threshold": False, "pass": True}},
        "runtime_s": time.monotonic() - t0}


def main() -> None:
    res = compute()
    inputs = [SIMS, CAMB, WMAP_ILC, WMAP_MASKS, WMAP_BANDS, WMAP_NINV, CG_CMB, BP_CMB, BP_MASK_I, BP_MASK_P, PR4_CACHE]
    prov = {"script": "scripts/r54/run_r54_l02_pr4_bypass.py", "script_sha256": sha256(Path(__file__)),
            "inputs_sha256": {**{str(p): sha256(p) for p in inputs if p.is_file()},
                              **{str(p.relative_to(ROOT)): sha256(p) for p in (NPZ, R54 / "RESULTS/R54_L01_RESULT.json", R54 / "RESULTS/R54_L1_TYPE1_TE.json")}},
            "bp_chains": [str(p) for p in BP_CHAINS], "seed": SEED, "python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__}
    cmb = load_script("r54_cmb_clean", "scripts/r54/run_r54_cmb_type1.py")
    out = {"schema": "htt.r54.l02_pr4_bypass/1", "node": "R54-L02", "claim_tier": "C0", **res, "provenance": prov,
           "limitations": ["Analytic T covariance truncated at ell' <= 30 (range of the C_ell file); the coupling uses the NSIDE 128 mask of the R51 operator.",
                           "Cosmoglobe and the BeyondPlanck mean map use a white-noise model of their posterior STDDEV maps; the BeyondPlanck posterior leg uses thinned samples (a posterior tail of the zero vector).",
                           "WMAP9 V uses an N_obs-weighted degrade of the NSIDE 512 map with the NSIDE 16 noise matrix; E-to-B leakage from ell > 6 is not modelled.",
                           "PR4 enters only as a difference test (one ring-half split, frequency-map cache of R49); no NPIPE simulation is used."]}
    OUT.write_text(json.dumps(cmb.clean(out), indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(cmb.clean({"status": out["status"], "decision": out.get("decision"), "acceptance": out.get("acceptance")}), indent=1))
    if out["status"] != "DONE_SCOPED_C0":
        raise SystemExit(out["status"])


if __name__ == "__main__":
    main()
