"""R51: source-bound PR3 low-ell temperature likelihood with finite-MC law.

Run: PYTHONPATH=htt/src:htt:. python scripts/r51/run_r51_pr3_lowell.py

Inputs stay local (raw maps, FFP10 cache). Commits only compact products.
Lane: SMICA_PR3_DIAGNOSTIC (SMICA map + matched SMICA FFP10 CMB+noise MC). The
Commander-primary calibration is UNAVAILABLE (no matched Commander MC); the
Commander map enters only as an uncalibrated cross-pipeline data difference.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import subprocess
import sys
import time
from pathlib import Path

import healpy as hp
import numpy as np
import scipy.stats
from astropy.io import fits
from scipy.stats import beta as beta_dist
from scipy.stats import chi2, kstest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "htt"), str(ROOT / "htt/src")]

from bass.transport.general_bianchi_transfer import (  # noqa: E402
    TiltedTransferParameters, compute_general_bianchi_transfer,
)
from htt.htt.infer.r49_general_bianchi_likelihood import _pack_transfer_modes, standard_lowell_mode_labels  # noqa: E402
from htt.htt.infer.r51_source_bound_response import (  # noqa: E402
    bianchi_i_shear_history_integral, carrier_quadratic, finite_mc_t_loglike, gaussian_loglike,
    heldout_pit, radiation_density_parameter, signed_linear_carrier,
)

OUT = ROOT / "docs/research_program/observational_publication_20261015/R50_OBSERVED_CONVERGENCE_20261115/R51"
RAW = Path("/mnt/extdrive/workdir/raw")
CACHE = Path("/mnt/extdrive/workdir/r49_chains")
SMICA = RAW / "planck_data/COM_CMB_IQU-smica_2048_R3.00_full.fits"
COMMANDER = RAW / "planck_data/COM_CMB_IQU-commander_2048_R3.00_full.fits"
MASK_I = RAW / "planck_data/COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits"
MASK_P = RAW / "planck_data/COM_Mask_CMB-common-Mask-Pol_2048_R3.00.fits"
FFP = RAW / "planck_ffp10/smica"
T_CMB_UK = 2.72548e6  # SSOT T_CMB
Z_STAR = 1089.94
PLANCK18 = {"H0": 67.36, "Omega_m": 0.3153}  # Planck 2018 VI TT,TE,EE+lowE+lensing
SOLAR_DIPOLE = {"amp_uK": 3362.08, "l_deg": 264.021, "b_deg": 48.253}  # Planck 2018 I
LABELS = standard_lowell_mode_labels((2, 3, 4, 5, 6), include_eb=True)
T_ROWS = np.array([lb.startswith("T_") for lb in LABELS])
# Orthonormal STF5 basis, tr(E_a E_b) = delta_ab, Galactic frame.
s2, s6 = 1 / math.sqrt(2), 1 / math.sqrt(6)
STF = np.array([
    [[s2, 0, 0], [0, -s2, 0], [0, 0, 0]],
    [[s6, 0, 0], [0, s6, 0], [0, 0, -2 * s6]],
    [[0, s2, 0], [s2, 0, 0], [0, 0, 0]],
    [[0, 0, s2], [0, 0, 0], [s2, 0, 0]],
    [[0, 0, 0], [0, 0, s2], [0, s2, 0]],
])
PREREG = {
    "written_before_inspection": True,
    "covariance_train_ffp10_ids": [0, 199],
    "heldout_ffp10_ids": [200, 299],
    "laws": ["finite_mc_sellentin_heavens", "plugin_gaussian"],
    "carriers": ["T45", "TEB135"],
    "tests": "central 68% and 95% PIT coverage (binomial test, Clopper-Pearson 95% CI) + KS uniformity per law x carrier",
    "n_tests": 12,
    "multiple_test_policy": "Bonferroni alpha=0.05/12 per test; a law is 'calibrated' only if none of its tests rejects",
    "target_likelihood": "T45 only, S from all 300 FFP10 pairs, finite-MC law",
    "polarization_policy": "E/B rows carry no source-bound response (0.18 gain is a working model): marginalized as free-mean nuisance = dropped",
    "estimand": "Sigma_ab = int_{t_*}^{t_0} sigma_ab dt, 5 orthonormal STF components, Galactic frame, dimensionless",
    "prior": "flat on each s_k within |s_k|<=1e-3 (proper box; posterior mass interior)",
    "signed_alternatives": "s = +-1e-5 e_k, k=0..4, fixed before inspection",
    "scalar_projection_axis": "e_1 = diag(1,1,-2)/sqrt(6) (Galactic-pole axisymmetric component)",
    "power_only": "|s|^2 (even summary)",
    "null": "same-estimator leave-one-out FFP10 replicate (Sigma=0 LCDM null); tail (k+1)/(N+1)",
    "velocity_null": "BETA_MO same-estimator joint null NOT produced; no matched Pi output",
}


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def lane_module():
    spec = importlib.util.spec_from_file_location("r49_lanes", ROOT / "scripts/r49/run_r49_cmb_and_multiprobe_lanes.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_mask(p: Path, col: str) -> np.ndarray:
    with fits.open(p, memmap=True) as h:
        return hp.reorder(np.asarray(h[1].data[col], np.float32).reshape(-1), n2r=True) > 0.5


def read_sim_ring_uK(p: Path):
    with fits.open(p, memmap=True) as h:
        d = h[1].data
        return [np.asarray(d[c], np.float64).reshape(-1) * 1e6 for c in ("INTENSITY", "Q-POLARISATION", "U-POLARISATION")]


def clopper(k: int, n: int) -> list[float]:
    lo = 0.0 if k == 0 else float(beta_dist.ppf(0.025, k, n - k + 1))
    hi = 1.0 if k == n else float(beta_dist.ppf(0.975, k + 1, n - k))
    return [lo, hi]


def tail(obs: float, arr) -> dict:
    k = int(np.sum(np.asarray(arr) >= obs))
    return {"k": k, "N": len(arr), "p_mc": (k + 1) / (len(arr) + 1)}


def main() -> dict:
    t0 = time.monotonic()
    OUT.mkdir(parents=True, exist_ok=True)
    git_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    prereg_path = OUT / "PREREGISTRATION.json"
    if not prereg_path.exists():
        prereg_path.write_text(json.dumps({**PREREG, "git_head_at_registration": git_sha,
                                           "registered_unix": time.time()}, indent=1) + "\n")
    lanes = lane_module()

    # ---- inputs and identities
    ids = {p.name: sha(p) for p in (SMICA, COMMANDER, MASK_I, MASK_P)}
    rehash = json.loads((ROOT / "docs/research_program/observational_publication_20261015/R49_GENERAL_TILTED_BIANCHI_20261112/DATA_REHASH_RECEIPT.json").read_text())["hashed_primary_files"]
    ids_match = {"smica": ids[SMICA.name] == rehash["pr3_smica_full"]["sha256"],
                 "mask_int": ids[MASK_I.name] == rehash["pr3_mask_int"]["sha256"],
                 "mask_pol": ids[MASK_P.name] == rehash["pr3_mask_pol"]["sha256"]}
    with fits.open(SMICA, memmap=True) as h:
        int_beam = np.asarray(h[2].data["INT_BEAM"], float).reshape(-1)[:7]
    pixwin = hp.pixwin(2048)[:7]

    op = lanes.build_lowell_mask_operators(read_mask(MASK_I, "TMASK"), read_mask(MASK_P, "PMASK"))
    d_smica = lanes.extract_debiased_135_uK(*lanes.read_nested_iqu_ring_uK(SMICA), op, in_place=True)
    d_comm = lanes.extract_debiased_135_uK(*lanes.read_nested_iqu_ring_uK(COMMANDER), op, in_place=True)
    with np.load(CACHE / "r49_real_multiprobe_dataset.npz", allow_pickle=False) as z:
        d_r49 = z["cmb_pr3_d"].copy()
    with np.load(CACHE / "ffp10_300_debiased_135.npz", allow_pickle=False) as z:
        sims, sims_noise = z["sim_tot"].copy(), z["sim_noise"].copy()
    spot = {}
    for i in (0, 299):  # independent astropy reader vs R49 raw-byte reader
        c = read_sim_ring_uK(FFP / f"cmb_mc/dx12_v3_smica_cmb_mc_{i:05d}_raw.fits")
        n = read_sim_ring_uK(FFP / f"noise_mc/dx12_v3_smica_noise_mc_{i:05d}_raw.fits")
        v = lanes.extract_debiased_135_uK(c[0] + n[0], c[1] + n[1], c[2] + n[2], op, in_place=True)
        del c, n
        spot[str(i)] = float(np.max(np.abs(v - sims[i])) / np.max(np.abs(sims[i])))

    # ---- forward response through the identical masked estimator (beam x pixel window bound)
    nside_t = 64
    nvec = np.array(hp.pix2vec(nside_t, np.arange(hp.nside2npix(nside_t)))).T
    J = np.zeros((135, 5))
    J_ideal = np.zeros((135, 5))
    recon_err = 0.0
    for k in range(5):
        tmap = -T_CMB_UK * np.einsum("pi,ij,pj->p", nvec, STF[k], nvec)
        alm = hp.map2alm(tmap, lmax=6, iter=10)
        recon_err = max(recon_err, float(np.max(np.abs(hp.alm2map(alm, nside_t, lmax=6) - tmap)) / np.max(np.abs(tmap))))
        J_ideal[:, k] = np.concatenate([lanes._pack_hp_alm_n(alm, lanes._MODES_45), np.zeros(90)])
        big = hp.alm2map(hp.almxfl(alm, int_beam * pixwin), 2048, lmax=6)
        J[:, k] = lanes.extract_debiased_135_uK(big, np.zeros_like(big), np.zeros_like(big), op, in_place=True)
        del big
    # independent route: R49 transfer GL quadrature + R49 mode packing (convention cross-check)
    J_transfer = np.zeros((135, 5))
    for k in range(5):
        out = compute_general_bianchi_transfer(TiltedTransferParameters(family="I", sigma_N=STF[k], ell_max=6, n_gl_theta=16))
        J_transfer[:, k] = T_CMB_UK * _pack_transfer_modes(out.cosmo_alm_T, out.cosmo_alm_E, out.cosmo_alm_B, LABELS)
    jt_scale = np.max(np.abs(J_ideal[T_ROWS]))
    checks = {
        "template_alm_reconstruction_rel": recon_err,
        "estimator_vs_ideal_T_rel": float(np.max(np.abs(J[T_ROWS] - J_ideal[T_ROWS])) / jt_scale),
        "estimator_T_to_EB_leak_rel": float(np.max(np.abs(J[~T_ROWS])) / jt_scale),
        "transfer_route_vs_healpy_T_rel": float(np.max(np.abs(J_transfer[T_ROWS] - J_ideal[T_ROWS])) / jt_scale),
        "observed_vs_R49_cached_d_max_abs_uK": float(np.max(np.abs(d_smica - d_r49))),
        "ffp10_cache_spot_recompute_rel": spot,
        "input_identity_matches_R49_rehash": ids_match,
        "beam_x_pixwin_ell2_6": (int_beam * pixwin)[2:].tolist(),
    }

    # ---- preregistered covariance calibration with disjoint train/heldout IDs
    train, held = sims[:200], sims[200:]
    calib = {}
    alpha = 0.05 / PREREG["n_tests"]
    for cname, rows in (("T45", T_ROWS), ("TEB135", np.ones(135, bool))):
        pits = [heldout_pit(x[rows], train[:, rows]) for x in held]
        for law, key in (("finite_mc", "pit_finite_mc"), ("plugin_gaussian", "pit_plugin_gaussian")):
            u = np.array([p[key] for p in pits])
            k68 = int(np.sum((u > 0.16) & (u < 0.84)))
            k95 = int(np.sum((u > 0.025) & (u < 0.975)))
            ks = float(kstest(u, "uniform").pvalue)
            b68 = float(scipy.stats.binomtest(k68, len(u), 0.68).pvalue)
            b95 = float(scipy.stats.binomtest(k95, len(u), 0.95).pvalue)
            calib[f"{cname}/{law}"] = {
                "n_heldout": len(u), "cov68": k68 / len(u), "cov68_CI95": clopper(k68, len(u)),
                "cov95": k95 / len(u), "cov95_CI95": clopper(k95, len(u)),
                "ks_p": ks, "binom68_p": b68, "binom95_p": b95,
                "rejected_at_bonferroni": bool(min(ks, b68, b95) < alpha),
            }

    # ---- target T-only likelihood, S from all 300 pairs
    N = sims.shape[0]
    S_full = np.cov(sims.T, ddof=1)
    S_full = 0.5 * (S_full + S_full.T)
    S = S_full[np.ix_(T_ROWS, T_ROWS)]
    JT, dT = J[T_ROWS], d_smica[T_ROWS]
    car = signed_linear_carrier(JT, dT, S)
    F, t, Q0 = car["F"], car["t"], car["Q0"]
    Finv = np.linalg.inv(F)
    Finv = 0.5 * (Finv + Finv.T)
    s_hat = Finv @ t
    sd = np.sqrt(np.diag(Finv))
    om_r = radiation_density_parameter(PLANCK18["H0"] / 100)
    hist = bianchi_i_shear_history_integral(PLANCK18["Omega_m"], om_r, 1 - PLANCK18["Omega_m"] - om_r, Z_STAR)

    def logl_t(s):
        return finite_mc_t_loglike(dT - JT @ s, S, N)

    def logl_g(s):
        return gaussian_loglike(dT - JT @ s, S)

    def tensor_t(s):
        return -0.5 * N * math.log1p(carrier_quadratic(car, s) / (N - 1))

    # importance-sampled finite-MC posterior (flat box prior, multivariate-t proposal df=5)
    rng = np.random.default_rng(51051)
    P = 2.0 * Finv
    Lp = np.linalg.cholesky(P)
    nd = 200000
    z = rng.standard_normal((nd, 5))
    g = rng.chisquare(5, nd) / 5
    draws = s_hat + (z / np.sqrt(g)[:, None]) @ Lp.T
    inbox = np.all(np.abs(draws) <= 1e-3, axis=1)
    qd = np.einsum("ni,ij,nj->n", draws - s_hat, np.linalg.inv(P), draws - s_hat)
    logq = -0.5 * (5 + 5) * np.log1p(qd / 5)
    Qd = Q0 - 2 * draws @ t + np.einsum("ni,ij,nj->n", draws, F, draws)
    logp = -0.5 * N * np.log1p(Qd / (N - 1))
    lw = np.where(inbox, logp - logq, -np.inf)
    w = np.exp(lw - lw.max())
    w /= w.sum()
    ess = float(1.0 / np.sum(w**2))
    post_mean = w @ draws
    post_cov = (draws - post_mean).T @ ((draws - post_mean) * w[:, None])
    post_sd = np.sqrt(np.diag(post_cov))
    norms = np.linalg.norm(draws, axis=1)
    order = np.argsort(norms)
    norm95 = float(norms[order][np.searchsorted(np.cumsum(w[order]), 0.95)])

    # ---- comparison methods on identical data / prior / law
    dom = s_hat + rng.standard_normal((500, 5)) @ np.linalg.cholesky(25.0 * Finv).T
    l0t, l0g = logl_t(np.zeros(5)), logl_g(np.zeros(5))
    err_tensor_t = max(abs((logl_t(s) - l0t) - (tensor_t(s) - tensor_t(np.zeros(5)))) for s in dom)
    err_tensor_g = max(abs((logl_g(s) - l0g) - (s @ t - 0.5 * s @ F @ s)) for s in dom)
    err_no_q0 = max(abs((logl_t(s) - l0t) - (s @ t - 0.5 * s @ F @ s)) for s in dom)
    e1 = np.eye(5)[1:2]
    FI_scalar = e1.T @ np.linalg.inv(e1 @ Finv @ e1.T) @ e1
    gen = np.sort(np.real(np.linalg.eigvals(np.linalg.solve(F, FI_scalar))))
    signed = []
    for k in range(5):
        a = 1e-5 * np.eye(5)[k]
        signed.append({"axis": k, "full_logLR_plus_vs_minus": logl_t(a) - logl_t(-a),
                       "tensor_logLR_plus_vs_minus": tensor_t(a) - tensor_t(-a),
                       "power_only_logLR_plus_vs_minus": 0.0})

    # ---- same-estimator leave-one-out Sigma=0 null and adequacy
    null_wald, null_q0, null_shat, null_q0_135, null_fsd = [], [], [], [], []
    for i in range(N):
        Sm_full = np.cov(np.delete(sims, i, axis=0).T, ddof=1)
        Sm_full = 0.5 * (Sm_full + Sm_full.T)
        c = signed_linear_carrier(JT, sims[i, T_ROWS], Sm_full[np.ix_(T_ROWS, T_ROWS)])
        sh = np.linalg.solve(c["F"], c["t"])
        null_wald.append(float(c["t"] @ sh)); null_q0.append(c["Q0"]); null_shat.append(sh)
        null_fsd.append(np.sqrt(np.diag(np.linalg.inv(c["F"]))))
        L135 = np.linalg.cholesky(Sm_full)
        null_q0_135.append(float(np.sum(np.linalg.solve(L135, sims[i]) ** 2)))
    null_shat = np.array(null_shat)
    null_fsd = np.array(null_fsd)
    # Parameter-interval coverage on the Sigma=0 LOO replicates (review finding 1):
    sd_ratio_post = float(np.mean(post_sd / sd))
    cov_post = np.mean(np.abs(null_shat) <= 1.959964 * sd_ratio_post * null_fsd, axis=0)
    cov_fisher = np.mean(np.abs(null_shat) <= 1.959964 * null_fsd, axis=0)
    C_emp = np.cov(null_shat.T, ddof=1)
    cov_emp = np.mean(np.abs(null_shat) <= 1.959964 * np.sqrt(np.diag(C_emp)), axis=0)
    cal = rng.multivariate_normal(s_hat, C_emp, size=200000)
    cal = cal[np.all(np.abs(cal) <= 1e-3, axis=1)]
    norm95_cal = float(np.quantile(np.linalg.norm(cal, axis=1), 0.95))
    obs_wald = float(t @ s_hat)
    obs_q0_135 = float(np.sum(np.linalg.solve(np.linalg.cholesky(S_full), d_smica) ** 2))

    # ---- removed-mode sensitivity: kinematic quadrupole of the solar dipole
    lr, br = math.radians(SOLAR_DIPOLE["l_deg"]), math.radians(SOLAR_DIPOLE["b_deg"])
    bh = np.array([math.cos(br) * math.cos(lr), math.cos(br) * math.sin(lr), math.sin(br)])
    beta = SOLAR_DIPOLE["amp_uK"] / T_CMB_UK
    kq = {}
    for bnu in (1.0, 1.5, 2.0):
        sig_kq = -bnu * beta**2 * (np.outer(bh, bh) - np.eye(3) / 3)  # dT/T = b beta^2 [(n.bh)^2-1/3] == -n Sigma_KQ n
        s_kq = np.einsum("kij,ij->k", STF, sig_kq)
        kq[f"b_nu={bnu}"] = {"s_equiv": s_kq.tolist(), "shift_in_gaussian_sd": (s_kq / sd).tolist()}

    # ---- Commander uncalibrated cross-pipeline difference
    diffT = (d_comm - d_smica)[T_ROWS]
    noise_sd = np.std(sims_noise[:, T_ROWS], axis=0, ddof=1)
    s_comm = Finv @ (JT.T @ np.linalg.solve(S, d_comm[T_ROWS]))

    result = {
        "node_id": "R51",
        "lane": "SMICA_PR3_DIAGNOSTIC_T_ONLY",
        "commander_primary_calibration": "UNAVAILABLE: Commander FFP10 MC incomplete (2 complete cmb_mc files, partials, no noise_mc)",
        "source_git_sha": git_sha, "input_sha256": ids, "n_mc": N, "p_target": int(T_ROWS.sum()),
        "estimand": PREREG["estimand"], "stf_basis": STF.tolist(), "checks": checks, "calibration": calib,
        "carrier": {"F": F.tolist(), "t": t.tolist(), "Q0": Q0},
        "Sigma_hat": s_hat.tolist(), "Sigma_sd_gaussian": sd.tolist(),
        "finite_mc_posterior": {"mean": post_mean.tolist(), "sd": post_sd.tolist(),
                                "sd_ratio_to_gaussian": (post_sd / sd).tolist(), "ess": ess, "n_draws": nd,
                                "Sigma_frobenius_95pct_upper_NOT_coverage_calibrated": norm95},
        "history_operator": {"I_hist": hist, "Omega_r": om_r, "z_star": Z_STAR,
                             "assumptions": "sigma a^3 const (no anisotropic stress), Planck18 LCDM background, fixed eigenframe", **PLANCK18},
        "interval_calibration": {
            "status": "finite-MC law calibrates the predictive data law (heldout PIT), NOT parameter intervals",
            "sigma0_loo_component_coverage_nominal95": {
                "finite_mc_posterior_width": cov_post.tolist(), "fisher_width": cov_fisher.tolist(),
                "loo_empirical_sampling_width": cov_emp.tolist(), "n_replicates": N},
            "loo_sampling_sd_over_fisher_sd": (np.sqrt(np.diag(C_emp)) / sd).tolist(),
            "Sigma_frobenius_95pct_upper_loo_calibrated": norm95_cal,
            "method": "flat-box Gaussian N(Sigma_hat, C_emp), C_emp = covariance of same-estimator LOO Sigma_hat over 300 FFP10 replicates",
        },
        "conditional_sigma_over_H0_today": {"mean": (post_mean / hist).tolist(), "sd_loo_calibrated": (np.sqrt(np.diag(C_emp)) / hist).tolist(),
                                            "frobenius_norm_95pct_upper_loo_calibrated": norm95_cal / hist,
                                            "status": "CONDITIONAL on history operator assumptions (no anisotropic stress; 67% of I_hist from z>500); unquantified systematic"},
        "zero_shear_test": {"wald_obs": obs_wald, "working_chi2_5_tail": float(chi2.sf(obs_wald, 5)),
                            "mc_same_estimator_loo": tail(obs_wald, null_wald),
                            "exchangeability": "approximate: observed uses S from 300 sims, replicate i uses the other 299"},
        "adequacy_ppc": {"Q0_T45_obs": Q0, "Q0_T45_mc_loo": tail(Q0, null_q0),
                         "Q0_TEB135_obs": obs_q0_135, "Q0_TEB135_mc_loo": tail(obs_q0_135, null_q0_135)},
        "null_shat_sd_over_fisher_sd": (np.std(null_shat, axis=0, ddof=1) / sd).tolist(),
        "comparisons": {
            "law": "finite_mc (Sellentin-Heavens) on T45; same data, prior box, N",
            "tensor_carrier_F_t_Q0_finite_mc_max_abs_logLR_err": err_tensor_t,
            "tensor_carrier_F_t_gaussian_max_abs_logLR_err": err_tensor_g,
            "tensor_F_t_without_Q0_under_finite_mc_max_abs_logLR_err": err_no_q0,
            "optimal_linear_score": "TIE with tensor carrier: identical (F,t); finite-MC law additionally needs scalar Q0",
            "scalar_fixed_axis_e1_generalized_Fisher_retention": gen.tolist(),
            "scalar_e1_marginal": "TIE for the e1 marginal only (Gaussian, flat prior); LOSS for 5D target",
            "power_only": "LOSS: sign-blind, logLR(+a vs -a)=0 identically",
            "signed_alternatives": signed,
            "domain": "500 draws from N(s_hat, 25 F^-1)",
        },
        "removed_mode_sensitivity_kinematic_quadrupole": {
            "status": "UNBOUND: KQ removal in PR3 SMICA map and FFP10 MC not verified from file metadata or local docs",
            "solar_dipole": SOLAR_DIPOLE, "cases": kq},
        "commander_cross_pipeline_uncalibrated": {
            "T45_diff_rms_uK": float(np.sqrt(np.mean(diffT**2))),
            "T45_diff_rms_in_smica_ffp10_noise_sd": float(np.sqrt(np.mean((diffT / noise_sd) ** 2))),
            "Sigma_hat_commander_minus_smica_in_sd": ((s_comm - s_hat) / sd).tolist(),
            "status": "UNCALIBRATED_DIAGNOSTIC (SMICA covariance; not a Commander likelihood)"},
        "prereg_erratum": ["polarization_policy: dropping E/B equals free-mean marginalization only under a Gaussian law; under the finite-MC law the T45 likelihood is the T-only law, not that marginal",
                           "written_before_inspection is asserted by this script at first run; the SMICA vector was already analysed in R49, so the analysis is not blind"],
        "velocity_null": "UNAVAILABLE: no same-estimator joint beta_MO replicates; BETA_MO_MATCHED_NULL not output",
        "elapsed_s": time.monotonic() - t0,
    }
    np.savez(OUT / "observed_carrier.npz", allow_pickle=False,
             mode_labels=np.array(LABELS), d_smica_135_uK=d_smica, d_commander_135_uK=d_comm,
             response_J_135x5_uK=J, response_J_ideal_135x5_uK=J_ideal, stf_basis_5x3x3=STF,
             S_ffp10_300_135x135_uK2=S_full, F_T45=F, t_T45=t, Q0_T45=np.array(Q0), n_mc=np.array(N),
             null_loo_shat_300x5=null_shat, null_loo_wald_300=np.array(null_wald))
    (OUT / "R51_PR3_LOWELL_RESULT.json").write_text(json.dumps(result, indent=1, allow_nan=False) + "\n")
    return result


if __name__ == "__main__":
    r = main()
    for key in ("checks", "Sigma_hat", "Sigma_sd_gaussian", "finite_mc_posterior", "history_operator",
                "conditional_sigma_over_H0_today", "zero_shear_test", "adequacy_ppc", "calibration",
                "comparisons", "removed_mode_sensitivity_kinematic_quadrupole", "commander_cross_pipeline_uncalibrated", "elapsed_s"):
        print(key, json.dumps(r[key], indent=1))
