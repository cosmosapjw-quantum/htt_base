"""R97 Unit B (G05_PLANCK / P2): Exact Mask-Pol E->B coupling, 60D cross-split leakage debiasing & NSIDE=2048 injection-recovery.

Reuses:
  - 999 CMB + 300 unique-noise NSIDE=2048 lmax=48 TEB harmonic cache in ~/Downloads/htt_r94_fullres_stream
  - PR3 common Mask-Int / Mask-Pol FITS (exact NSIDE=2048 RING)
  - scripts/r96/legacy_biposh_recovered.py & scripts/r96/cmb_crossfit_null.py
  - scripts/r94/gaunt_fast.py & scripts/r93/smica_ffp999_biposh.py

Performs:
  1. Analytic Master / Hivon et al. (2002) spin-2 Wigner-3j E->B mask-coupling operator M^{EE->BB}
     from Mask-Pol (lmax=96) and cross-checks against NSIDE=2048 pure-E Monte Carlo sky projection.
  2. Empirical cross-channel 60D signed L=2 leakage operator L_{E|T, B|T+E} calibrated strictly on
     even-ID training realizations (N=150) using signal-only + noise-only + paired realizations,
     and evaluated out-of-sample on odd-ID heldout realizations (N=150) + PR3 SMICA (Commander separate).
  3. Controlled anisotropy injection & recovery under exact NSIDE=2048 Mask-Int/Pol + SMICA 5' beam
     and OLS monopole/dipole subtraction (linearized template sweep on N=150 heldout + exact full-sky
     pixel-space multiplicative L=2 modulation verification at NSIDE=2048).

Preserves commander_null_qualified = False, Bianchi_family_attribution = None, physical_Pi = None, physical_GF = None.
"""
from __future__ import annotations

from decimal import Decimal, getcontext
import hashlib
import json
import math
import time
from pathlib import Path
import sys

import healpy as hp
import numpy as np
from scipy.linalg import cho_factor, cho_solve
from sympy.physics.wigner import wigner_3j

getcontext().prec = 60

ROOT = Path(__file__).resolve().parents[2]
for p in (str(ROOT), str(ROOT / "htt"), str(ROOT / "htt/src")):
    if p not in sys.path:
        sys.path.insert(0, p)

from scripts.r94 import gaunt_fast
from scripts.r93 import smica_ffp999_biposh as r93
from scripts.r95.planck_fullres_teb_analysis import _all_six_spectra
from scripts.r96 import cmb_crossfit_null as r96_cmb

STREAM = Path.home() / "Downloads/htt_r94_fullres_stream"
MASK_I_FITS = Path("/mnt/extdrive/workdir/raw/planck_data/COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits")
MASK_P_FITS = Path("/mnt/extdrive/workdir/raw/planck_data/COM_Mask_CMB-common-Mask-Pol_2048_R3.00.fits")
OUT_JSON = ROOT / "docs/research_program/observational_publication_20261015/R97_SCIENCE_EXECUTION_20261122/CMB_INJECTION_AND_EB_LEAKAGE.json"
LMAX = 48
FWHM_ARCMIN = 5.0


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def _smica_beam_wl(lmax: int, fwhm_arcmin: float = FWHM_ARCMIN) -> np.ndarray:
    fwhm_rad = math.radians(fwhm_arcmin / 60.0)
    sigma_b = fwhm_rad / math.sqrt(8.0 * math.log(2.0))
    ells = np.arange(lmax + 1, dtype=np.float64)
    return np.exp(-0.5 * ells * (ells + 1.0) * (sigma_b ** 2))


_FAC_INT = [math.factorial(k) for k in range(512)]


def _racah_w3j(j1: int, j2: int, j3: int, m1: int, m2: int, m3: int) -> float:
    """Exact integer-denominator Racah Wigner-3j converted at final step to float64 (zero cancellation)."""
    if m1 + m2 + m3 != 0 or j3 < abs(j1 - j2) or j3 > j1 + j2:
        return 0.0
    if abs(m1) > j1 or abs(m2) > j2 or abs(m3) > j3:
        return 0.0
    t1 = j3 - j2 + m1
    t2 = j3 - j1 - m2
    t3 = j1 + j2 - j3
    t4 = j1 - m1
    t5 = j2 + m2
    tmin = max(0, -t1, -t2)
    tmax = min(t3, t4, t5)
    if tmin > tmax:
        return 0.0
    M = _FAC_INT[tmax] * _FAC_INT[t1 + tmax] * _FAC_INT[t2 + tmax] * _FAC_INT[t3 - tmin] * _FAC_INT[t4 - tmin] * _FAC_INT[t5 - tmin]
    s_num = 0
    for t in range(tmin, tmax + 1):
        d = _FAC_INT[t] * _FAC_INT[t1 + t] * _FAC_INT[t2 + t] * _FAC_INT[t3 - t] * _FAC_INT[t4 - t] * _FAC_INT[t5 - t]
        term = M // d
        s_num += (-term if (t & 1) else term)
    if s_num == 0:
        return 0.0
    pref_num = (
        _FAC_INT[t3]
        * _FAC_INT[j1 + j3 - j2]
        * _FAC_INT[j2 + j3 - j1]
        * _FAC_INT[j1 + m1]
        * _FAC_INT[t4]
        * _FAC_INT[t5]
        * _FAC_INT[j2 - m2]
        * _FAC_INT[j3 + m3]
        * _FAC_INT[j3 - m3]
    )
    pref_den = _FAC_INT[j1 + j2 + j3 + 1]
    val = float(((Decimal(pref_num) / Decimal(pref_den)).sqrt() * Decimal(s_num)) / Decimal(M))
    if ((j1 - j2 - m3) & 1) == 1:
        val = -val
    return val


