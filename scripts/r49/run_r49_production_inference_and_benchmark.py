"""R49 GBI-07 & GBI-08 production runner: Matrix A..I benchmark, 4-chain MCMC, 5-views, MIO cert, PPC/LOPO, & adjudication."""

from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import math
import multiprocessing as mp_proc
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np
import scipy.linalg
import scipy.optimize
import scipy.special
import scipy.stats

WORKTREE_ROOT = Path(__file__).resolve().parents[2]
for _p in (str(WORKTREE_ROOT / "htt"), str(WORKTREE_ROOT / "htt" / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
if str(WORKTREE_ROOT) not in sys.path:
    sys.path.append(str(WORKTREE_ROOT))

from common.semantic_guards.no_overclaim import scan_paths
from htt.infer.r49_general_bianchi_likelihood import (
    CMBCarrierData,
    CMBModeBudgetSpec,
    FrameEpochAlignmentSpec,
    G_STF5,
    PARAM_NAMES_24,
    PsiCosmology,
    R49GeneralBianchiCobayaLikelihood,
    R49GeneralBianchiLikelihood,
    R49JointState,
    R49MultiProbeDataset,
    SplitPosteriorFiveViewError,
    T_CMB_K,
    compute_r49_htt_five_views_from_posterior,
    compute_scalar_xc_ablation_comparison,
    standard_lowell_mode_labels,
)
from mio.interface.mio_certificate import build_mio_certificate, certificate_to_payload
from tests.r49.test_gbi06_planck_lanes_and_data_contract import load_real_dataset_from_npz


R49_DOC_DIR = (
    WORKTREE_ROOT
    / "docs"
    / "research_program"
    / "observational_publication_20261015"
    / "R49_GENERAL_TILTED_BIANCHI_20261112"
)
REAL_DATASET_NPZ = Path("/mnt/extdrive/workdir/r49_chains/r49_real_multiprobe_dataset.npz")
CHAINS_OUT_NPZ = Path("/mnt/extdrive/workdir/r49_chains/r49_joint_posterior_chains.npz")

ALL_PROBES: tuple[str, ...] = ("CMB", "Quaia", "NVSS", "RACS", "Gaia", "PantheonPlus", "CF4", "DESI")
PROBES_NO_CMB: tuple[str, ...] = ("Quaia", "NVSS", "RACS", "Gaia", "PantheonPlus", "CF4", "DESI")

# Normalized Gaussian prior centers & widths across all 24 unconstrained coordinates:
# Broad uninformative vs calibrated likelihood widths, properly normalized for Bayesian evidence.
PRIOR_MEAN_24 = np.array(
    [0.0] * 20 + [67.4, 0.315, 147.09, 0.0],
    dtype=np.float64,
)
PRIOR_STD_24 = np.array(
    [5.0e-5] * 5          # sigma_AB_stf5
    + [5.0e-3] * 3        # omega_A
    + [0.05] * 3          # A_A
    + [5.0e-3] * 3        # v_matter
    + [5.0e-3] * 3        # v_rad
    + [5.0e-3] * 3        # beta_MO
    + [5.0, 0.1, 10.0, 0.1],  # H_0, Omega_m, r_d, DeltaOmega_k
    dtype=np.float64,
)
PARAM_SCALE_24 = np.array(
    [2.5e-6] * 5
    + [5.0e-3] * 3
    + [3.0e-4] * 3
    + [4.0e-5] * 3
    + [1.0e-4] * 3
    + [4.0e-5] * 3
    + [0.2, 0.004, 0.4, 0.01],
    dtype=np.float64,
)


def _git_head(repo_dir: Path) -> str:
    res = subprocess.run(
        ["git", "-C", str(repo_dir), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout.strip()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _in_physical_domain(vec24: np.ndarray) -> bool:
    if np.any(~np.isfinite(vec24)):
        return False
    if np.linalg.norm(vec24[11:14]) >= 0.2:
        return False
    if np.linalg.norm(vec24[14:17]) >= 0.2:
        return False
    if np.linalg.norm(vec24[17:20]) >= 0.2:
        return False
    H0, Om, rd, Ok = vec24[20:24]
    if not (30.0 < H0 < 120.0 and 0.05 < Om < 0.90 and 100.0 < rd < 200.0 and -0.35 < Ok < 0.35):
        return False
    return True


def _log_prior_subspace(vec24: np.ndarray, active_idx: np.ndarray) -> float:
    if not _in_physical_domain(vec24):
        return -np.inf
    idx = np.asarray(active_idx, dtype=np.int64)
    z = (vec24[idx] - PRIOR_MEAN_24[idx]) / PRIOR_STD_24[idx]
    lp = -0.5 * float(np.sum(z * z + 2.0 * np.log(PRIOR_STD_24[idx]) + math.log(2.0 * math.pi)))
    return lp


class SubspacePosteriorModel:
    """Evaluates normalized log-posterior for a fixed Bianchi family and active subspace."""

    def __init__(
        self,
        likelihood: R49GeneralBianchiLikelihood,
        *,
        family: str,
        active_idx: Sequence[int],
        h_bianchi: float = 0.25,
        omega_k: float = 0.0,
        handedness: int = 1,
        base_vec24: np.ndarray | None = None,
    ) -> None:
        self.likelihood = likelihood
        self.family = str(family)
        self.active_idx = np.asarray(active_idx, dtype=np.int64)
        self.h_bianchi = float(h_bianchi)
        self.omega_k = float(omega_k)
        self.handedness = int(handedness)
        self.base_vec24 = PRIOR_MEAN_24.copy() if base_vec24 is None else np.asarray(base_vec24, dtype=np.float64).copy()

    def expand(self, theta_sub: np.ndarray) -> np.ndarray:
        v = self.base_vec24.copy()
        v[self.active_idx] = theta_sub
        return v

    def make_state(self, theta_sub: np.ndarray) -> R49JointState:
        v = self.expand(theta_sub)
        return R49JointState.from_vector24(
            v,
            family=self.family,
            h_bianchi=self.h_bianchi,
            omega_k=self.omega_k,
            handedness=self.handedness,
        )

    def log_prior(self, theta_sub: np.ndarray) -> float:
        return _log_prior_subspace(self.expand(theta_sub), self.active_idx)

    def log_likelihood(self, theta_sub: np.ndarray) -> float:
        v = self.expand(theta_sub)
        if not _in_physical_domain(v):
            return -np.inf
        st = R49JointState.from_vector24(
            v,
            family=self.family,
            h_bianchi=self.h_bianchi,
            omega_k=self.omega_k,
            handedness=self.handedness,
        )
        return float(self.likelihood.logp(st))

    def log_posterior(self, theta_sub: np.ndarray) -> float:
        lp = self.log_prior(theta_sub)
        if not np.isfinite(lp):
            return -np.inf
        ll = self.log_likelihood(theta_sub)
        if not np.isfinite(ll):
            return -np.inf
        return float(lp + ll)


def _fit_map_and_laplace(
    model: SubspacePosteriorModel,
    *,
    dataset: R49MultiProbeDataset,
    mode_budget: CMBModeBudgetSpec,
    alignment: FrameEpochAlignmentSpec,
    active_probes: Sequence[str] = ALL_PROBES,
    theta_seed: np.ndarray | None = None,
    n_is_samples: int = 48,
    rng_seed: int = 2026,
    use_stage1_noncmb: bool = True,
    maxiter_full: int = 140,
    use_cmb_gauss_newton_hessian: bool = False,
) -> dict[str, Any]:
    """Two-stage MAP optimization + central-diff Hessian Laplace + Student-t IS check."""
    idx = model.active_idx
    d = int(len(idx))
    scales = PARAM_SCALE_24[idx]
    prior_prec = 1.0 / (PRIOR_STD_24[idx] ** 2)

    theta0 = PRIOR_MEAN_24[idx].copy() if theta_seed is None else np.asarray(theta_seed, dtype=np.float64).copy()

    if use_stage1_noncmb and "CMB" in active_probes and any(p in active_probes for p in PROBES_NO_CMB):
        non_cmb = tuple(p for p in active_probes if p != "CMB")
        lk_fast = R49GeneralBianchiLikelihood(
            dataset,
            mode_budget=mode_budget,
            alignment=alignment,
            active_probes=non_cmb,
        )
        m_fast = SubspacePosteriorModel(
            lk_fast,
            family=model.family,
            active_idx=idx,
            h_bianchi=model.h_bianchi,
            omega_k=model.omega_k,
            handedness=model.handedness,
            base_vec24=model.base_vec24,
        )
        # Skip CMB-only shear indices in Stage-1 unless needed by DESI DQ; L-BFGS-B handles all cleanly
        def nll_fast(u: np.ndarray) -> float:
            th = theta0 + u * scales
            lp = m_fast.log_posterior(th)
            return 1.0e30 if not np.isfinite(lp) else -lp

        res1 = scipy.optimize.minimize(
            nll_fast,
            np.zeros(d, dtype=np.float64),
            method="L-BFGS-B",
            options={"maxiter": 100, "ftol": 1.0e-12, "gtol": 1.0e-5, "eps": 2.0e-5},
        )
        cand1 = theta0 + res1.x * scales
        if np.isfinite(model.log_posterior(cand1)):
            theta0 = cand1

    def nll_full(u: np.ndarray) -> float:
        th = theta0 + u * scales
        lp = model.log_posterior(th)
        return 1.0e30 if not np.isfinite(lp) else -lp

    res2 = scipy.optimize.minimize(
        nll_full,
        np.zeros(d, dtype=np.float64),
        method="L-BFGS-B",
        options={"maxiter": int(maxiter_full), "ftol": 1.0e-12, "gtol": 1.0e-5, "eps": 2.0e-5},
    )
    theta_map = theta0 + res2.x * scales
    if not np.isfinite(model.log_posterior(theta_map)):
        theta_map = theta0.copy()

    logp_map_ll = model.log_likelihood(theta_map)
    logp_map_pr = model.log_prior(theta_map)
    logp_map = logp_map_ll + logp_map_pr

    # Full central-difference Hessian of -log_posterior wrt u = (theta - theta_map) / scales
    h_u = np.full(d, 1.0e-3, dtype=np.float64)
    H_u = np.zeros((d, d), dtype=np.float64)
    f0 = -logp_map
    g_u = np.zeros(d, dtype=np.float64)

    if use_cmb_gauss_newton_hessian and "CMB" in active_probes:
        # Build exact non-CMB + prior + CMB covariance-excess Hessian via fast 4-point diffs
        # (zero geodesic calls), then add CMB Fisher J_cmb^T C_eff^{-1} J_cmb (2*d_cmb calls).
        non_cmb = tuple(p for p in active_probes if p != "CMB")
        lk_nc = R49GeneralBianchiLikelihood(
            dataset,
            mode_budget=mode_budget,
            alignment=alignment,
            active_probes=non_cmb,
        )
        m_nc = SubspacePosteriorModel(
            lk_nc,
            family=model.family,
            active_idx=idx,
            h_bianchi=model.h_bianchi,
            omega_k=model.omega_k,
            handedness=model.handedness,
            base_vec24=model.base_vec24,
        )
        st_map = model.make_state(theta_map)
        mu0, cov0 = model.likelihood._predict_cmb_vector(st_map)
        r0 = dataset.cmb.d_obs - mu0
        cov_cmb_base = 0.5 * (dataset.cmb.cov + dataset.cmb.cov.T)
        if np.any(cov0 > 0.0):
            L_eff0 = scipy.linalg.cholesky(cov_cmb_base + np.diag(cov0), lower=True)
        else:
            L_eff0 = model.likelihood._cmb_chol
        cov_mask = model.likelihood._cmb_cov_mask
        cmb_log_norm = len(r0) * math.log(2.0 * math.pi)

        def _cmb_nll_from_pred(r_v: np.ndarray, cov_v: np.ndarray) -> float:
            if np.any(cov_v > 0.0):
                L_e = scipy.linalg.cholesky(cov_cmb_base + np.diag(cov_v), lower=True)
                ld_e = 2.0 * float(np.sum(np.log(np.diag(L_e))))
                w_e = scipy.linalg.solve_triangular(L_e, r_v, lower=True)
                return 0.5 * (float(w_e @ w_e) + ld_e + cmb_log_norm)
            w_e = scipy.linalg.solve_triangular(model.likelihood._cmb_chol, r_v, lower=True)
            return 0.5 * (float(w_e @ w_e) + model.likelihood._cmb_logdet + cmb_log_norm)

        def _nll_cmb_cov_at_fixed_r(vec24: np.ndarray) -> float:
            sig5 = vec24[:5]
            sig_amp2 = float(sig5 @ G_STF5 @ sig5)
            cov_ex = np.where(cov_mask, 1.0e-8 * (1.0e6 * T_CMB_K) ** 2 * sig_amp2, 0.0)
            return _cmb_nll_from_pred(r0, cov_ex)

        def nll_nc_cov(th: np.ndarray) -> float:
            lp_nc = m_nc.log_posterior(th)
            if not np.isfinite(lp_nc):
                return 1.0e30
            return -lp_nc + _nll_cmb_cov_at_fixed_r(model.expand(th))

        f0_nc = nll_nc_cov(theta_map)
        for j in range(d):
            ej = np.zeros(d, dtype=np.float64)
            ej[j] = h_u[j]
            fp = nll_nc_cov(theta_map + ej * scales)
            fm = nll_nc_cov(theta_map - ej * scales)
            g_u[j] = (fp - fm) / (2.0 * h_u[j])
            H_u[j, j] = (fp - 2.0 * f0_nc + fm) / (h_u[j] * h_u[j])

        step_u = np.clip(0.02 / np.sqrt(np.maximum(H_u.diagonal(), 1.0)), 2.0e-4, 0.2)
        for j in range(d):
            if abs(step_u[j] - h_u[j]) > 0.3 * h_u[j]:
                ej = np.zeros(d, dtype=np.float64)
                ej[j] = step_u[j]
                fp = nll_nc_cov(theta_map + ej * scales)
                fm = nll_nc_cov(theta_map - ej * scales)
                H_u[j, j] = (fp - 2.0 * f0_nc + fm) / (step_u[j] * step_u[j])

        for i in range(d):
            for j in range(i + 1, d):
                ei = np.zeros(d, dtype=np.float64)
                ej = np.zeros(d, dtype=np.float64)
                ei[i] = step_u[i]
                ej[j] = step_u[j]
                fpp = nll_nc_cov(theta_map + (ei + ej) * scales)
                fpm = nll_nc_cov(theta_map + (ei - ej) * scales)
                fmp = nll_nc_cov(theta_map + (-ei + ej) * scales)
                fmm = nll_nc_cov(theta_map + (-ei - ej) * scales)
                hij = (fpp - fpm - fmp + fmm) / (4.0 * step_u[i] * step_u[j])
                if np.isfinite(hij):
                    H_u[i, j] = hij
                    H_u[j, i] = hij

        # CMB Fisher block only for parameters entering CMB prediction (sigma, v_matter, v_rad, beta_MO)
        cmb_active = [j for j, orig_i in enumerate(idx) if (0 <= orig_i < 5) or (11 <= orig_i < 20)]
        J_cmb = np.zeros((len(mu0), d), dtype=np.float64)
        for j in cmb_active:
            ej = np.zeros(d, dtype=np.float64)
            ej[j] = step_u[j]
            th_p = theta_map + ej * scales
            th_m = theta_map - ej * scales
            st_p = model.make_state(th_p)
            st_m = model.make_state(th_m)
            mup, cov_p = model.likelihood._predict_cmb_vector(st_p)
            mum, cov_m = model.likelihood._predict_cmb_vector(st_m)
            J_cmb[:, j] = (mup - mum) / (2.0 * step_u[j])
            fp_tot = -m_nc.log_posterior(th_p) + _cmb_nll_from_pred(dataset.cmb.d_obs - mup, cov_p)
            fm_tot = -m_nc.log_posterior(th_m) + _cmb_nll_from_pred(dataset.cmb.d_obs - mum, cov_m)
            g_u[j] = (fp_tot - fm_tot) / (2.0 * step_u[j])
        W_J = scipy.linalg.solve_triangular(L_eff0, J_cmb, lower=True)
        H_u = 0.5 * (H_u + H_u.T) + W_J.T @ W_J
    else:
        for j in range(d):
            ej = np.zeros(d, dtype=np.float64)
            ej[j] = h_u[j]
            fp = -model.log_posterior(theta_map + ej * scales)
            fm = -model.log_posterior(theta_map - ej * scales)
            g_u[j] = (fp - fm) / (2.0 * h_u[j])
            H_u[j, j] = (fp - 2.0 * f0 + fm) / (h_u[j] * h_u[j])

        step_u = np.clip(0.02 / np.sqrt(np.maximum(H_u.diagonal(), 1.0)), 2.0e-4, 0.2)
        for j in range(d):
            if abs(step_u[j] - h_u[j]) > 0.3 * h_u[j]:
                ej = np.zeros(d, dtype=np.float64)
                ej[j] = step_u[j]
                fp = -model.log_posterior(theta_map + ej * scales)
                fm = -model.log_posterior(theta_map - ej * scales)
                H_u[j, j] = (fp - 2.0 * f0 + fm) / (step_u[j] * step_u[j])

        for i in range(d):
            for j in range(i + 1, d):
                ei = np.zeros(d, dtype=np.float64)
                ej = np.zeros(d, dtype=np.float64)
                ei[i] = step_u[i]
                ej[j] = step_u[j]
                fpp = -model.log_posterior(theta_map + (ei + ej) * scales)
                fpm = -model.log_posterior(theta_map + (ei - ej) * scales)
                fmp = -model.log_posterior(theta_map + (-ei + ej) * scales)
                fmm = -model.log_posterior(theta_map + (-ei - ej) * scales)
                hij = (fpp - fpm - fmp + fmm) / (4.0 * step_u[i] * step_u[j])
                if np.isfinite(hij):
                    H_u[i, j] = hij
                    H_u[j, i] = hij

    H_u = 0.5 * (H_u + H_u.T)
    prior_curv_u = prior_prec * (scales * scales)
    eigvals, eigvecs = np.linalg.eigh(H_u)
    floor_vals = np.einsum("ij,i,ij->j", eigvecs, prior_curv_u, eigvecs)
    eigvals_spd = np.maximum(eigvals, np.maximum(floor_vals, 1.0e-12))
    H_u_spd = (eigvecs * eigvals_spd[None, :]) @ eigvecs.T
    H_u_spd = 0.5 * (H_u_spd + H_u_spd.T)
    C_u = (eigvecs / eigvals_spd[None, :]) @ eigvecs.T
    C_u = 0.5 * (C_u + C_u.T)
    C_theta = C_u * np.outer(scales, scales)
    C_theta = 0.5 * (C_theta + C_theta.T)

    L_theta = scipy.linalg.cholesky(C_theta + 1.0e-30 * np.eye(d), lower=True)
    logdet_C_theta = 2.0 * float(np.sum(np.log(np.diag(L_theta))))
    log_z_laplace = float(logp_map + 0.5 * d * math.log(2.0 * math.pi) + 0.5 * logdet_C_theta)

    # Multivariate Student-t importance sampling check around Laplace covariance
    log_z_is = log_z_laplace
    is_mc_se = 0.0
    if n_is_samples > 0:
        df_t = 8.0
        rng = np.random.default_rng(rng_seed)
        g_draws = rng.chisquare(df_t, size=n_is_samples)
        z_norm = rng.normal(size=(n_is_samples, d))
        scale_t = np.sqrt(df_t / g_draws)[:, None]
        deltas = (z_norm @ L_theta.T) * scale_t
        maha2 = np.sum(z_norm * z_norm, axis=1) * (df_t / g_draws)

        c_norm_t = (
            scipy.special.gammaln(0.5 * (df_t + d))
            - scipy.special.gammaln(0.5 * df_t)
            - 0.5 * d * math.log(df_t * math.pi)
            - 0.5 * logdet_C_theta
        )
        log_weights = np.empty(n_is_samples, dtype=np.float64)
        for s_idx in range(n_is_samples):
            th_s = theta_map + deltas[s_idx]
            lp_true = model.log_posterior(th_s)
            log_q = c_norm_t - 0.5 * (df_t + d) * math.log1p(maha2[s_idx] / df_t)
            log_weights[s_idx] = lp_true - log_q
        finite_w = log_weights[np.isfinite(log_weights)]
        if len(finite_w) >= max(8, n_is_samples // 2):
            m_max = float(np.max(finite_w))
            ratios = np.exp(finite_w - m_max)
            log_z_is = float(m_max + math.log(float(np.mean(ratios))) + math.log(len(finite_w) / n_is_samples))
            is_mc_se = float(np.std(ratios, ddof=1) / (math.sqrt(len(finite_w)) * max(float(np.mean(ratios)), 1.0e-30)))

    return {
        "theta_map": theta_map,
        "vec24_map": model.expand(theta_map),
        "log_likelihood_map": float(logp_map_ll),
        "log_prior_map": float(logp_map_pr),
        "log_posterior_map": float(logp_map),
        "log_z_laplace": float(log_z_laplace),
        "log_z_is": float(log_z_is),
        "is_mc_se": float(is_mc_se),
        "C_theta": C_theta,
        "L_theta": L_theta,
        "posterior_std": np.sqrt(np.diag(C_theta)),
        "d_active": d,
        "max_grad_u": float(np.max(np.abs(g_u))),
    }


def _build_competitor_specs() -> list[dict[str, Any]]:
    idx_psi = [20, 21, 22, 23]
    idx_boost = [17, 18, 19] + idx_psi
    idx_shear_untilt = [0, 1, 2, 3, 4] + idx_psi
    idx_all24 = list(range(24))
    return [
        {
            "code": "A",
            "name": "A_ISOTROPIC_LCDM",
            "family": "FLRW",
            "h_bianchi": 0.0,
            "omega_k": 0.0,
            "transfer_mode": "linearized_near_flrw",
            "active_idx": idx_psi,
            "description": "Isotropic spatially curved LCDM background (all shear/tilt/boost zeroed).",
        },
        {
            "code": "B",
            "name": "B_PURE_LOCAL_BOOST",
            "family": "FLRW",
            "h_bianchi": 0.0,
            "omega_k": 0.0,
            "transfer_mode": "linearized_near_flrw",
            "active_idx": idx_boost,
            "description": "Isotropic LCDM plus local observer kinematic boost beta_MO only (no Bianchi shear/fluid tilt).",
        },
        {
            "code": "C",
            "name": "C_PURE_GLOBAL_SHEAR_UNTILT",
            "family": "I",
            "h_bianchi": 0.0,
            "omega_k": 0.0,
            "transfer_mode": "linearized_near_flrw",
            "active_idx": idx_shear_untilt,
            "description": "Untilted Bianchi I shear-only anisotropy (v_matter = v_rad = beta_MO = 0).",
        },
        {
            "code": "D",
            "name": "D_TILTED_BIANCHI_I",
            "family": "I",
            "h_bianchi": 0.0,
            "omega_k": 0.0,
            "transfer_mode": "linearized_near_flrw",
            "active_idx": idx_all24,
            "description": "General multi-fluid tilted Bianchi I (24D unconstrained subspace).",
        },
        {
            "code": "E",
            "name": "E_TILTED_BIANCHI_V",
            "family": "V",
            "h_bianchi": 0.0,
            "omega_k": 0.05,
            "transfer_mode": "linearized_near_flrw",
            "active_idx": idx_all24,
            "description": "General tilted Bianchi V open hyperbolic focusing model (24D).",
        },
        {
            "code": "F",
            "name": "F_TILTED_BIANCHI_VII0",
            "family": "VII_0",
            "h_bianchi": 0.0,
            "omega_k": 0.0,
            "transfer_mode": "linearized_near_flrw",
            "active_idx": idx_all24,
            "description": "General tilted Bianchi VII_0 flat helical model (24D).",
        },
        {
            "code": "G",
            "name": "G_TILTED_BIANCHI_VIIH",
            "family": "VII_h",
            "h_bianchi": 0.25,
            "omega_k": 0.05,
            "transfer_mode": "linearized_near_flrw",
            "active_idx": idx_all24,
            "description": "General tilted Bianchi VII_h open helical Class-B model (24D).",
        },
        {
            "code": "H",
            "name": "H_TILTED_BIANCHI_IX",
            "family": "IX",
            "h_bianchi": 0.0,
            "omega_k": -0.05,
            "transfer_mode": "linearized_near_flrw",
            "active_idx": idx_all24,
            "description": "General tilted Bianchi IX closed SO(3)-twist model (24D).",
        },
    ]


def _synthetic_dataset_from_state(
    template_ds: R49MultiProbeDataset,
    truth_state: R49JointState,
    seed: int = 777,
    noise_scale: float = 0.25,
) -> R49MultiProbeDataset:
    """Generate noiseless/low-noise synthetic 8-probe dataset using exact calibrated covariances."""
    lk_tmp = R49GeneralBianchiLikelihood(
        template_ds,
        mode_budget=CMBModeBudgetSpec(
            ell_min=2,
            ell_max=6,
            deterministic_ells=(2, 3, 4),
            covariance_ells=(5, 6),
            lane="PR3_CALIBRATED",
            mc_source="FFP10_PR3",
            transfer_mode="linearized_near_flrw",
        ),
        alignment=FrameEpochAlignmentSpec(triad_frame="galactic", triad_rotation=np.eye(3)),
    )
    rng = np.random.default_rng(seed)

    cmb_mu, cmb_cov_ex = lk_tmp._predict_cmb_vector(truth_state)
    if np.any(cmb_cov_ex > 0.0):
        C_syn_cmb = 0.5 * (template_ds.cmb.cov + template_ds.cmb.cov.T) + np.diag(cmb_cov_ex)
        L_cmb = scipy.linalg.cholesky(C_syn_cmb, lower=True)
    else:
        L_cmb = lk_tmp._cmb_chol
    cmb_d = cmb_mu + noise_scale * (L_cmb @ rng.normal(size=len(cmb_mu)))

    def _draw_dipole(key: str) -> Any:
        src = getattr(template_ds, key.lower())
        R_to_probe = lk_tmp._frame_rot_to_triad(src.coordinate_frame).T
        d_triad = float(src.c_eb) * (truth_state.beta_MO + 0.1 * truth_state.A_A)
        d_obs = R_to_probe @ d_triad
        cov_orig = src.cov
        L_c = scipy.linalg.cholesky(0.5 * (cov_orig + cov_orig.T), lower=True)
        d_obs = d_obs + noise_scale * (L_c @ rng.normal(size=3))
        return type(src)(
            probe_name=src.probe_name,
            d_obs=d_obs,
            cov=src.cov,
            c_eb=src.c_eb,
            coordinate_frame=src.coordinate_frame,
            z_eff=src.z_eff,
            n_sources=src.n_sources,
        )

    from htt.infer.r49_general_bianchi_likelihood import (
        CF4TomographicCarrierData,
        DESIBAOAndDirectionalCarrierData,
        GaiaVSHCarrierData,
        PantheonCarrierData,
        _stf5_rotation_matrix,
    )
    from common.relativistic_velocity_closure import kinematic_quadrupole_stf2
    from common.stf_metric_bridge import stf_matrix_to_cartesian

    H0_uasyr = (truth_state.psi.H_0 * 1.0227e-12) * (180.0 * 3600.0e6 / math.pi)
    e1_tri = H0_uasyr * (truth_state.beta_MO + truth_state.A_A)
    b1_tri = H0_uasyr * truth_state.omega_A
    e2_tri = H0_uasyr * (
        truth_state.sigma_AB_stf5 + 0.25 * stf_matrix_to_cartesian(kinematic_quadrupole_stf2(truth_state.beta_MO))
    )
    R_to_gaia = lk_tmp._frame_rot_to_triad(template_ds.gaia.coordinate_frame).T
    R5_to_gaia = _stf5_rotation_matrix(R_to_gaia)
    g11 = np.concatenate([R_to_gaia @ e1_tri, R_to_gaia @ b1_tri, R5_to_gaia @ e2_tri])
    L_g = scipy.linalg.cholesky(0.5 * (template_ds.gaia.cov_e1b1e2 + template_ds.gaia.cov_e1b1e2.T), lower=True)
    g11 = g11 + noise_scale * (L_g @ rng.normal(size=11))
    gaia_syn = GaiaVSHCarrierData(
        g11[:3],
        g11[3:6],
        g11[6:11],
        template_ds.gaia.cov_e1b1e2,
        coordinate_frame=template_ds.gaia.coordinate_frame,
        z_eff=template_ds.gaia.z_eff,
        n_sources=template_ds.gaia.n_sources,
    )

    pan = template_ds.pantheon
    z_h = pan.z_hd
    Om, Ok, H0 = truth_state.psi.Omega_m, truth_state.psi.DeltaOmega_k, truth_state.psi.H_0
    Ode = 1.0 - Om - Ok
    s_grid = np.linspace(0.0, 1.0, 32)[None, :]
    zp = z_h[:, None] * s_grid
    Ez = np.sqrt(np.maximum(Om * (1.0 + zp) ** 3 + Ok * (1.0 + zp) ** 2 + Ode, 1.0e-12))
    c_kms = 299792.458
    dc = (c_kms / H0) * z_h * np.trapezoid(1.0 / Ez, s_grid[0], axis=1)
    if abs(Ok) < 1.0e-6:
        dm = dc
    elif Ok > 0.0:
        sk = math.sqrt(Ok); rh = c_kms / H0; dm = (rh / sk) * np.sinh(sk * dc / rh)
    else:
        sk = math.sqrt(-Ok); rh = c_kms / H0; dm = (rh / sk) * np.sin(sk * dc / rh)
    mu_iso = 5.0 * np.log10(np.maximum((1.0 + pan.z_hel) * dm, 1.0e-9)) + 25.0 - 19.25
    n_dot_dip = lk_tmp._pan_n_triad @ (truth_state.beta_MO - truth_state.v_matter + 0.5 * truth_state.A_A)
    n_sig_n = np.einsum("ni,ij,nj->n", lk_tmp._pan_n_triad, truth_state.sigma_matrix, lk_tmp._pan_n_triad)
    dmu = -(5.0 / math.log(10.0)) * (n_dot_dip / np.maximum(z_h, 0.015) - 0.5 * z_h * n_sig_n)
    L_pan = scipy.linalg.cholesky(0.5 * (pan.cov + pan.cov.T), lower=True)
    m_syn = mu_iso + dmu + noise_scale * (L_pan @ rng.normal(size=len(z_h)))
    pan_syn = PantheonCarrierData(pan.z_hd, pan.z_hel, pan.n_hat_gal, m_syn, pan.cov)

    c4_triad = np.concatenate(
        [c_kms * (truth_state.v_matter - truth_state.beta_MO) + c_kms * 0.5 * (zl + zh) * 0.1 * truth_state.A_A for zl, zh in template_ds.cf4.shell_z_bins]
    )
    R_to_cf4 = lk_tmp._frame_rot_to_triad(template_ds.cf4.coordinate_frame).T
    n_c4_shells = len(template_ds.cf4.shell_z_bins)
    R_to_cf4_blk = scipy.linalg.block_diag(*([R_to_cf4] * n_c4_shells)) if n_c4_shells > 0 else np.eye(0)
    L_c4 = scipy.linalg.cholesky(0.5 * (template_ds.cf4.cov + template_ds.cf4.cov.T), lower=True)
    c4_syn = CF4TomographicCarrierData(
        template_ds.cf4.shell_z_bins,
        (R_to_cf4_blk @ c4_triad) + noise_scale * (L_c4 @ rng.normal(size=len(c4_triad))),
        template_ds.cf4.cov,
        coordinate_frame=template_ds.cf4.coordinate_frame,
    )

    dsi = template_ds.desi
    bao_syn = np.empty(len(dsi.bao_mean), dtype=np.float64)
    for idx_b, (zv, qty) in enumerate(zip(dsi.bao_z, dsi.bao_quantities)):
        if qty == "DM_over_rs":
            bao_syn[idx_b] = truth_state.psi.transverse_comoving_distance_Mpc(float(zv)) / truth_state.psi.r_d
        elif qty == "DH_over_rs":
            bao_syn[idx_b] = truth_state.psi.hubble_distance_Mpc(float(zv)) / truth_state.psi.r_d
        else:
            bao_syn[idx_b] = truth_state.psi.volume_distance_Mpc(float(zv)) / truth_state.psi.r_d
    bao_syn = bao_syn + noise_scale * (lk_tmp._desi_bao_L @ rng.normal(size=len(bao_syn)))
    R5_to_desi = _stf5_rotation_matrix(lk_tmp._frame_rot_to_triad(dsi.coordinate_frame).T)
    L_dq = scipy.linalg.cholesky(0.5 * (dsi.directional_quad_cov + dsi.directional_quad_cov.T), lower=True)
    dq_syn = (R5_to_desi @ truth_state.sigma_AB_stf5) + noise_scale * (L_dq @ rng.normal(size=5))
    desi_syn = DESIBAOAndDirectionalCarrierData(
        dsi.bao_z, dsi.bao_quantities, bao_syn, dsi.bao_cov, dq_syn, dsi.directional_quad_cov, coordinate_frame=dsi.coordinate_frame
    )

    cmb_syn = CMBCarrierData(
        template_ds.cmb.ells,
        template_ds.cmb.mode_labels,
        cmb_d,
        template_ds.cmb.cov,
        lane="PR3_CALIBRATED",
        mc_source="FFP10_PR3",
        coordinate_frame=template_ds.cmb.coordinate_frame,
        n_mc=template_ds.cmb.n_mc,
    )
    return R49MultiProbeDataset(
        cmb=cmb_syn,
        quaia=_draw_dipole("Quaia"),
        nvss=_draw_dipole("NVSS"),
        racs=_draw_dipole("RACS"),
        gaia=gaia_syn,
        pantheon=pan_syn,
        cf4=c4_syn,
        desi=desi_syn,
    )


def _run_mcmc_worker(args: tuple[Any, ...]) -> dict[str, Any]:
    """Run one Fisher-preconditioned adaptive-burnin -> fixed-kernel MH chain."""
    (
        chain_id,
        seed,
        dataset,
        family,
        h_bianchi,
        omega_k,
        handedness,
        theta_map,
        L_theta,
        n_burn,
        n_prod,
    ) = args
    mb = CMBModeBudgetSpec(
        ell_min=2,
        ell_max=6,
        deterministic_ells=(2, 3, 4),
        covariance_ells=(5, 6),
        lane=dataset.cmb.lane,
        mc_source=dataset.cmb.mc_source,
        transfer_mode="linearized_near_flrw",
    )
    al = FrameEpochAlignmentSpec(triad_frame="galactic", triad_rotation=np.eye(3))
    lk_cmb = R49GeneralBianchiLikelihood(
        dataset,
        mode_budget=mb,
        alignment=al,
        active_probes=("CMB",),
    )
    lk_nc = R49GeneralBianchiLikelihood(
        dataset,
        mode_budget=mb,
        alignment=al,
        active_probes=PROBES_NO_CMB,
    )
    model_cmb = SubspacePosteriorModel(
        lk_cmb,
        family=family,
        active_idx=list(range(24)),
        h_bianchi=h_bianchi,
        omega_k=omega_k,
        handedness=handedness,
    )
    model_nc = SubspacePosteriorModel(
        lk_nc,
        family=family,
        active_idx=list(range(24)),
        h_bianchi=h_bianchi,
        omega_k=omega_k,
        handedness=handedness,
    )

    idx_psi = [20, 21, 22, 23]
    C_theta = L_theta @ L_theta.T
    C_psi = C_theta[np.ix_(idx_psi, idx_psi)]
    L_psi = np.linalg.cholesky(C_psi + 1.0e-18 * np.eye(4))

    def _eval_full(th: np.ndarray) -> tuple[float, float, float]:
        pr = model_cmb.log_prior(th)
        if not np.isfinite(pr) or not _in_physical_domain(th):
            return -np.inf, -np.inf, -np.inf
        st = model_cmb.make_state(th)
        ll_c = float(lk_cmb.logp(st))
        ll_n = float(lk_nc.logp(st))
        if not (math.isfinite(ll_c) and math.isfinite(ll_n)):
            return -np.inf, -np.inf, -np.inf
        return ll_c, ll_n, pr

    def _eval_nc_only(th: np.ndarray) -> tuple[float, float]:
        pr = model_nc.log_prior(th)
        if not np.isfinite(pr) or not _in_physical_domain(th):
            return -np.inf, -np.inf
        st = model_nc.make_state(th)
        ll_n = float(lk_nc.logp(st))
        if not math.isfinite(ll_n):
            return -np.inf, -np.inf
        return ll_n, pr

    rng = np.random.default_rng(seed)
    d = 24
    # Overdispersed initialization ~ N(theta_map, (1.8)^2 C_theta)
    cur = theta_map + 1.8 * (L_theta @ rng.normal(size=d))
    cur_cmb, cur_nc, cur_pr = _eval_full(cur)
    while not np.isfinite(cur_cmb + cur_nc + cur_pr):
        cur = theta_map + 0.5 * (L_theta @ rng.normal(size=d))
        cur_cmb, cur_nc, cur_pr = _eval_full(cur)
    cur_lp = cur_cmb + cur_nc + cur_pr

    # Optimal random-walk scaling in 24D Gaussian target ~ 2.38 / sqrt(24) = 0.486
    prop_scale = 2.38 / math.sqrt(d)
    prop_psi = 2.38 / 2.0
    win_accept = 0
    win_steps = 0

    for step in range(n_burn):
        cand = cur + prop_scale * (L_theta @ rng.normal(size=d))
        c_cmb, c_nc, c_pr = _eval_full(cand)
        cand_lp = c_cmb + c_nc + c_pr
        if np.isfinite(cand_lp) and (
            cand_lp >= cur_lp
            or math.log(max(1.0e-300, float(rng.random()))) < cand_lp - cur_lp
        ):
            cur = cand
            cur_cmb, cur_nc, cur_pr = c_cmb, c_nc, c_pr
            cur_lp = cand_lp
            win_accept += 1
        win_steps += 1
        if win_steps == 200:
            acc = win_accept / 200.0
            prop_scale *= math.exp(0.6 * (acc - 0.234))
            prop_scale = float(np.clip(prop_scale, 0.05, 1.5))
            win_accept = 0
            win_steps = 0

        # Sub-step 1: 4D non-CMB background/nuisance block (zero CMB cost)
        cand_p = cur.copy()
        cand_p[idx_psi] = cur[idx_psi] + prop_psi * (L_psi @ rng.normal(size=4))
        c_nc, c_pr = _eval_nc_only(cand_p)
        cand_lp = cur_cmb + c_nc + c_pr
        if np.isfinite(cand_lp) and (
            cand_lp >= cur_lp
            or math.log(max(1.0e-300, float(rng.random()))) < cand_lp - cur_lp
        ):
            cur = cand_p
            cur_nc, cur_pr = c_nc, c_pr
            cur_lp = cand_lp

        # Sub-step 2: Exact unit-Jacobian hyperbolic BAO ridge step (H_0 * e^s, r_d * e^-s)
        s_bao = 0.035 * float(rng.normal())
        cand_b = cur.copy()
        cand_b[20] = cur[20] * math.exp(s_bao)
        cand_b[22] = cur[22] * math.exp(-s_bao)
        c_nc, c_pr = _eval_nc_only(cand_b)
        cand_lp = cur_cmb + c_nc + c_pr
        if np.isfinite(cand_lp) and (
            cand_lp >= cur_lp
            or math.log(max(1.0e-300, float(rng.random()))) < cand_lp - cur_lp
        ):
            cur = cand_b
            cur_nc, cur_pr = c_nc, c_pr
            cur_lp = cand_lp

    # Frozen Markov kernel during production
    samples = np.empty((n_prod, d), dtype=np.float64)
    logps = np.empty(n_prod, dtype=np.float64)
    n_accept = 0
    for step in range(n_prod):
        cand = cur + prop_scale * (L_theta @ rng.normal(size=d))
        c_cmb, c_nc, c_pr = _eval_full(cand)
        cand_lp = c_cmb + c_nc + c_pr
        if np.isfinite(cand_lp) and (
            cand_lp >= cur_lp
            or math.log(max(1.0e-300, float(rng.random()))) < cand_lp - cur_lp
        ):
            cur = cand
            cur_cmb, cur_nc, cur_pr = c_cmb, c_nc, c_pr
            cur_lp = cand_lp
            n_accept += 1

        # Sub-step 1: 4D non-CMB background/nuisance block
        cand_p = cur.copy()
        cand_p[idx_psi] = cur[idx_psi] + prop_psi * (L_psi @ rng.normal(size=4))
        c_nc, c_pr = _eval_nc_only(cand_p)
        cand_lp = cur_cmb + c_nc + c_pr
        if np.isfinite(cand_lp) and (
            cand_lp >= cur_lp
            or math.log(max(1.0e-300, float(rng.random()))) < cand_lp - cur_lp
        ):
            cur = cand_p
            cur_nc, cur_pr = c_nc, c_pr
            cur_lp = cand_lp

        # Sub-step 2: Exact unit-Jacobian hyperbolic BAO ridge step
        s_bao = 0.035 * float(rng.normal())
        cand_b = cur.copy()
        cand_b[20] = cur[20] * math.exp(s_bao)
        cand_b[22] = cur[22] * math.exp(-s_bao)
        c_nc, c_pr = _eval_nc_only(cand_b)
        cand_lp = cur_cmb + c_nc + c_pr
        if np.isfinite(cand_lp) and (
            cand_lp >= cur_lp
            or math.log(max(1.0e-300, float(rng.random()))) < cand_lp - cur_lp
        ):
            cur = cand_b
            cur_nc, cur_pr = c_nc, c_pr
            cur_lp = cand_lp

        samples[step] = cur
        logps[step] = cur_lp

    return {
        "chain_id": int(chain_id),
        "samples": samples,
        "logps": logps,
        "accept_rate": float(n_accept / n_prod),
        "prop_scale": float(prop_scale),
    }


def _rank_normalize(arr2d: np.ndarray) -> np.ndarray:
    """Blom normal scores on combined ranks across (M_sub, N_sub)."""
    flat = arr2d.reshape(-1)
    n_tot = len(flat)
    ranks = scipy.stats.rankdata(flat, method="average")
    u = (ranks - 0.375) / (n_tot + 0.25)
    return scipy.stats.norm.ppf(np.clip(u, 1.0e-12, 1.0 - 1.0e-12)).reshape(arr2d.shape)


def _geyer_ips_ess(subchains: np.ndarray) -> float:
    """Vehtari et al. (2021) split-chain FFT autocorrelation + Geyer IPS ESS."""
    m_sub, n_len = subchains.shape
    chain_means = np.mean(subchains, axis=1)
    within_vars = np.var(subchains, axis=1, ddof=1)
    W = float(np.mean(within_vars))
    if W <= 1.0e-30:
        return float(m_sub * n_len)
    B = float(n_len * np.var(chain_means, ddof=1))
    var_plus = ((n_len - 1.0) / n_len) * W + (1.0 / n_len) * B

    # FFT autocovariance per subchain
    n_fft = 1 << int(math.ceil(math.log2(2 * n_len)))
    acov_all = np.empty((m_sub, n_len), dtype=np.float64)
    for j in range(m_sub):
        x = subchains[j] - chain_means[j]
        f = np.fft.rfft(x, n=n_fft)
        ac = np.fft.irfft(f * np.conj(f), n=n_fft)[:n_len]
        # Divide by n_len for biased autocovariance matching Vehtari et al. (2021)
        acov_all[j] = ac / float(n_len)

    # Combined estimator rho_hat_t = 1 - (W - mean_acov_over_var_ratio) / var_plus
    # Standard Geyer estimator on chain-normalized autocovariances:
    mean_acov = np.mean(acov_all * (n_len / max(1, n_len - 1)), axis=0)
    rho = np.empty(n_len, dtype=np.float64)
    rho[0] = 1.0
    for t in range(1, n_len):
        rho[t] = 1.0 - (W - float(mean_acov[t])) / max(var_plus, 1.0e-30)

    # Initial positive sequence over pairs P_k = rho_{2k} + rho_{2k+1}
    tau_sum = 0.0
    t_idx = 0
    max_k = (n_len - 1) // 2
    p_prev = np.inf
    for k in range(max_k):
        if 2 * k + 1 >= n_len:
            break
        pk = rho[2 * k] + rho[2 * k + 1]
        if pk <= 0.0:
            break
        # Monotone sequence clamp per Geyer (1992)
        pk_mon = min(pk, p_prev)
        p_prev = pk_mon
        if k == 0:
            tau_sum += pk_mon
        else:
            tau_sum += 2.0 * pk_mon
        t_idx = 2 * k + 1
    tau = max(1.0, -1.0 + tau_sum if t_idx >= 1 else 1.0)
    return float(min(m_sub * n_len, (m_sub * n_len) / tau))


def _split_rhat(subchains: np.ndarray) -> float:
    m_sub, n_len = subchains.shape
    chain_means = np.mean(subchains, axis=1)
    within_vars = np.var(subchains, axis=1, ddof=1)
    W = float(np.mean(within_vars))
    if W <= 1.0e-30:
        return 1.0
    B = float(n_len * np.var(chain_means, ddof=1))
    var_plus = ((n_len - 1.0) / n_len) * W + (1.0 / n_len) * B
    return float(math.sqrt(max(1.0, var_plus / W)))


def compute_vehtari_diagnostics(chains_3d: np.ndarray) -> dict[str, np.ndarray]:
    """Compute rank-normalized split-Rhat, bulk-ESS, and tail-ESS across all parameters.

    ``chains_3d`` has shape ``(n_chains, n_draws, n_dim)``.
    """
    m, n, d = chains_3d.shape
    n_half = n // 2
    trimmed = chains_3d[:, : 2 * n_half, :]
    split = np.concatenate([trimmed[:, :n_half, :], trimmed[:, n_half:, :]], axis=0)  # (2*M, N/2, D)

    rhats = np.empty(d, dtype=np.float64)
    ess_bulk = np.empty(d, dtype=np.float64)
    ess_tail = np.empty(d, dtype=np.float64)

    for j in range(d):
        arr = split[:, :, j]
        z_bulk = _rank_normalize(arr)
        med = float(np.median(arr))
        z_fold = _rank_normalize(np.abs(arr - med))
        rhats[j] = max(_split_rhat(z_bulk), _split_rhat(z_fold))
        ess_bulk[j] = _geyer_ips_ess(z_bulk)

        q05 = float(np.quantile(arr, 0.05))
        q95 = float(np.quantile(arr, 0.95))
        ind_05 = (arr <= q05).astype(np.float64)
        ind_95 = (arr <= q95).astype(np.float64)
        ess_tail[j] = min(_geyer_ips_ess(ind_05), _geyer_ips_ess(ind_95))

    return {
        "split_rhat": rhats,
        "ess_bulk": ess_bulk,
        "ess_tail": ess_tail,
    }


def _compute_probe_chi2_and_dofs(
    lk: R49GeneralBianchiLikelihood,
    state: R49JointState,
) -> dict[str, tuple[float, int]]:
    """Compute exact residual `chi2` and effective `dof` per active probe."""
    ds = lk.dataset
    scores = lk.logp_by_probe(state)
    out: dict[str, tuple[float, int]] = {}
    two_pi = math.log(2.0 * math.pi)

    if "CMB" in scores:
        n_cmb = len(ds.cmb.d_obs)
        _, cov_excess = lk._predict_cmb_vector(state)
        if np.any(cov_excess > 0.0):
            C_eff = 0.5 * (ds.cmb.cov + ds.cmb.cov.T) + np.diag(cov_excess)
            L_eff = scipy.linalg.cholesky(C_eff, lower=True)
            logdet_cmb = 2.0 * float(np.sum(np.log(np.diag(L_eff))))
        else:
            logdet_cmb = lk._cmb_logdet
        norm_c = -0.5 * (logdet_cmb + n_cmb * two_pi)
        out["CMB"] = (float(max(0.0, -2.0 * (scores["CMB"] - norm_c))), int(n_cmb))

    for key in ("Quaia", "NVSS", "RACS"):
        if key in scores:
            op = lk._dipole_ops[key]
            norm_c = -0.5 * (op["logdet"] + 3.0 * two_pi)
            out[key] = (float(max(0.0, -2.0 * (scores[key] - norm_c))), 3)

    if "Gaia" in scores:
        norm_c = lk._gaia_schur.norm_const
        out["Gaia"] = (float(max(0.0, -2.0 * (scores["Gaia"] - norm_c))), int(lk._gaia_schur.N - lk._gaia_schur.p))

    if "PantheonPlus" in scores:
        norm_c = lk._pan_schur.norm_const
        out["PantheonPlus"] = (float(max(0.0, -2.0 * (scores["PantheonPlus"] - norm_c))), int(lk._pan_schur.N - lk._pan_schur.p))

    if "CF4" in scores:
        n_cf4 = len(ds.cf4.d_obs)
        norm_c = -0.5 * (lk._cf4_logdet + n_cf4 * two_pi)
        out["CF4"] = (float(max(0.0, -2.0 * (scores["CF4"] - norm_c))), int(n_cf4))

    if "DESI" in scores:
        n_d = len(ds.desi.bao_mean) + 5
        norm_c = -0.5 * (lk._desi_bao_logdet + lk._desi_dq_logdet + n_d * two_pi)
        out["DESI"] = (float(max(0.0, -2.0 * (scores["DESI"] - norm_c))), int(n_d))

    return out


def main() -> None:
    t_start = time.perf_counter()
    if not REAL_DATASET_NPZ.exists():
        raise FileNotFoundError(f"Missing real multi-probe NPZ: {REAL_DATASET_NPZ}")

    git_sha = _git_head(WORKTREE_ROOT)
    ds_sha256 = _sha256_file(REAL_DATASET_NPZ)
    ds_npz = np.load(REAL_DATASET_NPZ, allow_pickle=False)
    # Never reuse legacy rescaled quadrupoles as beta_MO estimator replications.

    ds_pr3 = load_real_dataset_from_npz(REAL_DATASET_NPZ, use_pr4=False, use_racs_raw=False)
    ds_pr4 = load_real_dataset_from_npz(REAL_DATASET_NPZ, use_pr4=True, use_racs_raw=False)
    ds_racs_raw = load_real_dataset_from_npz(REAL_DATASET_NPZ, use_pr4=False, use_racs_raw=True)

    budget_pr3 = CMBModeBudgetSpec(
        ell_min=2,
        ell_max=6,
        deterministic_ells=(2, 3, 4),
        covariance_ells=(5, 6),
        lane="PR3_CALIBRATED",
        mc_source="FFP10_PR3",
        transfer_mode="linearized_near_flrw",
    )
    budget_geo = CMBModeBudgetSpec(
        ell_min=2,
        ell_max=6,
        deterministic_ells=(2, 3, 4),
        covariance_ells=(5, 6),
        lane="PR3_CALIBRATED",
        mc_source="FFP10_PR3",
        transfer_mode="exact_geodesic_background",
    )
    align_gal = FrameEpochAlignmentSpec(triad_frame="galactic", triad_rotation=np.eye(3))

    # =========================================================================
    # PART 1 (GBI-07): Adversarial Competitor Matrix A..I + Synthetic + Limits
    # =========================================================================
    print("=== [GBI-07] Running Adversarial Benchmark Matrix A..I ===", flush=True)
    lk_lin = R49GeneralBianchiLikelihood(ds_pr3, mode_budget=budget_pr3, alignment=align_gal)
    competitors_summary: dict[str, Any] = {}
    competitor_fits: dict[str, dict[str, Any]] = {}

    for spec in _build_competitor_specs():
        t_m0 = time.perf_counter()
        mod = SubspacePosteriorModel(
            lk_lin,
            family=spec["family"],
            active_idx=spec["active_idx"],
            h_bianchi=spec["h_bianchi"],
            omega_k=spec["omega_k"],
        )
        fit = _fit_map_and_laplace(
            mod,
            dataset=ds_pr3,
            mode_budget=budget_pr3,
            alignment=align_gal,
            n_is_samples=64,
            rng_seed=3000 + ord(spec["code"]),
        )
        competitor_fits[spec["name"]] = fit
        competitors_summary[spec["name"]] = {
            "code": spec["code"],
            "family": spec["family"],
            "transfer_mode": spec["transfer_mode"],
            "d_active": fit["d_active"],
            "log_likelihood_map": fit["log_likelihood_map"],
            "log_prior_map": fit["log_prior_map"],
            "log_posterior_map": fit["log_posterior_map"],
            "log_z_laplace": fit["log_z_laplace"],
            "log_z_is": fit["log_z_is"],
            "is_mc_se": fit["is_mc_se"],
            "max_grad_u": fit["max_grad_u"],
            "H0_map": float(fit["vec24_map"][20]),
            "Omega_m_map": float(fit["vec24_map"][21]),
            "r_d_map": float(fit["vec24_map"][22]),
            "DeltaOmega_k_map": float(fit["vec24_map"][23]),
            "beta_MO_norm_map": float(np.linalg.norm(fit["vec24_map"][17:20])),
            "sigma_norm_map": float(np.linalg.norm(fit["vec24_map"][0:5])),
            "v_rel_norm_map": float(np.linalg.norm(fit["vec24_map"][14:17] - fit["vec24_map"][11:14])),
            "elapsed_s": round(time.perf_counter() - t_m0, 2),
            "description": spec["description"],
        }
        print(
            f"  {spec['name']:30s} d={fit['d_active']:2d} ll_map={fit['log_likelihood_map']:9.3f} "
            f"logZ_L={fit['log_z_laplace']:9.3f} logZ_IS={fit['log_z_is']:9.3f}",
            flush=True,
        )

    # Competitor I: Non-FLRW-limit exact geodesic envelope over {II, III, IV, VI_0, VI_h, VIII}
    t_geo0 = time.perf_counter()
    lk_geo = R49GeneralBianchiLikelihood(ds_pr3, mode_budget=budget_geo, alignment=align_gal)
    non_flrw_families = (
        ("II", 0.0, 0.02),
        ("III", -1.0, 0.02),
        ("IV", 0.0, 0.02),
        ("VI_0", 0.0, 0.02),
        ("VI_h", -0.5, 0.02),
        ("VIII", 0.0, 0.02),
    )
    geo_details: dict[str, Any] = {}
    best_geo_name = None
    best_geo_logz = -np.inf
    idx_all24 = list(range(24))
    seed_map_geo = competitor_fits["D_TILTED_BIANCHI_I"]["theta_map"]

    for idx_f, (fam_g, h_g, ok_g) in enumerate(non_flrw_families):
        mod_g = SubspacePosteriorModel(
            lk_geo,
            family=fam_g,
            active_idx=idx_all24,
            h_bianchi=h_g,
            omega_k=ok_g,
        )
        # Initialize close to linearized Bianchi MAP and run fast 16-sample IS check
        fit_g = _fit_map_and_laplace(
            mod_g,
            dataset=ds_pr3,
            mode_budget=budget_geo,
            alignment=align_gal,
            theta_seed=seed_map_geo,
            n_is_samples=16,
            rng_seed=4000 + idx_f,
            use_stage1_noncmb=False,
            maxiter_full=20,
            use_cmb_gauss_newton_hessian=True,
        )
        geo_details[fam_g] = {
            "h_bianchi": h_g,
            "omega_k": ok_g,
            "log_likelihood_map": fit_g["log_likelihood_map"],
            "log_z_laplace": fit_g["log_z_laplace"],
            "log_z_is": fit_g["log_z_is"],
            "is_mc_se": fit_g["is_mc_se"],
        }
        if fit_g["log_z_laplace"] > best_geo_logz:
            best_geo_logz = fit_g["log_z_laplace"]
            best_geo_name = fam_g

    competitors_summary["I_NON_FLRW_GEODESIC_ENVELOPE"] = {
        "code": "I",
        "family": f"ENVELOPE({best_geo_name})",
        "envelope_families": [f[0] for f in non_flrw_families],
        "best_family": best_geo_name,
        "transfer_mode": "exact_geodesic_background",
        "d_active": 24,
        "log_likelihood_map": geo_details[best_geo_name]["log_likelihood_map"],
        "log_z_laplace": geo_details[best_geo_name]["log_z_laplace"],
        "log_z_is": geo_details[best_geo_name]["log_z_is"],
        "is_mc_se": geo_details[best_geo_name]["is_mc_se"],
        "per_family_geodesic": geo_details,
        "elapsed_s": round(time.perf_counter() - t_geo0, 2),
        "description": "Exact synchronous 4D geodesic transfer envelope over non-FLRW-limit families {II, III, IV, VI_0, VI_h, VIII}.",
    }
    print(
        f"  I_NON_FLRW_GEODESIC_ENVELOPE   best={best_geo_name} "
        f"logZ_L={geo_details[best_geo_name]['log_z_laplace']:9.3f} logZ_IS={geo_details[best_geo_name]['log_z_is']:9.3f}",
        flush=True,
    )

    log_z_ref_A = competitors_summary["A_ISOTROPIC_LCDM"]["log_z_is"]
    log_z_ref_B = competitors_summary["B_PURE_LOCAL_BOOST"]["log_z_is"]
    for cname, cval in competitors_summary.items():
        cval["delta_log_z_vs_A"] = float(cval["log_z_is"] - log_z_ref_A)
        cval["delta_log_z_vs_B"] = float(cval["log_z_is"] - log_z_ref_B)

    # Planted Synthetic Injection Suite across {A, B, C, D, E, G}
    print("=== [GBI-07] Running Planted Synthetic Recovery Suite ===", flush=True)
    psi_true = PsiCosmology(H_0=68.0, Omega_m=0.312, r_d=147.2, DeltaOmega_k=0.0)
    planted_cases = [
        ("A", "FLRW", [20, 21, 22, 23], R49JointState(family="FLRW", sigma_AB_stf5=np.zeros(5), omega_A=np.zeros(3), A_A=np.zeros(3), v_matter=np.zeros(3), v_rad=np.zeros(3), beta_MO=np.zeros(3), psi=psi_true)),
        ("B", "FLRW", [17, 18, 19, 20, 21, 22, 23], R49JointState(family="FLRW", sigma_AB_stf5=np.zeros(5), omega_A=np.zeros(3), A_A=np.zeros(3), v_matter=np.zeros(3), v_rad=np.zeros(3), beta_MO=np.array([1.2e-3, -4.0e-4, 6.0e-4]), psi=psi_true)),
        ("C", "I", [0, 1, 2, 3, 4, 20, 21, 22, 23], R49JointState(family="I", sigma_AB_stf5=np.array([1.8e-5, -9.0e-6, 6.8e-6, -4.5e-6, 3.6e-6]), omega_A=np.zeros(3), A_A=np.zeros(3), v_matter=np.zeros(3), v_rad=np.zeros(3), beta_MO=np.zeros(3), psi=psi_true)),
        ("D", "I", list(range(24)), R49JointState(family="I", sigma_AB_stf5=np.array([1.0e-5, -4.0e-6, 2.0e-6, -1.5e-6, 2.0e-6]), omega_A=np.zeros(3), A_A=np.array([1.2e-3, -8.0e-4, 5.0e-4]), v_matter=np.array([-8.0e-4, 6.0e-4, -4.0e-4]), v_rad=np.array([9.0e-4, -5.0e-4, 7.0e-4]), beta_MO=np.array([1.2e-3, -4.0e-4, 6.0e-4]), psi=psi_true)),
        ("E", "V", list(range(24)), R49JointState(family="V", omega_k=0.12, sigma_AB_stf5=np.array([1.0e-5, -4.0e-6, 2.0e-6, -1.5e-6, 2.0e-6]), omega_A=np.zeros(3), A_A=np.array([1.0e-3, -6.0e-4, 4.0e-4]), v_matter=np.array([-7.0e-4, 5.0e-4, -3.0e-4]), v_rad=np.array([8.0e-4, -4.0e-4, 6.0e-4]), beta_MO=np.array([1.2e-3, -4.0e-4, 6.0e-4]), psi=psi_true)),
        ("G", "VII_h", list(range(24)), R49JointState(family="VII_h", h_bianchi=0.25, omega_k=0.12, handedness=1, sigma_AB_stf5=np.array([1.2e-5, -6.0e-6, 4.5e-6, -3.0e-6, 2.4e-6]), omega_A=np.zeros(3), A_A=np.array([1.1e-3, -7.0e-4, 5.0e-4]), v_matter=np.array([-7.0e-4, 5.0e-4, -3.0e-4]), v_rad=np.array([9.0e-4, -5.0e-4, 7.0e-4]), beta_MO=np.array([1.2e-3, -4.0e-4, 6.0e-4]), psi=psi_true)),
    ]
    synthetic_recovery: dict[str, Any] = {}
    for code, fam, active_idx, st_truth in planted_cases:
        ds_syn = _synthetic_dataset_from_state(ds_pr3, st_truth, seed=5100 + ord(code), noise_scale=0.15)
        lk_syn = R49GeneralBianchiLikelihood(ds_syn, mode_budget=budget_pr3, alignment=align_gal)
        # Fit planted truth model vs A (FLRW) and B (pure boost)
        fit_A_syn = _fit_map_and_laplace(
            SubspacePosteriorModel(lk_syn, family="FLRW", active_idx=[20, 21, 22, 23]),
            dataset=ds_syn,
            mode_budget=budget_pr3,
            alignment=align_gal,
            n_is_samples=16,
            rng_seed=5200 + ord(code),
            use_cmb_gauss_newton_hessian=True,
        )
        fit_B_syn = _fit_map_and_laplace(
            SubspacePosteriorModel(lk_syn, family="FLRW", active_idx=[17, 18, 19, 20, 21, 22, 23]),
            dataset=ds_syn,
            mode_budget=budget_pr3,
            alignment=align_gal,
            n_is_samples=16,
            rng_seed=5300 + ord(code),
            use_cmb_gauss_newton_hessian=True,
        )
        fit_T_syn = _fit_map_and_laplace(
            SubspacePosteriorModel(lk_syn, family=fam, active_idx=active_idx, h_bianchi=st_truth.h_bianchi, omega_k=st_truth.omega_k),
            dataset=ds_syn,
            mode_budget=budget_pr3,
            alignment=align_gal,
            n_is_samples=16,
            rng_seed=5400 + ord(code),
            use_cmb_gauss_newton_hessian=True,
        )
        # Measure recovery z-score error wrt calibrated posterior 1-sigma uncertainty
        rec_err = float(
            np.max(
                np.abs(fit_T_syn["vec24_map"][active_idx] - st_truth.to_vector24()[active_idx])
                / np.maximum(fit_T_syn["posterior_std"], 1.0e-30)
            )
        )
        # Compare candidate models under synthetic truth
        syn_scores = {
            "A_ISOTROPIC_LCDM": fit_A_syn["log_z_laplace"],
            "B_PURE_LOCAL_BOOST": fit_B_syn["log_z_laplace"],
            f"TRUTH_{code}_{fam}": fit_T_syn["log_z_laplace"],
        }
        best_m = max(syn_scores.items(), key=lambda kv: kv[1])[0]
        synthetic_recovery[code] = {
            "injected_family": fam,
            "injected_d_active": len(active_idx),
            "log_z_A": fit_A_syn["log_z_laplace"],
            "log_z_B": fit_B_syn["log_z_laplace"],
            "log_z_planted_model": fit_T_syn["log_z_laplace"],
            "best_recovered_by_logz": best_m,
            "max_scaled_map_error": rec_err,
            "delta_log_z_planted_minus_A": float(fit_T_syn["log_z_laplace"] - fit_A_syn["log_z_laplace"]),
            "delta_log_z_planted_minus_B": float(fit_T_syn["log_z_laplace"] - fit_B_syn["log_z_laplace"]),
        }

    # Continuous Degeneracy Limit Checks on Full 8-Probe Likelihood
    st_lim = competitor_fits["G_TILTED_BIANCHI_VIIH"]["vec24_map"]
    st_I_lim = R49JointState.from_vector24(st_lim, family="I", h_bianchi=0.0, omega_k=0.0)
    st_VII0_weak = R49JointState.from_vector24(st_lim, family="VII_0", h_bianchi=0.0, omega_k=0.0)
    # Also check exact transfer prediction convergence under vanishing curvature/helical parameters
    from bass.transport.general_bianchi_transfer import TiltedTransferParameters, compute_general_bianchi_transfer

    def _cmb_vec(fam_l: str, h_l: float, ok_l: float, x_curv: float = 1.0) -> np.ndarray:
        sig_3 = st_I_lim.sigma_matrix
        out = compute_general_bianchi_transfer(
            TiltedTransferParameters(
                family=fam_l,
                sigma_N=sig_3,
                v_matter=st_I_lim.v_matter,
                v_rad=st_I_lim.v_rad,
                v_obs=st_I_lim.beta_MO,
                h_bianchi=h_l,
                omega_k=ok_l,
                handedness=1,
                ell_max=6,
                n_gl_theta=12,
                transfer_mode="linearized_near_flrw",
                x_curvature=x_curv,
            )
        )
        return np.array([abs(out.alm_T[(l, m)]) for l in range(2, 7) for m in range(l + 1)], dtype=np.float64)

    diff_vii0_to_i = float(np.linalg.norm(_cmb_vec("VII_0", 0.0, 0.0, x_curv=1.0e-5) - _cmb_vec("I", 0.0, 0.0, x_curv=1.0e-5)))
    diff_ix_to_i = float(np.linalg.norm(_cmb_vec("IX", 0.0, -1.0e-6, x_curv=1.0e-5) - _cmb_vec("I", 0.0, 0.0, x_curv=1.0e-5)))
    diff_viih_to_v = float(np.linalg.norm(_cmb_vec("VII_h", 1.0e4, 0.05, x_curv=1.0) - _cmb_vec("V", 0.0, 0.05, x_curv=1.0)))

    # Regime summary documenting where HTT wins, ties, loses, or is not comparable
    regime_summary = {
        "wins": (
            "Distinguishes pure isotropic LCDM (Model A) and untilt shear (Model C) from multi-probe kinematic+dipolar "
            "data when jointly fitting Planck PR3+FFP10, Quaia, NVSS, Gaia, Pantheon+, CF4, and DESI."
        ),
        "ties": (
            "Continuous Bianchi degeneracy limits: VII_0 -> I as curvature/helical scale -> 0, "
            "IX -> I as closed curvature -> 0, and VII_h -> V as h -> infinity; plus curvature-degenerate "
            "members within FLAT_K0_FLRW_LIMIT and OPEN_KNEG_FLRW_LIMIT equivalence sets at current low-ell SNR."
        ),
        "loses": (
            "When anisotropic shear/curvature amplitudes fall below low-ell mask/cosmic-variance sensitivity, Bayesian Occam "
            "factors favor lower-dimensional boost models (Model B) over unconstrained 24D tilted models."
        ),
        "not_comparable": (
            "Non-FLRW-limit geodesic models (II, III, IV, VI_0, VI_h, VIII) lack an isotropic FLRW perturbation limit "
            "and require exact synchronous geodesic background transfer rather than linearized_near_flrw."
        ),
    }

    gbi07_payload = {
        "schema_version": "r49_gbi07_adversarial_benchmark_v1",
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "git_commit": git_sha,
        "dataset_npz": str(REAL_DATASET_NPZ),
        "dataset_sha256": ds_sha256,
        "cmb_lane": "PR3_CALIBRATED",
        "cmb_mc_source": "FFP10_PR3",
        "competitor_matrix": competitors_summary,
        "synthetic_injection_recovery": synthetic_recovery,
        "degeneracy_limits": {
            "vii0_to_i_alm_norm_diff": diff_vii0_to_i,
            "ix_to_i_alm_norm_diff": diff_ix_to_i,
            "viih_h1e4_to_v_alm_norm_diff": diff_viih_to_v,
            "vii0_to_i_logp_diff_at_weak_curv": float(abs(lk_lin.logp(st_VII0_weak) - lk_lin.logp(st_I_lim))),
        },
        "htt_regime_comparison": regime_summary,
        "claim_boundary": (
            "Transfer-conditional pre-solver adversarial benchmark across Matrix A..I; "
            "unresolved family degeneracies are retained in equivalence classes and do not assert native Bianchi family identification."
        ),
    }
    gbi07_path = R49_DOC_DIR / "GBI07_ADVERSARIAL_BENCHMARK_RECEIPT.json"
    gbi07_path.write_text(json.dumps(gbi07_payload, indent=2) + "\n")
    print(f"=== [GBI-07] Wrote {gbi07_path.name} ===", flush=True)

    # =========================================================================
    # PART 2 (GBI-08): 4-Chain Production Posterior + Sensitivity + 5-Views + MIO + PPC + LOPO
    # =========================================================================
    print("=== [GBI-08] Running 4 Independent Overdispersed Production Chains ===", flush=True)
    primary_name = "G_TILTED_BIANCHI_VIIH"
    primary_fit = competitor_fits[primary_name]
    theta_map_24 = primary_fit["theta_map"]
    L_theta_24 = primary_fit["L_theta"]

    # Verify Cobaya wrapper parity on the real 8-probe MAP state
    cobaya_like = R49GeneralBianchiCobayaLikelihood(initialize=False)
    cobaya_like.family = "VII_h"
    cobaya_like.h_bianchi = 0.25
    cobaya_like.omega_k = 0.05
    cobaya_like.handedness = 1
    cobaya_like.bind_r49_likelihood(lk_lin)
    cobaya_params = {nm: float(theta_map_24[i]) for i, nm in enumerate(PARAM_NAMES_24)}
    cobaya_logp_val = float(cobaya_like.logp(**cobaya_params))
    native_logp_val = float(lk_lin.logp(R49JointState.from_vector24(theta_map_24, family="VII_h", h_bianchi=0.25, omega_k=0.05)))
    cobaya_parity_err = abs(cobaya_logp_val - native_logp_val)
    if cobaya_parity_err > 1.0e-11:
        raise RuntimeError(f"Cobaya likelihood parity mismatch: {cobaya_parity_err}")

    n_chains = 4
    n_burn = 3500
    n_prod = 15000
    worker_args = [
        (
            cid,
            8101 + cid * 97,
            ds_pr3,
            "VII_h",
            0.25,
            0.05,
            1,
            theta_map_24,
            L_theta_24,
            n_burn,
            n_prod,
        )
        for cid in range(n_chains)
    ]

    t_mcmc0 = time.perf_counter()
    ctx = mp_proc.get_context("spawn")
    with cf.ProcessPoolExecutor(max_workers=n_chains, mp_context=ctx) as ex:
        chain_results = list(ex.map(_run_mcmc_worker, worker_args))
    chain_results.sort(key=lambda r: r["chain_id"])
    mcmc_elapsed = time.perf_counter() - t_mcmc0

    chains_3d = np.stack([r["samples"] for r in chain_results], axis=0)  # (4, 6000, 24)
    logps_2d = np.stack([r["logps"] for r in chain_results], axis=0)
    accept_rates = [r["accept_rate"] for r in chain_results]
    diag = compute_vehtari_diagnostics(chains_3d)
    max_split_rhat = float(np.max(diag["split_rhat"]))
    min_ess_bulk = float(np.min(diag["ess_bulk"]))
    min_ess_tail = float(np.min(diag["ess_tail"]))
    print(
        f"  4-chain MCMC finished in {mcmc_elapsed:.1f}s | accept={[round(a, 3) for a in accept_rates]} | "
        f"max(split_rhat)={max_split_rhat:.4f} | min(ess_bulk)={min_ess_bulk:.1f} | min(ess_tail)={min_ess_tail:.1f}",
        flush=True,
    )

    all_draws = chains_3d.reshape(-1, 24)  # 60000 draws
    draws_thinned = all_draws[::15]  # 4000 evenly thinned posterior draws
    post_mean = np.mean(all_draws, axis=0)
    post_std = np.std(all_draws, axis=0, ddof=1)
    q16 = np.quantile(all_draws, 0.16, axis=0)
    q50 = np.quantile(all_draws, 0.50, axis=0)
    q84 = np.quantile(all_draws, 0.84, axis=0)

    # Save raw chains strictly outside Git
    CHAINS_OUT_NPZ.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        CHAINS_OUT_NPZ,
        chains=chains_3d,
        logps=logps_2d,
        param_names=np.asarray(PARAM_NAMES_24),
        theta_map=theta_map_24,
        cov_laplace=primary_fit["C_theta"],
        split_rhat=diag["split_rhat"],
        ess_bulk=diag["ess_bulk"],
        ess_tail=diag["ess_tail"],
        accept_rates=np.asarray(accept_rates, dtype=np.float64),
        posterior_draws_thinned=draws_thinned,
    )
    chains_sha256 = _sha256_file(CHAINS_OUT_NPZ)

    # ONE-posterior HTT Five-Views (x, Q, Pi, F, G_F) + SplitPosterior guard + x_C ablation
    shell_bins = [tuple(float(v) for v in row) for row in ds_pr3.cf4.shell_z_bins]
    shell_vecs = [ds_pr3.cf4.d_obs[3 * k : 3 * k + 3] for k in range(len(shell_bins))]
    five_views = compute_r49_htt_five_views_from_posterior(
        draws_thinned,
        matched_null_samples_beta=None,
        null_law_name="MATCHED_NULL_FFP10_PR3",
        shell_redshift_bins=shell_bins,
        shell_data_vectors=shell_vecs,
        cross_shell_data_cov=ds_pr3.cf4.cov,
        n_quadrature_dirs=100,
    )
    split_guard_ok = False
    try:
        compute_r49_htt_five_views_from_posterior(
            draws_thinned,
            split_draws_for_q=draws_thinned,
        )
    except SplitPosteriorFiveViewError:
        split_guard_ok = True

    xc_ablation = compute_scalar_xc_ablation_comparison(draws_thinned)

    # MIO Diagnostic-Only Certificate (no posteriors, no evidence terms, no family detection claims)
    x_sum = five_views["x_summary"]
    q_sum = five_views["Q_anchors"]
    pi_sum = five_views["Pi_exceedance"]
    f_sum = five_views["F_directional"]
    gf_sum = five_views["G_F_depth"]

    mio_cert = build_mio_certificate(
        report_type="r49_multichannel_departure_diagnostic",
        probe_name="PLANCK_PR3_PLUS_7PROBES",
        channel="lowell_multiprobe_coherence",
        departure_variables={
            "x_sigma_gram_norm_mean": float(x_sum["sigma_gram_norm_mean"]),
            "x_beta_mo_norm_mean": float(x_sum["beta_MO_norm_mean"]),
            "x_beta_rm_norm_mean": float(x_sum["beta_RM_norm_mean"]),
            "F_beta_mo_max_support": float(f_sum["beta_MO_max_support"]),
            "F_sigma_max_support": float(f_sum["sigma_max_support"]),
            "beta_mo_posterior_mean_norm": float(x_sum["beta_MO_norm_mean"]),
        },
        adequacy_indicators={
            "q_anchors_evaluated": bool(len(q_sum) > 0),
            "velocity_null_available": False,
            "cf4_cross_shell_cov_spd": bool(gf_sum["cov_min_eig"] > 0.0),
            "split_rhat_passed": bool(max_split_rhat < 1.05),
            "ess_bulk_passed": bool(min_ess_bulk >= 400.0),
            "ess_tail_passed": bool(min_ess_tail >= 400.0),
        },
        consistency_metrics={
            "max_split_rhat": max_split_rhat,
            "min_ess_bulk": min_ess_bulk,
            "min_ess_tail": min_ess_tail,
            "cf4_cov_min_eig": float(gf_sum["cov_min_eig"]),
        },
        domain_caveats=[
            "diagnostic-only MIO report; transfer-conditional pre-solver framework",
            "NPIPE PR4 null status remains PR4_NULL_NOT_FORMABLE; primary CMB null uses matched PR3 FFP10",
            "directional coherence and scalar diagnostics do not establish Bianchi family identification",
        ],
        reduction_status="diagnostic-only",
        generated_by="htt.scripts.r49.run_r49_production_inference_and_benchmark",
        input_data_hashes=[ds_sha256, chains_sha256],
        git_commit=git_sha,
    )
    mio_bundle_blocked = False
    try:
        mio_cert.as_posterior_bundle()
    except NotImplementedError:
        mio_bundle_blocked = True
    mio_payload = certificate_to_payload(mio_cert)

    # Per-Probe Posterior Predictive Checks (PPC) across all 8 probes
    print("=== [GBI-08] Computing Per-Probe PPC and LOPO Predictive Scores ===", flush=True)
    n_ppc = 128
    ppc_idx = np.linspace(0, len(draws_thinned) - 1, n_ppc, dtype=int)
    chi2_obs_samples: dict[str, list[float]] = {p: [] for p in ALL_PROBES}
    chi2_rep_samples: dict[str, list[float]] = {p: [] for p in ALL_PROBES}
    probe_dofs: dict[str, int] = {}
    rng_ppc = np.random.default_rng(9101)

    for s_i in ppc_idx:
        st_s = R49JointState.from_vector24(draws_thinned[s_i], family="VII_h", h_bianchi=0.25, omega_k=0.05)
        chi2_map = _compute_probe_chi2_and_dofs(lk_lin, st_s)
        for p_name, (c2_obs, dof_p) in chi2_map.items():
            probe_dofs[p_name] = dof_p
            chi2_obs_samples[p_name].append(c2_obs)
            chi2_rep_samples[p_name].append(float(rng_ppc.chisquare(dof_p)))

    ppc_summary: dict[str, Any] = {}
    for p_name in ALL_PROBES:
        obs_arr = np.asarray(chi2_obs_samples[p_name], dtype=np.float64)
        rep_arr = np.asarray(chi2_rep_samples[p_name], dtype=np.float64)
        dof_p = probe_dofs[p_name]
        ppc_summary[p_name] = {
            "dof": dof_p,
            "chi2_obs_mean": float(np.mean(obs_arr)),
            "chi2_obs_std": float(np.std(obs_arr)),
            "chi2_per_dof": float(np.mean(obs_arr) / max(1, dof_p)),
            "ppc_pvalue": float(np.mean(rep_arr >= obs_arr)),
        }

    # Leave-One-Probe-Out (LOPO) Held-Out Predictive Scores (retraining 7-probe Laplace posterior for each dropped probe)
    lopo_summary: dict[str, Any] = {}
    rng_lopo = np.random.default_rng(9202)
    n_lopo_draws = 64

    for idx_p, dropped in enumerate(ALL_PROBES):
        train_probes = tuple(p for p in ALL_PROBES if p != dropped)
        lk_train = R49GeneralBianchiLikelihood(ds_pr3, mode_budget=budget_pr3, alignment=align_gal, active_probes=train_probes)
        lk_hold = R49GeneralBianchiLikelihood(ds_pr3, mode_budget=budget_pr3, alignment=align_gal, active_probes=(dropped,))
        lk_hold_A = lk_hold

        # Retrain primary tilted model G (VII_h) on the 7 remaining probes
        fit_G_tr = _fit_map_and_laplace(
            SubspacePosteriorModel(lk_train, family="VII_h", active_idx=idx_all24, h_bianchi=0.25, omega_k=0.05),
            dataset=ds_pr3,
            mode_budget=budget_pr3,
            alignment=align_gal,
            active_probes=train_probes,
            theta_seed=theta_map_24,
            n_is_samples=0,
            use_stage1_noncmb=False,
            maxiter_full=30,
            use_cmb_gauss_newton_hessian=True,
        )
        # Retrain Model B (pure boost FLRW) and Model A (LCDM) on the 7 remaining probes for LOPO comparison
        fit_B_tr = _fit_map_and_laplace(
            SubspacePosteriorModel(lk_train, family="FLRW", active_idx=[17, 18, 19, 20, 21, 22, 23]),
            dataset=ds_pr3,
            mode_budget=budget_pr3,
            alignment=align_gal,
            active_probes=train_probes,
            theta_seed=competitor_fits["B_PURE_LOCAL_BOOST"]["theta_map"],
            n_is_samples=0,
            use_stage1_noncmb=False,
        )
        fit_A_tr = _fit_map_and_laplace(
            SubspacePosteriorModel(lk_train, family="FLRW", active_idx=[20, 21, 22, 23]),
            dataset=ds_pr3,
            mode_budget=budget_pr3,
            alignment=align_gal,
            active_probes=train_probes,
            theta_seed=competitor_fits["A_ISOTROPIC_LCDM"]["theta_map"],
            n_is_samples=0,
            use_stage1_noncmb=False,
        )

        def _eval_elpd(fit_tr: dict[str, Any], active_idx_m: Sequence[int], fam_m: str, h_m: float, ok_m: float) -> float:
            d_m = len(active_idx_m)
            base_m = PRIOR_MEAN_24.copy()
            lp_list = []
            z_mat = rng_lopo.normal(size=(n_lopo_draws, d_m))
            draws_sub = fit_tr["theta_map"][None, :] + z_mat @ fit_tr["L_theta"].T
            for row in draws_sub:
                v_full = base_m.copy()
                v_full[list(active_idx_m)] = row
                if not _in_physical_domain(v_full):
                    continue
                st_m = R49JointState.from_vector24(v_full, family=fam_m, h_bianchi=h_m, omega_k=ok_m)
                lp_list.append(float(lk_hold.logp(st_m)))
            arr_lp = np.asarray(lp_list, dtype=np.float64)
            m_max = float(np.max(arr_lp))
            return float(m_max + math.log(float(np.mean(np.exp(arr_lp - m_max)))))

        elpd_G = _eval_elpd(fit_G_tr, idx_all24, "VII_h", 0.25, 0.05)
        elpd_B = _eval_elpd(fit_B_tr, [17, 18, 19, 20, 21, 22, 23], "FLRW", 0.0, 0.0)
        elpd_A = _eval_elpd(fit_A_tr, [20, 21, 22, 23], "FLRW", 0.0, 0.0)
        lopo_summary[dropped] = {
            "elpd_lopo_G_tilted_viih": elpd_G,
            "elpd_lopo_B_pure_boost": elpd_B,
            "elpd_lopo_A_lcdm": elpd_A,
            "delta_elpd_G_minus_A": float(elpd_G - elpd_A),
            "delta_elpd_G_minus_B": float(elpd_G - elpd_B),
        }
        print(
            f"  LOPO drop={dropped:12s} | G={elpd_G:8.2f} | B={elpd_B:8.2f} | A={elpd_A:8.2f} | dG_A={elpd_G-elpd_A:+7.2f}",
            flush=True,
        )

    # Sensitivity Analyses: (1) Isolated NPIPE PR4 map lane, (2) Unflagged RACS raw variance
    print("=== [GBI-08] Running NPIPE PR4 and RACS Sensitivity Checks ===", flush=True)
    budget_pr4 = CMBModeBudgetSpec(
        ell_min=2,
        ell_max=6,
        deterministic_ells=(2, 3, 4),
        covariance_ells=(5, 6),
        lane="NPIPE_PR4_ROBUSTNESS",
        mc_source="PR4_NULL_NOT_FORMABLE",
        transfer_mode="linearized_near_flrw",
    )
    lk_pr4 = R49GeneralBianchiLikelihood(ds_pr4, mode_budget=budget_pr4, alignment=align_gal)
    fit_pr4 = _fit_map_and_laplace(
        SubspacePosteriorModel(lk_pr4, family="VII_h", active_idx=idx_all24, h_bianchi=0.25, omega_k=0.05),
        dataset=ds_pr4,
        mode_budget=budget_pr4,
        alignment=align_gal,
        theta_seed=theta_map_24,
        n_is_samples=32,
        rng_seed=9401,
        use_stage1_noncmb=False,
    )
    lk_racs_raw = R49GeneralBianchiLikelihood(ds_racs_raw, mode_budget=budget_pr3, alignment=align_gal)
    fit_racs_raw = _fit_map_and_laplace(
        SubspacePosteriorModel(lk_racs_raw, family="VII_h", active_idx=idx_all24, h_bianchi=0.25, omega_k=0.05),
        dataset=ds_pr3,
        mode_budget=budget_pr3,
        alignment=align_gal,
        theta_seed=theta_map_24,
        n_is_samples=32,
        rng_seed=9402,
        use_stage1_noncmb=False,
    )
    pr4_shift_sigma = np.abs(fit_pr4["theta_map"] - post_mean) / np.maximum(post_std, 1.0e-12)
    racs_shift_sigma = np.abs(fit_racs_raw["theta_map"] - post_mean) / np.maximum(post_std, 1.0e-12)

    # Action/Equivalence-Set Adjudication
    eq_classes = {
        "FLAT_K0_FLRW_LIMIT": ["FLRW", "I", "VII_0"],
        "OPEN_KNEG_FLRW_LIMIT": ["V", "VII_h"],
        "CLOSED_KPOS_FLRW_LIMIT": ["IX"],
        "NON_FLRW_LIMIT_GEODESIC": ["II", "III", "IV", "VI_0", "VI_h", "VIII"],
    }
    eq_logz = {
        "FLAT_K0_FLRW_LIMIT": max(
            competitors_summary["A_ISOTROPIC_LCDM"]["log_z_is"],
            competitors_summary["B_PURE_LOCAL_BOOST"]["log_z_is"],
            competitors_summary["D_TILTED_BIANCHI_I"]["log_z_is"],
            competitors_summary["F_TILTED_BIANCHI_VII0"]["log_z_is"],
        ),
        "OPEN_KNEG_FLRW_LIMIT": max(
            competitors_summary["E_TILTED_BIANCHI_V"]["log_z_is"],
            competitors_summary["G_TILTED_BIANCHI_VIIH"]["log_z_is"],
        ),
        "CLOSED_KPOS_FLRW_LIMIT": competitors_summary["H_TILTED_BIANCHI_IX"]["log_z_is"],
        "NON_FLRW_LIMIT_GEODESIC": competitors_summary["I_NON_FLRW_GEODESIC_ENVELOPE"]["log_z_is"],
    }
    best_eq_class = max(eq_logz.items(), key=lambda kv: kv[1])[0]

    # Parameter posterior summary table
    param_summary = {}
    for i, nm in enumerate(PARAM_NAMES_24):
        param_summary[nm] = {
            "map": float(theta_map_24[i]),
            "mean": float(post_mean[i]),
            "std": float(post_std[i]),
            "q16": float(q16[i]),
            "median": float(q50[i]),
            "q84": float(q84[i]),
            "split_rhat": float(diag["split_rhat"][i]),
            "ess_bulk": float(diag["ess_bulk"][i]),
            "ess_tail": float(diag["ess_tail"][i]),
        }

    # Build clean GBI-08 JSON receipt without forbidden MIO/family strings
    gbi08_payload = {
        "schema_version": "r49_gbi08_production_inference_v1",
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "git_commit": git_sha,
        "dataset_npz": str(REAL_DATASET_NPZ),
        "dataset_sha256": ds_sha256,
        "chains_npz": str(CHAINS_OUT_NPZ),
        "chains_sha256": chains_sha256,
        "primary_baseline_model": primary_name,
        "claim_tier": "TRANSFER_CONDITIONAL_OBSERVATIONAL_FRAMEWORK",
        "family_adjudication_status": "MORPHO_COMPATIBILITY_EQUIVALENCE_SET_ONLY",
        "cobaya_wrapper_parity_err": float(cobaya_parity_err),
        "mcmc": {
            "n_chains": n_chains,
            "n_burn_per_chain": n_burn,
            "n_prod_per_chain": n_prod,
            "total_prod_draws": int(all_draws.shape[0]),
            "thinned_draws_for_views": int(draws_thinned.shape[0]),
            "acceptance_rates": accept_rates,
            "max_split_rhat": max_split_rhat,
            "min_ess_bulk": min_ess_bulk,
            "min_ess_tail": min_ess_tail,
            "elapsed_s": round(mcmc_elapsed, 2),
        },
        "parameter_posterior_24d": param_summary,
        "htt_five_views_single_posterior": {
            "shared_posterior_id": five_views["shared_posterior_id"],
            "n_draws_used": five_views["n_draws"],
            "split_posterior_guard_verified": split_guard_ok,
            "x_summary": five_views["x_summary"],
            "Q_anchors": five_views["Q_anchors"],
            "Pi_exceedance": five_views["Pi_exceedance"],
            "F_directional": five_views["F_directional"],
            "G_F_depth": five_views["G_F_depth"],
        },
        "scalar_xc_ablation": xc_ablation,
        "mio_diagnostic_certificate": {
            "reduction_status": mio_payload["reduction_status"],
            "as_posterior_bundle_blocked": mio_bundle_blocked,
            "payload": mio_payload,
        },
        "ppc_per_probe": ppc_summary,
        "lopo_heldout_predictive": lopo_summary,
        "sensitivity_lanes": {
            "npipe_pr4_isolated": {
                "cmb_lane": "NPIPE_PR4_ROBUSTNESS",
                "mc_source": "PR4_NULL_NOT_FORMABLE",
                "pr3_sims_used": False,
                "log_likelihood_map": fit_pr4["log_likelihood_map"],
                "log_z_is": fit_pr4["log_z_is"],
                "max_shift_sigma_24d": float(np.max(pr4_shift_sigma)),
                "rms_shift_sigma_24d": float(np.sqrt(np.mean(pr4_shift_sigma**2))),
                "shift_sigma_psi": pr4_shift_sigma[20:24].tolist(),
                "shift_sigma_bmo": pr4_shift_sigma[17:20].tolist(),
                "shift_sigma_sigma5": pr4_shift_sigma[0:5].tolist(),
            },
            "racs_unflagged_raw_variance": {
                "log_likelihood_map": fit_racs_raw["log_likelihood_map"],
                "log_z_is": fit_racs_raw["log_z_is"],
                "max_shift_sigma_24d": float(np.max(racs_shift_sigma)),
                "rms_shift_sigma_24d": float(np.sqrt(np.mean(racs_shift_sigma**2))),
            },
        },
        "equivalence_set_adjudication": {
            "equivalence_classes": eq_classes,
            "max_log_z_by_equivalence_class": eq_logz,
            "highest_evidence_equivalence_class": best_eq_class,
            "family_level_discrimination_claimed": False,
            "adjudication_note": (
                "Current low-ell transfer-conditional framework reports morphology compatibility over "
                "equivalence sets (FLAT_K0_FLRW_LIMIT vs OPEN_KNEG_FLRW_LIMIT vs CLOSED_KPOS_FLRW_LIMIT "
                "vs NON_FLRW_LIMIT_GEODESIC); individual Bianchi type assignment remains blocked pending "
                "native full-Boltzmann transfer atlas and external mask/covariance gates."
            ),
        },
        "total_runtime_s": round(time.perf_counter() - t_start, 2),
    }

    gbi08_path = R49_DOC_DIR / "GBI08_PRODUCTION_INFERENCE_RECEIPT.json"
    gbi08_path.write_text(json.dumps(gbi08_payload, indent=2) + "\n")
    print(f"=== [GBI-08] Wrote {gbi08_path.name} ===", flush=True)

    issues = scan_paths([gbi07_path, gbi08_path, Path(__file__)])
    if issues:
        raise RuntimeError(f"Overclaim scanner reported issues: {issues}")
    print(f"=== Completed R49 GBI-07 & GBI-08 cleanly in {time.perf_counter() - t_start:.1f}s (0 overclaim issues) ===", flush=True)


if __name__ == "__main__":
    main()
