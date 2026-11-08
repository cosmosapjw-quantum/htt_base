#!/usr/bin/env python3
"""Small NumPy verifier for the analytic R43 identifiability/readout claims.

This is a design-level synthetic check, not an observational likelihood.
Requires NumPy only. Run: python scripts/r43/verify_core_theorems.py
"""
from __future__ import annotations
import json
import numpy as np


def fibonacci_sphere(n: int) -> np.ndarray:
    i = np.arange(n, dtype=float)
    z = 1.0 - 2.0 * (i + 0.5) / n
    phi = 2.0 * np.pi * i / ((1.0 + np.sqrt(5.0)) / 2.0)
    r = np.sqrt(np.maximum(0.0, 1.0 - z * z))
    return np.column_stack((r * np.cos(phi), r * np.sin(phi), z))


def stf_basis() -> np.ndarray:
    """Orthonormal STF basis under Frobenius inner product."""
    q = np.zeros((5, 3, 3))
    q[0] = np.diag([1.0, -1.0, 0.0]) / np.sqrt(2.0)
    q[1] = np.diag([1.0, 1.0, -2.0]) / np.sqrt(6.0)
    q[2, 0, 1] = q[2, 1, 0] = 1.0 / np.sqrt(2.0)
    q[3, 0, 2] = q[3, 2, 0] = 1.0 / np.sqrt(2.0)
    q[4, 1, 2] = q[4, 2, 1] = 1.0 / np.sqrt(2.0)
    return q


def rank_after_nuisance_projection(jt: np.ndarray, jn: np.ndarray, cov: np.ndarray) -> tuple[int, np.ndarray]:
    """Rank of the efficient Fisher after whitening and nuisance projection."""
    l = np.linalg.cholesky(cov)
    x = np.linalg.solve(l, jt)
    b = np.linalg.solve(l, jn)
    p = b @ np.linalg.pinv(b)
    ieff = x.T @ (np.eye(x.shape[0]) - p) @ x
    ieff = 0.5 * (ieff + ieff.T)
    return int(np.linalg.matrix_rank(ieff, tol=1e-9)), ieff


def build_tomographic_design(tomography: bool, anchors: bool) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """17 physical + 14 nuisance coordinates; all response laws are mock functions."""
    z = np.array([0.02, 0.05, 0.10, 0.20, 0.35])
    nphys, nnuis = 17, 14
    rows_t, rows_n = [], []
    for zz in z:
        g_rm = 1.0 + (1.8 * zz if tomography else 0.0)
        g_sh = 1.0 - 0.4 * zz
        g_a = 1.0 + 0.6 * zz
        # Three-vector dipole channel: beta_RM + beta_MO + intrinsic dipole.
        for k in range(3):
            t, n = np.zeros(nphys), np.zeros(nnuis)
            t[k] = g_rm; t[3 + k] = 1.0
            n[k] = 1.0
            rows_t.append(t); rows_n.append(n)
        # STF shear channel: sigma_ab plus a five-component calibration nuisance.
        for k in range(5):
            t, n = np.zeros(nphys), np.zeros(nnuis)
            t[6 + k] = g_sh; n[3 + k] = 1.0
            rows_t.append(t); rows_n.append(n)
        # Curl channel: physical vorticity plus frame-spin nuisance.
        for k in range(3):
            t, n = np.zeros(nphys), np.zeros(nnuis)
            t[11 + k] = 1.0; n[8 + k] = 1.0
            rows_t.append(t); rows_n.append(n)
        # Polar-acceleration channel plus calibration nuisance.
        for k in range(3):
            t, n = np.zeros(nphys), np.zeros(nnuis)
            t[14 + k] = g_a; n[11 + k] = 1.0
            rows_t.append(t); rows_n.append(n)
    if anchors:
        # Independent synthetic beta_MO and frame-spin proxies. No real catalogue is implied.
        for offset in (3, 11):
            for k in range(3):
                t, n = np.zeros(nphys), np.zeros(nnuis)
                t[offset + k] = 1.0
                rows_t.append(t); rows_n.append(n)
    jt, jn = np.asarray(rows_t), np.asarray(rows_n)
    # Diagonal covariance isolates the structural-rank argument in this compact verifier.
    nobs = jt.shape[0]
    cov = np.eye(nobs)
    return jt, jn, cov


def hubble_design(n: int, hemisphere: bool = False) -> tuple[int, float]:
    e = fibonacci_sphere(n * (2 if hemisphere else 1))
    if hemisphere:
        e = e[e[:, 2] >= 0.0][:n]
    q = stf_basis()
    d = np.column_stack((np.ones(len(e)) / 3.0, -e, np.einsum("ni,kij,nj->nk", e, q, e)))
    return int(np.linalg.matrix_rank(d, tol=1e-10)), float(np.linalg.cond(d))


def main() -> None:
    cases = {}
    for name, tomo, anchor in (
        ("unanchored_tomographic", True, False),
        ("anchored_tomographic", True, True),
        ("unanchored_no_tomography", False, False),
    ):
        jt, jn, cov = build_tomographic_design(tomo, anchor)
        rank, _ = rank_after_nuisance_projection(jt, jn, cov)
        cases[name] = {"rank": rank, "nullity": 17 - rank}
    full = hubble_design(256, False)
    hemi = hubble_design(128, True)
    rng = np.random.default_rng(20261109)
    j = rng.normal(size=(250, 17))
    # A deterministic scalar compression; its Fisher is a rank-one contraction of raw Fisher.
    u = rng.normal(size=250); u /= np.linalg.norm(u)
    iy = j.T @ j
    it = np.outer(u @ j, u @ j)
    eigmin = float(np.linalg.eigvalsh(iy - it).min())
    # Fixed Gaussian family: posterior mean/covariance recover the likelihood score statistic.
    x = rng.normal(size=(120, 4)); y = rng.normal(size=120)
    vprior = np.diag([1.0, 0.8, 0.6, 0.4])
    v = np.linalg.inv(np.linalg.inv(vprior) + x.T @ x)
    m = v @ x.T @ y
    score_data = x.T @ y
    score_from_posterior = np.linalg.solve(v, m)
    suff_resid = float(np.linalg.norm(score_data - score_from_posterior) / max(1.0, np.linalg.norm(score_data)))
    out = {
        "scope": "synthetic structural-design verifier; not observational and not a full benchmark rerun",
        "identifiability_rank": cases,
        "directional_hubble": {"full_sky_rank_condition": full, "hemisphere_rank_condition": hemi},
        "data_processing": {"raw_fisher_rank": int(np.linalg.matrix_rank(iy)), "scalar_compressed_fisher_rank": int(np.linalg.matrix_rank(it)), "min_eigenvalue_raw_minus_compressed": eigmin},
        "fixed_gaussian_posterior_score_relative_residual": suff_resid,
    }
    assert cases["unanchored_tomographic"] == {"rank": 11, "nullity": 6}
    assert cases["anchored_tomographic"] == {"rank": 17, "nullity": 0}
    assert cases["unanchored_no_tomography"] == {"rank": 8, "nullity": 9}
    assert full[0] == 9 and hemi[0] == 9
    assert eigmin >= -1e-9 and suff_resid < 1e-12
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