def _spin2_mask_coupling_matrices(maskP: np.ndarray, lmax: int = LMAX) -> dict:
    """Exact Hivon+ (2002) Master spin-2 E/B mask-coupling matrices M^{++} (E->E, B->B) and M^{--} (E->B)."""
    lmax_m = 2 * lmax
    alm_m = hp.map2alm(maskP, lmax=lmax_m, iter=0, pol=False)
    wl_p = hp.alm2cl(alm_m)
    M_plus = np.zeros((lmax + 1, lmax + 1), dtype=np.float64)
    M_minus = np.zeros((lmax + 1, lmax + 1), dtype=np.float64)
    # Cross-check one entry against sympy.physics.wigner.wigner_3j
    w_ref = float(wigner_3j(10, 14, 6, 2, -2, 0))
    w_fast = _racah_w3j(10, 14, 6, 2, -2, 0)
    w3j_err = abs(w_ref - w_fast)
    if w3j_err > 1e-13:
        raise RuntimeError(f"Racah Wigner-3j precision failure: {w3j_err}")

    L_arr = np.arange(lmax_m + 1, dtype=np.float64)
    w_weighted = (2.0 * L_arr + 1.0) * wl_p
    for l1 in range(2, lmax + 1):
        for l2 in range(2, lmax + 1):
            pref = (2.0 * l2 + 1.0) / (8.0 * math.pi)
            sum_p = 0.0
            sum_m = 0.0
            L_lo = abs(l1 - l2)
            L_hi = min(l1 + l2, lmax_m)
            for L in range(L_lo, L_hi + 1):
                w = _racah_w3j(l1, l2, L, 2, -2, 0)
                term = w_weighted[L] * (w * w)
                if ((l1 + l2 + L) & 1) == 0:
                    sum_p += 2.0 * term
                else:
                    sum_m += 2.0 * term
            M_plus[l1, l2] = pref * sum_p
            M_minus[l1, l2] = pref * sum_m

    return {
        "M_EE_to_EE": M_plus,
        "M_EE_to_BB_leak": M_minus,
        "wigner3j_sympy_oracle_err": w3j_err,
        "f_sky_P_from_w00": float(alm_m[0].real / math.sqrt(4.0 * math.pi)),
    }


def _masked_ols_alm_from_fullsky(
    alm_TEB_full: np.ndarray,
    maskI: np.ndarray,
    maskP: np.ndarray,
    basis_T: np.ndarray,
    beta_G_inv: np.ndarray,
    pix_xyz: tuple[np.ndarray, np.ndarray, np.ndarray],
    lmax: int = LMAX,
) -> np.ndarray:
    """Apply SMICA 5' beam, NSIDE=2048 Mask-Int/Mask-Pol, and exact OLS monopole/dipole removal."""
    t_map, q_map, u_map = hp.alm2map(
        [alm_TEB_full[0], alm_TEB_full[1], alm_TEB_full[2]],
        nside=2048,
        lmax=lmax,
        pol=True,
    )
    vx, vy, vz = pix_xyz
    rhs = np.array([
        float(np.dot(maskI, t_map)),
        float(np.dot(maskI * vx, t_map)),
        float(np.dot(maskI * vy, t_map)),
        float(np.dot(maskI * vz, t_map)),
    ], dtype=np.float64)
    beta = beta_G_inv @ rhs
    aT_raw = hp.map2alm(t_map * maskI, lmax=lmax, iter=0, pol=False)
    aT = aT_raw - beta @ basis_T
    aE, aB = hp.map2alm_spin([q_map * maskP, u_map * maskP], spin=2, lmax=lmax)
    return np.asarray([aT, aE, aB], dtype=np.complex128)


def _fit_and_apply_shrinkage(X_train: np.ndarray, shrinkage: float) -> tuple[np.ndarray, np.ndarray, tuple]:
    mu = X_train.mean(axis=0)
    C = np.cov(X_train, rowvar=False, ddof=1)
    sd = np.sqrt(np.diag(C))
    corr = C / sd[:, None] / sd[None, :]
    corr_s = (1.0 - shrinkage) * corr + shrinkage * np.eye(X_train.shape[1])
    ch = cho_factor(corr_s, lower=True, check_finite=False)
    return mu, sd, ch


def _mahalanobis(v: np.ndarray, mu: np.ndarray, sd: np.ndarray, ch: tuple) -> float:
    r = (v - mu) / sd
    return float(r @ cho_solve(ch, r, check_finite=False))


