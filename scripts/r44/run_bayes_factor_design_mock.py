#!/usr/bin/env python3
"""R44 mock: Bayes-factor sufficiency and nuisance-projected shell design.

All data and response functions are synthetic. This script tests exact statistical
claims under declared Gaussian families; it is not an observational cosmology analysis.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
from scipy.linalg import cholesky, null_space, solve_triangular
from scipy.optimize import minimize
from scipy.stats import norm

SEED = 20261109
N_THETA = 17
N_ETA = 14
THETA_STD = np.array([4e-4] * 5 + [2e-4] * 3 + [2e-4] * 3 + [8e-4] * 3 + [8e-4] * 3)
ETA_STD = np.array([8e-4] * 3 + [2e-4] * 5 + [2e-4] * 3 + [2e-4] * 3)
N_SHELLS = 5


def _ar_cov(n_shells: int, n_comp: int, sigma: float, rho: float) -> np.ndarray:
    idx = np.arange(n_shells)
    corr = rho ** np.abs(idx[:, None] - idx[None, :])
    return sigma**2 * np.kron(corr, np.eye(n_comp)) + (0.25 * sigma) ** 2 * np.kron(np.ones((n_shells, n_shells)), np.eye(n_comp))


def _block_diag(mats: list[np.ndarray]) -> np.ndarray:
    n = sum(m.shape[0] for m in mats)
    out = np.zeros((n, n))
    i = 0
    for m in mats:
        j = i + m.shape[0]
        out[i:j, i:j] = m
        i = j
    return out


def build_design(anchors: bool = True, tomography: bool = True):
    """R43 shared 17D/14D design snapshot, vendored here for standalone R44 replay."""
    z = np.array([0.02, 0.05, 0.10, 0.20, 0.35], dtype=float)
    g_rm = (1.0 + 1.8 * z) if tomography else np.ones_like(z)
    g_sigma = 1.0 / (1.0 + 2.0 * z)
    g_A = 0.6 + 1.2 * z
    blocks, nuis, covs, labels = [], [], [], []
    groups, channel_rows, holdout = {}, {}, []
    offset = 0

    def add_shell_block(name: str, n_comp: int, sigma: float, rho: float,
                        theta_design: np.ndarray, eta_design: np.ndarray) -> None:
        nonlocal offset
        n = N_SHELLS * n_comp
        rows = np.arange(offset, offset + n)
        blocks.append(theta_design)
        nuis.append(eta_design)
        covs.append(_ar_cov(N_SHELLS, n_comp, sigma, rho))
        channel_rows[name] = rows
        groups[name] = rows
        labels.extend([f"{name}:z{j}:c{k}" for j in range(N_SHELLS) for k in range(n_comp)])
        holdout.extend(rows[-n_comp:].tolist())
        offset += n

    I3, I5 = np.eye(3), np.eye(5)
    dip_x, dip_z = np.zeros((N_SHELLS * 3, N_THETA)), np.zeros((N_SHELLS * 3, N_ETA))
    for s in range(N_SHELLS):
        rr = slice(3 * s, 3 * (s + 1))
        dip_x[rr, 11:14] = g_rm[s] * I3
        dip_x[rr, 14:17] = I3
        dip_z[rr, 0:3] = I3
    add_shell_block("dipole", 3, 4.5e-4, 0.35, dip_x, dip_z)

    sh_x, sh_z = np.zeros((N_SHELLS * 5, N_THETA)), np.zeros((N_SHELLS * 5, N_ETA))
    for s in range(N_SHELLS):
        rr = slice(5 * s, 5 * (s + 1))
        sh_x[rr, 0:5] = g_sigma[s] * I5
        sh_z[rr, 3:8] = I5
    add_shell_block("shear", 5, 1.6e-4, 0.30, sh_x, sh_z)

    cu_x, cu_z = np.zeros((N_SHELLS * 3, N_THETA)), np.zeros((N_SHELLS * 3, N_ETA))
    for s in range(N_SHELLS):
        rr = slice(3 * s, 3 * (s + 1))
        cu_x[rr, 5:8] = I3
        cu_z[rr, 8:11] = I3
    add_shell_block("curl", 3, 1.2e-4, 0.40, cu_x, cu_z)

    ac_x, ac_z = np.zeros((N_SHELLS * 3, N_THETA)), np.zeros((N_SHELLS * 3, N_ETA))
    for s in range(N_SHELLS):
        rr = slice(3 * s, 3 * (s + 1))
        ac_x[rr, 8:11] = g_A[s] * I3
        ac_z[rr, 11:14] = I3
    add_shell_block("acceleration", 3, 1.8e-4, 0.30, ac_x, ac_z)

    if anchors:
        for name, xmat, zmat, sigma in (
            ("beta_MO_anchor", np.pad(I3, ((0, 0), (14, 0))), np.zeros((3, N_ETA)), 2.0e-4),
            ("frame_anchor", np.zeros((3, N_THETA)), np.pad(I3, ((0, 0), (8, 3)), mode="constant"), 3.0e-5),
        ):
            rows = np.arange(offset, offset + 3)
            blocks.append(xmat); nuis.append(zmat); covs.append(sigma**2 * np.eye(3))
            labels.extend([f"{name}:c{k}" for k in range(3)])
            groups[name] = rows; channel_rows[name] = rows; offset += 3
    return np.vstack(blocks), np.vstack(nuis), _block_diag(covs), labels, np.array(holdout, int), groups, channel_rows
MODEL_COLUMNS = {
    "M0_NULL": [],
    "M1_LOCAL_BOOST": [14, 15, 16],
    "M2_GLOBAL_TILT_PLUS_BOOST": [11, 12, 13, 14, 15, 16],
    "M3_SHEAR_PROXY_PLUS_BOOST": [0, 1, 2, 3, 4, 14, 15, 16],
    "M4_FULL_KINEMATIC": list(range(17)),
}


def _solve_cov(C: np.ndarray, B: np.ndarray) -> np.ndarray:
    L = cholesky(C, lower=True, check_finite=False)
    return solve_triangular(L.T, solve_triangular(L, B, lower=True, check_finite=False),
                            lower=False, check_finite=False)


def _logdet_spd(C: np.ndarray) -> float:
    L = cholesky(C, lower=True, check_finite=False)
    return float(2.0 * np.log(np.diag(L)).sum())


def nuisance_integrated_covariance(Z: np.ndarray, C: np.ndarray) -> np.ndarray:
    return C + (Z * ETA_STD[None, :] ** 2) @ Z.T


def reference_posterior(y: np.ndarray, X: np.ndarray, Cbar: np.ndarray,
                         prior_std: np.ndarray = THETA_STD) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return m,V,q,G for one fixed full-chart Gaussian reference prior."""
    Ciy = _solve_cov(Cbar, y)
    CiX = _solve_cov(Cbar, X)
    G = X.T @ CiX
    q = X.T @ Ciy
    precision = np.diag(1.0 / prior_std**2) + G
    V = np.linalg.inv(precision)
    V = 0.5 * (V + V.T)
    m = V @ q
    return m, V, q, G

