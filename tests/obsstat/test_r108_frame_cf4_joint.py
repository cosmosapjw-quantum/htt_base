"""R108 H05 first step: synthetic checks of the bulk / expansion-dipole responses, GLS and the Schur holdout."""
from __future__ import annotations

import numpy as np
import pytest

from scripts.r108.frame_cf4_joint import (
    C_KMS, DIP_SLOTS, bulk_rows, dlnf_dz, f_curv, free_dipole_design, gls, hdipole_rows, nuisance_design, schur_predict,
)

CENTERS = (0.025, 0.04, 0.06, 0.08)
WIDTH = 0.012


def _stf(n):
    x, y, z = n.T
    s2, s6 = np.sqrt(2), np.sqrt(6)
    return np.column_stack(((x * x - y * y) / s2, (x * x + y * y - 2 * z * z) / s6, 2 * x * y / s2, 2 * x * z / s2, 2 * y * z / s2))


def _operator(n, z, sig):
    X = np.column_stack((np.ones(len(n)), n, _stf(n)))
    rows = []
    for c in CENTERS:
        w = np.exp(-0.5 * ((z - c) / WIDTH) ** 2) / sig ** 2
        rows.append(np.linalg.solve(X.T @ (w[:, None] * X), (X * w[:, None]).T))
    return np.vstack(rows)


def _sample(N=6000, seed=11):
    rng = np.random.default_rng(seed)
    n = rng.normal(size=(N, 3)); n /= np.linalg.norm(n, axis=1)[:, None]
    z = rng.uniform(0.01, 0.10, N)
    sig = np.full(N, 0.1)
    return n, z, sig, _operator(n, z, sig)


def test_curvature_factor_matches_readme_note6_derivative():
    z = np.linspace(0.01, 0.1, 50)
    h = 1e-6
    num = (np.log(f_curv(z + h)) - np.log(f_curv(z - h))) / (2 * h)
    assert np.max(abs(num - dlnf_dz(z))) < 1e-8


def test_bulk_and_expansion_rows_are_exact_linearisations():
    rng = np.random.default_rng(1)
    n = rng.normal(size=(200, 3)); n /= np.linalg.norm(n, axis=1)[:, None]
    z = rng.uniform(0.01, 0.1, 200)
    y = lambda zz: np.log(f_curv(zz) * zz)
    B = np.array([0.3, -0.2, 0.1])  # km/s, small enough that the second order is < 1e-8
    zB = (1 + z) * (1 + n @ B / C_KMS) - 1
    assert np.max(abs((y(zB) - y(z)) - bulk_rows(z, n) @ B)) < 1e-7
    hvec = np.array([1e-4, -2e-4, 5e-5])
    zH = z * (1 + n @ hvec)
    assert np.max(abs((y(zH) - y(z)) - hdipole_rows(z, n) @ hvec)) < 1e-7


def test_gls_recovers_injected_bulk_and_expansion_dipole():
    n, z, sig, A = _sample()
    P = nuisance_design()
    JB, JH = A @ bulk_rows(z, n), A @ hdipole_rows(z, n)
    B = np.array([250.0, -120.0, 40.0]); h = np.array([0.01, -0.02, 0.015])
    eta = np.random.default_rng(2).normal(size=P.shape[1]) * 0.01
    theta = P @ eta + JB @ B + JH @ h
    C = (A * sig[None, :] ** 2) @ A.T
    beta, cov, chi2 = gls(theta, np.hstack([P, JB, JH]), C)
    k = P.shape[1]
    assert np.allclose(beta[k:k + 3], B, rtol=0, atol=1e-6)
    assert np.allclose(beta[k + 3:k + 6], h, rtol=0, atol=1e-10)
    assert chi2 < 1e-12
    # a free per-window dipole model is saturated on the dipole slots
    _, _, chi2_free = gls(theta, np.hstack([P, free_dipole_design()]), C)
    assert chi2_free < 1e-12


def test_bulk_and_expansion_responses_differ_in_redshift_dependence():
    n, z, sig, A = _sample()
    JB, JH = A @ bulk_rows(z, n), A @ hdipole_rows(z, n)
    b = [np.mean(np.diag(JB[9 * w + 1:9 * w + 4])) for w in range(4)]
    h = [np.mean(np.diag(JH[9 * w + 1:9 * w + 4])) for w in range(4)]
    zeff = [h[w] / (b[w] * C_KMS) for w in range(4)]
    assert all(np.diff(zeff) > 0) and zeff[0] < 0.035 and zeff[-1] > 0.06


def test_schur_holdout_is_the_gaussian_chain_rule():
    n, z, sig, A = _sample(seed=5)
    P = nuisance_design()
    D = np.hstack([P, A @ bulk_rows(z, n)])
    C = (A * sig[None, :] ** 2) @ A.T
    rng = np.random.default_rng(9)
    theta = D @ rng.normal(size=D.shape[1]) * 1e-3 + np.linalg.cholesky(C) @ rng.normal(size=36)
    train = list(range(18))
    test = [9 * w + s for w in (2, 3) for s in DIP_SLOTS]
    rows = train + test
    _, _, chi2_all = gls(theta[rows], D[rows][:, np.linalg.norm(D[rows], axis=0) > 0], C[np.ix_(rows, rows)])
    Dt = D[train][:, np.linalg.norm(D[train], axis=0) > 0]
    _, _, chi2_train = gls(theta[train], Dt, C[np.ix_(train, train)])
    pred = schur_predict(theta, D, C, train, test)
    assert chi2_all == pytest.approx(chi2_train + pred["chi2"], rel=1e-8, abs=1e-8)