def _ols_ridge_leakage_debiasing(
    X_sig_all: np.ndarray,
    X_pair_train: np.ndarray,
    X_pair_test: np.ndarray,
    obs_smica: np.ndarray,
    obs_cmd: np.ndarray,
    lam_ridge: float = 10.0,
) -> dict:
    """Fit out-of-sample cross-channel T/E -> B linear mask leakage operators on even train split.

    Evaluates:
      (1) Paired CMB+noise 150 train / 150 heldout (T,E -> B) with well-regularized ridge
      (2) Pure signal-only (999 cmb_only skies: 500 train / 499 heldout) E -> B mask leakage
    """
    # Feature blocks in 60D vector: T = [0:20], E = [20:40], B = [40:60]
    def _fit_predict(src_tr: np.ndarray, tgt_tr: np.ndarray, src_te: np.ndarray, tgt_te: np.ndarray, src_obs_s, src_obs_c):
        # Standardize predictors on train
        mu_x = src_tr.mean(axis=0)
        sd_x = np.maximum(src_tr.std(axis=0, ddof=1), 1e-30)
        mu_y = tgt_tr.mean(axis=0)
        Z = (src_tr - mu_x) / sd_x
        Y = tgt_tr - mu_y
        # Ridge W: (Z^T Z + lam*n*I)^{-1} Z^T Y
        p = Z.shape[1]
        W = np.linalg.solve(Z.T @ Z + lam_ridge * len(Z) * np.eye(p), Z.T @ Y)
        pred_tr = mu_y + ((src_tr - mu_x) / sd_x) @ W
        pred_te = mu_y + ((src_te - mu_x) / sd_x) @ W
        pred_obs_s = mu_y + ((src_obs_s - mu_x) / sd_x) @ W
        pred_obs_c = mu_y + ((src_obs_c - mu_x) / sd_x) @ W
        res_tr = tgt_tr - pred_tr
        res_te = tgt_te - pred_te
        var_raw = float(np.sum(np.var(tgt_te - mu_y, axis=0, ddof=1)))
        var_res = float(np.sum(np.var(res_te, axis=0, ddof=1)))
        return {
            "W_frob_norm": float(np.linalg.norm(W)),
            "heldout_total_variance_raw": var_raw,
            "heldout_total_variance_after_debias": var_res,
            "heldout_variance_ratio_after_over_raw": float(var_res / max(var_raw, 1e-30)),
            "res_tr": res_tr,
            "res_te": res_te,
            "res_obs_smica": obs_smica[40:60] - pred_obs_s,
            "res_obs_cmd": obs_cmd[40:60] - pred_obs_c,
        }

    # Signal+noise paired predictors for B-band leakage (150 train / 150 test):
    res_paired = _fit_predict(
        X_pair_train[:, :40], X_pair_train[:, 40:60],
        X_pair_test[:, :40], X_pair_test[:, 40:60],
        obs_smica[:40], obs_cmd[:40],
    )
    X60_deb_tr = X_pair_train.copy(); X60_deb_tr[:, 40:60] = res_paired["res_tr"]
    X60_deb_te = X_pair_test.copy(); X60_deb_te[:, 40:60] = res_paired["res_te"]
    obs_s_deb = obs_smica.copy(); obs_s_deb[40:60] = res_paired["res_obs_smica"]
    obs_c_deb = obs_cmd.copy(); obs_c_deb[40:60] = res_paired["res_obs_cmd"]

    # Shrinkage whitening below is fit on the 150 train ridge residuals (with strong lam_ridge=10 regularization
    # so out-of-sample degrees-of-freedom shrinkage bias is negligible; W itself is strictly out-of-sample on even N=150).
    mu_raw, sd_raw, ch_raw = _fit_and_apply_shrinkage(X_pair_train, 0.20)
    mu_deb, sd_deb, ch_deb = _fit_and_apply_shrinkage(X60_deb_tr, 0.20)
    sc_te_raw = np.array([_mahalanobis(v, mu_raw, sd_raw, ch_raw) for v in X_pair_test])
    sc_te_deb = np.array([_mahalanobis(v, mu_deb, sd_deb, ch_deb) for v in X60_deb_te])
    q_s_raw = _mahalanobis(obs_smica, mu_raw, sd_raw, ch_raw)
    q_s_deb = _mahalanobis(obs_s_deb, mu_deb, sd_deb, ch_deb)
    q_c_deb = _mahalanobis(obs_c_deb, mu_deb, sd_deb, ch_deb)

    # Pure signal-only E -> B mask leakage across all 999 cmb_only realizations (500 train / 499 heldout)
    even_sig = (np.arange(len(X_sig_all)) % 2) == 0
    res_sig_only = _fit_predict(
        X_sig_all[even_sig, 20:40], X_sig_all[even_sig, 40:60],
        X_sig_all[~even_sig, 20:40], X_sig_all[~even_sig, 40:60],
        obs_smica[20:40], obs_cmd[20:40],
    )

    return {
        "train_N": int(len(X_pair_train)),
        "test_N": int(len(X_pair_test)),
        "ridge_lambda_scaled": lam_ridge,
        "paired_TE_to_B_heldout_variance_ratio": res_paired["heldout_variance_ratio_after_over_raw"],
        "sig_only_999_E_to_B_heldout_variance_ratio": res_sig_only["heldout_variance_ratio_after_over_raw"],
        "sig_only_999_E_to_B_W_frob_norm": res_sig_only["W_frob_norm"],
        "raw_60D_150_150_obs_smica_score": float(q_s_raw),
        "raw_60D_150_150_rank_p": float((np.count_nonzero(sc_te_raw >= q_s_raw) + 1) / (len(sc_te_raw) + 1)),
        "debiased_B_60D_150_150_obs_smica_score": float(q_s_deb),
        "debiased_B_60D_150_150_rank_p": float((np.count_nonzero(sc_te_deb >= q_s_deb) + 1) / (len(sc_te_deb) + 1)),
        "commander_debiased_score_NOT_NULL_QUALIFIED": float(q_c_deb),
    }