def log_bf_raw(y: np.ndarray, Cbar: np.ndarray, X: np.ndarray,
               cols: list[int], prior_std: np.ndarray = THETA_STD) -> float:
    """Exact log BF against the common zero-mean base model."""
    if not cols:
        return 0.0
    Xm = X[:, cols]
    lm = prior_std[cols]
    Sm = Cbar + (Xm * lm[None, :] ** 2) @ Xm.T
    return float(-0.5 * (_logdet_spd(Sm) - _logdet_spd(Cbar))
                 + 0.5 * (y @ (_solve_cov(Cbar, y) - _solve_cov(Sm, y))))


def log_bf_from_score(q: np.ndarray, G: np.ndarray, cols: list[int],
                      prior_std: np.ndarray = THETA_STD) -> float:
    """Exact same BF using q=X' C^-1 y and fixed design Gram matrix G."""
    if not cols:
        return 0.0
    Gm = G[np.ix_(cols, cols)]
    qm = q[cols]
    lm = prior_std[cols]
    A = np.diag(1.0 / lm**2) + Gm
    sign, logdet_ratio = np.linalg.slogdet(np.eye(len(cols)) + np.diag(lm**2) @ Gm)
    if sign <= 0:
        raise np.linalg.LinAlgError("non-positive model evidence determinant")
    return float(-0.5 * logdet_ratio + 0.5 * qm @ np.linalg.solve(A, qm))


