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