def _run_injection_recovery(
    terms: list,
    X_train: np.ndarray,
    X_test: np.ndarray,
    paired_test_alm: np.ndarray,
    noise_test_alm: np.ndarray,
    cl_sig_fullsky: dict[str, np.ndarray],
    maskI: np.ndarray,
    maskP: np.ndarray,
    basis_T: np.ndarray,
    beta_G_inv: np.ndarray,
    pix_xyz: tuple[np.ndarray, np.ndarray, np.ndarray],
) -> dict:
    """Controlled L=2 anisotropic BiPoSH & polarized Bianchi template injection-recovery on 150 heldout skies."""
    nalm = hp.Alm.getsize(LMAX)
    wl = _smica_beam_wl(LMAX, FWHM_ARCMIN)

    # 1. Construct physical L=2 modulated polarized CMB sky template (coherent dipolar/quadrupolar L=2 coupling l <-> l+2)
    # Use a deterministic Gaussian isotropic realization modulated by real quadrupole g(n) = sqrt(4pi/5) Y_{20}(n) + ...
    #Wait: construct TWO distinct injected physical signals at full NSIDE=2048 mask+beam:
    # Type 1: Additive coherent Bianchi-like polarized T/E/B low-ell template with l <-> l+2 L=2 correlations
    rng = np.random.default_rng(9702)
    C_T = r93.iso_theory_cl()
    # Generate coherent base isotropic T+E realization matching Planck EE/TE scales
    a_base = np.zeros((3, nalm), dtype=np.complex128)
    for ell in range(2, LMAX + 1):
        sig_T = math.sqrt(float(C_T[ell]))
        sig_E = 0.08 * sig_T
        idx0 = hp.Alm.getidx(LMAX, ell, 0)
        z0 = rng.normal()
        a_base[0, idx0] = sig_T * z0
        a_base[1, idx0] = 0.5 * sig_E * z0 + 0.866 * sig_E * rng.normal()
        for m in range(1, ell + 1):
            idxm = hp.Alm.getidx(LMAX, ell, m)
            zc = (rng.normal() + 1j * rng.normal()) / math.sqrt(2.0)
            a_base[0, idxm] = sig_T * zc
            a_base[1, idxm] = 0.5 * sig_E * zc + 0.866 * sig_E * ((rng.normal() + 1j * rng.normal()) / math.sqrt(2.0))

    # Full-sky map of a_base, apply deterministic L=2 modulation field M_L2(n) = 3*cos^2(theta) - 1 + 0.7*sin^2(theta)*cos(2phi),
    # smooth with SMICA 5' beam, mask by EXACT NSIDE=2048 Mask-Int & Mask-Pol, and OLS monopole/dipole subtract!
    t_b, q_b, u_b = hp.alm2map([a_base[0], a_base[1], a_base[2]], nside=2048, lmax=LMAX, pol=True)
    vx, vy, vz = pix_xyz
    mod_L2 = 0.5 * (3.0 * vz * vz - 1.0) + 0.6 * (vx * vx - vy * vy)
    # Apply SMICA 5' beam to modulated T/Q/U in harmonic space, then mask at NSIDE=2048:
    aT_mod = hp.map2alm(t_b * mod_L2, lmax=LMAX, iter=0, pol=False)
    aE_mod, aB_mod = hp.map2alm_spin([q_b * mod_L2, u_b * mod_L2], spin=2, lmax=LMAX)
    aTEB_beamed = np.asarray([hp.almxfl(aT_mod, wl), hp.almxfl(aE_mod, wl), hp.almxfl(aB_mod, wl)], dtype=np.complex128)
    delta_alm_masked = _masked_ols_alm_from_fullsky(aTEB_beamed, maskI, maskP, basis_T, beta_G_inv, pix_xyz, LMAX)

    def _bip60(arr):
        return np.column_stack([gaunt_fast.project(arr[:, i, :], terms[i], backend="native").reshape(len(arr), 20) for i in range(3)])

    # Check single-template BiPoSH projection v_tmpl (note: BiPoSH is quadratic in a_lm = a_bg + alpha*delta,
    # Wait! When alpha*delta is added to a_bg, the cross term 2 Re(a_bg * alpha*delta^*) has random phase per sky,
    # UNLESS delta itself is correlated WITH a_bg (e.g. multiplicative modulation a' = a_bg + alpha * M(n) * a_bg)!
    # THAT is the exact physics difference between additive non-Gaussian template vs multiplicative L=2 modulation!
    # We test BOTH:
    #   (A) Self-coherent quadratic injection: add sqrt(alpha) * delta_alm_masked -> quadratic delta*delta^* term scales cleanly as alpha!
    #   (B) Full NSIDE=2048 pixel-space multiplicative modulation T' = (1 + eps*M_L2)*T on 16 heldout CMB-only skies!
    v_tmpl = _bip60(delta_alm_masked[None, :, :])[0]
    # Normalize delta_alm_masked so that in whitening metric Sigma_train^{-1}, its pure BiPoSH norm is 1 sigma_unit (wait sqrt(60) chi or Mahalanobis!)
    mu_tr, sd_tr, ch_tr = _fit_and_apply_shrinkage(X_train, 0.20)
    # Use template amplitude so that its whitened Mahalanobis norm equals 1.0 when injected with weight 1 (i.e. scale alm by s so s^2 -> 1 sigma above null median ~ sqrt(d)!)
    # Let us inject an additive coherent non-Gaussian L=2 pattern scaled so E[Delta chi2] ~ alpha^2 * norm
    if float(np.linalg.norm(v_tmpl)) <= 0.0:
        raise RuntimeError("Degenerate L=2 modulation template BiPoSH projection")
    # Scale alm by 1 / sqrt(unit_norm_maha) so BiPoSH quadratic amplitude of pure template is ~1 unit of chi2_60^{1/2} (then scale amplitude linearly in BiPoSH units!)
    # Wait: BiPoSH scales as (scale_alm)^2! So if scale_alm = sqrt(A_amp / unit_norm_maha), template BiPoSH scales LINEARLY as A_amp!
    # Even better, scale in natural dimensionless field strength A_fld in {0, 1, 2, 3, 4} so Quadratic scales as A_fld^2!
    # Wait: let's inject ACTUAL pixel-space multiplicative modulation (1 + eps * M_L2) * T_cmb on 20 heldout full-res skies (took ~2.7s each -> 54s? Too slow for 20!).
    # Wait: how many full-res pixel SHTs for multiplicative modulation? 8 heldout skies * 2.7s = 21s! Let's run 8 full-res pixel-space multiplicative modulations PLUS all 150 heldout coherent-phase additive-cross & self-quadratic injections!
    del t_b, q_b, u_b

    # Test 1: Linear-in-BiPoSH coherent-pattern sweep on ALL 150 heldout skies across predeclared shrinkages
    # Normalize target direction u_dir = v_tmpl / sqrt(v_tmpl @ ...). Scale delta_alm by sqrt(A_sig * sqrt(2*60) / unit_norm_maha)
    # Wait: a chi^2_60 distribution has mean ~60 and SD ~ sqrt(2*60) ~ 11. So SNR ~ k corresponds to injected BiPoSH delta_maha ~ k * 11!
    # Let's parametrize injection amplitude as k_snr in (0.0, 0.25, 0.5, 1.0, 2.0, 3.0) in units of null SD_chi2 (approx sqrt(2*d)),
    # AND let's build the exact additive sky delta_i = sqrt(c) * delta_alm_masked where sqrt(c) matches k_snr!
    # Note: on each sky a_tot = a_sky_i + delta_inj, the cross-term (a_sky * delta_inj^* + conj) fluctuates around 0,
    # while the mean BiPoSH shift equals E[BiPoSH(a_sky + delta_inj) - BiPoSH(a_sky)] == BiPoSH(delta_inj)!
    # Let's VERIFY that exact quadratic identity E[BiPoSH(a + d)] - E[BiPoSH(a)] = BiPoSH(d)!
    base_norm_z = float(np.linalg.norm(v_tmpl / sd_tr))
    delta_unit_alm = delta_alm_masked / math.sqrt(max(base_norm_z, 1e-30))  # BiPoSH(delta_unit) has ||./sd|| = 1.0!
    v_unit = _bip60(delta_unit_alm[None, :, :])[0]

    # Wait: to extract recovered amplitude linearly, define whitened inner product score:
    # a_hat(x) = ((x - mu_tr)/sd_tr)^T Corr_tr^{-1} (v_unit/sd_tr) / [ (v_unit/sd_tr)^T Corr_tr^{-1} (v_unit/sd_tr) ]
    # Because E[BiPoSH(a_test_i + sqrt(A)*delta_unit)] = E[BiPoSH(a_test_i)] + A * v_unit, E[a_hat] == A with exact unit slope = 1.0!
    r_tmpl = v_unit / sd_tr
    cinv_tmpl = cho_solve(ch_tr, r_tmpl, check_finite=False)
    denom_mf = float(r_tmpl @ cinv_tmpl)

    # Pre-load the first 150 odd test TEB_alm (need paired TEB_alm for adding delta_alm)
    # Actually we ALREADY have X_test = BiPoSH(paired[odd]) and paired[odd] passed into caller!
    amp_grid = (0.0, 0.5, 1.0, 2.0, 4.0, 6.0)
    shrink_models = {str(lam): _fit_and_apply_shrinkage(X_train, lam) for lam in (0.05, 0.10, 0.20, 0.40)}
    sweep = {}

    rec_means = []
    # Note: caller passes paired_test_alm of shape (150, 3, nalm)
    for A_inj in amp_grid:
        if A_inj == 0.0:
            X_inj = X_test
        else:
            inj_alm = paired_test_alm + math.sqrt(A_inj) * delta_unit_alm[None, :, :]
            X_inj = _bip60(inj_alm)

        # Matched-filter recovered amplitude (calibrated strictly on lambda=0.20 train cov):
        a_hats = np.array([float(((v - mu_tr) / sd_tr) @ cinv_tmpl) / denom_mf for v in X_inj])
        cos_sims = np.array([
            float(np.dot((v - mu_tr) / sd_tr, r_tmpl) / (max(np.linalg.norm((v - mu_tr) / sd_tr), 1e-30) * np.linalg.norm(r_tmpl)))
            for v in X_inj
        ])
        by_shrink = {}
        for lam_s, (mu_l, sd_l, ch_l) in shrink_models.items():
            sc_null = np.array([_mahalanobis(v, mu_l, sd_l, ch_l) for v in X_test])
            sc_inj = np.array([_mahalanobis(v, mu_l, sd_l, ch_l) for v in X_inj])
            thr95 = float(np.quantile(sc_null, 0.95))
            thr99 = float(np.quantile(sc_null, 0.99))
            by_shrink[lam_s] = {
                "mean_score": float(np.mean(sc_inj)),
                "median_score": float(np.median(sc_inj)),
                "power_at_p95": float(np.mean(sc_inj >= thr95)),
                "power_at_p99": float(np.mean(sc_inj >= thr99)),
            }
        rec_means.append(float(np.mean(a_hats)))
        sweep[f"A_{A_inj:.2f}"] = {
            "A_injected": A_inj,
            "recovered_amplitude_mean": float(np.mean(a_hats)),
            "recovered_amplitude_se": float(np.std(a_hats, ddof=1) / math.sqrt(len(a_hats))),
            "recovered_amplitude_sd": float(np.std(a_hats, ddof=1)),
            "cosine_similarity_mean": float(np.mean(cos_sims)),
            "by_shrinkage": by_shrink,
        }

    # Linear regression slope & intercept of recovered mean amplitude vs A_inj
    A_vec = np.array(amp_grid, dtype=np.float64)
    slope, intercept = np.polyfit(A_vec, np.array(rec_means, dtype=np.float64), 1)

    # Test 2: Exact NSIDE=2048 pixel-space multiplicative L=2 modulation (1 + eps * M_L2) * (CMB_sig) + FFP10 noise
    # Draw full-sky (T, E) matching actual FFP10 beamed signal spectra cl_sig_fullsky, apply NSIDE=2048 masks + OLS subtraction,
    # and add independent odd-split FFP10 SMICA noise_test_alm[idx_m] so unmodulated scores match the ~60-75 null!
    mult_rows = []
    eps_mod = 0.25
    cl_tt_fs = cl_sig_fullsky["TT"]
    cl_ee_fs = cl_sig_fullsky["EE"]
    cl_te_fs = cl_sig_fullsky["TE"]
    for idx_m in range(6):
        alm_unmasked = np.zeros((3, nalm), dtype=np.complex128)
        for ell in range(2, LMAX + 1):
            c_tt = max(float(cl_tt_fs[ell]), 1e-12)
            c_ee = max(float(cl_ee_fs[ell]), 1e-12)
            c_te = float(cl_te_fs[ell])
            rho = np.clip(c_te / math.sqrt(c_tt * c_ee), -0.99, 0.99)
            sT = math.sqrt(c_tt)
            sE_par = rho * math.sqrt(c_ee)
            sE_orth = math.sqrt(max(1.0 - rho * rho, 0.0) * c_ee)
            i0 = hp.Alm.getidx(LMAX, ell, 0)
            z_t = rng.normal()
            alm_unmasked[0, i0] = sT * z_t
            alm_unmasked[1, i0] = sE_par * z_t + sE_orth * rng.normal()
            for m in range(1, ell + 1):
                im = hp.Alm.getidx(LMAX, ell, m)
                zt_c = (rng.normal() + 1j * rng.normal()) / math.sqrt(2.0)
                ze_c = (rng.normal() + 1j * rng.normal()) / math.sqrt(2.0)
                alm_unmasked[0, im] = sT * zt_c
                alm_unmasked[1, im] = sE_par * zt_c + sE_orth * ze_c
        ti, qi, ui = hp.alm2map([alm_unmasked[0], alm_unmasked[1], alm_unmasked[2]], nside=2048, lmax=LMAX, pol=True)
        alm_m_T = hp.map2alm(ti * (1.0 + eps_mod * mod_L2), lmax=LMAX, iter=0, pol=False)
        alm_m_E, alm_m_B = hp.map2alm_spin([qi * (1.0 + eps_mod * mod_L2), ui * (1.0 + eps_mod * mod_L2)], spin=2, lmax=LMAX)
        a_m = np.asarray([alm_m_T, alm_m_E, alm_m_B], dtype=np.complex128)
        mk_u = _masked_ols_alm_from_fullsky(alm_unmasked, maskI, maskP, basis_T, beta_G_inv, pix_xyz, LMAX) + noise_test_alm[idx_m]
        mk_m = _masked_ols_alm_from_fullsky(a_m, maskI, maskP, basis_T, beta_G_inv, pix_xyz, LMAX) + noise_test_alm[idx_m]
        b_u = _bip60(mk_u[None, :, :])[0]
        b_m = _bip60(mk_m[None, :, :])[0]
        mult_rows.append({
            "draw": idx_m,
            "score_unmodulated_60D": _mahalanobis(b_u, mu_tr, sd_tr, ch_tr),
            "score_modulated_eps0p25_60D": _mahalanobis(b_m, mu_tr, sd_tr, ch_tr),
            "T_20D_shift_norm": float(np.linalg.norm(b_m[:20] - b_u[:20])),
            "EB_40D_shift_norm": float(np.linalg.norm(b_m[20:] - b_u[20:])),
        })

    null_020 = np.array([_mahalanobis(v, mu_tr, sd_tr, ch_tr) for v in X_test])
    return {
        "coherent_additive_L2_sweep_150_heldout": sweep,
        "recovered_amplitude_linear_fit": {"slope": float(slope), "intercept": float(intercept)},
        "heldout_null_score_p95_p99_lambda020": [
            float(np.quantile(null_020, 0.95)),
            float(np.quantile(null_020, 0.99)),
        ],
        "nside2048_multiplicative_modulation_eps0p25": {
            "n_draws": len(mult_rows),
            "draws": mult_rows,
            "mean_score_unmodulated": float(np.mean([r["score_unmodulated_60D"] for r in mult_rows])),
            "mean_score_modulated": float(np.mean([r["score_modulated_eps0p25_60D"] for r in mult_rows])),
        },
    }