def log_bf_from_reference_posterior(m: np.ndarray, V: np.ndarray, G: np.ndarray,
                                    cols: list[int], prior_std: np.ndarray = THETA_STD,
                                    prior_mean: np.ndarray | None = None) -> float:
    """Reconstruct q from the complete fixed Gaussian posterior, then the BF."""
    b = np.zeros_like(m) if prior_mean is None else np.asarray(prior_mean, float)
    q = np.linalg.solve(V, m) - np.linalg.solve(np.diag(prior_std**2), b)
    return log_bf_from_score(q, G, cols, prior_std)


def common_covariance_model_experiment(seed: int = SEED, n_rep: int = 250) -> dict[str, Any]:
    """Compare raw, score and posterior evidence, then falsify q under covariance shift."""
    X, Z, C, *_ = build_design(anchors=True, tomography=True)
    Cbar = nuisance_integrated_covariance(Z, C)
    rng = np.random.default_rng(seed)
    theta_true = np.zeros(17)
    theta_true[0:5] = np.array([0.8, -0.5, 0.35, 0.2, -0.15]) * 1.4e-4
    theta_true[11:14] = np.array([0.7, -0.4, 0.25]) * 6.5e-4
    theta_true[14:17] = np.array([-0.8, 0.45, 0.2]) * 7.0e-4
    m_abs = {k: [] for k in MODEL_COLUMNS}
    max_score_error = 0.0
    max_posterior_error = 0.0
    for _ in range(n_rep):
        y = X @ theta_true + rng.multivariate_normal(np.zeros(len(Cbar)), Cbar)
        m, V, q, G = reference_posterior(y, X, Cbar)
        for name, cols in MODEL_COLUMNS.items():
            raw = log_bf_raw(y, Cbar, X, cols)
            from_q = log_bf_from_score(q, G, cols)
            from_post = log_bf_from_reference_posterior(m, V, G, cols)
            max_score_error = max(max_score_error, abs(raw - from_q))
            max_posterior_error = max(max_posterior_error, abs(raw - from_post))
            m_abs[name].append(abs(raw - from_post))

    # Two observations with the same common-covariance score q but different
    # likelihood under a competing model that changes covariance.
    A = X.T @ _solve_cov(Cbar, np.eye(len(Cbar)))
    N = null_space(A)
    if N.shape[1] == 0:
        raise RuntimeError("mock design unexpectedly has no score-null data direction")
    h = N[:, 0]
    h = h / np.sqrt(h @ _solve_cov(Cbar, h))
    # Align the alternative covariance mode with a data direction invisible to q.
    v = h.copy()
    tau2 = 0.8
    C_alt = Cbar + tau2 * np.outer(v, v)
    def covariance_log_bf(y: np.ndarray) -> float:
        return float(-0.5 * (_logdet_spd(C_alt) - _logdet_spd(Cbar))
                     + 0.5 * y @ (_solve_cov(Cbar, y) - _solve_cov(C_alt, y)))
    y_zero = np.zeros(len(Cbar))
    y_null = h
    q_zero = X.T @ _solve_cov(Cbar, y_zero)
    q_null = X.T @ _solve_cov(Cbar, y_null)
    cov_bf_zero = covariance_log_bf(y_zero)
    cov_bf_null = covariance_log_bf(y_null)

    return {
        "n_replications": n_rep,
        "n_data": int(len(Cbar)),
        "n_physical_chart": int(X.shape[1]),
        "common_covariance_model_family": "same nuisance-integrated Cbar; all alternatives are submodels of the fixed 17D chart X; independent zero-mean Gaussian coefficient priors with fixed known variances",
        "max_abs_log_bf_error_raw_vs_score": max_score_error,
        "max_abs_log_bf_error_raw_vs_complete_posterior_mV": max_posterior_error,
        "mean_abs_log_bf_error_by_model": {k: float(np.mean(v)) for k, v in m_abs.items()},
        "mean_only_is_also_exact_when_reference_V_is_fixed": True,
        "proof_identity": "q = V^{-1} m - B^{-1} b; here b=0, B=diag(THETA_STD^2), V is fixed by X,Cbar,B and independent of y",
        "model_dependent_covariance_counterexample": {
            "same_common_score_max_abs_difference": float(np.max(np.abs(q_zero - q_null))),
            "common_score_norm": float(np.linalg.norm(q_zero)),
            "alternative_covariance_log_bf_at_zero": cov_bf_zero,
            "alternative_covariance_log_bf_at_score_null_vector": cov_bf_null,
            "log_bf_difference_despite_same_q": abs(cov_bf_zero - cov_bf_null),
            "interpretation": "A mean-score summary for fixed Cbar is not sufficient when a competitor changes covariance; the residual quadratic form carries model-discriminating information."
        }
    }


def norm_sufficiency_counterexample() -> dict[str, Any]:
    """Equal posterior-mean norms can have different BFs under anisotropic geometry."""
    tau2 = 1.0
    def logbf(y: np.ndarray, sig2: np.ndarray) -> float:
        C = np.diag(sig2)
        S = C + tau2 * np.eye(3)
        return float(-0.5 * (np.linalg.slogdet(S)[1] - np.linalg.slogdet(C)[1])
                     + 0.5 * y @ (np.linalg.solve(C, y) - np.linalg.solve(S, y)))
    def posterior_mean(y: np.ndarray, sig2: np.ndarray) -> np.ndarray:
        return tau2 / (tau2 + sig2) * y
    # Isotropic case: rotational invariance makes the norm sufficient for this
    # particular spherical-prior, common-covariance binary comparison.
    sig_iso = np.array([1.0, 1.0, 1.0])
    yx, yz = np.array([1.2, 0.0, 0.0]), np.array([0.0, 0.0, 1.2])
    iso = {"posterior_mean_norms": [float(np.linalg.norm(posterior_mean(y, sig_iso))) for y in (yx, yz)],
           "log_bfs": [logbf(y, sig_iso) for y in (yx, yz)]}
    # An anisotropic response/noise geometry breaks rotational invariance.
    sig_aniso = np.array([0.35, 1.0, 2.8])
    yx_a = np.array([0.72, 0.0, 0.0])
    # Choose z amplitude so the posterior mean norm is the same.
    amp_z = float(np.linalg.norm(posterior_mean(yx_a, sig_aniso)) /
                  (tau2 / (tau2 + sig_aniso[2])))
    yz_a = np.array([0.0, 0.0, amp_z])
    aniso_norms = [float(np.linalg.norm(posterior_mean(y, sig_aniso))) for y in (yx_a, yz_a)]
    aniso_bfs = [logbf(y, sig_aniso) for y in (yx_a, yz_a)]
    return {
        "isotropic_control": iso,
        "anisotropic_equal_norm_pair": {
            "noise_variances": sig_aniso.tolist(),
            "data_vectors": [yx_a.tolist(), yz_a.tolist()],
            "posterior_mean_norms": aniso_norms,
            "log_bfs": aniso_bfs,
            "absolute_log_bf_difference": abs(aniso_bfs[0] - aniso_bfs[1]),
        },
        "interpretation": "A scalar vector norm can be sufficient only under a symmetry-compatible model/prior/metric. Anisotropic survey geometry generally makes direction decision-relevant."
    }