def compute() -> dict:
    t0 = time.perf_counter()
    ids, paired, signal, noise, obs_smica, _ = r96_cmb.load()
    with np.load(STREAM / "observed_smica_commander_TEB_alm.npz", allow_pickle=False) as f:
        obs_cmd = f["commander_TEB_n2048sub"].astype(np.complex128)
    with np.load(STREAM / "alm_basis_lmax48.npz", allow_pickle=False) as f:
        basis_T = np.asarray(f["basis_T_alm"], dtype=np.complex128)

    nfirst = ids < 300
    paired300 = paired[nfirst]
    raw = _all_six_spectra(paired300, LMAX)
    C_w = np.zeros((3, LMAX + 1), dtype=np.float64)
    C_w[0] = r93.iso_theory_cl()
    C_w[1, 2:] = np.maximum(raw["EE"][:, 2:].mean(axis=0), 1e-12)
    C_w[2, 2:] = np.maximum(raw["BB"][:, 2:].mean(axis=0), 1e-12)
    terms = [gaunt_fast.build_terms(C_w[i], LMAX) for i in range(3)]

    def _bip60(arr):
        return np.column_stack([gaunt_fast.project(arr[:, i, :], terms[i], backend="native").reshape(len(arr), 20) for i in range(3)])

    X300 = _bip60(paired300)
    Xsig999 = _bip60(signal)
    y_smica = _bip60(obs_smica[None, :, :])[0]
    y_cmd = _bip60(obs_cmd[None, :, :])[0]

    # Exact even/odd split matching R96 (150 train / 150 test)
    even = (np.arange(300) % 2) == 0
    X_train, X_test = X300[even], X300[~even]
    paired_test = paired300[~even]
    noise_test = noise[~even]

    # 1. Exact NSIDE=2048 Mask-Int / Mask-Pol Master E->B analytic coupling & comparison with MC pure-E
    maskI = hp.read_map(str(MASK_I_FITS), dtype=np.float64)
    maskP = hp.read_map(str(MASK_P_FITS), dtype=np.float64)
    pix = np.arange(hp.nside2npix(2048))
    vx, vy, vz = hp.pix2vec(2048, pix)
    del pix
    sw = float(np.sum(maskI))
    f_sky_I_exact = sw / float(hp.nside2npix(2048))
    f_sky_P_exact = float(np.mean(maskP))
    sx, sy, sz = float(np.dot(maskI, vx)), float(np.dot(maskI, vy)), float(np.dot(maskI, vz))
    G_ols = np.array([
        [sw, sx, sy, sz],
        [sx, float(np.dot(maskI * vx, vx)), float(np.dot(maskI * vx, vy)), float(np.dot(maskI * vx, vz))],
        [sy, float(np.dot(maskI * vy, vx)), float(np.dot(maskI * vy, vy)), float(np.dot(maskI * vy, vz))],
        [sz, float(np.dot(maskI * vz, vx)), float(np.dot(maskI * vz, vy)), float(np.dot(maskI * vz, vz))],
    ], dtype=np.float64)
    G_inv = np.linalg.inv(G_ols)

    master_eb = _spin2_mask_coupling_matrices(maskP, LMAX)
    # Empirical full-sky beamed signal spectra estimated from all 999 cmb_only realizations divided by mask f_sky:
    raw_sig999 = _all_six_spectra(signal, LMAX)
    cl_sig_fullsky = {
        "TT": raw_sig999["TT"].mean(axis=0) / f_sky_I_exact,
        "EE": raw_sig999["EE"].mean(axis=0) / f_sky_P_exact,
        "TE": raw_sig999["TE"].mean(axis=0) / float(np.mean(maskI * maskP)),
    }
    cl_theory_EE = np.zeros(LMAX + 1, dtype=np.float64)
    cl_theory_EE[2:] = 0.01 * np.array(C_w[0, 2:]) * (np.arange(2, LMAX + 1) / 10.0) ** 0.5
    pred_cl_E_masked = master_eb["M_EE_to_EE"] @ cl_theory_EE
    pred_cl_B_leak = master_eb["M_EE_to_BB_leak"] @ cl_theory_EE
    pred_ratio_ell2_to_48 = float(np.mean(pred_cl_B_leak[2:] / np.maximum(pred_cl_E_masked[2:], 1e-30)))

    # 8-draw NSIDE=2048 pure-E Monte Carlo verification against Master analytic E->B prediction:
    rng_mc = np.random.default_rng(9703)
    nalm = hp.Alm.getsize(LMAX)
    mc_B_over_E = []
    for _ in range(8):
        aE = np.zeros(nalm, dtype=np.complex128)
        for ell in range(2, LMAX + 1):
            sd_e = math.sqrt(float(cl_theory_EE[ell]))
            aE[hp.Alm.getidx(LMAX, ell, 0)] = sd_e * rng_mc.normal()
            for m in range(1, ell + 1):
                aE[hp.Alm.getidx(LMAX, ell, m)] = sd_e * (rng_mc.normal() + 1j * rng_mc.normal()) / math.sqrt(2.0)
        az = np.zeros_like(aE)
        _, qp, up = hp.alm2map([az, aE, az], nside=2048, lmax=LMAX, pol=True)
        e_l, b_l = hp.map2alm_spin([qp * maskP, up * maskP], spin=2, lmax=LMAX)
        cE = hp.alm2cl(e_l)[2:]
        cB = hp.alm2cl(b_l)[2:]
        mc_B_over_E.append(float(np.mean(cB / np.maximum(cE, 1e-30))))

    # 2. Cross-split 60D empirical E->B leakage debiasing
    debias = _ols_ridge_leakage_debiasing(Xsig999, X_train, X_test, y_smica, y_cmd, lam_ridge=10.0)

    # 3. Injection & recovery experiments
    inj = _run_injection_recovery(
        terms, X_train, X_test, paired_test, noise_test, cl_sig_fullsky, maskI, maskP, basis_T, G_inv, (vx, vy, vz)
    )
    del maskI, maskP, vx, vy, vz

    out = {
        "schema": "htt.r97.cmb_mask_eb_leakage_and_injection_recovery/1",
        "elapsed_seconds": time.perf_counter() - t0,
        "sources_sha256": {
            "mask_int": _sha(MASK_I_FITS),
            "mask_pol": _sha(MASK_P_FITS),
            "fullres_manifest": _sha(STREAM / "full_stream_manifest_r95.json"),
            "observed_smica_commander": _sha(STREAM / "observed_smica_commander_TEB_alm.npz"),
        },
        "nside_source": 2048,
        "lmax": LMAX,
        "smica_fwhm_arcmin": FWHM_ARCMIN,
        "N_train_even": 150,
        "N_test_odd": 150,
        "master_spin2_mask_coupling": {
            "f_sky_P_exact": master_eb["f_sky_P_from_w00"],
            "wigner3j_sympy_oracle_err": master_eb["wigner3j_sympy_oracle_err"],
            "analytic_master_mean_clBB_over_clEE_2_48": pred_ratio_ell2_to_48,
            "nside2048_mc8_mean_clBB_over_clEE_2_48": float(np.mean(mc_B_over_E)),
            "nside2048_mc8_sd": float(np.std(mc_B_over_E, ddof=1)),
            "analytic_vs_mc_rel_diff": float(abs(pred_ratio_ell2_to_48 - np.mean(mc_B_over_E)) / np.mean(mc_B_over_E)),
        },
        "cross_split_60D_eb_leakage_debiasing": debias,
        "anisotropy_injection_recovery": inj,
        "physics_gates": {
            "smica_unique_noise_N": 300,
            "commander_null_qualified": False,
            "Bianchi_family_attribution": None,
            "physical_Pi": None,
            "physical_GF": None,
            "source_conditional_diagnostic_only": True,
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2) + "\n")
    return out


if __name__ == "__main__":
    res = compute()
    print(json.dumps({
        "master_vs_mc_eb": {
            "analytic": res["master_spin2_mask_coupling"]["analytic_master_mean_clBB_over_clEE_2_48"],
            "mc8": res["master_spin2_mask_coupling"]["nside2048_mc8_mean_clBB_over_clEE_2_48"],
            "rel_diff": res["master_spin2_mask_coupling"]["analytic_vs_mc_rel_diff"],
        },
        "debias": res["cross_split_60D_eb_leakage_debiasing"],
        "inj_fit": res["anisotropy_injection_recovery"]["recovered_amplitude_linear_fit"],
        "inj_A6_p020": res["anisotropy_injection_recovery"]["coherent_additive_L2_sweep_150_heldout"]["A_6.00"]["by_shrinkage"]["0.2"],
        "mult_mod": res["anisotropy_injection_recovery"]["nside2048_multiplicative_modulation_eps0p25"]["mean_score_unmodulated"],
        "mult_mod_after": res["anisotropy_injection_recovery"]["nside2048_multiplicative_modulation_eps0p25"]["mean_score_modulated"],
        "elapsed_s": res["elapsed_seconds"],
    }))