def beta_mo_readout_counterexample(seed: int = SEED) -> dict[str, Any]:
    """Same beta_MO vector readout, different M1-vs-M2 evidence due to beta_RM."""
    X, Z, C, *_ = build_design(anchors=True, tomography=True)
    Cbar = nuisance_integrated_covariance(Z, C)
    CinvX = _solve_cov(Cbar, X)
    G = X.T @ CinvX
    V = np.linalg.inv(np.diag(1.0 / THETA_STD**2) + G)
    # Preserve only the beta_MO posterior mean vector, while changing beta_RM score.
    rows = V[14:17, :] @ X.T @ _solve_cov(Cbar, np.eye(len(Cbar)))
    N = null_space(rows)
    if N.shape[1] == 0:
        raise RuntimeError("no null direction for beta_MO-only readout counterexample")
    # Choose the null-space direction most visible to the beta_RM score.
    target = _solve_cov(Cbar, X[:, 11:14])
    coeff = N.T @ target
    h = N @ coeff[:, int(np.argmax(np.linalg.norm(coeff, axis=0)))]
    h /= np.sqrt(h @ _solve_cov(Cbar, h))
    y0 = np.zeros(len(Cbar))
    y1 = h
    m0, V0, q0, G0 = reference_posterior(y0, X, Cbar)
    m1, V1, q1, G1 = reference_posterior(y1, X, Cbar)
    mo_mean_gap = float(np.linalg.norm(m0[14:17] - m1[14:17]))
    mo_score_gap = float(np.linalg.norm(q0[14:17] - q1[14:17]))
    rm_score_gap = float(np.linalg.norm(q0[11:14] - q1[11:14]))
    bf_m1_gap = abs(log_bf_from_score(q0, G0, MODEL_COLUMNS["M1_LOCAL_BOOST"]) -
                    log_bf_from_score(q1, G1, MODEL_COLUMNS["M1_LOCAL_BOOST"]))
    bf_m2_gap = abs(log_bf_from_score(q0, G0, MODEL_COLUMNS["M2_GLOBAL_TILT_PLUS_BOOST"]) -
                    log_bf_from_score(q1, G1, MODEL_COLUMNS["M2_GLOBAL_TILT_PLUS_BOOST"]))
    return {
        "beta_MO_posterior_mean_vector_gap": mo_mean_gap,
        "beta_MO_score_gap": mo_score_gap,
        "beta_RM_score_gap": rm_score_gap,
        "local_boost_M1_log_bf_gap": bf_m1_gap,
        "global_tilt_plus_boost_M2_log_bf_gap": bf_m2_gap,
        "interpretation": "The beta_MO-only posterior mean vector (and its norm) is identical in two data sets, but the Bayes factor for a model that also includes beta_RM changes. It is not sufficient for M1-vs-M2 model comparison."
    }

def binary_gaussian_data_processing() -> dict[str, Any]:
    """Exact Gaussian KL/TV contraction for a common deterministic linear map."""
    from scipy.stats import norm as normal_dist
    delta = np.array([0.8, -0.6, 0.4, 0.3])
    C = np.diag([1.0, 1.5, 0.8, 2.0])
    # Retain only the first coordinate, a strict lossy compression.
    A = np.array([[1.0], [0.0], [0.0], [0.0]])
    d2_raw = float(delta @ np.linalg.solve(C, delta))
    Cr = A.T @ C @ A
    dr = A.T @ delta
    d2_comp = float(dr @ np.linalg.solve(Cr, dr))
    tv_raw = float(2.0 * normal_dist.cdf(np.sqrt(d2_raw) / 2.0) - 1.0)
    tv_comp = float(2.0 * normal_dist.cdf(np.sqrt(d2_comp) / 2.0) - 1.0)
    return {
        "family": "P0=N(0,C), P1=N(delta,C), T(y)=A^T y",
        "raw_kl_P1_P0": 0.5 * d2_raw,
        "compressed_kl_P1T_P0T": 0.5 * d2_comp,
        "raw_total_variation": tv_raw,
        "compressed_total_variation": tv_comp,
        "kl_contraction_ratio": (0.5 * d2_comp) / (0.5 * d2_raw),
        "tv_contraction_ratio": tv_comp / tv_raw,
        "scope": "exact equal-covariance Gaussian binary experiment; for general deterministic T, the KL and TV inequalities follow from data processing"
    }


def _dipole_design(z: np.ndarray, counts: np.ndarray, n_anchor: float,
                   sigma_stat: float = 1.0e-3, sigma_cv: float = 1.8e-4,
                   corr_length: float = 0.22, anchor_sigma: float = 3.5e-4) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """One-component redshift tomography with beta_RM, beta_MO and nuisance modes.

    Mean: g(z) beta_RM + beta_MO + d_intrinsic + c_z z.
    Independent low-z anchor: beta_MO + noise.
    Response g(z)=z/(z+0.12) is deliberately synthetic, not a physical transfer.
    """
    z = np.asarray(z, float)
    counts = np.asarray(counts, float)
    if np.any(counts <= 0) or n_anchor <= 0:
        raise ValueError("all shell and anchor allocations must be positive")
    g = z / (z + 0.12)
    D = np.column_stack([g, np.ones_like(z)])
    N = np.column_stack([np.ones_like(z), z])
    R = np.exp(-np.abs(z[:, None] - z[None, :]) / corr_length)
    Cshell = np.diag(sigma_stat**2 / counts) + sigma_cv**2 * R
    # Anchor contributes to beta_MO and has no intrinsic-dipole or calibration response.
    D = np.vstack([D, [0.0, 1.0]])
    N = np.vstack([N, [0.0, 0.0]])
    C = np.zeros((len(z) + 1, len(z) + 1))
    C[:-1, :-1] = Cshell
    C[-1, -1] = anchor_sigma**2 / n_anchor
    return D, N, C


def _efficient_information(D: np.ndarray, N: np.ndarray, C: np.ndarray) -> tuple[np.ndarray, int]:
    CiD = _solve_cov(C, D)
    CiN = _solve_cov(C, N)
    Ftt = D.T @ CiD
    Ftn = D.T @ CiN
    Fnn = N.T @ CiN
    Ieff = Ftt - Ftn @ np.linalg.pinv(Fnn, rcond=1e-12) @ Ftn.T
    Ieff = 0.5 * (Ieff + Ieff.T)
    rank = int(np.linalg.matrix_rank(Ieff, tol=max(1.0, np.linalg.norm(Ieff, 2)) * 1e-10))
    return Ieff, rank


def _design_metrics(z: np.ndarray, counts: np.ndarray, n_anchor: float) -> dict[str, Any]:
    D, N, C = _dipole_design(z, counts, n_anchor)
    Ieff, rank = _efficient_information(D, N, C)
    c = np.array([1.0, -1.0])  # target beta_RM - beta_MO
    if rank < 2:
        return {"rank": rank, "c_variance": float("inf"), "logdet": float("-inf"), "I_eff": Ieff}
    cvar = float(c @ np.linalg.solve(Ieff, c))
    sign, ld = np.linalg.slogdet(Ieff)
    return {"rank": rank, "c_variance": cvar, "c_sigma": float(np.sqrt(cvar)),
            "logdet": float(ld if sign > 0 else -np.inf), "I_eff": Ieff}


def optimize_shell_design(seed: int = SEED, n_total_cost: int = 6000) -> dict[str, Any]:
    """Compare uniform, D-optimal and c-optimal allocations with correlated shells."""
    z = np.array([0.015, 0.035, 0.07, 0.13, 0.24, 0.42, 0.72, 1.10])
    nbin = len(z)
    anchor_cost = 4.0
    min_shell = 40.0
    min_anchor = 25.0
    # x = [8 shell counts, n_anchor], with weighted survey cost fixed.
    def unpack(x: np.ndarray) -> tuple[np.ndarray, float]:
        return x[:nbin], float(x[-1])
    def objective_c(x: np.ndarray) -> float:
        counts, na = unpack(x)
        return _design_metrics(z, counts, na)["c_variance"]
    def objective_d(x: np.ndarray) -> float:
        counts, na = unpack(x)
        ld = _design_metrics(z, counts, na)["logdet"]
        return -ld if np.isfinite(ld) else 1e12
    constraint = {"type": "eq", "fun": lambda x: float(np.sum(x[:nbin]) + anchor_cost * x[-1] - n_total_cost)}
    bounds = [(min_shell, n_total_cost) for _ in range(nbin)] + [(min_anchor, n_total_cost / anchor_cost)]
    x0 = np.array([(n_total_cost - anchor_cost * 100.0) / nbin] * nbin + [100.0])
    uniform = x0.copy()
    # Multi-start SLSQP; use deterministic starting points, record optimizer state.
    starts = [x0]
    for weights in (np.array([.04,.06,.10,.14,.18,.18,.16,.14]),
                    np.array([.14,.14,.14,.14,.12,.12,.10,.10])):
        na = 120.0
        counts = weights / weights.sum() * (n_total_cost - anchor_cost * na)
        starts.append(np.r_[counts, na])
    def multi_start(fun: Any) -> Any:
        sols = []
        for start in starts:
            res = minimize(fun, start, method="SLSQP", bounds=bounds, constraints=[constraint],
                           options={"maxiter": 1200, "ftol": 1e-10})
            if res.success and np.isfinite(res.fun):
                sols.append(res)
        if not sols:
            raise RuntimeError("optimal-design solver did not converge from any deterministic start")
        return min(sols, key=lambda r: r.fun)
    res_c = multi_start(objective_c)
    res_d = multi_start(objective_d)
    # Baselines: uniform with anchor, and no anchor (unidentifiable contrast).
    c0, a0 = unpack(uniform)
    md0 = _design_metrics(z, c0, a0)
    cm, am = unpack(res_c.x)
    dm = _design_metrics(z, cm, am)
    cd, ad = unpack(res_d.x)
    dd = _design_metrics(z, cd, ad)
    no_anchor = _design_metrics(z, np.full(nbin, n_total_cost / nbin), 1e-20)
    return {
        "redshift_shells": z.tolist(),
        "response": "g(z)=z/(z+0.12), synthetic only",
        "mean_model": "g(z) beta_RM + beta_MO + d_intrinsic + c_z*z; independent low-z anchor measures beta_MO",
        "covariance": "diag(sigma_stat^2/n_s) + sigma_cv^2 exp(-|z_s-z_s'|/L_corr), plus independent anchor variance sigma_anchor^2/n_anchor",
        "resource_budget": {"total_cost": n_total_cost, "anchor_cost_multiplier": anchor_cost,
                            "minimum_per_shell": min_shell, "minimum_anchor_count": min_anchor},
        "target": "delta = beta_RM - beta_MO",
        "allocations": {
            "uniform": {"shell_counts": c0.tolist(), "anchor_count": a0,
                        "target_variance": md0["c_variance"], "target_sigma": md0.get("c_sigma"), "logdet_Ieff": md0["logdet"]},
            "c_optimal": {"shell_counts": cm.tolist(), "anchor_count": am,
                          "target_variance": dm["c_variance"], "target_sigma": dm.get("c_sigma"), "logdet_Ieff": dm["logdet"],
                          "optimizer_success": bool(res_c.success), "optimizer_message": str(res_c.message)},
            "d_optimal": {"shell_counts": cd.tolist(), "anchor_count": ad,
                          "target_variance": dd["c_variance"], "target_sigma": dd.get("c_sigma"), "logdet_Ieff": dd["logdet"],
                          "optimizer_success": bool(res_d.success), "optimizer_message": str(res_d.message)},
            "no_independent_beta_MO_anchor": {"rank": no_anchor["rank"], "target_variance": None,
                                               "target_status": "UNIDENTIFIABLE",
                                               "interpretation": "beta_MO shares a constant-redshift direction with intrinsic dipole; beta_RM-beta_MO is not data-identifiable"}
        },
        "relative_c_variance_reduction_c_optimal_vs_uniform": float(1.0 - dm["c_variance"] / md0["c_variance"]),
        "relative_c_variance_reduction_c_optimal_vs_d_optimal": float(1.0 - dm["c_variance"] / dd["c_variance"]),
        "scope": "one-dimensional dipole contrast design; response and covariance are synthetic; it is a method-design experiment, not an actual survey forecast"
    }


def run_design_calibration(design: dict[str, Any], seed: int = SEED, n_rep: int = 400) -> dict[str, Any]:
    z = np.asarray(design["redshift_shells"], float)
    rng = np.random.default_rng(seed)
    truth = np.array([6.0e-4, -3.5e-4])
    nuisance_truth = np.array([2.0e-4, -1.0e-4])
    out = {}
    for name in ("uniform", "c_optimal", "d_optimal"):
        alloc = design["allocations"][name]
        counts = np.asarray(alloc["shell_counts"], float)
        na = float(alloc["anchor_count"])
        D, N, C = _dipole_design(z, counts, na)
        J = np.column_stack([D, N])
        CiJ = _solve_cov(C, J)
        F = J.T @ CiJ
        V = np.linalg.inv(F)
        V = 0.5 * (V + V.T)
        A = V @ CiJ.T
        mu = J @ np.r_[truth, nuisance_truth]
        L = cholesky(C, lower=True)
        estimates = np.empty((n_rep, 2))
        for i in range(n_rep):
            y = mu + L @ rng.normal(size=len(mu))
            estimates[i] = (A @ y)[:2]
        contrast = estimates[:, 0] - estimates[:, 1]
        truth_c = truth[0] - truth[1]
        c = np.array([1.0, -1.0])
        sd = float(np.sqrt(c @ V[:2, :2] @ c))
        cover = float(np.mean(np.abs(contrast - truth_c) <= norm.ppf(0.975) * sd))
        out[name] = {"replications": n_rep, "truth_delta": float(truth_c),
                     "analytic_sd_delta": sd, "empirical_rmse_delta": float(np.sqrt(np.mean((contrast - truth_c)**2))),
                     "empirical_bias_delta": float(np.mean(contrast - truth_c)),
                     "coverage_95": cover, "coverage_mcse": float(np.sqrt(0.95 * 0.05 / n_rep))}
    return out


def run_experiment(seed: int = SEED, n_rep: int = 250, n_design_rep: int = 400) -> dict[str, Any]:
    common = common_covariance_model_experiment(seed, n_rep)
    norm_demo = norm_sufficiency_counterexample()
    beta_mo_only = beta_mo_readout_counterexample(seed)
    dpi = binary_gaussian_data_processing()
    design = optimize_shell_design(seed)
    design_cal = run_design_calibration(design, seed + 1, n_design_rep)
    return {
        "schema": "htt.r44_bayes_factor_and_design_mock/1",
        "seed": seed,
        "classification": "SYNTHETIC_STATISTICAL_THEORY_EXPERIMENT_NOT_OBSERVATIONAL",
        "research_scope": "tensorized posterior-pushforward T=(x,Q,Pi,F,G_F) versus physical generative theories/readout methods; no scalar-versus-tensor five-variable benchmark",
        "exact_common_covariance_bayes_factor_sufficiency": common,
        "scalar_norm_sufficiency_scope_test": norm_demo,
        "beta_MO_only_readout_counterexample": beta_mo_only,
        "binary_gaussian_data_processing": dpi,
        "c_optimal_redshift_shell_design": design,
        "design_mock_calibration": design_cal,
        "main_conclusions": [
            "For a common known covariance and candidates nested in one fixed linear chart, q=X^T C^-1(y-mu) is a common sufficient statistic for all candidate-model Bayes factors.",
            "The complete Gaussian reference posterior mean/covariance recovers q exactly; when V is fixed, its mean alone is an invertible encoding of q.",
            "This exact result does not extend automatically to model-dependent covariance, selection, window functions, or model-dependent summary maps.",
            "A scalar norm is sufficient only under additional rotational symmetry of the prior and observation metric; anisotropic geometry can make direction essential.",
            "The c-optimal redshift/anchor allocation for beta_RM-beta_MO need not coincide with a D-optimal allocation maximizing total information volume."
        ],
        "limitations": [
            "No Planck, Gaia, Quaia, NVSS, Pantheon, DESI or other real survey data are used.",
            "The redshift response g(z)=z/(z+0.12) is a synthetic design function, not a derived physical transfer kernel.",
            "The mock is linear-Gaussian and local; it does not establish global identifiability or Bianchi family identification.",
            "The five readout families remain a joint posterior push-forward and must not be multiplied as independent likelihood factors.",
            "For actual model comparison, all competitors must use the same raw observation contract or the exact model-dependent covariance/selection likelihood; source-specific transfers remain unimplemented here."
        ]
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--replications", type=int, default=250)
    p.add_argument("--design-replications", type=int, default=400)
    p.add_argument("--output", type=Path, default=Path("R44_MOCK_RESULTS.json"))
    args = p.parse_args()
    result = run_experiment(args.seed, args.replications, args.design_replications)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "max_logbf_error": result["exact_common_covariance_bayes_factor_sufficiency"]["max_abs_log_bf_error_raw_vs_complete_posterior_mV"],
        "covariance_counterexample_delta": result["exact_common_covariance_bayes_factor_sufficiency"]["model_dependent_covariance_counterexample"]["log_bf_difference_despite_same_q"],
        "c_optimal_variance_reduction_vs_uniform": result["c_optimal_redshift_shell_design"]["relative_c_variance_reduction_c_optimal_vs_uniform"],
        "c_optimal_variance_reduction_vs_d_optimal": result["c_optimal_redshift_shell_design"]["relative_c_variance_reduction_c_optimal_vs_d_optimal"],
    }, indent=2))


if __name__ == "__main__":
    main()
